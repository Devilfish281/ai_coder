# tests/display/test_display.py
from pathlib import Path


from ai_coder.github_issues import GitHubIssueSkipReason


from ai_coder.agent_provider import (
    AgentProviderEvent,
    NORMALIZED_EVENT_TYPE_ERROR,
    NORMALIZED_EVENT_TYPE_RESULT,
    NORMALIZED_EVENT_TYPE_SESSION,
    NORMALIZED_EVENT_TYPE_TEXT,
    NORMALIZED_EVENT_TYPE_TOOL_CALL,
)


from ai_coder.display import (
    ConsoleDisplay,
    SilentDisplay,
    i_display_agent_events,
    i_display_cleanup_result,
    i_display_command_failure,
    i_display_commit_result,
    i_display_issue_skip_reasons,
    i_display_phase,
    i_display_selected_issue,
    i_display_test_result,
)


def test_silent_display_stores_messages_without_printing(capsys) -> None:
    display = SilentDisplay()

    display.i_display_message("hello")

    assert display.messages == ["hello"]
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == ""


def test_console_display_prints_message(capsys) -> None:
    display = ConsoleDisplay()

    display.i_display_message("hello")

    captured = capsys.readouterr()
    assert captured.out == "hello\n"


def test_display_phase_stores_phase_message() -> None:
    display = SilentDisplay()

    i_display_phase(display, "setup")

    assert display.messages == ["Phase: setup"]


def test_display_selected_issue_stores_issue_number_and_title() -> None:
    display = SilentDisplay()

    i_display_selected_issue(
        display,
        issue_number=25,
        issue_title="Add display and logging phases",
    )

    assert display.messages == ["Selected issue #25: Add display and logging phases"]


def test_display_issue_skip_reasons_stores_readable_messages() -> None:
    display = SilentDisplay()
    skipped_issues = (
        GitHubIssueSkipReason(
            issue_number=4,
            reason="vague",
            message="Skipped issue #4 because it does not include enough actionable detail.",
        ),
        GitHubIssueSkipReason(
            issue_number=5,
            reason="unsafe",
            message="Skipped issue #5 because it contains unsafe automation instructions.",
        ),
    )

    i_display_issue_skip_reasons(display, skipped_issues)

    assert display.messages == [
        "Skipped issue #4: vague — Skipped issue #4 because it does not include enough actionable detail.",
        "Skipped issue #5: unsafe — Skipped issue #5 because it contains unsafe automation instructions.",
    ]


def test_display_issue_skip_reasons_ignores_empty_reason_list() -> None:
    display = SilentDisplay()

    i_display_issue_skip_reasons(display, ())

    assert display.messages == []


def test_display_command_failure_includes_stdout_stderr_and_exit_code() -> None:
    display = SilentDisplay()

    i_display_command_failure(
        display,
        stdout="command stdout",
        stderr="command stderr",
        exit_code=7,
    )

    assert display.messages == [
        "Command failed.",
        "Exit code: 7",
        "Stdout: command stdout",
        "Stderr: command stderr",
    ]


def test_display_command_failure_uses_empty_marker_for_missing_output() -> None:
    display = SilentDisplay()

    i_display_command_failure(
        display,
        stdout="",
        stderr="",
        exit_code=1,
    )

    assert display.messages == [
        "Command failed.",
        "Exit code: 1",
        "Stdout: <empty>",
        "Stderr: <empty>",
    ]


def test_display_test_result_shows_pass_message() -> None:
    display = SilentDisplay()

    i_display_test_result(
        display,
        passed=True,
        stdout="",
        stderr="",
        exit_code=0,
    )

    assert display.messages == ["Tests passed."]


def test_display_test_result_shows_fail_message_and_diagnostics() -> None:
    display = SilentDisplay()

    i_display_test_result(
        display,
        passed=False,
        stdout="test stdout",
        stderr="pytest failed",
        exit_code=1,
    )

    assert display.messages == [
        "Tests failed.",
        "Exit code: 1",
        "Stdout: test stdout",
        "Stderr: pytest failed",
    ]


def test_display_commit_result_shows_commit_hash() -> None:
    display = SilentDisplay()

    i_display_commit_result(
        display,
        committed=True,
        commit_hash="abc123def456",
    )

    assert display.messages == ["Commit created: abc123def456"]


def test_display_commit_result_shows_skipped_message() -> None:
    display = SilentDisplay()

    i_display_commit_result(
        display,
        committed=False,
        commit_hash="",
        message="Commit skipped because tests failed.",
    )

    assert display.messages == ["Commit skipped because tests failed."]


def test_display_cleanup_result_shows_preserved_worktree_path() -> None:
    display = SilentDisplay()
    worktree_path = Path("worktree")

    i_display_cleanup_result(
        display,
        removed=False,
        preserved=True,
        worktree_path=worktree_path,
    )

    assert display.messages == ["Preserved worktree: worktree"]


def test_display_cleanup_result_shows_removed_worktree_path() -> None:
    display = SilentDisplay()
    worktree_path = Path("worktree")

    i_display_cleanup_result(
        display,
        removed=True,
        preserved=False,
        worktree_path=worktree_path,
    )

    assert display.messages == ["Removed worktree: worktree"]


def test_display_agent_events_shows_readable_normalized_messages() -> None:
    display = SilentDisplay()
    events = (
        AgentProviderEvent(
            event_type="thread.started",
            session_id="thread_041",
            normalized_type=NORMALIZED_EVENT_TYPE_SESSION,
            raw={"secret": "raw json should not display"},
        ),
        AgentProviderEvent(
            event_type="item.completed",
            item_type="agent_message",
            text="Codex finished the issue.",
            normalized_type=NORMALIZED_EVENT_TYPE_TEXT,
            raw={"secret": "raw json should not display"},
        ),
        AgentProviderEvent(
            event_type="item.started",
            item_type="command_execution",
            status="started",
            normalized_type=NORMALIZED_EVENT_TYPE_TOOL_CALL,
            raw={"secret": "raw json should not display"},
        ),
        AgentProviderEvent(
            event_type="item.completed",
            item_type="command_execution",
            text="pytest passed",
            normalized_type=NORMALIZED_EVENT_TYPE_RESULT,
            raw={"secret": "raw json should not display"},
        ),
        AgentProviderEvent(
            event_type="error",
            text="Codex JSONL failure.",
            normalized_type=NORMALIZED_EVENT_TYPE_ERROR,
            raw={"secret": "raw json should not display"},
        ),
    )

    i_display_agent_events(display, events)

    assert display.messages == [
        "Agent session: thread_041",
        "Agent text: Codex finished the issue.",
        "Agent tool call: command_execution started",
        "Agent result: pytest passed",
        "Agent error: Codex JSONL failure.",
    ]
    assert "raw json should not display" not in "\n".join(display.messages)


def test_display_agent_events_ignores_empty_event_list() -> None:
    display = SilentDisplay()

    i_display_agent_events(display, ())

    assert display.messages == []
