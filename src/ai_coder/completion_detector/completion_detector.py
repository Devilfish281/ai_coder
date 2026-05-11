from __future__ import annotations

from dataclasses import dataclass

# logger & setup_config
from ai_coder.setup_config import c_setup_config
from ai_coder.my_utils.env_loader import load_dotenv_once

load_dotenv_once()
setup_config = c_setup_config.get_instance()
logger = setup_config.get_logger()


@dataclass(frozen=True)
class CompletionDetectionResult:
    completed: bool
    message: str


def i_completion_detector_detect(completed: bool) -> CompletionDetectionResult:
    logger.info("Starting completion detection.")
    if completed:
        logger.info("The orchestrator detected the completion signal.")
        return CompletionDetectionResult(
            completed=True,
            message="The orchestrator detected the completion signal.",
        )

    logger.info("The orchestrator did not detect the completion signal.")
    return CompletionDetectionResult(
        completed=False,
        message="The orchestrator did not detect the completion signal.",
    )
