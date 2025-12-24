
from typing import List, Dict
from rank_bm25 import BM25Okapi

class KeywordSearcher:
    """
    Literal keyword retrieval built on BM25.
    You feed it all chunk texts once → it builds an index.
    Then you can query instantly.
    """

    def __init__(self, chunks: List[Dict]):
        """
        chunks: [{"text": str, "meta": {...}}, ...]
        """
        self.texts = [c["text"] for c in chunks]
        self.metas = [c["meta"] for c in chunks]

        # tokenize corpus
        tokenized = [t.lower().split() for t in self.texts]

        # BM25 model build
        self.bm25 = BM25Okapi(tokenized)

    def search(self, query: str, top_k: int = 5) -> List[Dict]:
        """
        Returns BM25 keyword matches sorted by score.
        """
        q_tokens = query.lower().split()
        scores = self.bm25.get_scores(q_tokens)

        ranked = sorted(
            enumerate(scores),
            key=lambda x: x[1],
            reverse=True
        )[:top_k]
        # print(list(enumerate(scores)))
        
        return [
            {
                "score": float(score),
                "text": self.texts[idx],
                "meta": self.metas[idx],
            }
            for idx, score in ranked if score > 0
        ]

