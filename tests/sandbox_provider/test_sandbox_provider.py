import sys

from ai_coder.sandbox_provider import LocalSandboxProvider, i_sandbox_start


def test_local_sandbox_provider_runs_command_in_working_directory(tmp_path) -> None:
    sandbox = LocalSandboxProvider(tmp_path)

    result = sandbox.i_sandbox_run(
        [sys.executable, "-c", "from pathlib import Path; print(Path.cwd().name)"]
    )

    assert result.exit_code == 0
    assert result.stderr == ""
    assert result.stdout.strip() == tmp_path.name


def test_local_sandbox_provider_returns_nonzero_exit_code(tmp_path) -> None:
    sandbox = LocalSandboxProvider(tmp_path)

    result = sandbox.i_sandbox_run(
        [sys.executable, "-c", "import sys; sys.stderr.write('bad'); sys.exit(5)"]
    )

    assert result.exit_code == 5
    assert result.stdout == ""
    assert result.stderr == "bad"


def test_sandbox_start_returns_stub_result(tmp_path) -> None:
    result = i_sandbox_start(tmp_path)

    assert result.working_directory == tmp_path
    assert result.provider_name == "local"
    assert result.started is True
    assert "stubbed" in result.message
