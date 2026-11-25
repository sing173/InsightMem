from __future__ import annotations

import copy
import json
import re

from .models import MemoryItem

Namespace = tuple[str, ...]


def _tokens(text: str) -> set[str]:
    return set(re.findall(r"[a-z0-9]+|[\u4e00-\u9fff]", text.lower()))


def _as_text(value: dict) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


class LocalStore:
    """Offline store with the put/get/search surface used by LangGraph Store."""

    def __init__(self) -> None:
        self._data: dict[Namespace, dict[str, dict]] = {}

    def put(self, namespace: Namespace, key: str, value: dict) -> None:
        self._data.setdefault(tuple(namespace), {})[key] = copy.deepcopy(value)

    def get(self, namespace: Namespace, key: str) -> MemoryItem | None:
        value = self._data.get(tuple(namespace), {}).get(key)
        return MemoryItem(key, copy.deepcopy(value), 0.0) if value is not None else None

    def search(self, namespace: Namespace, query: str | None = None, limit: int = 10) -> list[MemoryItem]:
        if limit <= 0:
            raise ValueError("limit must be positive")
        records = self._data.get(tuple(namespace), {})
        query_tokens = _tokens(query or "")
        scored: list[MemoryItem] = []
        for key, value in records.items():
            document_tokens = _tokens(_as_text(value))
            if query_tokens:
                score = len(query_tokens & document_tokens) / len(query_tokens | document_tokens)
                if score <= 0:
                    continue
            else:
                score = 0.0
            scored.append(MemoryItem(key, copy.deepcopy(value), score))
        return sorted(scored, key=lambda item: (-item.score, item.key))[:limit]


def seed_memories(store, path, user_id: str) -> None:
    from pathlib import Path

    from .memory import EpisodicMemory, ProceduralMemory, SemanticMemory

    users = json.loads(Path(path).read_text(encoding="utf-8"))["users"]
    memories = users.get(user_id, {})
    semantic = SemanticMemory(store, user_id)
    episodic = EpisodicMemory(store, user_id)
    procedural = ProceduralMemory(store, user_id)
    for item in memories.get("semantic", []):
        semantic.add(item["key"], item["value"])
    for item in memories.get("episodic", []):
        episodic.add(item["key"], item["value"])
    for item in memories.get("procedural", []):
        procedural.add(item["key"], item["value"])