import uuid
from pathlib import Path
from typing import Dict

import chromadb

from src.ingest.loader import DirectoryLoader, Document
from src.ingest.chunker import Chunker
from src.ingest.embedder import Embedder
from src.utils.registry import register_files
from src.utils.utils import log, log_warn, log_error

BATCH_SIZE = 500


class Indexer:
    """
    Coordinates ingestion:
    Loader -> Chunker -> Embedder -> ChromaDB -> Registry
    """

    def __init__(
        self,
        persist_path: str = "data/chroma",
        collection_name: str = "soko_docs",
    ):
        self.persist_path = persist_path
        self.collection_name = collection_name

        self.client = None
        self.collection = None

        self.chunker = Chunker()
        self.embedder = None  # lazy init

    # ---------- internal ----------

    def _init_db(self):
        if self.client:
            return

        Path(self.persist_path).parent.mkdir(parents=True, exist_ok=True)
        log(f"[system] Initializing vector database at {self.persist_path}")

        self.client = chromadb.PersistentClient(path=self.persist_path)
        self.collection = self.client.get_or_create_collection(self.collection_name)

    def _init_embedder(self):
        if self.embedder:
            return

        log("[system] Loading embedding model")
        self.embedder = Embedder()

    # ---------- public ----------

    def ingest(self, path: str) -> bool:
        """
        Ingest a directory or a single file.
        Returns True if anything was ingested.
        """
        loader = DirectoryLoader(path)
        documents = loader.load()

        if not documents:
            log_warn("[system-warning] Nothing new to ingest.")
            return False

        # Chunk
        chunks = self.chunker.chunk(documents)
        if not chunks:
            log_warn("[system-warning] No chunks created.")
            return False

        # Init heavy resources only now
        self._init_db()
        self._init_embedder()

        texts = [c.text for c in chunks]
        metadatas = [c.meta for c in chunks]
        ids = [str(uuid.uuid4()) for _ in chunks]

        log(f"[system] Embedding {len(chunks)} chunks")
        embeddings = self.embedder.embed(texts)

        log("[system] Writing embeddings to ChromaDB")
        try:
            for i in range(0, len(ids), BATCH_SIZE):
                self.collection.add(
                    ids=ids[i : i + BATCH_SIZE],
                    embeddings=embeddings[i : i + BATCH_SIZE],
                    documents=texts[i : i + BATCH_SIZE],
                    metadatas=metadatas[i : i + BATCH_SIZE],
                )
        except Exception as e:
            log_error(f"[system-error] Failed to write to ChromaDB: {e}")
            return False

        # ---- registry update (commit point) ----
        file_map: Dict[str, str] = {}
        for doc in documents:
            file_map[doc.path.name] = doc.meta["hash"]

        parent_dir = documents[0].path.parent
        register_files(
            directory=parent_dir,
            file_map=file_map,
            chunk_count=len(chunks),
        )

        log(
            f"[system] Ingestion complete. "
            f"Stored {len(chunks)} chunks from {len(file_map)} files."
        )
        return True

    def close(self):
        """
        Explicitly release DB resources.
        Required for reset on Windows.
        """
        self.client = None
        self.collection = None
