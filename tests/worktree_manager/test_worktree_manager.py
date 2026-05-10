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

    assert result == "ralph/issue-12-fix-prompt-builder"


def test_worktree_create_command_is_testable_without_running_git() -> None:
    result = i_worktree_create_command(
        repo_path="C:/repo/ai_coder",
        worktree_path="C:/repo/ai_coder_worktrees/issue-12",
        branch_name="ralph/issue-12-fix-prompt-builder",
    )

    assert result == [
        "git",
        "-C",
        "C:/repo/ai_coder",
        "worktree",
        "add",
        "-b",
        "ralph/issue-12-fix-prompt-builder",
        "C:/repo/ai_coder_worktrees/issue-12",
    ]


def test_worktree_create_stub_returns_command_without_running_git(tmp_path) -> None:
    result = i_worktree_create(
        repo_path=tmp_path / "repo",
        issue_number=12,
        issue_title="Fix Prompt Builder",
        worktree_root=tmp_path / "worktrees",
    )

    assert result.created is False
    assert result.branch_name == "ralph/issue-12-fix-prompt-builder"
    assert result.command[0] == "git"
    assert "stubbed" in result.message


def test_worktree_preserve_preserves_failed_run() -> None:
    result = i_worktree_preserve(completed=False)

    assert result.preserved is True
    assert "stopped before completion" in result.reason
