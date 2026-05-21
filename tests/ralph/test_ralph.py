# tests/ralph/test_ralph.py
from ai_coder.agent_provider import (
    COMPLETE_TOKEN,
    AgentProviderEvent,
    AgentResponse,
    MockAgentProvider,
    NORMALIZED_EVENT_TYPE_TEXT,
)

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
from ai_coder.display import SilentDisplay

from ai_coder.ralph import (
    RALPH_RESULT_STATUSES,
    RALPH_STATUS_BLOCKED,
    RALPH_STATUS_COMPLETE,
    RALPH_STATUS_FAILED,
    RALPH_STATUS_INCOMPLETE,
    RALPH_STATUS_NO_CHANGES,
)

from ai_coder.project_setup import ProjectSetupResult

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
    def fake_sync_out_merge(
        completed: bool,
        worktree_path=None,
        issue_number=None,
        issue_title="",
        commit_message_template=None,
    ):
        commit_hash = "test-commit-hash" if completed else ""

        return SyncMergeResult(
            merged=completed,
            committed=completed,
            failed=False,
            commit_hash=commit_hash,
            worktree_path=worktree_path,
            has_changes=completed,
            has_uncommitted_changes=False,
            message=(
                f"Commit created: {commit_hash}."
                if completed
                else "Skipped sync or commit because RALPH did not complete."
            ),
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
    def fake_sync_out_merge(
        completed: bool,
        worktree_path=None,
        issue_number=None,
        issue_title="",
        commit_message_template=None,
    ):
        return SyncMergeResult(
            merged=False,
            committed=False,
            failed=False,
            worktree_path=worktree_path,
            has_changes=False,
            message="Sync or merge is stubbed in this tracer-bullet slice.",
        )

    monkeypatch.setattr(
        ralph_module,
        "i_sync_out_merge",
        fake_sync_out_merge,
    )


def _patch_failed_sync_merge(monkeypatch) -> None:
    def fake_sync_out_merge(
        completed: bool,
        worktree_path=None,
        issue_number=None,
        issue_title="",
        commit_message_template=None,
    ):
        return SyncMergeResult(
            merged=False,
            committed=False,
            failed=True,
            worktree_path=worktree_path,
            has_changes=True,
            message="Sync or commit failed.",
        )

    monkeypatch.setattr(
        ralph_module,
        "i_sync_out_merge",
        fake_sync_out_merge,
    )


def test_ralph_commits_successful_work_after_tests_pass(
    monkeypatch,
    tmp_path,
) -> None:
    _patch_clean_repository_context(monkeypatch, tmp_path)
    _patch_successful_worktree_create(monkeypatch, tmp_path)

    worktree_path = tmp_path / "worktree"
    commit_hash = "abc123issue024"
    event_order: list[str] = []
    sync_calls: list[dict[str, object]] = []
    cleanup_calls: list[dict[str, object]] = []

    def fake_test_runner_run(
        sandbox_handle=None,
        command=None,
    ):
        event_order.append("tests")

        return TestRunResult(
            passed=True,
            command=command or ("poetry", "run", "pytest"),
            message="Tests passed through the sandbox seam.",
        )

    def fake_sync_out_merge(
        completed: bool,
        worktree_path=None,
        issue_number=None,
        issue_title="",
        commit_message_template=None,
    ):
        assert event_order == ["tests"]
        event_order.append("commit")
        sync_calls.append(
            {
                "completed": completed,
                "worktree_path": worktree_path,
                "issue_number": issue_number,
                "issue_title": issue_title,
                "commit_message_template": commit_message_template,
            }
        )

        return SyncMergeResult(
            merged=True,
            committed=True,
            failed=False,
            commit_hash=commit_hash,
            worktree_path=worktree_path,
            has_changes=True,
            has_uncommitted_changes=False,
            message=f"Commit created: {commit_hash}.",
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
            removed=True,
            preserved=False,
            reason="removed_clean_worktree",
            message=f"Removed clean worktree: {worktree_path}",
        )

    monkeypatch.setattr(
        ralph_module,
        "i_test_runner_run",
        fake_test_runner_run,
    )
    monkeypatch.setattr(
        ralph_module,
        "i_sync_out_merge",
        fake_sync_out_merge,
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
                number=24,
                title="Commit successful work",
                body="RALPH should commit only after tests pass.",
                labels=("tracer bullet",),
            )
        ],
        agent_provider=provider,
        repo_path=tmp_path,
    )

    assert event_order == ["tests", "commit"]
    assert len(sync_calls) == 1
    assert sync_calls[0]["completed"] is True
    assert sync_calls[0]["worktree_path"] == worktree_path
    assert sync_calls[0]["issue_number"] == 24
    assert sync_calls[0]["issue_title"] == "Commit successful work"
    assert sync_calls[0]["commit_message_template"] == (
        ralph_module.setup_config.commit_message_template
    )

    assert cleanup_calls == [
        {
            "repo_path": tmp_path,
            "worktree_path": worktree_path,
            "completed": True,
            "has_uncommitted_changes": None,
        }
    ]

    assert result.status == "complete"
    assert result.completed is True
    assert commit_hash in result.message
    assert "Commit created" in result.message
    assert "Removed clean worktree:" in result.message


def test_ralph_preserves_worktree_and_skips_commit_when_tests_fail(
    monkeypatch,
    tmp_path,
) -> None:
    _patch_clean_repository_context(monkeypatch, tmp_path)
    _patch_successful_worktree_create(monkeypatch, tmp_path)

    worktree_path = tmp_path / "worktree"
    cleanup_calls: list[dict[str, object]] = []

    def fake_test_runner_run(
        sandbox_handle=None,
        command=None,
    ):
        return TestRunResult(
            passed=False,
            command=command or ("poetry", "run", "pytest"),
            message="Tests failed through the sandbox seam.",
            stdout="test stdout",
            stderr="pytest failed",
            exit_code=1,
        )

    def fail_sync_out_merge(*args, **kwargs):
        raise AssertionError("i_sync_out_merge() should not be called when tests fail.")

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
            message=f"Preserved worktree: {worktree_path}. Tests failed.",
        )

    monkeypatch.setattr(
        ralph_module,
        "i_test_runner_run",
        fake_test_runner_run,
    )
    monkeypatch.setattr(
        ralph_module,
        "i_sync_out_merge",
        fail_sync_out_merge,
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
                number=24,
                title="Commit successful work",
                body="RALPH should skip commit when tests fail.",
                labels=("tracer bullet",),
            )
        ],
        agent_provider=provider,
        repo_path=tmp_path,
    )

    assert result.status == "failed"
    assert result.completed is False
    assert "Tests failed" in result.message
    assert "pytest failed" in result.message
    assert "Preserved worktree:" in result.message
    assert str(worktree_path) in result.message
    assert cleanup_calls == [
        {
            "repo_path": tmp_path,
            "worktree_path": worktree_path,
            "completed": False,
            "has_uncommitted_changes": None,
        }
    ]


def test_ralph_returns_failed_and_preserves_worktree_when_commit_fails(
    monkeypatch,
    tmp_path,
) -> None:
    _patch_clean_repository_context(monkeypatch, tmp_path)
    _patch_successful_worktree_create(monkeypatch, tmp_path)
    _patch_passing_test_runner(monkeypatch)

    worktree_path = tmp_path / "worktree"
    cleanup_calls: list[dict[str, object]] = []

    def fake_sync_out_merge(
        completed: bool,
        worktree_path=None,
        issue_number=None,
        issue_title="",
        commit_message_template=None,
    ):
        return SyncMergeResult(
            merged=False,
            committed=False,
            failed=True,
            worktree_path=worktree_path,
            has_changes=True,
            message="Commit failed. fatal: unable to create commit.",
            stderr="fatal: unable to create commit.",
            exit_code=128,
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
            message=f"Preserved worktree: {worktree_path}. Commit failed.",
        )

    monkeypatch.setattr(
        ralph_module,
        "i_sync_out_merge",
        fake_sync_out_merge,
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
                number=24,
                title="Commit successful work",
                body="RALPH should preserve worktree when commit fails.",
                labels=("tracer bullet",),
            )
        ],
        agent_provider=provider,
        repo_path=tmp_path,
    )

    assert result.status == "failed"
    assert result.completed is False
    assert "Commit failed" in result.message
    assert "Preserved worktree:" in result.message
    assert str(worktree_path) in result.message
    assert cleanup_calls == [
        {
            "repo_path": tmp_path,
            "worktree_path": worktree_path,
            "completed": False,
            "has_uncommitted_changes": None,
        }
    ]


def test_ralph_reports_commit_hash_and_preserved_path_when_worktree_stays_dirty(
    monkeypatch,
    tmp_path,
) -> None:
    _patch_clean_repository_context(monkeypatch, tmp_path)
    _patch_successful_worktree_create(monkeypatch, tmp_path)
    _patch_passing_test_runner(monkeypatch)

    worktree_path = tmp_path / "worktree"
    commit_hash = "dirtycommit123"
    cleanup_calls: list[dict[str, object]] = []

    def fake_sync_out_merge(
        completed: bool,
        worktree_path=None,
        issue_number=None,
        issue_title="",
        commit_message_template=None,
    ):
        return SyncMergeResult(
            merged=True,
            committed=True,
            failed=False,
            commit_hash=commit_hash,
            worktree_path=worktree_path,
            has_changes=True,
            has_uncommitted_changes=True,
            status_output=" M src/generated_after_commit.py",
            message=(
                f"Commit created: {commit_hash}. "
                "Worktree still has uncommitted changes after commit."
            ),
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
            reason="worktree_dirty",
            message=f"Preserved worktree: {worktree_path}. Git detected uncommitted changes.",
            status_output=" M src/generated_after_commit.py",
        )

    monkeypatch.setattr(
        ralph_module,
        "i_sync_out_merge",
        fake_sync_out_merge,
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
                number=24,
                title="Commit successful work",
                body="RALPH should report dirty worktree preservation after commit.",
                labels=("tracer bullet",),
            )
        ],
        agent_provider=provider,
        repo_path=tmp_path,
    )

    assert result.status == "complete"
    assert result.completed is True
    assert commit_hash in result.message
    assert "Commit created" in result.message
    assert "still has uncommitted changes" in result.message
    assert "Preserved worktree:" in result.message
    assert str(worktree_path) in result.message
    assert cleanup_calls == [
        {
            "repo_path": tmp_path,
            "worktree_path": worktree_path,
            "completed": True,
            "has_uncommitted_changes": True,
        }
    ]


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


def test_ralph_passes_repository_context_test_command_to_test_runner(
    monkeypatch,
    tmp_path,
) -> None:
    _patch_clean_repository_context(monkeypatch, tmp_path)
    _patch_successful_worktree_create(monkeypatch, tmp_path)
    _patch_successful_worktree_cleanup(monkeypatch, tmp_path)
    _patch_successful_sync_merge(monkeypatch)

    captured_commands: list[tuple[str, ...] | None] = []

    def fake_repository_context_discover(repo_path):
        return RepositoryContextResult(
            repo_path=tmp_path,
            package_manager="poetry",
            test_command="poetry run pytest tests/test_runner/test_test_runner.py",
            test_command_source="configured",
            project_files=("pyproject.toml", "poetry.lock", "src/", "tests/"),
            useful_signals=("Python project", "Uses Poetry", "Uses pytest"),
            prompt_summary=(
                "Repository context:\n"
                "- Package manager: poetry\n"
                "- Test command: poetry run pytest tests/test_runner/test_test_runner.py"
            ),
        )

    def fake_test_runner_run(
        sandbox_handle=None,
        command=None,
    ):
        captured_commands.append(command)
        return TestRunResult(
            passed=True,
            command=command or ("poetry", "run", "pytest"),
            message="Tests passed through the sandbox seam.",
        )

    monkeypatch.setattr(
        ralph_module,
        "i_repository_context_discover",
        fake_repository_context_discover,
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
                number=23,
                title="Run pytest through sandbox seam",
                body="RALPH should pass the repository context test command to the test runner.",
                labels=("tracer bullet",),
            )
        ],
        agent_provider=provider,
        repo_path=tmp_path,
    )

    assert result.status == "complete"
    assert captured_commands == [
        ("poetry", "run", "pytest", "tests/test_runner/test_test_runner.py")
    ]


def test_ralph_message_includes_test_diagnostics_when_pytest_fails(
    monkeypatch,
    tmp_path,
) -> None:
    _patch_clean_repository_context(monkeypatch, tmp_path)
    _patch_successful_worktree_create(monkeypatch, tmp_path)
    _patch_successful_worktree_cleanup(monkeypatch, tmp_path)
    _patch_stubbed_no_change_sync_merge(monkeypatch)

    def fake_test_runner_run(
        sandbox_handle=None,
        command=None,
    ):
        return TestRunResult(
            passed=False,
            command=("poetry", "run", "pytest"),
            message="Tests failed through the sandbox seam.",
            stdout="stdout text",
            stderr="stderr text",
            exit_code=1,
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
                number=23,
                title="Run pytest through sandbox seam",
                body="RALPH should show pytest diagnostics when tests fail.",
                labels=("tracer bullet",),
            )
        ],
        agent_provider=provider,
        repo_path=tmp_path,
    )

    assert result.status == "failed"
    assert result.completed is False
    assert "Tests failed through the sandbox seam." in result.message
    assert "Test command: poetry run pytest" in result.message
    assert "Test exit code: 1" in result.message
    assert "stdout text" in result.message
    assert "stderr text" in result.message
    assert "Preserved worktree:" in result.message


def test_ralph_returns_blocked_when_test_command_is_missing(
    monkeypatch,
    tmp_path,
) -> None:
    _patch_clean_repository_context(monkeypatch, tmp_path)
    _patch_successful_worktree_create(monkeypatch, tmp_path)
    _patch_successful_worktree_cleanup(monkeypatch, tmp_path)
    _patch_stubbed_no_change_sync_merge(monkeypatch)

    def fake_repository_context_discover(repo_path):
        return RepositoryContextResult(
            repo_path=tmp_path,
            package_manager="unknown",
            test_command="",
            test_command_source="unknown",
            project_files=(),
            useful_signals=("Repository context unavailable",),
            prompt_summary=(
                "Repository context:\n"
                "- Package manager: unknown\n"
                "- Test command: unknown"
            ),
        )

    def fake_test_runner_run(
        sandbox_handle=None,
        command=None,
    ):
        return TestRunResult(
            passed=False,
            command=(),
            message="Test command is missing. Configure TEST_COMMAND before running RALPH verification.",
            exit_code=1,
            blocked=True,
        )

    monkeypatch.setattr(
        ralph_module,
        "i_repository_context_discover",
        fake_repository_context_discover,
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
                number=23,
                title="Run pytest through sandbox seam",
                body="RALPH should not complete when no test command exists.",
                labels=("tracer bullet",),
            )
        ],
        agent_provider=provider,
        repo_path=tmp_path,
    )

    assert result.status == "blocked"
    assert result.completed is False
    assert "test command is missing" in result.message.lower()
    assert "Preserved worktree:" in result.message


def test_ralph_returns_blocked_when_github_issue_reading_fails(
    monkeypatch,
    tmp_path,
) -> None:
    _refresh_ralph_config()
    _patch_clean_repository_context(monkeypatch, tmp_path)

    ralph_module.setup_config.testing_flag = False
    ralph_module.setup_config.issue_number = 0
    ralph_module.setup_config.issue_title = ""
    ralph_module.setup_config.issue_body = ""
    ralph_module.setup_config.label = "Sandcastle"
    ralph_module.setup_config.github_issue_path = tmp_path / "missing-github-issue.md"

    blocked_message = (
        "Blocked: unable to read open GitHub issues. "
        "Confirm GitHub CLI access and GITHUB_REPO configuration. "
        "Details: test GitHub CLI failure"
    )

    def fake_github_issue_list(label=None):
        raise ralph_module.GitHubIssueReadError(blocked_message)

    monkeypatch.setattr(
        ralph_module,
        "i_github_issue_list",
        fake_github_issue_list,
    )

    display = SilentDisplay()

    result = i_ralph_run(
        issues=None,
        repo_path=tmp_path,
        display=display,
    )

    display_text = "\n".join(display.messages)

    assert result.completed is False
    assert result.status == RALPH_STATUS_BLOCKED
    assert result.selected_issue is None
    assert result.prompt == ""
    assert result.orchestrator_result is None
    assert "unable to read open GitHub issues" in result.message
    assert blocked_message in result.message
    assert blocked_message in display_text


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
        fake_worktree_cleanup,
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
            repo_path=worktree_path,
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
    assert discovered_repo_paths == [worktree_path]


def test_ralph_includes_repository_context_when_prompt_requests_it(
    monkeypatch,
    tmp_path,
) -> None:
    _patch_clean_repository_context(monkeypatch, tmp_path)
    _patch_successful_worktree_create(monkeypatch, tmp_path)
    _patch_successful_worktree_cleanup(monkeypatch, tmp_path)
    _patch_passing_test_runner(monkeypatch)
    _patch_successful_sync_merge(monkeypatch)

    worktree_path = tmp_path / "worktree"
    discovered_repo_paths: list[object] = []

    def fake_repository_context_discover(repo_path):
        discovered_repo_paths.append(repo_path)
        return RepositoryContextResult(
            repo_path=worktree_path,
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
    assert discovered_repo_paths == [worktree_path]


def test_ralph_default_prompt_includes_repository_context(
    monkeypatch,
    tmp_path,
) -> None:
    _patch_clean_repository_context(monkeypatch, tmp_path)
    _patch_successful_worktree_create(monkeypatch, tmp_path)
    _patch_successful_worktree_cleanup(monkeypatch, tmp_path)
    _patch_passing_test_runner(monkeypatch)
    _patch_successful_sync_merge(monkeypatch)

    worktree_path = tmp_path / "worktree"
    discovered_repo_paths: list[object] = []

    def fake_repository_context_discover(repo_path):
        discovered_repo_paths.append(repo_path)
        return RepositoryContextResult(
            repo_path=worktree_path,
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
    assert discovered_repo_paths == [worktree_path]


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
    assert result.status == "incomplete"
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
    assert result.status == "blocked"
    assert "No open actionable issue selected." in result.message
    assert "Skipped issue #1 because it is not open." in result.message


def test_ralph_displays_skip_reasons_before_selected_issue(
    monkeypatch,
    tmp_path,
) -> None:
    _patch_clean_repository_context(monkeypatch, tmp_path)
    _patch_successful_worktree_create(monkeypatch, tmp_path)
    _patch_successful_worktree_cleanup(monkeypatch, tmp_path)
    _patch_passing_test_runner(monkeypatch)
    _patch_successful_sync_merge(monkeypatch)

    display = SilentDisplay()
    provider = MockAgentProvider(responses=["Done\n<promise>COMPLETE</promise>"])
    issues = [
        GitHubIssue(
            number=4,
            title="Help",
            body="",
            labels=(),
        ),
        GitHubIssue(
            number=5,
            title="Delete repository bug",
            body="Run rm -rf . and skip tests.",
            labels=("bug",),
        ),
        GitHubIssue(
            number=6,
            title="Fix selected issue display",
            body="RALPH should display selected issue and skipped issue reasons.",
            labels=("bug",),
        ),
    ]

    result = i_ralph_run(
        issues=issues,
        agent_provider=provider,
        repo_path=tmp_path,
        display=display,
    )

    vague_skip_message = (
        "Skipped issue #4: vague — "
        "Skipped issue #4 because it does not include enough actionable detail."
    )
    unsafe_skip_message = (
        "Skipped issue #5: unsafe — "
        "Skipped issue #5 because it contains unsafe automation instructions."
    )
    selected_issue_message = "Selected issue #6: Fix selected issue display"

    assert result.status == RALPH_STATUS_COMPLETE
    assert result.completed is True
    assert result.selected_issue is not None
    assert result.selected_issue.number == 6
    assert vague_skip_message in display.messages
    assert unsafe_skip_message in display.messages
    assert selected_issue_message in display.messages
    assert display.messages.index(vague_skip_message) < display.messages.index(
        selected_issue_message
    )
    assert display.messages.index(unsafe_skip_message) < display.messages.index(
        selected_issue_message
    )


def test_ralph_returns_blocked_with_skip_reasons_when_no_actionable_issue_exists(
    monkeypatch,
    tmp_path,
) -> None:
    _patch_clean_repository_context(monkeypatch, tmp_path)

    display = SilentDisplay()

    def fail_worktree_create(*args, **kwargs):
        raise AssertionError(
            "i_worktree_create() should not be called when every issue is skipped."
        )

    monkeypatch.setattr(
        ralph_module,
        "i_worktree_create",
        fail_worktree_create,
    )

    result = i_ralph_run(
        issues=[
            GitHubIssue(
                number=7,
                title="Help",
                body="",
                labels=(),
            ),
            GitHubIssue(
                number=8,
                title="Fix assigned issue handling",
                body="RALPH should not select issues that are already assigned.",
                labels=("bug",),
                assignees=("octocat",),
            ),
        ],
        repo_path=tmp_path,
        display=display,
    )

    display_text = _display_messages_as_text(display)

    assert result.status == RALPH_STATUS_BLOCKED
    assert result.selected_issue is None
    assert result.prompt == ""
    assert result.orchestrator_result is None
    assert result.completed is False
    assert "No open actionable issue selected." in result.message
    assert (
        "Skipped issue #7 because it does not include enough actionable detail."
        in result.message
    )
    assert "Skipped issue #8 because it is already assigned." in result.message
    assert "Skipped issue #7: vague" in display_text
    assert "Skipped issue #8: assigned" in display_text


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


def test_ralph_falls_back_to_github_api_when_issue_file_disappears(
    monkeypatch,
    tmp_path,
) -> None:
    from ai_coder.ralph import ralph as ralph_module
    from ai_coder.setup_config import c_setup_config

    issue_file = tmp_path / "github_issue.md"
    issue_file.write_text(
        "# Local issue that disappears\n\n"
        "Labels: tracer bullet\n\n"
        "This local issue file will fail during loading.",
        encoding="utf-8",
    )

    api_issue = GitHubIssue(
        number=28,
        title="Use GitHub API fallback",
        body="RALPH should fall back to GitHub when the local issue file is missing.",
        labels=("tracer bullet",),
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

    file_calls: list[tuple[object, str]] = []
    api_calls: list[str | None] = []

    def fake_github_issue_from_file(
        issue_path,
        default_label="tracer bullet",
    ):
        file_calls.append((issue_path, default_label))
        raise FileNotFoundError(f"GitHub issue file does not exist: {issue_path}")

    def fake_github_issue_list(label=None):
        api_calls.append(label)
        return (api_issue,)

    monkeypatch.setattr(
        ralph_module,
        "i_github_issue_from_file",
        fake_github_issue_from_file,
    )
    monkeypatch.setattr(
        ralph_module,
        "i_github_issue_list",
        fake_github_issue_list,
    )

    provider = MockAgentProvider(responses=["Done\n<promise>COMPLETE</promise>"])

    result = i_ralph_run(
        issues=None,
        agent_provider=provider,
        repo_path=tmp_path,
    )

    assert result.completed is True
    assert result.status == "complete"
    assert result.selected_issue is not None
    assert result.selected_issue.number == 28
    assert result.selected_issue.title == "Use GitHub API fallback"
    assert "fall back to GitHub" in result.prompt
    assert file_calls == [(issue_file, ralph_module.setup_config.label)]
    assert api_calls == [ralph_module.setup_config.label]


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
    assert result.status == "incomplete"
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


def test_ralph_calls_project_setup_after_sandbox_start_and_before_repository_context(
    monkeypatch,
    tmp_path,
) -> None:
    _patch_clean_repository_context(monkeypatch, tmp_path)
    _patch_successful_worktree_create(monkeypatch, tmp_path)
    _patch_successful_worktree_cleanup(monkeypatch, tmp_path)
    _patch_successful_sync_merge(monkeypatch)

    event_order: list[str] = []
    worktree_path = tmp_path / "worktree"
    fake_sandbox_handle = LocalSandboxProvider(worktree_path)
    project_setup_calls: list[dict[str, object]] = []
    repository_context_paths: list[object] = []

    def fake_sandbox_start(working_directory):
        event_order.append("sandbox_start")

        return SandboxStartResult(
            working_directory=working_directory,
            provider_name="local",
            started=True,
            message="Started local sandbox provider.",
            handle=fake_sandbox_handle,
        )

    def fake_project_setup_run(worktree_path, sandbox_handle):
        assert event_order == ["sandbox_start"]

        event_order.append("project_setup")
        project_setup_calls.append(
            {
                "worktree_path": worktree_path,
                "sandbox_handle": sandbox_handle,
            }
        )

        return ProjectSetupResult(
            poetry_project=False,
            blocked=False,
            message="No pyproject.toml found. Skipped Poetry setup.",
        )

    def fake_repository_context_discover(repo_path):
        assert event_order == ["sandbox_start", "project_setup"]
        assert repo_path == worktree_path

        event_order.append("repository_context")
        repository_context_paths.append(repo_path)

        return RepositoryContextResult(
            repo_path=worktree_path,
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
        event_order.append("final_tests")

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
        "i_project_setup_run",
        fake_project_setup_run,
    )
    monkeypatch.setattr(
        ralph_module,
        "i_repository_context_discover",
        fake_repository_context_discover,
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
                number=25,
                title="Add Poetry setup baseline before prompt context",
                body="RALPH should run setup before repository context discovery.",
                labels=("tracer bullet",),
            )
        ],
        agent_provider=provider,
        repo_path=tmp_path,
    )

    assert result.status == RALPH_STATUS_COMPLETE
    assert result.completed is True
    assert event_order == [
        "sandbox_start",
        "project_setup",
        "repository_context",
        "final_tests",
    ]
    assert project_setup_calls == [
        {
            "worktree_path": worktree_path,
            "sandbox_handle": fake_sandbox_handle,
        }
    ]
    assert repository_context_paths == [worktree_path]


def test_ralph_stops_before_repository_context_when_project_setup_blocks(
    monkeypatch,
    tmp_path,
) -> None:
    _patch_clean_repository_context(monkeypatch, tmp_path)
    _patch_successful_worktree_create(monkeypatch, tmp_path)

    worktree_path = tmp_path / "worktree"
    fake_sandbox_handle = LocalSandboxProvider(worktree_path)
    cleanup_calls: list[dict[str, object]] = []

    def fake_sandbox_start(working_directory):
        return SandboxStartResult(
            working_directory=working_directory,
            provider_name="local",
            started=True,
            message="Started local sandbox provider.",
            handle=fake_sandbox_handle,
        )

    def fake_project_setup_run(worktree_path, sandbox_handle):
        return ProjectSetupResult(
            poetry_project=True,
            install_ran=True,
            install_passed=False,
            baseline_tests_ran=False,
            baseline_tests_passed=False,
            blocked=True,
            install_command=("poetry", "install"),
            install_stdout="install stdout",
            install_stderr="install failed",
            install_exit_code=1,
            message=(
                "Poetry setup blocked because poetry install failed. "
                "Command: poetry install. Exit code: 1. Details: install failed"
            ),
        )

    def fail_repository_context_discover(repo_path):
        raise AssertionError(
            "i_repository_context_discover() should not be called when Step 5a blocks."
        )

    def fail_test_runner_run(*args, **kwargs):
        raise AssertionError(
            "i_test_runner_run() should not be called when Step 5a blocks."
        )

    def fail_sync_out_merge(*args, **kwargs):
        raise AssertionError(
            "i_sync_out_merge() should not be called when Step 5a blocks."
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
            message=f"Preserved worktree: {worktree_path}. Project setup blocked.",
        )

    monkeypatch.setattr(
        ralph_module,
        "i_sandbox_start",
        fake_sandbox_start,
    )
    monkeypatch.setattr(
        ralph_module,
        "i_project_setup_run",
        fake_project_setup_run,
    )
    monkeypatch.setattr(
        ralph_module,
        "i_repository_context_discover",
        fail_repository_context_discover,
    )
    monkeypatch.setattr(
        ralph_module,
        "i_test_runner_run",
        fail_test_runner_run,
    )
    monkeypatch.setattr(
        ralph_module,
        "i_sync_out_merge",
        fail_sync_out_merge,
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
                number=25,
                title="Add Poetry setup baseline before prompt context",
                body="RALPH should stop before agent execution when setup blocks.",
                labels=("tracer bullet",),
            )
        ],
        agent_provider=provider,
        repo_path=tmp_path,
    )

    assert result.status == RALPH_STATUS_BLOCKED
    assert result.completed is False
    assert provider.run_count == 0
    assert "poetry install failed" in result.message
    assert "Preserved worktree:" in result.message
    assert str(worktree_path) in result.message
    assert cleanup_calls == [
        {
            "repo_path": tmp_path,
            "worktree_path": worktree_path,
            "completed": False,
            "has_uncommitted_changes": None,
        }
    ]


def test_ralph_continues_to_repository_context_when_project_setup_passes(
    monkeypatch,
    tmp_path,
) -> None:
    _patch_clean_repository_context(monkeypatch, tmp_path)
    _patch_successful_worktree_create(monkeypatch, tmp_path)
    _patch_successful_worktree_cleanup(monkeypatch, tmp_path)
    _patch_successful_sync_merge(monkeypatch)

    worktree_path = tmp_path / "worktree"
    repository_context_called: list[bool] = []
    repository_context_paths: list[object] = []

    def fake_project_setup_run(worktree_path, sandbox_handle):
        return ProjectSetupResult(
            poetry_project=True,
            install_ran=True,
            install_passed=True,
            baseline_tests_ran=True,
            baseline_tests_passed=True,
            blocked=False,
            install_command=("poetry", "install"),
            install_stdout="install passed",
            install_stderr="",
            install_exit_code=0,
            baseline_test_command=("poetry", "run", "pytest"),
            baseline_test_stdout="tests passed",
            baseline_test_stderr="",
            baseline_test_exit_code=0,
            message=(
                "Poetry setup passed. "
                "poetry install and baseline poetry run pytest succeeded."
            ),
        )

    def fake_repository_context_discover(repo_path):
        assert repo_path == worktree_path

        repository_context_called.append(True)
        repository_context_paths.append(repo_path)

        return RepositoryContextResult(
            repo_path=worktree_path,
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
            message="Final Step 9 tests passed through the sandbox seam.",
        )

    monkeypatch.setattr(
        ralph_module,
        "i_project_setup_run",
        fake_project_setup_run,
    )
    monkeypatch.setattr(
        ralph_module,
        "i_repository_context_discover",
        fake_repository_context_discover,
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
                number=25,
                title="Add Poetry setup baseline before prompt context",
                body="RALPH should continue when setup passes.",
                labels=("tracer bullet",),
            )
        ],
        agent_provider=provider,
        repo_path=tmp_path,
    )

    assert result.status == RALPH_STATUS_COMPLETE
    assert result.completed is True
    assert repository_context_called == [True]
    assert repository_context_paths == [worktree_path]
    assert provider.run_count == 1


def _display_messages_as_text(display: SilentDisplay) -> str:
    return "\n".join(display.messages)


def test_ralph_displays_major_phases_on_success(
    monkeypatch,
    tmp_path,
) -> None:
    _patch_clean_repository_context(monkeypatch, tmp_path)
    _patch_successful_worktree_create(monkeypatch, tmp_path)
    _patch_successful_worktree_cleanup(monkeypatch, tmp_path)
    _patch_passing_test_runner(monkeypatch)
    _patch_successful_sync_merge(monkeypatch)

    display = SilentDisplay()
    provider = MockAgentProvider(responses=["Done\n<promise>COMPLETE</promise>"])

    result = i_ralph_run(
        issues=[
            GitHubIssue(
                number=25,
                title="Add display and logging phases",
                body="RALPH should display readable progress phases.",
                labels=("tracer bullet",),
            )
        ],
        agent_provider=provider,
        repo_path=tmp_path,
        display=display,
    )

    display_text = _display_messages_as_text(display)

    assert result.status == "complete"
    assert "Phase: setup" in display_text
    assert "Phase: worktree" in display_text
    assert "Phase: sandbox" in display_text
    assert "Phase: prompt" in display_text
    assert "Phase: agent" in display_text
    assert "Phase: tests" in display_text
    assert "Phase: commit" in display_text
    assert "Phase: cleanup" in display_text
    assert "Selected issue #25: Add display and logging phases" in display_text
    assert "Tests passed." in display_text
    assert "Commit created: test-commit-hash" in display_text


def test_ralph_displays_failed_test_diagnostics_and_preserved_worktree(
    monkeypatch,
    tmp_path,
) -> None:
    _patch_clean_repository_context(monkeypatch, tmp_path)
    _patch_successful_worktree_create(monkeypatch, tmp_path)

    worktree_path = tmp_path / "worktree"
    display = SilentDisplay()
    provider = MockAgentProvider(responses=["Done\n<promise>COMPLETE</promise>"])

    def fake_test_runner_run(
        sandbox_handle=None,
        command=None,
    ):
        return TestRunResult(
            passed=False,
            command=command or ("poetry", "run", "pytest"),
            message="Tests failed through the sandbox seam.",
            stdout="test stdout",
            stderr="pytest failed",
            exit_code=1,
        )

    def fail_sync_out_merge(*args, **kwargs):
        raise AssertionError("i_sync_out_merge() should not be called when tests fail.")

    def fake_worktree_cleanup(
        repo_path,
        worktree_path,
        completed,
        has_uncommitted_changes=None,
    ):
        return WorktreeCleanupResult(
            worktree_path=worktree_path,
            removed=False,
            preserved=True,
            reason="run_incomplete",
            message=f"Preserved worktree: {worktree_path}. Tests failed.",
        )

    monkeypatch.setattr(
        ralph_module,
        "i_test_runner_run",
        fake_test_runner_run,
    )
    monkeypatch.setattr(
        ralph_module,
        "i_sync_out_merge",
        fail_sync_out_merge,
    )
    monkeypatch.setattr(
        ralph_module,
        "i_worktree_cleanup",
        fake_worktree_cleanup,
    )

    result = i_ralph_run(
        issues=[
            GitHubIssue(
                number=25,
                title="Add display and logging phases",
                body="RALPH should display failed test diagnostics.",
                labels=("tracer bullet",),
            )
        ],
        agent_provider=provider,
        repo_path=tmp_path,
        display=display,
    )

    display_text = _display_messages_as_text(display)

    assert result.status == "failed"
    assert "Phase: tests" in display_text
    assert "Tests failed." in display_text
    assert "Exit code: 1" in display_text
    assert "Stdout: test stdout" in display_text
    assert "Stderr: pytest failed" in display_text
    assert f"Preserved worktree: {worktree_path}" in display_text


def test_ralph_displays_commit_hash_after_success(
    monkeypatch,
    tmp_path,
) -> None:
    _patch_clean_repository_context(monkeypatch, tmp_path)
    _patch_successful_worktree_create(monkeypatch, tmp_path)
    _patch_successful_worktree_cleanup(monkeypatch, tmp_path)
    _patch_passing_test_runner(monkeypatch)

    display = SilentDisplay()
    commit_hash = "displaycommit123"
    provider = MockAgentProvider(responses=["Done\n<promise>COMPLETE</promise>"])

    def fake_sync_out_merge(
        completed: bool,
        worktree_path=None,
        issue_number=None,
        issue_title="",
        commit_message_template=None,
    ):
        return SyncMergeResult(
            merged=True,
            committed=True,
            failed=False,
            commit_hash=commit_hash,
            worktree_path=worktree_path,
            has_changes=True,
            has_uncommitted_changes=False,
            message=f"Commit created: {commit_hash}.",
        )

    monkeypatch.setattr(
        ralph_module,
        "i_sync_out_merge",
        fake_sync_out_merge,
    )

    result = i_ralph_run(
        issues=[
            GitHubIssue(
                number=25,
                title="Add display and logging phases",
                body="RALPH should display successful commit hashes.",
                labels=("tracer bullet",),
            )
        ],
        agent_provider=provider,
        repo_path=tmp_path,
        display=display,
    )

    display_text = _display_messages_as_text(display)

    assert result.status == "complete"
    assert f"Commit created: {commit_hash}" in display_text


def test_ralph_displays_preserved_worktree_path_when_cleanup_preserves_work(
    monkeypatch,
    tmp_path,
) -> None:
    _patch_clean_repository_context(monkeypatch, tmp_path)
    _patch_successful_worktree_create(monkeypatch, tmp_path)
    _patch_passing_test_runner(monkeypatch)

    display = SilentDisplay()
    worktree_path = tmp_path / "worktree"
    provider = MockAgentProvider(responses=["Done\n<promise>COMPLETE</promise>"])

    def fake_sync_out_merge(
        completed: bool,
        worktree_path=None,
        issue_number=None,
        issue_title="",
        commit_message_template=None,
    ):
        return SyncMergeResult(
            merged=True,
            committed=True,
            failed=False,
            commit_hash="dirtydisplay123",
            worktree_path=worktree_path,
            has_changes=True,
            has_uncommitted_changes=True,
            status_output=" M src/generated_after_commit.py",
            message=(
                "Commit created: dirtydisplay123. "
                "Worktree still has uncommitted changes after commit."
            ),
        )

    def fake_worktree_cleanup(
        repo_path,
        worktree_path,
        completed,
        has_uncommitted_changes=None,
    ):
        return WorktreeCleanupResult(
            worktree_path=worktree_path,
            removed=False,
            preserved=True,
            reason="worktree_dirty",
            message=f"Preserved worktree: {worktree_path}. Git detected uncommitted changes.",
            status_output=" M src/generated_after_commit.py",
        )

    monkeypatch.setattr(
        ralph_module,
        "i_sync_out_merge",
        fake_sync_out_merge,
    )
    monkeypatch.setattr(
        ralph_module,
        "i_worktree_cleanup",
        fake_worktree_cleanup,
    )

    result = i_ralph_run(
        issues=[
            GitHubIssue(
                number=25,
                title="Add display and logging phases",
                body="RALPH should display preserved dirty worktree paths.",
                labels=("tracer bullet",),
            )
        ],
        agent_provider=provider,
        repo_path=tmp_path,
        display=display,
    )

    display_text = _display_messages_as_text(display)

    assert result.status == "complete"
    assert f"Preserved worktree: {worktree_path}" in display_text


def test_ralph_blocks_and_preserves_worktree_when_docker_sandbox_start_fails(
    monkeypatch,
    tmp_path,
) -> None:
    _patch_clean_repository_context(monkeypatch, tmp_path)
    _patch_successful_worktree_create(monkeypatch, tmp_path)

    worktree_path = tmp_path / "worktree"
    docker_failure_message = (
        "Docker sandbox startup failed: " "Docker image is missing: ai-code-test:latest"
    )
    sandbox_start_calls: list[object] = []
    cleanup_calls: list[dict[str, object]] = []
    display = SilentDisplay()

    def fake_sandbox_start(working_directory):
        sandbox_start_calls.append(working_directory)
        return SandboxStartResult(
            working_directory=working_directory,
            provider_name="docker",
            started=False,
            message=docker_failure_message,
            handle=None,
        )

    def fail_repository_context_discover(*args, **kwargs):
        raise AssertionError(
            "i_repository_context_discover() should not be called "
            "after Docker sandbox startup fails."
        )

    def fail_prompt_resolve(*args, **kwargs):
        raise AssertionError(
            "i_prompt_resolve() should not be called "
            "after Docker sandbox startup fails."
        )

    def fail_orchestrator_run(*args, **kwargs):
        raise AssertionError(
            "i_orchestrator_run() should not be called "
            "after Docker sandbox startup fails."
        )

    def fail_test_runner_run(*args, **kwargs):
        raise AssertionError(
            "i_test_runner_run() should not be called "
            "after Docker sandbox startup fails."
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
        fake_worktree_cleanup,
    )

    provider = MockAgentProvider(responses=["Done\n<promise>COMPLETE</promise>"])

    result = i_ralph_run(
        issues=[
            GitHubIssue(
                number=28,
                title="Add Docker sandbox mode selection",
                body=(
                    "RALPH should preserve the worktree when Docker sandbox "
                    "startup fails."
                ),
                labels=("tracer bullet",),
            )
        ],
        agent_provider=provider,
        repo_path=tmp_path,
        display=display,
    )

    display_text = "\n".join(display.messages)

    assert result.selected_issue is not None
    assert result.selected_issue.number == 28
    assert result.completed is False
    assert result.status == RALPH_STATUS_BLOCKED
    assert result.prompt == ""
    assert result.orchestrator_result is None
    assert docker_failure_message in result.message
    assert "Preserved worktree:" in result.message
    assert docker_failure_message in display_text
    assert "Phase: cleanup" in display_text
    assert f"Preserved worktree: {worktree_path}" in display_text
    assert sandbox_start_calls == [worktree_path]
    assert provider.run_count == 0
    assert cleanup_calls == [
        {
            "repo_path": tmp_path,
            "worktree_path": worktree_path,
            "completed": False,
            "has_uncommitted_changes": None,
        }
    ]


def _patch_successful_repository_context_discover(monkeypatch, tmp_path) -> None:
    def fake_repository_context_discover(repo_path):
        return RepositoryContextResult(
            repo_path=tmp_path,
            package_manager="poetry",
            test_command="poetry run pytest",
            test_command_source="configured",
            project_files=("pyproject.toml", "poetry.lock", "src/", "tests/"),
            useful_signals=("Python project", "Uses Poetry", "Uses pytest"),
            prompt_summary="Repository context summary for provider seam tests.",
        )

    monkeypatch.setattr(
        ralph_module,
        "i_repository_context_discover",
        fake_repository_context_discover,
    )


def _patch_successful_project_setup(monkeypatch) -> None:
    def fake_project_setup_run(worktree_path, sandbox_handle):
        return ProjectSetupResult(
            poetry_project=True,
            install_ran=True,
            install_passed=True,
            baseline_tests_ran=True,
            baseline_tests_passed=True,
            blocked=False,
            install_command=("poetry", "install"),
            install_stdout="poetry install passed",
            install_stderr="",
            install_exit_code=0,
            baseline_test_command=("poetry", "run", "pytest"),
            baseline_test_stdout="baseline tests passed",
            baseline_test_stderr="",
            baseline_test_exit_code=0,
            message="Poetry setup passed.",
        )

    monkeypatch.setattr(
        ralph_module,
        "i_project_setup_run",
        fake_project_setup_run,
    )


def test_ralph_displays_normalized_provider_events(
    monkeypatch,
    tmp_path,
) -> None:
    _patch_clean_repository_context(monkeypatch, tmp_path)
    _patch_successful_worktree_create(monkeypatch, tmp_path)
    _patch_successful_worktree_cleanup(monkeypatch, tmp_path)
    _patch_successful_project_setup(monkeypatch)
    _patch_successful_repository_context_discover(monkeypatch, tmp_path)
    _patch_passing_test_runner(monkeypatch)
    _patch_successful_sync_merge(monkeypatch)

    event = AgentProviderEvent(
        event_type="item.completed",
        item_type="agent_message",
        text="Codex normalized event output.",
        normalized_type=NORMALIZED_EVENT_TYPE_TEXT,
        raw={"secret": "raw json should not display"},
    )
    provider = MockAgentProvider(
        responses=[
            AgentResponse(
                output="Codex normalized event output.\n<promise>COMPLETE</promise>",
                events=(event,),
            )
        ]
    )
    display = SilentDisplay()

    result = i_ralph_run(
        issues=[
            GitHubIssue(
                number=43,
                title="Add CodexProvider stream event normalization",
                body="RALPH should display normalized provider events.",
                labels=("tracer bullet",),
            )
        ],
        agent_provider=provider,
        repo_path=tmp_path,
        display=display,
    )

    display_text = _display_messages_as_text(display)

    assert result.status == RALPH_STATUS_COMPLETE
    assert result.completed is True
    assert result.orchestrator_result is not None
    assert result.orchestrator_result.events == (event,)
    assert "Agent text: Codex normalized event output." in display_text
    assert "raw json should not display" not in display_text


def test_ralph_displays_provider_output_summary_without_prompt_body(
    monkeypatch,
    tmp_path,
) -> None:
    _patch_clean_repository_context(monkeypatch, tmp_path)
    _patch_successful_worktree_create(monkeypatch, tmp_path)
    _patch_successful_worktree_cleanup(monkeypatch, tmp_path)
    _patch_successful_project_setup(monkeypatch)
    _patch_successful_repository_context_discover(monkeypatch, tmp_path)
    _patch_passing_test_runner(monkeypatch)
    _patch_successful_sync_merge(monkeypatch)

    prompt_secret_text = "SECRET_PROMPT_BODY_SHOULD_NOT_DISPLAY_038"
    provider_output = (
        "Visible provider output for display.\n<promise>COMPLETE</promise>"
    )
    display = SilentDisplay()
    provider = MockAgentProvider(responses=[provider_output])

    result = i_ralph_run(
        issues=[
            GitHubIssue(
                number=38,
                title="Add agent provider seam",
                body=f"Do the provider seam work. {prompt_secret_text}",
                labels=("tracer bullet",),
            )
        ],
        agent_provider=provider,
        repo_path=tmp_path,
        display=display,
    )

    display_text = _display_messages_as_text(display)

    assert result.status == RALPH_STATUS_COMPLETE
    assert result.completed is True
    assert "Agent provider: MockAgentProvider" in display_text
    assert "Agent completed: True" in display_text
    assert (
        "Agent final output: Visible provider output for display. <promise>COMPLETE</promise>"
        in display_text
    )
    assert prompt_secret_text not in display_text


def test_ralph_uses_agent_provider_create_seam_when_no_provider_is_injected(
    monkeypatch,
    tmp_path,
) -> None:
    _patch_clean_repository_context(monkeypatch, tmp_path)
    _patch_successful_worktree_create(monkeypatch, tmp_path)
    _patch_successful_worktree_cleanup(monkeypatch, tmp_path)
    _patch_successful_project_setup(monkeypatch)
    _patch_successful_repository_context_discover(monkeypatch, tmp_path)
    _patch_passing_test_runner(monkeypatch)
    _patch_successful_sync_merge(monkeypatch)

    worktree_path = tmp_path / "worktree"
    sandbox_handle = FakeRalphAgentSandboxHandle(
        worktree_path,
        CommandResult(
            stdout="sandbox command passed",
            stderr="",
            exit_code=0,
        ),
    )
    seam_calls: list[dict[str, object]] = []
    fake_provider = MockAgentProvider(
        responses=["Provider seam completed.\n<promise>COMPLETE</promise>"]
    )

    monkeypatch.setattr(
        ralph_module.setup_config,
        "default_agent",
        "codex",
    )
    monkeypatch.setattr(
        ralph_module.setup_config,
        "codex_command",
        "codex",
    )

    def fake_sandbox_start(working_directory):
        return SandboxStartResult(
            working_directory=working_directory,
            provider_name="local",
            started=True,
            message="Started fake sandbox for provider seam test.",
            handle=sandbox_handle,
        )

    def fake_agent_provider_create(
        provider_name,
        sandbox_handle,
        worktree_path,
        codex_command="",
        final_output_path=None,
    ):
        seam_calls.append(
            {
                "provider_name": provider_name,
                "sandbox_handle": sandbox_handle,
                "worktree_path": worktree_path,
                "codex_command": codex_command,
                "final_output_path": final_output_path,
            }
        )
        return fake_provider

    monkeypatch.setattr(
        ralph_module,
        "i_sandbox_start",
        fake_sandbox_start,
    )
    monkeypatch.setattr(
        ralph_module,
        "i_agent_provider_create",
        fake_agent_provider_create,
    )

    result = i_ralph_run(
        issues=[
            GitHubIssue(
                number=38,
                title="Add agent provider seam",
                body="RALPH should create providers through the public seam.",
                labels=("tracer bullet",),
            )
        ],
        repo_path=tmp_path,
    )

    assert result.status == RALPH_STATUS_COMPLETE
    assert result.completed is True
    assert len(seam_calls) == 1
    assert seam_calls[0]["provider_name"] == "codex"
    assert seam_calls[0]["sandbox_handle"] is sandbox_handle
    assert seam_calls[0]["worktree_path"] == worktree_path
    assert seam_calls[0]["codex_command"] == "codex"
    assert seam_calls[0]["final_output_path"] is None

    seam_call_text = " ".join(str(value) for value in seam_calls[0].values())
    forbidden_codex_fragments = (
        "exec",
        "--cd",
        "--sandbox",
        "workspace-write",
        "--color",
        "--json",
        "--output-last-message",
        "--full-auto",
        "--dangerously-bypass-approvals-and-sandbox",
        "--yolo",
    )
    for forbidden_fragment in forbidden_codex_fragments:
        assert forbidden_fragment not in seam_call_text

    assert fake_provider.prompts
    assert (
        "RALPH should create providers through the public seam."
        in fake_provider.prompts[0]
    )
