from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class WorktreeCreateResult:
    repo_path: Path
    worktree_path: Path
    branch_name: str
    command: tuple[str, ...]
    created: bool
    message: str


@dataclass(frozen=True)
class WorktreePreserveResult:
    preserved: bool
    reason: str


def i_worktree_sanitize_branch_name(raw_name: str) -> str:
    lowered_name = raw_name.strip().lower()
    safe_name = re.sub(r"[^a-z0-9._/-]+", "-", lowered_name)
    safe_name = re.sub(r"[-/]+", "-", safe_name)
    safe_name = safe_name.strip("-./")

    return safe_name or "ralph-work"


def i_worktree_branch_name(
    issue_number: int,
    issue_title: str,
    prefix: str = "ralph",
) -> str:
    safe_title = i_worktree_sanitize_branch_name(issue_title)
    return f"{prefix}/issue-{issue_number}-{safe_title}"


def i_worktree_create_command(
    repo_path: str | Path,
    worktree_path: str | Path,
    branch_name: str,
) -> list[str]:
    return [
        "git",
        "-C",
        str(repo_path),
        "worktree",
        "add",
        "-b",
        branch_name,
        str(worktree_path),
    ]


def i_worktree_create(
    repo_path: str | Path,
    issue_number: int,
    issue_title: str,
    worktree_root: str | Path | None = None,
) -> WorktreeCreateResult:
    resolved_repo_path = Path(repo_path)
    branch_name = i_worktree_branch_name(issue_number, issue_title)
    resolved_worktree_root = (
        resolved_repo_path.parent / "ai_coder_worktrees"
        if worktree_root is None
        else Path(worktree_root)
    )
    worktree_path = resolved_worktree_root / i_worktree_sanitize_branch_name(
        branch_name
    )
    command = i_worktree_create_command(
        resolved_repo_path,
        worktree_path,
        branch_name,
    )

    return WorktreeCreateResult(
        repo_path=resolved_repo_path,
        worktree_path=worktree_path,
        branch_name=branch_name,
        command=tuple(command),
        created=False,
        message="Worktree creation is stubbed in this tracer-bullet slice.",
    )


def i_worktree_preserve(
    completed: bool,
    has_uncommitted_changes: bool = False,
) -> WorktreePreserveResult:
    if has_uncommitted_changes:
        return WorktreePreserveResult(
            preserved=True,
            reason="Preserved because uncommitted changes were detected.",
        )

    if not completed:
        return WorktreePreserveResult(
            preserved=True,
            reason="Preserved because RALPH stopped before completion.",
        )

    return WorktreePreserveResult(
        preserved=False,
        reason="No preservation needed after successful completion.",
    )
