import sys

import pytest

from ai_coder.sandbox_provider import LocalSandboxProvider, i_sandbox_start


def test_local_sandbox_provider_runs_command_in_working_directory(tmp_path) -> None:
    sandbox = LocalSandboxProvider(tmp_path)

    result = sandbox.i_sandboxhandle_run(
        [sys.executable, "-c", "from pathlib import Path; print(Path.cwd().name)"]
    )

    assert result.exit_code == 0
    assert result.succeeded is True
    assert result.stderr == ""
    assert result.stdout.strip() == tmp_path.name


def test_local_sandbox_provider_returns_nonzero_exit_code(tmp_path) -> None:
    sandbox = LocalSandboxProvider(tmp_path)

    result = sandbox.i_sandboxhandle_run(
        [sys.executable, "-c", "import sys; sys.stderr.write('bad'); sys.exit(5)"]
    )

    assert result.exit_code == 5
    assert result.succeeded is False
    assert result.stdout == ""
    assert result.stderr == "bad"


def test_local_sandbox_provider_rejects_empty_command(tmp_path) -> None:
    sandbox = LocalSandboxProvider(tmp_path)

    with pytest.raises(ValueError, match="command cannot be empty"):
        sandbox.i_sandboxhandle_run([])


def test_sandbox_start_returns_local_handle(tmp_path) -> None:
    result = i_sandbox_start(tmp_path, provider_name="local")

    assert result.working_directory == tmp_path
    assert result.provider_name == "local"
    assert result.started is True
    assert result.handle is not None
    assert result.handle.worktree_path == tmp_path
    assert result.handle.working_directory == tmp_path
    assert "Started local sandbox provider" in result.message


def test_sandbox_start_reports_missing_local_working_directory(tmp_path) -> None:
    missing_path = tmp_path / "missing-worktree"

    result = i_sandbox_start(missing_path, provider_name="local")

    assert result.working_directory == missing_path
    assert result.provider_name == "local"
    assert result.started is False
    assert result.handle is None
    assert "Local sandbox startup failed" in result.message
    assert str(missing_path) in result.message
