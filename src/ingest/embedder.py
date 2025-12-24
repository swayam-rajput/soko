from typing import List
try:
    from sentence_transformers import SentenceTransformer
except ImportError:
    SentenceTransformer = None


class Embedder:
    """
    Lazily loads the embedding model only when first used.
    """

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        if SentenceTransformer is None:
            raise ImportError(
                "sentence-transformers is not installed. "
                "Run `pip install sentence-transformers`."
            )

        self.model_name = model_name
        self._model = None
        self.dimension = None

    def _load_model(self):
        if self._model is not None:
            return

        self._model = SentenceTransformer(self.model_name)
        self.dimension = self._model.get_sentence_embedding_dimension()

    def embed(self, texts: List[str]) -> List[List[float]]:
        if not texts:
            return []

        self._load_model()
        embeddings = self._model.encode(texts, convert_to_numpy=True)
        return embeddings.tolist()

    def embed_query(self, query: str) -> List[float]:
        return self.embed([query])[0]
