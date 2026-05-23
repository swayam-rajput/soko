from typing import List, Dict


def to_llm_context(results: List[Dict]) -> str:
        """
        Convert retrieval results into a clean text block formatted for LLM context ingestion.
        Each result becomes a labeled document section.
        
        Expected input format per item:
        {
            "score": float,
            "text": str,
            "meta": dict
        }
        """

        context_sections = []

        for i, r in enumerate(results, start=1):
            path = r["meta"].get("doc_id") or r["meta"].get("source") or "unknown"
            section = (
                f"[DOC {i}]\n"
                f"file: {path}\n"
                f"score: {round(r['score'], 4)}\n"
                f"---\n"
                f"{r['text']}\n"
            )
            context_sections.append(section)

            return "\n".join(context_sections).strip()
