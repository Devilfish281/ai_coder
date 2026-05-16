# src/ai_coder/completion_detector/completion_detector.py
"""Detect whether agent output contains the RALPH completion token.

This module provides the completion-detector seam used by the orchestrator.
The detector is intentionally small: it treats output as plain text and marks
the task complete only when the configured completion token appears in that
text.
"""

from __future__ import annotations

from dataclasses import dataclass

from ai_coder.agent_provider import COMPLETE_TOKEN
from ai_coder.setup_config import c_setup_config
from ai_coder.my_utils.env_loader import load_dotenv_once

load_dotenv_once()
setup_config = c_setup_config.get_instance()
logger = setup_config.get_logger()


@dataclass(frozen=True)
class CompletionDetectionResult:
    """Store the result of checking agent output for completion.

    :ivar completed: Whether the completion token was found in the output text.
    :vartype completed: bool
    :ivar message: Human-readable explanation of the detection result.
    :vartype message: str
    """

    completed: bool
    message: str


def i_completion_detector_detect(
    output_text: str,
    completion_token: str = COMPLETE_TOKEN,
) -> CompletionDetectionResult:
    """Detect whether output text contains the completion token.

    The detector performs a plain substring check. It does not parse XML,
    execute text, run shell commands, or interpret the output as structured
    data. This keeps the completion seam simple and predictable for tests.

    :param output_text: Agent output text to inspect.
    :type output_text: str
    :param completion_token: Token that marks a task as complete.
    :type completion_token: str
    :return: Result showing whether the token was found.
    :rtype: CompletionDetectionResult
    """

    logger.info("Starting completion detection.")

    if completion_token in output_text:
        message = f"The completion detector found {completion_token}."
        logger.info(message)
        return CompletionDetectionResult(
            completed=True,
            message=message,
        )

    message = f"The completion detector did not find {completion_token}."
    logger.info(message)
    return CompletionDetectionResult(
        completed=False,
        message=message,
    )
