"""
ollama_manager.py — Manages the `ollama serve` background process.

On app startup (if autostart is configured), this spawns `ollama serve`
as a detached subprocess so the user doesn't have to do it manually.
"""

import subprocess
import sys
import time
import httpx
import psutil
import atexit
from .utils import log_error, log, log_model, log_warn

_we_started_ollama = False
_ollama_proc: subprocess.Popen | None = None


def is_ollama_running(base_url: str = "http://localhost:11434") -> bool:
    """Return True if Ollama is already reachable."""
    try:
        r = httpx.get(f"{base_url}/api/tags", timeout=2.0)
        return r.status_code == 200
    except Exception:
        return False

def _find_ollama_pid() -> int | None:
    """Return the PID of the Ollama process, if we started it."""
    try:
        for proc in psutil.process_iter(["pid", "name", "cmdline"]):
            try:
                cmdline = proc.info.get("cmdline") or []
                # Look for "ollama serve" or "ollama.exe serve"
                if len(cmdline) >= 2:
                    if "ollama" in cmdline[0].lower() and "serve" in cmdline[1].lower():
                        return proc.info["pid"]
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
    except Exception as e:
        log_warn(f"Could not scan for Ollama process: {e}")
    return None

def start_ollama(base_url: str = "http://localhost:11434") -> bool:
    """
    Spawn `ollama serve` as a background process if it isn't already running.

    Returns True if Ollama is reachable after the attempt.
    """
    global _ollama_proc, _we_started_ollama

    if is_ollama_running(base_url):
        log_model("Ollama is already running.")
        return True

    log_model("Starting Ollama in the background...")

    try:
        # On Windows, CREATE_NO_WINDOW keeps the child console hidden.
        kwargs: dict = {}
        if sys.platform == "win32":
            pass
            # kwargs["creationflags"] = subprocess.CREATE_NO_WINDOW

        _ollama_proc = subprocess.Popen(
            ["ollama", "serve"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            **kwargs,
        )
        _we_started_ollama = True
    except FileNotFoundError:
        log_error(
            "'ollama' not found in PATH. "
            "Install Ollama from https://ollama.com and try again.",
        )
        return False

    # Give it up to 8 seconds to become reachable
    for _ in range(8):
        time.sleep(1)
        if is_ollama_running(base_url):
            log_model("Ollama started successfully.")
            atexit.register(stop_ollama)
            return True

    log_warn(
        "Ollama did not respond in time. "
        "It may still be loading — queries will retry.",
    )
    return False


def stop_ollama(force: bool = False) -> None:
    """Terminate the Ollama process that *we* started (if any)."""
    global _ollama_proc, _we_started_ollama
    if not force and not _we_started_ollama:
        log_model(
            "Not stopping Ollama (it was already running before we started).",
        )
        return

    pid = _find_ollama_pid()
    
    if pid is None:
        log_model("Ollama is not running.")
        return

    try:
        # Try graceful shutdown first
        proc = psutil.Process(pid)
        proc.terminate()
        
        # Wait up to 5 seconds for graceful shutdown
        try:
            proc.wait(timeout=10)
            log_model("Ollama stopped.")
        except psutil.TimeoutExpired:
            # Force kill if it didn't stop
            log_warn('Ollama didn\'t stop gracefully, shutting down forecefully...')
            proc.kill()
            proc.wait(timeout=2)
            log_warn("Ollama force-stopped.")
            
    except psutil.NoSuchProcess:
        log_warn("Ollama process already exited.")
    except psutil.AccessDenied:
        console.print(
            "Permission denied. Run as administrator to stop Ollama.",
            style="red"
        )
    except Exception as e:
        log_error(f"Failed to stop Ollama: {e}", style="red")
    finally:
        _ollama_proc = None
        _we_started_ollama = False


def ensure_model_available(model_name: str, base_url: str = "http://localhost:11434") -> bool:
    """
    Check if a model is available, and prompt to pull it if not.
    
    Args:
        model_name: Name of the model (e.g., "llama3")
        base_url: Ollama API base URL
        
    Returns:
        True if model is available or successfully pulled
    """
    try:
        r = httpx.get(f"{base_url}/api/tags", timeout=5.0)
        if r.status_code != 200:
            return False
        
        models = r.json().get("models", [])
        model_names = [m.get("name", "").split(":")[0] for m in models]
        
        if model_name in model_names:
            return True
        
        # Model not found - suggest pulling it
        log_warn(
            f"Model '{model_name}' not found locally.",
        )
        log(
            f"Pull it with: ollama pull {model_name}",
            style="grey70"
        )
        return False
        
    except Exception as e:
        log_error(f"Could not check models: {e}", style="red")
        return False
