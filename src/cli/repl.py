import shlex
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from src.ingest.indexer import Indexer
from src.agent.chain import FileSearchAgent
from src.utils.utils import load_chunks_from_chroma
from src.utils.utils import log_error, log
from src.utils.status import status
from src.utils.config import load_config, set_value
from src.utils.ollama_manager import start_ollama, is_ollama_running, stop_ollama

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
    print_dim("  reset [cache|index|all]")
    print_dim("  status")
    print_dim("  config")
    print_dim("  exit")


def show_config():
    """Pretty-print the current config."""
    cfg = load_config()
    console.print("\n[bold]Current settings:[/bold]", style="white")
    for k, v in cfg.items():
        console.print(f"  [cyan]{k}[/cyan] = [yellow]{v}[/yellow]")
    console.print()


def handle_config(args: list[str]):
    """
    config                        — show all settings
    config set <key> <value>      — update a setting
    """
    if not args:
        show_config()
        return

    if args[0] == "set":
        if len(args) < 3:
            print_error("Usage: config set <key> <value>")
            print_dim("  Keys: use_ollama_by_default, ollama_autostart, ollama_model, ollama_base_url")
            return

        key, raw_val = args[1], args[2]

        # Coerce booleans and keep strings
        if raw_val.lower() in ("true", "1", "yes"):
            val = True
        elif raw_val.lower() in ("false", "0", "no"):
            val = False
        else:
            val = raw_val  # keep as string (e.g. model name / URL)

        set_value(key, val)
        log(f"Config updated: {key} = {val}")

        # If the user enabled autostart, fire it up right now too
        if key == "ollama_autostart" and val is True:
            cfg = load_config()
            start_ollama(cfg["ollama_base_url"])
    else:
        print_error(f"Unknown config sub-command: {args[0]}")
        print_dim("Usage: config | config set <key> <value>")


def run_repl():
    logo = """


    ███████╗ ██████╗ ██╗  ██╗ ██████╗
    ██╔════╝██╔═══██╗██║ ██╔╝██╔═══██╗
    ███████╗██║   ██║█████╔╝ ██║   ██║
    ╚════██║██║   ██║██╔═██╗ ██║   ██║
    ███████║╚██████╔╝██║  ██╗╚██████╔╝
    ╚══════╝ ╚═════╝ ╚═╝  ╚═╝ ╚═════╝

"""
    print(logo)
    print("Soko — Intelligent File System")
    print_dim("Type 'help' to see available commands.\n")

    # --- Ollama autostart ---
    cfg = load_config()
    if cfg["ollama_autostart"]:
        start_ollama(cfg["ollama_base_url"])
    elif cfg["use_ollama_by_default"] and not is_ollama_running(cfg["ollama_base_url"]):
        print_dim(
            "[system] Ollama is set as default but is not running. "
            "Run 'config set ollama_autostart true' to start it automatically, "
            "or start it manually with: ollama serve"
        )

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
            elif command == "status":
                status()

            elif command == "config":
                handle_config(args)
                # Reset agent so it picks up any changed settings on next 'ask'
                agent = None

            else:
                print_error(f"Unknown command: {command}")
                print_dim("Type 'help' to see available commands.")

        except KeyboardInterrupt:
            print_dim("\nInterrupted. Type 'exit' to quit.")
        except Exception as e:
            print_error(f"Error: {e}")
