import os
from pathlib import Path
import pdfplumber
import json
import csv
import logging
logging.getLogger('pdfminer').setLevel(logging.ERROR)


class Document:
    def __init__(self, path: Path, text: str, meta: dict):
        self.path = path
        self.text = text
        self.meta = meta                # size, modified time, extension etc.
    def __repr__(self):
        return f"{self.path}, {self.meta['size']} bytes, {self.meta['modified']}, {self.meta['extension']}, {self.meta['filename']}, {self.meta['parent']}"

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
        ".json":"json"
    }

    def __init__(self, directory: str):
        self.directory = Path(directory)

    def load(self):
        docs = []
        for file_path in self.directory.rglob("*"):
            if not file_path.is_file():
                continue

            ext = file_path.suffix.lower()
            if ext not in self.SUPPORTED:
                continue

            loader_type = self.SUPPORTED[ext]
            text = self._dispatch(file_path, loader_type)

            if text and text.strip():
                meta = self._build_metadata(file_path)
                docs.append(Document(file_path, text, meta))

        return docs


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
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                return f.read()
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
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                return f.read()
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
            "extension":  path.suffix.lower(),
            "size":       stat.st_size,
            "modified":   stat.st_mtime,
            "filename":   path.name,
            "parent":     str(path.parent)
        }

# document = DirectoryLoader('data/').load()
# print(document)