# tests/test_runner/test_test_runner.py
from ai_coder.sandbox_provider import CommandResult
from ai_coder.test_runner import i_test_runner_run

import ai_coder.test_runner.test_runner as test_runner_module


class FakeSandboxHandle:
    def __init__(
        self,
        command_result: CommandResult | None = None,
    ) -> None:
        self.command_result = command_result or CommandResult(
            stdout="tests passed",
            stderr="",
            exit_code=0,
        )
        self.commands: list[tuple[list[str], object]] = []

    def i_sandboxhandle_run(
        self,
        command,
        cwd=None,
    ):
        self.commands.append((command, cwd))
        return self.command_result


def test_test_runner_uses_configured_command_through_sandbox_seam(
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        test_runner_module.setup_config,
        "test_command",
        "poetry run pytest",
    )
    sandbox = FakeSandboxHandle()

    result = i_test_runner_run(sandbox_handle=sandbox)

    assert result.passed is True
    assert result.command == ("poetry", "run", "pytest")
    assert result.stdout == "tests passed"
    assert result.stderr == ""
    assert result.exit_code == 0
    assert result.blocked is False
    assert "Tests passed" in result.message
    assert sandbox.commands == [(["poetry", "run", "pytest"], None)]


def test_test_runner_explicit_command_wins_over_configured_command(
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        test_runner_module.setup_config,
        "test_command",
        "poetry run pytest",
    )
    sandbox = FakeSandboxHandle()

    result = i_test_runner_run(
        sandbox_handle=sandbox,
        command=("pytest", "-q"),
    )

    assert result.passed is True
    assert result.command == ("pytest", "-q")
    assert result.stdout == "tests passed"
    assert result.stderr == ""
    assert result.exit_code == 0
    assert result.blocked is False
    assert "Tests passed" in result.message
    assert sandbox.commands == [(["pytest", "-q"], None)]


def test_test_runner_uses_sandbox_handle_when_provided() -> None:
    sandbox = FakeSandboxHandle()

    result = i_test_runner_run(
        sandbox_handle=sandbox,
        command=("pytest",),
    )

    assert result.passed is True
    assert result.command == ("pytest",)
    assert result.stdout == "tests passed"
    assert result.stderr == ""
    assert result.exit_code == 0
    assert result.blocked is False
    assert "Tests passed" in result.message
    assert sandbox.commands == [(["pytest"], None)]


def test_test_runner_returns_failed_result_when_sandbox_command_fails() -> None:
    command_result = CommandResult(
        stdout="pytest stdout text",
        stderr="pytest failed",
        exit_code=1,
    )
    sandbox = FakeSandboxHandle(command_result)

    result = i_test_runner_run(
        sandbox_handle=sandbox,
        command=("pytest",),
    )

    assert command_result.succeeded is False
    assert command_result.failed is True
    assert result.passed is False
    assert result.command == ("pytest",)
    assert result.stdout == "pytest stdout text"
    assert result.stderr == "pytest failed"
    assert result.exit_code == 1
    assert result.blocked is False
    assert "Tests failed" in result.message
    assert sandbox.commands == [(["pytest"], None)]


def test_test_runner_missing_command_returns_safe_blocked_result(
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        test_runner_module.setup_config,
        "test_command",
        "",
    )
    sandbox = FakeSandboxHandle()

    result = i_test_runner_run(sandbox_handle=sandbox)

    assert result.passed is False
    assert result.blocked is True
    assert result.command == ()
    assert result.stdout == ""
    assert result.stderr == ""
    assert result.exit_code == 1
    assert "test command is missing" in result.message.lower()
    assert sandbox.commands == []


def test_test_runner_stub_returns_passed_result() -> None:
    result = i_test_runner_run(command=("poetry", "run", "pytest"))

    assert result.passed is True
    assert result.command == ("poetry", "run", "pytest")
    assert result.blocked is False
    assert "stubbed" in result.message
