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

_RUNTIME_ENV_NAMES = (
    "PROJECT_NAME",
    "REPO_PATH",
    "GITHUB_REPO",
    "RALPH_AGENT",
    "DRY_RUN",
    "TEST_COMMAND",
    "COMMIT_MESSAGE_TEMPLATE",
    "ISSUE_NUMBER",
    "ISSUE_TITLE",
    "ISSUE_BODY",
    "GITHUB_ISSUE_PATH",
    "GITHUB_ISSUE_DIR",
    "GITHUB_ISSUE_FILE_NAME",
    "LABEL",
    "MAX_ITERATIONS",
    "PROMPT_PATH",
    "RALPH_SANDBOX_MODE",
    "OPENAI_MODEL",
    "RALPH_DOCKER_IMAGE_NAME",
    "RALPH_DOCKERFILE_PATH",
    "CODEX_COMMAND",
)


def _clear_runtime_env(monkeypatch) -> None:
    for env_name in _RUNTIME_ENV_NAMES:
        monkeypatch.delenv(env_name, raising=False)


def _prepare_valid_paths(monkeypatch, tmp_path: Path) -> Path:
    prompt_file = tmp_path / "prompt.md"
    prompt_file.write_text("prompt", encoding="utf-8")

    monkeypatch.setenv("REPO_PATH", str(tmp_path))
    monkeypatch.setenv("PROMPT_PATH", str(prompt_file))

    return prompt_file


def _fresh_config():
    c_setup_config._instance = None
    return c_setup_config.get_instance()


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
    _clear_runtime_env(monkeypatch)
    prompt_file = _prepare_valid_paths(monkeypatch, tmp_path)

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

    config = _fresh_config()

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
    _clear_runtime_env(monkeypatch)
    prompt_file = _prepare_valid_paths(monkeypatch, tmp_path)

    config = _fresh_config()

    assert config.project_name == DEFAULT_PROJECT_NAME
    assert config.repo_path == tmp_path
    assert config.github_repo == DEFAULT_GITHUB_REPO
    assert config.default_agent == DEFAULT_AGENT_NAME
    assert config.dry_run is True
    assert config.test_command == DEFAULT_TEST_COMMAND
    assert config.commit_message_template == DEFAULT_COMMIT_MESSAGE_TEMPLATE
    assert config.max_iterations == 3
    assert config.prompt_path == prompt_file
    assert config.sandbox_mode == "local"


def test_setup_config_env_values_override_defaults(monkeypatch, tmp_path) -> None:
    _clear_runtime_env(monkeypatch)
    prompt_file = _prepare_valid_paths(monkeypatch, tmp_path)

    monkeypatch.setenv("PROJECT_NAME", "Custom AI Code")
    monkeypatch.setenv("GITHUB_REPO", "Devilfish281/custom_ai_coder")
    monkeypatch.setenv("RALPH_AGENT", "mock")
    monkeypatch.setenv("DRY_RUN", "false")
    monkeypatch.setenv("TEST_COMMAND", "pytest")
    monkeypatch.setenv(
        "COMMIT_MESSAGE_TEMPLATE",
        "RALPH: custom issue #{issue_number}",
    )
    monkeypatch.setenv("MAX_ITERATIONS", "5")
    monkeypatch.setenv("RALPH_SANDBOX_MODE", "local")

    config = _fresh_config()

    assert config.project_name == "Custom AI Code"
    assert config.repo_path == tmp_path
    assert config.github_repo == "Devilfish281/custom_ai_coder"
    assert config.default_agent == "mock"
    assert config.dry_run is False
    assert config.test_command == "pytest"
    assert config.commit_message_template == "RALPH: custom issue #{issue_number}"
    assert config.max_iterations == 5
    assert config.prompt_path == prompt_file
    assert config.sandbox_mode == "local"


def test_setup_config_validate_initialization_accepts_valid_loaded_values(
    monkeypatch,
    tmp_path,
) -> None:
    _clear_runtime_env(monkeypatch)
    _prepare_valid_paths(monkeypatch, tmp_path)

    monkeypatch.setenv("PROJECT_NAME", "AI Code")
    monkeypatch.setenv("GITHUB_REPO", "Devilfish281/ai_coder")
    monkeypatch.setenv("RALPH_AGENT", "mock")
    monkeypatch.setenv("TEST_COMMAND", "poetry run pytest")
    monkeypatch.setenv(
        "COMMIT_MESSAGE_TEMPLATE",
        "RALPH: issue #{issue_number} - {issue_title}",
    )
    monkeypatch.setenv("MAX_ITERATIONS", "3")
    monkeypatch.setenv("RALPH_SANDBOX_MODE", "local")

    config = _fresh_config()

    config.validate_initialization()


def test_setup_config_missing_optional_values_use_safe_defaults(
    monkeypatch,
    tmp_path,
) -> None:
    _clear_runtime_env(monkeypatch)
    _prepare_valid_paths(monkeypatch, tmp_path)

    config = _fresh_config()
    result = config.to_dict()

    assert result["project_name"] == DEFAULT_PROJECT_NAME
    assert result["github_repo"] == DEFAULT_GITHUB_REPO
    assert result["default_agent"] == DEFAULT_AGENT_NAME
    assert result["dry_run"] is True
    assert result["test_command"] == DEFAULT_TEST_COMMAND
    assert result["commit_message_template"] == DEFAULT_COMMIT_MESSAGE_TEMPLATE
    assert result["max_iterations"] == 3
    assert result["sandbox_mode"] == "local"


def test_setup_config_invalid_env_int_has_clear_error(monkeypatch, tmp_path) -> None:
    _clear_runtime_env(monkeypatch)
    _prepare_valid_paths(monkeypatch, tmp_path)
    monkeypatch.setenv("MAX_ITERATIONS", "not-a-number")

    c_setup_config._instance = None

    with pytest.raises(ValueError, match="MAX_ITERATIONS must be an integer."):
        c_setup_config.get_instance()


def test_setup_config_rejects_invalid_max_iterations(monkeypatch, tmp_path) -> None:
    _clear_runtime_env(monkeypatch)
    _prepare_valid_paths(monkeypatch, tmp_path)
    monkeypatch.setenv("MAX_ITERATIONS", "0")

    config = _fresh_config()

    with pytest.raises(ValueError, match="MAX_ITERATIONS must be at least 1"):
        config.validate_initialization()


def test_setup_config_rejects_unknown_agent(monkeypatch, tmp_path) -> None:
    _clear_runtime_env(monkeypatch)
    _prepare_valid_paths(monkeypatch, tmp_path)
    monkeypatch.setenv("RALPH_AGENT", "unknown")

    config = _fresh_config()

    with pytest.raises(ValueError, match="RALPH_AGENT must be 'mock' or 'codex'"):
        config.validate_initialization()


def test_setup_config_rejects_unsupported_sandbox_mode(monkeypatch, tmp_path) -> None:
    _clear_runtime_env(monkeypatch)
    _prepare_valid_paths(monkeypatch, tmp_path)
    monkeypatch.setenv("RALPH_SANDBOX_MODE", "cloud")

    config = _fresh_config()

    with pytest.raises(
        ValueError, match="RALPH_SANDBOX_MODE must be 'local' or 'docker'"
    ):
        config.validate_initialization()


def test_setup_config_local_mock_mode_does_not_require_docker_or_codex_settings(
    monkeypatch,
    tmp_path,
) -> None:
    _clear_runtime_env(monkeypatch)
    _prepare_valid_paths(monkeypatch, tmp_path)

    missing_dockerfile_path = tmp_path / "missing.Dockerfile"

    monkeypatch.setenv("RALPH_SANDBOX_MODE", "local")
    monkeypatch.setenv("RALPH_AGENT", "mock")
    monkeypatch.setenv("RALPH_DOCKER_IMAGE_NAME", "")
    monkeypatch.setenv("RALPH_DOCKERFILE_PATH", str(missing_dockerfile_path))
    monkeypatch.delenv("CODEX_COMMAND", raising=False)

    config = _fresh_config()

    config.validate_initialization()


def test_setup_config_docker_mode_requires_docker_image_name(
    monkeypatch,
    tmp_path,
) -> None:
    _clear_runtime_env(monkeypatch)
    _prepare_valid_paths(monkeypatch, tmp_path)

    dockerfile_path = tmp_path / "Dockerfile"
    dockerfile_path.write_text("FROM python:3.12-slim\n", encoding="utf-8")

    monkeypatch.setenv("RALPH_SANDBOX_MODE", "docker")
    monkeypatch.setenv("RALPH_AGENT", "mock")
    monkeypatch.setenv("RALPH_DOCKER_IMAGE_NAME", "")
    monkeypatch.setenv("RALPH_DOCKERFILE_PATH", str(dockerfile_path))

    config = _fresh_config()

    with pytest.raises(
        ValueError,
        match="RALPH_SANDBOX_MODE='docker' requires RALPH_DOCKER_IMAGE_NAME",
    ):
        config.validate_initialization()


def test_setup_config_docker_mode_requires_existing_dockerfile_path(
    monkeypatch,
    tmp_path,
) -> None:
    _clear_runtime_env(monkeypatch)
    _prepare_valid_paths(monkeypatch, tmp_path)

    missing_dockerfile_path = tmp_path / "missing.Dockerfile"

    monkeypatch.setenv("RALPH_SANDBOX_MODE", "docker")
    monkeypatch.setenv("RALPH_AGENT", "mock")
    monkeypatch.setenv("RALPH_DOCKER_IMAGE_NAME", "ai-code-test:latest")
    monkeypatch.setenv("RALPH_DOCKERFILE_PATH", str(missing_dockerfile_path))

    config = _fresh_config()

    with pytest.raises(
        ValueError,
        match="RALPH_SANDBOX_MODE='docker' requires RALPH_DOCKERFILE_PATH to exist",
    ):
        config.validate_initialization()


def test_setup_config_local_mode_ignores_missing_dockerfile_path(
    monkeypatch,
    tmp_path,
) -> None:
    _clear_runtime_env(monkeypatch)
    _prepare_valid_paths(monkeypatch, tmp_path)

    missing_dockerfile_path = tmp_path / "missing.Dockerfile"

    monkeypatch.setenv("RALPH_SANDBOX_MODE", "local")
    monkeypatch.setenv("RALPH_AGENT", "mock")
    monkeypatch.setenv("RALPH_DOCKER_IMAGE_NAME", "")
    monkeypatch.setenv("RALPH_DOCKERFILE_PATH", str(missing_dockerfile_path))

    config = _fresh_config()

    config.validate_initialization()


def test_setup_config_codex_mode_requires_codex_command(
    monkeypatch,
    tmp_path,
) -> None:
    _clear_runtime_env(monkeypatch)
    _prepare_valid_paths(monkeypatch, tmp_path)

    monkeypatch.setenv("RALPH_SANDBOX_MODE", "local")
    monkeypatch.setenv("RALPH_AGENT", "codex")
    monkeypatch.setenv("CODEX_COMMAND", "")

    config = _fresh_config()

    with pytest.raises(
        ValueError,
        match="RALPH_AGENT='codex' requires CODEX_COMMAND",
    ):
        config.validate_initialization()


def test_setup_config_mock_mode_ignores_missing_codex_command(
    monkeypatch,
    tmp_path,
) -> None:
    _clear_runtime_env(monkeypatch)
    _prepare_valid_paths(monkeypatch, tmp_path)

    monkeypatch.setenv("RALPH_SANDBOX_MODE", "local")
    monkeypatch.setenv("RALPH_AGENT", "mock")
    monkeypatch.delenv("CODEX_COMMAND", raising=False)

    config = _fresh_config()

    config.validate_initialization()


def test_setup_config_codex_mode_accepts_codex_command(
    monkeypatch,
    tmp_path,
) -> None:
    _clear_runtime_env(monkeypatch)
    _prepare_valid_paths(monkeypatch, tmp_path)

    monkeypatch.setenv("RALPH_SANDBOX_MODE", "local")
    monkeypatch.setenv("RALPH_AGENT", "codex")
    monkeypatch.setenv("CODEX_COMMAND", "codex")

    config = _fresh_config()

    config.validate_initialization()
