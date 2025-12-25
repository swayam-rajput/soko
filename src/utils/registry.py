import json
import time
from pathlib import Path
from typing import Dict, List

REGISTRY_PATH = Path("data/raw/ingested_dirs.json")


def _load_registry() -> List[Dict]:
    if not REGISTRY_PATH.exists():
        return []
    try:
        with open(REGISTRY_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


def _save_registry(data: List[Dict]):
    REGISTRY_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(REGISTRY_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def register_directory(
    directory: Path,
    file_names: List[str],
    file_count: int,
    chunk_count: int,
):
    directory = directory.resolve()
    registry = _load_registry()

    # check if directory already exists
    for entry in registry:
        if entry["path"] == str(directory):
            # append new files only
            existing_files = set(entry.get("files", []))
            new_files = [f for f in file_names if f not in existing_files]

            entry["files"] = sorted(existing_files.union(new_files))
            entry["file_count"] = len(entry["files"])
            entry["chunk_count"] += chunk_count
            entry["ingested_at"] = time.time()

            _save_registry(registry)
            return

    # new directory entry
    registry.append({
        "path": str(directory),
        "ingested_at": time.time(),
        "files": sorted(file_names),
        "file_count": file_count,
        "chunk_count": chunk_count,
    })

    _save_registry(registry)


def list_ingested_directories() -> List[Dict]:
    return _load_registry()
