# tests/main/test_main.py
import importlib

import ai_coder.ralph.ralph as ralph_module
from ai_coder.repository_context import RepositoryStartResult

from ai_coder.worktree_manager import WorktreeCleanupResult, WorktreeCreateResult
from ai_coder.setup_config import c_setup_config

from ai_coder.sync_out import SyncMergeResult
from ai_coder.test_runner import TestRunResult

main_module = importlib.import_module("ai_coder.main.main")

_MAIN_TEST_ENV_NAMES = (
    "TESTING_FLAG",
    "ISSUE_NUMBER",
    "ISSUE_TITLE",
    "ISSUE_BODY",
    "LABEL",
    "MAX_ITERATIONS",
    "PROMPT_PATH",
    "REPO_PATH",
    "RALPH_AGENT",
    "DRY_RUN",
    "RALPH_SANDBOX_MODE",
)


def _clear_main_test_env(monkeypatch) -> None:
    for env_name in _MAIN_TEST_ENV_NAMES:
        monkeypatch.delenv(env_name, raising=False)


def _refresh_main_config() -> None:
    c_setup_config._instance = None
    refreshed_config = c_setup_config.get_instance()

    main_module.setup_config = refreshed_config
    main_module.logger = refreshed_config.get_logger()

    ralph_module.setup_config = refreshed_config
    ralph_module.logger = refreshed_config.get_logger()


def _patch_clean_repository_context(monkeypatch, tmp_path) -> None:
    def fake_repository_start(repo_path):
        return RepositoryStartResult(
            repo_path=tmp_path,
            ready=True,
            message="Repository context discovered. Repository is clean.",
            active_branch="main",
            is_clean=True,
            status_output="",
            blocked_reason="",
        )

    monkeypatch.setattr(
        ralph_module,
        "i_repository_start",
        fake_repository_start,
    )


def _patch_successful_worktree_create(monkeypatch, tmp_path) -> None:
    def fake_worktree_create(
        repo_path,
        issue_number,
        issue_title,
        worktree_root=None,
    ):
        branch_name = f"ralph-issue-{issue_number}-test-worktree"
        worktree_path = tmp_path / "worktree"
        worktree_path.mkdir(parents=True, exist_ok=True)

        return WorktreeCreateResult(
            repo_path=tmp_path,
            worktree_path=worktree_path,
            branch_name=branch_name,
            command=(
                "git",
                "-C",
                str(tmp_path),
                "worktree",
                "add",
                "-b",
                branch_name,
                str(worktree_path),
            ),
            created=True,
            message="Created Git worktree: test worktree.",
        )

    monkeypatch.setattr(
        ralph_module,
        "i_worktree_create",
        fake_worktree_create,
    )


def _patch_successful_worktree_cleanup(monkeypatch, tmp_path) -> None:
    def fake_worktree_cleanup(
        repo_path,
        worktree_path,
        completed,
        has_uncommitted_changes=None,
    ):
        if completed:
            return WorktreeCleanupResult(
                worktree_path=worktree_path,
                removed=True,
                preserved=False,
                reason="removed_clean_worktree",
                message=f"Removed clean worktree: {worktree_path}",
            )

        return WorktreeCleanupResult(
            worktree_path=worktree_path,
            removed=False,
            preserved=True,
            reason="run_incomplete",
            message=f"Preserved worktree: {worktree_path}. RALPH did not complete.",
        )

    monkeypatch.setattr(
        ralph_module,
        "i_worktree_cleanup",
        fake_worktree_cleanup,
    )


def _patch_passing_test_runner(monkeypatch) -> None:
    def fake_test_runner_run(
        sandbox_handle=None,
        command=None,
    ):
        return TestRunResult(
            passed=True,
            command=command or ("poetry", "run", "pytest"),
            message="Tests passed through the sandbox seam.",
        )

    monkeypatch.setattr(
        ralph_module,
        "i_test_runner_run",
        fake_test_runner_run,
    )


def _patch_successful_sync_merge(monkeypatch) -> None:
    def fake_sync_out_merge(completed: bool):
        return SyncMergeResult(
            merged=completed,
            failed=False,
            message="Sync or commit succeeded.",
        )

    monkeypatch.setattr(
        ralph_module,
        "i_sync_out_merge",
        fake_sync_out_merge,
    )


def _prepare_main_cli_test_config(monkeypatch, tmp_path):
    _clear_main_test_env(monkeypatch)

    prompt_file = tmp_path / "prompt.md"
    prompt_file.write_text("prompt", encoding="utf-8")

    monkeypatch.setenv("TESTING_FLAG", "true")
    monkeypatch.setenv("REPO_PATH", str(tmp_path))
    monkeypatch.setenv("PROMPT_PATH", str(prompt_file))

    _refresh_main_config()

    return prompt_file


def test_main_runs_default_fake_issue(capsys, monkeypatch, tmp_path) -> None:
    _patch_clean_repository_context(monkeypatch, tmp_path)
    _patch_successful_worktree_create(monkeypatch, tmp_path)
    _patch_successful_worktree_cleanup(monkeypatch, tmp_path)
    _patch_passing_test_runner(monkeypatch)
    _patch_successful_sync_merge(monkeypatch)

    _clear_main_test_env(monkeypatch)
    monkeypatch.setenv("TESTING_FLAG", "true")
    _refresh_main_config()

    exit_code = main_module.main([])

    captured = capsys.readouterr()

    assert exit_code == 0
    assert "Selected issue #1: Minimal local RALPH loop" in captured.out
    assert "RALPH completed the selected issue." in captured.out


def test_main_accepts_custom_fake_issue(capsys, monkeypatch, tmp_path) -> None:
    _patch_clean_repository_context(monkeypatch, tmp_path)
    _patch_successful_worktree_create(monkeypatch, tmp_path)
    _patch_successful_worktree_cleanup(monkeypatch, tmp_path)
    _patch_passing_test_runner(monkeypatch)
    _patch_successful_sync_merge(monkeypatch)

    _clear_main_test_env(monkeypatch)
    monkeypatch.setenv("TESTING_FLAG", "true")
    _refresh_main_config()

    exit_code = main_module.main(
        [
            "--issue-number",
            "7",
            "--issue-title",
            "Fix prompt builder",
            "--issue-body",
            "Prompt builder should include the issue title.",
            "--label",
            "bug",
        ]
    )

    captured = capsys.readouterr()

    assert exit_code == 0
    assert "Selected issue #7: Fix prompt builder" in captured.out
    assert "RALPH completed the selected issue." in captured.out


def test_main_custom_issue_text_stays_inert(capsys, monkeypatch, tmp_path) -> None:
    _patch_clean_repository_context(monkeypatch, tmp_path)
    _patch_successful_worktree_create(monkeypatch, tmp_path)
    _patch_successful_worktree_cleanup(monkeypatch, tmp_path)
    _patch_passing_test_runner(monkeypatch)
    _patch_successful_sync_merge(monkeypatch)

    _clear_main_test_env(monkeypatch)
    monkeypatch.setenv("TESTING_FLAG", "true")
    _refresh_main_config()

    exit_code = main_module.main(
        [
            "--issue-number",
            "14",
            "--issue-title",
            "Fix !`echo title`",
            "--issue-body",
            "Body !`echo unsafe` {{ISSUE_TITLE}}",
            "--label",
            "bug",
        ]
    )

    captured = capsys.readouterr()

    assert exit_code == 0
    assert "Selected issue #14: Fix !`echo title`" in captured.out
    assert "Body !`echo unsafe` {{ISSUE_TITLE}}" in captured.out
    assert "RALPH completed the selected issue." in captured.out


def test_main_rejects_invalid_max_iterations(capsys, monkeypatch) -> None:
    _clear_main_test_env(monkeypatch)
    monkeypatch.setenv("TESTING_FLAG", "true")
    _refresh_main_config()

    exit_code = main_module.main(["--max-iterations", "0"])

    captured = capsys.readouterr()

    assert exit_code == 1
    assert "Error: --max-iterations must be at least 1." in captured.out


def test_main_rejects_empty_label(capsys, monkeypatch) -> None:
    _clear_main_test_env(monkeypatch)
    monkeypatch.setenv("TESTING_FLAG", "true")
    _refresh_main_config()

    exit_code = main_module.main(
        [
            "--issue-number",
            "1",
            "--issue-title",
            "A",
            "--issue-body",
            "B",
            "--label",
            "   ",
        ]
    )

    captured = capsys.readouterr()

    assert exit_code == 1
    assert "Error: --label cannot be empty." in captured.out


def test_main_valid_cli_overrides_update_setup_config(
    capsys,
    monkeypatch,
    tmp_path,
) -> None:
    _patch_clean_repository_context(monkeypatch, tmp_path)
    prompt_file = _prepare_main_cli_test_config(monkeypatch, tmp_path)
    _patch_successful_worktree_create(monkeypatch, tmp_path)
    _patch_successful_worktree_cleanup(monkeypatch, tmp_path)
    _patch_passing_test_runner(monkeypatch)
    _patch_successful_sync_merge(monkeypatch)

    exit_code = main_module.main(
        [
            "--issue-number",
            "8",
            "--issue-title",
            "Use CLI overrides",
            "--issue-body",
            "CLI values should update setup_config after validation.",
            "--label",
            "bug",
            "--max-iterations",
            "2",
            "--prompt-path",
            str(prompt_file),
            "--repo-path",
            str(tmp_path),
            "--agent",
            "mock",
            "--sandbox",
            "local",
            "--no-dry-run",
        ]
    )

    captured = capsys.readouterr()

    assert exit_code == 0
    assert "Selected issue #8: Use CLI overrides" in captured.out
    assert main_module.setup_config.issue_number == 8
    assert main_module.setup_config.issue_title == "Use CLI overrides"
    assert main_module.setup_config.issue_body == (
        "CLI values should update setup_config after validation."
    )
    assert main_module.setup_config.label == "bug"
    assert main_module.setup_config.max_iterations == 2
    assert main_module.setup_config.prompt_path == prompt_file
    assert main_module.setup_config.repo_path == tmp_path
    assert main_module.setup_config.default_agent == "mock"
    assert main_module.setup_config.sandbox_mode == "local"
    assert main_module.setup_config.dry_run is False


def test_main_rejects_codex_agent_until_codex_runtime_exists(
    capsys,
    monkeypatch,
) -> None:
    _clear_main_test_env(monkeypatch)
    monkeypatch.setenv("TESTING_FLAG", "true")
    _refresh_main_config()

    exit_code = main_module.main(["--agent", "codex"])

    captured = capsys.readouterr()

    assert exit_code == 1
    assert "Error: --agent must be 'mock' for Release 1." in captured.out


def test_main_invalid_max_iterations_leaves_setup_config_unchanged(
    capsys,
    monkeypatch,
    tmp_path,
) -> None:
    _prepare_main_cli_test_config(monkeypatch, tmp_path)
    original_config = main_module.setup_config.to_dict()

    exit_code = main_module.main(["--max-iterations", "0"])

    captured = capsys.readouterr()

    assert exit_code == 1
    assert "Error: --max-iterations must be at least 1." in captured.out
    assert main_module.setup_config.to_dict() == original_config


def test_main_invalid_prompt_path_leaves_setup_config_unchanged(
    capsys,
    monkeypatch,
    tmp_path,
) -> None:
    _prepare_main_cli_test_config(monkeypatch, tmp_path)
    missing_prompt_file = tmp_path / "missing_prompt.md"
    original_config = main_module.setup_config.to_dict()

    exit_code = main_module.main(["--prompt-path", str(missing_prompt_file)])

    captured = capsys.readouterr()

    assert exit_code == 1
    assert "Error: --prompt-path does not exist:" in captured.out
    assert main_module.setup_config.to_dict() == original_config


def test_main_invalid_repo_path_leaves_setup_config_unchanged(
    capsys,
    monkeypatch,
    tmp_path,
) -> None:
    _prepare_main_cli_test_config(monkeypatch, tmp_path)
    missing_repo_path = tmp_path / "missing_repo"
    original_config = main_module.setup_config.to_dict()

    exit_code = main_module.main(["--repo-path", str(missing_repo_path)])

    captured = capsys.readouterr()

    assert exit_code == 1
    assert "Error: --repo-path does not exist:" in captured.out
    assert main_module.setup_config.to_dict() == original_config


def test_main_cli_repo_path_override_can_fix_bad_env_repo_path(
    capsys,
    monkeypatch,
    tmp_path,
) -> None:
    _patch_clean_repository_context(monkeypatch, tmp_path)
    _patch_successful_worktree_create(monkeypatch, tmp_path)
    _patch_successful_worktree_cleanup(monkeypatch, tmp_path)
    _patch_passing_test_runner(monkeypatch)
    _patch_successful_sync_merge(monkeypatch)

    _clear_main_test_env(monkeypatch)

    prompt_file = tmp_path / "prompt.md"
    prompt_file.write_text("prompt", encoding="utf-8")
    missing_repo_path = tmp_path / "missing_repo"

    monkeypatch.setenv("TESTING_FLAG", "true")
    monkeypatch.setenv("REPO_PATH", str(missing_repo_path))
    monkeypatch.setenv("PROMPT_PATH", str(prompt_file))
    _refresh_main_config()

    exit_code = main_module.main(
        [
            "--repo-path",
            str(tmp_path),
            "--prompt-path",
            str(prompt_file),
        ]
    )

    captured = capsys.readouterr()

    assert exit_code == 0
    assert "Selected issue #1: Minimal local RALPH loop" in captured.out
    assert main_module.setup_config.repo_path == tmp_path
