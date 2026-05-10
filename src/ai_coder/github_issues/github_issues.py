from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable


@dataclass(frozen=True)
class GitHubIssue:
    number: int
    title: str
    body: str = ""
    labels: tuple[str, ...] = field(default_factory=tuple)
    state: str = "open"
    blocked_by: tuple[int, ...] = field(default_factory=tuple)


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


def i_github_issue_list(label: str | None = None) -> tuple[GitHubIssue, ...]:
    command = [
        "gh",
        "issue",
        "list",
        "--state",
        "open",
        "--json",
        "number,title,body,labels",
    ]

    if label and label.strip():
        command.extend(["--label", label.strip()])

    completed_process = subprocess.run(
        command,
        capture_output=True,
        text=True,
        check=False,
    )

    if completed_process.returncode != 0:
        raise RuntimeError(
            "Failed to list GitHub issues with gh issue list: "
            f"{completed_process.stderr.strip()}"
        )

    raw_issues = json.loads(completed_process.stdout or "[]")
    return tuple(_github_issue_from_gh_json(raw_issue) for raw_issue in raw_issues)


def i_github_issue_select(issues: Iterable[GitHubIssue]) -> GitHubIssue | None:
    issue_list = list(issues)
    open_issue_numbers = {
        issue.number for issue in issue_list if issue.state.lower() == "open"
    }

    actionable_issues = [
        issue
        for issue in issue_list
        if issue.state.lower() == "open"
        and not any(blocker in open_issue_numbers for blocker in issue.blocked_by)
    ]

    if not actionable_issues:
        return None

    return min(actionable_issues, key=_issue_sort_key)


def i_github_issue_close(
    issue: GitHubIssue,
    tests_passed: bool,
    committed: bool,
) -> GitHubIssueCloseResult:
    if tests_passed and committed:
        return GitHubIssueCloseResult(
            issue_number=issue.number,
            closed=False,
            message="GitHub issue closing is stubbed in this tracer-bullet slice.",
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


def _github_issue_from_gh_json(raw_issue: dict) -> GitHubIssue:
    raw_labels = raw_issue.get("labels", [])
    label_names = tuple(
        str(label.get("name", ""))
        for label in raw_labels
        if str(label.get("name", "")).strip()
    )

    return GitHubIssue(
        number=int(raw_issue["number"]),
        title=str(raw_issue.get("title", "")),
        body=str(raw_issue.get("body", "")),
        labels=label_names,
    )


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
