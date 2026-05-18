# tests/ralph/test_release1_end_to_end.py
from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from typing import Any

import ai_coder.ralph.ralph as ralph_module
import ai_coder.repository_context.repository_context as repository_context_module
import ai_coder.sandbox_provider.sandbox_provider as sandbox_provider_module
from ai_coder.agent_provider import COMPLETE_TOKEN, AgentResponse
from ai_coder.display import SilentDisplay

from ai_coder.github_issues import GitHubIssue, GitHubIssueCloseResult

from ai_coder.ralph import RALPH_STATUS_COMPLETE, RALPH_STATUS_FAILED, i_ralph_run

from ai_coder.sandbox_provider import CommandResult


class Release1FileWritingAgentProvider:
    def __init__(
        self,
        marker_file: str = "release1_marker.txt",
        marker_text: str = "Release 1 marker written through the sandbox seam.",
    ) -> None:
        self.marker_file = marker_file
        self.marker_text = marker_text
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
                error="Release 1 test agent did not receive a sandbox handle.",
            )

        command = [
            sys.executable,
            "-c",
            (
                "from pathlib import Path\n"
                f"Path({self.marker_file!r}).write_text("
                f"{self.marker_text!r}, encoding='utf-8')\n"
            ),
        ]
        self.commands.append(command)

        command_result = self.sandbox_handle.i_sandboxhandle_run(command)
        self.command_results.append(command_result)

        if command_result.failed:
            return AgentResponse(
                output=command_result.stdout,
                error=(
                    command_result.stderr
                    or "Release 1 test agent failed to write the marker file."
                ),
            )

        return AgentResponse(
            output=f"Release 1 test agent wrote {self.marker_file}.\n{COMPLETE_TOKEN}",
        )


class Release1FailingTestAgentProvider:
    def __init__(
        self,
        failing_test_file: str = "tests/test_release1_failure.py",
        marker_file: str = "release1_failure_marker.txt",
    ) -> None:
        self.failing_test_file = failing_test_file
        self.marker_file = marker_file
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
                error="Release 1 failing test agent did not receive a sandbox handle.",
            )

        command = [
            sys.executable,
            "-c",
            (
                "from pathlib import Path\n"
                f"Path({self.failing_test_file!r}).write_text("
                "'def test_release1_failure_is_preserved():\\n"
                '    assert False, "Release 1 failure path"\\n\', '
                "encoding='utf-8')\n"
                f"Path({self.marker_file!r}).write_text("
                "'Release 1 failure marker written through the sandbox seam.', "
                "encoding='utf-8')\n"
            ),
        ]
        self.commands.append(command)

        command_result = self.sandbox_handle.i_sandboxhandle_run(command)
        self.command_results.append(command_result)

        if command_result.failed:
            return AgentResponse(
                output=command_result.stdout,
                error=(
                    command_result.stderr
                    or "Release 1 failing test agent failed to write files."
                ),
            )

        return AgentResponse(
            output=(
                "Release 1 failing test agent wrote a failing pytest file.\n"
                f"{COMPLETE_TOKEN}"
            ),
        )


def test_release1_end_to_end_success_commits_after_tests_pass(
    monkeypatch,
    tmp_path,
) -> None:
    repo_path = _build_release1_temp_repo(tmp_path)
    fake_agent = Release1FileWritingAgentProvider()
    display = SilentDisplay()
    close_calls: list[dict[str, object]] = []
    issue = GitHubIssue(
        number=27,
        title="R1 e2e tracer",
        body=(
            "Connect the Release 1 pieces so RALPH proves the safe local "
            "single-issue workflow."
        ),
        labels=("tracer bullet",),
    )

    monkeypatch.setattr(ralph_module.setup_config, "test_command", "")
    monkeypatch.setattr(repository_context_module.setup_config, "test_command", "")
    monkeypatch.setattr(ralph_module.setup_config, "sandbox_mode", "local")
    monkeypatch.setattr(sandbox_provider_module.setup_config, "sandbox_mode", "local")
    monkeypatch.setattr(
        ralph_module.setup_config,
        "commit_message_template",
        "RALPH: issue #{issue_number} - {issue_title}",
    )

    original_agent_builder = ralph_module._build_default_agent_provider

    def attach_sandbox_to_test_agent(agent_provider, sandbox_handle):
        if agent_provider is fake_agent:
            fake_agent.attach_sandbox_handle(sandbox_handle)
            return fake_agent

        return original_agent_builder(agent_provider, sandbox_handle)

    def fake_github_issue_close(issue, tests_passed, committed):
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
            message="GitHub issue closing is stubbed in this tracer-bullet slice.",
        )

    monkeypatch.setattr(
        ralph_module,
        "_build_default_agent_provider",
        attach_sandbox_to_test_agent,
    )
    monkeypatch.setattr(
        ralph_module,
        "i_github_issue_close",
        fake_github_issue_close,
    )

    result = i_ralph_run(
        issues=[issue],
        repo_path=repo_path,
        agent_provider=fake_agent,
        max_iterations=1,
        prompt_template=(
            "Issue #{{ISSUE_NUMBER}}\n"
            "Title: {{ISSUE_TITLE}}\n"
            "Body: {{ISSUE_BODY}}\n"
            "Labels: {{ISSUE_LABELS}}\n"
            "Branch: {{BRANCH_NAME}}\n"
            "Worktree: {{WORKTREE_PATH}}\n"
            "Repository context:\n{{REPOSITORY_CONTEXT}}\n"
            "Complete token: {{COMPLETE_TOKEN}}\n"
        ),
        display=display,
    )

    display_text = "\n".join(display.messages)
    ralph_branch = _find_single_ralph_branch(repo_path, issue_number=27)
    committed_marker_text = _run_git(
        repo_path,
        "show",
        f"{ralph_branch}:{fake_agent.marker_file}",
    ).stdout
    worktree_path = repo_path / ".ai_coder" / "ai_coder_worktrees" / ralph_branch

    assert result.status == RALPH_STATUS_COMPLETE
    assert result.completed is True
    assert result.selected_issue == issue
    assert f"Issue #{issue.number}" in result.prompt
    assert issue.title in result.prompt
    assert issue.body in result.prompt
    assert "Repository context:" in result.prompt
    assert "tests/" in result.prompt
    assert fake_agent.run_count == 1
    assert fake_agent.prompts == [result.prompt]
    assert fake_agent.sandbox_handle is not None
    assert len(fake_agent.commands) == 1
    assert fake_agent.command_results[0].succeeded is True
    assert issue.body not in " ".join(fake_agent.commands[0])
    assert "Phase: worktree" in display_text
    assert "Phase: sandbox" in display_text
    assert "Phase: prompt" in display_text
    assert "Phase: agent" in display_text
    assert "Phase: tests" in display_text
    assert "Phase: commit" in display_text
    assert "Test command: pytest" in display_text
    assert "Tests passed." in display_text
    assert "Commit created:" in result.message
    assert "Removed clean worktree:" in result.message
    assert "Preserved worktree" not in result.message
    assert fake_agent.marker_text in committed_marker_text
    assert not worktree_path.exists()
    assert close_calls == [
        {
            "issue": issue,
            "tests_passed": True,
            "committed": True,
        }
    ]


def test_release1_end_to_end_failure_preserves_worktree(
    monkeypatch,
    tmp_path,
) -> None:
    repo_path = _build_release1_temp_repo(tmp_path)
    fake_agent = Release1FailingTestAgentProvider()
    display = SilentDisplay()
    close_calls: list[dict[str, object]] = []
    issue = GitHubIssue(
        number=28,
        title="R1 failure preserve",
        body=(
            "Prove RALPH preserves the worktree when the agent completes "
            "but final pytest fails."
        ),
        labels=("tracer bullet",),
    )

    monkeypatch.setattr(ralph_module.setup_config, "test_command", "")
    monkeypatch.setattr(repository_context_module.setup_config, "test_command", "")
    monkeypatch.setattr(ralph_module.setup_config, "sandbox_mode", "local")
    monkeypatch.setattr(sandbox_provider_module.setup_config, "sandbox_mode", "local")
    monkeypatch.setattr(
        ralph_module.setup_config,
        "commit_message_template",
        "RALPH: issue #{issue_number} - {issue_title}",
    )

    original_agent_builder = ralph_module._build_default_agent_provider

    def attach_sandbox_to_test_agent(agent_provider, sandbox_handle):
        if agent_provider is fake_agent:
            fake_agent.attach_sandbox_handle(sandbox_handle)
            return fake_agent

        return original_agent_builder(agent_provider, sandbox_handle)

    def fake_github_issue_close(issue, tests_passed, committed):
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
            message="Issue was not closed because tests have not passed and committed work is not confirmed.",
        )

    monkeypatch.setattr(
        ralph_module,
        "_build_default_agent_provider",
        attach_sandbox_to_test_agent,
    )
    monkeypatch.setattr(
        ralph_module,
        "i_github_issue_close",
        fake_github_issue_close,
    )

    result = i_ralph_run(
        issues=[issue],
        repo_path=repo_path,
        agent_provider=fake_agent,
        max_iterations=1,
        prompt_template=(
            "Issue #{{ISSUE_NUMBER}}\n"
            "Title: {{ISSUE_TITLE}}\n"
            "Body: {{ISSUE_BODY}}\n"
            "Labels: {{ISSUE_LABELS}}\n"
            "Branch: {{BRANCH_NAME}}\n"
            "Worktree: {{WORKTREE_PATH}}\n"
            "Repository context:\n{{REPOSITORY_CONTEXT}}\n"
            "Complete token: {{COMPLETE_TOKEN}}\n"
        ),
        display=display,
    )

    display_text = "\n".join(display.messages)
    ralph_branch = _find_single_ralph_branch(repo_path, issue_number=28)
    preserved_worktree_path = (
        repo_path / ".ai_coder" / "ai_coder_worktrees" / ralph_branch
    )
    preserved_status = _run_git(
        preserved_worktree_path,
        "status",
        "--porcelain",
    ).stdout
    host_log = _run_git(
        repo_path,
        "log",
        "--oneline",
        "--all",
    ).stdout

    assert result.status == RALPH_STATUS_FAILED
    assert result.completed is False
    assert result.selected_issue == issue
    assert result.orchestrator_result is not None
    assert result.orchestrator_result.completed is True
    assert fake_agent.run_count == 1
    assert fake_agent.prompts == [result.prompt]
    assert fake_agent.sandbox_handle is not None
    assert len(fake_agent.commands) == 1
    assert fake_agent.command_results[0].succeeded is True
    assert issue.body not in " ".join(fake_agent.commands[0])
    assert "Tests failed" in result.message
    assert "Preserved worktree:" in result.message
    assert "Commit created:" not in result.message
    assert "Phase: tests" in display_text
    assert "Tests failed." in display_text
    assert "Phase: cleanup" in display_text
    assert "Preserved worktree:" in display_text
    assert preserved_worktree_path.exists()
    assert (preserved_worktree_path / fake_agent.failing_test_file).exists()
    assert (preserved_worktree_path / fake_agent.marker_file).exists()
    assert fake_agent.failing_test_file in preserved_status
    assert issue.title not in host_log
    assert close_calls == [
        {
            "issue": issue,
            "tests_passed": False,
            "committed": False,
        }
    ]


def _build_release1_temp_repo(tmp_path: Path) -> Path:
    repo_path = tmp_path / "r"
    repo_path.mkdir()

    _run_process(["git", "init"], cwd=repo_path)
    _run_git(repo_path, "config", "user.name", "RALPH Release 1 Test")
    _run_git(repo_path, "config", "user.email", "ralph-release1@example.test")

    tests_path = repo_path / "tests"
    tests_path.mkdir()
    (tests_path / "test_smoke.py").write_text(
        "def test_smoke_passes():\n" "    assert 1 + 1 == 2\n",
        encoding="utf-8",
    )
    (repo_path / "README.md").write_text(
        "# Release 1 Sample Repo\n",
        encoding="utf-8",
    )
    (repo_path / ".gitignore").write_text(
        "__pycache__/\n" "*.py[cod]\n" ".pytest_cache/\n",
        encoding="utf-8",
    )

    _run_git(repo_path, "add", "README.md", ".gitignore", "tests/test_smoke.py")
    _run_git(repo_path, "commit", "-m", "Initial Release 1 sample repo")

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
