import sys

from src.ingest.indexer import Indexer
from src.agent.chain import FileSearchAgent
from chromadb import PersistentClient


# -------- utility: rebuild chunks from chroma --------
def load_chunks_from_chroma(
    persist_dir="data/chroma",
    collection_name="soko_docs"
):
    client = PersistentClient(path=persist_dir)
    collection = client.get_or_create_collection(collection_name)

    data = collection.get(include=["documents", "metadatas"])

    chunks = []
    for text, meta in zip(data["documents"], data["metadatas"]):
        chunks.append({
            "text": text,
            "meta": meta
        })

    return chunks


# -------- menu actions --------
def ingest_documents():
    path = input("\nEnter folder path to ingest: ").strip()
    if not path:
        print("Invalid path.")
        return

    indexer = Indexer(
        persistent_path="data/chroma",
        collection_name="soko_docs"
    )

    print("\nIngesting documents...")
    indexer.ingest(path)
    print("Ingestion complete.\n")


def ask_question():
    print("\nLoading indexed chunks...")
    chunks = load_chunks_from_chroma()

    if not chunks:
        print("No documents indexed. Please ingest first.\n")
        return

    agent = FileSearchAgent(chunks)

    while True:
        question = input("\nAsk a question (or type 'back'): ").strip()
        if question.lower() == "back":
            break
        if not question:
            continue

        answer = agent.ask(question)
        print("\n--- ANSWER ---")
        print(answer)
        print("--------------")


def exit_program():
    print("\nExiting Intelligent File System.")
    sys.exit(0)


# -------- main menu loop --------
def main_menu():
    while True:
        print("\n===== Intelligent File System =====")
        print("1. Ingest documents")
        print("2. Ask questions")
        print("3. Exit")

        choice = input("Select an option: ").strip()

        if choice == "1":
            ingest_documents()
        elif choice == "2":
            ask_question()
        elif choice == "3":
            exit_program()
        else:
            print("Invalid option. Try again.")


if __name__ == "__main__":
    main_menu()
