from dataclasses import dataclass
from typing import List, Dict
try:
    from loader import Document
except ImportError:
    from src.ingest.loader import Document

@dataclass
class Chunk:
    text: str
    source: str
    meta: Dict
    
    def __repr__(self):
        return f"Chunk(source={self.source}, text_len={len(self.text)}, idx={self.meta.get('chunk_index')})"


class Chunker:
    """
    Splits long documents into smaller chunks for embedding.
    Uses a recursive character splitting strategy (simulating LangChain's RecursiveCharacterTextSplitter)
    to keep related text together.
    """
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        # Priority of separators: paragraphs, newlines, spaces, characters
        self.separators = ["\n\n", "\n", " ", ""]

    def chunk(self, documents: List[Document]) -> List[Chunk]:
        """
        Process a list of Documents into a list of Chunks.
        """
        all_chunks = []
        
        for doc in documents:
            if not doc.text:
                continue
                
            text_chunks = self._split_text(doc.text)
            
            for i, text in enumerate(text_chunks):
                # Create metadata for the chunk
                chunk_meta = doc.meta.copy() if doc.meta else {}
                chunk_meta["chunk_index"] = i
                chunk_meta["doc_id"] = str(doc.path)
                
                all_chunks.append(Chunk(
                    text=text,
                    source=str(doc.path),
                    meta=chunk_meta
                ))
                
        return all_chunks

    def _split_text(self, text: str) -> List[str]:
        """
        Recursively split text by separators until chunks are small enough.
        """
        return self._recursive_split(text, self.separators)

    def _recursive_split(self, text: str, separators: List[str]) -> List[str]:
        """
        Core logic:
        1. If text is small enough, return it.
        2. If no separators left, hard split by character size.
        3. Try splitting by the current separator.
        4. Merge small splits back together until they fill a chunk.
        """
        final_chunks = []
        
        # Base case: text fits
        if len(text) <= self.chunk_size:
            return [text]
            
        # Base case: no separators left -> force split
        if not separators:
            # Simple character slicing with overlap
            for i in range(0, len(text), self.chunk_size - self.chunk_overlap):
                yielded_chunk = text[i : i + self.chunk_size]
                final_chunks.append(yielded_chunk)
            return final_chunks

        # Recursive Step
        separator = separators[0]
        next_separators = separators[1:]
        
        # If separator not in text, skip to next separator level
        if separator not in text:
            return self._recursive_split(text, next_separators)
            
        # Split by the separator
        splits = text.split(separator)
        
        # Now merge splits that are small enough
        current_chunk = []
        current_len = 0
        
        for split in splits:
            split_len = len(split)
            
            # If a single split is huge, we need to recurse on it individually
            if split_len > self.chunk_size:
                # First, flush any accumulated chunk
                if current_chunk:
                    joined = separator.join(current_chunk)
                    final_chunks.append(joined)
                    current_chunk = []
                    current_len = 0
                
                # Recurse on this big split
                sub_chunks = self._recursive_split(split, next_separators)
                final_chunks.extend(sub_chunks)
                continue
            
            # Check if adding this split exceeds size
            # We add len(separator) because we'll rejoin with it
            sep_len = len(separator) if current_chunk else 0
            
            if current_len + sep_len + split_len > self.chunk_size:
                # Flush current chunk
                joined = separator.join(current_chunk)
                final_chunks.append(joined)
                
                # Start new chunk with overlaps if possible? 
                # (Simple version: just set current_chunk to [split])
                # For strictly accurate overlap in recursive logic, it's complex.
                # Here we just implement the content grouping, overlap is harder with separators.
                # To simulate overlap roughly: we could keep the last N items.
                # For now, let's just do greedy packing.
                
                current_chunk = [split]
                current_len = split_len
            else:
                current_chunk.append(split)
                current_len += sep_len + split_len
                
        # Flush the last chunk
        if current_chunk:
            final_chunks.append(separator.join(current_chunk))
            
        return final_chunks