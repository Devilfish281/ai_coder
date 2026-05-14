# src/ai_coder/prompt_preprocessor/prompt_preprocessor.py
from __future__ import annotations

from typing import Mapping


def i_prompt_preprocess(raw_prompt: str, values: Mapping[str, object]) -> str:
    prepared_prompt = raw_prompt

    for key, value in values.items():
        prepared_prompt = prepared_prompt.replace(
            f"{{{{{key}}}}}",
            _prompt_value_to_text(value),
        )  #  Changed Code

    return prepared_prompt


def _prompt_value_to_text(value: object) -> str:
    if value is None:
        return ""

    return str(value)
