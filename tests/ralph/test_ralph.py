# tests/ralph/test_ralph.py
from ai_coder.agent_provider import COMPLETE_TOKEN, MockAgentProvider
from ai_coder.sync_out import SyncMergeResult


from ai_coder.github_issues import GitHubIssue
from ai_coder.repository_context import (
    RepositoryContextResult,
    RepositoryStartResult,
)

from ai_coder.sandbox_provider import (
    CommandResult,
    LocalSandboxProvider,
    SandboxStartResult,
)


from ai_coder.ralph import i_ralph_run


from ai_coder.ralph import (
    RALPH_RESULT_STATUSES,
    RALPH_STATUS_BLOCKED,
    RALPH_STATUS_COMPLETE,
    RALPH_STATUS_FAILED,
    RALPH_STATUS_INCOMPLETE,
    RALPH_STATUS_NO_CHANGES,
)


from ai_coder.test_runner import TestRunResult
from ai_coder.worktree_manager import WorktreeCleanupResult, WorktreeCreateResult

import ai_coder.ralph.ralph as ralph_module
from ai_coder.setup_config import c_setup_config


def _refresh_ralph_config() -> None:
    c_setup_config._instance = None
    ralph_module.setup_config = c_setup_config.get_instance()
    ralph_module.logger = ralph_module.setup_config.get_logger()


def test_ralph_result_status_contract_lists_all_supported_statuses() -> None:
    assert RALPH_STATUS_COMPLETE == "complete"
    assert RALPH_STATUS_INCOMPLETE == "incomplete"
    assert RALPH_STATUS_FAILED == "failed"
    assert RALPH_STATUS_BLOCKED == "blocked"
    assert RALPH_STATUS_NO_CHANGES == "no_changes"
    assert RALPH_RESULT_STATUSES == (
        "complete",
        "incomplete",
        "failed",
        "blocked",
        "no_changes",
    )


class FakeRalphAgentSandboxHandle:
    def __init__(self, worktree_path, command_result: CommandResult) -> None:
        self.worktree_path = worktree_path
        self.working_directory = worktree_path
        self.command_result = command_result
        self.commands: list[list[str]] = []

    def i_sandboxhandle_run(self, command: list[str], cwd=None) -> CommandResult:
        self.commands.append(command)
        return self.command_result

    def i_sandboxhandle_close(self) -> None:
        return None


def _patch_clean_repository_context(monkeypatch, tmp_path) -> None:
    def fake_repository_start(repo_path):
        return RepositoryStartResult(
            repo_path=tmp_path,
            ready=True,
            message="Repository context discovered. Repository is clean.",
            active_branch="main",
            is_clean=True,
            status_output="",
            blocked_reason="",
        )

    monkeypatch.setattr(
        ralph_module,
        "i_repository_start",
        fake_repository_start,
    )


def _patch_successful_worktree_create(monkeypatch, tmp_path) -> None:
    def fake_worktree_create(
        repo_path,
        issue_number,
        issue_title,
        worktree_root=None,
    ):
        worktree_path = tmp_path / "worktree"
        worktree_path.mkdir(parents=True, exist_ok=True)

        return WorktreeCreateResult(
            repo_path=tmp_path,
            worktree_path=worktree_path,
            branch_name=f"ralph-issue-{issue_number}-test-worktree",
            command=(
                "git",
                "-C",
                str(tmp_path),
                "worktree",
                "add",
                "-b",
                f"ralph-issue-{issue_number}-test-worktree",
                str(worktree_path),
            ),
            created=True,
            message="Created Git worktree: test worktree.",
        )

    monkeypatch.setattr(
        ralph_module,
        "i_worktree_create",
        fake_worktree_create,
    )


def _patch_successful_worktree_cleanup(monkeypatch, tmp_path) -> None:
    def fake_worktree_cleanup(
        repo_path,
        worktree_path,
        completed,
        has_uncommitted_changes=None,
    ):
        if completed:
            return WorktreeCleanupResult(
                worktree_path=worktree_path,
                removed=True,
                preserved=False,
                reason="removed_clean_worktree",
                message=f"Removed clean worktree: {worktree_path}",
            )

        return WorktreeCleanupResult(
            worktree_path=worktree_path,
            removed=False,
            preserved=True,
            reason="run_incomplete",
            message=f"Preserved worktree: {worktree_path}. RALPH did not complete.",
        )

    monkeypatch.setattr(
        ralph_module,
        "i_worktree_cleanup",
        fake_worktree_cleanup,
    )


def _patch_successful_sync_merge(monkeypatch) -> None:
    def fake_sync_out_merge(completed: bool):
        return SyncMergeResult(
            merged=completed,
            failed=False,
            message="Sync or commit succeeded.",
        )

    monkeypatch.setattr(
        ralph_module,
        "i_sync_out_merge",
        fake_sync_out_merge,
    )


def _patch_passing_test_runner(monkeypatch) -> None:
    def fake_test_runner_run(
        sandbox_handle=None,
        command=None,
    ):
        return TestRunResult(
            passed=True,
            command=command or ("poetry", "run", "pytest"),
            message="Tests passed through the sandbox seam.",
        )

    monkeypatch.setattr(
        ralph_module,
        "i_test_runner_run",
        fake_test_runner_run,
    )


def _patch_failing_test_runner(monkeypatch) -> None:
    def fake_test_runner_run(
        sandbox_handle=None,
        command=None,
    ):
        return TestRunResult(
            passed=False,
            command=command or ("poetry", "run", "pytest"),
            message="Tests failed through the sandbox seam.",
            stdout="",
            stderr="pytest failed",
            exit_code=1,
        )

    monkeypatch.setattr(
        ralph_module,
        "i_test_runner_run",
        fake_test_runner_run,
    )


def _patch_stubbed_no_change_sync_merge(monkeypatch) -> None:
    def fake_sync_out_merge(completed: bool):
        return SyncMergeResult(
            merged=False,
            failed=False,
            message="Sync or merge is stubbed in this tracer-bullet slice.",
        )

    monkeypatch.setattr(
        ralph_module,
        "i_sync_out_merge",
        fake_sync_out_merge,
    )


def _patch_failed_sync_merge(monkeypatch) -> None:
    def fake_sync_out_merge(completed: bool):
        return SyncMergeResult(
            merged=False,
            failed=True,
            message="Sync or commit failed.",
        )

    monkeypatch.setattr(
        ralph_module,
        "i_sync_out_merge",
        fake_sync_out_merge,
    )


def test_ralph_passes_sandbox_handle_to_test_runner(
    monkeypatch,
    tmp_path,
) -> None:
    _patch_clean_repository_context(monkeypatch, tmp_path)
    _patch_successful_worktree_create(monkeypatch, tmp_path)
    _patch_successful_worktree_cleanup(monkeypatch, tmp_path)
    _patch_successful_sync_merge(monkeypatch)

    fake_sandbox_handle = LocalSandboxProvider(tmp_path / "worktree")
    received_test_runner_handles: list[object] = []

    def fake_sandbox_start(working_directory):
        return SandboxStartResult(
            working_directory=working_directory,
            provider_name="local",
            started=True,
            message="Started local sandbox provider.",
            handle=fake_sandbox_handle,
        )

    def fake_test_runner_run(
        sandbox_handle=None,
        command=None,
    ):
        received_test_runner_handles.append(sandbox_handle)
        return TestRunResult(
            passed=True,
            command=command or ("poetry", "run", "pytest"),
            message="Tests passed through the sandbox seam.",
        )

    monkeypatch.setattr(
        ralph_module,
        "i_sandbox_start",
        fake_sandbox_start,
    )
    monkeypatch.setattr(
        ralph_module,
        "i_test_runner_run",
        fake_test_runner_run,
    )

    provider = MockAgentProvider(responses=["Done\n<promise>COMPLETE</promise>"])

    result = i_ralph_run(
        issues=[
            GitHubIssue(
                number=15,
                title="Add local sandbox provider",
                body="RALPH should pass the sandbox handle to test running.",
                labels=("tracer bullet",),
            )
        ],
        agent_provider=provider,
        repo_path=tmp_path,
    )

    assert result.completed is True
    assert result.status == "complete"
    assert received_test_runner_handles == [fake_sandbox_handle]


def test_ralph_default_agent_provider_runs_through_sandbox_seam(
    monkeypatch,
    tmp_path,
) -> None:
    _patch_clean_repository_context(monkeypatch, tmp_path)
    _patch_successful_worktree_create(monkeypatch, tmp_path)
    _patch_successful_worktree_cleanup(monkeypatch, tmp_path)
    _patch_successful_sync_merge(monkeypatch)

    worktree_path = tmp_path / "worktree"
    fake_sandbox_handle = FakeRalphAgentSandboxHandle(
        worktree_path=worktree_path,
        command_result=CommandResult(
            stdout="Fake test agent completed.\n<promise>COMPLETE</promise>\n",
            stderr="",
            exit_code=0,
        ),
    )

    def fake_sandbox_start(working_directory):
        return SandboxStartResult(
            working_directory=working_directory,
            provider_name="local",
            started=True,
            message="Started local sandbox provider.",
            handle=fake_sandbox_handle,
        )

    def fake_test_runner_run(
        sandbox_handle=None,
        command=None,
    ):
        return TestRunResult(
            passed=True,
            command=command or ("poetry", "run", "pytest"),
            message="Tests passed through the sandbox seam.",
        )

    monkeypatch.setattr(
        ralph_module,
        "i_sandbox_start",
        fake_sandbox_start,
    )
    monkeypatch.setattr(
        ralph_module,
        "i_test_runner_run",
        fake_test_runner_run,
    )

    result = i_ralph_run(
        issues=[
            GitHubIssue(
                number=20,
                title="Add fake test agent provider",
                body="RALPH should use the sandbox-backed fake provider by default.",
                labels=("tracer bullet",),
            )
        ],
        repo_path=tmp_path,
    )

    assert result.completed is True
    assert result.status == "complete"
    assert result.orchestrator_result is not None
    assert result.orchestrator_result.iterations == 1
    assert result.orchestrator_result.error is None
    assert COMPLETE_TOKEN in result.orchestrator_result.final_output
    assert len(fake_sandbox_handle.commands) == 1
    assert COMPLETE_TOKEN in " ".join(fake_sandbox_handle.commands[0])


def test_ralph_returns_failed_when_default_fake_test_agent_fails(
    monkeypatch,
    tmp_path,
) -> None:
    _patch_clean_repository_context(monkeypatch, tmp_path)
    _patch_successful_worktree_create(monkeypatch, tmp_path)

    worktree_path = tmp_path / "worktree"
    cleanup_calls: list[dict[str, object]] = []
    fake_sandbox_handle = FakeRalphAgentSandboxHandle(
        worktree_path=worktree_path,
        command_result=CommandResult(
            stdout="",
            stderr="fake failure",
            exit_code=7,
        ),
    )

    def fake_sandbox_start(working_directory):
        return SandboxStartResult(
            working_directory=working_directory,
            provider_name="local",
            started=True,
            message="Started local sandbox provider.",
            handle=fake_sandbox_handle,
        )

    def fake_test_runner_run(
        sandbox_handle=None,
        command=None,
    ):
        return TestRunResult(
            passed=True,
            command=command or ("poetry", "run", "pytest"),
            message="Tests passed through the sandbox seam.",
        )

    def fake_worktree_cleanup(
        repo_path,
        worktree_path,
        completed,
        has_uncommitted_changes=None,
    ):
        cleanup_calls.append(
            {
                "repo_path": repo_path,
                "worktree_path": worktree_path,
                "completed": completed,
                "has_uncommitted_changes": has_uncommitted_changes,
            }
        )
        return WorktreeCleanupResult(
            worktree_path=worktree_path,
            removed=False,
            preserved=True,
            reason="run_incomplete",
            message=f"Preserved worktree: {worktree_path}. RALPH did not complete.",
        )

    monkeypatch.setattr(
        ralph_module,
        "i_sandbox_start",
        fake_sandbox_start,
    )
    monkeypatch.setattr(
        ralph_module,
        "i_test_runner_run",
        fake_test_runner_run,
    )
    monkeypatch.setattr(
        ralph_module,
        "i_worktree_cleanup",
        fake_worktree_cleanup,
    )

    result = i_ralph_run(
        issues=[
            GitHubIssue(
                number=20,
                title="Add fake test agent provider",
                body="RALPH should report fake agent command failure.",
                labels=("tracer bullet",),
            )
        ],
        repo_path=tmp_path,
    )

    assert result.completed is False
    assert result.status == "failed"
    assert result.orchestrator_result is not None
    assert result.orchestrator_result.error == "fake failure"
    assert "fake failure" in result.message
    assert "Preserved worktree:" in result.message
    assert len(fake_sandbox_handle.commands) == 1
    assert cleanup_calls == [
        {
            "repo_path": tmp_path,
            "worktree_path": worktree_path,
            "completed": False,
            "has_uncommitted_changes": None,
        }
    ]


def test_ralph_returns_failed_when_tests_fail_after_agent_completion(
    monkeypatch,
    tmp_path,
) -> None:
    _patch_clean_repository_context(monkeypatch, tmp_path)
    _patch_successful_worktree_create(monkeypatch, tmp_path)
    _patch_successful_worktree_cleanup(monkeypatch, tmp_path)
    _patch_failing_test_runner(monkeypatch)
    _patch_stubbed_no_change_sync_merge(monkeypatch)

    provider = MockAgentProvider(responses=["Done\n<promise>COMPLETE</promise>"])

    result = i_ralph_run(
        issues=[
            GitHubIssue(
                number=22,
                title="Add RALPH result status contract",
                body="RALPH should report failed when tests fail.",
                labels=("tracer bullet",),
            )
        ],
        agent_provider=provider,
        repo_path=tmp_path,
    )

    assert result.status == "failed"
    assert result.completed is False
    assert "Tests failed" in result.message
    assert "Preserved worktree:" in result.message


def test_ralph_returns_failed_when_sync_or_commit_fails(
    monkeypatch,
    tmp_path,
) -> None:
    _patch_clean_repository_context(monkeypatch, tmp_path)
    _patch_successful_worktree_create(monkeypatch, tmp_path)
    _patch_successful_worktree_cleanup(monkeypatch, tmp_path)
    _patch_passing_test_runner(monkeypatch)
    _patch_failed_sync_merge(monkeypatch)

    provider = MockAgentProvider(responses=["Done\n<promise>COMPLETE</promise>"])

    result = i_ralph_run(
        issues=[
            GitHubIssue(
                number=22,
                title="Add RALPH result status contract",
                body="RALPH should report failed when sync or commit fails.",
                labels=("tracer bullet",),
            )
        ],
        agent_provider=provider,
        repo_path=tmp_path,
    )

    assert result.status == "failed"
    assert result.completed is False
    assert "sync" in result.message.lower() or "commit" in result.message.lower()
    assert "Preserved worktree:" in result.message


def test_ralph_returns_no_changes_when_agent_completes_without_detected_changes(
    monkeypatch,
    tmp_path,
) -> None:
    _patch_clean_repository_context(monkeypatch, tmp_path)
    _patch_successful_worktree_create(monkeypatch, tmp_path)
    _patch_successful_worktree_cleanup(monkeypatch, tmp_path)
    _patch_passing_test_runner(monkeypatch)
    _patch_stubbed_no_change_sync_merge(monkeypatch)

    provider = MockAgentProvider(responses=["Done\n<promise>COMPLETE</promise>"])

    result = i_ralph_run(
        issues=[
            GitHubIssue(
                number=22,
                title="Add RALPH result status contract",
                body="RALPH should report no_changes when no commit or sync is proven.",
                labels=("tracer bullet",),
            )
        ],
        agent_provider=provider,
        repo_path=tmp_path,
    )

    assert result.status == "no_changes"
    assert result.completed is False
    assert "no code changes" in result.message.lower()


def test_ralph_can_complete_no_change_issue_when_no_changes_are_allowed(
    monkeypatch,
    tmp_path,
) -> None:
    _patch_clean_repository_context(monkeypatch, tmp_path)
    _patch_successful_worktree_create(monkeypatch, tmp_path)
    _patch_successful_worktree_cleanup(monkeypatch, tmp_path)
    _patch_passing_test_runner(monkeypatch)
    _patch_stubbed_no_change_sync_merge(monkeypatch)

    provider = MockAgentProvider(responses=["Done\n<promise>COMPLETE</promise>"])

    result = i_ralph_run(
        issues=[
            GitHubIssue(
                number=22,
                title="Add RALPH result status contract",
                body="RALPH should allow explicitly no-change issues.",
                labels=("tracer bullet",),
            )
        ],
        agent_provider=provider,
        repo_path=tmp_path,
        allow_no_changes=True,
    )

    assert result.status == "complete"
    assert result.completed is True
    assert "RALPH completed the selected issue." in result.message


def test_ralph_blocks_when_sandbox_startup_fails(
    monkeypatch,
    tmp_path,
) -> None:
    _patch_clean_repository_context(monkeypatch, tmp_path)
    _patch_successful_worktree_create(monkeypatch, tmp_path)

    worktree_path = tmp_path / "worktree"
    startup_message = f"Local sandbox startup failed: working directory does not exist: {worktree_path}"

    def fake_sandbox_start(working_directory):
        return SandboxStartResult(
            working_directory=working_directory,
            provider_name="local",
            started=False,
            message=startup_message,
            handle=None,
        )

    def fail_repository_context_discover(*args, **kwargs):
        raise AssertionError("i_repository_context_discover() should not be called.")

    def fail_prompt_resolve(*args, **kwargs):
        raise AssertionError("i_prompt_resolve() should not be called.")

    def fail_orchestrator_run(*args, **kwargs):
        raise AssertionError("i_orchestrator_run() should not be called.")

    def fail_test_runner_run(*args, **kwargs):
        raise AssertionError("i_test_runner_run() should not be called.")

    cleanup_calls: list[dict[str, object]] = []

    def fake_worktree_cleanup(  #  Changed Code
        repo_path,
        worktree_path,
        completed,
        has_uncommitted_changes=None,
    ):
        cleanup_calls.append(
            {
                "repo_path": repo_path,
                "worktree_path": worktree_path,
                "completed": completed,
                "has_uncommitted_changes": has_uncommitted_changes,
            }
        )
        return WorktreeCleanupResult(
            worktree_path=worktree_path,
            removed=False,
            preserved=True,
            reason="run_incomplete",
            message=f"Preserved worktree: {worktree_path}. RALPH did not complete.",
        )

    monkeypatch.setattr(
        ralph_module,
        "i_sandbox_start",
        fake_sandbox_start,
    )
    monkeypatch.setattr(
        ralph_module,
        "i_repository_context_discover",
        fail_repository_context_discover,
    )
    monkeypatch.setattr(
        ralph_module,
        "i_prompt_resolve",
        fail_prompt_resolve,
    )
    monkeypatch.setattr(
        ralph_module,
        "i_orchestrator_run",
        fail_orchestrator_run,
    )
    monkeypatch.setattr(
        ralph_module,
        "i_test_runner_run",
        fail_test_runner_run,
    )
    monkeypatch.setattr(
        ralph_module,
        "i_worktree_cleanup",
        fake_worktree_cleanup,  #  Changed Code
    )

    provider = MockAgentProvider(responses=["Done\n<promise>COMPLETE</promise>"])

    result = i_ralph_run(
        issues=[
            GitHubIssue(
                number=15,
                title="Add local sandbox provider",
                body="RALPH should block when local sandbox startup fails.",
                labels=("tracer bullet",),
            )
        ],
        agent_provider=provider,
        repo_path=tmp_path,
    )

    assert result.selected_issue is not None
    assert result.selected_issue.number == 15
    assert result.completed is False
    assert result.status == "blocked"
    assert result.prompt == ""
    assert result.orchestrator_result is None
    assert "Local sandbox startup failed" in result.message
    assert str(worktree_path) in result.message
    assert provider.run_count == 0
    assert cleanup_calls == [
        {
            "repo_path": tmp_path,
            "worktree_path": worktree_path,
            "completed": False,
            "has_uncommitted_changes": None,
        }
    ]
    assert "Preserved worktree" in result.message


def test_ralph_stops_before_worktree_creation_when_repository_is_blocked(
    monkeypatch,
    tmp_path,
) -> None:
    dirty_status_output = " M src/ai_coder/ralph/ralph.py\n?? scratch.md"
    blocked_message = (
        "Blocked: Repository has uncommitted changes. "
        f"Repository root: {tmp_path}. "
        "Active branch: main. "
        "RALPH stopped before worktree creation because the main repository is unsafe. "
        "Commit, stash, or discard the changes, then run RALPH again.\n\n"
        f"Git status output:\n{dirty_status_output}"
    )

    def fake_repository_start(repo_path):
        return RepositoryStartResult(
            repo_path=tmp_path,
            ready=False,
            message=blocked_message,
            active_branch="main",
            is_clean=False,
            status_output=dirty_status_output,
            blocked_reason="repository_dirty",
        )

    def fail_worktree_create(*args, **kwargs):
        raise AssertionError("i_worktree_create() should not be called.")

    def fail_repository_context_discover(*args, **kwargs):
        raise AssertionError("i_repository_context_discover() should not be called.")

    monkeypatch.setattr(
        ralph_module,
        "i_repository_start",
        fake_repository_start,
    )
    monkeypatch.setattr(
        ralph_module,
        "i_worktree_create",
        fail_worktree_create,
    )

    monkeypatch.setattr(
        ralph_module,
        "i_repository_context_discover",
        fail_repository_context_discover,
    )

    provider = MockAgentProvider()

    result = i_ralph_run(
        issues=[
            GitHubIssue(
                number=7,
                title="Add repository clean-state guard",
                body="RALPH should stop when the repository is dirty.",
                labels=("bug",),
            )
        ],
        agent_provider=provider,
        repo_path=tmp_path,
    )

    assert result.selected_issue is None
    assert result.prompt == ""
    assert result.orchestrator_result is None
    assert result.completed is False
    assert result.status == "blocked"
    assert result.message == blocked_message
    assert "Blocked" in result.message
    assert "uncommitted changes" in result.message
    assert "RALPH stopped before worktree creation" in result.message
    assert str(tmp_path) in result.message
    assert "Git status output:" in result.message
    assert "src/ai_coder/ralph/ralph.py" in result.message
    assert "scratch.md" in result.message
    assert "Commit, stash, or discard" in result.message
    assert provider.run_count == 0


def test_ralph_creates_worktree_when_repository_is_clean(
    monkeypatch,
    tmp_path,
) -> None:
    _patch_clean_repository_context(monkeypatch, tmp_path)
    _patch_passing_test_runner(monkeypatch)
    _patch_successful_sync_merge(monkeypatch)

    worktree_calls: list[dict[str, object]] = []
    worktree_path = tmp_path / "worktree"
    worktree_path.mkdir(parents=True, exist_ok=True)

    def fake_worktree_create(
        repo_path,
        issue_number,
        issue_title,
        worktree_root=None,
    ):
        worktree_calls.append(
            {
                "repo_path": repo_path,
                "issue_number": issue_number,
                "issue_title": issue_title,
                "worktree_root": worktree_root,
            }
        )

        return WorktreeCreateResult(
            repo_path=tmp_path,
            worktree_path=worktree_path,
            branch_name="ralph-issue-7-clean-repository-path",
            command=(
                "git",
                "-C",
                str(tmp_path),
                "worktree",
                "add",
                "-b",
                "ralph-issue-7-clean-repository-path",
                str(worktree_path),
            ),
            created=True,
            message="Created Git worktree: test worktree.",
        )

    monkeypatch.setattr(
        ralph_module,
        "i_worktree_create",
        fake_worktree_create,
    )

    provider = MockAgentProvider(responses=["Done\n<promise>COMPLETE</promise>"])

    result = i_ralph_run(
        issues=[
            GitHubIssue(
                number=7,
                title="Clean repository path",
                body="RALPH should continue when the repository is clean.",
                labels=("bug",),
            )
        ],
        agent_provider=provider,
        repo_path=tmp_path,
    )

    assert result.selected_issue is not None
    assert result.selected_issue.number == 7
    assert result.completed is True
    assert result.status == "complete"
    assert result.status != "blocked"
    assert provider.run_count == 1
    assert len(worktree_calls) == 1
    assert worktree_calls[0]["repo_path"] == tmp_path
    assert worktree_calls[0]["issue_number"] == 7
    assert worktree_calls[0]["issue_title"] == "Clean repository path"


def test_ralph_stops_when_worktree_creation_fails_before_sandbox_start(
    monkeypatch,
    tmp_path,
) -> None:
    _patch_clean_repository_context(monkeypatch, tmp_path)

    failure_message = "Failed to create Git worktree: branch already exists."

    def fake_worktree_create(
        repo_path,
        issue_number,
        issue_title,
        worktree_root=None,
    ):
        return WorktreeCreateResult(
            repo_path=tmp_path,
            worktree_path=tmp_path / "worktree",
            branch_name="ralph-issue-13-add-safe-worktree-creation",
            command=(
                "git",
                "-C",
                str(tmp_path),
                "worktree",
                "add",
                "-b",
                "ralph-issue-13-add-safe-worktree-creation",
                str(tmp_path / "worktree"),
            ),
            created=False,
            message=failure_message,
        )

    def fail_sandbox_start(*args, **kwargs):
        raise AssertionError("i_sandbox_start() should not be called.")

    def fail_repository_context_discover(*args, **kwargs):
        raise AssertionError("i_repository_context_discover() should not be called.")

    monkeypatch.setattr(
        ralph_module,
        "i_worktree_create",
        fake_worktree_create,
    )
    monkeypatch.setattr(
        ralph_module,
        "i_sandbox_start",
        fail_sandbox_start,
    )
    monkeypatch.setattr(
        ralph_module,
        "i_repository_context_discover",
        fail_repository_context_discover,
    )

    provider = MockAgentProvider()

    result = i_ralph_run(
        issues=[
            GitHubIssue(
                number=13,
                title="Add safe worktree creation",
                body="RALPH should stop when worktree creation fails.",
                labels=("bug",),
            )
        ],
        agent_provider=provider,
        repo_path=tmp_path,
    )

    assert result.selected_issue is not None
    assert result.selected_issue.number == 13
    assert result.prompt == ""
    assert result.orchestrator_result is None
    assert result.completed is False
    assert result.status == "blocked"
    assert result.message == failure_message
    assert "Failed to create Git worktree" in result.message
    assert provider.run_count == 0


def test_ralph_uses_created_worktree_path_for_sandbox_startup(
    monkeypatch,
    tmp_path,
) -> None:
    _patch_clean_repository_context(monkeypatch, tmp_path)
    _patch_successful_sync_merge(monkeypatch)

    worktree_path = tmp_path / "created-worktree"
    sandbox_start_paths: list[object] = []

    def fake_worktree_create(
        repo_path,
        issue_number,
        issue_title,
        worktree_root=None,
    ):
        return WorktreeCreateResult(
            repo_path=tmp_path,
            worktree_path=worktree_path,
            branch_name="ralph-issue-13-add-safe-worktree-creation",
            command=(
                "git",
                "-C",
                str(tmp_path),
                "worktree",
                "add",
                "-b",
                "ralph-issue-13-add-safe-worktree-creation",
                str(worktree_path),
            ),
            created=True,
            message="Created Git worktree: test worktree.",
        )

    def fake_sandbox_start(working_directory, provider_name=None):
        sandbox_start_paths.append(working_directory)
        return SandboxStartResult(
            working_directory=worktree_path,
            provider_name="local",
            started=True,
            message="Started test local sandbox.",
            handle=LocalSandboxProvider(worktree_path),
        )

    def fake_test_runner_run(
        sandbox_handle=None,
        command=None,
    ):
        return TestRunResult(
            passed=True,
            command=command or ("poetry", "run", "pytest"),
            message="Tests passed through the sandbox seam.",
        )

    def fake_worktree_cleanup(
        repo_path,
        worktree_path,
        completed,
        has_uncommitted_changes=None,
    ):
        return WorktreeCleanupResult(
            worktree_path=worktree_path,
            removed=True,
            preserved=False,
            reason="removed_clean_worktree",
            message=f"Removed clean worktree: {worktree_path}",
        )

    monkeypatch.setattr(
        ralph_module,
        "i_worktree_create",
        fake_worktree_create,
    )
    monkeypatch.setattr(
        ralph_module,
        "i_sandbox_start",
        fake_sandbox_start,
    )
    monkeypatch.setattr(
        ralph_module,
        "i_test_runner_run",
        fake_test_runner_run,
    )
    monkeypatch.setattr(
        ralph_module,
        "i_worktree_cleanup",
        fake_worktree_cleanup,
    )

    provider = MockAgentProvider(responses=["Done\n<promise>COMPLETE</promise>"])

    result = i_ralph_run(
        issues=[
            GitHubIssue(
                number=13,
                title="Add safe worktree creation",
                body="RALPH should start the sandbox in the created worktree.",
                labels=("tracer bullet",),
            )
        ],
        agent_provider=provider,
        repo_path=tmp_path,
    )

    assert sandbox_start_paths == [worktree_path]
    assert sandbox_start_paths[0] != tmp_path
    assert result.selected_issue is not None
    assert result.selected_issue.number == 13
    assert result.completed is True
    assert result.status == "complete"
    assert provider.run_count == 1


def test_ralph_includes_sandbox_aware_prompt_placeholders_after_sandbox_start(
    monkeypatch,
    tmp_path,
) -> None:
    _patch_clean_repository_context(monkeypatch, tmp_path)
    _patch_successful_sync_merge(monkeypatch)

    worktree_path = tmp_path / "issue-18-worktree"
    worktree_path.mkdir(parents=True, exist_ok=True)
    branch_name = "ralph-issue-18-add-sandbox-aware-prompt-preprocessing"
    sandbox_start_paths: list[object] = []
    discovered_repo_paths: list[object] = []

    def fake_worktree_create(
        repo_path,
        issue_number,
        issue_title,
        worktree_root=None,
    ):
        return WorktreeCreateResult(
            repo_path=tmp_path,
            worktree_path=worktree_path,
            branch_name=branch_name,
            command=(
                "git",
                "-C",
                str(tmp_path),
                "worktree",
                "add",
                "-b",
                branch_name,
                str(worktree_path),
            ),
            created=True,
            message="Created Git worktree: test worktree.",
        )

    def fake_sandbox_start(working_directory):
        sandbox_start_paths.append(working_directory)
        return SandboxStartResult(
            working_directory=worktree_path,
            provider_name="local",
            started=True,
            message="Started test local sandbox.",
            handle=LocalSandboxProvider(worktree_path),
        )

    def fake_repository_context_discover(repo_path):
        discovered_repo_paths.append(repo_path)
        return RepositoryContextResult(
            repo_path=tmp_path,
            package_manager="poetry",
            test_command="poetry run pytest",
            test_command_source="configured",
            project_files=("pyproject.toml", "poetry.lock", "src/", "tests/"),
            useful_signals=("Python project", "Uses Poetry", "Uses pytest"),
            prompt_summary=(
                "Repository context:\n"
                "- Package manager: poetry\n"
                "- Test command: poetry run pytest"
            ),
        )

    def fake_test_runner_run(
        sandbox_handle=None,
        command=None,
    ):
        return TestRunResult(
            passed=True,
            command=command or ("poetry", "run", "pytest"),
            message="Tests passed through the sandbox seam.",
        )

    def fake_worktree_cleanup(
        repo_path,
        worktree_path,
        completed,
        has_uncommitted_changes=None,
    ):
        return WorktreeCleanupResult(
            worktree_path=worktree_path,
            removed=True,
            preserved=False,
            reason="removed_clean_worktree",
            message=f"Removed clean worktree: {worktree_path}",
        )

    monkeypatch.setattr(ralph_module, "i_worktree_create", fake_worktree_create)
    monkeypatch.setattr(ralph_module, "i_sandbox_start", fake_sandbox_start)
    monkeypatch.setattr(
        ralph_module,
        "i_repository_context_discover",
        fake_repository_context_discover,
    )
    monkeypatch.setattr(ralph_module, "i_test_runner_run", fake_test_runner_run)
    monkeypatch.setattr(ralph_module, "i_worktree_cleanup", fake_worktree_cleanup)

    prompt_template = (
        "Issue: {{ISSUE_NUMBER}}\n"
        "Title: {{ISSUE_TITLE}}\n"
        "Body: {{ISSUE_BODY}}\n"
        "Labels: {{ISSUE_LABELS}}\n"
        "Branch: {{BRANCH_NAME}}\n"
        "Worktree: {{WORKTREE_PATH}}\n"
        "Done: {{COMPLETE_TOKEN}}"
    )
    provider = MockAgentProvider(responses=["Done\n<promise>COMPLETE</promise>"])

    result = i_ralph_run(
        issues=[
            GitHubIssue(
                number=18,
                title="Add sandbox-aware prompt preprocessing",
                body="Preprocess after sandbox and worktree context exist.",
                labels=("tracer bullet", "Sandcastle"),
            )
        ],
        prompt_template=prompt_template,
        agent_provider=provider,
        repo_path=tmp_path,
    )

    assert result.completed is True
    assert result.status == "complete"
    assert "Issue: 18" in result.prompt
    assert "Title: Add sandbox-aware prompt preprocessing" in result.prompt
    assert "Body: Preprocess after sandbox and worktree context exist." in result.prompt
    assert "Labels: tracer bullet, Sandcastle" in result.prompt
    assert f"Branch: {branch_name}" in result.prompt
    assert f"Worktree: {worktree_path}" in result.prompt
    assert "Done: <promise>COMPLETE</promise>" in result.prompt
    assert provider.prompts == [result.prompt]
    assert sandbox_start_paths == [worktree_path]
    assert discovered_repo_paths == [tmp_path]


def test_ralph_includes_repository_context_when_prompt_requests_it(
    monkeypatch,
    tmp_path,
) -> None:
    _patch_clean_repository_context(monkeypatch, tmp_path)
    _patch_successful_worktree_create(monkeypatch, tmp_path)
    _patch_successful_worktree_cleanup(monkeypatch, tmp_path)
    _patch_passing_test_runner(monkeypatch)
    _patch_successful_sync_merge(monkeypatch)

    discovered_repo_paths: list[object] = []

    def fake_repository_context_discover(repo_path):
        discovered_repo_paths.append(repo_path)
        return RepositoryContextResult(
            repo_path=tmp_path,
            package_manager="poetry",
            test_command="poetry run pytest",
            test_command_source="inferred_from_poetry",
            project_files=("pyproject.toml", "poetry.lock", "tests/"),
            useful_signals=("Uses Poetry", "Uses pytest"),
            prompt_summary=(
                "Repository context:\n"
                "- Package manager: poetry\n"
                "- Test command: poetry run pytest"
            ),
        )

    monkeypatch.setattr(
        ralph_module,
        "i_repository_context_discover",
        fake_repository_context_discover,
    )

    prompt_template = (
        "Repository facts:\n"
        "{{REPOSITORY_CONTEXT}}\n\n"
        "Issue #{{ISSUE_NUMBER}}: {{ISSUE_TITLE}}\n"
        "Body: {{ISSUE_BODY}}\n"
        "Done token: {{COMPLETE_TOKEN}}"
    )
    provider = MockAgentProvider(responses=["Done\n<promise>COMPLETE</promise>"])

    result = i_ralph_run(
        issues=[
            GitHubIssue(
                number=8,
                title="Add repository context discovery",
                body="RALPH should include repository context in the prompt.",
                labels=("tracer bullet",),
            )
        ],
        prompt_template=prompt_template,
        agent_provider=provider,
        repo_path=tmp_path,
    )

    assert result.completed is True
    assert result.status == "complete"
    assert "Repository context:" in result.prompt
    assert "Package manager: poetry" in result.prompt
    assert "Test command: poetry run pytest" in result.prompt
    assert "Issue #8: Add repository context discovery" in result.prompt
    assert "RALPH should include repository context in the prompt." in result.prompt
    assert provider.prompts == [result.prompt]
    assert discovered_repo_paths == [tmp_path]


def test_ralph_default_prompt_includes_repository_context(
    monkeypatch,
    tmp_path,
) -> None:
    _patch_clean_repository_context(monkeypatch, tmp_path)
    _patch_successful_worktree_create(monkeypatch, tmp_path)
    _patch_successful_worktree_cleanup(monkeypatch, tmp_path)
    _patch_passing_test_runner(monkeypatch)
    _patch_successful_sync_merge(monkeypatch)

    discovered_repo_paths: list[object] = []

    def fake_repository_context_discover(repo_path):
        discovered_repo_paths.append(repo_path)
        return RepositoryContextResult(
            repo_path=tmp_path,
            package_manager="poetry",
            test_command="poetry run pytest",
            test_command_source="configured",
            project_files=("pyproject.toml", "poetry.lock", "src/", "tests/"),
            useful_signals=("Python project", "Uses Poetry", "Uses pytest"),
            prompt_summary=(
                "Repository context:\n"
                "- Package manager: poetry\n"
                "- Test command: poetry run pytest\n"
                "- Important files: pyproject.toml, poetry.lock, src/, tests/\n"
                "- Project signals: Python project, Uses Poetry, Uses pytest"
            ),
        )

    monkeypatch.setattr(
        ralph_module,
        "i_repository_context_discover",
        fake_repository_context_discover,
    )

    provider = MockAgentProvider(responses=["Done\n<promise>COMPLETE</promise>"])

    result = i_ralph_run(
        issues=[
            GitHubIssue(
                number=8,
                title="Add repository context discovery",
                body="Default prompts should include repository context.",
                labels=("tracer bullet",),
            )
        ],
        agent_provider=provider,
        repo_path=tmp_path,
        prompt_path=None,
    )

    assert result.completed is True
    assert result.status == "complete"
    assert "Repository context" in result.prompt
    assert "Package manager: poetry" in result.prompt
    assert "Test command: poetry run pytest" in result.prompt
    assert "Default prompts should include repository context." in result.prompt
    assert provider.prompts == [result.prompt]
    assert discovered_repo_paths == [tmp_path]


def test_ralph_selects_issue_builds_prompt_and_completes(
    monkeypatch,
    tmp_path,
) -> None:
    _patch_clean_repository_context(monkeypatch, tmp_path)
    _patch_successful_worktree_create(monkeypatch, tmp_path)
    _patch_successful_worktree_cleanup(monkeypatch, tmp_path)
    _patch_passing_test_runner(monkeypatch)
    _patch_successful_sync_merge(monkeypatch)

    issues = [
        GitHubIssue(
            number=3,
            title="Polish README",
            body="Make the README clearer.",
            labels=("polish",),
        ),
        GitHubIssue(
            number=2,
            title="Minimal local RALPH loop",
            body="Build fake issue to mock agent flow.",
            labels=("tracer bullet",),
        ),
    ]
    provider = MockAgentProvider(responses=["Done\n<promise>COMPLETE</promise>"])

    result = i_ralph_run(issues, agent_provider=provider)

    assert result.selected_issue is not None
    assert result.selected_issue.number == 2
    assert "Issue #2: Minimal local RALPH loop" in result.prompt
    assert "Build fake issue to mock agent flow." in result.prompt
    assert result.completed is True
    assert result.status == "complete"
    assert result.orchestrator_result is not None
    assert result.orchestrator_result.iterations == 1


def test_ralph_returns_incomplete_status_when_orchestrator_does_not_complete(
    monkeypatch,
    tmp_path,
) -> None:
    _patch_clean_repository_context(monkeypatch, tmp_path)
    _patch_successful_worktree_create(monkeypatch, tmp_path)
    _patch_successful_worktree_cleanup(monkeypatch, tmp_path)

    issues = [
        GitHubIssue(
            number=10,
            title="Keep working",
            body="The mock agent should not finish in this test.",
            labels=("tracer bullet",),
        )
    ]
    provider = MockAgentProvider(responses=["Still working"])

    result = i_ralph_run(
        issues,
        agent_provider=provider,
        max_iterations=1,
    )

    assert result.selected_issue is not None
    assert result.selected_issue.number == 10
    assert result.orchestrator_result is not None
    assert result.completed is False
    assert result.status == "incomplete"  #  Changed Code
    assert "RALPH stopped before completion." in result.message
    assert "Preserved worktree:" in result.message
    assert str(tmp_path / "worktree") in result.message


def test_ralph_returns_clear_result_when_no_issue_is_selected(
    monkeypatch,
    tmp_path,
) -> None:
    _patch_clean_repository_context(monkeypatch, tmp_path)

    result = i_ralph_run([GitHubIssue(number=1, title="Closed issue", state="closed")])

    assert result.selected_issue is None
    assert result.prompt == ""
    assert result.orchestrator_result is None
    assert result.completed is False
    assert result.status == "blocked"  #  Changed Code
    assert result.message == "No open actionable issue selected."


def test_ralph_resolves_prompt_file_before_preprocessing(
    monkeypatch,
    tmp_path,
) -> None:
    _patch_clean_repository_context(monkeypatch, tmp_path)
    _patch_successful_worktree_create(monkeypatch, tmp_path)
    _patch_successful_worktree_cleanup(monkeypatch, tmp_path)
    _patch_passing_test_runner(monkeypatch)
    _patch_successful_sync_merge(monkeypatch)

    prompt_file = tmp_path / "ralph_prompt.txt"
    prompt_file.write_text(
        "Issue #{{ISSUE_NUMBER}}: {{ISSUE_TITLE}}\n"
        "Body: {{ISSUE_BODY}}\n"
        "Done token: {{COMPLETE_TOKEN}}",
        encoding="utf-8",
    )
    provider = MockAgentProvider(responses=["Done\n<promise>COMPLETE</promise>"])

    result = i_ralph_run(
        [
            GitHubIssue(
                number=9,
                title="Use prompt resolver",
                body="Load the raw template before preprocessing.",
                labels=("tracer bullet",),
            )
        ],
        prompt_template="",
        prompt_path=prompt_file,
        agent_provider=provider,
        repo_path=tmp_path,
    )

    assert result.completed is True
    assert result.status == "complete"
    assert "Issue #9: Use prompt resolver" in result.prompt
    assert "Body: Load the raw template before preprocessing." in result.prompt
    assert "Done token: <promise>COMPLETE</promise>" in result.prompt
    assert provider.prompts == [result.prompt]


def test_ralph_creates_test_issue_when_no_issues_and_testing_flag(
    monkeypatch,
    tmp_path,
) -> None:

    from ai_coder.ralph import ralph as ralph_module
    from ai_coder.setup_config import c_setup_config

    c_setup_config._instance = None
    monkeypatch.setenv("TESTING_FLAG", "true")
    monkeypatch.delenv("ISSUE_NUMBER", raising=False)
    monkeypatch.delenv("ISSUE_TITLE", raising=False)
    monkeypatch.delenv("ISSUE_BODY", raising=False)
    _refresh_ralph_config()

    ralph_module.setup_config = c_setup_config.get_instance()
    ralph_module.logger = ralph_module.setup_config.get_logger()
    _patch_clean_repository_context(monkeypatch, tmp_path)
    _patch_successful_worktree_create(monkeypatch, tmp_path)
    _patch_successful_worktree_cleanup(monkeypatch, tmp_path)
    _patch_passing_test_runner(monkeypatch)
    _patch_successful_sync_merge(monkeypatch)

    provider = MockAgentProvider(responses=["Done\n<promise>COMPLETE</promise>"])

    result = i_ralph_run(
        issues=None,
        agent_provider=provider,
    )

    assert result.completed is True
    assert result.status == "complete"
    assert result.selected_issue is not None
    assert result.selected_issue.number == 1
    assert result.selected_issue.title == "Minimal local RALPH loop"


def test_ralph_loads_local_issue_file_when_no_issue_is_provided(
    monkeypatch, tmp_path
) -> None:
    from ai_coder.ralph import ralph as ralph_module
    from ai_coder.setup_config import c_setup_config

    issue_file = tmp_path / "github_issue.md"
    issue_file.write_text(
        "# Add local issue fallback\n\n"
        "Labels: tracer bullet\n\n"
        "RALPH should load this issue from a local markdown file.",
        encoding="utf-8",
    )

    c_setup_config._instance = None
    monkeypatch.setenv("TESTING_FLAG", "false")
    monkeypatch.delenv("ISSUE_NUMBER", raising=False)
    monkeypatch.delenv("ISSUE_TITLE", raising=False)
    monkeypatch.delenv("ISSUE_BODY", raising=False)
    monkeypatch.setenv("GITHUB_ISSUE_PATH", str(issue_file))
    _refresh_ralph_config()

    ralph_module.setup_config = c_setup_config.get_instance()
    ralph_module.logger = ralph_module.setup_config.get_logger()
    _patch_clean_repository_context(monkeypatch, tmp_path)
    _patch_successful_worktree_create(monkeypatch, tmp_path)
    _patch_successful_worktree_cleanup(monkeypatch, tmp_path)
    _patch_passing_test_runner(monkeypatch)
    _patch_successful_sync_merge(monkeypatch)

    provider = MockAgentProvider(responses=["Done\n<promise>COMPLETE</promise>"])

    result = i_ralph_run(
        issues=None,
        agent_provider=provider,
    )

    assert result.completed is True
    assert result.status == "complete"
    assert result.selected_issue is not None
    assert result.selected_issue.title == "Add local issue fallback"
    assert "RALPH should load this issue from a local markdown file." in result.prompt


def test_ralph_incomplete_run_preserves_worktree_and_reports_path(
    monkeypatch,
    tmp_path,
) -> None:
    _patch_clean_repository_context(monkeypatch, tmp_path)
    _patch_successful_worktree_create(monkeypatch, tmp_path)

    worktree_path = tmp_path / "worktree"

    cleanup_calls: list[dict[str, object]] = []

    def fake_worktree_cleanup(
        repo_path,
        worktree_path,
        completed,
        has_uncommitted_changes=None,
    ):
        cleanup_calls.append(
            {
                "repo_path": repo_path,
                "worktree_path": worktree_path,
                "completed": completed,
                "has_uncommitted_changes": has_uncommitted_changes,
            }
        )
        return WorktreeCleanupResult(
            worktree_path=worktree_path,
            removed=False,
            preserved=True,
            reason="run_incomplete",
            message=f"Preserved worktree: {worktree_path}. RALPH did not complete.",
        )

    monkeypatch.setattr(
        ralph_module,
        "i_worktree_cleanup",
        fake_worktree_cleanup,
    )

    provider = MockAgentProvider(responses=["Still working"])

    result = i_ralph_run(
        issues=[
            GitHubIssue(
                number=14,
                title="Add worktree preservation and cleanup rules",
                body="RALPH should preserve incomplete worktrees.",
                labels=("tracer bullet",),
            )
        ],
        agent_provider=provider,
        max_iterations=1,
        repo_path=tmp_path,
    )

    assert result.completed is False
    assert result.status == "incomplete"  #  Changed Code
    assert "RALPH stopped before completion." in result.message
    assert "Preserved worktree:" in result.message
    assert str(worktree_path) in result.message
    assert provider.run_count == 1

    assert cleanup_calls == [
        {
            "repo_path": tmp_path,
            "worktree_path": worktree_path,
            "completed": False,
            "has_uncommitted_changes": None,
        }
    ]


def test_ralph_successful_clean_run_reports_worktree_cleanup(
    monkeypatch,
    tmp_path,
) -> None:
    _patch_clean_repository_context(monkeypatch, tmp_path)
    _patch_successful_worktree_create(monkeypatch, tmp_path)
    _patch_passing_test_runner(monkeypatch)
    _patch_successful_sync_merge(monkeypatch)

    worktree_path = tmp_path / "worktree"
    cleanup_calls: list[dict[str, object]] = []

    def fake_worktree_cleanup(
        repo_path,
        worktree_path,
        completed,
        has_uncommitted_changes=None,
    ):
        cleanup_calls.append(
            {
                "repo_path": repo_path,
                "worktree_path": worktree_path,
                "completed": completed,
                "has_uncommitted_changes": has_uncommitted_changes,
            }
        )
        return WorktreeCleanupResult(
            worktree_path=worktree_path,
            removed=True,
            preserved=False,
            reason="removed_clean_worktree",
            message=f"Removed clean worktree: {worktree_path}",
        )

    monkeypatch.setattr(
        ralph_module,
        "i_worktree_cleanup",
        fake_worktree_cleanup,
    )

    provider = MockAgentProvider(responses=["Done\n<promise>COMPLETE</promise>"])

    result = i_ralph_run(
        issues=[
            GitHubIssue(
                number=14,
                title="Add worktree preservation and cleanup rules",
                body="RALPH may remove successful clean worktrees.",
                labels=("tracer bullet",),
            )
        ],
        agent_provider=provider,
        repo_path=tmp_path,
    )

    assert result.completed is True
    assert result.status == "complete"
    assert "RALPH completed the selected issue." in result.message
    assert "Removed clean worktree:" in result.message
    assert str(worktree_path) in result.message
    assert cleanup_calls == [
        {
            "repo_path": tmp_path,
            "worktree_path": worktree_path,
            "completed": True,
            "has_uncommitted_changes": None,
        }
    ]


def test_ralph_dirty_worktree_preservation_is_reported(
    monkeypatch,
    tmp_path,
) -> None:
    _patch_clean_repository_context(monkeypatch, tmp_path)
    _patch_successful_worktree_create(monkeypatch, tmp_path)
    _patch_passing_test_runner(monkeypatch)
    _patch_successful_sync_merge(monkeypatch)

    worktree_path = tmp_path / "worktree"
    cleanup_calls: list[dict[str, object]] = []

    def fake_worktree_cleanup(
        repo_path,
        worktree_path,
        completed,
        has_uncommitted_changes=None,
    ):
        cleanup_calls.append(
            {
                "repo_path": repo_path,
                "worktree_path": worktree_path,
                "completed": completed,
                "has_uncommitted_changes": has_uncommitted_changes,
            }
        )
        return WorktreeCleanupResult(
            worktree_path=worktree_path,
            removed=False,
            preserved=True,
            reason="worktree_dirty",
            message=f"Preserved worktree: {worktree_path}. Git detected uncommitted changes.",
            status_output=" M src/file.py\n?? new_file.py",
        )

    monkeypatch.setattr(
        ralph_module,
        "i_worktree_cleanup",
        fake_worktree_cleanup,
    )

    provider = MockAgentProvider(responses=["Done\n<promise>COMPLETE</promise>"])

    result = i_ralph_run(
        issues=[
            GitHubIssue(
                number=14,
                title="Add worktree preservation and cleanup rules",
                body="RALPH should report dirty worktree preservation.",
                labels=("tracer bullet",),
            )
        ],
        agent_provider=provider,
        repo_path=tmp_path,
    )

    assert result.completed is True
    assert result.status == "complete"
    assert "Preserved worktree:" in result.message
    assert "Git detected uncommitted changes" in result.message
    assert str(worktree_path) in result.message
    assert cleanup_calls == [
        {
            "repo_path": tmp_path,
            "worktree_path": worktree_path,
            "completed": True,
            "has_uncommitted_changes": None,
        }
    ]


# 019 tests
def test_ralph_treats_untrusted_issue_fields_as_inert_prompt_text(
    monkeypatch,
    tmp_path,
) -> None:
    _patch_clean_repository_context(monkeypatch, tmp_path)
    _patch_successful_worktree_create(monkeypatch, tmp_path)
    _patch_successful_worktree_cleanup(monkeypatch, tmp_path)
    _patch_successful_sync_merge(monkeypatch)

    sentinel_file = tmp_path / "ralph_prompt_should_not_create_this.txt"

    issue_title = (
        'Fix literal !`echo title` $(Write-Output "title") ' "&& echo title | whoami"
    )
    issue_body = (
        f"Keep this literal: !`echo created > {sentinel_file}` "
        r"and Windows text C:\Temp\RALPH & Test | whoami %USERNAME% ^."
    )
    issue_labels = (
        "tracer bullet",
        "label:needs-review",
        r"windows path C:\Temp\A&B",
        "pipe | label",
        'quote "label"',
        "percent %PATH%",
        "caret ^",
    )
    formatted_labels = ", ".join(issue_labels)

    prompt_template = (
        "Number: {{ISSUE_NUMBER}}\n"
        "Title: {{ISSUE_TITLE}}\n"
        "Body: {{ISSUE_BODY}}\n"
        "Labels: {{ISSUE_LABELS}}\n"
        "Branch: {{BRANCH_NAME}}\n"
        "Worktree: {{WORKTREE_PATH}}\n"
        "Done token: {{COMPLETE_TOKEN}}"
    )

    def fake_test_runner_run(
        sandbox_handle=None,
        command=None,
    ):
        return TestRunResult(
            passed=True,
            command=command or ("poetry", "run", "pytest"),
            message="Tests passed through the sandbox seam.",
        )

    monkeypatch.setattr(
        ralph_module,
        "i_test_runner_run",
        fake_test_runner_run,
    )

    provider = MockAgentProvider(responses=["Done\n<promise>COMPLETE</promise>"])

    result = i_ralph_run(
        issues=[
            GitHubIssue(
                number=19,
                title=issue_title,
                body=issue_body,
                labels=issue_labels,
            )
        ],
        prompt_template=prompt_template,
        agent_provider=provider,
        repo_path=tmp_path,
    )

    assert result.completed is True
    assert result.status == "complete"
    assert result.prompt
    assert issue_title in result.prompt
    assert issue_body in result.prompt
    assert f"Labels: {formatted_labels}" in result.prompt
    assert "Branch: ralph-issue-19-test-worktree" in result.prompt
    assert f"Worktree: {tmp_path / 'worktree'}" in result.prompt
    assert "Done token: <promise>COMPLETE</promise>" in result.prompt
    assert provider.prompts == [result.prompt]
    assert sentinel_file.exists() is False
