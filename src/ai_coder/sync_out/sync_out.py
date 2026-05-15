# src/ai_coder/sync_out/sync_out.py
from __future__ import annotations

import subprocess
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

from ai_coder.setup_config import c_setup_config
from ai_coder.my_utils.env_loader import load_dotenv_once

load_dotenv_once()
setup_config = c_setup_config.get_instance()
logger = setup_config.get_logger()


@dataclass(frozen=True)
class SyncOutResult:
    source_path: Path
    target_path: Path
    changed: bool


@dataclass(frozen=True)
class GitCommandResult:
    command: tuple[str, ...]
    stdout: str
    stderr: str
    exit_code: int

    @property
    def succeeded(self) -> bool:
        return self.exit_code == 0

    @property
    def failed(self) -> bool:
        return not self.succeeded


@dataclass(frozen=True)
class SyncMergeResult:
    merged: bool
    message: str
    failed: bool = False
    committed: bool = False
    commit_hash: str = ""
    worktree_path: Path | None = None
    has_changes: bool = False
    has_uncommitted_changes: bool = False
    status_output: str = ""
    command: tuple[str, ...] = ()
    stdout: str = ""
    stderr: str = ""
    exit_code: int = 0


def i_sync_out_run(source_path: str | Path, target_path: str | Path) -> SyncOutResult:
    return SyncOutResult(
        source_path=Path(source_path),
        target_path=Path(target_path),
        changed=False,
    )


def i_sync_out_merge(
    completed: bool,
    worktree_path: str | Path | None = None,
    issue_number: int | None = None,
    issue_title: str = "",
    commit_message_template: str | None = None,
) -> SyncMergeResult:
    logger.info("Starting sync or merge process.")

    resolved_worktree_path = None if worktree_path is None else Path(worktree_path)

    if not completed:
        logger.info("Skipping sync or merge because RALPH did not complete.")
        return SyncMergeResult(
            merged=False,
            committed=False,
            worktree_path=resolved_worktree_path,
            message="Skipped sync or merge because RALPH did not complete.",
        )

    if resolved_worktree_path is None:
        logger.info("Sync or merge is stubbed in this tracer-bullet slice.")
        return SyncMergeResult(
            merged=False,
            committed=False,
            message="Sync or merge is stubbed in this tracer-bullet slice.",
        )

    commit_message_result = _format_commit_message_result(
        issue_number=issue_number,
        issue_title=issue_title,
        commit_message_template=commit_message_template,
    )

    if commit_message_result.failed:
        return SyncMergeResult(
            merged=False,
            committed=False,
            failed=True,
            worktree_path=resolved_worktree_path,
            message=commit_message_result.message,
        )

    initial_status_result = _get_git_status(resolved_worktree_path)

    if initial_status_result.failed:
        return _failed_sync_result(
            worktree_path=resolved_worktree_path,
            command_result=initial_status_result,
            message_prefix="Failed to inspect worktree changes before commit.",
        )

    initial_status_output = initial_status_result.stdout.strip()

    if not initial_status_output:
        message = f"No changes found to commit in worktree: {resolved_worktree_path}"
        logger.info(message)
        return SyncMergeResult(
            merged=False,
            committed=False,
            worktree_path=resolved_worktree_path,
            has_changes=False,
            status_output="",
            command=initial_status_result.command,
            stdout=initial_status_result.stdout,
            stderr=initial_status_result.stderr,
            exit_code=initial_status_result.exit_code,
            message=message,
        )

    add_result = _run_git_command(
        [
            "git",
            "-C",
            str(resolved_worktree_path),
            "add",
            "-A",
        ]
    )

    if add_result.failed:
        return _failed_sync_result(
            worktree_path=resolved_worktree_path,
            command_result=add_result,
            message_prefix="Failed to stage worktree changes before commit.",
            status_output=initial_status_output,
        )

    commit_result = _run_git_command(
        [
            "git",
            "-C",
            str(resolved_worktree_path),
            "commit",
            "-m",
            commit_message_result.message,
        ]
    )

    if commit_result.failed:
        return _failed_sync_result(
            worktree_path=resolved_worktree_path,
            command_result=commit_result,
            message_prefix="Commit failed.",
            status_output=initial_status_output,
        )

    commit_hash_result = _run_git_command(
        [
            "git",
            "-C",
            str(resolved_worktree_path),
            "rev-parse",
            "HEAD",
        ]
    )

    if commit_hash_result.failed:
        return _failed_sync_result(
            worktree_path=resolved_worktree_path,
            command_result=commit_hash_result,
            message_prefix="Commit was created, but RALPH could not read the commit hash.",
            status_output=initial_status_output,
            committed=True,
        )

    commit_hash = commit_hash_result.stdout.strip()

    final_status_result = _get_git_status(resolved_worktree_path)

    if final_status_result.failed:
        return _failed_sync_result(
            worktree_path=resolved_worktree_path,
            command_result=final_status_result,
            message_prefix="Commit was created, but RALPH could not verify final worktree state.",
            status_output=initial_status_output,
            committed=True,
            commit_hash=commit_hash,
        )

    final_status_output = final_status_result.stdout.strip()
    has_uncommitted_changes = bool(final_status_output)

    message = _build_commit_success_message(
        commit_hash=commit_hash,
        worktree_path=resolved_worktree_path,
        has_uncommitted_changes=has_uncommitted_changes,
    )

    logger.info(message)

    return SyncMergeResult(
        merged=True,
        committed=True,
        failed=False,
        commit_hash=commit_hash,
        worktree_path=resolved_worktree_path,
        has_changes=True,
        has_uncommitted_changes=has_uncommitted_changes,
        status_output=final_status_output,
        command=commit_result.command,
        stdout=commit_result.stdout,
        stderr=commit_result.stderr,
        exit_code=commit_result.exit_code,
        message=message,
    )


@dataclass(frozen=True)
class CommitMessageResult:
    message: str
    failed: bool = False


def _format_commit_message_result(
    issue_number: int | None,
    issue_title: str,
    commit_message_template: str | None,
) -> CommitMessageResult:
    template = commit_message_template or setup_config.commit_message_template

    try:
        commit_message = template.format(
            issue_number=issue_number or 0,
            issue_title=issue_title,
        )
    except (KeyError, IndexError, ValueError) as error:
        return CommitMessageResult(
            message=f"Commit message formatting failed: {error}",
            failed=True,
        )

    cleaned_commit_message = commit_message.strip()

    if not cleaned_commit_message:
        return CommitMessageResult(
            message="Commit message formatting failed: commit message is empty.",
            failed=True,
        )

    return CommitMessageResult(message=cleaned_commit_message)


def _get_git_status(worktree_path: Path) -> GitCommandResult:
    return _run_git_command(
        [
            "git",
            "-C",
            str(worktree_path),
            "status",
            "--porcelain",
        ]
    )


def _run_git_command(command: Sequence[str]) -> GitCommandResult:
    command_parts = tuple(str(part) for part in command)
    logger.info("Running Git sync_out command: %s", list(command_parts))

    try:
        completed_process = subprocess.run(
            list(command_parts),
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError as error:
        logger.error("Git sync_out command failed before completion: %s", error)
        return GitCommandResult(
            command=command_parts,
            stdout="",
            stderr=str(error),
            exit_code=1,
        )

    return GitCommandResult(
        command=command_parts,
        stdout=completed_process.stdout or "",
        stderr=completed_process.stderr or "",
        exit_code=completed_process.returncode,
    )


def _failed_sync_result(
    worktree_path: Path,
    command_result: GitCommandResult,
    message_prefix: str,
    status_output: str = "",
    committed: bool = False,
    commit_hash: str = "",
) -> SyncMergeResult:
    diagnostic_text = command_result.stderr.strip() or command_result.stdout.strip()
    message = message_prefix

    if diagnostic_text:
        message = f"{message} {diagnostic_text}"

    logger.error(message)

    return SyncMergeResult(
        merged=False,
        committed=committed,
        failed=True,
        commit_hash=commit_hash,
        worktree_path=worktree_path,
        has_changes=bool(status_output.strip()),
        has_uncommitted_changes=True,
        status_output=status_output,
        command=command_result.command,
        stdout=command_result.stdout,
        stderr=command_result.stderr,
        exit_code=command_result.exit_code,
        message=message,
    )


def _build_commit_success_message(
    commit_hash: str,
    worktree_path: Path,
    has_uncommitted_changes: bool,
) -> str:
    message = f"Commit created: {commit_hash}. Worktree: {worktree_path}."

    if has_uncommitted_changes:
        return f"{message} Worktree still has uncommitted changes after commit."

    return f"{message} Worktree is clean after commit."
