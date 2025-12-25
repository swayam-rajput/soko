import hashlib
from pathlib import Path


def file_hash(path: Path, algo: str = "sha256") -> str:
    h = hashlib.new(algo)

    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)

    return h.hexdigest()
