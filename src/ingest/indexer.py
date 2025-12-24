import chromadb
from pathlib import Path
import uuid

from .loader import DirectoryLoader
from .embedder import Embedder
from .chunker import Chunker
BATCH_SIZE = 500

class Indexer:
    def __init__(self, persistent_path: str = 'data/chroma', collection_name = 'soko_docs'):
        Path(persistent_path).parent.mkdir(parents=True,exist_ok=True)
        print(f'Initializing Vector DB at {persistent_path}')
        self.client = chromadb.PersistentClient(path=persistent_path)

        self.collection = self.client.get_or_create_collection(collection_name)

        self.chunker = Chunker()
        self.embedder = Embedder()

    def ingest(self,directory_path: str):
        
        print(f"--- Ingesting {directory_path} ---")
        
        loader = DirectoryLoader(directory_path)
        docs = loader.load()
        print('Doc List\n',docs)
        if not docs:
            print("No documents found.")
            return
        
        
        chunks = self.chunker.chunk(docs)
        if not chunks:
            print("No chunks created.")
            return

        print(f'Embedding {len(chunks)} chunks')
        ids = [str(uuid.uuid4()) for _ in chunks]
        texts = [chunk.text for chunk in chunks]
        metadatas = [chunk.meta for chunk in chunks]
        embeddings = self.embedder.embed(texts)


        print('Saving to ChromaDB...')
        for i in range(0,len(ids),BATCH_SIZE):
            self.collection.add(
                ids=ids[i:i+BATCH_SIZE],
                embeddings=embeddings[i:i+BATCH_SIZE],
                documents=texts[i:i+BATCH_SIZE],
                metadatas=metadatas[i:i+BATCH_SIZE]
            )
        print(f'Saved...\nTotal Stored: {self.collection.count()}')

# indexer = Indexer()
# indexer.ingest('data/')