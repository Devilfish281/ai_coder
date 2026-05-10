from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class SyncInResult:
    source_path: Path
    target_path: Path
    changed: bool


def i_sync_in_run(source_path: str | Path, target_path: str | Path) -> SyncInResult:
    return SyncInResult(
        source_path=Path(source_path),
        target_path=Path(target_path),
        changed=False,
    )
