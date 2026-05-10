from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class RepositoryStartResult:
    repo_path: Path
    ready: bool
    message: str


def i_repository_start(repo_path: str | Path | None = None) -> RepositoryStartResult:
    resolved_repo_path = Path.cwd() if repo_path is None else Path(repo_path)

    return RepositoryStartResult(
        repo_path=resolved_repo_path,
        ready=True,
        message="Repository context selected for this tracer-bullet run.",
    )
