# src/ai_coder/worktree_manager/worktree_manager.py
from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass
from pathlib import Path

from ai_coder.setup_config import c_setup_config
from ai_coder.my_utils.env_loader import load_dotenv_once

load_dotenv_once()
setup_config = c_setup_config.get_instance()
logger = setup_config.get_logger()

DEFAULT_WORKTREE_BRANCH_PREFIX = "ralph"  #
DEFAULT_WORKTREE_BRANCH_MAX_LENGTH = 80  #
DEFAULT_WORKTREE_TITLE_FALLBACK = "work"  #


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


@dataclass(frozen=True)
class WorktreeCleanupResult:
    worktree_path: Path
    removed: bool
    preserved: bool
    reason: str
    message: str
    command: tuple[str, ...] = ()
    status_output: str = ""


@dataclass(frozen=True)
class _GitWorktreeCommandResult:
    stdout: str
    stderr: str
    exit_code: int
    error: str = ""

    @property
    def succeeded(self) -> bool:
        return self.exit_code == 0 and not self.error


def i_worktree_sanitize_branch_name(raw_name: str) -> str:
    lowered_name = raw_name.strip().lower()
    safe_name = re.sub(r"[^a-z0-9]+", "-", lowered_name)
    safe_name = re.sub(r"-+", "-", safe_name)
    safe_name = safe_name.strip("-")

    return safe_name or DEFAULT_WORKTREE_TITLE_FALLBACK


def i_worktree_branch_name(
    issue_number: int,
    issue_title: str,
    prefix: str = DEFAULT_WORKTREE_BRANCH_PREFIX,
) -> str:
    if issue_number < 1:  #
        raise ValueError("issue_number must be a positive integer.")  #

    safe_prefix = i_worktree_sanitize_branch_name(prefix)  #
    safe_title = i_worktree_sanitize_branch_name(issue_title)
    branch_prefix = f"{safe_prefix}-issue-{issue_number}-"  #
    available_title_length = DEFAULT_WORKTREE_BRANCH_MAX_LENGTH - len(branch_prefix)  #

    if available_title_length < len(DEFAULT_WORKTREE_TITLE_FALLBACK):  #
        raise ValueError(
            "branch prefix is too long for the configured branch limit."
        )  #

    shortened_title = safe_title[:available_title_length].strip("-")  #

    if not shortened_title:  #
        shortened_title = DEFAULT_WORKTREE_TITLE_FALLBACK  #

    return f"{branch_prefix}{shortened_title}"


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
        resolved_repo_path / ".ai_coder" / "ai_coder_worktrees"
        if worktree_root is None
        else Path(worktree_root)
    )

    logger.info(f"Resolved worktree root: {resolved_worktree_root}")

    worktree_path = resolved_worktree_root / branch_name
    logger.info(f"Resolved worktree path: {worktree_path}")

    command = i_worktree_create_command(
        resolved_repo_path,
        worktree_path,
        branch_name,
    )

    logger.info(f"Prepared Git worktree creation command: {command}")

    try:
        resolved_worktree_root.mkdir(parents=True, exist_ok=True)
    except OSError as error:
        message = f"Failed to prepare Git worktree root: {error}"
        logger.error(message)

        return WorktreeCreateResult(
            repo_path=resolved_repo_path,
            worktree_path=worktree_path,
            branch_name=branch_name,
            command=tuple(command),
            created=False,
            message=message,
        )

    if worktree_path.exists():
        message = f"Failed to create Git worktree because the path already exists: {worktree_path}"
        logger.error(message)
        return WorktreeCreateResult(
            repo_path=resolved_repo_path,
            worktree_path=worktree_path,
            branch_name=branch_name,
            command=tuple(command),
            created=False,
            message=message,
        )

    command_result = _run_worktree_create_command(command)

    if command_result.succeeded:
        message = f"Created Git worktree: {worktree_path}"
        logger.info(message)
        return WorktreeCreateResult(
            repo_path=resolved_repo_path,
            worktree_path=worktree_path,
            branch_name=branch_name,
            command=tuple(command),
            created=True,
            message=message,
        )

    if command_result.error:
        message = f"Failed to run Git worktree command: {command_result.error}"
        logger.error(message)
        return WorktreeCreateResult(
            repo_path=resolved_repo_path,
            worktree_path=worktree_path,
            branch_name=branch_name,
            command=tuple(command),
            created=False,
            message=message,
        )

    git_output = command_result.stderr.strip() or command_result.stdout.strip()
    if not git_output:
        git_output = f"Git exited with code {command_result.exit_code}."

    message = f"Failed to create Git worktree: {git_output}"
    logger.error(message)

    return WorktreeCreateResult(
        repo_path=resolved_repo_path,
        worktree_path=worktree_path,
        branch_name=branch_name,
        command=tuple(command),
        created=False,
        message=message,
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


def i_worktree_cleanup(
    repo_path: str | Path,
    worktree_path: str | Path,
    completed: bool,
    has_uncommitted_changes: bool | None = None,
) -> WorktreeCleanupResult:
    logger.info("START: i_worktree_cleanup")

    resolved_repo_path = Path(repo_path)
    resolved_worktree_path = Path(worktree_path)

    logger.info("Cleanup repository path: %s", resolved_repo_path)
    logger.info("Cleanup worktree path: %s", resolved_worktree_path)
    logger.info("Cleanup completed flag: %s", completed)
    logger.info("Cleanup known dirty flag: %s", has_uncommitted_changes)

    if not completed:
        message = (
            "Preserved worktree: "
            f"{resolved_worktree_path}. "
            "RALPH did not complete, so cleanup was skipped."
        )
        logger.info(message)
        return WorktreeCleanupResult(
            worktree_path=resolved_worktree_path,
            removed=False,
            preserved=True,
            reason="run_incomplete",
            message=message,
        )

    if has_uncommitted_changes is True:
        message = (
            "Preserved worktree: "
            f"{resolved_worktree_path}. "
            "Known uncommitted changes were reported."
        )
        logger.info(message)
        return WorktreeCleanupResult(
            worktree_path=resolved_worktree_path,
            removed=False,
            preserved=True,
            reason="worktree_dirty",
            message=message,
        )

    if has_uncommitted_changes is None:
        status_command = [
            "git",
            "-C",
            str(resolved_worktree_path),
            "status",
            "--porcelain",
        ]
        status_result = _run_worktree_git_command(status_command)

        if not status_result.succeeded:
            git_output = _git_command_message(status_result)
            message = (
                "Preserved worktree: "
                f"{resolved_worktree_path}. "
                "Could not safely verify worktree clean state, so cleanup was skipped. "
                f"{git_output}"
            )
            logger.error(message)
            return WorktreeCleanupResult(
                worktree_path=resolved_worktree_path,
                removed=False,
                preserved=True,
                reason="dirty_state_detection_failed",
                message=message,
                command=tuple(status_command),
                status_output=git_output,
            )

        status_output = status_result.stdout.strip()

        if status_output:
            message = (
                "Preserved worktree: "
                f"{resolved_worktree_path}. "
                "Git detected uncommitted changes."
            )
            logger.info(message)
            return WorktreeCleanupResult(
                worktree_path=resolved_worktree_path,
                removed=False,
                preserved=True,
                reason="worktree_dirty",
                message=message,
                command=tuple(status_command),
                status_output=status_output,
            )

    remove_command = [
        "git",
        "-C",
        str(resolved_repo_path),
        "worktree",
        "remove",
        str(resolved_worktree_path),
    ]
    remove_result = _run_worktree_git_command(remove_command)

    if remove_result.succeeded:
        message = f"Removed clean worktree: {resolved_worktree_path}"
        logger.info(message)
        return WorktreeCleanupResult(
            worktree_path=resolved_worktree_path,
            removed=True,
            preserved=False,
            reason="removed_clean_worktree",
            message=message,
            command=tuple(remove_command),
        )

    git_output = _git_command_message(remove_result)
    message = (
        "Preserved worktree: "
        f"{resolved_worktree_path}. "
        f"Failed to remove clean worktree: {git_output}"
    )
    logger.error(message)

    return WorktreeCleanupResult(
        worktree_path=resolved_worktree_path,
        removed=False,
        preserved=True,
        reason="cleanup_failed",
        message=message,
        command=tuple(remove_command),
    )


def _run_worktree_create_command(
    command: list[str],
) -> _GitWorktreeCommandResult:
    logger.info("Running Git worktree creation command: %s", command)

    try:
        completed_process = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError as error:
        logger.error("Git worktree command failed before completion: %s", error)
        return _GitWorktreeCommandResult(
            stdout="",
            stderr="",
            exit_code=1,
            error=str(error),
        )

    return _GitWorktreeCommandResult(
        stdout=completed_process.stdout or "",
        stderr=completed_process.stderr or "",
        exit_code=completed_process.returncode,
    )


def _run_worktree_git_command(
    command: list[str],
) -> _GitWorktreeCommandResult:
    logger.info("Running Git worktree command: %s", command)

    try:
        completed_process = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError as error:
        logger.error("Git worktree command failed before completion: %s", error)
        return _GitWorktreeCommandResult(
            stdout="",
            stderr="",
            exit_code=1,
            error=str(error),
        )

    return _GitWorktreeCommandResult(
        stdout=completed_process.stdout or "",
        stderr=completed_process.stderr or "",
        exit_code=completed_process.returncode,
    )


def _git_command_message(command_result: _GitWorktreeCommandResult) -> str:
    if command_result.error:
        return command_result.error

    git_output = command_result.stderr.strip() or command_result.stdout.strip()

    if git_output:
        return git_output

    return f"Git exited with code {command_result.exit_code}."
