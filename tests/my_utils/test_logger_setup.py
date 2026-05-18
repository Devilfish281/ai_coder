# tests/my_utils/test_logger_setup.py
import logging

from ai_coder.my_utils.logger_setup import SecretRedactionFilter


def test_secret_redaction_filter_redacts_record_message() -> None:
    record = logging.LogRecord(
        name="test",
        level=logging.INFO,
        pathname=__file__,
        lineno=1,
        msg="token=super-secret-026",
        args=(),
        exc_info=None,
    )
    filter_instance = SecretRedactionFilter(("super-secret-026",))

    result = filter_instance.filter(record)

    assert result is True
    assert record.msg == "token=<redacted>"
    assert "super-secret-026" not in record.getMessage()


def test_secret_redaction_filter_redacts_string_args() -> None:
    record = logging.LogRecord(
        name="test",
        level=logging.INFO,
        pathname=__file__,
        lineno=1,
        msg="token=%s normal=%s",
        args=("super-secret-026", "visible"),
        exc_info=None,
    )
    filter_instance = SecretRedactionFilter(("super-secret-026",))

    result = filter_instance.filter(record)

    assert result is True
    assert record.args == ("<redacted>", "visible")
    assert record.getMessage() == "token=<redacted> normal=visible"
    assert "super-secret-026" not in record.getMessage()


def test_secret_redaction_filter_keeps_normal_values_visible() -> None:
    record = logging.LogRecord(
        name="test",
        level=logging.INFO,
        pathname=__file__,
        lineno=1,
        msg="PYTHONUNBUFFERED=%s",
        args=("1",),
        exc_info=None,
    )
    filter_instance = SecretRedactionFilter(("super-secret-026",))

    result = filter_instance.filter(record)

    assert result is True
    assert record.getMessage() == "PYTHONUNBUFFERED=1"
