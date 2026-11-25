from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

Action = Literal["ignore", "notify", "respond"]
MemoryKind = Literal["semantic", "episodic", "procedural"]


@dataclass(frozen=True)
class Email:
    id: str
    sender: str
    subject: str
    body: str
    received_at: str | None = None

    @classmethod
    def from_dict(cls, data: dict) -> "Email":
        return cls(**data)


@dataclass(frozen=True)
class LabeledEmail:
    email: Email
    expected_action: Action
    required_memory: tuple[MemoryKind, ...] = ()
    gold_tokens: tuple[str, ...] = ()

    @classmethod
    def from_dict(cls, data: dict) -> "LabeledEmail":
        return cls(
            email=Email.from_dict(data["email"]),
            expected_action=data["expected_action"],
            required_memory=tuple(data.get("required_memory", ())),
            gold_tokens=tuple(data.get("gold_tokens", ())),
        )


@dataclass(frozen=True)
class AgentConfig:
    use_semantic: bool = False
    use_episodic: bool = False
    use_procedural: bool = False

    @property
    def label(self) -> str:
        enabled = [
            name
            for name, active in (
                ("semantic", self.use_semantic),
                ("episodic", self.use_episodic),
                ("procedural", self.use_procedural),
            )
            if active
        ]
        return "+".join(enabled) if enabled else "baseline"


@dataclass(frozen=True)
class MemoryItem:
    key: str
    value: dict
    score: float = 0.0


@dataclass(frozen=True)
class AgentResult:
    email_id: str
    action: Action
    response: str
    used_memory: tuple[str, ...] = ()
    context: str = ""