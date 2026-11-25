from __future__ import annotations

import json
import platform
import re
import subprocess
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from insightmem.coding.config import CodingConfig
from insightmem.coding.service import CodingMemoryService
from insightmem.store import MemoryMessage

from .demo import HashEmbedder


def _write_json(path: Path, payload: dict) -> None:
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _git_commit(project_root: Path) -> str | None:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=project_root,
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError:
        return None
    return result.stdout.strip() if result.returncode == 0 else None


@dataclass(frozen=True)
class ExperimentRun:
    run_id: str
    directory: Path
    database_path: Path
    _service: CodingMemoryService = field(repr=False)

    def add(self, request_id: str, user_id: str, session_id: str, messages: list[MemoryMessage]) -> int:
        return self._service.add(request_id, user_id, session_id, messages)

    def search(self, user_id: str, query: str, top_k: int = 5) -> list[dict]:
        return [asdict(hit) for hit in self._service.search(user_id, query, top_k)]

    def stats(self) -> dict:
        return self._service.stats()

    def save(self, filename: str, payload: dict) -> Path:
        if not filename or Path(filename).name != filename or filename in {".", ".."}:
            raise ValueError("filename must be a plain file name")
        path = self.directory / filename
        _write_json(path, payload)
        return path


def start_experiment(
    project_root: str | Path,
    name: str,
    *,
    config: CodingConfig | None = None,
    embedder=None,
) -> ExperimentRun:
    root = Path(project_root).resolve()
    if root.name == "notebooks":
        root = root.parent
    selected_config = config or CodingConfig()
    selected_embedder = embedder or HashEmbedder()
    safe_name = re.sub(r"[^A-Za-z0-9_-]+", "-", name).strip("-") or "run"
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    run_id = f"{stamp}-{safe_name}-{uuid4().hex[:8]}"
    directory = root / "runs" / run_id
    directory.mkdir(parents=True, exist_ok=False)
    database_path = directory / "memory.sqlite3"
    service = CodingMemoryService(database_path, selected_embedder, selected_config)
    _write_json(directory / "manifest.json", {
        "run_id": run_id,
        "run_name": name,
        "project": root.name,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "code_commit": _git_commit(root),
        "python": platform.python_version(),
        "platform": platform.platform(),
        "config": asdict(selected_config),
        "embedding": service.identity,
        "database": database_path.name,
    })
    return ExperimentRun(run_id, directory, database_path, service)
