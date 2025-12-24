import sys

from src.ingest.indexer import Indexer
from src.agent.chain import FileSearchAgent
from src.utils.utils import load_chunks_from_chroma

from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from InquirerPy import inquirer

console = Console()

# ---------- UI helpers ----------
def info(msg: str):
    console.print(f"[cyan]{msg}[/cyan]")

def success(msg: str):
    console.print(f"[green]{msg}[/green]")

def error(msg: str):
    console.print(f"[red]{msg}[/red]")

def show_answer(answer: str):
    panel = Panel(
        Text(answer.strip(), style="white"),
        title="Answer",
        border_style="bright_blue",
    )
    console.print(panel)


# ---------- actions ----------
def ingest_documents():
    path = inquirer.text(
        message="Enter folder path to ingest:"
    ).execute()

    if not path.strip():
        error("Invalid path.")
        return

    indexer = Indexer(
        persistent_path="data/chroma",
        collection_name="soko_docs"
    )

    info("Ingesting documents...")
    indexer.ingest(path)
    success("Ingestion complete.")


def ask_questions():
    info("Loading indexed chunks...")
    chunks = load_chunks_from_chroma()

    if not chunks:
        error("No documents indexed. Please ingest first.")
        return

    agent = FileSearchAgent(chunks)

    while True:
        question = inquirer.text(
            message="Ask a question (type 'back' to return):"
        ).execute()

        if question.lower() == "back":
            break
        if not question.strip():
            continue

        answer = agent.ask(question)
        show_answer(answer)


def exit_program():
    info("Exiting Soko.")
    sys.exit(0)


# ---------- menu ----------
def run_cli():
    while True:
        choice = inquirer.select(
            message="Soko — Intelligent File System",
            choices=[
                "Ingest documents",
                "Ask questions",
                "Exit",
            ],
        ).execute()

        if choice == "Ingest documents":
            ingest_documents()
        elif choice == "Ask questions":
            ask_questions()
        elif choice == "Exit":
            exit_program()
