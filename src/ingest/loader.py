import time
import csv
import json
import pdfplumber
from pathlib import Path
import logging
from typing import List, Union

logging.getLogger("pdfminer").setLevel(logging.ERROR)

from src.utils.utils import log, log_warn
from src.utils.hash import file_hash
from src.utils.registry import is_file_ingested


class Document:
    def __init__(self, path: Path, text: str, meta: dict):
        self.path = path
        self.text = text
        self.meta = meta

    def __repr__(self):
        return f"{self.path.name} ({self.meta.get('extension')})"


class DirectoryLoader:
    """
    Discovers and loads supported files from a directory OR a single file.
    Enforces deduplication using content hashes.
    """

    SUPPORTED = {
        ".txt": "text",
        ".md":  "text",
        ".pdf": "pdf",
        ".py":  "code",
        ".csv": "csv",
        ".json": "json",
    }

    def __init__(self, path: Union[str, Path]):
        self.path = Path(path)

    def load(self) -> List[Document]:
        start_time = time.time()

        files = self._collect_files()
        total = len(files)

        if total == 0:
            log_warn("No supported files found.")
            return []

        log(f"Found {total} supported files. Starting ingestion...")

        docs: List[Document] = []
        processed = 0
        skipped = 0

        for idx, file_path in enumerate(files, start=1):
            processed += 1
            elapsed = time.time() - start_time
            avg_time = elapsed / processed
            remaining = avg_time * (total - processed)

            log(
                f"[system] ({idx}/{total}) Processing: {file_path.name} "
                f"| elapsed: {elapsed:.1f}s | ETA: {remaining:.1f}s"
            )

            file_hash_value = file_hash(file_path)
            parent = file_path.parent.resolve()

            if is_file_ingested(parent, file_path.name, file_hash_value):
                skipped += 1
                log(f"Skipping already ingested file: {file_path.name}")
                continue

            loader_type = self.SUPPORTED[file_path.suffix.lower()]
            text = self._dispatch(file_path, loader_type)

            if not text or not text.strip():
                log_warn(f"Failed to load file: {file_path.name}")
                continue

            meta = self._build_metadata(file_path, file_hash_value)
            docs.append(Document(file_path, text, meta))

        total_time = time.time() - start_time
        log(
            f"[system] Ingestion complete. "
            f"Loaded {len(docs)} new documents "
            f"(skipped {skipped}) in {total_time:.1f}s."
        )

        return docs

    # ---------- helpers ----------

    def _collect_files(self) -> List[Path]:
        if self.path.is_file():
            return (
                [self.path]
                if self.path.suffix.lower() in self.SUPPORTED
                else []
            )

        return sorted(
            p for p in self.path.rglob("*")
            if p.is_file() and p.suffix.lower() in self.SUPPORTED
        )

    def _dispatch(self, path: Path, kind: str) -> str | None:
        try:
            if kind == "text" or kind == "code":
                return path.read_text(encoding="utf-8", errors="ignore")

            if kind == "pdf":
                return self._load_pdf(path)

            if kind == "csv":
                return self._load_csv(path)

            if kind == "json":
                return json.dumps(json.loads(path.read_text()), indent=2)

        except Exception:
            return None

        return None

    def _load_pdf(self, path: Path) -> str:
        pages = []
        with pdfplumber.open(path) as pdf:
            for p in pdf.pages:
                pages.append(p.extract_text() or "")
        return "\n".join(pages)

    def _load_csv(self, path: Path) -> str:
        rows = []
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            reader = csv.reader(f)
            for row in reader:
                rows.append(" ".join(row))
        return "\n".join(rows)

    def _build_metadata(self, path: Path, hash_value: str) -> dict:
        stat = path.stat()
        return {
            "filename": path.name,
            "extension": path.suffix.lower(),
            "size": stat.st_size,
            "modified": stat.st_mtime,
            "parent": str(path.parent.resolve()),
            "hash": hash_value,
        }
