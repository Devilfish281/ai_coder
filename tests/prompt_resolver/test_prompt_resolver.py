# test/prompt_resolver/test_prompt_resolver.py
import pytest

from ai_coder.prompt_resolver import i_prompt_resolve


def test_prompt_resolve_returns_inline_prompt() -> None:
    result = i_prompt_resolve(inline_prompt="hello")

    assert result == "hello"


def test_prompt_resolve_reads_prompt_file(tmp_path) -> None:
    prompt_file = tmp_path / "prompt.txt"
    prompt_file.write_text("file prompt", encoding="utf-8")

    result = i_prompt_resolve(prompt_path=prompt_file)

    assert result == "file prompt"


def test_prompt_resolve_raises_helpful_error_for_missing_file(tmp_path) -> None:
    missing_file = tmp_path / "missing.txt"

    with pytest.raises(FileNotFoundError, match="Prompt file does not exist"):
        i_prompt_resolve(prompt_path=missing_file)


def test_prompt_resolve_rejects_missing_prompt_source() -> None:
    with pytest.raises(ValueError, match="Provide inline_prompt or prompt_path"):
        i_prompt_resolve()


def test_prompt_resolve_rejects_inline_and_file_together(tmp_path) -> None:
    prompt_file = tmp_path / "prompt.txt"
    prompt_file.write_text("file prompt", encoding="utf-8")

    with pytest.raises(ValueError, match="Use either inline_prompt or prompt_path"):
        i_prompt_resolve(inline_prompt="hello", prompt_path=prompt_file)


def test_prompt_resolve_preserves_large_inline_prompt() -> None:
    large_prompt = "Fix this issue safely.\n" * 5000

    result = i_prompt_resolve(inline_prompt=large_prompt)

    assert result == large_prompt
    assert len(result) == len(large_prompt)


def test_prompt_resolve_preserves_large_file_prompt(tmp_path) -> None:
    large_prompt = "Use RALPH tracer-bullet workflow.\n" * 5000
    prompt_file = tmp_path / "large_prompt.md"
    prompt_file.write_text(large_prompt, encoding="utf-8")

    result = i_prompt_resolve(prompt_path=prompt_file)

    assert result == large_prompt
    assert len(result) == len(large_prompt)
