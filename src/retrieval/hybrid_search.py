from typing import List, Dict
from .vector_search import VectorSearcher
from .keyword_search import KeywordSearcher


class HybridSearcher:
    """
    Combines semantic vector search (Chroma) and keyword search (BM25)
    using normalized, weighted score fusion.
    """

    def __init__(self, chunks: List[Dict]):
        """
        chunks: list of
        {
            "text": str,
            "meta": dict   
        }
        """
        self.vector = VectorSearcher()
        self.keyword = KeywordSearcher(chunks)

    def search(self, query: str, top_k: int = 5) -> List[Dict]:
        
        v_results = self.vector.query(query, top_k * 2)

        v_scores = [r["distances"] for r in v_results]
        v_norm = []

        if v_scores:
            vmin, vmax = min(v_scores), max(v_scores)

            for r in v_results:
                
                score = 1 - (r["distances"] - vmin) / (vmax - vmin + 1e-9)

                v_norm.append({
                    "score": score,
                    "text": r["documents"],
                    "meta": r["metadatas"],
                })

        
        k_results = self.keyword.search(query, top_k * 2)

        k_scores = [r["score"] for r in k_results]
        k_norm = []

        if k_scores:
            kmin, kmax = min(k_scores), max(k_scores)

            for r in k_results:
                score = (r["score"] - kmin) / (kmax - kmin + 1e-9)

                k_norm.append({
                    "score": score,
                    "text": r["text"],
                    "meta": r["meta"],
                })

        
        merged: Dict[str, Dict] = {}

        def add_results(results, weight):
            for r in results:
                
                source_id = r["meta"].get("source") or r["meta"].get("id")

                if source_id not in merged:
                    merged[source_id] = {
                        "text": r["text"],
                        "meta": r["meta"],
                        "score": 0.0,
                    }

                merged[source_id]["score"] += r["score"] * weight

        add_results(v_norm, weight=0.7)
        add_results(k_norm, weight=0.3)

        
        final = list(merged.values())
        final.sort(key=lambda x: x["score"], reverse=True)

        return final[:top_k]
