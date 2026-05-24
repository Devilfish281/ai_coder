# tests/codex_preflight/test_codex_preflight.py
from types import SimpleNamespace

from ai_coder.codex_preflight import i_codex_preflight_check


def test_codex_preflight_passes_when_provider_is_codex_and_sandbox_is_local() -> None:
    config = SimpleNamespace(
        default_agent="codex",
        sandbox_mode="local",
    )

    result = i_codex_preflight_check(config)

    assert result.ready is True
    assert result.blocked is False
    assert result.agent_provider == "codex"
    assert result.sandbox_mode == "local"
    assert result.message == (
        "Codex preflight passed: provider is 'codex' and sandbox mode is 'local'."
    )


def test_codex_preflight_blocks_provider_mismatch() -> None:
    config = SimpleNamespace(
        default_agent="mock",
        sandbox_mode="local",
    )

    result = i_codex_preflight_check(config)

    assert result.ready is False
    assert result.blocked is True
    assert result.agent_provider == "mock"
    assert result.sandbox_mode == "local"
    assert "RALPH_AGENT" in result.message
    assert "codex" in result.message
    assert "mock" in result.message


def test_codex_preflight_blocks_sandbox_mismatch() -> None:
    config = SimpleNamespace(
        default_agent="codex",
        sandbox_mode="docker",
    )

    result = i_codex_preflight_check(config)

    assert result.ready is False
    assert result.blocked is True
    assert result.agent_provider == "codex"
    assert result.sandbox_mode == "docker"
    assert "RALPH_SANDBOX_MODE" in result.message
    assert "local" in result.message
    assert "docker" in result.message


def test_codex_preflight_normalizes_case_and_whitespace() -> None:
    config = SimpleNamespace(
        default_agent="  CoDeX  ",
        sandbox_mode="  LoCaL  ",
    )

    result = i_codex_preflight_check(config)

    assert result.ready is True
    assert result.blocked is False
    assert result.agent_provider == "codex"
    assert result.sandbox_mode == "local"
    assert "preflight passed" in result.message
