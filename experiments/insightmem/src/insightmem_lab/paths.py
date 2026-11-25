from pathlib import Path


def find_project_root(start: str | Path | None = None) -> Path:
    candidate = Path(start or Path.cwd()).resolve()
    if candidate.is_file():
        candidate = candidate.parent
    for directory in (candidate, *candidate.parents):
        if (directory / "src" / "insightmem_lab").is_dir() and (directory / "notebooks").is_dir():
            return directory
        nested = directory / "experiments" / "insightmem"
        if (nested / "src" / "insightmem_lab").is_dir() and (nested / "notebooks").is_dir():
            return nested
    raise FileNotFoundError("open this notebook from the repository root or the InsightMem experiment project")
