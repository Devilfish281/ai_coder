# src/ai_coder/repository_context/repository_context.py
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
class RepositoryStartResult:
    repo_path: Path
    ready: bool
    message: str
    active_branch: str = ""


@dataclass(frozen=True)
class GitCommandResult:
    stdout: str
    stderr: str
    exit_code: int

    @property
    def succeeded(self) -> bool:
        return self.exit_code == 0


def i_repository_start(repo_path: str | Path | None = None) -> RepositoryStartResult:
    resolved_input_path = _resolve_input_path(repo_path)
    logger.info("Started repository context selection.")
    logger.info("Resolving repository path: %s", resolved_input_path)

    root_result = _run_git_command(
        [
            "git",
            "-C",
            str(resolved_input_path),
            "rev-parse",
            "--show-toplevel",
        ]
    )

    if not root_result.succeeded:
        message = (
            "Blocked: Could not detect a Git repository root from "
            f"{resolved_input_path}."
        )
        logger.error("%s Git stderr: %s", message, root_result.stderr.strip())
        return RepositoryStartResult(
            repo_path=resolved_input_path,
            ready=False,
            message=message,
            active_branch="",
        )

    repo_root_text = root_result.stdout.strip()

    if not repo_root_text:
        message = (
            "Blocked: Could not detect a Git repository root from "
            f"{resolved_input_path}."
        )
        logger.error("%s Git stdout was empty.", message)
        return RepositoryStartResult(
            repo_path=resolved_input_path,
            ready=False,
            message=message,
            active_branch="",
        )

    detected_repo_root = Path(repo_root_text)
    logger.info("Detected Git repository root: %s", detected_repo_root)

    branch_result = _run_git_command(
        [
            "git",
            "-C",
            str(detected_repo_root),
            "rev-parse",
            "--abbrev-ref",
            "HEAD",
        ]
    )

    if not branch_result.succeeded:
        return _blocked_branch_result(detected_repo_root, branch_result.stderr)

    active_branch = branch_result.stdout.strip()

    if not active_branch:
        return _blocked_branch_result(
            detected_repo_root,
            "Git branch command returned empty stdout.",
        )

    if active_branch == "HEAD":
        return _blocked_branch_result(
            detected_repo_root,
            "Repository is in detached HEAD state.",
        )

    message = (
        "Repository context discovered. "
        f"Repository root: {detected_repo_root}. "
        f"Active branch: {active_branch}."
    )
    logger.info(message)

    return RepositoryStartResult(
        repo_path=detected_repo_root,
        ready=True,
        message=message,
        active_branch=active_branch,
    )


def _resolve_input_path(repo_path: str | Path | None) -> Path:
    if repo_path is None:
        return Path.cwd().resolve(strict=False)

    return Path(repo_path).resolve(strict=False)


def _run_git_command(command: Sequence[str]) -> GitCommandResult:
    logger.info("Running Git repository context command: %s", list(command))

    try:
        completed_process = subprocess.run(
            list(command),
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError as error:
        logger.error("Git command failed before completion: %s", error)
        return GitCommandResult(
            stdout="",
            stderr=str(error),
            exit_code=1,
        )

    return GitCommandResult(
        stdout=completed_process.stdout or "",
        stderr=completed_process.stderr or "",
        exit_code=completed_process.returncode,
    )


def _blocked_branch_result(repo_root: Path, reason: str) -> RepositoryStartResult:
    message = f"Blocked: Could not detect an active Git branch from {repo_root}."
    logger.error("%s Reason: %s", message, reason.strip())

    return RepositoryStartResult(
        repo_path=repo_root,
        ready=False,
        message=message,
        active_branch="",
    )
