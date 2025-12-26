from dataclasses import dataclass
from typing import List, Dict
from .loader import Document

@dataclass
class Chunk:
    text: str
    source: str
    meta: Dict

class Chunker:
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def chunk(self, documents: List[Document]) -> List[Chunk]:
        all_chunks = []

        for doc in documents:
            text = doc.text
            if not text:
                continue

            splits = self._split_text(text)

            for i, chunk_text in enumerate(splits):
                meta = dict(doc.meta or {})
                meta["chunk_index"] = i
                meta["doc_id"] = str(doc.path)

                all_chunks.append(
                    Chunk(
                        text=chunk_text,
                        source=str(doc.path),
                        meta=meta
                    )
                )

        return all_chunks

    def _split_text(self, text: str) -> List[str]:
        chunks = []
        start = 0

        while start < len(text):
            end = start + self.chunk_size
            chunk = text[start:end]
            chunks.append(chunk)
            start = end - self.chunk_overlap

        return chunks
