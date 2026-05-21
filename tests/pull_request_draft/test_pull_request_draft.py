# tests/pull_request_draft/test_pull_request_draft.py
from __future__ import annotations

import inspect

import ai_coder.pull_request_draft.pull_request_draft as pull_request_draft_module
from ai_coder.pull_request_draft import (
    PullRequestDraftResult,
    i_pull_request_draft_build,
)


def test_pull_request_draft_builds_ready_metadata_for_successful_run() -> None:
    result = i_pull_request_draft_build(
        issue_number=50,
        issue_title="Add pull request draft workflow placeholder",
        head_branch="ralph/issue-050-add-pr-draft-placeholder",
        commit_hash="abc123def456",
        tests_passed=True,
        committed=True,
        final_status="complete",
    )

    assert isinstance(result, PullRequestDraftResult)
    assert result.ready is True
    assert result.created is False
    assert result.enabled is False
    assert result.future_disabled is True
    assert result.issue_number == 50
    assert result.issue_title == "Add pull request draft workflow placeholder"
    assert result.base_branch == "main"
    assert result.head_branch == "ralph/issue-050-add-pr-draft-placeholder"
    assert result.commit_hash == "abc123def456"
    assert result.title == (
        "RALPH: issue #50 - Add pull request draft workflow placeholder"
    )
    assert "Refs #50" in result.body
    assert "abc123def456" in result.body
    assert "poetry run pytest passed" in result.body
    assert "future/disabled" in result.body
    assert "No pull request was created." in result.body
    assert "gh pr create" in result.suggested_command
    assert "--draft" in result.suggested_command
    assert "--base main" in result.suggested_command
    assert "--head ralph/issue-050-add-pr-draft-placeholder" in result.suggested_command
    assert "--title <reviewed-title>" in result.suggested_command
    assert "--body-file" in result.suggested_command
    assert "future/disabled" in result.message
    assert "no pull request was created" in result.message.lower()


def test_pull_request_draft_uses_refs_not_closing_keywords_in_body() -> None:
    result = i_pull_request_draft_build(
        issue_number=50,
        issue_title="Add pull request draft workflow placeholder",
        head_branch="ralph/issue-050-add-pr-draft-placeholder",
        commit_hash="abc123def456",
        tests_passed=True,
        committed=True,
        final_status="complete",
    )

    body_lower = result.body.lower()

    assert "refs #50" in body_lower
    assert "close #50" not in body_lower
    assert "closes #50" not in body_lower
    assert "closed #50" not in body_lower
    assert "fix #50" not in body_lower
    assert "fixes #50" not in body_lower
    assert "fixed #50" not in body_lower
    assert "resolve #50" not in body_lower
    assert "resolves #50" not in body_lower
    assert "resolved #50" not in body_lower


def test_pull_request_draft_returns_not_ready_when_run_is_incomplete() -> None:
    result = i_pull_request_draft_build(
        issue_number=50,
        issue_title="Add pull request draft workflow placeholder",
        head_branch="ralph/issue-050-add-pr-draft-placeholder",
        commit_hash="abc123def456",
        tests_passed=True,
        committed=True,
        final_status="incomplete",
    )

    assert result.ready is False
    assert result.created is False
    assert result.enabled is False
    assert result.future_disabled is True
    assert result.title == ""
    assert result.body == ""
    assert result.suggested_command == ""
    assert "skipped" in result.message.lower()
    assert "No pull request was created." in result.message


def test_pull_request_draft_returns_not_ready_when_tests_fail() -> None:
    result = i_pull_request_draft_build(
        issue_number=50,
        issue_title="Add pull request draft workflow placeholder",
        head_branch="ralph/issue-050-add-pr-draft-placeholder",
        commit_hash="abc123def456",
        tests_passed=False,
        committed=True,
        final_status="complete",
    )

    assert result.ready is False
    assert result.created is False
    assert result.suggested_command == ""
    assert "tests passed and committed changes" in result.message


def test_pull_request_draft_returns_not_ready_when_commit_is_missing() -> None:
    result = i_pull_request_draft_build(
        issue_number=50,
        issue_title="Add pull request draft workflow placeholder",
        head_branch="ralph/issue-050-add-pr-draft-placeholder",
        commit_hash="",
        tests_passed=True,
        committed=False,
        final_status="complete",
    )

    assert result.ready is False
    assert result.created is False
    assert result.suggested_command == ""
    assert "No pull request was created." in result.message


def test_pull_request_draft_module_does_not_require_subprocess_or_github_cli() -> None:
    module_source = inspect.getsource(pull_request_draft_module)

    assert "subprocess" not in module_source
    assert "GhCli" not in module_source

    result = i_pull_request_draft_build(
        issue_number=50,
        issue_title="Add pull request draft workflow placeholder",
        head_branch="ralph/issue-050-add-pr-draft-placeholder",
        commit_hash="abc123def456",
        tests_passed=True,
        committed=True,
        final_status="complete",
    )

    assert result.ready is True
    assert result.created is False
