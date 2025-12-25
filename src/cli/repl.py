import shlex
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from src.ingest.indexer import Indexer
from src.agent.chain import FileSearchAgent
from src.utils.utils import load_chunks_from_chroma
from src.utils.utils import log_error,log
console = Console()


def print_dim(msg: str):
    console.print(msg, style="#9C9C93")


def print_error(msg: str):
    console.print(msg, style="red")


def print_answer(answer: str):
    panel = Panel(
        Text(answer.strip(), style="white"),
        title="Answer",
        border_style="#4A6D7C",
    )
    console.print(panel)


def show_help():
    print_dim("Available commands:")
    print_dim("  ingest <path>")
    print_dim("  ask <question>")
    print_dim("  exit")


def run_repl():
    print("Soko — Intelligent File System")
    print_dim("Type 'help' to see available commands.\n")

    agent = None

    while True:
        try:
            user_input = console.input(
                "[bold cyan]Soko >[/bold cyan] ",
                markup=True,
            ).strip()

            if not user_input:
                continue

            parts = shlex.split(user_input)
            command = parts[0].lower()
            args = parts[1:]

            if command == "exit":
                print_dim("Exiting Soko.")
                break

            elif command == "help":
                show_help()

            elif command == "ingest":
                if not args:
                    print_error("Usage: ingest <directory_path>")
                    continue

                path = args[0]
                indexer = Indexer()
                print_dim(f"\[system] Ingesting documents from {path}")
                success = indexer.ingest(path)
                if not success:
                    print_error('\[system] Ingestion failed.')

                agent = None  # reset agent after ingestion

            elif command == "ask":
                if not args:
                    print_error("Usage: ask <your question>")
                    continue

                if agent is None:
                    print_dim("\[system] Loading indexed documents...")
                    chunks = load_chunks_from_chroma()
                    if not chunks:
                        print_error("\[system-error] No documents indexed. Run 'ingest' first.")
                        continue
                    agent = FileSearchAgent(chunks)

                question = " ".join(args)
                answer = agent.ask(question)
                print_answer(answer)
            elif command.startswith("reset"):
                from src.utils.reset import reset_cache, reset_index, reset_all

                if len(parts) == 1:
                    print_error("Usage: reset \[cache|index|all]")
                    

                target = parts[1]

                if target == "cache":
                    reset_cache()
                elif target == "index":
                    reset_index()
                elif target == "all":
                    reset_all()
                else:
                    print_error("Invalid reset option. Use: cache, index, or all.")

            else:
                print_error(f"Unknown command: {command}")
                print_dim("Type 'help' to see available commands.")

        except KeyboardInterrupt:
            print_dim("\nInterrupted. Type 'exit' to quit.")
        except Exception as e:
            print_error(f"Error: {e}")
