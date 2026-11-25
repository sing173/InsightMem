from __future__ import annotations

import json
from pathlib import Path

from .agent import EmailAgent
from .models import AgentConfig, LabeledEmail


def load_labeled_emails(path: str | Path) -> list[LabeledEmail]:
    rows = json.loads(Path(path).read_text(encoding="utf-8"))
    return [LabeledEmail.from_dict(row) for row in rows]


def evaluate(cases: list[LabeledEmail], agent: EmailAgent) -> dict:
    rows = []
    for case in cases:
        result = agent.handle(case.email)
        action_ok = result.action == case.expected_action
        memory_ok = all(
            any(item.startswith(f"{kind}:") for item in result.used_memory)
            for kind in case.required_memory
        )
        writing_ok = case.expected_action != "respond" or all(
            token in result.response for token in case.gold_tokens
        )
        rows.append({
            "email_id": case.email.id,
            "expected_action": case.expected_action,
            "predicted_action": result.action,
            "action_ok": action_ok,
            "memory_ok": memory_ok,
            "writing_ok": writing_ok,
            "used_memory": list(result.used_memory),
            "response": result.response,
        })

    routing_total = len(rows)
    routing_passed = sum(row["action_ok"] for row in rows)
    writing_rows = [row for row, case in zip(rows, cases) if case.expected_action == "respond"]
    memory_rows = [row for row, case in zip(rows, cases) if case.required_memory]
    return {
        "summary": {
            "cases": len(rows),
            "routing_accuracy": _fraction(routing_passed, routing_total),
            "writing_compliance": _fraction(sum(row["writing_ok"] for row in writing_rows), len(writing_rows)),
            "required_memory_recall": _fraction(sum(row["memory_ok"] for row in memory_rows), len(memory_rows)),
        },
        "failures": [
            row for row in rows
            if not (row["action_ok"] and row["memory_ok"] and row["writing_ok"])
        ],
        "cases": rows,
    }


def evaluate_config(cases: list[LabeledEmail], store, user_id: str, config: AgentConfig) -> dict:
    result = evaluate(cases, EmailAgent(store, user_id, config))
    result["config"] = {
        "label": config.label,
        "use_semantic": config.use_semantic,
        "use_episodic": config.use_episodic,
        "use_procedural": config.use_procedural,
    }
    return result


def _fraction(passed: int, total: int) -> dict:
    return {
        "passed": passed,
        "total": total,
        "value": round(passed / total, 4) if total else None,
    }