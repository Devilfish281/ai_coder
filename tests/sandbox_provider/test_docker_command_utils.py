# tests/sandbox_provider/test_docker_command_utils.py
from ai_coder.sandbox_provider.docker_command_utils import i_dockercommand_redact


def test_redacts_short_env_option_secret_value() -> None:
    command = ["docker", "run", "-e", "OPENAI_API_KEY=sk-test"]
    result = i_dockercommand_redact(command, ("OPENAI_API_KEY",))
    assert result == ["docker", "run", "-e", "OPENAI_API_KEY=<redacted>"]


def test_redacts_long_env_option_secret_value() -> None:
    command = ["docker", "run", "--env", "OPENAI_API_KEY=sk-test"]
    result = i_dockercommand_redact(command, ("OPENAI_API_KEY",))
    assert result == ["docker", "run", "--env", "OPENAI_API_KEY=<redacted>"]


def test_redacts_single_token_long_env_option_secret_value() -> None:
    command = ["docker", "run", "--env=OPENAI_API_KEY=sk-test"]
    result = i_dockercommand_redact(command, ("OPENAI_API_KEY",))
    assert result == ["docker", "run", "--env=OPENAI_API_KEY=<redacted>"]


def test_does_not_redact_normal_env_value() -> None:
    command = ["docker", "run", "-e", "PYTHONUNBUFFERED=1"]
    result = i_dockercommand_redact(command, ("OPENAI_API_KEY",))
    assert result == ["docker", "run", "-e", "PYTHONUNBUFFERED=1"]


def test_dockercommand_redact_does_not_mutate_original_command() -> None:
    command = ["docker", "run", "-e", "OPENAI_API_KEY=sk-test"]

    result = i_dockercommand_redact(command, ("OPENAI_API_KEY",))

    assert result == ["docker", "run", "-e", "OPENAI_API_KEY=<redacted>"]
    assert command == ["docker", "run", "-e", "OPENAI_API_KEY=sk-test"]


def test_dockercommand_redact_ignores_blank_secret_names() -> None:
    command = ["docker", "run", "-e", "OPENAI_API_KEY=sk-test"]

    result = i_dockercommand_redact(command, ("", "   "))

    assert result == ["docker", "run", "-e", "OPENAI_API_KEY=sk-test"]


def test_dockercommand_redact_preserves_env_arg_without_value() -> None:
    command = ["docker", "run", "-e", "OPENAI_API_KEY"]

    result = i_dockercommand_redact(command, ("OPENAI_API_KEY",))

    assert result == ["docker", "run", "-e", "OPENAI_API_KEY"]
