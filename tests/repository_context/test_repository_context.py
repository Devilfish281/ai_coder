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
    assert str(repo_root) in result.message
    assert "main" in result.message
    assert "RALPH stopped before worktree creation" in result.message
    assert "Git status output:" in result.message
    assert "Commit, stash, or discard" in result.message
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
    assert str(repo_root) in result.message
    assert "main" in result.message
    assert "RALPH could not safely verify the repository clean state" in result.message
    assert "Git error output:" in result.message
    assert "Run git status manually" in result.message
    assert result.blocked_reason == "clean_state_detection_failed"


def test_repository_context_discovery_prefers_configured_test_command(
    monkeypatch,
    tmp_path,
) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    (repo_root / "pyproject.toml").write_text(
        "[tool.pytest.ini_options]\n", encoding="utf-8"
    )
    (repo_root / "poetry.lock").write_text("", encoding="utf-8")
    (repo_root / "README.md").write_text("# Test Repo\n", encoding="utf-8")
    (repo_root / "src").mkdir()
    (repo_root / "tests").mkdir()
    (repo_root / ".env").write_text("SECRET_VALUE=do-not-read\n", encoding="utf-8")

    monkeypatch.setattr(
        repository_context_module.setup_config,
        "test_command",
        "custom test command",
    )

    result = repository_context_module.i_repository_context_discover(repo_root)

    assert result.repo_path == repo_root
    assert result.package_manager == "poetry"
    assert result.test_command == "custom test command"
    assert result.test_command_source == "configured"
    assert "pyproject.toml" in result.project_files
    assert "poetry.lock" in result.project_files
    assert "src/" in result.project_files
    assert "tests/" in result.project_files
    assert "Uses Poetry" in result.useful_signals
    assert "Uses pytest" in result.useful_signals
    assert "custom test command" in result.prompt_summary
    assert ".env" not in result.prompt_summary


def test_repository_context_discovery_infers_poetry_pytest_command(
    monkeypatch,
    tmp_path,
) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    (repo_root / "pyproject.toml").write_text(
        "[tool.pytest.ini_options]\n", encoding="utf-8"
    )
    (repo_root / "poetry.lock").write_text("", encoding="utf-8")
    (repo_root / "tests").mkdir()

    monkeypatch.setattr(
        repository_context_module.setup_config,
        "test_command",
        "",
    )

    result = repository_context_module.i_repository_context_discover(repo_root)

    assert result.package_manager == "poetry"
    assert result.test_command == "poetry run pytest"
    assert result.test_command_source == "inferred_from_poetry"
    assert "Uses Poetry" in result.useful_signals
    assert "Uses pytest" in result.useful_signals
    assert "poetry run pytest" in result.prompt_summary


def test_repository_context_discovery_infers_pytest_from_tests_directory(
    monkeypatch,
    tmp_path,
) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    (repo_root / "pyproject.toml").write_text("", encoding="utf-8")
    (repo_root / "tests").mkdir()

    monkeypatch.setattr(
        repository_context_module.setup_config,
        "test_command",
        "",
    )

    result = repository_context_module.i_repository_context_discover(repo_root)

    assert result.package_manager == "python"
    assert result.test_command == "pytest"
    assert result.test_command_source == "inferred_from_tests_dir"
    assert "Python project" in result.useful_signals
    assert "Uses pytest" in result.useful_signals


def test_repository_context_discovery_keeps_prompt_summary_safe(
    monkeypatch,
    tmp_path,
) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    (repo_root / "pyproject.toml").write_text("", encoding="utf-8")
    (repo_root / "tests").mkdir()
    (repo_root / ".env").write_text("OPENAI_API_KEY=secret\n", encoding="utf-8")
    (repo_root / ".git").mkdir()
    (repo_root / ".venv").mkdir()
    (repo_root / "node_modules").mkdir()
    (repo_root / ".pytest_cache").mkdir()
    logs_dir = repo_root / "var" / "logs"
    logs_dir.mkdir(parents=True)
    (logs_dir / "reportlog.log").write_text("log text\n", encoding="utf-8")

    monkeypatch.setattr(
        repository_context_module.setup_config,
        "test_command",
        "",
    )

    result = repository_context_module.i_repository_context_discover(repo_root)

    assert "Repository context:" in result.prompt_summary
    assert "pyproject.toml" in result.prompt_summary
    assert "tests/" in result.prompt_summary
    assert ".env" not in result.prompt_summary
    assert ".git" not in result.prompt_summary
    assert ".venv" not in result.prompt_summary
    assert "node_modules" not in result.prompt_summary
    assert ".pytest_cache" not in result.prompt_summary
    assert "reportlog.log" not in result.prompt_summary


def test_repository_context_discovery_excludes_common_unsafe_directories(
    monkeypatch,
    tmp_path,
) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()

    (repo_root / "pyproject.toml").write_text("", encoding="utf-8")
    (repo_root / "poetry.lock").write_text("", encoding="utf-8")
    (repo_root / "src").mkdir()
    (repo_root / "tests").mkdir()

    for directory_name in (
        ".git",
        ".venv",
        "venv",
        "__pycache__",
        ".pytest_cache",
        ".mypy_cache",
        ".ruff_cache",
        "node_modules",
        "dist",
        "build",
    ):
        (repo_root / directory_name).mkdir()

    monkeypatch.setattr(
        repository_context_module.setup_config,
        "test_command",
        "",
    )

    result = repository_context_module.i_repository_context_discover(repo_root)

    assert "pyproject.toml" in result.prompt_summary
    assert "poetry.lock" in result.prompt_summary
    assert "src/" in result.prompt_summary
    assert "tests/" in result.prompt_summary

    assert ".git" not in result.prompt_summary
    assert ".venv" not in result.prompt_summary
    assert "venv" not in result.project_files
    assert "__pycache__" not in result.prompt_summary
    assert ".pytest_cache" not in result.prompt_summary
    assert ".mypy_cache" not in result.prompt_summary
    assert ".ruff_cache" not in result.prompt_summary
    assert "node_modules" not in result.prompt_summary
    assert "dist" not in result.project_files
    assert "build" not in result.project_files


def test_repository_context_discovery_excludes_secret_environment_files(
    monkeypatch,
    tmp_path,
) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()

    (repo_root / "pyproject.toml").write_text("", encoding="utf-8")
    (repo_root / "tests").mkdir()
    (repo_root / ".env").write_text("OPENAI_API_KEY=secret\n", encoding="utf-8")
    (repo_root / ".env.local").write_text("LOCAL_SECRET=secret\n", encoding="utf-8")
    (repo_root / ".env.production").write_text("PROD_SECRET=secret\n", encoding="utf-8")
    (repo_root / ".env.example").write_text("EXAMPLE_SECRET=secret\n", encoding="utf-8")

    monkeypatch.setattr(
        repository_context_module.setup_config,
        "test_command",
        "",
    )

    result = repository_context_module.i_repository_context_discover(repo_root)

    assert "pyproject.toml" in result.project_files
    assert "tests/" in result.project_files
    assert ".env" not in result.prompt_summary
    assert ".env.local" not in result.prompt_summary
    assert ".env.production" not in result.prompt_summary
    assert ".env.example" not in result.prompt_summary
    assert ".env" not in result.project_files
    assert ".env.local" not in result.project_files
    assert ".env.production" not in result.project_files
    assert ".env.example" not in result.project_files


def test_repository_context_discovery_excludes_generated_logs_and_reports(
    monkeypatch,
    tmp_path,
) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()

    (repo_root / "pyproject.toml").write_text("", encoding="utf-8")
    (repo_root / "tests").mkdir()

    logs_dir = repo_root / "logs"
    logs_dir.mkdir()
    (logs_dir / "reportlog.log").write_text("log text\n", encoding="utf-8")

    var_logs_dir = repo_root / "var" / "logs"
    var_logs_dir.mkdir(parents=True)
    (var_logs_dir / "reportlog.log").write_text("log text\n", encoding="utf-8")

    reports_dir = repo_root / "reports"
    reports_dir.mkdir()
    (reports_dir / "summary.md").write_text("# Generated report\n", encoding="utf-8")

    var_reports_dir = repo_root / "var" / "reports"
    var_reports_dir.mkdir(parents=True)
    (var_reports_dir / "summary.md").write_text(
        "# Generated report\n", encoding="utf-8"
    )

    monkeypatch.setattr(
        repository_context_module.setup_config,
        "test_command",
        "",
    )

    result = repository_context_module.i_repository_context_discover(repo_root)

    assert "pyproject.toml" in result.prompt_summary
    assert "tests/" in result.prompt_summary
    assert "reportlog.log" not in result.prompt_summary
    assert "logs/" not in result.project_files
    assert "var/logs" not in result.prompt_summary
    assert "reports/" not in result.project_files
    assert "var/reports" not in result.prompt_summary
    assert "summary.md" not in result.prompt_summary


def test_repository_context_discovery_excludes_large_binary_like_files(
    monkeypatch,
    tmp_path,
) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()

    (repo_root / "pyproject.toml").write_text("", encoding="utf-8")
    (repo_root / "tests").mkdir()

    for file_name in (
        "diagram.png",
        "photo.jpg",
        "manual.pdf",
        "archive.zip",
        "program.exe",
        "library.dll",
        "module.pyc",
    ):
        (repo_root / file_name).write_bytes(b"binary-like test data")

    monkeypatch.setattr(
        repository_context_module.setup_config,
        "test_command",
        "",
    )

    result = repository_context_module.i_repository_context_discover(repo_root)

    assert "pyproject.toml" in result.prompt_summary
    assert "tests/" in result.prompt_summary
    assert "diagram.png" not in result.prompt_summary
    assert "photo.jpg" not in result.prompt_summary
    assert "manual.pdf" not in result.prompt_summary
    assert "archive.zip" not in result.prompt_summary
    assert "program.exe" not in result.prompt_summary
    assert "library.dll" not in result.prompt_summary
    assert "module.pyc" not in result.prompt_summary


def test_repository_context_discovery_keeps_safe_project_markers(
    monkeypatch,
    tmp_path,
) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()

    (repo_root / "pyproject.toml").write_text(
        "[tool.pytest.ini_options]\n", encoding="utf-8"
    )
    (repo_root / "poetry.lock").write_text("", encoding="utf-8")
    (repo_root / "README.md").write_text("# Safe Project\n", encoding="utf-8")
    (repo_root / "src").mkdir()
    (repo_root / "tests").mkdir()

    monkeypatch.setattr(
        repository_context_module.setup_config,
        "test_command",
        "",
    )

    result = repository_context_module.i_repository_context_discover(repo_root)

    assert result.package_manager == "poetry"
    assert result.test_command == "poetry run pytest"
    assert result.test_command_source == "inferred_from_poetry"
    assert "pyproject.toml" in result.project_files
    assert "poetry.lock" in result.project_files
    assert "README.md" in result.project_files
    assert "src/" in result.project_files
    assert "tests/" in result.project_files
    assert "Python project" in result.useful_signals
    assert "Uses Poetry" in result.useful_signals
    assert "Uses pytest" in result.useful_signals
    assert "poetry run pytest" in result.prompt_summary


def test_repository_context_exclusion_policy_is_easy_to_extend() -> None:
    assert isinstance(repository_context_module.EXCLUDED_DIRECTORY_NAMES, tuple)
    assert isinstance(repository_context_module.EXCLUDED_FILE_NAMES, tuple)
    assert isinstance(repository_context_module.EXCLUDED_FILE_PATTERNS, tuple)
    assert isinstance(repository_context_module.GENERATED_DIRECTORY_PATHS, tuple)
    assert isinstance(repository_context_module.GENERATED_FILE_SUFFIXES, tuple)
    assert isinstance(repository_context_module.LARGE_BINARY_FILE_SUFFIXES, tuple)

    assert ".git" in repository_context_module.EXCLUDED_DIRECTORY_NAMES
    assert ".env" in repository_context_module.EXCLUDED_FILE_NAMES
    assert ".env.*" in repository_context_module.EXCLUDED_FILE_PATTERNS
    assert "var/logs" in repository_context_module.GENERATED_DIRECTORY_PATHS
    assert ".log" in repository_context_module.GENERATED_FILE_SUFFIXES
    assert ".pdf" in repository_context_module.LARGE_BINARY_FILE_SUFFIXES


def test_repository_context_project_file_collection_applies_exclusion_policy(
    monkeypatch,
    tmp_path,
) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()

    (repo_root / "pyproject.toml").write_text("", encoding="utf-8")
    (repo_root / "poetry.lock").write_text("", encoding="utf-8")
    (repo_root / "README.md").write_text("# Safe Project\n", encoding="utf-8")
    (repo_root / ".env").write_text("OPENAI_API_KEY=secret\n", encoding="utf-8")
    (repo_root / ".env.local").write_text("LOCAL_SECRET=secret\n", encoding="utf-8")
    (repo_root / "manual.pdf").write_bytes(b"binary-like test data")

    (repo_root / "src").mkdir()
    (repo_root / "tests").mkdir()
    (repo_root / ".git").mkdir()
    (repo_root / ".venv").mkdir()
    (repo_root / "node_modules").mkdir()
    (repo_root / "logs").mkdir()
    (repo_root / "reports").mkdir()

    monkeypatch.setattr(
        repository_context_module,
        "SAFE_PROJECT_FILE_NAMES",
        (
            "pyproject.toml",
            "poetry.lock",
            "README.md",
            ".env",
            ".env.local",
            "manual.pdf",
        ),
    )
    monkeypatch.setattr(
        repository_context_module,
        "SAFE_PROJECT_DIRECTORY_NAMES",
        (
            "src",
            "tests",
            ".git",
            ".venv",
            "node_modules",
            "logs",
            "reports",
        ),
    )
    monkeypatch.setattr(
        repository_context_module.setup_config,
        "test_command",
        "",
    )

    result = repository_context_module.i_repository_context_discover(repo_root)

    assert result.project_files == (
        "pyproject.toml",
        "poetry.lock",
        "README.md",
        "src/",
        "tests/",
    )
    assert ".env" not in result.project_files
    assert ".env.local" not in result.project_files
    assert "manual.pdf" not in result.project_files
    assert ".git/" not in result.project_files
    assert ".venv/" not in result.project_files
    assert "node_modules/" not in result.project_files
    assert "logs/" not in result.project_files
    assert "reports/" not in result.project_files


def test_repository_context_discovery_does_not_add_broad_root_listing_yet(
    monkeypatch,
    tmp_path,
) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()

    (repo_root / "pyproject.toml").write_text("", encoding="utf-8")
    (repo_root / "poetry.lock").write_text("", encoding="utf-8")
    (repo_root / "README.md").write_text("# Safe Project\n", encoding="utf-8")
    (repo_root / "src").mkdir()
    (repo_root / "tests").mkdir()

    (repo_root / "LICENSE").write_text("MIT\n", encoding="utf-8")
    (repo_root / "CONTRIBUTING.md").write_text("# Contributing\n", encoding="utf-8")
    (repo_root / "docs").mkdir()
    (repo_root / "scripts").mkdir()

    monkeypatch.setattr(
        repository_context_module.setup_config,
        "test_command",
        "",
    )

    result = repository_context_module.i_repository_context_discover(repo_root)

    assert result.project_files == (
        "pyproject.toml",
        "poetry.lock",
        "README.md",
        "src/",
        "tests/",
    )
    assert "LICENSE" not in result.project_files
    assert "CONTRIBUTING.md" not in result.project_files
    assert "docs/" not in result.project_files
    assert "scripts/" not in result.project_files
    assert "LICENSE" not in result.prompt_summary
    assert "CONTRIBUTING.md" not in result.prompt_summary
    assert "docs/" not in result.prompt_summary
    assert "scripts/" not in result.prompt_summary


def test_repository_context_discovery_returns_unknown_context_for_missing_path(
    monkeypatch,
    tmp_path,
) -> None:
    missing_repo_path = tmp_path / "missing-repo"

    monkeypatch.setattr(
        repository_context_module.setup_config,
        "test_command",
        "",
    )

    result = repository_context_module.i_repository_context_discover(missing_repo_path)

    assert result.repo_path == missing_repo_path
    assert result.package_manager == "unknown"
    assert result.test_command == ""
    assert result.test_command_source == "unknown"
    assert result.project_files == ()
    assert result.useful_signals == ("Repository context unavailable",)
    assert "Repository context unavailable" in result.prompt_summary


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
