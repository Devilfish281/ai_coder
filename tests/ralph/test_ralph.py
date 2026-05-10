from ai_coder.agent_provider import MockAgentProvider
from ai_coder.github_issues import GitHubIssue
from ai_coder.ralph import i_ralph_run


import ai_coder.ralph.ralph as ralph_module
from ai_coder.setup_config import c_setup_config


def _refresh_ralph_config() -> None:
    c_setup_config._instance = None
    ralph_module.setup_config = c_setup_config.get_instance()
    ralph_module.logger = ralph_module.setup_config.get_logger()


def test_ralph_selects_issue_builds_prompt_and_completes() -> None:
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
    assert result.orchestrator_result is not None
    assert result.orchestrator_result.iterations == 1


def test_ralph_returns_clear_result_when_no_issue_is_selected() -> None:
    result = i_ralph_run([GitHubIssue(number=1, title="Closed issue", state="closed")])

    assert result.selected_issue is None
    assert result.prompt == ""
    assert result.orchestrator_result is None
    assert result.completed is False
    assert result.message == "No open actionable issue selected."


def test_ralph_resolves_prompt_file_before_preprocessing(tmp_path) -> None:
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
    assert "Issue #9: Use prompt resolver" in result.prompt
    assert "Body: Load the raw template before preprocessing." in result.prompt
    assert "Done token: <promise>COMPLETE</promise>" in result.prompt
    assert provider.prompts == [result.prompt]


def test_ralph_creates_test_issue_when_no_issues_and_testing_flag(monkeypatch) -> None:
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

    provider = MockAgentProvider(responses=["Done\n<promise>COMPLETE</promise>"])

    result = i_ralph_run(
        issues=None,
        agent_provider=provider,
    )

    assert result.completed is True
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

    provider = MockAgentProvider(responses=["Done\n<promise>COMPLETE</promise>"])

    result = i_ralph_run(
        issues=None,
        agent_provider=provider,
    )

    assert result.completed is True
    assert result.selected_issue is not None
    assert result.selected_issue.title == "Add local issue fallback"
    assert "RALPH should load this issue from a local markdown file." in result.prompt
