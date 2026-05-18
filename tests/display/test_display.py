# tests/display/test_display.py
from ai_coder.display import ConsoleDisplay, SilentDisplay


from pathlib import Path

from ai_coder.display import (
    ConsoleDisplay,
    SilentDisplay,
    i_display_cleanup_result,
    i_display_command_failure,
    i_display_commit_result,
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
