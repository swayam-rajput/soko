# Soko — Intelligent File System with Agentic RAG

Soko is an intelligent file system that ingests local documents, builds a structured semantic index, and answers natural-language questions using retrieval-augmented, agent-orchestrated reasoning.

Unlike basic RAG demos, Soko is designed as a system, not a script. It separates ingestion, retrieval, caching, orchestration, and control-plane metadata so it remains robust under real-world constraints such as large document sets, API quotas, and incremental updates.

---

## Why Soko Exists

Most RAG projects stop at:
“Embed files → ask questions”

Soko addresses what breaks immediately after that:
- Knowing what has been ingested
- Incremental ingestion without reprocessing everything
- Surviving LLM quota limits
- Avoiding repeated LLM calls
- Resetting system state safely
- Reasoning at the file system level

---

## Architecture Overview

Soko is split into four planes:

1. Ingestion Plane — loading, chunking, embedding, indexing  
2. Retrieval Plane — hybrid semantic + keyword search  
3. Reasoning Plane — agent-orchestrated answer generation  
4. Control Plane — registry, cache, reset, system state  

---

## Ingestion Pipeline

Supported file types:
- PDF
- TXT
- Markdown
- Python
- CSV
- JSON

Ingestion flow:
- Directory or single-file input
- Recursive scanning (directory mode)
- Metadata extraction (filename, size, timestamps)
- Semantic chunking
- Embedding via Sentence Transformers
- Storage in ChromaDB
- Registry update for incremental ingestion

---

## Retrieval

- Dense vector search via ChromaDB
- Keyword/BM25-style scoring
- Hybrid score normalization and ranking
- Context assembly with source metadata

Embeddings are used only for retrieval.  
LLMs receive plain text context.

---

## Agentic Reasoning

- Explicit state machine using LangGraph
- Deterministic execution flow
- Cache-aware answer generation
- LangChain used only for model abstraction

---

## Persistent Answer Caching

- SQLite-backed key–value store
- Key = SHA-256(question + retrieved context)
- Prevents repeated LLM calls
- Cache survives restarts
- Resettable independently

---

## LLM Strategy

- Cloud LLMs (Gemini / OpenAI)
- Automatic fallback to local models (planned)
- Retrieval pipeline remains unchanged

---

## Reset Commands

reset cache  → clears answer cache  
reset index  → clears vector DB + cache  
reset all    → clears vector DB, cache, registry  

---

## CLI Commands

ingest <path>  
ask <question>  
dirs  
files <dir>  
cache  
cache clear  
reset [cache|index|all]  
help  
exit  

---

## Installation

Python 3.10+

Install dependencies:
pip install -r requirements.txt

Set API key:
export GOOGLE_API_KEY=your_key_here

---

## Resume One-Liner

Built an intelligent file system using agentic Retrieval-Augmented Generation with hybrid search, persistent caching, incremental ingestion, and cloud-to-local LLM fallback.

---

## License

MIT
