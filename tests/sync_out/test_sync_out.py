from pathlib import Path

from ai_coder.sync_out import i_sync_out_merge, i_sync_out_run


def test_sync_out_run_returns_clear_minimal_result() -> None:
    result = i_sync_out_run("source", "target")

    assert result.source_path == Path("source")
    assert result.target_path == Path("target")
    assert result.changed is False


def test_sync_out_merge_stub_does_not_merge() -> None:
    result = i_sync_out_merge(completed=True)

    assert result.merged is False
    assert "stubbed" in result.message
