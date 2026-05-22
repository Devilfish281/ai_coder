# src/ai_coder/scaffold/__init__.py
from __future__ import annotations

from ai_coder.scaffold.scaffold import (
    ACTION_CREATED,
    ACTION_OVERWRITTEN,
    ACTION_SKIPPED_EXISTING,
    ScaffoldFileResult,
    ScaffoldResult,
    i_scaffold_create,
)

__all__ = [
    "ACTION_CREATED",
    "ACTION_OVERWRITTEN",
    "ACTION_SKIPPED_EXISTING",
    "ScaffoldFileResult",
    "ScaffoldResult",
    "i_scaffold_create",
]
