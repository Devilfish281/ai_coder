from __future__ import annotations

import subprocess
from collections.abc import Sequence
from pathlib import Path
from types import SimpleNamespace

import ai_coder.repository_context.repository_context as repository_context_module
from ai_coder.repository_context import i_repository_start


def test_repository_start_detects_repo_root_from_current_working_directory(
    monkeypatch,
    tmp_path,
) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    nested_path = repo_root / "src" / "ai_coder"
    nested_path.mkdir(parents=True)

    monkeypatch.chdir(nested_path)
    _patch_git_discovery(monkeypatch, repo_root=repo_root, branch_name="main")

    result = i_repository_start()

    assert result.ready is True
    assert result.repo_path == repo_root
    assert result.active_branch == "main"
    assert "Repository context discovered" in result.message


def test_repository_start_detects_repo_root_from_explicit_repo_path(
    monkeypatch,
    tmp_path,
) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()

    _patch_git_discovery(monkeypatch, repo_root=repo_root, branch_name="main")

    result = i_repository_start(repo_root)

    assert result.ready is True
    assert result.repo_path == repo_root
    assert result.active_branch == "main"
    assert "Repository context discovered" in result.message


def test_repository_start_detects_top_level_root_from_nested_path(
    monkeypatch,
    tmp_path,
) -> None:
    repo_root = tmp_path / "repo"
    nested_path = repo_root / "src" / "ai_coder"
    nested_path.mkdir(parents=True)

    _patch_git_discovery(monkeypatch, repo_root=repo_root, branch_name="feature/test")

    result = i_repository_start(nested_path)

    assert result.ready is True
    assert result.repo_path == repo_root
    assert result.repo_path != nested_path
    assert result.active_branch == "feature/test"


def test_repository_start_returns_blocked_result_for_non_repo_path(
    monkeypatch,
    tmp_path,
) -> None:
    non_repo_path = tmp_path / "not-a-repo"
    non_repo_path.mkdir()

    _patch_git_discovery(
        monkeypatch,
        repo_root=non_repo_path,
        branch_name="main",
        root_return_code=128,
        root_stderr="fatal: not a git repository",
    )

    result = i_repository_start(non_repo_path)

    assert result.ready is False
    assert result.repo_path == non_repo_path
    assert result.active_branch == ""
    assert result.message.startswith("Blocked:")
    assert "Could not detect a Git repository root" in result.message


def test_repository_start_returns_blocked_result_when_branch_discovery_fails(
    monkeypatch,
    tmp_path,
) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()

    _patch_git_discovery(
        monkeypatch,
        repo_root=repo_root,
        branch_name="",
        branch_return_code=128,
        branch_stderr="fatal: ambiguous argument HEAD",
    )

    result = i_repository_start(repo_root)

    assert result.ready is False
    assert result.repo_path == repo_root
    assert result.active_branch == ""
    assert result.message.startswith("Blocked:")
    assert "Could not detect an active Git branch" in result.message


def test_repository_start_returns_blocked_result_for_detached_head(
    monkeypatch,
    tmp_path,
) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()

    _patch_git_discovery(monkeypatch, repo_root=repo_root, branch_name="HEAD")

    result = i_repository_start(repo_root)

    assert result.ready is False
    assert result.repo_path == repo_root
    assert result.active_branch == ""
    assert result.message.startswith("Blocked:")
    assert "Could not detect an active Git branch" in result.message


def test_repository_start_allows_clean_main_repo_state(
    monkeypatch,
    tmp_path,
) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    commands: list[list[str]] = []

    _patch_git_discovery(
        monkeypatch,
        repo_root=repo_root,
        branch_name="main",
        status_stdout="",
        command_log=commands,
    )

    result = i_repository_start(repo_root)

    assert result.ready is True
    assert result.is_clean is True
    assert result.status_output == ""
    assert result.blocked_reason == ""
    assert result.repo_path == repo_root
    assert result.active_branch == "main"
    assert "Repository context discovered" in result.message
    assert ["git", "-C", str(repo_root), "status", "--porcelain"] in commands


def test_repository_start_blocks_dirty_main_repo_state(
    monkeypatch,
    tmp_path,
) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    dirty_status_output = " M src/ai_coder/ralph/ralph.py\n?? scratch.md\n"

    _patch_git_discovery(
        monkeypatch,
        repo_root=repo_root,
        branch_name="main",
        status_stdout=dirty_status_output,
    )

    result = i_repository_start(repo_root)

    assert result.ready is False
    assert result.is_clean is False
    assert "src/ai_coder/ralph/ralph.py" in result.status_output
    assert "scratch.md" in result.status_output
    assert "Blocked" in result.message
    assert "uncommitted changes" in result.message
    assert str(repo_root) in result.message  #  Added Code
    assert "main" in result.message  #  Added Code
    assert "RALPH stopped before worktree creation" in result.message  #  Added Code
    assert "Git status output:" in result.message  #  Added Code
    assert "Commit, stash, or discard" in result.message  #  Added Code
    assert result.blocked_reason == "repository_dirty"


def test_repository_start_blocks_clean_state_detection_failure(
    monkeypatch,
    tmp_path,
) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    git_error = "fatal: unable to read index"

    _patch_git_discovery(
        monkeypatch,
        repo_root=repo_root,
        branch_name="main",
        status_return_code=1,
        status_stderr=git_error,
    )

    result = i_repository_start(repo_root)

    assert result.ready is False
    assert result.is_clean is False
    assert "Blocked" in result.message
    assert "clean-state detection failed" in result.message
    assert git_error in result.status_output
    assert str(repo_root) in result.message  #  Added Code
    assert "main" in result.message  #  Added Code
    assert (
        "RALPH could not safely verify the repository clean state" in result.message
    )  #  Added Code
    assert "Git error output:" in result.message  #  Added Code
    assert "Run git status manually" in result.message  #  Added Code
    assert result.blocked_reason == "clean_state_detection_failed"


def _patch_git_discovery(
    monkeypatch,
    *,
    repo_root: Path,
    branch_name: str,
    root_return_code: int = 0,
    branch_return_code: int = 0,
    status_return_code: int = 0,
    root_stderr: str = "",
    branch_stderr: str = "",
    status_stdout: str = "",
    status_stderr: str = "",
    command_log: list[list[str]] | None = None,
) -> None:
    def fake_run(
        command: Sequence[str],
        *,
        capture_output: bool,
        text: bool,
        check: bool,
    ) -> subprocess.CompletedProcess[str]:
        command_parts = [str(part) for part in command]

        if command_log is not None:
            command_log.append(command_parts)

        assert capture_output is True
        assert text is True
        assert check is False
        assert command_parts[0] == "git"
        assert command_parts[1] == "-C"

        if command_parts[-2:] == ["rev-parse", "--show-toplevel"]:
            return subprocess.CompletedProcess(
                args=command_parts,
                returncode=root_return_code,
                stdout=f"{repo_root}\n" if root_return_code == 0 else "",
                stderr=root_stderr,
            )

        if command_parts[-3:] == ["rev-parse", "--abbrev-ref", "HEAD"]:
            return subprocess.CompletedProcess(
                args=command_parts,
                returncode=branch_return_code,
                stdout=f"{branch_name}\n" if branch_return_code == 0 else "",
                stderr=branch_stderr,
            )

        if command_parts[-2:] == ["status", "--porcelain"]:
            return subprocess.CompletedProcess(
                args=command_parts,
                returncode=status_return_code,
                stdout=status_stdout if status_return_code == 0 else "",
                stderr=status_stderr,
            )

        return subprocess.CompletedProcess(
            args=command_parts,
            returncode=1,
            stdout="",
            stderr=f"Unexpected command: {command_parts}",
        )

    monkeypatch.setattr(
        repository_context_module,
        "subprocess",
        SimpleNamespace(run=fake_run),
        raising=False,
    )
