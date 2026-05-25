# src/ai_coder/scaffold/__init__.py
from __future__ import annotations

from ai_coder.scaffold.scaffold import (
    ACTION_CREATED,
    ACTION_OVERWRITTEN,
    ACTION_SKIPPED_EXISTING,
    CODEX_SMOKE_ARTIFACT_RELATIVE_PATHS,
    CODEX_SMOKE_CHECKLIST_RELATIVE_PATH,
    CODEX_SMOKE_INVOCATION_DECISION,
    CODEX_SMOKE_INVOCATION_STYLE,
    CODEX_SMOKE_PROMPT_RELATIVE_PATH,
    ScaffoldFileResult,
    ScaffoldResult,
    i_scaffold_create,
)

__all__ = [
    "ACTION_CREATED",
    "ACTION_OVERWRITTEN",
    "ACTION_SKIPPED_EXISTING",
    "CODEX_SMOKE_ARTIFACT_RELATIVE_PATHS",
    "CODEX_SMOKE_CHECKLIST_RELATIVE_PATH",
    "CODEX_SMOKE_INVOCATION_DECISION",
    "CODEX_SMOKE_INVOCATION_STYLE",
    "CODEX_SMOKE_PROMPT_RELATIVE_PATH",
    "ScaffoldFileResult",
    "ScaffoldResult",
    "i_scaffold_create",
]
