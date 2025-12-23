from typing import List, Dict, Any
import chromadb
from chromadb.utils import embedding_functions
try:
    from src.ingest.embedder import Embedder
except ImportError:
    from ..ingest.embedder import Embedder
    

class VectorSearcher:
    """Handles semantic search over the indexed ChromaDB"""
    def __init__(self, persist_dir:str='data/chroma', collection_name:str = 'soko_docs'):
        self.client = chromadb.PersistentClient(path=persist_dir)
        self.collection = self.client.get_or_create_collection(collection_name)
        self.embedder = Embedder()
    

    def query(self, text:str, k:int = 5) -> List[Dict[str, Any]]:
        """Convert text -> embedding -> query Chroma -> return structured results"""
        query_vector = self.embedder.embed([text])[0]
        results = self.collection.query(query_embeddings=[query_vector],n_results=k)

        output = []      
        for i in range(len(results['ids'][0])):
            output.append({
                'id':results['ids'][0][i],
                'documents':results['documents'][0][i],
                'metadatas':results['metadatas'][0][i],
                'distances':results['distances'][0][i],
            })      
        
        return output

    
# from src.retrieval.vector_search import VectorSearcher

# vs = VectorSearcher()
# print(vs.query("about miyamoto musashi's way of strategy", k=10))
