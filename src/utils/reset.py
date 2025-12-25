import chromadb
import sqlite3
from pathlib import Path
from src.utils.utils import log, log_warn

CHROMA_PATH = "data/chroma"
COLLECTION_NAME = "soko_docs"

CACHE_DB = Path("data/cache-db/cache.db")
REGISTRY_FILE = Path("data/raw/ingested_dirs.json")


def reset_cache():
    if not CACHE_DB.exists():
        log_warn("No cache database found.")
        return

    try:
        conn = sqlite3.connect(CACHE_DB)
        conn.execute("DELETE FROM cache")
        conn.commit()
        conn.close()
        log("Answer cache cleared.")
    except Exception as e:
        raise RuntimeError(f"Failed to reset cache: {e}")


def reset_index():
    try:
        client = chromadb.PersistentClient(path=CHROMA_PATH)

        try:
            client.delete_collection(COLLECTION_NAME)
            log("Chroma collection deleted.")
        except Exception:
            log_warn("Collection did not exist.")

        client.get_or_create_collection(COLLECTION_NAME)
        log("Chroma collection recreated (empty).")

    except Exception as e:
        raise RuntimeError(f"Failed to reset index: {e}")

    reset_cache()


def reset_registry():
    if REGISTRY_FILE.exists():
        REGISTRY_FILE.unlink()
        log("Ingestion registry cleared.")
    else:
        log_warn("No registry file found.")

def reset_all():
    reset_index()
    reset_registry()
