# src/ai_coder/display/display.py
from __future__ import annotations

from typing import Protocol

_EMPTY_OUTPUT_TEXT = "<empty>"


class DisplayProtocol(Protocol):
    def i_display_message(self, message: str) -> None:
        raise NotImplementedError


class SilentDisplay:
    def __init__(self) -> None:
        self.messages: list[str] = []

    def i_display_message(self, message: str) -> None:
        self.messages.append(message)


class ConsoleDisplay:
    def i_display_message(self, message: str) -> None:
        print(message)


def i_display_phase(display: DisplayProtocol, phase_name: str) -> None:
    cleaned_phase_name = phase_name.strip().lower()
    display.i_display_message(f"Phase: {cleaned_phase_name}")


def i_display_selected_issue(
    display: DisplayProtocol,
    issue_number: int,
    issue_title: str,
) -> None:
    display.i_display_message(f"Selected issue #{issue_number}: {issue_title}")


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
