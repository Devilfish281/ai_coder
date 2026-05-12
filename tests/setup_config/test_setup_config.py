from pathlib import Path

import pytest

from ai_coder.setup_config import (
    DEFAULT_AGENT_NAME,
    DEFAULT_COMMIT_MESSAGE_TEMPLATE,
    DEFAULT_GITHUB_REPO,
    DEFAULT_PROJECT_NAME,
    DEFAULT_TEST_COMMAND,
    c_setup_config,
)

_RUNTIME_ENV_NAMES = (  #  Added Code
    "PROJECT_NAME",  #  Added Code
    "REPO_PATH",  #  Added Code
    "GITHUB_REPO",  #  Added Code
    "RALPH_AGENT",  #  Added Code
    "DRY_RUN",  #  Added Code
    "TEST_COMMAND",  #  Added Code
    "COMMIT_MESSAGE_TEMPLATE",  #  Added Code
    "ISSUE_NUMBER",  #  Added Code
    "ISSUE_TITLE",  #  Added Code
    "ISSUE_BODY",  #  Added Code
    "GITHUB_ISSUE_PATH",  #  Added Code
    "GITHUB_ISSUE_DIR",  #  Added Code
    "GITHUB_ISSUE_FILE_NAME",  #  Added Code
    "LABEL",  #  Added Code
    "MAX_ITERATIONS",  #  Added Code
    "PROMPT_PATH",  #  Added Code
    "RALPH_SANDBOX_MODE",  #  Added Code
    "OPENAI_MODEL",  #  Added Code
)  #  Added Code


def _clear_runtime_env(monkeypatch) -> None:  #  Added Code
    for env_name in _RUNTIME_ENV_NAMES:  #  Added Code
        monkeypatch.delenv(env_name, raising=False)  #  Added Code


def _prepare_valid_paths(monkeypatch, tmp_path: Path) -> Path:  #  Added Code
    prompt_file = tmp_path / "prompt.md"  #  Added Code
    prompt_file.write_text("prompt", encoding="utf-8")  #  Added Code

    monkeypatch.setenv("REPO_PATH", str(tmp_path))  #  Added Code
    monkeypatch.setenv("PROMPT_PATH", str(prompt_file))  #  Added Code

    return prompt_file  #  Added Code


def _fresh_config():  #  Added Code
    c_setup_config._instance = None  #  Added Code
    return c_setup_config.get_instance()  #  Added Code


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
    _clear_runtime_env(monkeypatch)  #  Added Code
    prompt_file = _prepare_valid_paths(monkeypatch, tmp_path)  #  Changed Code

    monkeypatch.setenv("PROJECT_NAME", "AI Code")
    monkeypatch.setenv("GITHUB_REPO", "Devilfish281/ai_coder")
    monkeypatch.setenv("RALPH_AGENT", "mock")
    monkeypatch.setenv("DRY_RUN", "true")
    monkeypatch.setenv("TEST_COMMAND", "poetry run pytest")
    monkeypatch.setenv(
        "COMMIT_MESSAGE_TEMPLATE",
        "RALPH: issue #{issue_number} - {issue_title}",
    )
    monkeypatch.setenv("MAX_ITERATIONS", "3")
    monkeypatch.setenv("RALPH_SANDBOX_MODE", "local")

    config = _fresh_config()  #  Changed Code

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


def test_setup_config_loads_safe_defaults_when_env_values_are_missing(
    monkeypatch,
    tmp_path,
) -> None:
    _clear_runtime_env(monkeypatch)  #  Added Code
    prompt_file = _prepare_valid_paths(monkeypatch, tmp_path)  #  Added Code

    config = _fresh_config()  #  Added Code

    assert config.project_name == DEFAULT_PROJECT_NAME  #  Added Code
    assert config.repo_path == tmp_path  #  Added Code
    assert config.github_repo == DEFAULT_GITHUB_REPO  #  Added Code
    assert config.default_agent == DEFAULT_AGENT_NAME  #  Added Code
    assert config.dry_run is True  #  Added Code
    assert config.test_command == DEFAULT_TEST_COMMAND  #  Added Code
    assert (
        config.commit_message_template == DEFAULT_COMMIT_MESSAGE_TEMPLATE
    )  #  Added Code
    assert config.max_iterations == 3  #  Added Code
    assert config.prompt_path == prompt_file  #  Added Code
    assert config.sandbox_mode == "local"  #  Added Code


def test_setup_config_env_values_override_defaults(monkeypatch, tmp_path) -> None:
    _clear_runtime_env(monkeypatch)  #  Added Code
    prompt_file = _prepare_valid_paths(monkeypatch, tmp_path)  #  Added Code

    monkeypatch.setenv("PROJECT_NAME", "Custom AI Code")  #  Added Code
    monkeypatch.setenv("GITHUB_REPO", "Devilfish281/custom_ai_coder")  #  Added Code
    monkeypatch.setenv("RALPH_AGENT", "mock")  #  Added Code
    monkeypatch.setenv("DRY_RUN", "false")  #  Added Code
    monkeypatch.setenv("TEST_COMMAND", "pytest")  #  Added Code
    monkeypatch.setenv(  #  Added Code
        "COMMIT_MESSAGE_TEMPLATE",  #  Added Code
        "RALPH: custom issue #{issue_number}",  #  Added Code
    )  #  Added Code
    monkeypatch.setenv("MAX_ITERATIONS", "5")  #  Added Code
    monkeypatch.setenv("RALPH_SANDBOX_MODE", "local")  #  Added Code

    config = _fresh_config()  #  Added Code

    assert config.project_name == "Custom AI Code"  #  Added Code
    assert config.repo_path == tmp_path  #  Added Code
    assert config.github_repo == "Devilfish281/custom_ai_coder"  #  Added Code
    assert config.default_agent == "mock"  #  Added Code
    assert config.dry_run is False  #  Added Code
    assert config.test_command == "pytest"  #  Added Code
    assert (
        config.commit_message_template == "RALPH: custom issue #{issue_number}"
    )  #  Added Code
    assert config.max_iterations == 5  #  Added Code
    assert config.prompt_path == prompt_file  #  Added Code
    assert config.sandbox_mode == "local"  #  Added Code


def test_setup_config_validate_initialization_accepts_valid_loaded_values(
    monkeypatch,
    tmp_path,
) -> None:
    _clear_runtime_env(monkeypatch)  #  Added Code
    _prepare_valid_paths(monkeypatch, tmp_path)  #  Added Code

    monkeypatch.setenv("PROJECT_NAME", "AI Code")  #  Added Code
    monkeypatch.setenv("GITHUB_REPO", "Devilfish281/ai_coder")  #  Added Code
    monkeypatch.setenv("RALPH_AGENT", "mock")  #  Added Code
    monkeypatch.setenv("TEST_COMMAND", "poetry run pytest")  #  Added Code
    monkeypatch.setenv(  #  Added Code
        "COMMIT_MESSAGE_TEMPLATE",  #  Added Code
        "RALPH: issue #{issue_number} - {issue_title}",  #  Added Code
    )  #  Added Code
    monkeypatch.setenv("MAX_ITERATIONS", "3")  #  Added Code
    monkeypatch.setenv("RALPH_SANDBOX_MODE", "local")  #  Added Code

    config = _fresh_config()  #  Added Code

    config.validate_initialization()  #  Added Code


def test_setup_config_missing_optional_values_use_safe_defaults(
    monkeypatch,
    tmp_path,
) -> None:
    _clear_runtime_env(monkeypatch)  #  Added Code
    _prepare_valid_paths(monkeypatch, tmp_path)  #  Added Code

    config = _fresh_config()  #  Added Code
    result = config.to_dict()  #  Added Code

    assert result["project_name"] == DEFAULT_PROJECT_NAME  #  Added Code
    assert result["github_repo"] == DEFAULT_GITHUB_REPO  #  Added Code
    assert result["default_agent"] == DEFAULT_AGENT_NAME  #  Added Code
    assert result["dry_run"] is True  #  Added Code
    assert result["test_command"] == DEFAULT_TEST_COMMAND  #  Added Code
    assert (
        result["commit_message_template"] == DEFAULT_COMMIT_MESSAGE_TEMPLATE
    )  #  Added Code
    assert result["max_iterations"] == 3  #  Added Code
    assert result["sandbox_mode"] == "local"  #  Added Code


def test_setup_config_invalid_env_int_has_clear_error(monkeypatch, tmp_path) -> None:
    _clear_runtime_env(monkeypatch)  #  Added Code
    _prepare_valid_paths(monkeypatch, tmp_path)  #  Added Code
    monkeypatch.setenv("MAX_ITERATIONS", "not-a-number")  #  Added Code

    c_setup_config._instance = None  #  Added Code

    with pytest.raises(
        ValueError, match="MAX_ITERATIONS must be an integer."
    ):  #  Added Code
        c_setup_config.get_instance()  #  Added Code


def test_setup_config_rejects_invalid_max_iterations(monkeypatch, tmp_path) -> None:
    _clear_runtime_env(monkeypatch)  #  Added Code
    _prepare_valid_paths(monkeypatch, tmp_path)  #  Changed Code
    monkeypatch.setenv("MAX_ITERATIONS", "0")

    config = _fresh_config()  #  Changed Code

    with pytest.raises(ValueError, match="MAX_ITERATIONS must be at least 1"):
        config.validate_initialization()


def test_setup_config_rejects_unsupported_agent(monkeypatch, tmp_path) -> None:
    _clear_runtime_env(monkeypatch)  #  Added Code
    _prepare_valid_paths(monkeypatch, tmp_path)  #  Changed Code
    monkeypatch.setenv("RALPH_AGENT", "codex")

    config = _fresh_config()  #  Changed Code

    with pytest.raises(ValueError, match="RALPH_AGENT must be 'mock'"):
        config.validate_initialization()


def test_setup_config_rejects_unsupported_sandbox_mode(monkeypatch, tmp_path) -> None:
    _clear_runtime_env(monkeypatch)  #  Added Code
    _prepare_valid_paths(monkeypatch, tmp_path)  #  Changed Code
    monkeypatch.setenv("RALPH_SANDBOX_MODE", "cloud")

    config = _fresh_config()  #  Changed Code

    with pytest.raises(
        ValueError, match="RALPH_SANDBOX_MODE must be 'local' or 'docker'"
    ):
        config.validate_initialization()
