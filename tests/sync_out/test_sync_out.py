# tests/sync_out/test_sync_out.py
from pathlib import Path
from types import SimpleNamespace

import ai_coder.sync_out.sync_out as sync_out_module
from ai_coder.sync_out import SyncMergeResult, i_sync_out_merge, i_sync_out_run


def test_sync_out_run_returns_clear_minimal_result() -> None:
    result = i_sync_out_run("source", "target")

    assert result.source_path == Path("source")
    assert result.target_path == Path("target")
    assert result.changed is False


def test_sync_out_merge_stub_does_not_merge() -> None:
    result = i_sync_out_merge(completed=True)

    assert result.merged is False
    assert result.committed is False
    assert result.failed is False
    assert "stubbed" in result.message


def test_sync_merge_result_can_represent_explicit_failure() -> None:
    result = SyncMergeResult(
        merged=False,
        failed=True,
        message="Sync or commit failed.",
    )

    assert result.merged is False
    assert result.committed is False
    assert result.failed is True
    assert "failed" in result.message


def test_sync_out_merge_does_not_commit_when_not_completed(
    monkeypatch,
    tmp_path,
) -> None:
    def fail_run(*args, **kwargs):
        raise AssertionError("subprocess.run() should not be called.")

    monkeypatch.setattr(
        sync_out_module,
        "subprocess",
        SimpleNamespace(run=fail_run),
    )

    result = i_sync_out_merge(
        completed=False,
        worktree_path=tmp_path,
        issue_number=24,
        issue_title="Commit successful work",
    )

    assert result.failed is False
    assert result.merged is False
    assert result.committed is False
    assert result.commit_hash == ""
    assert result.worktree_path == tmp_path
    assert "Skipped sync or merge because RALPH did not complete" in result.message


def test_sync_out_merge_commits_successful_changes_and_returns_hash(
    monkeypatch,
    tmp_path,
) -> None:
    worktree_path = tmp_path / "worktree"
    worktree_path.mkdir()
    fake_hash = "abc123def4567890"
    captured_commands: list[list[str]] = []

    def fake_run(command, capture_output, text, check):
        command_parts = [str(part) for part in command]
        captured_commands.append(command_parts)

        assert capture_output is True
        assert text is True
        assert check is False

        if command_parts[-2:] == ["status", "--porcelain"]:
            if len(captured_commands) == 1:
                return SimpleNamespace(
                    returncode=0,
                    stdout=" M src/file.py\n?? tests/test_file.py\n",
                    stderr="",
                )

            return SimpleNamespace(
                returncode=0,
                stdout="",
                stderr="",
            )

        if command_parts[-2:] == ["add", "-A"]:
            return SimpleNamespace(
                returncode=0,
                stdout="",
                stderr="",
            )

        if command_parts[3:5] == ["commit", "-m"]:
            return SimpleNamespace(
                returncode=0,
                stdout="[branch abc123] RALPH commit\n",
                stderr="",
            )

        if command_parts[-2:] == ["rev-parse", "HEAD"]:
            return SimpleNamespace(
                returncode=0,
                stdout=f"{fake_hash}\n",
                stderr="",
            )

        return SimpleNamespace(
            returncode=1,
            stdout="",
            stderr=f"Unexpected command: {command_parts}",
        )

    monkeypatch.setattr(
        sync_out_module,
        "subprocess",
        SimpleNamespace(run=fake_run),
    )

    result = i_sync_out_merge(
        completed=True,
        worktree_path=worktree_path,
        issue_number=24,
        issue_title="Commit successful work",
        commit_message_template="RALPH: issue #{issue_number} - {issue_title}",
    )

    expected_commit_message = "RALPH: issue #24 - Commit successful work"

    assert result.failed is False
    assert result.merged is True
    assert result.committed is True
    assert result.commit_hash == fake_hash
    assert result.worktree_path == worktree_path
    assert result.has_changes is True
    assert result.has_uncommitted_changes is False
    assert fake_hash in result.message
    assert "Commit created" in result.message

    assert captured_commands == [
        ["git", "-C", str(worktree_path), "status", "--porcelain"],
        ["git", "-C", str(worktree_path), "add", "-A"],
        ["git", "-C", str(worktree_path), "commit", "-m", expected_commit_message],
        ["git", "-C", str(worktree_path), "rev-parse", "HEAD"],
        ["git", "-C", str(worktree_path), "status", "--porcelain"],
    ]


def test_sync_out_merge_reports_no_changes_when_status_is_clean(
    monkeypatch,
    tmp_path,
) -> None:
    worktree_path = tmp_path / "worktree"
    worktree_path.mkdir()
    captured_commands: list[list[str]] = []

    def fake_run(command, capture_output, text, check):
        command_parts = [str(part) for part in command]
        captured_commands.append(command_parts)

        return SimpleNamespace(
            returncode=0,
            stdout="",
            stderr="",
        )

    monkeypatch.setattr(
        sync_out_module,
        "subprocess",
        SimpleNamespace(run=fake_run),
    )

    result = i_sync_out_merge(
        completed=True,
        worktree_path=worktree_path,
        issue_number=24,
        issue_title="Commit successful work",
    )

    assert result.failed is False
    assert result.merged is False
    assert result.committed is False
    assert result.commit_hash == ""
    assert result.worktree_path == worktree_path
    assert result.has_changes is False
    assert result.has_uncommitted_changes is False
    assert "No changes found" in result.message
    assert captured_commands == [
        ["git", "-C", str(worktree_path), "status", "--porcelain"],
    ]


def test_sync_out_merge_returns_failed_when_git_commit_fails(
    monkeypatch,
    tmp_path,
) -> None:
    worktree_path = tmp_path / "worktree"
    worktree_path.mkdir()
    captured_commands: list[list[str]] = []

    def fake_run(command, capture_output, text, check):
        command_parts = [str(part) for part in command]
        captured_commands.append(command_parts)

        if command_parts[-2:] == ["status", "--porcelain"]:
            return SimpleNamespace(
                returncode=0,
                stdout=" M src/file.py\n",
                stderr="",
            )

        if command_parts[-2:] == ["add", "-A"]:
            return SimpleNamespace(
                returncode=0,
                stdout="",
                stderr="",
            )

        if command_parts[3:5] == ["commit", "-m"]:
            return SimpleNamespace(
                returncode=128,
                stdout="",
                stderr="fatal: unable to auto-detect email address",
            )

        return SimpleNamespace(
            returncode=1,
            stdout="",
            stderr=f"Unexpected command: {command_parts}",
        )

    monkeypatch.setattr(
        sync_out_module,
        "subprocess",
        SimpleNamespace(run=fake_run),
    )

    result = i_sync_out_merge(
        completed=True,
        worktree_path=worktree_path,
        issue_number=24,
        issue_title="Commit successful work",
    )

    assert result.failed is True
    assert result.merged is False
    assert result.committed is False
    assert result.commit_hash == ""
    assert result.worktree_path == worktree_path
    assert result.has_changes is True
    assert result.exit_code == 128
    assert "Commit failed" in result.message
    assert "unable to auto-detect email address" in result.message
    assert captured_commands == [
        ["git", "-C", str(worktree_path), "status", "--porcelain"],
        ["git", "-C", str(worktree_path), "add", "-A"],
        [
            "git",
            "-C",
            str(worktree_path),
            "commit",
            "-m",
            "RALPH: issue #24 - Commit successful work",
        ],
    ]


def test_sync_out_merge_reports_dirty_worktree_after_commit(
    monkeypatch,
    tmp_path,
) -> None:
    worktree_path = tmp_path / "worktree"
    worktree_path.mkdir()
    fake_hash = "dirty123abc"
    captured_commands: list[list[str]] = []

    def fake_run(command, capture_output, text, check):
        command_parts = [str(part) for part in command]
        captured_commands.append(command_parts)

        if command_parts[-2:] == ["status", "--porcelain"]:
            if len(captured_commands) == 1:
                return SimpleNamespace(
                    returncode=0,
                    stdout=" M src/file.py\n",
                    stderr="",
                )

            return SimpleNamespace(
                returncode=0,
                stdout=" M src/generated_after_commit.py\n",
                stderr="",
            )

        if command_parts[-2:] == ["add", "-A"]:
            return SimpleNamespace(
                returncode=0,
                stdout="",
                stderr="",
            )

        if command_parts[3:5] == ["commit", "-m"]:
            return SimpleNamespace(
                returncode=0,
                stdout="[branch dirty123] RALPH commit\n",
                stderr="",
            )

        if command_parts[-2:] == ["rev-parse", "HEAD"]:
            return SimpleNamespace(
                returncode=0,
                stdout=f"{fake_hash}\n",
                stderr="",
            )

        return SimpleNamespace(
            returncode=1,
            stdout="",
            stderr=f"Unexpected command: {command_parts}",
        )

    monkeypatch.setattr(
        sync_out_module,
        "subprocess",
        SimpleNamespace(run=fake_run),
    )

    result = i_sync_out_merge(
        completed=True,
        worktree_path=worktree_path,
        issue_number=24,
        issue_title="Commit successful work",
    )

    assert result.failed is False
    assert result.merged is True
    assert result.committed is True
    assert result.commit_hash == fake_hash
    assert result.worktree_path == worktree_path
    assert result.has_changes is True
    assert result.has_uncommitted_changes is True
    assert "src/generated_after_commit.py" in result.status_output
    assert "still has uncommitted changes" in result.message
    assert fake_hash in result.message

    assert captured_commands == [
        ["git", "-C", str(worktree_path), "status", "--porcelain"],
        ["git", "-C", str(worktree_path), "add", "-A"],
        [
            "git",
            "-C",
            str(worktree_path),
            "commit",
            "-m",
            "RALPH: issue #24 - Commit successful work",
        ],
        ["git", "-C", str(worktree_path), "rev-parse", "HEAD"],
        ["git", "-C", str(worktree_path), "status", "--porcelain"],
    ]
