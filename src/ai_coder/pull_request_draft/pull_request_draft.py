# src/ai_coder/pull_request_draft/pull_request_draft.py
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PullRequestDraftResult:
    ready: bool
    created: bool
    enabled: bool
    future_disabled: bool
    issue_number: int
    issue_title: str
    base_branch: str
    head_branch: str
    commit_hash: str
    title: str
    body: str
    suggested_command: str
    message: str


def i_pull_request_draft_build(
    *,
    issue_number: int,
    issue_title: str,
    head_branch: str,
    commit_hash: str,
    base_branch: str = "main",
    tests_passed: bool,
    committed: bool,
    final_status: str,
    verification_command: str = "poetry run pytest",
    reviewed_title_placeholder: str = "<reviewed-title>",
    reviewed_body_file: str = ".ai_coder/pr_draft_body.md",
) -> PullRequestDraftResult:
    """Build inert future PR draft metadata without creating a pull request."""

    cleaned_issue_title = issue_title.strip()
    cleaned_base_branch = base_branch.strip() or "main"
    cleaned_head_branch = head_branch.strip()
    cleaned_commit_hash = commit_hash.strip()
    cleaned_final_status = final_status.strip().lower()

    if not _has_successful_run_inputs(
        tests_passed=tests_passed,
        committed=committed,
        final_status=cleaned_final_status,
        head_branch=cleaned_head_branch,
        commit_hash=cleaned_commit_hash,
    ):
        return PullRequestDraftResult(
            ready=False,
            created=False,
            enabled=False,
            future_disabled=True,
            issue_number=issue_number,
            issue_title=cleaned_issue_title,
            base_branch=cleaned_base_branch,
            head_branch=cleaned_head_branch,
            commit_hash=cleaned_commit_hash,
            title="",
            body="",
            suggested_command="",
            message=(
                "Pull request workflow skipped. RALPH did not complete with "
                "tests passed and committed changes. No pull request was created."
            ),
        )

    title = f"RALPH: issue #{issue_number} - {cleaned_issue_title}"
    body = _build_draft_body(
        issue_number=issue_number,
        commit_hash=cleaned_commit_hash,
        verification_command=verification_command,
    )
    suggested_command = _build_suggested_command(
        base_branch=cleaned_base_branch,
        head_branch=cleaned_head_branch,
        reviewed_title_placeholder=reviewed_title_placeholder,
        reviewed_body_file=reviewed_body_file,
    )

    return PullRequestDraftResult(
        ready=True,
        created=False,
        enabled=False,
        future_disabled=True,
        issue_number=issue_number,
        issue_title=cleaned_issue_title,
        base_branch=cleaned_base_branch,
        head_branch=cleaned_head_branch,
        commit_hash=cleaned_commit_hash,
        title=title,
        body=body,
        suggested_command=suggested_command,
        message=(
            "Pull request workflow is future/disabled. "
            "Draft metadata is ready, but no pull request was created."
        ),
    )


def _has_successful_run_inputs(
    *,
    tests_passed: bool,
    committed: bool,
    final_status: str,
    head_branch: str,
    commit_hash: str,
) -> bool:
    return (
        tests_passed
        and committed
        and final_status == "complete"
        and bool(head_branch)
        and bool(commit_hash)
    )


def _build_draft_body(
    *,
    issue_number: int,
    commit_hash: str,
    verification_command: str,
) -> str:
    cleaned_verification_command = verification_command.strip() or "poetry run pytest"
    return "\n".join(
        (
            f"Refs #{issue_number}",
            "",
            "Summary: RALPH completed the safe workflow for this issue.",
            f"Commit: {commit_hash}",
            f"Verification: {cleaned_verification_command} passed.",
            "",
            "Pull request creation is future/disabled in this workflow slice.",
            "No pull request was created.",
        )
    )


def _build_suggested_command(
    *,
    base_branch: str,
    head_branch: str,
    reviewed_title_placeholder: str,
    reviewed_body_file: str,
) -> str:
    return " ".join(
        (
            "gh pr create",
            "--draft",
            f"--base {base_branch}",
            f"--head {head_branch}",
            f"--title {reviewed_title_placeholder}",
            f"--body-file {reviewed_body_file}",
        )
    )
