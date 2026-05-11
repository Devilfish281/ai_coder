# src/ai_coder/worktree_manager/worktree_manager.py
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

# logger & setup_config
from ai_coder.setup_config import c_setup_config
from ai_coder.my_utils.env_loader import load_dotenv_once

load_dotenv_once()
setup_config = c_setup_config.get_instance()
logger = setup_config.get_logger()


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
    return f"{prefix}-issue-{issue_number}-{safe_title}"  #  Changed Code


def i_worktree_create_command(
    repo_path: str | Path,
    worktree_path: str | Path,
    branch_name: str,
) -> list[str]:
    logger.info("START: i_worktree_create_command")
    logger.info("Preparing Git worktree creation command.")
    logger.info(f"Input repository path: {repo_path}")
    logger.info(f"Input worktree path: {worktree_path}")
    logger.info(f"Input branch name: {branch_name}")

    # git -C C:\Users\ME\Documents\Python\2026\Projects\ai_coder\.ai_coder worktree add -b ralph/issue-1-confirm-release-1-runtime-contract C:\Users\ME\Documents\Python\2026\Projects\ai_coder_worktrees\ralph-issue-1-confirm-release-1-runtime-contract
    #  -C  = Git, pretend you are inside this repository folder.
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
    logger.info("START: i_worktree_create")
    logger.info("Preparing to create Git worktree for the selected issue.")
    logger.info(f"Input repository path: {repo_path}")
    logger.info(f"Input issue number: {issue_number}")
    logger.info(f"Input issue title: {issue_title}")
    logger.info(f"Input worktree root: {worktree_root}")

    resolved_repo_path = Path(repo_path)
    branch_name = i_worktree_branch_name(issue_number, issue_title)
    resolved_worktree_root = (
        resolved_repo_path / ".ai_coder" / "ai_coder_worktrees"  #  Changed Code
        if worktree_root is None
        else Path(worktree_root)
    )

    logger.info(f"Resolved worktree root: {resolved_worktree_root}")

    worktree_path = resolved_worktree_root / i_worktree_sanitize_branch_name(
        branch_name
    )
    logger.info(f"Resolved worktree path: {worktree_path}")

    command = i_worktree_create_command(
        resolved_repo_path,
        worktree_path,
        branch_name,
    )

    # 'git', '-C', 'C:\\Users\\ME\\Documents\\Python\\2026\\Projects\\ai_coder', 'worktree', 'add', '-b', 'ralph-issue-1-minimal-local-ralph-loop', 'C:\\Users\\ME\\Documents\\Python\\2026\\Projects\\ai_coder\\.ai_coder\\ai_coder_worktrees\\ralph-issue-1-minimal-local-ralph-loop'

    # Go to my ai_coder repository.
    # Create a new Git worktree.
    # Create a new branch named ralph-issue-1-minimal-local-ralph-loop.
    # Put that branch into a new folder inside .ai_coder\ai_coder_worktrees.

    # Git says -C <path> means “run Git as if Git was started in that folder,” so your -C path should be the real repo root:
    # C:\Users\ME\Documents\Python\2026\Projects\ai_coder

    # 'worktree'  Use the Git worktree feature.
    # 'add' Create a new worktree.
    # '-b' Create a new branch. The next text is the new branch name.
    # Worktree path
    # C:\Users\ME\Documents\Python\2026\Projects\ai_coder\.ai_coder\ai_coder_worktrees\ralph-issue-1-minimal-local-ralph-loop
    # This is the new folder Git will create.

    logger.info(f"Prepared Git worktree creation command: {command}")

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
    logger.info("START: i_worktree_preserve")

    if has_uncommitted_changes:
        logger.info("Uncommitted changes detected. Preserving worktree.")
        logger.info(
            "Preservation needed due to uncommitted changes. Worktree will be preserved."
        )
        logger.info("Stubbed preservation logic.")
        return WorktreePreserveResult(
            preserved=True,
            reason="Preserved because uncommitted changes were detected.",
        )

    if not completed:
        logger.info("RALPH stopped before completion. Preserving worktree.")
        logger.info("Stubbed preservation logic.")
        return WorktreePreserveResult(
            preserved=True,
            reason="Preserved because RALPH stopped before completion.",
        )

    logger.info("No preservation needed. Worktree will not be preserved.")
    return WorktreePreserveResult(
        preserved=False,
        reason="No preservation needed after successful completion.",
    )
