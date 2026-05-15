# src/ai_coder/sync_out/sync_out.py
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

# logger & setup_config
from ai_coder.setup_config import c_setup_config
from ai_coder.my_utils.env_loader import load_dotenv_once

load_dotenv_once()
setup_config = c_setup_config.get_instance()
logger = setup_config.get_logger()


@dataclass(frozen=True)
class SyncOutResult:
    source_path: Path
    target_path: Path
    changed: bool


@dataclass(frozen=True)
class SyncMergeResult:
    merged: bool
    message: str
    failed: bool = False


def i_sync_out_run(source_path: str | Path, target_path: str | Path) -> SyncOutResult:
    return SyncOutResult(
        source_path=Path(source_path),
        target_path=Path(target_path),
        changed=False,
    )


def i_sync_out_merge(completed: bool) -> SyncMergeResult:
    logger.info("Starting sync or merge process.")
    if completed:
        logger.info("Sync or merge is stubbed in this tracer-bullet slice.")
        return SyncMergeResult(
            merged=False,
            message="Sync or merge is stubbed in this tracer-bullet slice.",
        )

    logger.info("Error occurred.")
    logger.info("Skipping sync or merge because RALPH did not complete.")
    return SyncMergeResult(
        merged=False,
        message="Skipped sync or merge because RALPH did not complete.",
    )
