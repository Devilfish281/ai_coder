from ai_coder.agent_provider import MockAgentProvider
from ai_coder.github_issues import GitHubIssue
from ai_coder.repository_context import RepositoryStartResult
from ai_coder.ralph import i_ralph_run
from ai_coder.worktree_manager import WorktreeCreateResult

import ai_coder.ralph.ralph as ralph_module
from ai_coder.setup_config import c_setup_config


def _refresh_ralph_config() -> None:
    c_setup_config._instance = None
    ralph_module.setup_config = c_setup_config.get_instance()
    ralph_module.logger = ralph_module.setup_config.get_logger()


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


def test_ralph_stops_before_worktree_creation_when_repository_is_blocked(
    monkeypatch,
    tmp_path,
) -> None:
    dirty_status_output = " M src/ai_coder/ralph/ralph.py\n?? scratch.md"
    blocked_message = (  #  Changed Code
        "Blocked: Repository has uncommitted changes. "  #  Changed Code
        f"Repository root: {tmp_path}. "  #  Changed Code
        "Active branch: main. "  #  Changed Code
        "RALPH stopped before worktree creation because the main repository is unsafe. "  #  Changed Code
        "Commit, stash, or discard the changes, then run RALPH again.\n\n"  #  Changed Code
        f"Git status output:\n{dirty_status_output}"  #  Changed Code
    )  #  Changed Code

    def fake_repository_start(repo_path):
        return RepositoryStartResult(
            repo_path=tmp_path,
            ready=False,
            message=blocked_message,
            active_branch="main",
            is_clean=False,
            status_output=dirty_status_output,  #  Changed Code
            blocked_reason="repository_dirty",
        )

    def fail_worktree_create(*args, **kwargs):
        raise AssertionError("i_worktree_create() should not be called.")

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

    worktree_calls: list[dict[str, object]] = []
    worktree_path = tmp_path / "worktree"

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
            created=False,
            message="Worktree creation is stubbed in this tracer-bullet slice.",
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


def test_ralph_selects_issue_builds_prompt_and_completes(
    monkeypatch,
    tmp_path,
) -> None:
    _patch_clean_repository_context(monkeypatch, tmp_path)

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
    assert result.message == "RALPH stopped before completion."


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
    assert result.status == "incomplete"
    assert result.message == "No open actionable issue selected."


def test_ralph_resolves_prompt_file_before_preprocessing(
    monkeypatch,
    tmp_path,
) -> None:
    _patch_clean_repository_context(monkeypatch, tmp_path)

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
        agent_provider=provider,
        prompt_path=prompt_file,
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
