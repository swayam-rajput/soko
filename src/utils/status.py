from datetime import datetime
from src.utils.registry import list_ingested_directories
from src.utils.utils import log, log_warn


def status():
    registry = list_ingested_directories()

    if not registry:
        log_warn("[system-warning] No directories have been ingested yet.")
        return

    log("[system] Ingestion status:\n")

    for idx, entry in enumerate(registry, start=1):
        path = entry.get("path", "unknown")
        files = entry.get("files", {})
        file_count = entry.get("file_count", len(files))
        chunk_count = entry.get("chunk_count", 0)
        ts = entry.get("ingested_at")

        ts_readable = (
            datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M:%S")
            if ts else "unknown"
        )

        log(
            f" {idx}. {path}\n"
            f"    Files ingested : {file_count}\n"
            f"    Files : {files.keys()}\n"
            f"    Chunks stored  : {chunk_count}\n"
            f"    Last ingested  : {ts_readable}\n"
        )
