import chromadb
from pathlib import Path
import uuid

from .loader import DirectoryLoader
from .embedder import Embedder
from .chunker import Chunker

from ..utils.utils import log,log_error,log_warn
from ..utils.registry import register_directory

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

    def ingest(self, path_str: str):
        path = Path(path_str)

        if not path.exists():
            log_error(f"\[system-error] Path does not exist: {path}")
            return False

        if path.is_file():
            return self._ingest_file(path)

        if path.is_dir():
            return self._ingest_directory(path)

        log_error(f"\[system-error] Unsupported path: {path}")
        return False

    def _ingest_file(self, file_path: Path):
        log(f"\[system] Ingesting file: {file_path.name}")

        loader = DirectoryLoader(file_path.parent)
        doc = loader.load_file(file_path)

        if not doc:
            log_error("\[system-error] Failed to load file")
            return False

        return self._process_documents(
            docs=[doc],
            parent=file_path.parent,
        )

    

    def _ingest_directory(self, directory: Path):
        log(f"\[system] Ingesting directory: {directory}")

        loader = DirectoryLoader(directory)
        docs = loader.load()

        if not docs:
            log_warn("\[system-warning] No documents found.")
            return False

        return self._process_documents(
            docs=docs,
            parent=directory,
        )


    def _process_documents(self, docs, parent: Path):
        chunks = self.chunker.chunk(docs)
        if not chunks: 
            log_warn('\[system-warning] No chunks created.')
            return False
    
        self._init_db()
        
        log(f'\[system] Embedding {len(chunks)} chunks')
        
        ids = [str(uuid.uuid4()) for _ in chunks]
        texts = [c.text for c in chunks]
        metadatas = [c.meta for c in chunks]
        embeddings = self.embedder.embed(texts)

        log("\[system] Saving to ChromaDB...")
        for i in range(0, len(ids), BATCH_SIZE):
            self.collection.add(
                ids=ids[i:i+BATCH_SIZE],
                embeddings=embeddings[i:i+BATCH_SIZE],
                documents=texts[i:i+BATCH_SIZE],
                metadatas=metadatas[i:i+BATCH_SIZE],
            )

        log(f"\[system] Ingestion complete. Total stored: {self.collection.count()}")

        from src.utils.registry import register_directory
        register_directory(
            directory=parent,
            file_names=[d.path.name for d in docs],
            file_count=len(docs),
            chunk_count=len(chunks),
        )

        return True    
    
        

