from ai_coder.github_issues import (
    GitHubIssue,
    i_github_issue_close,
    i_github_issue_from_file,
    i_github_issue_select,
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


def test_github_issue_skips_issue_blocked_by_open_issue() -> None:
    issues = [
        GitHubIssue(number=1, title="Parent setup", labels=("tracer",)),
        GitHubIssue(number=2, title="Blocked bug", labels=("bug",), blocked_by=(1,)),
    ]

    selected_issue = i_github_issue_select(issues)

    assert selected_issue is not None
    assert selected_issue.number == 1


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
