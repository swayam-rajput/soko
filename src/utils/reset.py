import shutil
from pathlib import Path
from src.utils.utils import log, log_warn

CHROMA_DIR = Path("data/chroma")
CACHE_DB = Path("data/cache-db/cache.db")
REGISTRY_FILE = Path("data/raw/ingested_dirs.json")


def reset_cache():
    if CACHE_DB.exists():
        CACHE_DB.unlink()
        log("\[system] Answer cache cleared.")
    else:
        log_warn("\[system-warning] No cache to clear.")


def reset_index():
    if CHROMA_DIR.exists():
        shutil.rmtree(CHROMA_DIR)
        log("\[system] Vector database deleted.")
    else:
        log_warn("\[system-warning] No vector database found.")

    reset_cache()


def reset_all():
    reset_index()

    if REGISTRY_FILE.exists():
        REGISTRY_FILE.unlink()
        log("\[system] Ingestion registry cleared.")
    else:
        log_warn("\[system-warning] No registry file found.")
