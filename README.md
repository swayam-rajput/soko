# Soko

Soko is an intelligent file system that ingests local documents, builds a semantic index over their contents, and answers natural-language questions using retrieval-augmented generation (RAG). It is designed as a system rather than a demo: ingestion is incremental, duplicate documents are prevented via content hashing, retrieval is hybrid (semantic + keyword), and reasoning is orchestrated through an explicit agent workflow.


## Overview

Soko allows a user to ingest local files or directories and query them conversationally from a CLI. Unlike basic RAG pipelines, Soko tracks what has already been ingested, avoids reprocessing identical files, caches previous answers to reduce LLM usage, and provides reset mechanisms that respect database lifecycles and operating system constraints.

## Architecture and Data Flow
#### 1. Ingestion
- User provides a file path or directory
- Supported files are discovered recursively
- Each file’s content hash (SHA-256) is computed
- Files already present in the registry are skipped

#### 2. Processing
- New documents are split into semantic chunks
- Chunks are embedded using a sentence-transformer model
- Embeddings and metadata are stored in ChromaDB

#### 3. Registry Update
- After successful writes, the registry is updated with file names and hashes
- Enables incremental, restart-safe ingestion

#### 4. Querying
- User query triggers hybrid retrieval (vector + keyword)
- Relevant chunks are assembled into an LLM-ready context

#### 5. Reasoning
- LangGraph orchestrates retrieval and answer generation
- Persistent cache is checked before calling the LLM


## Key Features

- Multi-format ingestion: PDF, TXT, MD, CSV, JSON, and source code
- Hash-based deduplication and incremental ingestion
- Semantic chunking and embedding
- Vector storage using ChromaDB
- Hybrid retrieval (semantic + keyword)
- Agentic reasoning using LangGraph
- LLM-agnostic design (Gemini supported, local models planned)
- Persistent answer caching
- CLI-based user interaction
- Logical reset mechanisms (no unsafe file deletion)
- Registry tracking of ingested directories and files

## Requirements

Soko is designed to run locally and requires only a standard Python environment with a small set of well-defined dependencies.

#### System Requirements

- Python 3.10 or newer

- Supported OS: Windows, macOS, Linux

- Sufficient disk space for vector storage (depends on document size)

#### Core Dependencies

- ChromaDB – persistent local vector database

- Sentence Transformers – semantic embedding generation

- PyTorch – backend for embedding models

- pdfplumber / pdfminer – PDF text extraction

#### Agentic Reasoning & LLM Integration

- LangGraph – explicit agent execution graph

- LangChain Core – model and tool abstractions

- Google Generative AI (Gemini) – cloud LLM support

    - Requires a valid GOOGLE_API_KEY environment variable

## CLI Usage

```bash
Soko > ingest ./documents
Soko > ingest ./book.pdf
Soko > ask "What is this document about?"
Soko > status
Soko > reset cache
Soko > reset index
Soko > reset all
```

## Folder Structure
```
src/
│── ingest/
│── retrieval/
│── agent/
│── cache/
│── cli/
│── utils/

data/
│── chroma/
│── cache-db/
│── raw/
```

## How Ingestion Works
#### 1. File discovery (directory or single file)
#### 2. Content hashing for deduplication
#### 3. Semantic chunking
#### 4. Embedding generation
#### 5. Vector storage in ChromaDB
#### 6. Registry update (commit step)

## How Retrieval Works
#### 1. Query embedding
#### 2. Vector similarity search
#### 3. Keyword/BM25-style scoring
#### 4. Score normalization
#### 5. Hybrid ranking
#### 6. Context assembly


### Deduplication

Each file is identified by a SHA-256 hash of its contents. A file is skipped during ingestion if its hash already exists in the registry. This ensures deterministic deduplication and allows modified files to be re-ingested safely.


### Agentic Reasoning

LangGraph is used to define an explicit execution graph (retrieve → answer). Compared to LangChain’s higher-level abstractions, LangGraph makes control flow and state transitions explicit, improving debuggability and predictability.


### Design Decisions

- **ChromaDB**: simple local persistence and vector operations
- **Content hashes**: content-based identity instead of filenames or paths
- **Logical resets**: truncate collections and tables instead of deleting files
- **Caching**: reduce LLM calls and quota usage



## Limitations and Future Work

- No local LLM inference yet
- Keyword ranking is basic
- Registry is JSON-based and may migrate to a database
- No multi-user support
- Add ASCII art to let users know the status of their operations




