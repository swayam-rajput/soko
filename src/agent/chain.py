from __future__ import annotations
from typing import TypedDict, Literal
from dataclasses import dataclass
from enum import Enum
import logging

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_ollama import ChatOllama
from langgraph.graph import StateGraph, END

from .tools import RetrievalTools
from src.cache.cache import Cache
from src.utils.config import load_config

logger = logging.getLogger(__name__)


class LLMProvider(str, Enum):
    """LLM provider identifiers."""
    GEMINI = "gemini"
    OLLAMA = "ollama"


@dataclass
class LLMConfig:
    """Configuration for LLM setup."""
    ollama_model: str
    ollama_base_url: str
    use_ollama_primary: bool
    
    @classmethod
    def from_config(cls, cfg: dict, override_model: str | None = None) -> LLMConfig:
        """Create LLMConfig from config dict with optional model override."""
        return cls(
            ollama_model=override_model or cfg["ollama_model"],
            ollama_base_url=cfg["ollama_base_url"],
            use_ollama_primary=cfg["use_ollama_by_default"]
        )


class AgentState(TypedDict):
    """State passed through the LangGraph workflow."""
    question: str
    context: str
    answer: str


class LLMError(Exception):
    """Base exception for LLM-related errors."""
    pass


class RateLimitError(LLMError):
    """Raised when API rate limit is exceeded."""
    pass


class ConnectionError(LLMError):
    """Raised when LLM connection fails."""
    pass


class ErrorClassifier:
    """Classifies LLM exceptions into specific error types."""
    
    @staticmethod
    def classify(exc: Exception) -> type[LLMError] | None:
        """
        Classify an exception into a specific LLM error type.
        
        Returns:
            Error class if classified, None if unrecognized
        """
        msg = str(exc).lower()
        
        # Rate limit detection
        if "429" in msg or "resource_exhausted" in msg:
            return RateLimitError
        
        # Connection detection
        if any(term in msg for term in ["connection refused", "connecterror", "connect"]):
            return ConnectionError
        
        return None


class LLMManager:
    """Manages primary and fallback LLM instances with error handling."""
    
    def __init__(self, config: LLMConfig):
        self.config = config
        self.gemini = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0)
        self.ollama = ChatOllama(
            model=config.ollama_model,
            base_url=config.ollama_base_url,
            temperature=0
        )
        
        # Set primary/fallback based on config
        if config.use_ollama_primary:
            self.primary = (self.ollama, LLMProvider.OLLAMA)
            self.fallback = (self.gemini, LLMProvider.GEMINI)
        else:
            self.primary = (self.gemini, LLMProvider.GEMINI)
            self.fallback = (self.ollama, LLMProvider.OLLAMA)
    
    def invoke(self, prompt: str) -> tuple[str, str]:
        """
        Invoke LLM with automatic fallback.
        
        Returns:
            Tuple of (response_text, model_identifier)
            
        Raises:
            LLMError: If both primary and fallback fail
        """
        primary_llm, primary_provider = self.primary
        fallback_llm, fallback_provider = self.fallback
        
        # Try primary LLM
        try:
            response = primary_llm.invoke(prompt)
            model_id = self._get_model_identifier(primary_provider)
            return response.content, model_id
            
        except Exception as primary_exc:
            error_type = ErrorClassifier.classify(primary_exc)
            
            # Only fallback for known recoverable errors
            if error_type not in (RateLimitError, ConnectionError):
                raise
            
            logger.warning(
                f"{primary_provider.value} failed ({error_type.__name__}) "
                f"— falling back to {fallback_provider.value}"
            )
            
            # Try fallback LLM
            try:
                response = fallback_llm.invoke(prompt)
                model_id = self._get_model_identifier(fallback_provider)
                return response.content, model_id
                
            except Exception as fallback_exc:
                fallback_error = ErrorClassifier.classify(fallback_exc)
                
                if fallback_error == ConnectionError:
                    raise ConnectionError(
                        f"Both LLMs unavailable.\n"
                        f"Primary ({primary_provider.value}): {error_type.__name__}\n"
                        f"Fallback ({fallback_provider.value}): Connection failed\n\n"
                        f"Start Ollama with: ollama serve\n"
                        f"Pull model: ollama pull {self.config.ollama_model}"
                    ) from fallback_exc
                
                # Unexpected fallback error
                raise LLMError(
                    f"Primary failed with {error_type.__name__}, "
                    f"fallback failed with {type(fallback_exc).__name__}"
                ) from fallback_exc
    
    def _get_model_identifier(self, provider: LLMProvider) -> str:
        """Get human-readable model identifier."""
        if provider == LLMProvider.OLLAMA:
            return f"ollama/{self.config.ollama_model}"
        return "gemini-2.5-flash"


class FileSearchAgent:
    """
    LangGraph agent for document search and question answering.
    
    Features:
    - Semantic document retrieval
    - LLM-based answer generation with primary/fallback
    - Response caching for identical queries
    - Automatic error recovery
    """

    def __init__(self, chunks, ollama_model: str | None = None):
        """
        Initialize the agent.
        
        Args:
            chunks: Document chunks for retrieval
            ollama_model: Override default Ollama model
        """
        cfg = load_config()
        llm_config = LLMConfig.from_config(cfg, ollama_model)
        
        self.llm_manager = LLMManager(llm_config)
        self.tools = RetrievalTools(chunks)
        self.cache = Cache()
        self.graph = self._build_graph()

    def _build_graph(self) -> StateGraph:
        """Build the LangGraph execution graph."""
        graph = StateGraph(AgentState)
        
        graph.add_node("retrieve", self._retrieve_node)
        graph.add_node("answer", self._answer_node)
        
        graph.set_entry_point("retrieve")
        graph.add_edge("retrieve", "answer")
        graph.add_edge("answer", END)
        
        return graph.compile()

    def _retrieve_node(self, state: AgentState) -> dict:
        """Retrieve relevant document context."""
        context = self.tools.search_documents(state["question"])
        return {"context": context}

    def _answer_node(self, state: AgentState) -> dict:
        """Generate answer using LLM with caching."""
        question = state["question"]
        context = state["context"]
        
        # Check cache first
        cache_key = self.cache.make_key(question, context)
        cached_answer = self.cache.get(cache_key)
        
        if cached_answer:
            logger.info("Cache hit - skipping LLM call")
            return {"answer": cached_answer}
        
        # Generate answer via LLM
        prompt = self._build_prompt(context, question)
        
        try:
            answer, model_id = self.llm_manager.invoke(prompt)
            self.cache.set(key=cache_key, answer=answer, model=model_id)
            return {"answer": answer}
            
        except LLMError as e:
            logger.error(f"LLM invocation failed: {e}")
            return {"answer": f"[Error] {str(e)}"}

    @staticmethod
    def _build_prompt(context: str, question: str) -> str:
        """Build the LLM prompt with context and question."""
        return f"""You are answering questions using retrieved document context.

Context:
{context}

Question:
{question}

Provide a clear, accurate answer based solely on the context provided."""

    def ask(self, question: str) -> str:
        """
        Ask a question and get an answer.
        
        Args:
            question: User question
            
        Returns:
            Generated answer
        """
        try:
            result = self.graph.invoke({"question": question})
            return result["answer"]
        except Exception as e:
            logger.exception("Graph execution failed")
            return f"[Error] Failed to process question: {str(e)}"


# Convenience function for quick testing
def create_agent(chunks, use_ollama: bool = False, ollama_model: str | None = None) -> FileSearchAgent:
    """
    Factory function to create a FileSearchAgent with common configurations.
    
    Args:
        chunks: Document chunks
        use_ollama: Whether to use Ollama as primary LLM
        ollama_model: Custom Ollama model name
        
    Returns:
        Configured FileSearchAgent instance
    """
    return FileSearchAgent(chunks, ollama_model=ollama_model)