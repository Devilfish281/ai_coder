# src/ai_coder/repository_context/repository_context.py
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from venv import logger

# need for Logger & setup_config
from ai_coder.setup_config import c_setup_config
from ai_coder.my_utils.env_loader import load_dotenv_once

load_dotenv_once()
setup_config = c_setup_config.get_instance()
logger = setup_config.get_logger()


@dataclass(frozen=True)
class RepositoryStartResult:
    repo_path: Path
    ready: bool
    message: str


def i_repository_start(repo_path: str | Path | None = None) -> RepositoryStartResult:
    resolved_repo_path = Path.cwd() if repo_path is None else Path(repo_path)
    logger.info("Started repository context selection.")
    logger.info(f"Resolving repository path: {resolved_repo_path}")

    return RepositoryStartResult(
        repo_path=resolved_repo_path,
        ready=True,
        message="Repository context selected for this tracer-bullet run.",
    )
