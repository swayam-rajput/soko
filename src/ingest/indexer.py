import chromadb
from pathlib import Path
import uuid

from .loader import DirectoryLoader
from .embedder import Embedder
from .chunker import Chunker

from ..utils.utils import log,log_error,log_warn

BATCH_SIZE = 500


class Indexer:
    def __init__(
        self,
        persistent_path: str = "data/chroma",
        collection_name: str = "soko_docs",
    ):
        self.persistent_path = persistent_path
        self.collection_name = collection_name

        self.client = None
        self.collection = None

        self.chunker = Chunker()
        self.embedder = Embedder()

    def _init_db(self):
        if self.client is not None:
            return

        Path(self.persistent_path).parent.mkdir(parents=True, exist_ok=True)
        log(f"\[system] Initializing Vector DB at {self.persistent_path}")

        self.client = chromadb.PersistentClient(path=self.persistent_path)
        self.collection = self.client.get_or_create_collection(self.collection_name)

    def ingest(self, directory_path: str):
        directory = Path(directory_path)


        if not directory.exists():
            log_error(f"\[system-error] Directory does not exist: {directory_path}")
            return False

        if not directory.is_dir():
            log_error(f"\[system-error] Path is not a directory: {directory_path}")
            return False

        log(f"\[system] Ingesting directory: {directory_path}")

        loader = DirectoryLoader(directory_path)
        docs = loader.load()

        if not docs:
            log_warn("\[system-warning]No documents found.")
            return False

        chunks = self.chunker.chunk(docs)
        if not chunks:
            log_warn("\[system-warning] No chunks created.")
            return False


        self._init_db()

        log(f"\[system] Embedding {len(chunks)} chunks")

        ids = [str(uuid.uuid4()) for _ in chunks]
        texts = [chunk.text for chunk in chunks]
        metadatas = [chunk.meta for chunk in chunks]
        embeddings = self.embedder.embed(texts)

        log("\[system] Saving to ChromaDB...")
        for i in range(0, len(ids), BATCH_SIZE):
            self.collection.add(
                ids=ids[i : i + BATCH_SIZE],
                embeddings=embeddings[i : i + BATCH_SIZE],
                documents=texts[i : i + BATCH_SIZE],
                metadatas=metadatas[i : i + BATCH_SIZE],
            )

        log(f"\[system] Ingestion complete. Total stored: {self.collection.count()}")
        return True