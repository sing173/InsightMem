from __future__ import annotations

from .models import Email, MemoryItem


class SemanticMemory:
    def __init__(self, store, user_id: str) -> None:
        self.store = store
        self.namespace = ("email", "semantic", user_id)

    def add(self, key: str, value: dict) -> None:
        self.store.put(self.namespace, key, value)

    def recall(self, query: str, limit: int = 3) -> list[MemoryItem]:
        return self.store.search(self.namespace, query=query, limit=limit)


class EpisodicMemory:
    def __init__(self, store, user_id: str) -> None:
        self.store = store
        self.namespace = ("email", "episodic", user_id)

    def add(self, key: str, value: dict) -> None:
        self.store.put(self.namespace, key, value)

    def similar(self, email: Email, limit: int = 2) -> list[MemoryItem]:
        query = f"{email.sender} {email.subject} {email.body}"
        return self.store.search(self.namespace, query=query, limit=limit)


class ProceduralMemory:
    def __init__(self, store, user_id: str) -> None:
        self.store = store
        self.namespace = ("email", "procedural", user_id)

    def add(self, key: str, value: dict) -> None:
        self.store.put(self.namespace, key, value)

    def instructions(self) -> dict | None:
        item = self.store.get(self.namespace, "email-style")
        return item.value if item else None