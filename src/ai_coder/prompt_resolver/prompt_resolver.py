# src/ai_coder/prompt_resolver/prompt_resolver.py
from __future__ import annotations

from pathlib import Path


def i_prompt_resolve(
    inline_prompt: str | None = None,
    prompt_path: str | Path | None = None,
) -> str:
    if inline_prompt is not None and prompt_path is not None:
        raise ValueError("Use either inline_prompt or prompt_path, not both.")

    if inline_prompt is not None:
        return inline_prompt

    if prompt_path is None:
        raise ValueError("Provide inline_prompt or prompt_path.")

    resolved_path = Path(prompt_path)

    if not resolved_path.exists():
        raise FileNotFoundError(f"Prompt file does not exist: {resolved_path}")

    if not resolved_path.is_file():
        raise ValueError(f"Prompt path must be a file: {resolved_path}")

    return resolved_path.read_text(encoding="utf-8")
