from __future__ import annotations

from .memory import EpisodicMemory, ProceduralMemory, SemanticMemory
from .models import AgentConfig, AgentResult, Email
from .store import LocalStore

IGNORE_MARKERS = ("unsubscribe", "newsletter", "promotional", "last chance", "sale ends")
NOTIFY_MARKERS = ("sev-1", "production is down", "suspicious login", "security alert", "urgent outage")
ACTIONS = {"ignore", "notify", "respond"}


def _base_action(email: Email) -> str:
    text = f"{email.sender} {email.subject} {email.body}".lower()
    if any(marker in text for marker in IGNORE_MARKERS):
        return "ignore"
    if any(marker in text for marker in NOTIFY_MARKERS):
        return "notify"
    return "respond"


class EmailAgent:
    def __init__(self, store: LocalStore, user_id: str, config: AgentConfig) -> None:
        self.user_id = user_id
        self.config = config
        self.semantic = SemanticMemory(store, user_id)
        self.episodic = EpisodicMemory(store, user_id)
        self.procedural = ProceduralMemory(store, user_id)

    def handle(self, email: Email) -> AgentResult:
        action = _base_action(email)
        used_memory: list[str] = []
        context: list[str] = []

        if self.config.use_episodic and action == "respond":
            examples = self.episodic.similar(email, limit=2)
            if examples and examples[0].score >= 0.18:
                example = examples[0]
                example_action = str(example.value.get("action", "respond"))
                if example_action in ACTIONS:
                    action = example_action
                    used_memory.append(f"episodic:{example.key}")
                    context.append(f"example={example.key} score={example.score:.3f} action={example_action}")

        if self.config.use_procedural:
            instructions = self.procedural.instructions()
            if instructions:
                context.append(str(instructions.get("prompt", "email-style")))
                used_memory.append("procedural:email-style")
                for rule in instructions.get("rules", []):
                    marker = str(rule.get("sender_contains", "")).lower()
                    rule_action = str(rule.get("action", ""))
                    if marker and marker in email.sender.lower() and rule_action in ACTIONS:
                        action = rule_action

        signature = None
        if self.config.use_semantic and action == "respond":
            facts = self.semantic.recall(f"{email.subject} signature tone", limit=3)
            for fact in facts:
                context.append(f"fact={fact.key} score={fact.score:.3f}")
                if fact.value.get("kind") == "signature":
                    signature = str(fact.value.get("value", "")) or None
                    if signature:
                        used_memory.append(f"semantic:{fact.key}")

        return AgentResult(
            email_id=email.id,
            action=action,
            response=self._write_response(email, action, signature),
            used_memory=tuple(used_memory),
            context="\n".join(context),
        )

    @staticmethod
    def _write_response(email: Email, action: str, signature: str | None) -> str:
        if action == "ignore":
            return ""
        if action == "notify":
            return f"Notification queued: {email.subject}"
        if signature:
            return f"Hi,\n\nThanks for the note about \"{email.subject}\". I'll follow up shortly.\n\n{signature}"
        return (
            f"Hi,\n\nThank you for your email about \"{email.subject}\". "
            "I will review it and follow up with you shortly.\n\nBest,"
        )