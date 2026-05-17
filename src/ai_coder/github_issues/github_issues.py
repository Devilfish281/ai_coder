# src/ai_coder/github_issues/github_issues.py
from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

# logger & setup_config
from ai_coder.setup_config import c_setup_config
from ai_coder.my_utils.env_loader import load_dotenv_once

load_dotenv_once()
setup_config = c_setup_config.get_instance()
logger = setup_config.get_logger()


@dataclass(frozen=True)
class GitHubIssue:
    number: int
    title: str
    body: str = ""
    labels: tuple[str, ...] = field(default_factory=tuple)
    state: str = "open"
    blocked_by: tuple[int, ...] = field(default_factory=tuple)
    assignees: tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class ProvidedIssueData:
    number: int
    title: str
    body: str = ""
    labels: tuple[str, ...] = ("tracer bullet",)


@dataclass(frozen=True)
class GitHubIssueSkipReason:
    issue_number: int
    reason: str
    message: str


@dataclass(frozen=True)
class GitHubIssueSelectionResult:
    selected_issue: GitHubIssue | None
    skipped_issues: tuple[GitHubIssueSkipReason, ...] = field(default_factory=tuple)
    message: str = ""


@dataclass(frozen=True)
class GitHubIssueCloseResult:
    issue_number: int
    closed: bool
    message: str


def i_github_issue_from_file(
    issue_path: str | Path,
    default_label: str = "tracer bullet",
) -> GitHubIssue:
    resolved_path = Path(issue_path)

    if not resolved_path.exists():
        raise FileNotFoundError(f"GitHub issue file does not exist: {resolved_path}")

    raw_text = resolved_path.read_text(encoding="utf-8")
    title = _extract_issue_title(raw_text)
    labels = _extract_issue_labels(raw_text, default_label)
    body = _extract_issue_body(raw_text)

    return GitHubIssue(
        number=1,
        title=title,
        body=body,
        labels=labels,
    )


def i_github_issue_from_provided(
    provided_issue: ProvidedIssueData,
) -> GitHubIssue:
    if provided_issue.number < 1:
        raise ValueError("provided issue number must be a positive integer")

    if not provided_issue.title.strip():
        raise ValueError("provided issue title cannot be empty")

    return GitHubIssue(
        number=provided_issue.number,
        title=provided_issue.title,
        body=provided_issue.body,
        labels=_normalize_provided_issue_labels(provided_issue.labels),
    )


def i_github_issue_list(label: str | None = None) -> tuple[GitHubIssue, ...]:
    command = [
        "gh",
        "issue",
        "list",
        "--repo",
        setup_config.github_repo,
        "--state",
        "open",
        "--json",
        "number,title,body,labels,assignees",
    ]

    logger.info(f"Listing GitHub issues with label: {label}")
    if label and label.strip():
        command.extend(["--label", label.strip()])
        logger.info(f"Added label filter to command: {label.strip()}")

    logger.info("Running command to list GitHub issues...")
    logger.debug(f"Command: {' '.join(command)}")
    completed_process = subprocess.run(
        command,
        capture_output=True,
        text=True,
        check=False,
    )

    stdout_text = completed_process.stdout or ""
    stderr_text = completed_process.stderr or ""

    logger.debug(f"GitHub issue list return code: {completed_process.returncode}")
    logger.debug(f"GitHub issue list stderr: {stderr_text.strip()}")

    if completed_process.returncode != 0:
        raise RuntimeError(
            "Failed to list GitHub issues with gh issue list: " f"{stderr_text.strip()}"
        )

    logger.info("Parsing GitHub issues from command output...")
    logger.debug(f"Raw command output: {stdout_text.strip()}")
    logger.info("Successfully listed GitHub issues. Parsing JSON output...")
    raw_issues = json.loads(stdout_text or "[]")

    logger.info(f"Parsed {len(raw_issues)} GitHub issues.")
    return tuple(_github_issue_from_gh_json(raw_issue) for raw_issue in raw_issues)


def i_github_issue_select_actionable(
    issues: Iterable[GitHubIssue],
) -> GitHubIssueSelectionResult:
    issue_list = list(issues)
    logger.info(
        "START: Selecting actionable issue from list of %d issues.", len(issue_list)
    )

    open_issue_numbers = {
        issue.number for issue in issue_list if issue.state.lower() == "open"
    }

    actionable_issues: list[GitHubIssue] = []
    skipped_issues: list[GitHubIssueSkipReason] = []

    for issue in issue_list:
        skip_reason = _evaluate_issue_actionability(
            issue=issue,
            open_issue_numbers=open_issue_numbers,
        )

        if skip_reason is not None:
            skipped_issues.append(skip_reason)
            continue

        actionable_issues.append(issue)

    if not actionable_issues:
        return GitHubIssueSelectionResult(
            selected_issue=None,
            skipped_issues=tuple(skipped_issues),
            message="No actionable issue selected.",
        )

    selected_issue = min(actionable_issues, key=_issue_sort_key)

    return GitHubIssueSelectionResult(
        selected_issue=selected_issue,
        skipped_issues=tuple(skipped_issues),
        message=f"Selected issue #{selected_issue.number}: {selected_issue.title}.",
    )


def i_github_issue_select(issues: Iterable[GitHubIssue]) -> GitHubIssue | None:
    result = i_github_issue_select_actionable(issues)
    return result.selected_issue


def i_github_issue_close(
    issue: GitHubIssue,
    tests_passed: bool,
    committed: bool,
) -> GitHubIssueCloseResult:
    logger.info("Starting GitHub issue closing process.")
    logger.info(f"Issue number: {issue.number}")
    logger.info(f"Tests passed: {tests_passed}")
    logger.info(f"Committed work confirmed: {committed}")
    if tests_passed and committed:
        logger.info(
            "Tests have passed and committed work is confirmed. Closing the issue."
        )
        return GitHubIssueCloseResult(
            issue_number=issue.number,
            closed=False,
            message="GitHub issue closing is stubbed in this tracer-bullet slice.",
        )

    logger.info(
        "Tests have not passed or committed work is not confirmed. Issue will not be closed."
    )
    return GitHubIssueCloseResult(
        issue_number=issue.number,
        closed=False,
        message="Issue was not closed because tests have not passed and committed work is not confirmed.",
    )


def _extract_issue_title(raw_text: str) -> str:
    title_from_template = _extract_first_content_line_after_heading(
        raw_text,
        "## Add a title",
    )

    if title_from_template:
        return title_from_template

    for line in raw_text.splitlines():
        stripped_line = line.strip()
        if stripped_line.startswith("# "):
            title = stripped_line.removeprefix("# ").strip()
            if title and title.lower() != "create new issue":
                return title

    raise ValueError("GitHub issue file must include a title.")


def _extract_issue_labels(
    raw_text: str,
    default_label: str,
) -> tuple[str, ...]:
    labels_section = _extract_markdown_section(raw_text, "### LABELS")
    if labels_section.strip():
        return _split_labels(labels_section, default_label)

    for line in raw_text.splitlines():
        stripped_line = line.strip()
        if stripped_line.lower().startswith("labels:"):
            raw_labels = stripped_line.split(":", maxsplit=1)[1]
            return _split_labels(raw_labels, default_label)

    return (default_label,)


def _extract_issue_body(raw_text: str) -> str:
    description_section = _extract_markdown_section(
        raw_text,
        "## Add a description",
    )

    if description_section.strip():
        body = _remove_markdown_section(description_section, "### LABELS")
        body = body.strip()

        if not body:
            raise ValueError("GitHub issue file must include a body after the title.")

        return body

    body_lines: list[str] = []

    for line in raw_text.splitlines():
        stripped_line = line.strip()

        if stripped_line.startswith("# "):
            continue

        if stripped_line.lower().startswith("labels:"):
            continue

        body_lines.append(line)

    body = "\n".join(body_lines).strip()

    if not body:
        raise ValueError("GitHub issue file must include a body after the title.")

    return body


def _extract_first_content_line_after_heading(
    raw_text: str,
    heading: str,
) -> str:
    section_text = _extract_markdown_section(raw_text, heading)

    for line in section_text.splitlines():
        stripped_line = line.strip()
        if stripped_line and not stripped_line.startswith("#"):
            return stripped_line

    return ""


def _extract_markdown_section(raw_text: str, heading: str) -> str:
    lines = raw_text.splitlines()
    heading_level = _markdown_heading_level(heading)
    collected_lines: list[str] = []
    collecting = False

    for line in lines:
        stripped_line = line.strip()

        if stripped_line.lower() == heading.lower():
            collecting = True
            continue

        if collecting and _is_same_or_higher_markdown_heading(
            stripped_line,
            heading_level,
        ):
            break

        if collecting:
            collected_lines.append(line)

    return "\n".join(collected_lines).strip()


def _remove_markdown_section(raw_text: str, heading: str) -> str:
    lines = raw_text.splitlines()
    heading_level = _markdown_heading_level(heading)
    kept_lines: list[str] = []
    skipping = False

    for line in lines:
        stripped_line = line.strip()

        if stripped_line.lower() == heading.lower():
            skipping = True
            continue

        if skipping and _is_same_or_higher_markdown_heading(
            stripped_line,
            heading_level,
        ):
            skipping = False

        if not skipping:
            kept_lines.append(line)

    return "\n".join(kept_lines).strip()


def _markdown_heading_level(line: str) -> int:
    stripped_line = line.strip()
    if not stripped_line.startswith("#"):
        return 0

    return len(stripped_line) - len(stripped_line.lstrip("#"))


def _is_same_or_higher_markdown_heading(
    line: str,
    heading_level: int,
) -> bool:
    current_level = _markdown_heading_level(line)
    return current_level > 0 and current_level <= heading_level


def _split_labels(raw_labels: str, default_label: str) -> tuple[str, ...]:
    labels = tuple(
        label.strip()
        for label in raw_labels.replace("\n", ",").split(",")
        if label.strip()
    )

    return labels or (default_label,)


def _normalize_provided_issue_labels(
    labels: Iterable[str] | None,
    default_label: str = "tracer bullet",
) -> tuple[str, ...]:
    if labels is None:
        return (default_label,)

    normalized_labels = tuple(
        str(label).strip() for label in labels if str(label).strip()
    )

    return normalized_labels or (default_label,)


ACTIONABLE_LABEL_MARKERS = (
    "bug",
    "tracer",
    "feature",
    "enhancement",
    "polish",
    "refactor",
)

UNSAFE_ISSUE_TEXT_MARKERS = (
    "delete repo",
    "delete repository",
    "rm -rf",
    "format drive",
    "disable tests",
    "skip tests",
    "ignore tests",
    "exfiltrate",
    "steal token",
    "print secrets",
    "dump env",
)


def _evaluate_issue_actionability(
    issue: GitHubIssue,
    open_issue_numbers: set[int],
) -> GitHubIssueSkipReason | None:
    if issue.state.lower() != "open":
        return _skip_reason(
            issue=issue,
            reason="closed",
            message=f"Skipped issue #{issue.number} because it is not open.",
        )

    open_blockers = tuple(
        blocker for blocker in issue.blocked_by if blocker in open_issue_numbers
    )

    if open_blockers:
        return _skip_reason(
            issue=issue,
            reason="blocked",
            message=(
                f"Skipped issue #{issue.number} because it is blocked by "
                f"open issue #{open_blockers[0]}."
            ),
        )

    if issue.assignees:
        return _skip_reason(
            issue=issue,
            reason="assigned",
            message=f"Skipped issue #{issue.number} because it is already assigned.",
        )

    if _issue_is_unsafe(issue):
        return _skip_reason(
            issue=issue,
            reason="unsafe",
            message=(
                f"Skipped issue #{issue.number} because it contains unsafe "
                "automation instructions."
            ),
        )

    if _issue_is_vague(issue):
        return _skip_reason(
            issue=issue,
            reason="vague",
            message=(
                f"Skipped issue #{issue.number} because it does not include "
                "enough actionable detail."
            ),
        )

    return None


def _issue_is_vague(issue: GitHubIssue) -> bool:
    title_word_count = len(issue.title.split())
    body_character_count = len("".join(issue.body.split()))
    label_text = " ".join(issue.labels).lower()

    has_actionable_label = any(
        marker in label_text for marker in ACTIONABLE_LABEL_MARKERS
    )

    return (
        title_word_count < 3 and body_character_count < 20 and not has_actionable_label
    )


def _issue_is_unsafe(issue: GitHubIssue) -> bool:
    issue_text = _issue_text_for_actionability(issue)

    return any(marker in issue_text for marker in UNSAFE_ISSUE_TEXT_MARKERS)


def _issue_text_for_actionability(issue: GitHubIssue) -> str:
    return " ".join(
        (
            issue.title,
            issue.body,
            *issue.labels,
        )
    ).lower()


def _skip_reason(
    issue: GitHubIssue,
    reason: str,
    message: str,
) -> GitHubIssueSkipReason:
    return GitHubIssueSkipReason(
        issue_number=issue.number,
        reason=reason,
        message=message,
    )


def _github_issue_from_gh_json(raw_issue: dict) -> GitHubIssue:
    raw_labels = raw_issue.get("labels", [])
    label_names = tuple(
        str(label.get("name", ""))
        for label in raw_labels
        if str(label.get("name", "")).strip()
    )

    raw_assignees = raw_issue.get("assignees", [])
    assignee_names = tuple(
        _assignee_name_from_gh_json(assignee)
        for assignee in raw_assignees
        if _assignee_name_from_gh_json(assignee)
    )

    return GitHubIssue(
        number=int(raw_issue["number"]),
        title=str(raw_issue.get("title", "")),
        body=str(raw_issue.get("body", "")),
        labels=label_names,
        assignees=assignee_names,
    )


def _assignee_name_from_gh_json(raw_assignee: object) -> str:
    if not isinstance(raw_assignee, dict):
        return str(raw_assignee).strip()

    login = str(raw_assignee.get("login", "")).strip()
    if login:
        return login

    name = str(raw_assignee.get("name", "")).strip()
    if name:
        return name

    return ""


def _issue_sort_key(issue: GitHubIssue) -> tuple[int, int]:
    return (_priority_for_issue(issue), issue.number)


def _priority_for_issue(issue: GitHubIssue) -> int:
    searchable_text = " ".join([issue.title, *issue.labels]).lower()

    if "bug" in searchable_text:
        return 0
    if "tracer" in searchable_text:
        return 1
    if "feature" in searchable_text:
        return 2
    if "enhancement" in searchable_text:
        return 2
    if "polish" in searchable_text:
        return 3
    if "refactor" in searchable_text:
        return 4

    return 5
