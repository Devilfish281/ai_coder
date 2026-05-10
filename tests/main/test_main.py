import ai_coder.main.main as main_module
import ai_coder.ralph.ralph as ralph_module
from ai_coder.main import main
from ai_coder.setup_config import c_setup_config


def _refresh_main_config() -> None:
    c_setup_config._instance = None
    refreshed_config = c_setup_config.get_instance()

    main_module.setup_config = refreshed_config
    main_module.logger = refreshed_config.get_logger()

    ralph_module.setup_config = refreshed_config
    ralph_module.logger = refreshed_config.get_logger()


def test_main_runs_default_fake_issue(capsys, monkeypatch) -> None:
    monkeypatch.setenv("TESTING_FLAG", "true")
    monkeypatch.delenv("ISSUE_NUMBER", raising=False)
    monkeypatch.delenv("ISSUE_TITLE", raising=False)
    monkeypatch.delenv("ISSUE_BODY", raising=False)
    _refresh_main_config()

    exit_code = main([])

    captured = capsys.readouterr()

    assert exit_code == 0
    assert "Selected issue #1: Minimal local RALPH loop" in captured.out
    assert "RALPH completed the selected issue." in captured.out


def test_main_accepts_custom_fake_issue(capsys, monkeypatch) -> None:
    monkeypatch.setenv("TESTING_FLAG", "true")
    _refresh_main_config()

    exit_code = main(
        [
            "--issue-number",
            "7",
            "--issue-title",
            "Fix prompt builder",
            "--issue-body",
            "Prompt builder should include the issue title.",
            "--label",
            "bug",
        ]
    )

    captured = capsys.readouterr()

    assert exit_code == 0
    assert "Selected issue #7: Fix prompt builder" in captured.out
    assert "RALPH completed the selected issue." in captured.out


def test_main_rejects_invalid_max_iterations(capsys, monkeypatch) -> None:
    monkeypatch.setenv("TESTING_FLAG", "true")
    _refresh_main_config()

    exit_code = main(["--max-iterations", "0"])

    captured = capsys.readouterr()

    assert exit_code == 1
    assert "Error: --max-iterations must be at least 1." in captured.out


def test_main_rejects_empty_label(capsys, monkeypatch) -> None:
    monkeypatch.setenv("TESTING_FLAG", "true")
    _refresh_main_config()

    exit_code = main(
        [
            "--issue-number",
            "1",
            "--issue-title",
            "A",
            "--issue-body",
            "B",
            "--label",
            "   ",
        ]
    )

    captured = capsys.readouterr()

    assert exit_code == 1
    assert "Error: --label cannot be empty." in captured.out
