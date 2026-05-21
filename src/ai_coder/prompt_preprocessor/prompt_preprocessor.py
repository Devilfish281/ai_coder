# src/ai_coder/prompt_preprocessor/prompt_preprocessor.py
from __future__ import annotations

import re

from typing import Mapping

_PLACEHOLDER_PATTERN = re.compile(r"\{\{([A-Za-z0-9_]+)\}\}")


def i_prompt_preprocess(raw_prompt: str, values: Mapping[str, object]) -> str:
    def replace_placeholder(match: re.Match[str]) -> str:
        placeholder_name = match.group(1)

        if placeholder_name not in values:
            return match.group(0)

        return _prompt_value_to_text(values[placeholder_name])

    return _PLACEHOLDER_PATTERN.sub(replace_placeholder, raw_prompt)


def _prompt_value_to_text(value: object) -> str:
    if value is None:
        return ""

    return str(value)
