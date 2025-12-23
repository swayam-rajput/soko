import chromadb
from pathlib import Path
import uuid

from loader import DirectoryLoader
from embedder import Embedder
from chunker import Chunker

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
        self.collection.add(ids=ids,embeddings=embeddings,documents=texts,metadatas=metadatas)
        print(f'Saved...\nTotal Stored: {self.collection.count()}')

# indexer = Indexer()
# indexer.ingest('data/')