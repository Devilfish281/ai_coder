# tests/sandbox_provider/test_sandbox_provider.py
import subprocess
import sys
from pathlib import Path
import pytest

import ai_coder.sandbox_provider.mount_utils as mount_utils_module
from ai_coder.sandbox_provider.mount_utils import (
    PARENT_GIT_SANDBOX_DIR,
    SANDBOX_REPO_DIR,
    i_mountutils_to_docker_host_path,
)

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
        command_parts = list(command)
        commands.append(command_parts)

        assert capture_output is True
        assert text is True
        assert check is False

        if command_parts[:3] == ["docker", "image", "inspect"]:
            return subprocess.CompletedProcess(
                args=command,
                returncode=0,
                stdout="[]",
                stderr="",
            )

        if command_parts[:3] == ["docker", "run", "--rm"]:
            return subprocess.CompletedProcess(
                args=command,
                returncode=0,
                stdout="command passed",
                stderr="",
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
    assert first_result.stdout == "command passed"
    assert second_result.stdout == "command passed"
    assert image_inspect_commands == [
        ["docker", "image", "inspect", image_name],
    ]
    assert len(docker_run_commands) == 2
    assert docker_run_commands[0][-2:] == ["python", "--version"]
    assert docker_run_commands[1][-2:] == ["pytest", "--version"]


def test_docker_sandbox_provider_runs_command_with_bind_mount_and_workspace(
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
        command_parts = list(command)
        commands.append(command_parts)

        assert capture_output is True
        assert text is True
        assert check is False

        if command_parts[:3] == ["docker", "image", "inspect"]:
            return subprocess.CompletedProcess(
                args=command,
                returncode=0,
                stdout="[]",
                stderr="",
            )

        if command_parts[:3] == ["docker", "run", "--rm"]:
            return subprocess.CompletedProcess(
                args=command,
                returncode=0,
                stdout="hello from docker\n",
                stderr="",
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

    provider = DockerSandboxProvider(
        worktree_path=tmp_path,
        image_name=image_name,
        docker_build_command=build_command,
    )

    result = provider.i_sandboxhandle_run(
        ["python", "-c", "print('hello from docker')"]
    )

    docker_run_commands = [
        command for command in commands if command[:3] == ["docker", "run", "--rm"]
    ]
    docker_run_command = docker_run_commands[0]
    volume_index = docker_run_command.index("-v")
    workdir_index = docker_run_command.index("-w")
    image_index = docker_run_command.index(image_name)

    assert result.succeeded is True
    assert result.failed is False
    assert result.stdout == "hello from docker\n"
    assert result.stderr == ""
    assert result.exit_code == 0
    assert docker_run_command[:3] == ["docker", "run", "--rm"]

    expected_host_path = i_mountutils_to_docker_host_path(
        tmp_path,
        platform_name="windows",
    )

    assert docker_run_command[volume_index + 1] == f"{expected_host_path}:/workspace"

    assert docker_run_command[workdir_index + 1] == "/workspace"
    assert docker_run_command[image_index + 1 :] == [
        "python",
        "-c",
        "print('hello from docker')",
    ]


def test_docker_sandbox_provider_returns_failed_command_result(
    monkeypatch,
    tmp_path,
) -> None:
    image_name = "ai-code-test:latest"
    build_command = "docker build -f .ai_coder/Dockerfile -t ai-code-test:latest ."

    def fake_run(
        command,
        capture_output,
        text,
        check=False,
    ):
        command_parts = list(command)

        assert capture_output is True
        assert text is True
        assert check is False

        if command_parts[:3] == ["docker", "image", "inspect"]:
            return subprocess.CompletedProcess(
                args=command,
                returncode=0,
                stdout="[]",
                stderr="",
            )

        if command_parts[:3] == ["docker", "run", "--rm"]:
            return subprocess.CompletedProcess(
                args=command,
                returncode=7,
                stdout="partial output",
                stderr="command failed",
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

    provider = DockerSandboxProvider(
        worktree_path=tmp_path,
        image_name=image_name,
        docker_build_command=build_command,
    )

    result = provider.i_sandboxhandle_run(["python", "-c", "bad"])

    assert result.stdout == "partial output"
    assert result.stderr == "command failed"
    assert result.exit_code == 7
    assert result.failed is True
    assert result.succeeded is False


def test_docker_sandbox_provider_keeps_normal_env_allowlist_behavior_with_docker_run(
    monkeypatch,
    tmp_path,
) -> None:
    commands: list[list[str]] = []
    image_name = "ai-code-test:latest"
    build_command = "docker build -f .ai_coder/Dockerfile -t ai-code-test:latest ."

    monkeypatch.delenv("PYTHONUNBUFFERED", raising=False)
    monkeypatch.setenv("RALPH_NORMAL_ENV_033", "visible-value-033")
    monkeypatch.delenv("RALPH_MISSING_ENV_033", raising=False)
    monkeypatch.setattr(
        sandbox_provider_module.setup_config,
        "docker_env_allowlist",
        (
            "PYTHONUNBUFFERED",
            "RALPH_NORMAL_ENV_033",
            "RALPH_MISSING_ENV_033",
        ),
    )
    monkeypatch.setattr(
        sandbox_provider_module.setup_config,
        "docker_secret_env_allowlist",
        (),
    )

    def fake_run(
        command,
        capture_output,
        text,
        check=False,
    ):
        command_parts = list(command)
        commands.append(command_parts)

        assert capture_output is True
        assert text is True
        assert check is False

        if command_parts[:3] == ["docker", "image", "inspect"]:
            return subprocess.CompletedProcess(
                args=command,
                returncode=0,
                stdout="[]",
                stderr="",
            )

        if command_parts[:3] == ["docker", "run", "--rm"]:
            return subprocess.CompletedProcess(
                args=command,
                returncode=0,
                stdout="env command passed",
                stderr="",
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

    provider = DockerSandboxProvider(
        worktree_path=tmp_path,
        image_name=image_name,
        docker_build_command=build_command,
    )

    result = provider.i_sandboxhandle_run(["python", "-c", "print('env')"])

    docker_run_commands = [
        command for command in commands if command[:3] == ["docker", "run", "--rm"]
    ]
    docker_run_command = docker_run_commands[0]
    env_values = [
        docker_run_command[index + 1]
        for index, command_part in enumerate(docker_run_command)
        if command_part == "-e"
    ]

    assert result.succeeded is True
    assert "PYTHONUNBUFFERED=1" in env_values
    assert "RALPH_NORMAL_ENV_033=visible-value-033" in env_values
    assert not any(
        env_value.startswith("RALPH_MISSING_ENV_033=") for env_value in env_values
    )


def test_docker_sandbox_provider_keeps_secret_env_allowlist_behavior_with_docker_run(
    monkeypatch,
    tmp_path,
) -> None:
    commands: list[list[str]] = []
    redaction_calls: list[tuple[list[str], tuple[str, ...]]] = []
    image_name = "ai-code-test:latest"
    build_command = "docker build -f .ai_coder/Dockerfile -t ai-code-test:latest ."
    secret_name = "RALPH_SECRET_ENV_030"
    secret_value = "super-secret-value-030"
    original_redact = sandbox_provider_module.i_dockercommand_redact

    monkeypatch.setattr(
        sandbox_provider_module.setup_config,
        "docker_env_allowlist",
        (),
    )
    monkeypatch.setattr(
        sandbox_provider_module.setup_config,
        "docker_secret_env_allowlist",
        (secret_name,),
    )
    monkeypatch.setenv(secret_name, secret_value)

    def fake_redact(command, secret_env_names):
        redaction_calls.append((list(command), tuple(secret_env_names)))
        return original_redact(command, secret_env_names)

    def fake_run(
        command,
        capture_output,
        text,
        check=False,
    ):
        command_parts = list(command)
        commands.append(command_parts)

        assert capture_output is True
        assert text is True
        assert check is False

        if command_parts[:3] == ["docker", "image", "inspect"]:
            return subprocess.CompletedProcess(
                args=command,
                returncode=0,
                stdout="[]",
                stderr="",
            )

        if command_parts[:3] == ["docker", "run", "--rm"]:
            return subprocess.CompletedProcess(
                args=command,
                returncode=0,
                stdout="secret env command passed",
                stderr="",
            )

        return subprocess.CompletedProcess(
            args=command,
            returncode=99,
            stdout="",
            stderr=f"Unexpected command: {command_parts}",
        )

    monkeypatch.setattr(
        sandbox_provider_module,
        "i_dockercommand_redact",
        fake_redact,
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

    result = provider.i_sandboxhandle_run(["python", "-c", "print('secret')"])

    docker_run_commands = [
        command for command in commands if command[:3] == ["docker", "run", "--rm"]
    ]
    docker_run_command = docker_run_commands[0]
    env_values = [
        docker_run_command[index + 1]
        for index, command_part in enumerate(docker_run_command)
        if command_part == "-e"
    ]
    redacted_command = original_redact(
        redaction_calls[0][0],
        redaction_calls[0][1],
    )

    assert result.succeeded is True
    assert f"{secret_name}={secret_value}" in env_values
    assert redaction_calls[0][1] == (secret_name,)
    assert secret_value not in " ".join(redacted_command)
    assert f"{secret_name}=<redacted>" in redacted_command


def test_docker_sandbox_provider_missing_secret_env_raises_when_building_docker_command(  #  Changed Code
    monkeypatch,
    tmp_path,
) -> None:
    commands: list[list[str]] = []
    image_name = "ai-code-test:latest"
    build_command = "docker build -f .ai_coder/Dockerfile -t ai-code-test:latest ."
    secret_name = "RALPH_MISSING_SECRET_ENV_034"  #  Changed Code

    monkeypatch.setattr(
        sandbox_provider_module.setup_config,
        "docker_env_allowlist",
        (),
    )
    monkeypatch.setattr(
        sandbox_provider_module.setup_config,
        "docker_secret_env_allowlist",
        (secret_name,),
    )
    monkeypatch.delenv(secret_name, raising=False)

    def fake_run(
        command,
        capture_output,
        text,
        check=False,
    ):
        command_parts = list(command)
        commands.append(command_parts)

        assert capture_output is True
        assert text is True
        assert check is False

        if command_parts[:3] == ["docker", "image", "inspect"]:
            return subprocess.CompletedProcess(
                args=command,
                returncode=0,
                stdout="[]",
                stderr="",
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

    provider = DockerSandboxProvider(
        worktree_path=tmp_path,
        image_name=image_name,
        docker_build_command=build_command,
    )

    with pytest.raises(
        ValueError,
        match=f"Missing required Docker secret env var: {secret_name}",
    ):
        provider.i_sandboxhandle_run(["python", "-c", "print('secret')"])

    assert commands == [["docker", "image", "inspect", image_name]]


def test_docker_sandbox_provider_empty_secret_env_raises_when_building_docker_command(
    monkeypatch,
    tmp_path,
) -> None:
    commands: list[list[str]] = []
    image_name = "ai-code-test:latest"
    build_command = "docker build -f .ai_coder/Dockerfile -t ai-code-test:latest ."
    secret_name = "RALPH_EMPTY_SECRET_ENV_034"

    monkeypatch.setattr(
        sandbox_provider_module.setup_config,
        "docker_env_allowlist",
        (),
    )
    monkeypatch.setattr(
        sandbox_provider_module.setup_config,
        "docker_secret_env_allowlist",
        (secret_name,),
    )
    monkeypatch.setenv(secret_name, "   ")

    def fake_run(
        command,
        capture_output,
        text,
        check=False,
    ):
        command_parts = list(command)
        commands.append(command_parts)

        assert capture_output is True
        assert text is True
        assert check is False

        if command_parts[:3] == ["docker", "image", "inspect"]:
            return subprocess.CompletedProcess(
                args=command,
                returncode=0,
                stdout="[]",
                stderr="",
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

    provider = DockerSandboxProvider(
        worktree_path=tmp_path,
        image_name=image_name,
        docker_build_command=build_command,
    )

    with pytest.raises(
        ValueError,
        match=f"Docker secret env var is empty: {secret_name}",
    ):
        provider.i_sandboxhandle_run(["python", "-c", "print('secret')"])

    assert commands == [["docker", "image", "inspect", image_name]]


def test_docker_sandbox_provider_does_not_validate_secret_env_during_construction(
    monkeypatch,
    tmp_path,
) -> None:
    commands: list[list[str]] = []
    image_name = "ai-code-test:latest"
    build_command = "docker build -f .ai_coder/Dockerfile -t ai-code-test:latest ."
    secret_name = "RALPH_CONSTRUCTION_SECRET_ENV_034"

    monkeypatch.setattr(
        sandbox_provider_module.setup_config,
        "docker_env_allowlist",
        (),
    )
    monkeypatch.setattr(
        sandbox_provider_module.setup_config,
        "docker_secret_env_allowlist",
        (secret_name,),
    )
    monkeypatch.delenv(secret_name, raising=False)

    def fake_run(
        command,
        capture_output,
        text,
        check=False,
    ):
        command_parts = list(command)
        commands.append(command_parts)

        assert capture_output is True
        assert text is True
        assert check is False

        if command_parts[:3] == ["docker", "image", "inspect"]:
            return subprocess.CompletedProcess(
                args=command,
                returncode=0,
                stdout="[]",
                stderr="",
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

    provider = DockerSandboxProvider(
        worktree_path=tmp_path,
        image_name=image_name,
        docker_build_command=build_command,
    )

    assert provider.image_name == image_name
    assert commands == [["docker", "image", "inspect", image_name]]


def test_docker_sandbox_provider_bind_mount_allows_container_file_edits_to_appear_on_host(
    monkeypatch,
    tmp_path,
) -> None:
    image_name = "ai-code-test:latest"
    build_command = "docker build -f .ai_coder/Dockerfile -t ai-code-test:latest ."
    marker_file = tmp_path / "docker_marker.txt"

    def fake_run(
        command,
        capture_output,
        text,
        check=False,
    ):
        command_parts = list(command)

        assert capture_output is True
        assert text is True
        assert check is False

        if command_parts[:3] == ["docker", "image", "inspect"]:
            return subprocess.CompletedProcess(
                args=command,
                returncode=0,
                stdout="[]",
                stderr="",
            )

        if command_parts[:3] == ["docker", "run", "--rm"]:
            marker_file.write_text(
                "written from docker bind mount",
                encoding="utf-8",
            )
            return subprocess.CompletedProcess(
                args=command,
                returncode=0,
                stdout="wrote marker",
                stderr="",
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

    provider = DockerSandboxProvider(
        worktree_path=tmp_path,
        image_name=image_name,
        docker_build_command=build_command,
    )

    result = provider.i_sandboxhandle_run(["python", "-c", "write marker"])

    assert marker_file.read_text(encoding="utf-8") == "written from docker bind mount"
    assert result.stdout == "wrote marker"
    assert result.stderr == ""
    assert result.exit_code == 0
    assert result.succeeded is True
    assert result.failed is False


def test_docker_sandbox_provider_uses_workspace_as_default_workdir(
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
        command_parts = list(command)
        commands.append(command_parts)

        assert capture_output is True
        assert text is True
        assert check is False

        if command_parts[:3] == ["docker", "image", "inspect"]:
            return subprocess.CompletedProcess(
                args=command,
                returncode=0,
                stdout="[]",
                stderr="",
            )

        if command_parts[:3] == ["docker", "run", "--rm"]:
            return subprocess.CompletedProcess(
                args=command,
                returncode=0,
                stdout="/workspace\n",
                stderr="",
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

    provider = DockerSandboxProvider(
        worktree_path=tmp_path,
        image_name=image_name,
        docker_build_command=build_command,
    )

    result = provider.i_sandboxhandle_run(["pwd"])

    docker_run_commands = [
        command for command in commands if command[:3] == ["docker", "run", "--rm"]
    ]
    docker_run_command = docker_run_commands[0]
    workdir_index = docker_run_command.index("-w")

    assert result.succeeded is True
    assert result.stdout == "/workspace\n"
    assert docker_run_command[workdir_index + 1] == "/workspace"


def test_docker_sandbox_provider_maps_relative_cwd_under_workspace(
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
        command_parts = list(command)
        commands.append(command_parts)

        assert capture_output is True
        assert text is True
        assert check is False

        if command_parts[:3] == ["docker", "image", "inspect"]:
            return subprocess.CompletedProcess(
                args=command,
                returncode=0,
                stdout="[]",
                stderr="",
            )

        if command_parts[:3] == ["docker", "run", "--rm"]:
            return subprocess.CompletedProcess(
                args=command,
                returncode=0,
                stdout="/workspace/tests\n",
                stderr="",
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

    provider = DockerSandboxProvider(
        worktree_path=tmp_path,
        image_name=image_name,
        docker_build_command=build_command,
    )

    result = provider.i_sandboxhandle_run(["pwd"], cwd=Path("tests"))

    docker_run_commands = [
        command for command in commands if command[:3] == ["docker", "run", "--rm"]
    ]
    docker_run_command = docker_run_commands[0]
    workdir_index = docker_run_command.index("-w")

    assert result.succeeded is True
    assert result.stdout == "/workspace/tests\n"
    assert docker_run_command[workdir_index + 1] == "/workspace/tests"


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


def test_docker_sandbox_provider_mounts_corrected_git_metadata_for_windows_worktree(
    monkeypatch,
    tmp_path,
) -> None:
    commands: list[list[str]] = []
    image_name = "ai-code-test:latest"
    build_command = "docker build -f .ai_coder/Dockerfile -t ai-code-test:latest ."
    repo_path = tmp_path / "repo"
    worktree_path = repo_path / ".ai_coder" / "ai_coder_worktrees" / "ralph-issue-032"
    parent_git_dir = repo_path / ".git"
    worktree_git_dir = parent_git_dir / "worktrees" / "ralph-issue-032"
    windows_gitdir_path = str(worktree_git_dir).replace("/", "\\")

    worktree_path.mkdir(parents=True)
    worktree_git_dir.mkdir(parents=True)
    (worktree_path / ".git").write_text(
        f"gitdir: {windows_gitdir_path}\n",
        encoding="utf-8",
    )

    def fake_run(
        command,
        capture_output,
        text,
        check=False,
    ):
        command_parts = list(command)
        commands.append(command_parts)

        assert capture_output is True
        assert text is True
        assert check is False

        if command_parts[:3] == ["docker", "image", "inspect"]:
            return subprocess.CompletedProcess(
                args=command,
                returncode=0,
                stdout="[]",
                stderr="",
            )

        if command_parts[:3] == ["docker", "run", "--rm"]:
            return subprocess.CompletedProcess(
                args=command,
                returncode=0,
                stdout="git status output",
                stderr="",
            )

        return subprocess.CompletedProcess(
            args=command,
            returncode=99,
            stdout="",
            stderr=f"Unexpected command: {command_parts}",
        )

    monkeypatch.setattr(
        mount_utils_module.platform,
        "system",
        lambda: "Windows",
    )
    monkeypatch.setattr(
        sandbox_provider_module.subprocess,
        "run",
        fake_run,
    )

    provider = DockerSandboxProvider(
        worktree_path=worktree_path,
        host_repo_path=repo_path,
        image_name=image_name,
        docker_build_command=build_command,
    )

    result = provider.i_sandboxhandle_run(["git", "status", "--short"])

    docker_run_command = [
        command for command in commands if command[:3] == ["docker", "run", "--rm"]
    ][0]
    volume_specs = [
        docker_run_command[index + 1]
        for index, value in enumerate(docker_run_command)
        if value == "-v"
    ]
    expected_worktree_host_path = i_mountutils_to_docker_host_path(
        worktree_path,
        platform_name="windows",
    )
    expected_parent_git_host_path = i_mountutils_to_docker_host_path(
        parent_git_dir,
        platform_name="windows",
    )
    corrected_git_mount_suffix = f":{SANDBOX_REPO_DIR}/.git:ro"
    corrected_git_mounts = [
        volume_spec
        for volume_spec in volume_specs
        if volume_spec.endswith(corrected_git_mount_suffix)
    ]
    workdir_index = docker_run_command.index("-w")
    image_index = docker_run_command.index(image_name)

    assert result.succeeded is True
    assert f"{expected_worktree_host_path}:{SANDBOX_REPO_DIR}" in volume_specs
    assert f"{expected_parent_git_host_path}:{PARENT_GIT_SANDBOX_DIR}" in volume_specs
    assert len(corrected_git_mounts) == 1

    corrected_git_host_path = corrected_git_mounts[0].rsplit(
        corrected_git_mount_suffix,
        1,
    )[0]
    corrected_git_text = Path(corrected_git_host_path).read_text(encoding="utf-8")

    assert corrected_git_text == (
        "gitdir: /.ralph-parent-git/worktrees/ralph-issue-032\n"
    )
    assert docker_run_command[workdir_index + 1] == SANDBOX_REPO_DIR
    assert docker_run_command[image_index + 1 :] == ["git", "status", "--short"]


def test_docker_sandbox_provider_keeps_host_git_state_inspectable_after_fake_docker_write(
    monkeypatch,
    tmp_path,
) -> None:
    repo_path = tmp_path / "repo"
    worktree_path = tmp_path / "worktree"
    image_name = "ai-code-test:latest"
    build_command = "docker build -f .ai_coder/Dockerfile -t ai-code-test:latest ."
    changed_file = worktree_path / "changed_by_fake_docker.txt"
    original_subprocess_run = subprocess.run

    repo_path.mkdir()
    _run_git_command(repo_path, "init")
    _run_git_command(repo_path, "config", "user.name", "RALPH Test")
    _run_git_command(repo_path, "config", "user.email", "ralph-test@example.test")
    (repo_path / "README.md").write_text("# Test Repo\n", encoding="utf-8")
    _run_git_command(repo_path, "add", "README.md")
    _run_git_command(repo_path, "commit", "-m", "Initial commit")
    _run_git_command(
        repo_path,
        "worktree",
        "add",
        "-b",
        "ralph-issue-032-test",
        str(worktree_path),
    )

    def fake_run(
        command,
        capture_output,
        text,
        check=False,
    ):
        command_parts = list(command)

        assert capture_output is True
        assert text is True
        assert check is False

        if command_parts[:3] == ["git", "-C", str(worktree_path)]:
            return original_subprocess_run(
                command,
                capture_output=capture_output,
                text=text,
                check=check,
            )

        if command_parts[:3] == ["docker", "image", "inspect"]:
            return subprocess.CompletedProcess(
                args=command,
                returncode=0,
                stdout="[]",
                stderr="",
            )

        if command_parts[:3] == ["docker", "run", "--rm"]:
            changed_file.write_text(
                "written by fake docker command",
                encoding="utf-8",
            )
            return subprocess.CompletedProcess(
                args=command,
                returncode=0,
                stdout="fake docker wrote file",
                stderr="",
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

    provider = DockerSandboxProvider(
        worktree_path=worktree_path,
        host_repo_path=repo_path,
        image_name=image_name,
        docker_build_command=build_command,
    )

    result = provider.i_sandboxhandle_run(["python", "-c", "write file"])
    status_result = _run_git_command(worktree_path, "status", "--porcelain")

    assert result.succeeded is True
    assert changed_file.exists()
    assert "?? changed_by_fake_docker.txt" in status_result.stdout


def _run_git_command(
    repo_path: Path,
    *arguments: str,
) -> subprocess.CompletedProcess[str]:
    completed_process = subprocess.run(
        ["git", "-C", str(repo_path), *arguments],
        capture_output=True,
        text=True,
        check=False,
    )

    assert completed_process.returncode == 0, (
        f"Command failed: git -C {repo_path} {' '.join(arguments)}\n"
        f"stdout:\n{completed_process.stdout}\n"
        f"stderr:\n{completed_process.stderr}"
    )

    return completed_process
