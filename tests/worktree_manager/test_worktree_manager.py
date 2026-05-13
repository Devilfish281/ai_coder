# src/ai_coder/worktree_manager/worktree_manager.py
from types import SimpleNamespace
import pytest

import ai_coder.worktree_manager.worktree_manager as worktree_manager_module

from ai_coder.worktree_manager import (
    i_worktree_branch_name,
    i_worktree_create,
    i_worktree_create_command,
    i_worktree_preserve,
    i_worktree_sanitize_branch_name,
)


def test_worktree_sanitize_branch_name() -> None:
    result = i_worktree_sanitize_branch_name("Build RALPH Loop!!!")

    assert result == "build-ralph-loop"


def test_worktree_branch_name_includes_issue_number_and_safe_title() -> None:
    result = i_worktree_branch_name(12, "Fix Prompt Builder")

    assert result == "ralph-issue-12-fix-prompt-builder"


def test_worktree_create_command_is_testable_without_running_git() -> None:
    result = i_worktree_create_command(
        repo_path="C:/repo/ai_coder",
        worktree_path="C:/repo/ai_coder_worktrees/issue-12",
        branch_name="ralph-issue-12-fix-prompt-builder",
    )

    assert result == [
        "git",
        "-C",
        "C:/repo/ai_coder",
        "worktree",
        "add",
        "-b",
        "ralph-issue-12-fix-prompt-builder",
        "C:/repo/ai_coder_worktrees/issue-12",
    ]


def test_worktree_create_runs_git_command_when_creation_succeeds(
    monkeypatch,
    tmp_path,
) -> None:
    captured_commands: list[list[str]] = []

    def fake_run(command, capture_output, text, check):
        captured_commands.append(command)
        return SimpleNamespace(
            returncode=0,
            stdout="Preparing worktree",
            stderr="",
        )

    monkeypatch.setattr(
        worktree_manager_module,
        "subprocess",
        SimpleNamespace(run=fake_run),
        raising=False,
    )

    result = i_worktree_create(
        repo_path=tmp_path / "repo",
        issue_number=13,
        issue_title="Add safe worktree creation",
        worktree_root=tmp_path / "worktrees",
    )

    assert result.created is True
    assert result.branch_name == "ralph-issue-13-add-safe-worktree-creation"
    assert result.worktree_path.name == result.branch_name
    assert result.command == (
        "git",
        "-C",
        str(tmp_path / "repo"),
        "worktree",
        "add",
        "-b",
        "ralph-issue-13-add-safe-worktree-creation",
        str(tmp_path / "worktrees" / "ralph-issue-13-add-safe-worktree-creation"),
    )
    assert captured_commands == [list(result.command)]
    assert "Created Git worktree" in result.message


def test_worktree_branch_name_does_not_use_slashes() -> None:
    result = i_worktree_branch_name(1, "Minimal local RALPH loop")

    assert result == "ralph-issue-1-minimal-local-ralph-loop"
    assert "/" not in result


def test_worktree_preserve_preserves_failed_run() -> None:
    result = i_worktree_preserve(completed=False)

    assert result.preserved is True
    assert "stopped before completion" in result.reason


def test_worktree_create_defaults_to_hidden_ai_coder_worktree_root(tmp_path) -> None:
    repo_path = tmp_path / "ai_coder"

    result = i_worktree_create(
        repo_path=repo_path,
        issue_number=1,
        issue_title="Minimal local RALPH loop",
    )

    assert result.worktree_path == (
        repo_path
        / ".ai_coder"
        / "ai_coder_worktrees"
        / "ralph-issue-1-minimal-local-ralph-loop"
    )


def test_worktree_branch_name_shortens_long_issue_titles() -> None:  #
    long_title = (  #
        "Add a very very very very very very very very very very "  #
        "long worktree branch naming strategy for Windows paths"  #
    )  #

    result = i_worktree_branch_name(12, long_title)  #

    assert result.startswith("ralph-issue-12-")  #
    assert len(result) <= 80  #
    assert not result.endswith("-")  #


def test_worktree_branch_name_sanitizes_git_and_windows_unsafe_characters() -> None:  #
    result = i_worktree_branch_name(
        12, 'Fix prompt !`echo title` {{ISSUE_BODY}} / \\ : * ? " < > | [ ] ~ ^ @'
    )  #

    assert result.startswith("ralph-issue-12-")  #
    assert " " not in result  #
    assert "/" not in result  #
    assert "\\" not in result  #
    assert ":" not in result  #
    assert "*" not in result  #
    assert "?" not in result  #
    assert '"' not in result  #
    assert "<" not in result  #
    assert ">" not in result  #
    assert "|" not in result  #
    assert "[" not in result  #
    assert "]" not in result  #
    assert "~" not in result  #
    assert "^" not in result  #
    assert "@" not in result  #
    assert "--" not in result  #


def test_worktree_branch_name_uses_fallback_when_title_has_no_safe_characters() -> (
    None
):  #
    result = i_worktree_branch_name(12, "!!! /// ::: ***")  #

    assert result == "ralph-issue-12-work"  #


def test_worktree_branch_name_rejects_invalid_issue_number() -> None:  #
    with pytest.raises(ValueError, match="issue_number"):  #
        i_worktree_branch_name(0, "Fix bug")  #


def test_worktree_create_uses_shortened_branch_name_for_worktree_folder(
    tmp_path,
) -> None:  #
    repo_path = tmp_path / "ai_coder"  #
    long_title = (  #
        "Add a very very very very very very very very very very "  #
        "long worktree branch naming strategy for Windows paths"  #
    )  #

    result = i_worktree_create(  #
        repo_path=repo_path,  #
        issue_number=12,  #
        issue_title=long_title,  #
    )  #

    assert result.branch_name.startswith("ralph-issue-12-")  #
    assert len(result.branch_name) <= 80  #
    assert result.worktree_path.name == result.branch_name  #
    assert len(result.worktree_path.name) <= 80  #


def test_worktree_create_returns_failed_result_when_git_command_fails(
    monkeypatch,
    tmp_path,
) -> None:
    def fake_run(command, capture_output, text, check):
        return SimpleNamespace(
            returncode=128,
            stdout="",
            stderr="fatal: a branch named ralph-issue-13-add-safe-worktree-creation already exists",
        )

    monkeypatch.setattr(
        worktree_manager_module,
        "subprocess",
        SimpleNamespace(run=fake_run),
        raising=False,
    )

    result = i_worktree_create(
        repo_path=tmp_path / "repo",
        issue_number=13,
        issue_title="Add safe worktree creation",
        worktree_root=tmp_path / "worktrees",
    )

    assert result.created is False
    assert "Failed to create Git worktree" in result.message
    assert "fatal: a branch named" in result.message
    assert result.command[0] == "git"
    assert result.command[3:6] == ("worktree", "add", "-b")


def test_worktree_create_returns_failed_result_when_git_cannot_start(
    monkeypatch,
    tmp_path,
) -> None:
    def fake_run(command, capture_output, text, check):
        raise OSError("git not found")

    monkeypatch.setattr(
        worktree_manager_module,
        "subprocess",
        SimpleNamespace(run=fake_run),
        raising=False,
    )

    result = i_worktree_create(
        repo_path=tmp_path / "repo",
        issue_number=13,
        issue_title="Add safe worktree creation",
        worktree_root=tmp_path / "worktrees",
    )

    assert result.created is False
    assert "Failed to run Git worktree command" in result.message
    assert "git not found" in result.message
    assert result.command[0] == "git"


def test_worktree_create_blocks_existing_worktree_path_before_running_git(
    monkeypatch,
    tmp_path,
) -> None:
    worktree_path = tmp_path / "worktrees" / "ralph-issue-13-add-safe-worktree-creation"
    worktree_path.mkdir(parents=True)

    def fail_run(command, capture_output, text, check):
        raise AssertionError("subprocess.run() should not be called.")

    monkeypatch.setattr(
        worktree_manager_module,
        "subprocess",
        SimpleNamespace(run=fail_run),
        raising=False,
    )

    result = i_worktree_create(
        repo_path=tmp_path / "repo",
        issue_number=13,
        issue_title="Add safe worktree creation",
        worktree_root=tmp_path / "worktrees",
    )

    assert result.created is False
    assert result.worktree_path == worktree_path
    assert "already exists" in result.message
