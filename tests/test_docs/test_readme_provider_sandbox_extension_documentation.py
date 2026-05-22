# tests/test_docs/test_readme_provider_sandbox_extension_documentation.py
from __future__ import annotations

from pathlib import Path


def _read_readme() -> str:
    repo_root = Path(__file__).resolve().parents[2]
    readme_path = repo_root / "README.md"
    return readme_path.read_text(encoding="utf-8")


def _assert_contains_all(readme_text: str, expected_phrases: tuple[str, ...]) -> None:
    lowered_readme_text = readme_text.lower()

    for expected_phrase in expected_phrases:
        assert expected_phrase.lower() in lowered_readme_text


def test_readme_documents_provider_and_sandbox_extension_model() -> None:
    readme_text = _read_readme()

    _assert_contains_all(
        readme_text,
        (
            "provider and sandbox extension guide",
            "sandbox seam",
            "i_sandbox_start",
            "i_sandboxhandle_run",
            "CommandResult",
            "Docker bind-mount",
            "/workspace",
            "PYTHONUNBUFFERED",
            "docker_env_allowlist",
            "docker_secret_env_allowlist",
            "redact",
            "CodexProvider",
            "codex exec",
            "i_agent_provider_create",
            "future agent provider",
            "future sandbox provider",
            ".ai-code",
            "scaffold",
            "extension",
        ),
    )


def test_readme_keeps_future_extension_points_separate_from_current_behavior() -> None:
    readme_text = _read_readme()

    _assert_contains_all(
        readme_text,
        (
            "future extension",
            "automatic pull request creation",
            "automatic GitHub issue closing",
            "cloud sandbox",
            "not implemented",
        ),
    )
