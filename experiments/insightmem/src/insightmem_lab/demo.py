from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np

from insightmem.store import MemoryMessage


class HashEmbedder:
    identity = "hash|dimensions=64|version=1"

    @staticmethod
    def _vector(text: str) -> np.ndarray:
        digest = hashlib.sha256(text.encode("utf-8")).digest()
        raw = (digest * 3)[:64]
        return np.frombuffer(raw, dtype=np.uint8).astype(np.float32) + 1.0

    def encode_documents(self, texts: list[str]) -> np.ndarray:
        return np.asarray([self._vector(text) for text in texts], dtype=np.float32)

    def encode_queries(self, texts: list[str]) -> np.ndarray:
        return np.asarray([self._vector(text) for text in texts], dtype=np.float32)


def load_sample_messages(project_root: str | Path) -> list[MemoryMessage]:
    path = Path(project_root) / "data" / "sample_messages.json"
    rows = json.loads(path.read_text(encoding="utf-8"))
    return [MemoryMessage(**row) for row in rows]
