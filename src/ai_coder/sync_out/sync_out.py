from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class SyncOutResult:
    source_path: Path
    target_path: Path
    changed: bool


@dataclass(frozen=True)
class SyncMergeResult:
    merged: bool
    message: str


def i_sync_out_run(source_path: str | Path, target_path: str | Path) -> SyncOutResult:
    return SyncOutResult(
        source_path=Path(source_path),
        target_path=Path(target_path),
        changed=False,
    )


def i_sync_out_merge(completed: bool) -> SyncMergeResult:
    if completed:
        return SyncMergeResult(
            merged=False,
            message="Sync or merge is stubbed in this tracer-bullet slice.",
        )

    return SyncMergeResult(
        merged=False,
        message="Skipped sync or merge because RALPH did not complete.",
    )
