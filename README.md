# Soko

Soko is an intelligent file system that ingests local documents, builds a semantic index over their contents, and answers natural-language questions using Retrieval-Augmented Generation (RAG). It is designed as a production-oriented system rather than a demo: ingestion is incremental, duplicate documents are prevented through content hashing, retrieval combines semantic and keyword search, and the query pipeline is orchestrated using LangGraph.

---

## Overview

Soko allows users to ingest individual files or entire directories and interact with their documents through a terminal interface.

Unlike a basic RAG application, Soko focuses on building a persistent document system by supporting:

- Incremental ingestion
- Hash-based deduplication
- Hybrid retrieval
- Persistent answer caching
- Explicit query orchestration
- Safe reset mechanisms

The system is designed so that documents only need to be processed once while remaining searchable across future sessions.

---

# Architecture

The architecture consists of two independent pipelines connected through persistent storage.

- **Ingestion Pipeline** – discovers, processes, and indexes documents.
- **Query Pipeline** – retrieves relevant information and generates answers.

Both pipelines share the same vector database, registry, and cache.

## Workflow

![Workflow](/soko-workflow.png)

---

# System Workflow

## Ingestion Pipeline

The ingestion pipeline converts raw documents into a searchable semantic index.

### 1. File Discovery

The user provides either

- a single file
- a directory

Directories are scanned recursively and supported file types are collected.

---

### 2. Deduplication

Each discovered file is hashed using SHA-256.

The registry is checked before processing.

If a file hash already exists, the file is skipped entirely.

This allows incremental ingestion without reprocessing previously indexed documents.

---

### 3. Document Processing

New documents are

- loaded
- cleaned
- split into semantic chunks

Chunking ensures that retrieval occurs over meaningful pieces of text instead of entire documents.

---

### 4. Embedding Generation

Each chunk is converted into a dense vector representation using a Sentence Transformer embedding model.

These embeddings capture semantic meaning instead of simple keyword frequency.

---

### 5. Vector Storage

Each embedding, along with its metadata, is stored inside ChromaDB.

Stored metadata includes information such as

- filename
- parent directory
- chunk index
- content hash

This metadata is later used for retrieval and citation.

---

### 6. Registry Update

After successful indexing, the registry is updated.

Only completed ingestions are committed, making the process restart-safe.

---

# Query Pipeline

When a user asks a question, Soko retrieves relevant context before generating a response.

### 1. User Query

The user submits a natural-language question through the CLI.

Examples:

```text
What is Retrieval-Augmented Generation?

Explain RSA.

Which files contain Hopfield Network?
```

---

### 2. Intent Classification

LangGraph determines how the request should be processed.

Examples include

- Question Answering
- File Discovery
- Future workflow extensions

---

### 3. Hybrid Retrieval

Retrieval combines two independent search techniques.

### Semantic Search

Queries are embedded and searched against ChromaDB using vector similarity.

This retrieves documents with similar meaning.

### Keyword Search

A BM25-based keyword search retrieves documents containing exact terms.

This improves performance for technical identifiers, filenames, and exact phrases.

---

### 4. Score Fusion

Results from semantic search and keyword search are merged into a unified ranking.

This balances semantic relevance with exact keyword matches.

---

### 5. Context Formatting

Retrieved chunks are grouped by their source file.

Instead of passing isolated chunks to the language model, Soko formats context as

```text
=== File: Notes.pdf ===
...

=== File: Assignment.md ===
...
```

This preserves document provenance and helps the model generate grounded answers.

---

### 6. Cache Lookup

Before calling the language model, Soko checks a persistent SQLite cache.

If the same question has already been answered using the same context, the cached response is returned immediately.

Otherwise, the request proceeds to the language model.

---

### 7. Answer Generation

The formatted context is passed to the configured language model.

Current support includes

- Gemini
- Ollama fallback (planned/optional)

The generated response is returned to the user and stored in the cache.

---

# LangGraph Workflow

LangGraph is used as the orchestration layer for Soko's query pipeline.

Instead of implementing retrieval inside one large function, each stage is represented as an explicit node with clearly defined inputs and outputs.

Current workflow:
![Workflow](/soko-workflow.png)

Using LangGraph keeps the retrieval workflow modular and allows future extensions such as

- reranking
- query rewriting
- citation verification
- local/cloud model routing
- multi-agent workflows

without restructuring the application.

---

# Storage Components

Soko maintains three persistent storage layers.

| Component | Purpose |
|-----------|---------|
| ChromaDB | Stores document embeddings and metadata |
| Registry | Tracks SHA-256 hashes of ingested files |
| SQLite Cache | Stores previous question-answer pairs |

Each component has a single responsibility, making the system easier to maintain.

---

# Key Features

- Recursive document ingestion
- Multi-format document support
- Incremental indexing
- SHA-256 hash-based deduplication
- Semantic document chunking
- Sentence Transformer embeddings
- ChromaDB vector storage
- Hybrid retrieval (Vector + BM25)
- LangGraph query orchestration
- Persistent SQLite answer cache
- CLI interface built with Rich
- Logical reset operations
- Metadata-aware context formatting

---

# Supported File Types

- PDF
- TXT
- Markdown
- CSV
- JSON
- Python source files

Additional loaders can be added without modifying the retrieval pipeline.

---

# Requirements

## System Requirements

- Python 3.10+
- Windows
- Linux
- macOS

---

## Core Dependencies

### Vector Database

- ChromaDB

### Embeddings

- Sentence Transformers

### Machine Learning Backend

- PyTorch

### PDF Processing

- pdfplumber
- pdfminer

### Retrieval

- rank-bm25

### Agent Framework

- LangGraph

### LLM Abstractions

- LangChain Core

### Language Models

- Google Gemini

Requires

```
GOOGLE_API_KEY
```

---

# CLI Usage

```bash
Soko > ingest ./documents

Soko > ingest ./book.pdf

Soko > ask "Explain Retrieval-Augmented Generation."

Soko > ask "Which files contain RSA?"

Soko > status

Soko > reset cache

Soko > reset index

Soko > reset all

Soko > exit
```

---

# Folder Structure

```
src/
│
├── agent/
├── cache/
├── cli/
├── ingest/
├── retrieval/
└── utils/

data/
│
├── chroma/
├── cache-db/
└── raw/
```

---

# Why Hybrid Retrieval?

Semantic search understands meaning.

Keyword search understands exact text.

Neither approach is sufficient by itself.

By combining both retrieval strategies before ranking, Soko improves both recall and precision across a wider range of queries.

---

# Deduplication

Each file is identified by its SHA-256 content hash rather than its filename.

This ensures

- renamed files are not duplicated
- identical files are skipped
- modified files are automatically reprocessed

---

# Design Decisions

### ChromaDB

Provides lightweight persistent vector storage suitable for local-first applications.

### SHA-256 Registry

Tracks document identity by content instead of filesystem location.

### SQLite Cache

Reduces repeated LLM calls and improves response latency.

### LangGraph

Separates retrieval, formatting, caching, and answer generation into explicit workflow stages.

### Logical Reset Operations

Collections and caches are cleared through application logic instead of deleting database files directly, avoiding filesystem locking issues.

---

# Limitations

- Local GGUF inference is not yet integrated by default
- Keyword ranking is intentionally simple
- Registry currently uses JSON storage
- No reranking model
- No citation generation
- No multi-user support

---

# Future Work

- Local GGUF model support
- Cross-encoder reranking
- Citation-aware responses
- OCR support for scanned PDFs
- Metadata filtering
- Query rewriting
- Multi-agent workflows
- Local-only inference mode
- Improved file discovery mode
- Plugin architecture for new document loaders

---

# License

MIT License
