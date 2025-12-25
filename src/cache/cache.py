import sqlite3
import hashlib
import time
from pathlib import Path
from typing import Optional

DB_PATH = Path("data/cache-db/cache.db")


class Cache:
    def __init__(self):
        DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(DB_PATH)
        self._init_db()

    def _init_db(self):
        self.conn.execute(
            """
            CREATE TABLE IF NOT EXISTS cache (
                key TEXT PRIMARY KEY,
                answer TEXT NOT NULL,
                model TEXT,
                created_at REAL
            )
            """
        )
        self.conn.commit()

    @staticmethod
    def make_key(question: str, context: str) -> str:
        payload = f"{question.strip()}||{context.strip()}"
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    def get(self, key: str) -> Optional[str]:
        cur = self.conn.execute(
            "SELECT answer FROM cache WHERE key = ?",
            (key,)
        )
        row = cur.fetchone()
        return row[0] if row else None

    def set(self, key: str, answer: str, model: str):
        self.conn.execute(
            """
            INSERT OR REPLACE INTO cache (key, answer, model, created_at)
            VALUES (?, ?, ?, ?)
            """,
            (key, answer, model, time.time())
        )
        self.conn.commit()

    def clear(self):
        self.conn.execute("DELETE FROM cache")
        self.conn.commit()
    
    def size(self) -> int:
        cur = self.conn.execute("SELECT COUNT(*) FROM cache")
        return cur.fetchone()[0]
