# src/ai_coder/display/display.py
from __future__ import annotations

from collections.abc import Iterable
from typing import Protocol

from ai_coder.agent_provider import (
    AgentProviderEvent,
    NORMALIZED_EVENT_TYPE_ERROR,
    NORMALIZED_EVENT_TYPE_RESULT,
    NORMALIZED_EVENT_TYPE_SESSION,
    NORMALIZED_EVENT_TYPE_TEXT,
    NORMALIZED_EVENT_TYPE_TOOL_CALL,
)

_EMPTY_OUTPUT_TEXT = "<empty>"
_REDACTED_SECRET_TEXT = "<redacted>"


class DisplayProtocol(Protocol):
    def i_display_message(self, message: str) -> None:
        raise NotImplementedError


class SilentDisplay:
    def __init__(self) -> None:
        self.messages: list[str] = []

    def i_display_message(self, message: str) -> None:
        self.messages.append(message)


class ConsoleDisplay:
    def __init__(self, secret_values: Iterable[object] = ()) -> None:
        self.secret_values = tuple(secret_values)

    def i_display_message(self, message: str) -> None:
        print(i_display_redact_text(message, self.secret_values))


def i_display_redact_text(
    text: object,
    secret_values: Iterable[object],
) -> str:
    redacted_text = str(text)

    for secret_value in secret_values:
        secret_text = str(secret_value).strip()

        if not secret_text:
            continue

        redacted_text = redacted_text.replace(
            secret_text,
            _REDACTED_SECRET_TEXT,
        )

    return redacted_text


def i_display_phase(display: DisplayProtocol, phase_name: str) -> None:
    cleaned_phase_name = phase_name.strip().lower()
    display.i_display_message(f"Phase: {cleaned_phase_name}")


def i_display_selected_issue(
    display: DisplayProtocol,
    issue_number: int,
    issue_title: str,
) -> None:
    display.i_display_message(f"Selected issue #{issue_number}: {issue_title}")


def i_display_issue_skip_reasons(
    display: DisplayProtocol,
    skipped_issues: Iterable[object],
) -> None:
    for skipped_issue in skipped_issues:
        issue_number = getattr(skipped_issue, "issue_number", "")
        reason = getattr(skipped_issue, "reason", "")
        message = getattr(skipped_issue, "message", "")

        display.i_display_message(
            f"Skipped issue #{issue_number}: {reason} — {message}"
        )


def i_display_agent_events(
    display: DisplayProtocol,
    events: Iterable[AgentProviderEvent],
) -> None:
    for event in events:
        message = _format_agent_event_message(event)

        if not message:
            continue

        display.i_display_message(message)


def i_display_command_failure(
    display: DisplayProtocol,
    *,
    stdout: str = "",
    stderr: str = "",
    exit_code: int | str | None = None,
) -> None:
    display.i_display_message("Command failed.")
    _display_command_diagnostics(
        display,
        stdout=stdout,
        stderr=stderr,
        exit_code=exit_code,
    )


def i_display_test_result(
    display: DisplayProtocol,
    *,
    passed: bool,
    stdout: str = "",
    stderr: str = "",
    exit_code: int | str | None = None,
) -> None:
    if passed:
        display.i_display_message("Tests passed.")
        return

    display.i_display_message("Tests failed.")
    _display_command_diagnostics(
        display,
        stdout=stdout,
        stderr=stderr,
        exit_code=exit_code,
    )


def i_display_commit_result(
    display: DisplayProtocol,
    *,
    committed: bool,
    commit_hash: str = "",
    message: str = "",
) -> None:
    if committed and commit_hash:
        display.i_display_message(f"Commit created: {commit_hash}")
        return

    if committed:
        display.i_display_message("Commit created.")
        return

    if message:
        display.i_display_message(message)
        return

    display.i_display_message("Commit skipped.")


def i_display_cleanup_result(
    display: DisplayProtocol,
    *,
    removed: bool,
    preserved: bool,
    worktree_path: object | None = None,
    message: str = "",
) -> None:
    worktree_path_text = "" if worktree_path is None else str(worktree_path)

    if preserved and worktree_path_text:
        display.i_display_message(f"Preserved worktree: {worktree_path_text}")
        return

    if removed and worktree_path_text:
        display.i_display_message(f"Removed worktree: {worktree_path_text}")
        return

    if message:
        display.i_display_message(message)


def i_display_pull_request_draft(
    display: DisplayProtocol,
    pull_request_draft_result: object,
) -> None:
    ready = bool(getattr(pull_request_draft_result, "ready", False))
    title = str(getattr(pull_request_draft_result, "title", "")).strip()
    suggested_command = str(
        getattr(pull_request_draft_result, "suggested_command", "")
    ).strip()
    message = str(getattr(pull_request_draft_result, "message", "")).strip()

    if not ready:
        display.i_display_message("Pull request workflow: skipped.")
        display.i_display_message(f"Reason: {_format_output_text(message)}")
        return

    display.i_display_message("Pull request workflow: future/disabled.")
    display.i_display_message("No pull request was created.")

    if title:
        display.i_display_message(f"Draft PR title: {title}")

    if suggested_command:
        display.i_display_message(f"Suggested PR command: {suggested_command}")


def i_display_issue_close_result(
    display: DisplayProtocol,
    issue_close_result: object,
) -> None:
    ready = bool(getattr(issue_close_result, "ready", False))
    dry_run = bool(getattr(issue_close_result, "dry_run", True))
    would_close = bool(getattr(issue_close_result, "would_close", False))
    issue_number = getattr(issue_close_result, "issue_number", "")
    suggested_command = str(
        getattr(issue_close_result, "suggested_command", "")
    ).strip()
    blocked_reason = str(getattr(issue_close_result, "blocked_reason", "")).strip()
    message = str(getattr(issue_close_result, "message", "")).strip()

    if not ready:
        display.i_display_message("Issue close workflow: skipped.")
        display.i_display_message(
            f"Reason: {_format_output_text(blocked_reason or message)}"
        )
        display.i_display_message("No GitHub issue was closed.")
        return

    if dry_run and would_close:
        display.i_display_message("Issue close workflow: dry-run.")
        display.i_display_message("No GitHub issue was closed.")
        display.i_display_message(
            f"Would close issue #{issue_number} after human review."
        )

        if suggested_command:
            display.i_display_message(
                f"Suggested issue close command: {suggested_command}"
            )

        return

    display.i_display_message("Issue close workflow: future/disabled.")
    display.i_display_message("No GitHub issue was closed.")

    if suggested_command:
        display.i_display_message(f"Suggested issue close command: {suggested_command}")


def _format_agent_event_message(event: AgentProviderEvent) -> str:
    if event.normalized_type == NORMALIZED_EVENT_TYPE_SESSION:
        return _format_agent_session_event(event)

    if event.normalized_type == NORMALIZED_EVENT_TYPE_TEXT:
        return _format_agent_text_event(event)

    if event.normalized_type == NORMALIZED_EVENT_TYPE_TOOL_CALL:
        return _format_agent_tool_call_event(event)

    if event.normalized_type == NORMALIZED_EVENT_TYPE_RESULT:
        return _format_agent_result_event(event)

    if event.normalized_type == NORMALIZED_EVENT_TYPE_ERROR:
        return _format_agent_error_event(event)

    return ""


def _format_agent_session_event(event: AgentProviderEvent) -> str:
    if event.session_id:
        return f"Agent session: {event.session_id}"

    return "Agent session event."


def _format_agent_text_event(event: AgentProviderEvent) -> str:
    text = _format_output_text(event.text)
    return f"Agent text: {text}"


def _format_agent_tool_call_event(event: AgentProviderEvent) -> str:
    tool_name = event.item_type or event.event_type or "unknown"
    status = event.status or "started"
    return f"Agent tool call: {tool_name} {status}"


def _format_agent_result_event(event: AgentProviderEvent) -> str:
    result_text = event.text or event.item_type or event.event_type
    return f"Agent result: {_format_output_text(result_text)}"


def _format_agent_error_event(event: AgentProviderEvent) -> str:
    error_text = event.text or event.event_type
    return f"Agent error: {_format_output_text(error_text)}"


def _display_command_diagnostics(
    display: DisplayProtocol,
    *,
    stdout: str = "",
    stderr: str = "",
    exit_code: int | str | None = None,
) -> None:
    exit_code_text = "unknown" if exit_code is None else str(exit_code)

    display.i_display_message(f"Exit code: {exit_code_text}")
    display.i_display_message(f"Stdout: {_format_output_text(stdout)}")
    display.i_display_message(f"Stderr: {_format_output_text(stderr)}")


def _format_output_text(output_text: str) -> str:
    cleaned_output_text = str(output_text).strip()

    if not cleaned_output_text:
        return _EMPTY_OUTPUT_TEXT

    return cleaned_output_text
