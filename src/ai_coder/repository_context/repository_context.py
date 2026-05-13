# src/ai_coder/repository_context/repository_context.py
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
    repo_path: Path
    ready: bool
    message: str
    active_branch: str = ""
    is_clean: bool = False
    status_output: str = ""
    blocked_reason: str = ""


@dataclass(frozen=True)
class RepositoryContextResult:
    repo_path: Path
    package_manager: str
    test_command: str
    test_command_source: str
    project_files: tuple[str, ...]
    useful_signals: tuple[str, ...]
    prompt_summary: str


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


def _should_exclude_context_path(path: Path, repo_root: Path) -> bool:
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
    try:
        return path.relative_to(repo_root)
    except ValueError:
        return path


def _normalize_context_path_text(path: Path) -> str:
    return path.as_posix().strip("/")


def _collect_project_files(repo_path: Path) -> tuple[str, ...]:
    project_files: list[str] = []

    for file_name in SAFE_PROJECT_FILE_NAMES:
        candidate_path = repo_path / file_name

        if _should_exclude_context_path(candidate_path, repo_path):
            continue

        if candidate_path.is_file():  #  Changed Code
            project_files.append(file_name)

    for directory_name in SAFE_PROJECT_DIRECTORY_NAMES:
        candidate_path = repo_path / directory_name

        if _should_exclude_context_path(candidate_path, repo_path):
            continue

        if candidate_path.is_dir():  #  Changed Code
            project_files.append(f"{directory_name}/")

    return tuple(project_files)


def _detect_package_manager(project_files: tuple[str, ...]) -> str:
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
    test_command_text = test_command or "unknown"

    return (
        "Repository context unavailable.\n"
        f"- Repository path: {repo_path}\n"
        "- Package manager: unknown\n"
        f"- Test command: {test_command_text}"
    )


def _join_context_values(values: tuple[str, ...]) -> str:
    if not values:
        return "none detected"

    return ", ".join(values)


def _check_clean_state(repo_root: Path) -> GitCommandResult:
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
    return result.stderr.strip() or result.stdout.strip()


def _blocked_dirty_result(
    repo_root: Path,
    active_branch: str,
    status_output: str,
) -> RepositoryStartResult:
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
    message = (
        "Blocked: Repository clean-state detection failed. "
        f"Repository root: {repo_root}. "
        f"Active branch: {active_branch}. "
        "RALPH could not safely verify the repository clean state, so it stopped before worktree creation. "  #  Changed Code
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
    message = f"Blocked: Could not detect an active Git branch from {repo_root}."
    logger.error("%s Reason: %s", message, reason.strip())

    return RepositoryStartResult(
        repo_path=repo_root,
        ready=False,
        message=message,
        active_branch="",
    )
