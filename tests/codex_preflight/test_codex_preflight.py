# tests/codex_preflight/test_codex_preflight.py
from __future__ import annotations

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


def test_codex_preflight_passes_when_provider_is_codex_and_sandbox_is_local() -> None:
    config = SimpleNamespace(
        default_agent="codex",
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

    assert result.ready is True
    assert result.blocked is False
    assert result.agent_provider == "codex"
    assert result.sandbox_mode == "local"
    assert result.codex_command == "codex"
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


def test_codex_preflight_normalizes_case_and_whitespace() -> None:
    config = SimpleNamespace(
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


def test_codex_preflight_checks_configured_codex_command() -> None:
    config = SimpleNamespace(
        default_agent="codex",
        sandbox_mode="local",
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


def test_codex_preflight_runs_read_only_version_command() -> None:
    config = SimpleNamespace(
        default_agent="codex",
        sandbox_mode="local",
        codex_command="codex",
    )
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


def test_codex_preflight_blocks_missing_codex_executable() -> None:
    config = SimpleNamespace(
        default_agent="codex",
        sandbox_mode="local",
        codex_command="codex",
    )
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


def test_codex_preflight_blocks_version_command_failure_with_diagnostics() -> None:
    config = SimpleNamespace(
        default_agent="codex",
        sandbox_mode="local",
        codex_command="codex",
    )
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


def test_codex_preflight_blocks_missing_executable_from_file_not_found_error() -> None:
    config = SimpleNamespace(
        default_agent="codex",
        sandbox_mode="local",
        codex_command="codex",
    )
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
