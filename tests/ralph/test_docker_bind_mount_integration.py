# tests/ralph/test_docker_bind_mount_integration.py
from __future__ import annotations

import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Sequence

import ai_coder.ralph.ralph as ralph_module
import ai_coder.repository_context.repository_context as repository_context_module
import ai_coder.sandbox_provider.sandbox_provider as sandbox_provider_module
from ai_coder.agent_provider import COMPLETE_TOKEN, AgentResponse
from ai_coder.display import SilentDisplay
from ai_coder.github_issues import GitHubIssue, GitHubIssueCloseResult
from ai_coder.ralph import RALPH_STATUS_COMPLETE, RALPH_STATUS_FAILED, i_ralph_run
from ai_coder.sandbox_provider import CommandResult

WORKSPACE_PATH = "/workspace"
DOCKER_TEST_IMAGE_NAME = "ai-code-test:latest"
DOCKER_TEST_BUILD_COMMAND = (
    "docker build -f .ai_coder/Dockerfile -t ai-code-test:latest ."
)
DOCKER_SECRET_NAME = "RALPH_DOCKER_SECRET_036"
DOCKER_SECRET_VALUE = "super-secret-value-036"


@dataclass(frozen=True)
class DockerRunRecord:
    command: tuple[str, ...]
    workdir: str
    workspace_host_path: Path
    image_name: str
    inner_command: tuple[str, ...]


@dataclass(frozen=True)
class DockerFileWrite:
    command_text: str
    relative_path: str
    file_text: str
    stdout: str = "docker command wrote file\n"
    stderr: str = ""
    exit_code: int = 0


class FakeDockerSubprocess:
    def __init__(
        self,
        image_name: str = DOCKER_TEST_IMAGE_NAME,
    ) -> None:
        self.image_name = image_name
        self.original_subprocess_run = subprocess.run
        self.commands: list[tuple[str, ...]] = []
        self.image_inspects: list[tuple[str, ...]] = []
        self.docker_runs: list[DockerRunRecord] = []
        self.file_writes: list[DockerFileWrite] = []
        self.pytest_failure_file: str = ""
        self.pytest_failure_stdout: str = "pytest stdout from docker\n"
        self.pytest_failure_stderr: str = "pytest failed from docker\n"

    def install(self, monkeypatch) -> None:
        monkeypatch.setattr(
            sandbox_provider_module.subprocess,
            "run",
            self.run,
        )

    def add_file_write(
        self,
        *,
        command_text: str,
        relative_path: str,
        file_text: str,
        stdout: str = "docker command wrote file\n",
        stderr: str = "",
        exit_code: int = 0,
    ) -> None:
        self.file_writes.append(
            DockerFileWrite(
                command_text=command_text,
                relative_path=relative_path,
                file_text=file_text,
                stdout=stdout,
                stderr=stderr,
                exit_code=exit_code,
            )
        )

    def fail_pytest_when_file_exists(
        self,
        relative_path: str,
        *,
        stdout: str = "pytest stdout from docker\n",
        stderr: str = "pytest failed from docker\n",
    ) -> None:
        self.pytest_failure_file = relative_path
        self.pytest_failure_stdout = stdout
        self.pytest_failure_stderr = stderr

    def run(
        self,
        command: Sequence[object],
        *args: object,
        **kwargs: object,
    ) -> subprocess.CompletedProcess[str]:
        command_parts = tuple(str(part) for part in command)

        if command_parts[:1] != ("docker",):
            return self.original_subprocess_run(
                command,
                *args,
                **kwargs,
            )

        self.commands.append(command_parts)

        capture_output = kwargs.get("capture_output")
        text = kwargs.get("text")
        check = kwargs.get("check", False)

        assert capture_output is True
        assert text is True
        assert check is False

        if command_parts[:3] == ("docker", "image", "inspect"):
            return self._handle_image_inspect(command_parts)

        if command_parts[:3] == ("docker", "run", "--rm"):
            return self._handle_docker_run(command_parts)

        return subprocess.CompletedProcess(
            args=command_parts,
            returncode=99,
            stdout="",
            stderr=f"Unexpected Docker command: {command_parts}",
        )

    def _handle_image_inspect(
        self,
        command_parts: tuple[str, ...],
    ) -> subprocess.CompletedProcess[str]:
        self.image_inspects.append(command_parts)

        return subprocess.CompletedProcess(
            args=command_parts,
            returncode=0,
            stdout="[]",
            stderr="",
        )

    def _handle_docker_run(
        self,
        command_parts: tuple[str, ...],
    ) -> subprocess.CompletedProcess[str]:
        workdir = self._extract_workdir(command_parts)
        workspace_host_path = self._extract_workspace_host_path(command_parts)
        image_index = self._find_image_index(command_parts)
        image_name = command_parts[image_index]
        inner_command = command_parts[image_index + 1 :]

        assert workdir == WORKSPACE_PATH or workdir.startswith(f"{WORKSPACE_PATH}/")
        assert workspace_host_path.exists()

        self.docker_runs.append(
            DockerRunRecord(
                command=command_parts,
                workdir=workdir,
                workspace_host_path=workspace_host_path,
                image_name=image_name,
                inner_command=inner_command,
            )
        )

        return self._result_for_inner_command(
            command_parts=command_parts,
            workspace_host_path=workspace_host_path,
            inner_command=inner_command,
        )

    def _result_for_inner_command(
        self,
        *,
        command_parts: tuple[str, ...],
        workspace_host_path: Path,
        inner_command: tuple[str, ...],
    ) -> subprocess.CompletedProcess[str]:
        inner_command_text = " ".join(inner_command)
        matching_file_writes = [
            file_write
            for file_write in self.file_writes
            if file_write.command_text in inner_command_text
        ]

        if matching_file_writes:
            for file_write in matching_file_writes:
                target_path = workspace_host_path / file_write.relative_path
                target_path.parent.mkdir(parents=True, exist_ok=True)
                target_path.write_text(file_write.file_text, encoding="utf-8")

            result_file_write = matching_file_writes[-1]

            return subprocess.CompletedProcess(
                args=command_parts,
                returncode=result_file_write.exit_code,
                stdout=result_file_write.stdout,
                stderr=result_file_write.stderr,
            )

        if inner_command[:2] == ("poetry", "install"):
            return subprocess.CompletedProcess(
                args=command_parts,
                returncode=0,
                stdout="poetry install passed from docker\n",
                stderr="",
            )

        if self._is_pytest_command(inner_command):
            return self._pytest_result(command_parts, workspace_host_path)

        return subprocess.CompletedProcess(
            args=command_parts,
            returncode=0,
            stdout="docker command completed\n",
            stderr="",
        )

    def _pytest_result(
        self,
        command_parts: tuple[str, ...],
        workspace_host_path: Path,
    ) -> subprocess.CompletedProcess[str]:
        if self.pytest_failure_file:
            failure_path = workspace_host_path / self.pytest_failure_file

            if failure_path.exists():
                return subprocess.CompletedProcess(
                    args=command_parts,
                    returncode=1,
                    stdout=self.pytest_failure_stdout,
                    stderr=self.pytest_failure_stderr,
                )

        return subprocess.CompletedProcess(
            args=command_parts,
            returncode=0,
            stdout="pytest passed from docker\n",
            stderr="",
        )

    def _is_pytest_command(
        self,
        inner_command: tuple[str, ...],
    ) -> bool:
        return inner_command[:3] == ("poetry", "run", "pytest") or inner_command[
            :1
        ] == ("pytest",)

    def _extract_workdir(
        self,
        command_parts: tuple[str, ...],
    ) -> str:
        assert "-w" in command_parts
        workdir_index = command_parts.index("-w")
        assert workdir_index + 1 < len(command_parts)
        return command_parts[workdir_index + 1]

    def _find_image_index(
        self,
        command_parts: tuple[str, ...],
    ) -> int:
        assert self.image_name in command_parts
        return command_parts.index(self.image_name)

    def _extract_workspace_host_path(
        self,
        command_parts: tuple[str, ...],
    ) -> Path:
        for index, command_part in enumerate(command_parts):
            if command_part in {"-v", "--volume"}:
                assert index + 1 < len(command_parts)
                host_path = self._workspace_host_path_from_volume_text(
                    command_parts[index + 1]
                )

                if host_path is not None:
                    return host_path

            if command_part.startswith("--mount="):
                host_path = self._workspace_host_path_from_mount_text(
                    command_part.removeprefix("--mount=")
                )

                if host_path is not None:
                    return host_path

            if command_part == "--mount":
                assert index + 1 < len(command_parts)
                host_path = self._workspace_host_path_from_mount_text(
                    command_parts[index + 1]
                )

                if host_path is not None:
                    return host_path

        raise AssertionError("Docker run command did not mount /workspace.")

    def _workspace_host_path_from_volume_text(
        self,
        volume_text: str,
    ) -> Path | None:
        readonly_suffix = f":{WORKSPACE_PATH}:ro"

        if volume_text.endswith(readonly_suffix):
            raise AssertionError("Docker /workspace bind mount must be writable.")

        writable_suffix = f":{WORKSPACE_PATH}"

        if volume_text.endswith(writable_suffix):
            host_path_text = volume_text[: -len(writable_suffix)]
            return Path(host_path_text)

        return None

    def _workspace_host_path_from_mount_text(
        self,
        mount_text: str,
    ) -> Path | None:
        mount_parts = {}
        mount_flags = set()

        for raw_part in mount_text.split(","):
            cleaned_part = raw_part.strip()

            if "=" not in cleaned_part:
                mount_flags.add(cleaned_part)
                continue

            key, value = cleaned_part.split("=", 1)
            mount_parts[key.strip()] = value.strip()

        target_path = (
            mount_parts.get("target")
            or mount_parts.get("dst")
            or mount_parts.get("destination")
        )
        source_path = mount_parts.get("src") or mount_parts.get("source")

        if target_path != WORKSPACE_PATH or source_path is None:
            return None

        if "readonly" in mount_flags or "ro" in mount_flags:
            raise AssertionError("Docker /workspace bind mount must be writable.")

        return Path(source_path)


class DockerBindMountAgentProvider:
    def __init__(
        self,
        *,
        command_text: str,
        success_message: str,
    ) -> None:
        self.command_text = command_text
        self.success_message = success_message
        self.prompts: list[str] = []
        self.commands: list[list[str]] = []
        self.command_results: list[CommandResult] = []
        self.run_count = 0
        self.sandbox_handle: Any | None = None

    def attach_sandbox_handle(self, sandbox_handle: Any) -> None:
        self.sandbox_handle = sandbox_handle

    def i_agent_provider_run(self, prompt: str) -> AgentResponse:
        self.prompts.append(prompt)
        self.run_count += 1

        if self.sandbox_handle is None:
            return AgentResponse(
                output="",
                error="Docker bind-mount test agent did not receive a sandbox handle.",
            )

        command = [sys.executable, "-c", self.command_text]
        self.commands.append(command)

        command_result = self.sandbox_handle.i_sandboxhandle_run(command)
        self.command_results.append(command_result)

        if command_result.failed:
            return AgentResponse(
                output=command_result.stdout,
                error=command_result.stderr or "Docker bind-mount test agent failed.",
            )

        return AgentResponse(
            output=f"{self.success_message}\n{command_result.stdout}{COMPLETE_TOKEN}",
        )


def test_ralph_docker_bind_mount_success_commits_and_removes_clean_worktree(
    monkeypatch,
    tmp_path,
) -> None:
    repo_path = _build_docker_temp_repo(tmp_path)
    fake_agent = DockerBindMountAgentProvider(
        command_text="write docker success marker 036",
        success_message="Docker bind-mount success agent completed.",
    )
    fake_docker = FakeDockerSubprocess()
    display = SilentDisplay()
    close_calls: list[dict[str, object]] = []
    redacted_commands: list[str] = []
    marker_file = "docker_success_marker.txt"
    marker_text = "Docker bind-mount success marker 036."
    issue = GitHubIssue(
        number=36,
        title="Add Docker bind-mount integration tracer bullet",
        body="Docker mode should edit the mounted worktree through the sandbox seam.",
        labels=("tracer bullet",),
    )

    _configure_docker_mode(monkeypatch)
    _attach_sandbox_to_agent(monkeypatch, fake_agent)
    _stub_github_issue_close(monkeypatch, close_calls)
    _spy_on_docker_redaction(monkeypatch, redacted_commands)
    fake_docker.install(monkeypatch)
    fake_docker.add_file_write(
        command_text=fake_agent.command_text,
        relative_path=marker_file,
        file_text=marker_text,
        stdout="docker agent stdout 036\n",
        stderr="docker agent stderr 036\n",
        exit_code=0,
    )

    result = i_ralph_run(
        issues=[issue],
        repo_path=repo_path,
        agent_provider=fake_agent,
        max_iterations=1,
        prompt_template=_docker_prompt_template(),
        display=display,
    )

    display_text = "\n".join(display.messages)
    ralph_branch = _find_single_ralph_branch(repo_path, issue_number=36)
    committed_marker_text = _run_git(
        repo_path, "show", f"{ralph_branch}:{marker_file}"
    ).stdout
    worktree_path = repo_path / ".ai_coder" / "ai_coder_worktrees" / ralph_branch
    redacted_command_text = _joined_redacted_command_text(redacted_commands)

    assert result.status == RALPH_STATUS_COMPLETE
    assert result.completed is True
    assert result.selected_issue == issue
    assert fake_agent.run_count == 1
    assert fake_agent.prompts == [result.prompt]
    assert fake_agent.sandbox_handle is not None
    assert len(fake_agent.commands) == 1
    assert issue.body not in " ".join(fake_agent.commands[0])
    assert fake_agent.command_results[0].stdout == "docker agent stdout 036\n"
    assert fake_agent.command_results[0].stderr == "docker agent stderr 036\n"
    assert fake_agent.command_results[0].exit_code == 0
    assert fake_agent.command_results[0].succeeded is True
    assert (
        "docker",
        "image",
        "inspect",
        DOCKER_TEST_IMAGE_NAME,
    ) in fake_docker.image_inspects
    assert fake_docker.docker_runs
    assert all(record.workdir == WORKSPACE_PATH for record in fake_docker.docker_runs)
    assert all(
        record.image_name == DOCKER_TEST_IMAGE_NAME
        for record in fake_docker.docker_runs
    )
    assert any(
        record.workspace_host_path.name == ralph_branch
        for record in fake_docker.docker_runs
    )
    assert marker_text in committed_marker_text
    assert "Tests passed." in display_text
    assert "Commit created:" in result.message
    assert "Removed clean worktree:" in result.message
    assert not worktree_path.exists()
    assert close_calls == [
        {
            "issue": issue,
            "tests_passed": True,
            "committed": True,
        }
    ]
    assert DOCKER_SECRET_VALUE not in display_text
    assert DOCKER_SECRET_VALUE not in redacted_command_text
    assert f"{DOCKER_SECRET_NAME}=<redacted>" in redacted_command_text


def test_ralph_docker_bind_mount_failed_tests_preserves_worktree(
    monkeypatch,
    tmp_path,
) -> None:
    repo_path = _build_docker_temp_repo(tmp_path)
    fake_agent = DockerBindMountAgentProvider(
        command_text="write docker failure marker 036",
        success_message="Docker bind-mount failure agent completed.",
    )
    fake_docker = FakeDockerSubprocess()
    display = SilentDisplay()
    close_calls: list[dict[str, object]] = []
    redacted_commands: list[str] = []
    marker_file = "docker_failure_marker.txt"
    failing_test_file = "tests/test_docker_bind_mount_failure_036.py"
    issue = GitHubIssue(
        number=36,
        title="Add Docker bind-mount integration tracer bullet",
        body="Docker mode should preserve failed worktrees.",
        labels=("tracer bullet",),
    )

    _configure_docker_mode(monkeypatch)
    _attach_sandbox_to_agent(monkeypatch, fake_agent)
    _stub_github_issue_close(monkeypatch, close_calls)
    _spy_on_docker_redaction(monkeypatch, redacted_commands)
    fake_docker.install(monkeypatch)
    fake_docker.add_file_write(
        command_text=fake_agent.command_text,
        relative_path=marker_file,
        file_text="Docker bind-mount failure marker 036.",
        stdout="docker failure agent stdout 036\n",
    )
    fake_docker.add_file_write(
        command_text=fake_agent.command_text,
        relative_path=failing_test_file,
        file_text='def test_docker_bind_mount_failure_036():\n    assert False, "Docker failure path 036"\n',
        stdout="docker failure agent stdout 036\n",
    )
    fake_docker.fail_pytest_when_file_exists(
        failing_test_file,
        stdout="pytest stdout from docker\n",
        stderr="pytest failed from docker\n",
    )

    result = i_ralph_run(
        issues=[issue],
        repo_path=repo_path,
        agent_provider=fake_agent,
        max_iterations=1,
        prompt_template=_docker_prompt_template(),
        display=display,
    )

    display_text = "\n".join(display.messages)
    ralph_branch = _find_single_ralph_branch(repo_path, issue_number=36)
    preserved_worktree_path = (
        repo_path / ".ai_coder" / "ai_coder_worktrees" / ralph_branch
    )
    preserved_status = _run_git(preserved_worktree_path, "status", "--porcelain").stdout
    host_log = _run_git(repo_path, "log", "--oneline", "--all").stdout
    redacted_command_text = _joined_redacted_command_text(redacted_commands)

    assert result.status == RALPH_STATUS_FAILED
    assert result.completed is False
    assert result.selected_issue == issue
    assert result.orchestrator_result is not None
    assert result.orchestrator_result.completed is True
    assert COMPLETE_TOKEN in result.orchestrator_result.final_output
    assert fake_agent.run_count == 1
    assert fake_agent.command_results[0].succeeded is True
    assert fake_agent.command_results[0].stdout == "docker failure agent stdout 036\n"
    assert "Tests failed" in result.message
    assert "pytest stdout from docker" in result.message
    assert "pytest failed from docker" in result.message
    assert "Commit created:" not in result.message
    assert "Phase: tests" in display_text
    assert "Tests failed." in display_text
    assert "Stdout: pytest stdout from docker" in display_text
    assert "Stderr: pytest failed from docker" in display_text
    assert "Phase: cleanup" in display_text
    assert "Preserved worktree:" in display_text
    assert preserved_worktree_path.exists()
    assert (preserved_worktree_path / marker_file).exists()
    assert (preserved_worktree_path / failing_test_file).exists()
    assert failing_test_file in preserved_status
    assert issue.title not in host_log
    assert close_calls == [
        {
            "issue": issue,
            "tests_passed": False,
            "committed": False,
        }
    ]
    assert DOCKER_SECRET_VALUE not in display_text
    assert DOCKER_SECRET_VALUE not in redacted_command_text
    assert f"{DOCKER_SECRET_NAME}=<redacted>" in redacted_command_text


def _configure_docker_mode(monkeypatch) -> None:
    monkeypatch.setattr(ralph_module.setup_config, "test_command", "")
    monkeypatch.setattr(repository_context_module.setup_config, "test_command", "")
    monkeypatch.setattr(ralph_module.setup_config, "sandbox_mode", "docker")
    monkeypatch.setattr(sandbox_provider_module.setup_config, "sandbox_mode", "docker")
    monkeypatch.setattr(
        sandbox_provider_module.setup_config,
        "docker_image_name",
        DOCKER_TEST_IMAGE_NAME,
    )
    monkeypatch.setattr(
        sandbox_provider_module.setup_config,
        "docker_env_allowlist",
        ("PYTHONUNBUFFERED",),
    )
    monkeypatch.setattr(
        sandbox_provider_module.setup_config,
        "docker_secret_env_allowlist",
        (DOCKER_SECRET_NAME,),
    )
    monkeypatch.setattr(
        ralph_module.setup_config,
        "commit_message_template",
        "RALPH: issue #{issue_number} - {issue_title}",
    )
    monkeypatch.setenv(DOCKER_SECRET_NAME, DOCKER_SECRET_VALUE)


def _attach_sandbox_to_agent(
    monkeypatch,
    fake_agent: DockerBindMountAgentProvider,
) -> None:
    original_agent_builder = ralph_module._build_default_agent_provider

    def attach_sandbox_to_test_agent(agent_provider, sandbox_handle):
        if agent_provider is fake_agent:
            fake_agent.attach_sandbox_handle(sandbox_handle)
            return fake_agent

        return original_agent_builder(agent_provider, sandbox_handle)

    monkeypatch.setattr(
        ralph_module,
        "_build_default_agent_provider",
        attach_sandbox_to_test_agent,
    )


def _stub_github_issue_close(
    monkeypatch,
    close_calls: list[dict[str, object]],
) -> None:
    def fake_github_issue_close(
        issue,
        tests_passed,
        committed,
        **kwargs,
    ):
        close_calls.append(
            {
                "issue": issue,
                "tests_passed": tests_passed,
                "committed": committed,
            }
        )
        return GitHubIssueCloseResult(
            issue_number=issue.number,
            closed=False,
            ready=False,
            blocked_reason="GitHub issue closing is stubbed in the Docker integration test.",
            message="GitHub issue closing is stubbed in the Docker integration test.",
        )

    monkeypatch.setattr(
        ralph_module,
        "i_github_issue_close",
        fake_github_issue_close,
    )


def _spy_on_docker_redaction(
    monkeypatch,
    redacted_commands: list[str],
) -> None:
    original_redact = sandbox_provider_module.i_dockercommand_redact

    def fake_redact(command, secret_env_names):
        redacted_command = original_redact(command, secret_env_names)
        redacted_commands.append(" ".join(redacted_command))
        return redacted_command

    monkeypatch.setattr(
        sandbox_provider_module,
        "i_dockercommand_redact",
        fake_redact,
    )


def _joined_redacted_command_text(
    redacted_commands: list[str],
) -> str:
    return "\n".join(redacted_commands)


def _docker_prompt_template() -> str:
    return (
        "Issue #{{ISSUE_NUMBER}}\n"
        "Title: {{ISSUE_TITLE}}\n"
        "Body: {{ISSUE_BODY}}\n"
        "Labels: {{ISSUE_LABELS}}\n"
        "Branch: {{BRANCH_NAME}}\n"
        "Worktree: {{WORKTREE_PATH}}\n"
        "Repository context:\n{{REPOSITORY_CONTEXT}}\n"
        "Complete token: {{COMPLETE_TOKEN}}\n"
    )


def _build_docker_temp_repo(tmp_path: Path) -> Path:
    repo_path = tmp_path / "r"
    repo_path.mkdir()

    _run_process(["git", "init"], cwd=repo_path)
    _run_git(repo_path, "config", "user.name", "RALPH Docker Test")
    _run_git(repo_path, "config", "user.email", "ralph-docker@example.test")

    tests_path = repo_path / "tests"
    tests_path.mkdir()
    (tests_path / "test_smoke.py").write_text(
        "def test_smoke_passes():\n" "    assert 1 + 1 == 2\n",
        encoding="utf-8",
    )
    (repo_path / "pyproject.toml").write_text(
        "[tool.pytest.ini_options]\n" 'testpaths = ["tests"]\n',
        encoding="utf-8",
    )
    (repo_path / "poetry.lock").write_text("", encoding="utf-8")
    (repo_path / "README.md").write_text(
        "# Docker Bind Mount Sample Repo\n", encoding="utf-8"
    )
    (repo_path / ".gitignore").write_text(
        "__pycache__/\n" "*.py[cod]\n" ".pytest_cache/\n",
        encoding="utf-8",
    )

    _run_git(
        repo_path,
        "add",
        "README.md",
        ".gitignore",
        "pyproject.toml",
        "poetry.lock",
        "tests/test_smoke.py",
    )
    _run_git(repo_path, "commit", "-m", "Initial Docker bind mount sample repo")

    return repo_path


def _find_single_ralph_branch(repo_path: Path, issue_number: int) -> str:
    branch_result = _run_git(repo_path, "branch", "--format=%(refname:short)")
    branch_prefix = f"ralph-issue-{issue_number}-"
    matching_branches = [
        branch_name.strip()
        for branch_name in branch_result.stdout.splitlines()
        if branch_name.strip().startswith(branch_prefix)
    ]

    assert len(matching_branches) == 1
    return matching_branches[0]


def _run_git(repo_path: Path, *arguments: str) -> subprocess.CompletedProcess[str]:
    return _run_process(["git", *arguments], cwd=repo_path)


def _run_process(
    command: list[str],
    cwd: Path,
) -> subprocess.CompletedProcess[str]:
    completed_process = subprocess.run(
        command,
        cwd=cwd,
        capture_output=True,
        text=True,
        check=False,
    )

    assert completed_process.returncode == 0, (
        f"Command failed: {command}\n"
        f"cwd: {cwd}\n"
        f"stdout:\n{completed_process.stdout}\n"
        f"stderr:\n{completed_process.stderr}"
    )

    return completed_process
