# tests/sandbox_provider/test_sandbox_provider.py
import subprocess
import sys

import pytest

import ai_coder.sandbox_provider.sandbox_provider as sandbox_provider_module
from ai_coder.sandbox_provider import (
    CommandResult,
    DockerImageMissingError,
    DockerSandboxProvider,
    LocalSandboxProvider,
    i_sandbox_start,
)


def test_command_result_success_state_is_consistent() -> None:
    result = CommandResult(
        stdout="command output",
        stderr="",
        exit_code=0,
    )

    assert result.stdout == "command output"
    assert result.stderr == ""
    assert result.exit_code == 0
    assert result.succeeded is True
    assert result.failed is False


def test_command_result_failure_state_is_consistent() -> None:
    result = CommandResult(
        stdout="",
        stderr="command failed",
        exit_code=7,
    )

    assert result.stdout == ""
    assert result.stderr == "command failed"
    assert result.exit_code == 7
    assert result.succeeded is False
    assert result.failed is True


def test_local_sandbox_provider_runs_command_in_working_directory(tmp_path) -> None:
    sandbox = LocalSandboxProvider(tmp_path)

    result = sandbox.i_sandboxhandle_run(
        [sys.executable, "-c", "from pathlib import Path; print(Path.cwd().name)"]
    )

    assert result.exit_code == 0
    assert result.succeeded is True
    assert result.failed is False
    assert result.stderr == ""
    assert result.stdout.strip() == tmp_path.name


def test_local_sandbox_provider_returns_nonzero_exit_code(tmp_path) -> None:
    sandbox = LocalSandboxProvider(tmp_path)

    result = sandbox.i_sandboxhandle_run(
        [sys.executable, "-c", "import sys; sys.stderr.write('bad'); sys.exit(5)"]
    )

    assert result.exit_code == 5
    assert result.succeeded is False
    assert result.failed is True
    assert result.stdout == ""
    assert result.stderr == "bad"


def test_local_sandbox_provider_normalizes_command_start_failure(
    monkeypatch,
    tmp_path,
) -> None:
    sandbox = LocalSandboxProvider(tmp_path)

    def fake_run(*args, **kwargs):
        raise OSError("missing executable")

    monkeypatch.setattr(
        sandbox_provider_module.subprocess,
        "run",
        fake_run,
    )

    result = sandbox.i_sandboxhandle_run(["missing-command"])

    assert result.stdout == ""
    assert "missing executable" in result.stderr
    assert result.exit_code == 1
    assert result.succeeded is False
    assert result.failed is True


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


def test_sandbox_start_uses_configured_local_mode_by_default(
    monkeypatch,
    tmp_path,
) -> None:
    monkeypatch.setattr(
        sandbox_provider_module.setup_config,
        "sandbox_mode",
        "local",
    )

    result = i_sandbox_start(tmp_path)

    assert result.working_directory == tmp_path
    assert result.provider_name == "local"
    assert result.started is True
    assert result.handle is not None
    assert isinstance(result.handle, LocalSandboxProvider)
    assert result.handle.worktree_path == tmp_path
    assert result.handle.working_directory == tmp_path
    assert "Started local sandbox provider" in result.message


def test_sandbox_start_uses_configured_docker_mode(
    monkeypatch,
    tmp_path,
) -> None:
    dockerfile_path = tmp_path / "Dockerfile"
    dockerfile_path.write_text("FROM python:3.12-slim\n", encoding="utf-8")
    image_checks: list[str] = []

    monkeypatch.setattr(
        sandbox_provider_module.setup_config,
        "sandbox_mode",
        "docker",
    )
    monkeypatch.setattr(
        sandbox_provider_module.setup_config,
        "docker_image_name",
        "ai-code-test:latest",
    )
    monkeypatch.setattr(
        sandbox_provider_module.setup_config,
        "ralph_dockerfile_path",
        dockerfile_path,
    )

    def fake_check_docker_image_exists(self) -> None:
        image_checks.append(self.image_name)

    monkeypatch.setattr(
        sandbox_provider_module.DockerSandboxProvider,
        "_check_docker_image_exists",
        fake_check_docker_image_exists,
    )

    result = i_sandbox_start(tmp_path)

    assert result.working_directory == tmp_path
    assert result.provider_name == "docker"
    assert result.started is True
    assert result.handle is not None
    assert result.handle.name == "docker"
    assert result.handle.worktree_path == tmp_path
    assert result.handle.image_name == "ai-code-test:latest"
    assert image_checks == ["ai-code-test:latest"]
    assert "Started Docker bind-mount sandbox provider" in result.message


def test_sandbox_start_local_mode_does_not_validate_docker_settings(
    monkeypatch,
    tmp_path,
) -> None:
    monkeypatch.setattr(
        sandbox_provider_module.setup_config,
        "sandbox_mode",
        "local",
    )

    def fail_if_docker_validation_runs() -> None:
        raise AssertionError("Local sandbox mode should not validate Docker settings.")

    class FailingDockerSandboxProvider:
        def __init__(self, *args, **kwargs) -> None:
            raise AssertionError("Local sandbox mode should not start Docker.")

    monkeypatch.setattr(
        sandbox_provider_module,
        "_validate_docker_config_if_available",
        fail_if_docker_validation_runs,
    )
    monkeypatch.setattr(
        sandbox_provider_module,
        "DockerSandboxProvider",
        FailingDockerSandboxProvider,
    )

    result = i_sandbox_start(tmp_path)

    assert result.provider_name == "local"
    assert result.started is True
    assert result.handle is not None
    assert isinstance(result.handle, LocalSandboxProvider)


def test_docker_sandbox_provider_checks_image_on_handle_creation(
    monkeypatch,
    tmp_path,
) -> None:
    commands: list[list[str]] = []
    image_name = "ai-code-test:latest"
    build_command = "docker build -f .ai_coder/Dockerfile -t ai-code-test:latest ."

    def fake_run(
        command,
        capture_output,
        text,
        check=False,
    ):
        commands.append(list(command))
        assert capture_output is True
        assert text is True
        assert check is False
        return subprocess.CompletedProcess(
            args=command,
            returncode=0,
            stdout="[]",
            stderr="",
        )

    monkeypatch.setattr(
        sandbox_provider_module.subprocess,
        "run",
        fake_run,
    )

    provider = DockerSandboxProvider(
        worktree_path=tmp_path,
        image_name=image_name,
        docker_build_command=build_command,
    )

    assert provider.image_name == image_name
    assert commands == [["docker", "image", "inspect", image_name]]


def test_docker_sandbox_provider_checks_image_once_per_handle(
    monkeypatch,
    tmp_path,
) -> None:
    commands: list[list[str]] = []
    image_name = "ai-code-test:latest"
    build_command = "docker build -f .ai_coder/Dockerfile -t ai-code-test:latest ."

    def fake_run(
        command,
        capture_output,
        text,
        check=False,
    ):
        commands.append(list(command))

        if list(command[:3]) == ["docker", "image", "inspect"]:
            return subprocess.CompletedProcess(
                args=command,
                returncode=0,
                stdout="[]",
                stderr="",
            )

        return subprocess.CompletedProcess(
            args=command,
            returncode=0,
            stdout="command passed",
            stderr="",
        )

    monkeypatch.setattr(
        sandbox_provider_module.subprocess,
        "run",
        fake_run,
    )

    provider = DockerSandboxProvider(
        worktree_path=tmp_path,
        image_name=image_name,
        docker_build_command=build_command,
    )

    first_result = provider.i_sandboxhandle_run(["python", "--version"])
    second_result = provider.i_sandboxhandle_run(["pytest", "--version"])

    image_inspect_commands = [
        command for command in commands if command[:3] == ["docker", "image", "inspect"]
    ]
    docker_run_commands = [
        command for command in commands if command[:3] == ["docker", "run", "--rm"]
    ]

    assert first_result.succeeded is True
    assert second_result.succeeded is True
    assert image_inspect_commands == [
        ["docker", "image", "inspect", image_name],
    ]
    assert len(docker_run_commands) == 2


def test_docker_sandbox_provider_missing_image_raises_clear_error(
    monkeypatch,
    tmp_path,
) -> None:
    image_name = "missing-ai-code-test:latest"
    build_command = (
        "docker build -f .ai_coder/Dockerfile " "-t missing-ai-code-test:latest ."
    )

    def fake_run(
        command,
        capture_output,
        text,
        check=False,
    ):
        return subprocess.CompletedProcess(
            args=command,
            returncode=1,
            stdout="",
            stderr=f"No such image: {image_name}",
        )

    monkeypatch.setattr(
        sandbox_provider_module.subprocess,
        "run",
        fake_run,
    )

    with pytest.raises(DockerImageMissingError) as error_info:
        DockerSandboxProvider(
            worktree_path=tmp_path,
            image_name=image_name,
            docker_build_command=build_command,
        )

    message = str(error_info.value)

    assert f"Docker image is missing: {image_name}" in message
    assert "Build it with:" in message
    assert build_command in message
    assert f"No such image: {image_name}" in message


def test_docker_sandbox_provider_missing_image_does_not_auto_build_or_pull(
    monkeypatch,
    tmp_path,
) -> None:
    image_name = "missing-ai-code-test:latest"
    build_command = (
        "docker build -f .ai_coder/Dockerfile " "-t missing-ai-code-test:latest ."
    )
    commands: list[list[str]] = []

    def fake_run(
        command,
        capture_output,
        text,
        check=False,
    ):
        command_parts = list(command)
        commands.append(command_parts)

        if command_parts[:3] == ["docker", "image", "inspect"]:
            return subprocess.CompletedProcess(
                args=command,
                returncode=1,
                stdout="",
                stderr=f"No such image: {image_name}",
            )

        return subprocess.CompletedProcess(
            args=command,
            returncode=99,
            stdout="",
            stderr=f"Unexpected command: {command_parts}",
        )

    monkeypatch.setattr(
        sandbox_provider_module.subprocess,
        "run",
        fake_run,
    )

    with pytest.raises(DockerImageMissingError):
        DockerSandboxProvider(
            worktree_path=tmp_path,
            image_name=image_name,
            docker_build_command=build_command,
        )

    assert commands == [["docker", "image", "inspect", image_name]]
    assert not any("build" in command for command in commands)
    assert not any("pull" in command for command in commands)


def test_sandbox_start_docker_missing_image_does_not_auto_build_or_pull(
    monkeypatch,
    tmp_path,
) -> None:
    dockerfile_path = tmp_path / "Dockerfile"
    dockerfile_path.write_text("FROM python:3.12-slim\n", encoding="utf-8")
    image_name = "missing-ai-code-test:latest"
    commands: list[list[str]] = []

    monkeypatch.setattr(
        sandbox_provider_module.setup_config,
        "sandbox_mode",
        "docker",
    )
    monkeypatch.setattr(
        sandbox_provider_module.setup_config,
        "docker_image_name",
        image_name,
    )
    monkeypatch.setattr(
        sandbox_provider_module.setup_config,
        "ralph_dockerfile_path",
        dockerfile_path,
    )

    def fake_run(
        command,
        capture_output,
        text,
        check=False,
    ):
        command_parts = list(command)
        commands.append(command_parts)

        if command_parts[:3] == ["docker", "image", "inspect"]:
            return subprocess.CompletedProcess(
                args=command,
                returncode=1,
                stdout="",
                stderr=f"No such image: {image_name}",
            )

        return subprocess.CompletedProcess(
            args=command,
            returncode=99,
            stdout="",
            stderr=f"Unexpected command: {command_parts}",
        )

    monkeypatch.setattr(
        sandbox_provider_module.subprocess,
        "run",
        fake_run,
    )

    result = i_sandbox_start(tmp_path)

    assert result.provider_name == "docker"
    assert result.started is False
    assert result.handle is None
    assert "Docker sandbox startup failed" in result.message
    assert image_name in result.message
    assert commands == [["docker", "image", "inspect", image_name]]
    assert not any("build" in command for command in commands)
    assert not any("pull" in command for command in commands)


def test_sandbox_start_local_mode_ignores_broken_docker_image_configuration(
    monkeypatch,
    tmp_path,
) -> None:
    missing_dockerfile_path = tmp_path / "missing.Dockerfile"

    monkeypatch.setattr(
        sandbox_provider_module.setup_config,
        "sandbox_mode",
        "local",
    )
    monkeypatch.setattr(
        sandbox_provider_module.setup_config,
        "docker_image_name",
        "",
    )
    monkeypatch.setattr(
        sandbox_provider_module.setup_config,
        "ralph_dockerfile_path",
        missing_dockerfile_path,
    )

    def fail_if_docker_validation_runs() -> None:
        raise AssertionError("Local sandbox mode should not validate Docker settings.")

    class FailingDockerSandboxProvider:
        def __init__(self, *args, **kwargs) -> None:
            raise AssertionError("Local sandbox mode should not start Docker.")

    monkeypatch.setattr(
        sandbox_provider_module,
        "_validate_docker_config_if_available",
        fail_if_docker_validation_runs,
    )
    monkeypatch.setattr(
        sandbox_provider_module,
        "DockerSandboxProvider",
        FailingDockerSandboxProvider,
    )

    result = i_sandbox_start(tmp_path)

    assert result.provider_name == "local"
    assert result.started is True
    assert result.handle is not None
    assert isinstance(result.handle, LocalSandboxProvider)


def test_sandbox_start_returns_clear_failure_from_real_docker_image_check(
    monkeypatch,
    tmp_path,
) -> None:
    dockerfile_path = tmp_path / "Dockerfile"
    dockerfile_path.write_text("FROM python:3.12-slim\n", encoding="utf-8")
    image_name = "missing-ai-code-test:latest"

    monkeypatch.setattr(
        sandbox_provider_module.setup_config,
        "sandbox_mode",
        "docker",
    )
    monkeypatch.setattr(
        sandbox_provider_module.setup_config,
        "docker_image_name",
        image_name,
    )
    monkeypatch.setattr(
        sandbox_provider_module.setup_config,
        "ralph_dockerfile_path",
        dockerfile_path,
    )

    def fake_run(
        command,
        capture_output,
        text,
        check=False,
    ):
        assert list(command) == ["docker", "image", "inspect", image_name]
        return subprocess.CompletedProcess(
            args=command,
            returncode=1,
            stdout="",
            stderr=f"No such image: {image_name}",
        )

    monkeypatch.setattr(
        sandbox_provider_module.subprocess,
        "run",
        fake_run,
    )

    result = i_sandbox_start(tmp_path)

    assert result.working_directory == tmp_path
    assert result.provider_name == "docker"
    assert result.started is False
    assert result.handle is None
    assert "Docker sandbox startup failed" in result.message
    assert image_name in result.message
    assert "Build it with:" in result.message
    assert f"No such image: {image_name}" in result.message


def test_sandbox_start_returns_clear_failure_when_docker_image_missing(
    monkeypatch,
    tmp_path,
) -> None:
    dockerfile_path = tmp_path / "Dockerfile"
    dockerfile_path.write_text("FROM python:3.12-slim\n", encoding="utf-8")

    image_name = "missing-ai-code-test:latest"
    build_command = (
        "docker build -f .ai_coder/Dockerfile " "-t missing-ai-code-test:latest ."
    )

    monkeypatch.setattr(
        sandbox_provider_module.setup_config,
        "sandbox_mode",
        "docker",
    )
    monkeypatch.setattr(
        sandbox_provider_module.setup_config,
        "docker_image_name",
        image_name,
    )
    monkeypatch.setattr(
        sandbox_provider_module.setup_config,
        "ralph_dockerfile_path",
        dockerfile_path,
    )

    def fake_docker_sandbox_provider(*args, **kwargs):
        raise sandbox_provider_module.DockerImageMissingError(
            f"Docker image is missing: {image_name}\n\n"
            "Build it with:\n\n"
            f"{build_command}"
        )

    monkeypatch.setattr(
        sandbox_provider_module,
        "DockerSandboxProvider",
        fake_docker_sandbox_provider,
    )

    result = i_sandbox_start(tmp_path)

    assert result.working_directory == tmp_path
    assert result.provider_name == "docker"
    assert result.started is False
    assert result.handle is None
    assert "Docker sandbox startup failed" in result.message
    assert image_name in result.message
    assert build_command in result.message
