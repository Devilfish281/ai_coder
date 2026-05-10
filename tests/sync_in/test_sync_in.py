from pathlib import Path

from ai_coder.sync_in import i_sync_in_run


def test_sync_in_run_returns_clear_minimal_result() -> None:
    result = i_sync_in_run("source", "target")

    assert result.source_path == Path("source")
    assert result.target_path == Path("target")
    assert result.changed is False
