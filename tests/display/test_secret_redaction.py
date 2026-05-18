# tests/display/test_secret_redaction.py
from ai_coder.display import i_display_redact_text


def test_display_redact_text_redacts_configured_secret_value() -> None:
    text = "OPENAI_API_KEY=sk-test-secret"

    result = i_display_redact_text(
        text,
        ("sk-test-secret",),
    )

    assert result == "OPENAI_API_KEY=<redacted>"
    assert "sk-test-secret" not in result


def test_display_redact_text_redacts_multiple_occurrences() -> None:
    text = "first=sk-test-secret second=sk-test-secret"

    result = i_display_redact_text(
        text,
        ("sk-test-secret",),
    )

    assert result == "first=<redacted> second=<redacted>"
    assert result.count("<redacted>") == 2
    assert "sk-test-secret" not in result


def test_display_redact_text_keeps_normal_env_value_visible() -> None:
    text = "PYTHONUNBUFFERED=1"

    result = i_display_redact_text(
        text,
        ("sk-test-secret",),
    )

    assert result == "PYTHONUNBUFFERED=1"


def test_display_redact_text_ignores_empty_secret_values() -> None:
    text = "safe text should stay safe"

    result = i_display_redact_text(
        text,
        ("", "   "),
    )

    assert result == "safe text should stay safe"


def test_display_redact_text_does_not_auto_detect_secret_looking_text() -> None:
    text = "OPENAI_API_KEY=not-configured"

    result = i_display_redact_text(
        text,
        (),
    )

    assert result == "OPENAI_API_KEY=not-configured"
