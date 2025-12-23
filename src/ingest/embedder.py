from typing import List, Any
try:
    from sentence_transformers import SentenceTransformer
except ImportError:
    SentenceTransformer = None

class Embedder:
    """
    Generates vector embeddings for text chunks using a local transformer model.
    """
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        if SentenceTransformer is None:
            raise ImportError("sentence-transformers is not installed. Please run `pip install sentence-transformers`.")
        
        print(f"Loading embedding model: {model_name}...")
        self.model = SentenceTransformer(model_name)
        # Determine embedding dimension (usually 384 for all-MiniLM-L6-v2)
        self.dimension = self.model.get_sentence_embedding_dimension()

    def embed(self, texts: List[str]) -> List[List[float]]:
        """
        Embed a list of texts into a list of floating point vectors.
        """
        if not texts:
            return []
            
        embeddings = self.model.encode(texts, convert_to_numpy=True)
        return embeddings.tolist()

    def embed_query(self, query: str) -> List[float]:
        """
        Embed a single query string.
        """
        return self.embed([query])[0]
