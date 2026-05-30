# src/ai_coder/project_setup/project_setup.py
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ai_coder.sandbox_provider import CommandResult


from ai_coder.my_utils.env_loader import load_dotenv_once
from ai_coder.setup_config import c_setup_config

load_dotenv_once()
setup_config = c_setup_config.get_instance()


@dataclass(frozen=True)
class ProjectSetupResult:
    """
    Store the result of the project setup baseline check.

    :ivar poetry_project: Whether the worktree contains ``pyproject.toml``.
    :vartype poetry_project: bool
    :ivar install_ran: Whether ``poetry install`` was run.
    :vartype install_ran: bool
    :ivar install_passed: Whether ``poetry install`` passed.
    :vartype install_passed: bool
    :ivar baseline_tests_ran: Whether baseline ``poetry run pytest`` was run.
    :vartype baseline_tests_ran: bool
    :ivar baseline_tests_passed: Whether baseline ``poetry run pytest`` passed.
    :vartype baseline_tests_passed: bool
    :ivar blocked: Whether setup should block RALPH from continuing.
    :vartype blocked: bool
    :ivar install_command: Command used for dependency installation.
    :vartype install_command: tuple[str, ...]
    :ivar install_stdout: Standard output from dependency installation.
    :vartype install_stdout: str
    :ivar install_stderr: Standard error from dependency installation.
    :vartype install_stderr: str
    :ivar install_exit_code: Exit code from dependency installation.
    :vartype install_exit_code: int
    :ivar baseline_test_command: Command used for baseline tests.
    :vartype baseline_test_command: tuple[str, ...]
    :ivar baseline_test_stdout: Standard output from baseline tests.
    :vartype baseline_test_stdout: str
    :ivar baseline_test_stderr: Standard error from baseline tests.
    :vartype baseline_test_stderr: str
    :ivar baseline_test_exit_code: Exit code from baseline tests.
    :vartype baseline_test_exit_code: int
    :ivar message: Human-readable setup result message.
    :vartype message: str
    """

    poetry_project: bool
    install_ran: bool = False
    install_passed: bool = False
    baseline_tests_ran: bool = False
    baseline_tests_passed: bool = False
    blocked: bool = False
    install_command: tuple[str, ...] = ()
    install_stdout: str = ""
    install_stderr: str = ""
    install_exit_code: int = 0
    baseline_test_command: tuple[str, ...] = ()
    baseline_test_stdout: str = ""
    baseline_test_stderr: str = ""
    baseline_test_exit_code: int = 0
    message: str = ""


def i_project_setup_run(
    worktree_path: str | Path,
    sandbox_handle: Any | None,
) -> ProjectSetupResult:
    """
    Run the baseline project setup commands for a fresh worktree.

    This function detects Poetry projects by looking for ``pyproject.toml``.
    If the worktree is a Poetry project, it runs ``poetry install`` first.
    If installation succeeds, it runs baseline ``poetry run pytest`` unless
    debug test skipping is enabled in setup_config.

    Commands are run through the sandbox handle so RALPH does not hard-code
    local, Docker, or future sandbox behavior.

    :param worktree_path: Fresh Git worktree path.
    :type worktree_path: str | Path
    :param sandbox_handle: Sandbox handle with ``i_sandboxhandle_run()``.
    :type sandbox_handle: Any | None
    :return: Project setup result.
    :rtype: ProjectSetupResult
    """

    resolved_worktree_path = Path(worktree_path)

    if not _is_poetry_project(resolved_worktree_path):
        return ProjectSetupResult(
            poetry_project=False,
            message="No pyproject.toml found. Skipped Poetry setup.",
        )

    if sandbox_handle is None:
        return ProjectSetupResult(
            poetry_project=True,
            blocked=True,
            message="Poetry setup blocked because sandbox handle is missing.",
        )

    install_command = ("poetry", "install")
    install_result = _run_command_through_sandbox(
        sandbox_handle=sandbox_handle,
        command=install_command,
        worktree_path=resolved_worktree_path,
    )

    if install_result.failed:
        return ProjectSetupResult(
            poetry_project=True,
            install_ran=True,
            install_passed=False,
            baseline_tests_ran=False,
            baseline_tests_passed=False,
            blocked=True,
            install_command=install_command,
            install_stdout=install_result.stdout,
            install_stderr=install_result.stderr,
            install_exit_code=install_result.exit_code,
            message=_format_failed_command_message(
                step_name="poetry install",
                command=install_command,
                result=install_result,
            ),
        )

    if setup_config.debug_skip_tests_flag:
        return ProjectSetupResult(
            poetry_project=True,
            install_ran=True,
            install_passed=True,
            baseline_tests_ran=False,
            baseline_tests_passed=False,
            blocked=False,
            install_command=install_command,
            install_stdout=install_result.stdout,
            install_stderr=install_result.stderr,
            install_exit_code=install_result.exit_code,
            message=(
                "Poetry setup passed. poetry install succeeded. "
                "Skipped baseline poetry run pytest because DEBUG_SKIP_TESTS_FLAG is enabled."
            ),
        )

    baseline_test_command = ("poetry", "run", "pytest")
    baseline_test_result = _run_command_through_sandbox(
        sandbox_handle=sandbox_handle,
        command=baseline_test_command,
        worktree_path=resolved_worktree_path,
    )

    if baseline_test_result.failed:
        return ProjectSetupResult(
            poetry_project=True,
            install_ran=True,
            install_passed=True,
            baseline_tests_ran=True,
            baseline_tests_passed=False,
            blocked=True,
            install_command=install_command,
            install_stdout=install_result.stdout,
            install_stderr=install_result.stderr,
            install_exit_code=install_result.exit_code,
            baseline_test_command=baseline_test_command,
            baseline_test_stdout=baseline_test_result.stdout,
            baseline_test_stderr=baseline_test_result.stderr,
            baseline_test_exit_code=baseline_test_result.exit_code,
            message=_format_failed_command_message(
                step_name="baseline poetry run pytest",
                command=baseline_test_command,
                result=baseline_test_result,
            ),
        )

    return ProjectSetupResult(
        poetry_project=True,
        install_ran=True,
        install_passed=True,
        baseline_tests_ran=True,
        baseline_tests_passed=True,
        blocked=False,
        install_command=install_command,
        install_stdout=install_result.stdout,
        install_stderr=install_result.stderr,
        install_exit_code=install_result.exit_code,
        baseline_test_command=baseline_test_command,
        baseline_test_stdout=baseline_test_result.stdout,
        baseline_test_stderr=baseline_test_result.stderr,
        baseline_test_exit_code=baseline_test_result.exit_code,
        message=(
            "Poetry setup passed. "
            "poetry install and baseline poetry run pytest succeeded."
        ),
    )


def _is_poetry_project(worktree_path: Path) -> bool:
    """
    Return ``True`` when the worktree looks like a Poetry project.

    :param worktree_path: Worktree path to inspect.
    :type worktree_path: Path
    :return: Whether ``pyproject.toml`` exists.
    :rtype: bool

    :meta private:
    """

    return (worktree_path / "pyproject.toml").exists()


def _run_command_through_sandbox(
    sandbox_handle: Any,
    command: tuple[str, ...],
    worktree_path: Path,
) -> CommandResult:
    """
    Run one command through the sandbox command seam.

    :param sandbox_handle: Sandbox handle with ``i_sandboxhandle_run()``.
    :type sandbox_handle: Any
    :param command: Command tuple to run.
    :type command: tuple[str, ...]
    :param worktree_path: Working directory for the command.
    :type worktree_path: Path
    :return: Normalized command result.
    :rtype: CommandResult

    :meta private:
    """

    return sandbox_handle.i_sandboxhandle_run(
        list(command),
        cwd=worktree_path,
    )


def _format_failed_command_message(
    step_name: str,
    command: tuple[str, ...],
    result: CommandResult,
) -> str:
    """
    Format a readable message for a failed setup command.

    :param step_name: Setup step that failed.
    :type step_name: str
    :param command: Command that failed.
    :type command: tuple[str, ...]
    :param result: Failed command result.
    :type result: CommandResult
    :return: Human-readable failure message.
    :rtype: str

    :meta private:
    """

    command_text = " ".join(command)
    stderr_text = result.stderr.strip()
    stdout_text = result.stdout.strip()

    details = stderr_text or stdout_text or "No command output was captured."

    return (
        f"Poetry setup blocked because {step_name} failed. "
        f"Command: {command_text}. "
        f"Exit code: {result.exit_code}. "
        f"Details: {details}"
    )
