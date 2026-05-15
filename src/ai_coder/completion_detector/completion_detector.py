# src/ai_coder/completion_detector/completion_detector.py
from __future__ import annotations

from dataclasses import dataclass

from ai_coder.agent_provider import COMPLETE_TOKEN  #  Changed Code
from ai_coder.setup_config import c_setup_config
from ai_coder.my_utils.env_loader import load_dotenv_once

load_dotenv_once()
setup_config = c_setup_config.get_instance()
logger = setup_config.get_logger()


@dataclass(frozen=True)
class CompletionDetectionResult:
    completed: bool
    message: str


def i_completion_detector_detect(  #  Changed Code
    output_text: str,  #  Changed Code
    completion_token: str = COMPLETE_TOKEN,
) -> CompletionDetectionResult:
    logger.info("Starting completion detection.")

    if completion_token in output_text:  #  Changed Code
        message = f"The completion detector found {completion_token}."
        logger.info(message)  #  Changed Code
        return CompletionDetectionResult(
            completed=True,
            message=message,  #  Changed Code
        )

    message = f"The completion detector did not find {completion_token}."
    logger.info(message)  #  Changed Code
    return CompletionDetectionResult(
        completed=False,
        message=message,  #  Changed Code
    )
