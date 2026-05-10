from pathlib import Path

from ai_coder.setup_config import c_setup_config


def test_setup_config_uses_issue_dir_and_file_name_first(monkeypatch, tmp_path) -> None:
    issue_dir = tmp_path / "issues"
    issue_file_name = "local_issue.md"
    fallback_path = tmp_path / "fallback" / "fallback_issue.md"

    monkeypatch.setenv("GITHUB_ISSUE_DIR", str(issue_dir))
    monkeypatch.setenv("GITHUB_ISSUE_FILE_NAME", issue_file_name)
    monkeypatch.setenv("GITHUB_ISSUE_PATH", str(fallback_path))

    result = c_setup_config.resolve_github_issue_path()

    assert result == issue_dir / issue_file_name


def test_setup_config_uses_issue_dir_with_path_file_name(monkeypatch, tmp_path) -> None:
    issue_dir = tmp_path / "issues"
    fallback_path = tmp_path / "fallback" / "fallback_issue.md"

    monkeypatch.setenv("GITHUB_ISSUE_DIR", str(issue_dir))
    monkeypatch.delenv("GITHUB_ISSUE_FILE_NAME", raising=False)
    monkeypatch.setenv("GITHUB_ISSUE_PATH", str(fallback_path))

    result = c_setup_config.resolve_github_issue_path()

    assert result == issue_dir / "fallback_issue.md"


def test_setup_config_uses_issue_file_name_with_path_dir(monkeypatch, tmp_path) -> None:
    fallback_path = tmp_path / "fallback" / "fallback_issue.md"

    monkeypatch.delenv("GITHUB_ISSUE_DIR", raising=False)
    monkeypatch.setenv("GITHUB_ISSUE_FILE_NAME", "local_issue.md")
    monkeypatch.setenv("GITHUB_ISSUE_PATH", str(fallback_path))

    result = c_setup_config.resolve_github_issue_path()

    assert result == tmp_path / "fallback" / "local_issue.md"


def test_setup_config_uses_github_issue_path_when_no_dir_or_file_name(
    monkeypatch, tmp_path
) -> None:
    fallback_path = tmp_path / "fallback" / "fallback_issue.md"

    monkeypatch.delenv("GITHUB_ISSUE_DIR", raising=False)
    monkeypatch.delenv("GITHUB_ISSUE_FILE_NAME", raising=False)
    monkeypatch.setenv("GITHUB_ISSUE_PATH", str(fallback_path))

    result = c_setup_config.resolve_github_issue_path()

    assert result == fallback_path
