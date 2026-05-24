# src/ai_coder/codex_preflight/codex_preflight.py
from __future__ import annotations

import shutil
import subprocess
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path, PureWindowsPath
from typing import Any

EXPECTED_CODEX_PROVIDER = "codex"
EXPECTED_CODEX_SANDBOX_MODE = "local"
CODEX_VERSION_ARGUMENT = "--version"
CODEX_PREFLIGHT_TIMEOUT_SECONDS = 10.0
MAX_DIAGNOSTIC_TEXT_LENGTH = 1000


@dataclass(frozen=True)
class CodexPreflightResult:
    """Store the read-only Codex preflight check result."""

    ready: bool
    blocked: bool
    message: str
    agent_provider: str
    sandbox_mode: str
    codex_command: str = ""
    version_command: tuple[str, ...] = ()
    version_output: str = ""
    diagnostics: str = ""
    exit_code: int | None = None


def i_codex_preflight_check(
    config: Any,
    *,
    command_runner: Callable[..., Any] | None = None,
    executable_finder: Callable[[str], str | None] | None = None,
) -> CodexPreflightResult:
    """Verify the minimum config required for the Phase 3 Codex smoke proof.

    This preflight is intentionally read-only. It only reads configuration
    values, checks executable availability, and runs a lightweight readiness
    command. It does not construct providers, start sandboxes, create
    worktrees, call models, commit changes, create pull requests, or close
    GitHub issues.
    """

    agent_provider = _normalize_config_value(
        getattr(config, "default_agent", ""),
    )
    sandbox_mode = _normalize_config_value(
        getattr(config, "sandbox_mode", ""),
    )
    codex_command = _clean_codex_command(config)

    if agent_provider != EXPECTED_CODEX_PROVIDER:
        return CodexPreflightResult(
            ready=False,
            blocked=True,
            message=(
                "Codex preflight blocked: RALPH_AGENT must be 'codex' for "
                "the Phase 3 Codex smoke proof. "
                f"Current provider: '{agent_provider}'."
            ),
            agent_provider=agent_provider,
            sandbox_mode=sandbox_mode,
            codex_command=codex_command,
        )

    if sandbox_mode != EXPECTED_CODEX_SANDBOX_MODE:
        return CodexPreflightResult(
            ready=False,
            blocked=True,
            message=(
                "Codex preflight blocked: RALPH_SANDBOX_MODE must be 'local' "
                "for the first Phase 3 Codex smoke proof. "
                f"Current sandbox mode: '{sandbox_mode}'."
            ),
            agent_provider=agent_provider,
            sandbox_mode=sandbox_mode,
            codex_command=codex_command,
        )

    if not codex_command:
        return _blocked_missing_codex_command(
            agent_provider=agent_provider,
            sandbox_mode=sandbox_mode,
        )

    if not _codex_executable_is_available(
        codex_command=codex_command,
        executable_finder=executable_finder,
    ):
        return _blocked_missing_codex_executable(
            agent_provider=agent_provider,
            sandbox_mode=sandbox_mode,
            codex_command=codex_command,
        )

    version_command = _build_codex_version_command(codex_command)
    return _run_codex_readiness_command(
        agent_provider=agent_provider,
        sandbox_mode=sandbox_mode,
        codex_command=codex_command,
        version_command=version_command,
        command_runner=command_runner,
    )


def _normalize_config_value(value: object) -> str:
    return str(value).strip().casefold()


def _clean_codex_command(config: Any) -> str:
    return str(getattr(config, "codex_command", "")).strip()


def _build_codex_version_command(codex_command: str) -> list[str]:
    return [
        codex_command,
        CODEX_VERSION_ARGUMENT,
    ]


def _codex_executable_is_available(
    *,
    codex_command: str,
    executable_finder: Callable[[str], str | None] | None,
) -> bool:
    if _codex_command_looks_like_path(codex_command):
        return Path(codex_command).is_file()

    finder = executable_finder or shutil.which
    return finder(codex_command) is not None


def _codex_command_looks_like_path(codex_command: str) -> bool:
    return (
        "/" in codex_command
        or "\\" in codex_command
        or bool(PureWindowsPath(codex_command).drive)
    )


def _run_codex_readiness_command(
    *,
    agent_provider: str,
    sandbox_mode: str,
    codex_command: str,
    version_command: list[str],
    command_runner: Callable[..., Any] | None,
) -> CodexPreflightResult:
    runner = command_runner or _default_codex_command_runner
    version_command_tuple = tuple(version_command)

    try:
        command_result = runner(version_command)
    except FileNotFoundError as error:
        return _blocked_missing_codex_executable_after_run(
            agent_provider=agent_provider,
            sandbox_mode=sandbox_mode,
            codex_command=codex_command,
            version_command=version_command_tuple,
            error=error,
        )
    except subprocess.TimeoutExpired as error:
        return _blocked_codex_readiness_timeout(
            agent_provider=agent_provider,
            sandbox_mode=sandbox_mode,
            codex_command=codex_command,
            version_command=version_command_tuple,
            error=error,
        )
    except OSError as error:
        return _blocked_codex_readiness_os_error(
            agent_provider=agent_provider,
            sandbox_mode=sandbox_mode,
            codex_command=codex_command,
            version_command=version_command_tuple,
            error=error,
        )

    exit_code = _command_result_exit_code(command_result)
    stdout_text = _command_result_text(command_result, "stdout")
    stderr_text = _command_result_text(command_result, "stderr")

    if exit_code != 0:
        diagnostics = _format_command_diagnostics(
            exit_code=exit_code,
            stdout_text=stdout_text,
            stderr_text=stderr_text,
        )
        message = _version_failure_message(
            exit_code=exit_code,
            stderr_text=stderr_text,
            stdout_text=stdout_text,
        )

        return CodexPreflightResult(
            ready=False,
            blocked=True,
            message=message,
            agent_provider=agent_provider,
            sandbox_mode=sandbox_mode,
            codex_command=codex_command,
            version_command=version_command_tuple,
            version_output=stdout_text.strip(),
            diagnostics=diagnostics,
            exit_code=exit_code,
        )

    version_output = stdout_text.strip() or stderr_text.strip()

    return CodexPreflightResult(
        ready=True,
        blocked=False,
        message=(
            "Codex preflight passed: provider is 'codex', sandbox mode is "
            "'local', and Codex readiness command succeeded."
        ),
        agent_provider=agent_provider,
        sandbox_mode=sandbox_mode,
        codex_command=codex_command,
        version_command=version_command_tuple,
        version_output=version_output,
        diagnostics="",
        exit_code=exit_code,
    )


def _default_codex_command_runner(
    command: list[str],
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
        timeout=CODEX_PREFLIGHT_TIMEOUT_SECONDS,
    )


def _blocked_missing_codex_command(
    *,
    agent_provider: str,
    sandbox_mode: str,
) -> CodexPreflightResult:
    message = (
        "Codex preflight blocked: CODEX_COMMAND is required when "
        "RALPH_AGENT is 'codex'."
    )

    return CodexPreflightResult(
        ready=False,
        blocked=True,
        message=message,
        agent_provider=agent_provider,
        sandbox_mode=sandbox_mode,
        codex_command="",
        diagnostics=message,
    )


def _blocked_missing_codex_executable(
    *,
    agent_provider: str,
    sandbox_mode: str,
    codex_command: str,
) -> CodexPreflightResult:
    message = (
        "Codex preflight blocked: Codex executable was not found: "
        f"'{codex_command}'."
    )

    return CodexPreflightResult(
        ready=False,
        blocked=True,
        message=message,
        agent_provider=agent_provider,
        sandbox_mode=sandbox_mode,
        codex_command=codex_command,
        diagnostics=message,
    )


def _blocked_missing_codex_executable_after_run(
    *,
    agent_provider: str,
    sandbox_mode: str,
    codex_command: str,
    version_command: tuple[str, ...],
    error: FileNotFoundError,
) -> CodexPreflightResult:
    message = (
        "Codex preflight blocked: Codex executable was not found: "
        f"'{codex_command}'."
    )
    diagnostics = _shorten_diagnostic_text(
        f"{message} Details: {error}",
    )

    return CodexPreflightResult(
        ready=False,
        blocked=True,
        message=message,
        agent_provider=agent_provider,
        sandbox_mode=sandbox_mode,
        codex_command=codex_command,
        version_command=version_command,
        diagnostics=diagnostics,
    )


def _blocked_codex_readiness_timeout(
    *,
    agent_provider: str,
    sandbox_mode: str,
    codex_command: str,
    version_command: tuple[str, ...],
    error: subprocess.TimeoutExpired,
) -> CodexPreflightResult:
    message = "Codex preflight blocked: Codex readiness command timed out."
    diagnostics = _shorten_diagnostic_text(
        f"{message} Timeout seconds: {error.timeout}."
    )

    return CodexPreflightResult(
        ready=False,
        blocked=True,
        message=message,
        agent_provider=agent_provider,
        sandbox_mode=sandbox_mode,
        codex_command=codex_command,
        version_command=version_command,
        diagnostics=diagnostics,
    )


def _blocked_codex_readiness_os_error(
    *,
    agent_provider: str,
    sandbox_mode: str,
    codex_command: str,
    version_command: tuple[str, ...],
    error: OSError,
) -> CodexPreflightResult:
    message = "Codex preflight blocked: Codex readiness command could not run."
    diagnostics = _shorten_diagnostic_text(
        f"{message} Details: {error}",
    )

    return CodexPreflightResult(
        ready=False,
        blocked=True,
        message=message,
        agent_provider=agent_provider,
        sandbox_mode=sandbox_mode,
        codex_command=codex_command,
        version_command=version_command,
        diagnostics=diagnostics,
    )


def _command_result_exit_code(command_result: Any) -> int:
    raw_exit_code = getattr(
        command_result,
        "returncode",
        getattr(command_result, "exit_code", 1),
    )

    try:
        return int(raw_exit_code)
    except (TypeError, ValueError):
        return 1


def _command_result_text(command_result: Any, field_name: str) -> str:
    return str(getattr(command_result, field_name, "") or "")


def _version_failure_message(
    *,
    exit_code: int,
    stderr_text: str,
    stdout_text: str,
) -> str:
    detail_text = stderr_text.strip() or stdout_text.strip()

    if detail_text:
        return (
            "Codex preflight blocked: Codex readiness command failed with "
            f"exit code {exit_code}. "
            f"Stderr: {_shorten_diagnostic_text(detail_text)}"
        )

    return (
        "Codex preflight blocked: Codex readiness command failed with "
        f"exit code {exit_code}."
    )


def _format_command_diagnostics(
    *,
    exit_code: int,
    stdout_text: str,
    stderr_text: str,
) -> str:
    diagnostics = (
        f"Exit code: {exit_code}. "
        f"Stdout: {_format_empty_text(stdout_text)}. "
        f"Stderr: {_format_empty_text(stderr_text)}."
    )
    return _shorten_diagnostic_text(diagnostics)


def _format_empty_text(text: str) -> str:
    cleaned_text = text.strip()

    if cleaned_text:
        return cleaned_text

    return "<empty>"


def _shorten_diagnostic_text(text: str) -> str:
    cleaned_text = text.strip()

    if len(cleaned_text) <= MAX_DIAGNOSTIC_TEXT_LENGTH:
        return cleaned_text

    return cleaned_text[: MAX_DIAGNOSTIC_TEXT_LENGTH - 3].rstrip() + "..."
