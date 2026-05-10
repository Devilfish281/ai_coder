from __future__ import annotations

from typing import Mapping


def i_prompt_preprocess(raw_prompt: str, values: Mapping[str, object]) -> str:
    prepared_prompt = raw_prompt

    for key, value in values.items():
        prepared_prompt = prepared_prompt.replace(f"{{{{{key}}}}}", str(value))

    return prepared_prompt
