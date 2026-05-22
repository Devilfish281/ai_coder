# tests/test_docs/test_readme_release1_documentation.py
from pathlib import Path


def _read_readme() -> str:
    repo_root = Path(__file__).resolve().parents[2]
    readme_path = repo_root / "README.md"
    return readme_path.read_text(encoding="utf-8")


def _assert_contains_any(readme_text: str, expected_phrases: tuple[str, ...]) -> None:
    lowered_readme_text = readme_text.lower()

    assert any(
        expected_phrase.lower() in lowered_readme_text
        for expected_phrase in expected_phrases
    )


def test_readme_documents_release_1_user_workflow() -> None:
    readme_text = _read_readme()

    assert "AI Code" in readme_text
    assert "RALPH" in readme_text
    assert "poetry install" in readme_text
    assert "ai-coder" in readme_text
    assert "poetry run pytest" in readme_text

    _assert_contains_any(
        readme_text,
        (
            "local single-issue tracer bullet",
            "release 1",
            "local release 1 tracer bullet",
        ),
    )

    _assert_contains_any(
        readme_text,
        (
            "worktree safety",
            "safe worktree",
            "preserve the worktree",
            "preserve failed or dirty worktrees",
        ),
    )

    _assert_contains_any(
        readme_text,
        (
            "future work",
            "not automatic",
            "does not create pull requests automatically",
            "does not close github issues automatically",
            "future/disabled",
        ),
    )
