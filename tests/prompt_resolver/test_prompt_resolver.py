import pytest

from ai_coder.prompt_resolver import i_prompt_resolve


def test_prompt_resolve_returns_inline_prompt() -> None:
    assert i_prompt_resolve(inline_prompt="hello") == "hello"


def test_prompt_resolve_reads_prompt_file(tmp_path) -> None:
    prompt_file = tmp_path / "prompt.txt"
    prompt_file.write_text("file prompt", encoding="utf-8")

    assert i_prompt_resolve(prompt_path=prompt_file) == "file prompt"


def test_prompt_resolve_raises_helpful_error_for_missing_file(tmp_path) -> None:
    missing_file = tmp_path / "missing.txt"

    with pytest.raises(FileNotFoundError, match="Prompt file does not exist"):
        i_prompt_resolve(prompt_path=missing_file)


def test_prompt_resolve_rejects_inline_and_file_together(tmp_path) -> None:
    prompt_file = tmp_path / "prompt.txt"
    prompt_file.write_text("file prompt", encoding="utf-8")

    with pytest.raises(ValueError, match="either inline_prompt or prompt_path"):
        i_prompt_resolve(inline_prompt="hello", prompt_path=prompt_file)
