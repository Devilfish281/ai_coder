from pathlib import Path

from ai_coder.setup_config import c_setup_config


def test_setup_config_uses_issue_dir_and_file_name_first(monkeypatch, tmp_path) -> None:
    issue_dir = tmp_path / "issues"
    issue_file_name = "local_issue.md"
    fallback_path = tmp_path / "fallback" / "fallback_issue.md"

    monkeypatch.setenv("GITHUB_ISSUE_DIR", str(issue_dir))
    monkeypatch.setenv("GITHUB_ISSUE_FILE_NAME", issue_file_name)
    monkeypatch.setenv("GITHUB_ISSUE_PATH", str(fallback_path))

    result = c_setup_config.resolve_github_issue_path()

    assert result == issue_dir / issue_file_name


def test_setup_config_uses_issue_dir_with_path_file_name(monkeypatch, tmp_path) -> None:
    issue_dir = tmp_path / "issues"
    fallback_path = tmp_path / "fallback" / "fallback_issue.md"

    monkeypatch.setenv("GITHUB_ISSUE_DIR", str(issue_dir))
    monkeypatch.delenv("GITHUB_ISSUE_FILE_NAME", raising=False)
    monkeypatch.setenv("GITHUB_ISSUE_PATH", str(fallback_path))

    result = c_setup_config.resolve_github_issue_path()

    assert result == issue_dir / "fallback_issue.md"


def test_setup_config_uses_issue_file_name_with_path_dir(monkeypatch, tmp_path) -> None:
    fallback_path = tmp_path / "fallback" / "fallback_issue.md"

    monkeypatch.delenv("GITHUB_ISSUE_DIR", raising=False)
    monkeypatch.setenv("GITHUB_ISSUE_FILE_NAME", "local_issue.md")
    monkeypatch.setenv("GITHUB_ISSUE_PATH", str(fallback_path))

    result = c_setup_config.resolve_github_issue_path()

    assert result == tmp_path / "fallback" / "local_issue.md"


def test_setup_config_uses_github_issue_path_when_no_dir_or_file_name(
    monkeypatch, tmp_path
) -> None:
    fallback_path = tmp_path / "fallback" / "fallback_issue.md"

    monkeypatch.delenv("GITHUB_ISSUE_DIR", raising=False)
    monkeypatch.delenv("GITHUB_ISSUE_FILE_NAME", raising=False)
    monkeypatch.setenv("GITHUB_ISSUE_PATH", str(fallback_path))

    result = c_setup_config.resolve_github_issue_path()

    assert result == fallback_path


def test_setup_config_exposes_release_1_runtime_fields(monkeypatch, tmp_path) -> None:
    prompt_file = tmp_path / "prompt.md"
    prompt_file.write_text("prompt", encoding="utf-8")

    monkeypatch.setenv("PROJECT_NAME", "AI Code")
    monkeypatch.setenv("REPO_PATH", str(tmp_path))
    monkeypatch.setenv("GITHUB_REPO", "Devilfish281/ai_coder")
    monkeypatch.setenv("RALPH_AGENT", "mock")
    monkeypatch.setenv("DRY_RUN", "true")
    monkeypatch.setenv("TEST_COMMAND", "poetry run pytest")
    monkeypatch.setenv(
        "COMMIT_MESSAGE_TEMPLATE",
        "RALPH: issue #{issue_number} - {issue_title}",
    )
    monkeypatch.setenv("MAX_ITERATIONS", "3")
    monkeypatch.setenv("PROMPT_PATH", str(prompt_file))
    monkeypatch.setenv("RALPH_SANDBOX_MODE", "local")

    c_setup_config._instance = None
    config = c_setup_config.get_instance()

    result = config.to_dict()

    assert result["project_name"] == "AI Code"
    assert result["repo_path"] == str(tmp_path)
    assert result["github_repo"] == "Devilfish281/ai_coder"
    assert result["default_agent"] == "mock"
    assert result["dry_run"] is True
    assert result["test_command"] == "poetry run pytest"
    assert result["commit_message_template"] == (
        "RALPH: issue #{issue_number} - {issue_title}"
    )
    assert result["max_iterations"] == 3
    assert result["prompt_path"] == str(prompt_file)
    assert result["sandbox_mode"] == "local"


import pytest


def test_setup_config_rejects_invalid_max_iterations(monkeypatch, tmp_path) -> None:
    prompt_file = tmp_path / "prompt.md"
    prompt_file.write_text("prompt", encoding="utf-8")

    monkeypatch.setenv("REPO_PATH", str(tmp_path))
    monkeypatch.setenv("PROMPT_PATH", str(prompt_file))
    monkeypatch.setenv("MAX_ITERATIONS", "0")

    c_setup_config._instance = None
    config = c_setup_config.get_instance()

    with pytest.raises(ValueError, match="MAX_ITERATIONS must be at least 1"):
        config.validate_initialization()


def test_setup_config_rejects_unsupported_agent(monkeypatch, tmp_path) -> None:
    prompt_file = tmp_path / "prompt.md"
    prompt_file.write_text("prompt", encoding="utf-8")

    monkeypatch.setenv("REPO_PATH", str(tmp_path))
    monkeypatch.setenv("PROMPT_PATH", str(prompt_file))
    monkeypatch.setenv("RALPH_AGENT", "codex")

    c_setup_config._instance = None
    config = c_setup_config.get_instance()

    with pytest.raises(ValueError, match="RALPH_AGENT must be 'mock'"):
        config.validate_initialization()


def test_setup_config_rejects_unsupported_sandbox_mode(monkeypatch, tmp_path) -> None:
    prompt_file = tmp_path / "prompt.md"
    prompt_file.write_text("prompt", encoding="utf-8")

    monkeypatch.setenv("REPO_PATH", str(tmp_path))
    monkeypatch.setenv("PROMPT_PATH", str(prompt_file))
    monkeypatch.setenv("RALPH_SANDBOX_MODE", "cloud")

    c_setup_config._instance = None
    config = c_setup_config.get_instance()

    with pytest.raises(
        ValueError, match="RALPH_SANDBOX_MODE must be 'local' or 'docker'"
    ):
        config.validate_initialization()
