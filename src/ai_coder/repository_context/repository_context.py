"""Repository context discovery and Git safety checks for RALPH.

This module provides the repository-context seam used before RALPH creates a
worktree or builds an agent prompt. It detects the current Git repository,
checks whether the active branch is safe, collects prompt-safe project signals,
and infers the test command for the current project.
"""

from __future__ import annotations

import fnmatch
import subprocess
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

from ai_coder.setup_config import c_setup_config
from ai_coder.my_utils.env_loader import load_dotenv_once

load_dotenv_once()
setup_config = c_setup_config.get_instance()
logger = setup_config.get_logger()

###############################################################################
# constants
SAFE_PROJECT_FILE_NAMES = (
    "pyproject.toml",
    "poetry.lock",
    "README.md",
)

SAFE_PROJECT_DIRECTORY_NAMES = (
    "src",
    "tests",
)

EXCLUDED_DIRECTORY_NAMES = (
    ".git",
    ".venv",
    "venv",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    "node_modules",
    "dist",
    "build",
)

EXCLUDED_FILE_NAMES = (".env",)

EXCLUDED_FILE_PATTERNS = (".env.*",)

GENERATED_DIRECTORY_PATHS = (
    "logs",
    "var/logs",
    "reports",
    "var/reports",
)

GENERATED_FILE_SUFFIXES = (".log",)

LARGE_BINARY_FILE_SUFFIXES = (
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".webp",
    ".ico",
    ".pdf",
    ".zip",
    ".tar",
    ".gz",
    ".7z",
    ".exe",
    ".dll",
    ".so",
    ".dylib",
    ".pyc",
)


@dataclass(frozen=True)
class RepositoryStartResult:
    """Describe whether the host repository is ready for RALPH.

    :ivar repo_path: Resolved repository path, or the attempted path when Git
        root detection fails.
    :vartype repo_path: Path
    :ivar ready: Whether the repository passed the startup safety checks.
    :vartype ready: bool
    :ivar message: Human-readable status or blocking message.
    :vartype message: str
    :ivar active_branch: Current Git branch name when detected.
    :vartype active_branch: str
    :ivar is_clean: Whether ``git status --porcelain`` returned no changes.
    :vartype is_clean: bool
    :ivar status_output: Raw Git status or diagnostic output used for blocking.
    :vartype status_output: str
    :ivar blocked_reason: Stable machine-readable reason when startup is blocked.
    :vartype blocked_reason: str
    """

    repo_path: Path
    ready: bool
    message: str
    active_branch: str = ""
    is_clean: bool = False
    status_output: str = ""
    blocked_reason: str = ""


@dataclass(frozen=True)
class RepositoryContextResult:
    """Store prompt-safe repository details discovered for RALPH.

    :ivar repo_path: Resolved repository path used for context discovery.
    :vartype repo_path: Path
    :ivar package_manager: Detected package manager name, such as ``poetry``.
    :vartype package_manager: str
    :ivar test_command: Configured or inferred test command.
    :vartype test_command: str
    :ivar test_command_source: Source of the test command decision.
    :vartype test_command_source: str
    :ivar project_files: Safe high-level project files and directories.
    :vartype project_files: tuple[str, ...]
    :ivar useful_signals: Human-readable project signals for the agent prompt.
    :vartype useful_signals: tuple[str, ...]
    :ivar prompt_summary: Text summary inserted into the RALPH prompt.
    :vartype prompt_summary: str
    """

    repo_path: Path
    package_manager: str
    test_command: str
    test_command_source: str
    project_files: tuple[str, ...]
    useful_signals: tuple[str, ...]
    prompt_summary: str


@dataclass(frozen=True)
class GitCommandResult:
    """Normalize Git command output for repository-context decisions.

    :ivar stdout: Captured standard output from the Git command.
    :vartype stdout: str
    :ivar stderr: Captured standard error from the Git command.
    :vartype stderr: str
    :ivar exit_code: Process exit code returned by the Git command.
    :vartype exit_code: int
    """

    stdout: str
    stderr: str
    exit_code: int

    @property
    def succeeded(self) -> bool:
        """Return whether the command completed successfully.

        :return: ``True`` when the command exit code is ``0``.
        :rtype: bool
        """

        return self.exit_code == 0


def i_repository_start(repo_path: str | Path | None = None) -> RepositoryStartResult:
    """Validate that a repository is safe before RALPH starts work.

    The startup check resolves the Git repository root, detects the active
    branch, rejects detached ``HEAD`` state, and blocks when the repository has
    uncommitted changes.

    :param repo_path: Optional path inside the target repository. When omitted,
        the current working directory is used.
    :type repo_path: str | Path | None
    :return: Startup result describing readiness or the blocking reason.
    :rtype: RepositoryStartResult
    """

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
    # Run Git inside this repository folder and tell me the current branch name.
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
    # Check whether this Git repository has uncommitted changes.
    clean_state_result = _check_clean_state(detected_repo_root)

    if not clean_state_result.succeeded:
        status_output = _git_diagnostic_output(clean_state_result)
        return _blocked_clean_state_detection_result(
            repo_root=detected_repo_root,
            active_branch=active_branch,
            status_output=status_output,
        )

    status_output = clean_state_result.stdout.strip()

    if status_output:
        return _blocked_dirty_result(
            repo_root=detected_repo_root,
            active_branch=active_branch,
            status_output=status_output,
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
        is_clean=True,
        status_output="",
        blocked_reason="",
    )


def i_repository_context_discover(
    repo_path: str | Path | None = None,
) -> RepositoryContextResult:
    """Discover safe repository facts for the RALPH prompt.

    This function intentionally gathers only high-level, prompt-safe facts. It
    avoids reading arbitrary source content and excludes private, generated, and
    binary-looking paths from context discovery.

    :param repo_path: Optional repository path. When omitted, the current
        working directory is used.
    :type repo_path: str | Path | None
    :return: Repository context result with package, test, and prompt details.
    :rtype: RepositoryContextResult
    """

    resolved_repo_path = _resolve_input_path(repo_path)
    logger.info("Starting repository context discovery: %s", resolved_repo_path)

    configured_test_command = getattr(setup_config, "test_command", "").strip()

    if not resolved_repo_path.exists():
        test_command, test_command_source = _detect_test_command(
            repo_path=resolved_repo_path,
            package_manager="unknown",
            project_files=(),
            configured_test_command=configured_test_command,
        )
        prompt_summary = _build_unavailable_prompt_summary(
            repo_path=resolved_repo_path,
            test_command=test_command,
        )

        return RepositoryContextResult(
            repo_path=resolved_repo_path,
            package_manager="unknown",
            test_command=test_command,
            test_command_source=test_command_source,
            project_files=(),
            useful_signals=("Repository context unavailable",),
            prompt_summary=prompt_summary,
        )

    project_files = _collect_project_files(resolved_repo_path)
    package_manager = _detect_package_manager(project_files)
    test_command, test_command_source = _detect_test_command(
        repo_path=resolved_repo_path,
        package_manager=package_manager,
        project_files=project_files,
        configured_test_command=configured_test_command,
    )
    useful_signals = _collect_useful_signals(
        package_manager=package_manager,
        project_files=project_files,
        test_command=test_command,
    )
    prompt_summary = _build_prompt_summary(
        package_manager=package_manager,
        test_command=test_command,
        project_files=project_files,
        useful_signals=useful_signals,
    )

    return RepositoryContextResult(
        repo_path=resolved_repo_path,
        package_manager=package_manager,
        test_command=test_command,
        test_command_source=test_command_source,
        project_files=project_files,
        useful_signals=useful_signals,
        prompt_summary=prompt_summary,
    )


def _resolve_input_path(repo_path: str | Path | None) -> Path:
    """Resolve an optional repository path without requiring it to exist.

    :param repo_path: User-provided repository path, or ``None`` to use the
        current working directory.
    :type repo_path: str | Path | None
    :return: Absolute path resolved with ``strict=False``.
    :rtype: Path
    """

    if repo_path is None:
        return Path.cwd().resolve(strict=False)

    return Path(repo_path).resolve(strict=False)


def _run_git_command(command: Sequence[str]) -> GitCommandResult:
    """Run a Git command and normalize the process result.

    :param command: Complete command argument sequence to pass to
        :func:`subprocess.run`.
    :type command: Sequence[str]
    :return: Normalized Git command result.
    :rtype: GitCommandResult
    """

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


def _should_exclude_context_path(path: Path, repo_root: Path) -> bool:
    """Return whether a path should be excluded from prompt context.

    :param path: Candidate file or directory path to evaluate.
    :type path: Path
    :param repo_root: Repository root used to compute a relative context path.
    :type repo_root: Path
    :return: ``True`` when the path is private, generated, or not useful for
        prompt-safe repository context.
    :rtype: bool
    """

    relative_path = _relative_context_path(path, repo_root)
    relative_path_text = _normalize_context_path_text(relative_path)
    file_name = path.name
    file_suffix = path.suffix.lower()

    if any(part in EXCLUDED_DIRECTORY_NAMES for part in relative_path.parts):
        return True

    if file_name in EXCLUDED_FILE_NAMES:
        return True

    if any(fnmatch.fnmatch(file_name, pattern) for pattern in EXCLUDED_FILE_PATTERNS):
        return True

    if relative_path_text in GENERATED_DIRECTORY_PATHS:
        return True

    if any(
        relative_path_text.startswith(f"{generated_path}/")
        for generated_path in GENERATED_DIRECTORY_PATHS
    ):
        return True

    if file_suffix in GENERATED_FILE_SUFFIXES:
        return True

    if file_suffix in LARGE_BINARY_FILE_SUFFIXES:
        return True

    return False


def _relative_context_path(path: Path, repo_root: Path) -> Path:
    """Return a path relative to the repository root when possible.

    :param path: Candidate path to make relative.
    :type path: Path
    :param repo_root: Repository root path.
    :type repo_root: Path
    :return: Relative path when ``path`` is inside ``repo_root``; otherwise the
        original path.
    :rtype: Path
    """

    try:
        return path.relative_to(repo_root)
    except ValueError:
        return path


def _normalize_context_path_text(path: Path) -> str:
    """Normalize a path for stable prompt-context filtering.

    :param path: Path to normalize.
    :type path: Path
    :return: POSIX-style path text with leading and trailing slashes removed.
    :rtype: str
    """

    return path.as_posix().strip("/")


def _collect_project_files(repo_path: Path) -> tuple[str, ...]:
    """Collect safe top-level project files and directories.

    :param repo_path: Repository path to inspect.
    :type repo_path: Path
    :return: Tuple of discovered safe project files and directories.
    :rtype: tuple[str, ...]
    """

    project_files: list[str] = []

    for file_name in SAFE_PROJECT_FILE_NAMES:
        candidate_path = repo_path / file_name

        if _should_exclude_context_path(candidate_path, repo_path):
            continue

        if candidate_path.is_file():
            project_files.append(file_name)

    for directory_name in SAFE_PROJECT_DIRECTORY_NAMES:
        candidate_path = repo_path / directory_name

        if _should_exclude_context_path(candidate_path, repo_path):
            continue

        if candidate_path.is_dir():
            project_files.append(f"{directory_name}/")

    return tuple(project_files)


def _detect_package_manager(project_files: tuple[str, ...]) -> str:
    """Infer the project package manager from safe project files.

    :param project_files: Safe files and directories discovered in the project.
    :type project_files: tuple[str, ...]
    :return: Package manager label used by repository context.
    :rtype: str
    """

    if "poetry.lock" in project_files:
        return "poetry"

    if "pyproject.toml" in project_files:
        return "python"

    return "unknown"


def _detect_test_command(
    repo_path: Path,
    package_manager: str,
    project_files: tuple[str, ...],
    configured_test_command: str,
) -> tuple[str, str]:
    """Choose the configured or inferred test command.

    Configured commands take priority over inferred commands.

    :param repo_path: Repository path used for fallback file-system checks.
    :type repo_path: Path
    :param package_manager: Detected package manager label.
    :type package_manager: str
    :param project_files: Safe files and directories discovered in the project.
    :type project_files: tuple[str, ...]
    :param configured_test_command: Test command supplied by configuration.
    :type configured_test_command: str
    :return: Pair of ``(test_command, test_command_source)``.
    :rtype: tuple[str, str]
    """

    if configured_test_command:
        return configured_test_command, "configured"

    has_tests_directory = "tests/" in project_files or (repo_path / "tests").is_dir()
    has_pyproject = (
        "pyproject.toml" in project_files or (repo_path / "pyproject.toml").is_file()
    )

    if package_manager == "poetry" and has_pyproject and has_tests_directory:
        return "poetry run pytest", "inferred_from_poetry"

    if has_tests_directory:
        return "pytest", "inferred_from_tests_dir"

    return "", "unknown"


def _collect_useful_signals(
    package_manager: str,
    project_files: tuple[str, ...],
    test_command: str,
) -> tuple[str, ...]:
    """Build human-readable project signals for the agent prompt.

    :param package_manager: Detected package manager label.
    :type package_manager: str
    :param project_files: Safe files and directories discovered in the project.
    :type project_files: tuple[str, ...]
    :param test_command: Configured or inferred test command.
    :type test_command: str
    :return: Tuple of prompt-safe project signals.
    :rtype: tuple[str, ...]
    """

    signals: list[str] = []

    if "pyproject.toml" in project_files:
        signals.append("Python project")

    if package_manager == "poetry":
        signals.append("Uses Poetry")

    if "pytest" in test_command or "tests/" in project_files:
        signals.append("Uses pytest")

    if "src/" in project_files:
        signals.append("Uses src layout")

    if "tests/" in project_files:
        signals.append("Has tests directory")

    return tuple(signals)


def _build_prompt_summary(
    package_manager: str,
    test_command: str,
    project_files: tuple[str, ...],
    useful_signals: tuple[str, ...],
) -> str:
    """Build the repository-context block for the RALPH prompt.

    :param package_manager: Detected package manager label.
    :type package_manager: str
    :param test_command: Configured or inferred test command.
    :type test_command: str
    :param project_files: Safe files and directories discovered in the project.
    :type project_files: tuple[str, ...]
    :param useful_signals: Prompt-safe project signals.
    :type useful_signals: tuple[str, ...]
    :return: Formatted repository-context prompt summary.
    :rtype: str
    """

    important_files_text = _join_context_values(project_files)
    useful_signals_text = _join_context_values(useful_signals)
    test_command_text = test_command or "unknown"

    return (
        "Repository context:\n"
        f"- Package manager: {package_manager}\n"
        f"- Test command: {test_command_text}\n"
        f"- Important files: {important_files_text}\n"
        f"- Project signals: {useful_signals_text}"
    )


def _build_unavailable_prompt_summary(
    repo_path: Path,
    test_command: str,
) -> str:
    """Build a prompt summary for a missing repository path.

    :param repo_path: Repository path that was requested but does not exist.
    :type repo_path: Path
    :param test_command: Configured or inferred test command, if available.
    :type test_command: str
    :return: Formatted unavailable-context prompt summary.
    :rtype: str
    """

    test_command_text = test_command or "unknown"

    return (
        "Repository context unavailable.\n"
        f"- Repository path: {repo_path}\n"
        "- Package manager: unknown\n"
        f"- Test command: {test_command_text}"
    )


def _join_context_values(values: tuple[str, ...]) -> str:
    """Join context values for display in a prompt summary.

    :param values: Context values to join.
    :type values: tuple[str, ...]
    :return: Comma-separated values, or ``none detected`` when empty.
    :rtype: str
    """

    if not values:
        return "none detected"

    return ", ".join(values)


def _check_clean_state(repo_root: Path) -> GitCommandResult:
    """Run the Git status command used to detect dirty repositories.

    :param repo_root: Git repository root to inspect.
    :type repo_root: Path
    :return: Normalized result from ``git status --porcelain``.
    :rtype: GitCommandResult
    """

    return _run_git_command(
        [
            "git",
            "-C",
            str(repo_root),
            "status",
            "--porcelain",
        ]
    )


def _git_diagnostic_output(result: GitCommandResult) -> str:
    """Choose the most useful diagnostic output from a Git result.

    :param result: Git command result to inspect.
    :type result: GitCommandResult
    :return: ``stderr`` when present; otherwise ``stdout``.
    :rtype: str
    """

    return result.stderr.strip() or result.stdout.strip()


def _blocked_dirty_result(
    repo_root: Path,
    active_branch: str,
    status_output: str,
) -> RepositoryStartResult:
    """Build a blocked startup result for a dirty repository.

    :param repo_root: Detected Git repository root.
    :type repo_root: Path
    :param active_branch: Detected active branch name.
    :type active_branch: str
    :param status_output: Raw ``git status --porcelain`` output.
    :type status_output: str
    :return: Blocked startup result with ``repository_dirty`` reason.
    :rtype: RepositoryStartResult
    """

    message = (
        "Blocked: Repository has uncommitted changes. "
        f"Repository root: {repo_root}. "
        f"Active branch: {active_branch}. "
        "RALPH stopped before worktree creation because the main repository is unsafe. "
        "Commit, stash, or discard the changes, then run RALPH again.\n\n"
        f"Git status output:\n{status_output}"
    )
    logger.error(message)

    return RepositoryStartResult(
        repo_path=repo_root,
        ready=False,
        message=message,
        active_branch=active_branch,
        is_clean=False,
        status_output=status_output,
        blocked_reason="repository_dirty",
    )


def _blocked_clean_state_detection_result(
    repo_root: Path,
    active_branch: str,
    status_output: str,
) -> RepositoryStartResult:
    """Build a blocked result when Git clean-state detection fails.

    :param repo_root: Detected Git repository root.
    :type repo_root: Path
    :param active_branch: Detected active branch name.
    :type active_branch: str
    :param status_output: Git diagnostic output explaining the failure.
    :type status_output: str
    :return: Blocked startup result with ``clean_state_detection_failed`` reason.
    :rtype: RepositoryStartResult
    """

    message = (
        "Blocked: Repository clean-state detection failed. "
        f"Repository root: {repo_root}. "
        f"Active branch: {active_branch}. "
        "RALPH could not safely verify the repository clean state, so it stopped before worktree creation. "
        "Run git status manually and fix the repository state before running RALPH again.\n\n"
        f"Git error output:\n{status_output}"
    )
    logger.error(message)

    return RepositoryStartResult(
        repo_path=repo_root,
        ready=False,
        message=message,
        active_branch=active_branch,
        is_clean=False,
        status_output=status_output,
        blocked_reason="clean_state_detection_failed",
    )


def _blocked_branch_result(repo_root: Path, reason: str) -> RepositoryStartResult:
    """Build a blocked startup result for active-branch detection failure.

    :param repo_root: Detected Git repository root.
    :type repo_root: Path
    :param reason: Diagnostic reason from Git or repository validation.
    :type reason: str
    :return: Blocked startup result for missing active branch information.
    :rtype: RepositoryStartResult
    """

    message = f"Blocked: Could not detect an active Git branch from {repo_root}."
    logger.error("%s Reason: %s", message, reason.strip())

    return RepositoryStartResult(
        repo_path=repo_root,
        ready=False,
        message=message,
        active_branch="",
    )
