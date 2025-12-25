from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import StateGraph, END
# from src.agent.tools import RetrievalTools
from .tools import RetrievalTools
from typing import TypedDict
from src.cache.cache import Cache

class AgentState(TypedDict):
    question:str
    context:str
    answer:str

class FileSearchAgent:
    """Langchain agnet that searches documents and answers questions"""
    def __init__(self, chunks):
        self.llm = ChatGoogleGenerativeAI(
            model='gemini-2.5-flash',
            temperature=0
        )
        self.tools = RetrievalTools(chunks)
        self.graph = self._build()
        self.cache = Cache()

    def _build(self):
        graph = StateGraph(AgentState)

        def retrieve(state: AgentState):
            context = self.tools.search_documents(state['question'])
            return {'context':context}

        def answer(state:AgentState):
            context = state['context']
            question = state['question']

            cache_key = self.cache.make_key(question,context)
            cached = self.cache.get(cache_key)
            
            if cached:
                print('[system] Cache hit (No LLM Call)')
                return {'answer':cached}
            
            prompt = f"""
You are answering questions using retrieved document context.
Context:
{state['context']}

Question:
{state['question']}
"""
            
            
            response = self.llm.invoke(prompt)
            self.cache.set(
                key=cache_key,
                answer=response.content,
                model=self.llm.model,
            )
            return {'answer': response.content}
        
        graph.add_node('retrieve', retrieve)
        graph.add_node('answer', answer)

        graph.set_entry_point("retrieve")
        graph.add_edge("retrieve",'answer')
        graph.add_edge('answer',END)

        return graph.compile()


    def ask(self, question: str) -> str:
        result = self.graph.invoke({'question':question})
        # print(result)
        return result['answer']

        