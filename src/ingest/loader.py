import time
import csv
import json
import pdfplumber
from pathlib import Path
import logging

logging.getLogger("pdfminer").setLevel(logging.ERROR)

from src.utils.utils import log


class Document:
    def __init__(self, path: Path, text: str, meta: dict):
        self.path = path
        self.text = text
        self.meta = meta

    def __repr__(self):
        return (
            f"{self.path}, {self.meta['size']} bytes, "
            f"{self.meta['modified']}, {self.meta['extension']}, "
            f"{self.meta['filename']}, {self.meta['parent']}"
        )


class DirectoryLoader:
    """
    Load many file types into uniform plain text format.
    Produces Document objects ready for chunking + embedding.
    """

    SUPPORTED = {
        ".txt": "text",
        ".md":  "text",
        ".pdf": "pdf",
        ".py":  "code",
        ".csv": "csv",
        ".json": "json",
    }

    def __init__(self, directory: str):
        self.directory = Path(directory)

    def load(self):
        start_time = time.time()

        # --- pre-scan ---
        all_files = [
            p for p in self.directory.rglob("*")
            if p.is_file() and p.suffix.lower() in self.SUPPORTED
        ]

        total = len(all_files)
        if total == 0:
            log("[system] No supported files found.")
            return []

        log(f"[system] Found {total} supported files. Starting ingestion...")

        docs = []
        processed = 0

        for idx, file_path in enumerate(all_files, start=1):
            processed += 1
            elapsed = time.time() - start_time
            avg_time = elapsed / processed
            remaining = avg_time * (total - processed)

            log(
                f"[system] ({idx}/{total}) Processing: {file_path.name} "
                f"| elapsed: {elapsed:.1f}s | ETA: {remaining:.1f}s"
            )

            loader_type = self.SUPPORTED[file_path.suffix.lower()]
            text = self._dispatch(file_path, loader_type)

            if text and text.strip():
                meta = self._build_metadata(file_path)
                docs.append(Document(file_path, text, meta))

        total_time = time.time() - start_time
        log(
            f"[system] Ingestion complete. "
            f"Loaded {len(docs)} documents in {total_time:.1f}s."
        )

        return docs

    # ---------- loaders ----------

    def _dispatch(self, path, type_):
        if type_ == "text":
            return self._load_text(path)
        if type_ == "pdf":
            return self._load_pdf(path)
        if type_ == "code":
            return self._load_code(path)
        if type_ == "csv":
            return self._load_csv(path)
        if type_ == "json":
            return self._load_json(path)
        return None

    def _load_text(self, path):
        try:
            return path.read_text(encoding="utf-8", errors="ignore")
        except:
            return None

    def _load_pdf(self, path):
        try:
            pages = []
            with pdfplumber.open(path) as pdf:
                for p in pdf.pages:
                    pages.append(p.extract_text() or "")
            return "\n".join(pages)
        except:
            return None

    def _load_code(self, path):
        try:
            return path.read_text(encoding="utf-8", errors="ignore")
        except:
            return None

    def _load_csv(self, path):
        try:
            rows = []
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                reader = csv.reader(f)
                for row in reader:
                    rows.append(" ".join(row))
            return "\n".join(rows)
        except:
            return None

    def _load_json(self, path):
        try:
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                obj = json.load(f)
            return json.dumps(obj, indent=2)
        except:
            return None

    def _build_metadata(self, path):
        stat = path.stat()
        return {
            "extension": path.suffix.lower(),
            "size": stat.st_size,
            "modified": stat.st_mtime,
            "filename": path.name,
            "parent": str(path.parent),
        }
