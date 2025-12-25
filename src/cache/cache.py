import hashlib
from typing import Optional

class AnswerCache:
    def __init__(self):
        self._store = {}

    def _key(self, question: str, context: str) -> str:
        data = (question + context).encode("utf-8")
        return hashlib.sha256(data).hexdigest()

    def get(self, question: str, context: str) -> Optional[str]:
        return self._store.get(self._key(question, context))

    def set(self, question: str, context: str, answer: str):
        self._store[self._key(question, context)] = answer
