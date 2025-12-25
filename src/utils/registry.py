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

def is_file_ingested(directory: Path, file_name: str, file_hash: str) -> bool:
    registry = _load_registry()
    directory = str(directory.resolve())

    for entry in registry:
        if entry["path"] == directory:
            files = entry.get("files", {})
            return files.get(file_name) == file_hash

    return False

def register_files(
    directory: Path,
    file_map: Dict[str, str],
    chunk_count: int,
):
    registry = _load_registry()
    directory = str(directory.resolve())

    for entry in registry:
        if entry["path"] == directory:
            entry["files"].update(file_map)
            entry["file_count"] = len(entry["files"])
            entry["chunk_count"] += chunk_count
            entry["ingested_at"] = time.time()
            _save_registry(registry)
            return

    registry.append({
        "path": directory,
        "files": file_map,
        "file_count": len(file_map),
        "chunk_count": chunk_count,
        "ingested_at": time.time()
    })

    _save_registry(registry)

def list_ingested_directories() -> List[Dict]:
    return _load_registry()
