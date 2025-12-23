from typing import List, Dict
from langchain.tools import tool
from src.retrieval.hybrid_search import HybridSearcher
from src.retrieval.formatter import to_llm_context

class RetrievalTools:
    """Tools exposed to the LLM."""
    def __init__(self, chunks:List[Dict]):
        self.searcher = HybridSearcher(chunks)

    @tool
    def search_documents(self, query:str, top_k: int = 5) -> str:
        """Run hybrid search and return LLM-ready context"""
        results = self.searcher.search(query=query,top_k=top_k)
        return to_llm_context(results)
    
