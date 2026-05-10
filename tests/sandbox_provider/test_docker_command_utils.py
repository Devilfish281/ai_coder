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
