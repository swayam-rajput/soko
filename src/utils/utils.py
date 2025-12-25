from chromadb import PersistentClient

def load_chunks_from_chroma(
    persist_dir="data/chroma",
    collection_name="soko_docs"
):
    client = PersistentClient(path=persist_dir)
    collection = client.get_or_create_collection(collection_name)

    data = collection.get(include=["documents", "metadatas"])

    return [
        {"text": text, "meta": meta}
        for text, meta in zip(data["documents"], data["metadatas"])
    ]


from rich.console import Console

console = Console()

def log(msg: str): console.print('\[system] '+msg, style="grey70")
def log_warn(msg): console.print('\[system-warning] '+msg, style="yellow")
def log_error(msg): console.print('\[system-error] '+msg, style="red")
