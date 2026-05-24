# tests/codex_preflight/test_codex_preflight.py
from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

from ai_coder.codex_preflight import i_codex_preflight_check


class FakeCommandRunner:
    def __init__(
        self,
        *,
        returncode: int = 0,
        stdout: str = "codex 1.0.0",
        stderr: str = "",
        error: Exception | None = None,
    ) -> None:
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr
        self.error = error
        self.calls: list[tuple[list[str], dict[str, object]]] = []

    def __call__(self, command: list[str], **kwargs: object) -> SimpleNamespace:
        self.calls.append((command, kwargs))

        if self.error is not None:
            raise self.error

        return SimpleNamespace(
            returncode=self.returncode,
            stdout=self.stdout,
            stderr=self.stderr,
        )


class FakeExecutableFinder:
    def __init__(self, found_path: str | None = "codex") -> None:
        self.found_path = found_path
        self.calls: list[str] = []

    def __call__(self, executable_name: str) -> str | None:
        self.calls.append(executable_name)
        return self.found_path


def _write_prompt_file(tmp_path: Path) -> Path:
    prompt_path = tmp_path / "codex_smoke_test.md"
    prompt_path.write_text(
        "Use Codex to complete the configured smoke proof.\n",
        encoding="utf-8",
    )
    return prompt_path


def _valid_codex_preflight_config(
    tmp_path: Path,
    **overrides: object,
) -> SimpleNamespace:
    values: dict[str, object] = {
        "default_agent": "codex",
        "sandbox_mode": "local",
        "codex_command": "codex",
        "prompt_path": _write_prompt_file(tmp_path),
        "prompt_text": "",
        "issue_number": 49,
        "issue_title": "Make startup log uppercase",
        "issue_body": "Change the startup log message text to all caps.",
        "github_repo": "Devilfish281/ai_coder",
        "label": "tracer bullet",
        "dry_run": True,
        "github_pull_request_creation_enabled": False,
        "pull_request_creation_enabled": False,
        "github_issue_close_enabled": False,
    }
    values.update(overrides)
    return SimpleNamespace(**values)


def test_codex_preflight_passes_when_provider_is_codex_and_sandbox_is_local(
    tmp_path: Path,
) -> None:
    config = _valid_codex_preflight_config(tmp_path)
    command_runner = FakeCommandRunner()
    executable_finder = FakeExecutableFinder(found_path="codex")

    result = i_codex_preflight_check(
        config,
        command_runner=command_runner,
        executable_finder=executable_finder,
    )

    assert result.ready is True
    assert result.blocked is False
    assert result.agent_provider == "codex"
    assert result.sandbox_mode == "local"
    assert result.codex_command == "codex"
    assert result.prompt_input_ready is True
    assert result.prompt_input_source == "prompt_path"
    assert result.issue_input_ready is True
    assert result.issue_input_source == "provided_issue"
    assert result.pull_request_safe is True
    assert result.issue_close_safe is True
    assert result.dry_run is True
    assert result.version_command == ("codex", "--version")
    assert result.version_output == "codex 1.0.0"
    assert result.diagnostics == ""
    assert result.exit_code == 0
    assert result.message == (
        "Codex preflight passed: provider is 'codex', sandbox mode is 'local', "
        "and Codex readiness command succeeded."
    )


def test_codex_preflight_blocks_provider_mismatch() -> None:
    config = SimpleNamespace(
        default_agent="mock",
        sandbox_mode="local",
        codex_command="codex",
    )

    result = i_codex_preflight_check(config)

    assert result.ready is False
    assert result.blocked is True
    assert result.agent_provider == "mock"
    assert result.sandbox_mode == "local"
    assert result.codex_command == "codex"
    assert result.version_command == ()
    assert result.version_output == ""
    assert result.diagnostics == ""
    assert result.exit_code is None
    assert "RALPH_AGENT" in result.message
    assert "codex" in result.message
    assert "mock" in result.message


def test_codex_preflight_blocks_sandbox_mismatch() -> None:
    config = SimpleNamespace(
        default_agent="codex",
        sandbox_mode="docker",
        codex_command="codex",
    )

    result = i_codex_preflight_check(config)

    assert result.ready is False
    assert result.blocked is True
    assert result.agent_provider == "codex"
    assert result.sandbox_mode == "docker"
    assert result.codex_command == "codex"
    assert result.version_command == ()
    assert result.version_output == ""
    assert result.diagnostics == ""
    assert result.exit_code is None
    assert "RALPH_SANDBOX_MODE" in result.message
    assert "local" in result.message
    assert "docker" in result.message


def test_codex_preflight_normalizes_case_and_whitespace(tmp_path: Path) -> None:
    config = _valid_codex_preflight_config(
        tmp_path,
        default_agent="  CoDeX  ",
        sandbox_mode="  LoCaL  ",
        codex_command="  codex  ",
    )
    command_runner = FakeCommandRunner()
    executable_finder = FakeExecutableFinder(found_path="codex")

    result = i_codex_preflight_check(
        config,
        command_runner=command_runner,
        executable_finder=executable_finder,
    )

    assert result.ready is True
    assert result.blocked is False
    assert result.agent_provider == "codex"
    assert result.sandbox_mode == "local"
    assert result.codex_command == "codex"
    assert result.version_command == ("codex", "--version")
    assert "preflight passed" in result.message


def test_codex_preflight_checks_configured_codex_command(tmp_path: Path) -> None:
    config = _valid_codex_preflight_config(
        tmp_path,
        codex_command="  codex  ",
    )
    command_runner = FakeCommandRunner()
    executable_finder = FakeExecutableFinder(found_path="codex")

    result = i_codex_preflight_check(
        config,
        command_runner=command_runner,
        executable_finder=executable_finder,
    )

    assert result.codex_command == "codex"
    assert executable_finder.calls == ["codex"]
    assert command_runner.calls[0][0] == ["codex", "--version"]


def test_codex_preflight_runs_read_only_version_command(tmp_path: Path) -> None:
    config = _valid_codex_preflight_config(tmp_path)
    command_runner = FakeCommandRunner(stdout="codex 2.1.0")
    executable_finder = FakeExecutableFinder(found_path="codex")

    result = i_codex_preflight_check(
        config,
        command_runner=command_runner,
        executable_finder=executable_finder,
    )

    assert len(command_runner.calls) == 1
    assert command_runner.calls[0][0] == ["codex", "--version"]
    assert result.ready is True
    assert result.blocked is False
    assert result.version_command == ("codex", "--version")
    assert result.version_output == "codex 2.1.0"


def test_codex_preflight_blocks_missing_codex_command() -> None:
    config = SimpleNamespace(
        default_agent="codex",
        sandbox_mode="local",
        codex_command="   ",
    )
    command_runner = FakeCommandRunner()
    executable_finder = FakeExecutableFinder(found_path="codex")

    result = i_codex_preflight_check(
        config,
        command_runner=command_runner,
        executable_finder=executable_finder,
    )

    assert result.ready is False
    assert result.blocked is True
    assert result.codex_command == ""
    assert result.version_command == ()
    assert result.version_output == ""
    assert "CODEX_COMMAND" in result.message
    assert "CODEX_COMMAND" in result.diagnostics
    assert command_runner.calls == []
    assert executable_finder.calls == []


def test_codex_preflight_blocks_missing_codex_executable(tmp_path: Path) -> None:
    config = _valid_codex_preflight_config(tmp_path)
    command_runner = FakeCommandRunner()
    executable_finder = FakeExecutableFinder(found_path=None)

    result = i_codex_preflight_check(
        config,
        command_runner=command_runner,
        executable_finder=executable_finder,
    )

    assert result.ready is False
    assert result.blocked is True
    assert result.codex_command == "codex"
    assert result.version_command == ()
    assert result.version_output == ""
    assert "executable was not found" in result.message
    assert "codex" in result.message
    assert "executable was not found" in result.diagnostics
    assert command_runner.calls == []


def test_codex_preflight_blocks_version_command_failure_with_diagnostics(
    tmp_path: Path,
) -> None:
    config = _valid_codex_preflight_config(tmp_path)
    command_runner = FakeCommandRunner(
        returncode=1,
        stdout="",
        stderr="Codex is not ready.",
    )
    executable_finder = FakeExecutableFinder(found_path="codex")

    result = i_codex_preflight_check(
        config,
        command_runner=command_runner,
        executable_finder=executable_finder,
    )

    assert result.ready is False
    assert result.blocked is True
    assert result.codex_command == "codex"
    assert result.version_command == ("codex", "--version")
    assert result.version_output == ""
    assert result.exit_code == 1
    assert "exit code 1" in result.message
    assert "Codex is not ready." in result.diagnostics


def test_codex_preflight_blocks_missing_executable_from_file_not_found_error(
    tmp_path: Path,
) -> None:
    config = _valid_codex_preflight_config(tmp_path)
    command_runner = FakeCommandRunner(error=FileNotFoundError("codex"))
    executable_finder = FakeExecutableFinder(found_path="codex")

    result = i_codex_preflight_check(
        config,
        command_runner=command_runner,
        executable_finder=executable_finder,
    )

    assert result.ready is False
    assert result.blocked is True
    assert result.codex_command == "codex"
    assert result.version_command == ("codex", "--version")
    assert "executable was not found" in result.message
    assert "codex" in result.diagnostics


def test_codex_preflight_does_not_run_version_when_provider_mismatch_blocks() -> None:
    config = SimpleNamespace(
        default_agent="mock",
        sandbox_mode="local",
        codex_command="codex",
    )
    command_runner = FakeCommandRunner()
    executable_finder = FakeExecutableFinder(found_path="codex")

    result = i_codex_preflight_check(
        config,
        command_runner=command_runner,
        executable_finder=executable_finder,
    )

    assert result.ready is False
    assert result.blocked is True
    assert command_runner.calls == []
    assert executable_finder.calls == []


def test_codex_preflight_does_not_run_version_when_sandbox_mismatch_blocks() -> None:
    config = SimpleNamespace(
        default_agent="codex",
        sandbox_mode="docker",
        codex_command="codex",
    )
    command_runner = FakeCommandRunner()
    executable_finder = FakeExecutableFinder(found_path="codex")

    result = i_codex_preflight_check(
        config,
        command_runner=command_runner,
        executable_finder=executable_finder,
    )

    assert result.ready is False
    assert result.blocked is True
    assert command_runner.calls == []
    assert executable_finder.calls == []


def test_codex_preflight_blocks_missing_prompt_input(tmp_path: Path) -> None:
    config = _valid_codex_preflight_config(
        tmp_path,
        prompt_path=tmp_path / "missing_prompt.md",
        prompt_text="",
    )
    command_runner = FakeCommandRunner()
    executable_finder = FakeExecutableFinder(found_path="codex")

    result = i_codex_preflight_check(
        config,
        command_runner=command_runner,
        executable_finder=executable_finder,
    )

    assert result.ready is False
    assert result.blocked is True
    assert result.prompt_input_ready is False
    assert "prompt input" in result.message
    assert result.version_command == ()
    assert command_runner.calls == []
    assert executable_finder.calls == []


def test_codex_preflight_accepts_inline_prompt_text(tmp_path: Path) -> None:
    config = _valid_codex_preflight_config(
        tmp_path,
        prompt_path=tmp_path / "missing_prompt.md",
        prompt_text="Use Codex to run the smoke proof.",
    )
    command_runner = FakeCommandRunner()
    executable_finder = FakeExecutableFinder(found_path="codex")

    result = i_codex_preflight_check(
        config,
        command_runner=command_runner,
        executable_finder=executable_finder,
    )

    assert result.ready is True
    assert result.blocked is False
    assert result.prompt_input_ready is True
    assert result.prompt_input_source == "prompt_text"
    assert result.version_command == ("codex", "--version")
    assert command_runner.calls[0][0] == ["codex", "--version"]


def test_codex_preflight_blocks_missing_issue_input(tmp_path: Path) -> None:
    config = _valid_codex_preflight_config(
        tmp_path,
        issue_number=0,
        issue_title="",
        issue_body="",
        github_repo="",
        label="",
    )
    command_runner = FakeCommandRunner()
    executable_finder = FakeExecutableFinder(found_path="codex")

    result = i_codex_preflight_check(
        config,
        command_runner=command_runner,
        executable_finder=executable_finder,
    )

    assert result.ready is False
    assert result.blocked is True
    assert result.issue_input_ready is False
    assert "issue input" in result.message
    assert result.version_command == ()
    assert command_runner.calls == []
    assert executable_finder.calls == []


def test_codex_preflight_accepts_provided_issue_data(tmp_path: Path) -> None:
    config = _valid_codex_preflight_config(
        tmp_path,
        issue_number=49,
        issue_title="Make startup log uppercase",
        issue_body="Change the startup log message text to all caps.",
    )
    command_runner = FakeCommandRunner()
    executable_finder = FakeExecutableFinder(found_path="codex")

    result = i_codex_preflight_check(
        config,
        command_runner=command_runner,
        executable_finder=executable_finder,
    )

    assert result.ready is True
    assert result.blocked is False
    assert result.issue_input_ready is True
    assert result.issue_input_source == "provided_issue"
    assert result.version_command == ("codex", "--version")
    assert command_runner.calls[0][0] == ["codex", "--version"]


def test_codex_preflight_accepts_live_issue_reading_configuration(
    tmp_path: Path,
) -> None:
    config = _valid_codex_preflight_config(
        tmp_path,
        issue_number=0,
        issue_title="",
        issue_body="",
        github_repo="Devilfish281/ai_coder",
        label="tracer bullet",
    )
    command_runner = FakeCommandRunner()
    executable_finder = FakeExecutableFinder(found_path="codex")

    result = i_codex_preflight_check(
        config,
        command_runner=command_runner,
        executable_finder=executable_finder,
    )

    assert result.ready is True
    assert result.blocked is False
    assert result.issue_input_ready is True
    assert result.issue_input_source == "live_issue_reading"
    assert result.version_command == ("codex", "--version")
    assert command_runner.calls == [(["codex", "--version"], {})]


def test_codex_preflight_blocks_unsafe_pull_request_configuration(
    tmp_path: Path,
) -> None:
    config = _valid_codex_preflight_config(
        tmp_path,
        dry_run=False,
        github_pull_request_creation_enabled=True,
        github_issue_close_enabled=False,
    )
    command_runner = FakeCommandRunner()
    executable_finder = FakeExecutableFinder(found_path="codex")

    result = i_codex_preflight_check(
        config,
        command_runner=command_runner,
        executable_finder=executable_finder,
    )

    assert result.ready is False
    assert result.blocked is True
    assert result.pull_request_safe is False
    assert "pull request creation" in result.message
    assert result.version_command == ()
    assert command_runner.calls == []
    assert executable_finder.calls == []


def test_codex_preflight_blocks_unsafe_issue_close_configuration(
    tmp_path: Path,
) -> None:
    config = _valid_codex_preflight_config(
        tmp_path,
        dry_run=False,
        github_pull_request_creation_enabled=False,
        github_issue_close_enabled=True,
    )
    command_runner = FakeCommandRunner()
    executable_finder = FakeExecutableFinder(found_path="codex")

    result = i_codex_preflight_check(
        config,
        command_runner=command_runner,
        executable_finder=executable_finder,
    )

    assert result.ready is False
    assert result.blocked is True
    assert result.issue_close_safe is False
    assert "issue closing" in result.message
    assert result.version_command == ()
    assert command_runner.calls == []
    assert executable_finder.calls == []
