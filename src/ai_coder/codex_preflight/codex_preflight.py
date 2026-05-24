# src/ai_coder/codex_preflight/codex_preflight.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

EXPECTED_CODEX_PROVIDER = "codex"
EXPECTED_CODEX_SANDBOX_MODE = "local"


@dataclass(frozen=True)
class CodexPreflightResult:
    """Store the read-only Codex preflight check result."""

    ready: bool
    blocked: bool
    message: str
    agent_provider: str
    sandbox_mode: str


def i_codex_preflight_check(config: Any) -> CodexPreflightResult:
    """Verify the minimum config required for the Phase 3 Codex smoke proof.

    This preflight is intentionally read-only. It only reads configuration
    values and does not construct providers, start sandboxes, create worktrees,
    run commands, call models, commit changes, create pull requests, or close
    GitHub issues.
    """

    agent_provider = _normalize_config_value(
        getattr(config, "default_agent", ""),
    )
    sandbox_mode = _normalize_config_value(
        getattr(config, "sandbox_mode", ""),
    )

    if agent_provider != EXPECTED_CODEX_PROVIDER:
        return CodexPreflightResult(
            ready=False,
            blocked=True,
            message=(
                "Codex preflight blocked: RALPH_AGENT must be 'codex' for "
                "the Phase 3 Codex smoke proof. "
                f"Current provider: '{agent_provider}'."
            ),
            agent_provider=agent_provider,
            sandbox_mode=sandbox_mode,
        )

    if sandbox_mode != EXPECTED_CODEX_SANDBOX_MODE:
        return CodexPreflightResult(
            ready=False,
            blocked=True,
            message=(
                "Codex preflight blocked: RALPH_SANDBOX_MODE must be 'local' "
                "for the first Phase 3 Codex smoke proof. "
                f"Current sandbox mode: '{sandbox_mode}'."
            ),
            agent_provider=agent_provider,
            sandbox_mode=sandbox_mode,
        )

    return CodexPreflightResult(
        ready=True,
        blocked=False,
        message="Codex preflight passed: provider is 'codex' and sandbox mode is 'local'.",
        agent_provider=agent_provider,
        sandbox_mode=sandbox_mode,
    )


def _normalize_config_value(value: object) -> str:
    return str(value).strip().casefold()
