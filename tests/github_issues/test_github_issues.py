# tests\github_issues\test_github_issues.py

from types import SimpleNamespace
import json

import pytest


import ai_coder.github_issues.github_issues as github_issues_module

from ai_coder.github_issues import (
    GitHubIssue,
    GitHubIssueSelectionResult,
    GitHubIssueSkipReason,
    ProvidedIssueData,
    i_github_issue_close,
    i_github_issue_from_file,
    i_github_issue_from_provided,
    i_github_issue_list,
    i_github_issue_select,
    i_github_issue_select_actionable,
)


###############################################################################
# Helper function
###############################################################################
def _configure_github_issue_safeguards(
    *,
    actionable_labels: tuple[str, ...] = (
        "bug",
        "tracer",
        "tracer bullet",
        "feature",
        "enhancement",
        "polish",
        "refactor",
        "Sandcastle",
    ),
    blocked_labels: tuple[str, ...] = ("blocked",),
    unsafe_labels: tuple[str, ...] = (
        "unsafe",
        "do-not-automate",
        "manual-only",
        "security-sensitive",
    ),
    skip_assigned_issues: bool = True,
    allowed_assignees: tuple[str, ...] = (),
) -> None:
    github_issues_module.setup_config.github_actionable_label_allowlist = (
        actionable_labels
    )
    github_issues_module.setup_config.github_blocked_label_list = blocked_labels
    github_issues_module.setup_config.github_unsafe_label_list = unsafe_labels
    github_issues_module.setup_config.github_skip_assigned_issues = skip_assigned_issues
    github_issues_module.setup_config.github_allowed_assignee_logins = allowed_assignees


def _get_safe_pr_close_policy():
    return github_issues_module.i_github_issue_get_safe_pr_close_policy()


###############################################################################
#  Functiona
###############################################################################
def test_safe_pr_close_policy_states_when_pr_creation_is_allowed() -> None:
    policy = _get_safe_pr_close_policy()
    policy_text = " ".join(policy.pr_creation_allowed_when).casefold()

    assert "single actionable" in policy_text
    assert "completion signal" in policy_text
    assert "tests passed" in policy_text
    assert "committed" in policy_text
    assert "human approval" in policy_text


def test_safe_pr_close_policy_states_when_issue_closing_is_allowed() -> None:
    policy = _get_safe_pr_close_policy()
    policy_text = " ".join(policy.issue_closing_allowed_when).casefold()

    assert "fully completed" in policy_text
    assert "tests passed" in policy_text
    assert "committed" in policy_text
    assert "complete" in policy_text
    assert "human approval" in policy_text


def test_safe_pr_close_policy_requires_tests_before_close() -> None:
    policy = _get_safe_pr_close_policy()

    assert policy.tests_must_pass_before_close is True


def test_safe_pr_close_policy_requires_commit_before_close() -> None:
    policy = _get_safe_pr_close_policy()

    assert policy.changes_must_be_committed_before_close is True


def test_safe_pr_close_policy_requires_human_approval_by_default() -> None:
    policy = _get_safe_pr_close_policy()

    assert policy.human_approval_required is True
    assert policy.automatic_pr_creation_default_enabled is False
    assert policy.automatic_issue_closing_default_enabled is False
    assert policy.closing_keyword_requires_human_approval is True


def test_github_issue_close_stub_does_not_close_issue() -> None:
    issue = GitHubIssue(
        number=49,
        title="Confirm safe PR and close policy",
        labels=("HITL", "Sandcastle"),
    )

    result = i_github_issue_close(
        issue=issue,
        tests_passed=True,
        committed=True,
    )

    assert result.issue_number == 49
    assert result.closed is False
    assert "stubbed" in result.message.lower()


def test_github_issue_close_does_not_close_when_tests_fail() -> None:
    issue = GitHubIssue(
        number=49,
        title="Confirm safe PR and close policy",
        labels=("HITL", "Sandcastle"),
    )

    result = i_github_issue_close(
        issue=issue,
        tests_passed=False,
        committed=True,
    )

    assert result.issue_number == 49
    assert result.closed is False
    assert "tests have not passed" in result.message.lower()


def test_github_issue_close_does_not_close_when_commit_missing() -> None:
    issue = GitHubIssue(
        number=49,
        title="Confirm safe PR and close policy",
        labels=("HITL", "Sandcastle"),
    )

    result = i_github_issue_close(
        issue=issue,
        tests_passed=True,
        committed=False,
    )

    assert result.issue_number == 49
    assert result.closed is False
    assert "committed work is not confirmed" in result.message.lower()


def test_github_issue_from_provided_data_builds_issue() -> None:
    provided_issue = ProvidedIssueData(
        number=10,
        title="Add provided issue data model",
        body="RALPH should accept provided issue data.",
        labels=("tracer bullet", "Sandcastle"),
    )

    issue = i_github_issue_from_provided(provided_issue)

    assert issue == GitHubIssue(
        number=10,
        title="Add provided issue data model",
        body="RALPH should accept provided issue data.",
        labels=("tracer bullet", "Sandcastle"),
    )
    assert issue.state == "open"
    assert issue.blocked_by == ()


def test_github_issue_from_provided_data_uses_safe_defaults() -> None:
    provided_issue = ProvidedIssueData(
        number=11,
        title="Use safe defaults",
    )

    issue = i_github_issue_from_provided(provided_issue)

    assert issue.number == 11
    assert issue.title == "Use safe defaults"
    assert issue.body == ""
    assert issue.labels == ("tracer bullet",)
    assert issue.state == "open"
    assert issue.blocked_by == ()


def test_github_issue_from_provided_data_preserves_special_characters_as_text() -> None:
    special_title = "Fix prompt !`echo title` {{ISSUE_BODY}}"
    special_body = "Body has !`echo unsafe` && rm -rf . and {{COMPLETE_TOKEN}}"

    provided_issue = ProvidedIssueData(
        number=12,
        title=special_title,
        body=special_body,
        labels=("bug", "needs review"),
    )

    issue = i_github_issue_from_provided(provided_issue)

    assert issue.number == 12
    assert issue.title == special_title
    assert issue.body == special_body
    assert issue.labels == ("bug", "needs review")
    assert isinstance(issue, GitHubIssue)


def test_github_issue_from_provided_data_rejects_invalid_issue_number() -> None:
    provided_issue = ProvidedIssueData(
        number=0,
        title="Invalid issue number",
    )

    with pytest.raises(ValueError, match="issue number"):
        i_github_issue_from_provided(provided_issue)


def test_github_issue_from_provided_data_rejects_empty_title() -> None:
    provided_issue = ProvidedIssueData(
        number=13,
        title="   ",
    )

    with pytest.raises(ValueError, match="title"):
        i_github_issue_from_provided(provided_issue)


def test_github_issue_select_actionable_returns_selection_result() -> None:
    issues = [
        GitHubIssue(
            number=6,
            title="Add actionable issue selection seam",
            body="RALPH should choose one actionable issue and report skipped reasons.",
            labels=("tracer bullet",),
        ),
    ]

    result = i_github_issue_select_actionable(issues)

    assert isinstance(result, GitHubIssueSelectionResult)
    assert result.selected_issue is not None
    assert result.selected_issue.number == 6
    assert result.skipped_issues == ()
    assert result.message == "Selected issue #6: Add actionable issue selection seam."


def test_github_issue_select_actionable_records_closed_skip_reason() -> None:
    issues = [
        GitHubIssue(
            number=3,
            title="Closed bug",
            body="This issue is already closed.",
            labels=("bug",),
            state="closed",
        ),
    ]

    result = i_github_issue_select_actionable(issues)

    assert result.selected_issue is None
    assert result.message == "No actionable issue selected."
    assert result.skipped_issues == (
        GitHubIssueSkipReason(
            issue_number=3,
            reason="closed",
            message="Skipped issue #3 because it is not open.",
        ),
    )


def test_github_issue_select_actionable_records_blocked_skip_reason() -> None:
    issues = [
        GitHubIssue(
            number=1,
            title="Parent setup",
            body="Parent work must happen first.",
            labels=("tracer bullet",),
        ),
        GitHubIssue(
            number=2,
            title="Fix blocked bug",
            body="This bug depends on the parent setup issue.",
            labels=("bug",),
            blocked_by=(1,),
        ),
    ]

    result = i_github_issue_select_actionable(issues)

    assert result.selected_issue is not None
    assert result.selected_issue.number == 1
    assert result.skipped_issues == (
        GitHubIssueSkipReason(
            issue_number=2,
            reason="blocked",
            message="Skipped issue #2 because it is blocked by open issue #1.",
        ),
    )


def test_github_issue_select_actionable_records_assigned_skip_reason() -> None:
    issues = [
        GitHubIssue(
            number=3,
            title="Fix assigned bug",
            body="This issue is already assigned to a person.",
            labels=("bug",),
            assignees=("octocat",),
        ),
    ]

    result = i_github_issue_select_actionable(issues)

    assert result.selected_issue is None
    assert result.skipped_issues == (
        GitHubIssueSkipReason(
            issue_number=3,
            reason="assigned",
            message="Skipped issue #3 because it is already assigned.",
        ),
    )


def test_github_issue_select_actionable_records_vague_skip_reason() -> None:
    issues = [
        GitHubIssue(
            number=4,
            title="Help",
            body="",
            labels=(),
        ),
    ]

    result = i_github_issue_select_actionable(issues)

    assert result.selected_issue is None
    assert result.skipped_issues == (
        GitHubIssueSkipReason(
            issue_number=4,
            reason="vague",
            message="Skipped issue #4 because it does not include enough actionable detail.",
        ),
    )


def test_github_issue_select_actionable_records_unsafe_skip_reason() -> None:
    issues = [
        GitHubIssue(
            number=5,
            title="Delete repo",
            body="Run rm -rf . and skip tests.",
            labels=("bug",),
        ),
    ]

    result = i_github_issue_select_actionable(issues)

    assert result.selected_issue is None
    assert result.skipped_issues == (
        GitHubIssueSkipReason(
            issue_number=5,
            reason="unsafe",
            message="Skipped issue #5 because it contains unsafe automation instructions.",
        ),
    )


def test_github_issue_select_compatibility_wrapper_returns_selected_issue() -> None:
    issues = [
        GitHubIssue(
            number=8,
            title="Polish README",
            body="Improve README wording.",
            labels=("polish",),
        ),
        GitHubIssue(
            number=7,
            title="Fix user-facing bug",
            body="Fix broken behavior that affects the user.",
            labels=("bug",),
        ),
    ]

    selected_issue = i_github_issue_select(issues)

    assert selected_issue is not None
    assert selected_issue.number == 7


def test_github_issue_list_requests_assignees_once(monkeypatch) -> None:
    captured_command: list[str] = []

    def fake_run(
        command,
        capture_output,
        text,
        encoding=None,
        errors=None,
        check=False,
    ):
        captured_command.extend(command)
        assert capture_output is True
        assert text is True
        assert encoding == "utf-8"
        assert errors == "replace"
        assert check is False

        return SimpleNamespace(
            returncode=0,
            stdout=(
                '[{"number":20,'
                '"title":"Fix assigned issue parsing",'
                '"body":"RALPH should parse assignees from GitHub issue JSON.",'
                '"labels":[{"name":"bug"}],'
                '"assignees":[{"login":"octocat"}]}]'
            ),
            stderr="",
        )

    monkeypatch.setattr(
        github_issues_module.subprocess,
        "run",
        fake_run,
    )

    issues = i_github_issue_list()

    assert captured_command == [
        "gh",
        "issue",
        "list",
        "--repo",
        github_issues_module.setup_config.github_repo,
        "--state",
        "open",
        "--json",
        "number,title,body,labels,assignees,state",
    ]

    assert issues == (
        GitHubIssue(
            number=20,
            title="Fix assigned issue parsing",
            body="RALPH should parse assignees from GitHub issue JSON.",
            labels=("bug",),
            assignees=("octocat",),
        ),
    )


def test_github_issue_selects_bug_before_tracer() -> None:
    issues = [
        GitHubIssue(number=2, title="Build tracer bullet", labels=("tracer",)),
        GitHubIssue(number=1, title="Fix broken prompt builder", labels=("bug",)),
    ]

    selected_issue = i_github_issue_select(issues)

    assert selected_issue is not None
    assert selected_issue.number == 1


def test_github_issue_selects_tracer_before_polish_and_refactor() -> None:
    issues = [
        GitHubIssue(number=3, title="Clean up names", labels=("refactor",)),
        GitHubIssue(number=2, title="Improve wording", labels=("polish",)),
        GitHubIssue(number=4, title="Minimal RALPH loop", labels=("tracer bullet",)),
    ]

    selected_issue = i_github_issue_select(issues)

    assert selected_issue is not None
    assert selected_issue.number == 4


def test_github_issue_select_actionable_records_blocked_label_skip_reason() -> None:
    issues = [
        GitHubIssue(
            number=22,
            title="Fix blocked label handling",
            body="This issue is marked blocked and should not be selected yet.",
            labels=("bug", "blocked"),
        ),
    ]

    result = i_github_issue_select_actionable(issues)

    assert result.selected_issue is None
    assert result.skipped_issues == (
        GitHubIssueSkipReason(
            issue_number=22,
            reason="blocked",
            message="Skipped issue #22 because it is marked blocked.",
        ),
    )


def test_github_issue_select_actionable_records_blocked_body_marker_skip_reason() -> (
    None
):
    issues = [
        GitHubIssue(
            number=45,
            title="Add GitHub issue reading adapter",
            body="Parent GitHub issue reader work.",
            labels=("tracer bullet",),
        ),
        GitHubIssue(
            number=46,
            title="Add GitHub issue filtering",
            body="Blocked by #45 until the GitHub reader adapter is complete.",
            labels=("tracer bullet",),
        ),
    ]

    result = i_github_issue_select_actionable(issues)

    assert result.selected_issue is not None
    assert result.selected_issue.number == 45
    assert result.skipped_issues == (
        GitHubIssueSkipReason(
            issue_number=46,
            reason="blocked",
            message="Skipped issue #46 because it is blocked by open issue #45.",
        ),
    )


def test_github_issue_select_actionable_selects_highest_priority_unskipped_issue() -> (
    None
):
    issues = [
        GitHubIssue(
            number=30,
            title="Delete repository bug",
            body="Run rm -rf . and skip tests.",
            labels=("bug",),
        ),
        GitHubIssue(
            number=31,
            title="Fix real user facing bug",
            body="The command result should preserve stderr when the command fails.",
            labels=("bug",),
        ),
        GitHubIssue(
            number=32,
            title="Build tracer bullet flow",
            body="Add a thin end-to-end tracer bullet for the next workflow slice.",
            labels=("tracer bullet",),
        ),
        GitHubIssue(
            number=33,
            title="Help",
            body="",
            labels=(),
        ),
    ]

    result = i_github_issue_select_actionable(issues)

    assert result.selected_issue is not None
    assert result.selected_issue.number == 31
    assert result.skipped_issues == (
        GitHubIssueSkipReason(
            issue_number=30,
            reason="unsafe",
            message="Skipped issue #30 because it contains unsafe automation instructions.",
        ),
        GitHubIssueSkipReason(
            issue_number=33,
            reason="vague",
            message="Skipped issue #33 because it does not include enough actionable detail.",
        ),
    )


def test_github_issue_skips_issue_blocked_by_open_issue() -> None:
    issues = [
        GitHubIssue(number=1, title="Parent setup", labels=("tracer",)),
        GitHubIssue(number=2, title="Blocked bug", labels=("bug",), blocked_by=(1,)),
    ]

    selected_issue = i_github_issue_select(issues)

    assert selected_issue is not None
    assert selected_issue.number == 1


def test_github_issue_select_actionable_uses_configured_blocked_label() -> None:
    _configure_github_issue_safeguards(
        blocked_labels=("waiting-on-human",),
    )
    issues = [
        GitHubIssue(
            number=48,
            title="Add blocked label safeguard",
            body="This issue has enough detail but should be blocked by label.",
            labels=("bug", "waiting-on-human"),
        ),
    ]

    result = i_github_issue_select_actionable(issues)

    assert result.selected_issue is None
    assert result.skipped_issues == (
        GitHubIssueSkipReason(
            issue_number=48,
            reason="blocked",
            message="Skipped issue #48 because it has blocked label 'waiting-on-human'.",
        ),
    )


def test_github_issue_select_actionable_uses_configured_unsafe_label() -> None:
    _configure_github_issue_safeguards(
        unsafe_labels=("manual-only",),
    )
    issues = [
        GitHubIssue(
            number=49,
            title="Review sensitive automation workflow",
            body="This issue has safe text but should not be automated.",
            labels=("bug", "manual-only"),
        ),
    ]

    result = i_github_issue_select_actionable(issues)

    assert result.selected_issue is None
    assert result.skipped_issues == (
        GitHubIssueSkipReason(
            issue_number=49,
            reason="unsafe",
            message="Skipped issue #49 because it has unsafe label 'manual-only'.",
        ),
    )


def test_github_issue_select_actionable_allows_configured_actionable_label() -> None:
    _configure_github_issue_safeguards(
        actionable_labels=("workflow-approved",),
    )
    issues = [
        GitHubIssue(
            number=50,
            title="Add workflow approved label support",
            body="RALPH should treat this configured label as actionable.",
            labels=("workflow-approved",),
        ),
    ]

    result = i_github_issue_select_actionable(issues)

    assert result.selected_issue is not None
    assert result.selected_issue.number == 50
    assert result.skipped_issues == ()


def test_github_issue_select_actionable_skips_label_outside_allowed_workflow() -> None:
    _configure_github_issue_safeguards(
        actionable_labels=("bug",),
    )
    issues = [
        GitHubIssue(
            number=51,
            title="Discuss future roadmap details",
            body="This issue is clear but does not match the allowed workflow labels.",
            labels=("discussion",),
        ),
    ]

    result = i_github_issue_select_actionable(issues)

    assert result.selected_issue is None
    assert result.skipped_issues == (
        GitHubIssueSkipReason(
            issue_number=51,
            reason="outside_workflow",
            message="Skipped issue #51 because it does not have an allowed workflow label.",
        ),
    )


def test_github_issue_select_actionable_matches_configured_labels_case_insensitively() -> (
    None
):
    _configure_github_issue_safeguards(
        actionable_labels=("Sandcastle",),
    )
    issues = [
        GitHubIssue(
            number=52,
            title="Add case insensitive label matching",
            body="RALPH should trim labels and compare them case-insensitively.",
            labels=("  sandcastle  ",),
        ),
    ]

    result = i_github_issue_select_actionable(issues)

    assert result.selected_issue is not None
    assert result.selected_issue.number == 52


def test_github_issue_select_actionable_allows_configured_assignee() -> None:
    _configure_github_issue_safeguards(
        allowed_assignees=("ralph-bot",),
    )
    issues = [
        GitHubIssue(
            number=53,
            title="Allow configured RALPH assignee",
            body="Assigned work should be selectable when every assignee is allowed.",
            labels=("bug",),
            assignees=("RALPH-BOT",),
        ),
    ]

    result = i_github_issue_select_actionable(issues)

    assert result.selected_issue is not None
    assert result.selected_issue.number == 53
    assert result.skipped_issues == ()


def test_github_issue_select_actionable_skips_unallowed_assignee() -> None:
    _configure_github_issue_safeguards(
        allowed_assignees=("ralph-bot",),
    )
    issues = [
        GitHubIssue(
            number=54,
            title="Reject non allowed assignee",
            body="Assigned work should be skipped when an assignee is not allowed.",
            labels=("bug",),
            assignees=("octocat",),
        ),
    ]

    result = i_github_issue_select_actionable(issues)

    assert result.selected_issue is None
    assert result.skipped_issues == (
        GitHubIssueSkipReason(
            issue_number=54,
            reason="assigned",
            message="Skipped issue #54 because assignee 'octocat' is not allowed.",
        ),
    )


def test_github_issue_select_actionable_unsafe_label_wins_over_assignment_skip() -> (
    None
):
    _configure_github_issue_safeguards(
        unsafe_labels=("manual-only",),
    )
    issues = [
        GitHubIssue(
            number=55,
            title="Unsafe assigned issue",
            body="Unsafe label should be reported before assignment status.",
            labels=("bug", "manual-only"),
            assignees=("octocat",),
        ),
    ]

    result = i_github_issue_select_actionable(issues)

    assert result.selected_issue is None
    assert result.skipped_issues == (
        GitHubIssueSkipReason(
            issue_number=55,
            reason="unsafe",
            message="Skipped issue #55 because it has unsafe label 'manual-only'.",
        ),
    )


def test_github_issue_returns_none_when_no_actionable_issue_exists() -> None:
    issues = [
        GitHubIssue(number=1, title="Closed bug", labels=("bug",), state="closed"),
    ]

    selected_issue = i_github_issue_select(issues)

    assert selected_issue is None


def test_github_issue_from_file_loads_markdown_issue(tmp_path) -> None:
    issue_file = tmp_path / "github_issue.md"
    issue_file.write_text(
        "# Add local issue fallback\n\n"
        "Labels: tracer bullet, Sandcastle\n\n"
        "## Problem\n\n"
        "RALPH needs a local issue file fallback.",
        encoding="utf-8",
    )

    issue = i_github_issue_from_file(issue_file)

    assert issue.number == 1
    assert issue.title == "Add local issue fallback"
    assert issue.labels == ("tracer bullet", "Sandcastle")
    assert "RALPH needs a local issue file fallback." in issue.body


def test_github_issue_from_file_loads_create_issue_template(tmp_path) -> None:
    issue_file = tmp_path / "github_issue.md"
    issue_file.write_text(
        "# Create new issue\n\n"
        "## Add a title\n\n"
        "Fix local RALPH loop\n\n"
        "## Add a description\n\n"
        "### ISSUE_BODY\n\n"
        "RALPH should follow and stubout this workflow:\n\n"
        "1. Start with a Git repository.\n"
        "2. Read open GitHub issues.\n\n"
        "### Goal\n\n"
        "Have RALPH follow the workflow above.\n\n"
        "### Test plan\n\n"
        "```powershell\n"
        "poetry run pytest\n"
        "```\n\n"
        "### LABELS\n\n"
        "Polish\n",
        encoding="utf-8",
    )

    issue = i_github_issue_from_file(issue_file)

    assert issue.title == "Fix local RALPH loop"
    assert issue.labels == ("Polish",)
    assert "### ISSUE_BODY" in issue.body
    assert "RALPH should follow and stubout this workflow:" in issue.body
    assert "### Goal" in issue.body
    assert "poetry run pytest" in issue.body
    assert "### LABELS" not in issue.body


def test_github_issue_close_stub_does_not_close_issue() -> None:
    issue = GitHubIssue(number=9, title="Fix local RALPH loop")

    result = i_github_issue_close(issue, tests_passed=True, committed=True)

    assert result.issue_number == 9
    assert result.closed is False
    assert "stubbed" in result.message


# 019 Tests for security and special character handling
def test_github_issue_from_provided_data_preserves_labels_with_special_characters() -> (
    None
):
    special_labels = (
        "label:needs-review",
        r"windows path C:\Temp\A&B",
        "pipe | label",
        'quote "label"',
        "percent %PATH%",
        "caret ^",
    )

    provided_issue = ProvidedIssueData(
        number=21,
        title="Preserve provided label text",
        body="RALPH should preserve provided label text exactly.",
        labels=special_labels,
    )

    issue = i_github_issue_from_provided(provided_issue)

    assert issue.labels == special_labels
    assert issue.labels[0] == "label:needs-review"
    assert issue.labels[-1] == "caret ^"


def test_github_issue_list_reads_open_issues_through_adapter(monkeypatch) -> None:
    captured_commands: list[list[str]] = []

    def fake_run(
        command,
        capture_output,
        text,
        encoding=None,
        errors=None,
        check=False,
    ):
        captured_commands.append(list(command))
        assert capture_output is True
        assert text is True
        assert encoding == "utf-8"
        assert errors == "replace"
        assert check is False

        return _fake_gh_completed_process(
            stdout=(
                '[{"number":45,'
                '"title":"Add GitHub issue reading adapter",'
                '"body":"Read open GitHub issues through a real adapter.",'
                '"labels":[{"name":"Sandcastle"},{"name":"tracer bullet"}],'
                '"assignees":[]}]'
            ),
        )

    monkeypatch.setattr(
        github_issues_module.subprocess,
        "run",
        fake_run,
    )

    issues = i_github_issue_list()

    assert captured_commands == [
        [
            "gh",
            "issue",
            "list",
            "--repo",
            github_issues_module.setup_config.github_repo,
            "--state",
            "open",
            "--json",
            "number,title,body,labels,assignees,state",
        ]
    ]
    assert issues == (
        GitHubIssue(
            number=45,
            title="Add GitHub issue reading adapter",
            body="Read open GitHub issues through a real adapter.",
            labels=("Sandcastle", "tracer bullet"),
        ),
    )


def test_github_issue_list_captures_number_title_body_and_labels(monkeypatch) -> None:
    captured_commands: list[list[str]] = []

    def fake_run(
        command,
        capture_output,
        text,
        encoding=None,
        errors=None,
        check=False,
    ):
        captured_commands.append(list(command))
        return _fake_gh_completed_process(
            stdout=(
                '[{"number":46,'
                '"title":"Read GitHub issue labels",'
                '"body":"RALPH should capture title, body, labels, and issue number.",'
                '"labels":[{"name":"bug"},{"name":"Sandcastle"}],'
                '"assignees":[]}]'
            ),
        )

    monkeypatch.setattr(
        github_issues_module.subprocess,
        "run",
        fake_run,
    )

    issues = i_github_issue_list(label="Sandcastle")

    assert captured_commands == [
        [
            "gh",
            "issue",
            "list",
            "--repo",
            github_issues_module.setup_config.github_repo,
            "--state",
            "open",
            "--json",
            "number,title,body,labels,assignees,state",
            "--label",
            "Sandcastle",
        ]
    ]
    assert len(issues) == 1
    assert issues[0].number == 46
    assert issues[0].title == "Read GitHub issue labels"
    assert (
        issues[0].body == "RALPH should capture title, body, labels, and issue number."
    )
    assert issues[0].labels == ("bug", "Sandcastle")


def test_github_issue_list_raises_clear_error_when_gh_command_fails(
    monkeypatch,
) -> None:
    def fake_run(
        command,
        capture_output,
        text,
        encoding=None,
        errors=None,
        check=False,
    ):
        return _fake_gh_completed_process(
            returncode=1,
            stderr="HTTP 401: authentication failed",
        )

    monkeypatch.setattr(
        github_issues_module.subprocess,
        "run",
        fake_run,
    )

    with pytest.raises(
        RuntimeError, match="Blocked: unable to read open GitHub issues"
    ) as exc_info:
        i_github_issue_list()

    message = str(exc_info.value)
    assert "Confirm GitHub CLI access" in message
    assert "GITHUB_REPO" in message
    assert "HTTP 401: authentication failed" in message


def test_github_issue_list_raises_clear_error_when_gh_is_missing(monkeypatch) -> None:
    def fake_run(
        command,
        capture_output,
        text,
        encoding=None,
        errors=None,
        check=False,
    ):
        raise FileNotFoundError("No such file or directory: 'gh'")

    monkeypatch.setattr(
        github_issues_module.subprocess,
        "run",
        fake_run,
    )

    with pytest.raises(
        RuntimeError, match="Blocked: unable to read open GitHub issues"
    ) as exc_info:
        i_github_issue_list()

    message = str(exc_info.value)
    assert "Confirm GitHub CLI access" in message
    assert "GITHUB_REPO" in message
    assert "gh" in message.lower()


def test_github_issue_list_raises_clear_error_when_json_is_malformed(
    monkeypatch,
) -> None:
    def fake_run(
        command,
        capture_output,
        text,
        encoding=None,
        errors=None,
        check=False,
    ):
        return _fake_gh_completed_process(
            stdout="{not valid json",
        )

    monkeypatch.setattr(
        github_issues_module.subprocess,
        "run",
        fake_run,
    )

    with pytest.raises(
        RuntimeError, match="Blocked: unable to read open GitHub issues"
    ) as exc_info:
        i_github_issue_list()

    message = str(exc_info.value)
    assert "Confirm GitHub CLI access" in message
    assert "GITHUB_REPO" in message
    assert "json" in message.lower()


def _fake_gh_completed_process(
    *,
    returncode: int = 0,
    stdout: str = "[]",
    stderr: str = "",
) -> SimpleNamespace:
    return SimpleNamespace(
        returncode=returncode,
        stdout=stdout,
        stderr=stderr,
    )


def test_github_issue_list_preserves_shell_like_issue_text_as_inert_text(
    monkeypatch,
) -> None:
    captured_commands: list[list[str]] = []
    shell_like_title = r"Fix Windows path C:\Users\ME\project && echo unsafe"
    shell_like_body = "Body includes !`echo unsafe` and {{ISSUE_BODY}}"
    shell_like_label = "bug && echo unsafe"

    def fake_run(
        command,
        capture_output,
        text,
        encoding=None,
        errors=None,
        check=False,
    ):
        captured_commands.append(list(command))
        return _fake_gh_completed_process(
            stdout=json.dumps(
                [
                    {
                        "number": 47,
                        "title": shell_like_title,
                        "body": shell_like_body,
                        "labels": [
                            {"name": "Sandcastle"},
                            {"name": shell_like_label},
                        ],
                        "assignees": [],
                    }
                ]
            ),
        )

    monkeypatch.setattr(
        github_issues_module.subprocess,
        "run",
        fake_run,
    )

    issues = i_github_issue_list()

    assert len(issues) == 1
    assert issues[0].number == 47
    assert issues[0].title == shell_like_title
    assert issues[0].body == shell_like_body
    assert issues[0].labels == ("Sandcastle", shell_like_label)

    command_text = " ".join(captured_commands[0])
    assert shell_like_title not in captured_commands[0]
    assert shell_like_body not in captured_commands[0]
    assert shell_like_label not in captured_commands[0]
    assert "&& echo unsafe" not in command_text
    assert "!`echo unsafe`" not in command_text
    assert "{{ISSUE_BODY}}" not in command_text


def test_github_issue_list_uses_fixed_command_shape_without_shell(monkeypatch) -> None:
    captured_calls: list[dict[str, object]] = []

    def fake_run(
        command,
        capture_output,
        text,
        encoding=None,
        errors=None,
        check=False,
        **kwargs,
    ):
        captured_calls.append(
            {
                "command": list(command),
                "capture_output": capture_output,
                "text": text,
                "encoding": encoding,
                "errors": errors,
                "check": check,
                "kwargs": kwargs,
            }
        )
        return _fake_gh_completed_process(stdout="[]")

    monkeypatch.setattr(
        github_issues_module.subprocess,
        "run",
        fake_run,
    )

    issues = i_github_issue_list(label="Sandcastle")

    assert issues == ()
    assert captured_calls == [
        {
            "command": [
                "gh",
                "issue",
                "list",
                "--repo",
                github_issues_module.setup_config.github_repo,
                "--state",
                "open",
                "--json",
                "number,title,body,labels,assignees,state",
                "--label",
                "Sandcastle",
            ],
            "capture_output": True,
            "text": True,
            "encoding": "utf-8",
            "errors": "replace",
            "check": False,
            "kwargs": {},
        }
    ]


def test_github_issue_list_raises_clear_error_when_json_list_contains_non_object(
    monkeypatch,
) -> None:
    def fake_run(
        command,
        capture_output,
        text,
        encoding=None,
        errors=None,
        check=False,
    ):
        return _fake_gh_completed_process(stdout='["not an issue object"]')

    monkeypatch.setattr(
        github_issues_module.subprocess,
        "run",
        fake_run,
    )

    with pytest.raises(
        RuntimeError, match="Blocked: unable to read open GitHub issues"
    ) as exc_info:
        i_github_issue_list()

    message = str(exc_info.value)
    assert "expected issue objects" in message


def test_github_issue_list_requests_filtering_fields_and_parses_state_and_assignees(
    monkeypatch,
) -> None:
    captured_commands: list[list[str]] = []

    def fake_run(
        command,
        capture_output,
        text,
        encoding=None,
        errors=None,
        check=False,
    ):
        captured_commands.append(list(command))
        assert capture_output is True
        assert text is True
        assert encoding == "utf-8"
        assert errors == "replace"
        assert check is False

        return _fake_gh_completed_process(
            stdout=json.dumps(
                [
                    {
                        "number": 50,
                        "title": "Fix adapter state parsing",
                        "body": "RALPH should parse issue state and assignees.",
                        "labels": [
                            {"name": "Sandcastle"},
                            {"name": "bug"},
                        ],
                        "assignees": [
                            {"login": "octocat"},
                        ],
                        "state": "open",
                    }
                ]
            ),
        )

    monkeypatch.setattr(
        github_issues_module.subprocess,
        "run",
        fake_run,
    )

    issues = i_github_issue_list(label="Sandcastle")

    assert captured_commands == [
        [
            "gh",
            "issue",
            "list",
            "--repo",
            github_issues_module.setup_config.github_repo,
            "--state",
            "open",
            "--json",
            "number,title,body,labels,assignees,state",
            "--label",
            "Sandcastle",
        ]
    ]
    assert issues == (
        GitHubIssue(
            number=50,
            title="Fix adapter state parsing",
            body="RALPH should parse issue state and assignees.",
            labels=("Sandcastle", "bug"),
            state="open",
            assignees=("octocat",),
        ),
    )


def test_github_issue_list_output_can_be_filtered_by_blocked_body_marker(
    monkeypatch,
) -> None:
    def fake_run(
        command,
        capture_output,
        text,
        encoding=None,
        errors=None,
        check=False,
    ):
        return _fake_gh_completed_process(
            stdout=json.dumps(
                [
                    {
                        "number": 45,
                        "title": "Add GitHub issue reading adapter",
                        "body": "Parent adapter issue.",
                        "labels": [{"name": "tracer bullet"}],
                        "assignees": [],
                        "state": "open",
                    },
                    {
                        "number": 46,
                        "title": "Add GitHub issue filtering",
                        "body": "Blocked by #45 until the reader adapter is complete.",
                        "labels": [{"name": "tracer bullet"}],
                        "assignees": [],
                        "state": "open",
                    },
                ]
            ),
        )

    monkeypatch.setattr(
        github_issues_module.subprocess,
        "run",
        fake_run,
    )

    issues = i_github_issue_list()
    result = i_github_issue_select_actionable(issues)

    assert result.selected_issue is not None
    assert result.selected_issue.number == 45
    assert result.skipped_issues == (
        GitHubIssueSkipReason(
            issue_number=46,
            reason="blocked",
            message="Skipped issue #46 because it is blocked by open issue #45.",
        ),
    )
