from typing import List, Dict


# In src/retrieval/formatter.py
def to_llm_context(results: List[Dict]) -> str:
    """Format with actual filenames, not DOC indices."""
    if not results:
        return "[No relevant context found]"
    
    files = {}
    for result in results:
        text = result.get("text", "")
        meta = result.get("meta", {})
        
        filename = meta.get("filename", "unknown")
        parent = meta.get("parent", "")
        file_key = f"{parent}/{filename}" if parent else filename
        
        if file_key not in files:
            files[file_key] = []
        files[file_key].append(text)
    
    context_parts = []
    for source, chunks in files.items():
        header = f"=== File: {source} ==="
        content = "\n\n".join(chunks)
        context_parts.append(f"{header}\n{content}\n")
    
    return "\n".join(context_parts)