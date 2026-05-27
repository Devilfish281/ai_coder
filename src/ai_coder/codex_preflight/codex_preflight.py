# src/ai_coder/codex_preflight/codex_preflight.py
from __future__ import annotations

import os
import tomllib
import shutil
import subprocess
from collections.abc import Callable
from dataclasses import dataclass, replace
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
    prompt_input_ready: bool = False
    prompt_input_source: str = ""
    issue_input_ready: bool = False
    issue_input_source: str = ""
    pull_request_safe: bool = False
    issue_close_safe: bool = False
    dry_run: bool = True


@dataclass(frozen=True)
class _CodexSafeInputCheckResult:
    ready: bool
    source: str = ""
    message: str = ""
    diagnostics: str = ""
    dry_run: bool = True


def i_codex_preflight_check(
    config: Any,
    *,
    command_runner: Callable[..., Any] | None = None,
    executable_finder: Callable[[str], str | None] | None = None,
) -> CodexPreflightResult:
    """Verify the minimum config required for the Phase 3 Codex smoke proof.

    This preflight is intentionally read-only. It only reads configuration
    values, checks executable availability, checks known Codex config shape
    problems, and runs a lightweight readiness command. It does not construct
    providers, start sandboxes, create worktrees, call models, commit changes,
    create pull requests, or close GitHub issues.
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

    dry_run = _configured_dry_run(config)

    prompt_input_result = _check_prompt_input(config)
    if not prompt_input_result.ready:
        return _blocked_safe_input_result(
            agent_provider=agent_provider,
            sandbox_mode=sandbox_mode,
            codex_command=codex_command,
            prompt_input_result=prompt_input_result,
            issue_input_result=_CodexSafeInputCheckResult(ready=False),
            pull_request_safety_result=_CodexSafeInputCheckResult(ready=False),
            issue_close_safety_result=_CodexSafeInputCheckResult(ready=False),
            dry_run=dry_run,
            message=prompt_input_result.message,
            diagnostics=prompt_input_result.diagnostics,
        )

    issue_input_result = _check_issue_input(config)
    if not issue_input_result.ready:
        return _blocked_safe_input_result(
            agent_provider=agent_provider,
            sandbox_mode=sandbox_mode,
            codex_command=codex_command,
            prompt_input_result=prompt_input_result,
            issue_input_result=issue_input_result,
            pull_request_safety_result=_CodexSafeInputCheckResult(ready=False),
            issue_close_safety_result=_CodexSafeInputCheckResult(ready=False),
            dry_run=dry_run,
            message=issue_input_result.message,
            diagnostics=issue_input_result.diagnostics,
        )

    pull_request_safety_result = _check_pull_request_safety(
        config,
        dry_run=dry_run,
    )
    if not pull_request_safety_result.ready:
        return _blocked_safe_input_result(
            agent_provider=agent_provider,
            sandbox_mode=sandbox_mode,
            codex_command=codex_command,
            prompt_input_result=prompt_input_result,
            issue_input_result=issue_input_result,
            pull_request_safety_result=pull_request_safety_result,
            issue_close_safety_result=_CodexSafeInputCheckResult(ready=False),
            dry_run=dry_run,
            message=pull_request_safety_result.message,
            diagnostics=pull_request_safety_result.diagnostics,
        )

    issue_close_safety_result = _check_issue_close_safety(
        config,
        dry_run=dry_run,
    )
    if not issue_close_safety_result.ready:
        return _blocked_safe_input_result(
            agent_provider=agent_provider,
            sandbox_mode=sandbox_mode,
            codex_command=codex_command,
            prompt_input_result=prompt_input_result,
            issue_input_result=issue_input_result,
            pull_request_safety_result=pull_request_safety_result,
            issue_close_safety_result=issue_close_safety_result,
            dry_run=dry_run,
            message=issue_close_safety_result.message,
            diagnostics=issue_close_safety_result.diagnostics,
        )

    codex_config_result = _check_codex_config_toml_files(config)
    if not codex_config_result.ready:
        return _blocked_safe_input_result(
            agent_provider=agent_provider,
            sandbox_mode=sandbox_mode,
            codex_command=codex_command,
            prompt_input_result=prompt_input_result,
            issue_input_result=issue_input_result,
            pull_request_safety_result=pull_request_safety_result,
            issue_close_safety_result=issue_close_safety_result,
            dry_run=dry_run,
            message=codex_config_result.message,
            diagnostics=codex_config_result.diagnostics,
        )

    resolved_codex_command = _resolve_codex_executable_command(
        codex_command=codex_command,
        executable_finder=executable_finder,
    )

    if not resolved_codex_command:
        return _with_safe_input_fields(
            _blocked_missing_codex_executable(
                agent_provider=agent_provider,
                sandbox_mode=sandbox_mode,
                codex_command=codex_command,
            ),
            prompt_input_result=prompt_input_result,
            issue_input_result=issue_input_result,
            pull_request_safety_result=pull_request_safety_result,
            issue_close_safety_result=issue_close_safety_result,
            dry_run=dry_run,
        )

    version_command = _build_codex_version_command(resolved_codex_command)

    return _run_codex_readiness_command(
        agent_provider=agent_provider,
        sandbox_mode=sandbox_mode,
        codex_command=codex_command,
        version_command=version_command,
        command_runner=command_runner,
        prompt_input_result=prompt_input_result,
        issue_input_result=issue_input_result,
        pull_request_safety_result=pull_request_safety_result,
        issue_close_safety_result=issue_close_safety_result,
        dry_run=dry_run,
    )


def _normalize_config_value(value: object) -> str:
    return str(value).strip().casefold()


def _clean_codex_command(config: Any) -> str:
    return str(getattr(config, "codex_command", "")).strip()


def _check_prompt_input(config: Any) -> _CodexSafeInputCheckResult:
    prompt_text = _config_text(config, "prompt_text")

    if prompt_text:
        return _CodexSafeInputCheckResult(
            ready=True,
            source="prompt_text",
            diagnostics="Prompt input is configured from inline prompt text.",
        )

    prompt_path_text = _config_text(config, "prompt_path")

    if prompt_path_text:
        prompt_path = Path(prompt_path_text)

        if prompt_path.is_file():
            return _CodexSafeInputCheckResult(
                ready=True,
                source="prompt_path",
                diagnostics=f"Prompt input is configured from prompt path: {prompt_path}.",
            )

        message = "Codex preflight blocked: prompt input is required."
        diagnostics = _shorten_diagnostic_text(
            f"{message} Prompt path is not a file: {prompt_path}."
        )
        return _CodexSafeInputCheckResult(
            ready=False,
            message=message,
            diagnostics=diagnostics,
        )

    message = "Codex preflight blocked: prompt input is required."
    diagnostics = (
        f"{message} Configure prompt_text or set prompt_path to an existing file."
    )
    return _CodexSafeInputCheckResult(
        ready=False,
        message=message,
        diagnostics=diagnostics,
    )


def _check_issue_input(config: Any) -> _CodexSafeInputCheckResult:
    if _provided_issue_data_is_available(config):
        return _CodexSafeInputCheckResult(
            ready=True,
            source="provided_issue",
            diagnostics="Issue input is configured from provided issue data.",
        )

    if _live_issue_reading_is_configured(config):
        return _CodexSafeInputCheckResult(
            ready=True,
            source="live_issue_reading",
            diagnostics=(
                "Issue input is configured from live GitHub issue reading "
                f"for repo '{_config_text(config, 'github_repo')}' "
                f"and label '{_config_text(config, 'label')}'."
            ),
        )

    message = "Codex preflight blocked: issue input is required."
    diagnostics = _shorten_diagnostic_text(
        f"{message} Provide issue_number, issue_title, and issue_body, "
        "or configure github_repo and label for live issue reading."
    )
    return _CodexSafeInputCheckResult(
        ready=False,
        message=message,
        diagnostics=diagnostics,
    )


def _check_pull_request_safety(
    config: Any,
    *,
    dry_run: bool,
) -> _CodexSafeInputCheckResult:
    pull_request_creation_enabled = _pull_request_creation_is_enabled(config)

    if pull_request_creation_enabled and not dry_run:
        message = (
            "Codex preflight blocked: pull request creation must be disabled "
            "or dry-run for the Phase 3 Codex smoke proof."
        )
        return _CodexSafeInputCheckResult(
            ready=False,
            message=message,
            diagnostics=message,
            dry_run=dry_run,
        )

    source = "dry_run" if pull_request_creation_enabled else "disabled"
    return _CodexSafeInputCheckResult(
        ready=True,
        source=source,
        diagnostics=(
            "Pull request creation is safe because it is "
            f"{'enabled only in dry-run mode' if pull_request_creation_enabled else 'disabled'}."
        ),
        dry_run=dry_run,
    )


def _check_issue_close_safety(
    config: Any,
    *,
    dry_run: bool,
) -> _CodexSafeInputCheckResult:
    issue_close_enabled = _config_bool(
        config,
        "github_issue_close_enabled",
        default=False,
    )

    if issue_close_enabled and not dry_run:
        message = (
            "Codex preflight blocked: issue closing must be disabled or "
            "dry-run for the Phase 3 Codex smoke proof."
        )
        return _CodexSafeInputCheckResult(
            ready=False,
            message=message,
            diagnostics=message,
            dry_run=dry_run,
        )

    source = "dry_run" if issue_close_enabled else "disabled"
    return _CodexSafeInputCheckResult(
        ready=True,
        source=source,
        diagnostics=(
            "Issue closing is safe because it is "
            f"{'enabled only in dry-run mode' if issue_close_enabled else 'disabled'}."
        ),
        dry_run=dry_run,
    )


def _check_codex_config_toml_files(config: Any) -> _CodexSafeInputCheckResult:
    config_paths = _codex_config_path_candidates(config)
    checked_paths: list[str] = []

    for config_path in config_paths:
        if not config_path.exists():
            continue

        checked_paths.append(str(config_path))
        config_file_result = _check_codex_config_toml_file(config_path)

        if not config_file_result.ready:
            return config_file_result

    if checked_paths:
        return _CodexSafeInputCheckResult(
            ready=True,
            source=", ".join(checked_paths),
            diagnostics=(
                "Codex config.toml files were checked for invalid [features] "
                "value types."
            ),
        )

    return _CodexSafeInputCheckResult(
        ready=True,
        source="not_found",
        diagnostics="No Codex config.toml file was found to statically check.",
    )


def _codex_config_path_candidates(config: Any) -> tuple[Path, ...]:
    configured_paths = getattr(config, "codex_config_paths", ())

    if isinstance(configured_paths, str | Path):
        raw_config_paths = (configured_paths,)
    else:
        raw_config_paths = configured_paths or ()

    explicit_paths = tuple(
        Path(str(raw_path).strip())
        for raw_path in raw_config_paths
        if str(raw_path).strip()
    )

    if explicit_paths:
        return _unique_codex_config_paths(explicit_paths)

    candidate_paths: list[Path] = []

    codex_home = os.getenv("CODEX_HOME", "").strip()
    if codex_home:
        candidate_paths.append(Path(codex_home) / "config.toml")

    candidate_paths.append(Path.home() / ".codex" / "config.toml")

    repo_path_text = _config_text(config, "repo_path")
    if repo_path_text:
        candidate_paths.append(Path(repo_path_text) / ".codex" / "config.toml")

    return _unique_codex_config_paths(candidate_paths)


def _unique_codex_config_paths(paths: Iterable[Path]) -> tuple[Path, ...]:
    unique_paths: list[Path] = []
    seen_paths: set[str] = set()

    for path in paths:
        cleaned_path = Path(path)
        path_key = str(cleaned_path)

        if not path_key or path_key in seen_paths:
            continue

        seen_paths.add(path_key)
        unique_paths.append(cleaned_path)

    return tuple(unique_paths)


def _check_codex_config_toml_file(config_path: Path) -> _CodexSafeInputCheckResult:
    if not config_path.is_file():
        message = "Codex preflight blocked: config.toml path is not a file."
        diagnostics = _shorten_diagnostic_text(f"{message} Path: {config_path}.")
        return _CodexSafeInputCheckResult(
            ready=False,
            source=str(config_path),
            message=message,
            diagnostics=diagnostics,
        )

    try:
        parsed_config = tomllib.loads(config_path.read_text(encoding="utf-8"))
    except tomllib.TOMLDecodeError as error:
        message = "Codex preflight blocked: config.toml is not valid TOML."
        diagnostics = _shorten_diagnostic_text(
            f"{message} Path: {config_path}. Details: {error}."
        )
        return _CodexSafeInputCheckResult(
            ready=False,
            source=str(config_path),
            message=message,
            diagnostics=diagnostics,
        )
    except OSError as error:
        message = "Codex preflight blocked: config.toml could not be read."
        diagnostics = _shorten_diagnostic_text(
            f"{message} Path: {config_path}. Details: {error}."
        )
        return _CodexSafeInputCheckResult(
            ready=False,
            source=str(config_path),
            message=message,
            diagnostics=diagnostics,
        )

    features_value = parsed_config.get("features", {})

    if not features_value:
        return _CodexSafeInputCheckResult(
            ready=True,
            source=str(config_path),
            diagnostics=f"Codex config.toml has no [features] table: {config_path}.",
        )

    if not isinstance(features_value, dict):
        message = "Codex preflight blocked: config.toml [features] must be a table."
        diagnostics = _shorten_diagnostic_text(
            f"{message} Path: {config_path}. Actual value: {features_value!r}."
        )
        return _CodexSafeInputCheckResult(
            ready=False,
            source=str(config_path),
            message=message,
            diagnostics=diagnostics,
        )

    for feature_name, feature_value in features_value.items():
        if not isinstance(feature_value, bool):
            return _codex_feature_type_error_result(
                config_path=config_path,
                feature_name=str(feature_name),
                feature_value=feature_value,
            )

    return _CodexSafeInputCheckResult(
        ready=True,
        source=str(config_path),
        diagnostics=(
            "Codex config.toml [features] table contains only boolean values: "
            f"{config_path}."
        ),
    )


def _codex_feature_type_error_result(
    *,
    config_path: Path,
    feature_name: str,
    feature_value: object,
) -> _CodexSafeInputCheckResult:
    message = "Codex preflight blocked: config.toml [features] values must be booleans."
    diagnostics = (
        f"{message} Path: {config_path}. "
        f"Feature: {feature_name}. "
        f"Value: {feature_value!r}. "
        f"Type: {type(feature_value).__name__}. "
        'Move string settings such as web_search = "cached" out of [features] '
        "and place them at the top level of config.toml."
    )

    return _CodexSafeInputCheckResult(
        ready=False,
        source=str(config_path),
        message=message,
        diagnostics=_shorten_diagnostic_text(diagnostics),
    )


def _configured_dry_run(config: Any) -> bool:
    return _config_bool(config, "dry_run", default=True)


def _provided_issue_data_is_available(config: Any) -> bool:
    if _config_has_user_github_issue(config):
        return True

    return (
        _config_int(config, "issue_number") > 0
        and bool(_config_text(config, "issue_title"))
        and bool(_config_text(config, "issue_body"))
    )


def _config_has_user_github_issue(config: Any) -> bool:
    has_user_github_issue = getattr(config, "has_user_github_issue", None)

    if not callable(has_user_github_issue):
        return False

    try:
        return bool(has_user_github_issue())
    except TypeError:
        return False


def _live_issue_reading_is_configured(config: Any) -> bool:
    return bool(_config_text(config, "github_repo")) and bool(
        _config_text(config, "label")
    )


def _pull_request_creation_is_enabled(config: Any) -> bool:
    return _config_bool(
        config,
        "github_pull_request_creation_enabled",
        default=False,
    ) or _config_bool(
        config,
        "pull_request_creation_enabled",
        default=False,
    )


def _config_text(config: Any, field_name: str) -> str:
    return str(getattr(config, field_name, "") or "").strip()


def _config_int(config: Any, field_name: str, default: int = 0) -> int:
    raw_value = getattr(config, field_name, default)

    try:
        return int(str(raw_value).strip())
    except (TypeError, ValueError):
        return default


def _config_bool(config: Any, field_name: str, *, default: bool = False) -> bool:
    raw_value = getattr(config, field_name, default)

    if isinstance(raw_value, bool):
        return raw_value

    if raw_value is None:
        return default

    if isinstance(raw_value, str):
        cleaned_value = raw_value.strip().casefold()

        if cleaned_value in {"1", "true", "yes", "y", "on"}:
            return True

        if cleaned_value in {"0", "false", "no", "n", "off", ""}:
            return False

        return default

    return bool(raw_value)


def _blocked_safe_input_result(
    *,
    agent_provider: str,
    sandbox_mode: str,
    codex_command: str,
    prompt_input_result: _CodexSafeInputCheckResult,
    issue_input_result: _CodexSafeInputCheckResult,
    pull_request_safety_result: _CodexSafeInputCheckResult,
    issue_close_safety_result: _CodexSafeInputCheckResult,
    dry_run: bool,
    message: str,
    diagnostics: str,
) -> CodexPreflightResult:
    return CodexPreflightResult(
        ready=False,
        blocked=True,
        message=message,
        agent_provider=agent_provider,
        sandbox_mode=sandbox_mode,
        codex_command=codex_command,
        diagnostics=diagnostics,
        prompt_input_ready=prompt_input_result.ready,
        prompt_input_source=prompt_input_result.source,
        issue_input_ready=issue_input_result.ready,
        issue_input_source=issue_input_result.source,
        pull_request_safe=pull_request_safety_result.ready,
        issue_close_safe=issue_close_safety_result.ready,
        dry_run=dry_run,
    )


def _with_safe_input_fields(
    result: CodexPreflightResult,
    *,
    prompt_input_result: _CodexSafeInputCheckResult,
    issue_input_result: _CodexSafeInputCheckResult,
    pull_request_safety_result: _CodexSafeInputCheckResult,
    issue_close_safety_result: _CodexSafeInputCheckResult,
    dry_run: bool,
) -> CodexPreflightResult:
    return replace(
        result,
        prompt_input_ready=prompt_input_result.ready,
        prompt_input_source=prompt_input_result.source,
        issue_input_ready=issue_input_result.ready,
        issue_input_source=issue_input_result.source,
        pull_request_safe=pull_request_safety_result.ready,
        issue_close_safe=issue_close_safety_result.ready,
        dry_run=dry_run,
    )


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
    return bool(
        _resolve_codex_executable_command(
            codex_command=codex_command,
            executable_finder=executable_finder,
        )
    )


def _resolve_codex_executable_command(
    *,
    codex_command: str,
    executable_finder: Callable[[str], str | None] | None,
) -> str:
    if _codex_command_looks_like_path(codex_command):
        if Path(codex_command).is_file():
            return codex_command

        return ""

    finder = executable_finder or shutil.which
    resolved_command = finder(codex_command)

    if not resolved_command:
        return ""

    return resolved_command


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
    prompt_input_result: _CodexSafeInputCheckResult,
    issue_input_result: _CodexSafeInputCheckResult,
    pull_request_safety_result: _CodexSafeInputCheckResult,
    issue_close_safety_result: _CodexSafeInputCheckResult,
    dry_run: bool,
) -> CodexPreflightResult:
    runner = command_runner or _default_codex_command_runner
    version_command_tuple = tuple(version_command)

    try:
        command_result = runner(version_command)
    except FileNotFoundError as error:
        return _with_safe_input_fields(
            _blocked_missing_codex_executable_after_run(
                agent_provider=agent_provider,
                sandbox_mode=sandbox_mode,
                codex_command=codex_command,
                version_command=version_command_tuple,
                error=error,
            ),
            prompt_input_result=prompt_input_result,
            issue_input_result=issue_input_result,
            pull_request_safety_result=pull_request_safety_result,
            issue_close_safety_result=issue_close_safety_result,
            dry_run=dry_run,
        )
    except subprocess.TimeoutExpired as error:
        return _with_safe_input_fields(
            _blocked_codex_readiness_timeout(
                agent_provider=agent_provider,
                sandbox_mode=sandbox_mode,
                codex_command=codex_command,
                version_command=version_command_tuple,
                error=error,
            ),
            prompt_input_result=prompt_input_result,
            issue_input_result=issue_input_result,
            pull_request_safety_result=pull_request_safety_result,
            issue_close_safety_result=issue_close_safety_result,
            dry_run=dry_run,
        )
    except OSError as error:
        return _with_safe_input_fields(
            _blocked_codex_readiness_os_error(
                agent_provider=agent_provider,
                sandbox_mode=sandbox_mode,
                codex_command=codex_command,
                version_command=version_command_tuple,
                error=error,
            ),
            prompt_input_result=prompt_input_result,
            issue_input_result=issue_input_result,
            pull_request_safety_result=pull_request_safety_result,
            issue_close_safety_result=issue_close_safety_result,
            dry_run=dry_run,
        )

    exit_code = _command_result_exit_code(command_result)
    stdout_text = _command_result_text(command_result, "stdout")
    stderr_text = _command_result_text(command_result, "stderr")

    if exit_code != 0:
        diagnostics = _format_command_diagnostics(
            exit_code=exit_code,
            stdout_text=stdout_text,
            stderr_text=stderr_text,
            version_command=version_command_tuple,
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
            prompt_input_ready=prompt_input_result.ready,
            prompt_input_source=prompt_input_result.source,
            issue_input_ready=issue_input_result.ready,
            issue_input_source=issue_input_result.source,
            pull_request_safe=pull_request_safety_result.ready,
            issue_close_safe=issue_close_safety_result.ready,
            dry_run=dry_run,
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
        prompt_input_ready=prompt_input_result.ready,
        prompt_input_source=prompt_input_result.source,
        issue_input_ready=issue_input_result.ready,
        issue_input_source=issue_input_result.source,
        pull_request_safe=pull_request_safety_result.ready,
        issue_close_safe=issue_close_safety_result.ready,
        dry_run=dry_run,
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
        f"{message} "
        f"Version command: {_format_version_command_for_diagnostics(version_command)}. "
        f"Details: {error}",
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
        f"{message} "
        f"Version command: {_format_version_command_for_diagnostics(version_command)}. "
        f"Timeout seconds: {error.timeout}."
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
        f"{message} "
        f"Version command: {_format_version_command_for_diagnostics(version_command)}. "  #  Changed Code
        f"Details: {error}",
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
    version_command: tuple[str, ...],
) -> str:
    diagnostics = (
        f"Version command: {_format_version_command_for_diagnostics(version_command)}. "
        f"Exit code: {exit_code}. "
        f"Stdout: {_format_empty_text(stdout_text)}. "
        f"Stderr: {_format_empty_text(stderr_text)}."
    )
    return _shorten_diagnostic_text(diagnostics)


def _format_version_command_for_diagnostics(
    version_command: tuple[str, ...],
) -> str:
    return repr(version_command)


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
