# tests/project_setup/test_project_setup.py
from pathlib import Path

from ai_coder.project_setup import i_project_setup_run
from ai_coder.sandbox_provider import CommandResult


class FakeProjectSetupSandboxHandle:
    def __init__(
        self,
        command_results: list[CommandResult] | None = None,
    ) -> None:
        self.command_results = command_results or [
            CommandResult(stdout="command passed", stderr="", exit_code=0)
        ]
        self.commands: list[tuple[list[str], Path | None]] = []

    def i_sandboxhandle_run(
        self,
        command,
        cwd=None,
    ):
        self.commands.append((command, cwd))

        if len(self.command_results) > 1:
            return self.command_results.pop(0)

        return self.command_results[0]


def test_project_setup_skips_non_poetry_project(tmp_path) -> None:
    sandbox = FakeProjectSetupSandboxHandle()

    result = i_project_setup_run(
        worktree_path=tmp_path,
        sandbox_handle=sandbox,
    )

    assert result.poetry_project is False
    assert result.install_ran is False
    assert result.install_passed is False
    assert result.baseline_tests_ran is False
    assert result.baseline_tests_passed is False
    assert result.blocked is False
    assert "Skipped Poetry setup" in result.message
    assert sandbox.commands == []


def test_project_setup_poetry_project_runs_poetry_install(tmp_path) -> None:
    (tmp_path / "pyproject.toml").write_text("[tool.poetry]\n", encoding="utf-8")
    sandbox = FakeProjectSetupSandboxHandle()

    result = i_project_setup_run(
        worktree_path=tmp_path,
        sandbox_handle=sandbox,
    )

    assert result.poetry_project is True
    assert result.install_ran is True
    assert result.install_passed is True
    assert result.install_command == ("poetry", "install")
    assert sandbox.commands[0] == (["poetry", "install"], tmp_path)


def test_project_setup_successful_install_runs_baseline_pytest(tmp_path) -> None:
    (tmp_path / "pyproject.toml").write_text("[tool.poetry]\n", encoding="utf-8")
    sandbox = FakeProjectSetupSandboxHandle(
        [
            CommandResult(stdout="install passed", stderr="", exit_code=0),
            CommandResult(stdout="tests passed", stderr="", exit_code=0),
        ]
    )

    result = i_project_setup_run(
        worktree_path=tmp_path,
        sandbox_handle=sandbox,
    )

    assert result.blocked is False
    assert result.install_ran is True
    assert result.install_passed is True
    assert result.baseline_tests_ran is True
    assert result.baseline_tests_passed is True
    assert result.baseline_test_command == ("poetry", "run", "pytest")
    assert sandbox.commands == [
        (["poetry", "install"], tmp_path),
        (["poetry", "run", "pytest"], tmp_path),
    ]


def test_project_setup_failed_install_blocks_before_pytest(tmp_path) -> None:
    (tmp_path / "pyproject.toml").write_text("[tool.poetry]\n", encoding="utf-8")
    sandbox = FakeProjectSetupSandboxHandle(
        [CommandResult(stdout="install stdout", stderr="install failed", exit_code=1)]
    )

    result = i_project_setup_run(
        worktree_path=tmp_path,
        sandbox_handle=sandbox,
    )

    assert result.blocked is True
    assert result.install_ran is True
    assert result.install_passed is False
    assert result.baseline_tests_ran is False
    assert result.baseline_tests_passed is False
    assert result.install_stdout == "install stdout"
    assert result.install_stderr == "install failed"
    assert result.install_exit_code == 1
    assert "poetry install failed" in result.message
    assert sandbox.commands == [(["poetry", "install"], tmp_path)]


def test_project_setup_failed_baseline_pytest_blocks(tmp_path) -> None:
    (tmp_path / "pyproject.toml").write_text("[tool.poetry]\n", encoding="utf-8")
    sandbox = FakeProjectSetupSandboxHandle(
        [
            CommandResult(stdout="install passed", stderr="", exit_code=0),
            CommandResult(stdout="pytest stdout", stderr="pytest failed", exit_code=1),
        ]
    )

    result = i_project_setup_run(
        worktree_path=tmp_path,
        sandbox_handle=sandbox,
    )

    assert result.blocked is True
    assert result.install_ran is True
    assert result.install_passed is True
    assert result.baseline_tests_ran is True
    assert result.baseline_tests_passed is False
    assert result.baseline_test_stdout == "pytest stdout"
    assert result.baseline_test_stderr == "pytest failed"
    assert result.baseline_test_exit_code == 1
    assert "baseline poetry run pytest failed" in result.message
    assert sandbox.commands == [
        (["poetry", "install"], tmp_path),
        (["poetry", "run", "pytest"], tmp_path),
    ]
