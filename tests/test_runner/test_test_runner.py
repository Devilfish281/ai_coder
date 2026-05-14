# tests/test_runner/test_test_runner.py
from ai_coder.sandbox_provider import CommandResult
from ai_coder.test_runner import i_test_runner_run


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
    assert "Tests passed" in result.message
    assert sandbox.commands == [(["pytest"], None)]


def test_test_runner_returns_failed_result_when_sandbox_command_fails() -> None:
    command_result = CommandResult(
        stdout="",
        stderr="pytest failed",
        exit_code=1,
    )
    sandbox = FakeSandboxHandle(command_result)  #  Changed Code

    result = i_test_runner_run(
        sandbox_handle=sandbox,
        command=("pytest",),
    )

    assert command_result.succeeded is False
    assert command_result.failed is True
    assert result.passed is False
    assert result.command == ("pytest",)
    assert result.stdout == ""
    assert result.stderr == "pytest failed"
    assert result.exit_code == 1
    assert "Tests failed" in result.message
    assert sandbox.commands == [(["pytest"], None)]


def test_test_runner_stub_returns_passed_result() -> None:
    result = i_test_runner_run(command=("poetry", "run", "pytest"))

    assert result.passed is True
    assert result.command == ("poetry", "run", "pytest")
    assert "stubbed" in result.message
