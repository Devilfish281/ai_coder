from __future__ import annotations

from dataclasses import dataclass

# logger & setup_config
from ai_coder.setup_config import c_setup_config
from ai_coder.my_utils.env_loader import load_dotenv_once

load_dotenv_once()
setup_config = c_setup_config.get_instance()
logger = setup_config.get_logger()


@dataclass(frozen=True)
class TestRunResult:
    passed: bool
    command: tuple[str, ...]
    message: str


def i_test_runner_run(
    command: tuple[str, ...] = ("poetry", "run", "pytest")
) -> TestRunResult:
    logger.info("Starting test runner.")
    logger.info(f"Received test command: {command}")
    logger.info("Test running is stubbed in this tracer-bullet slice.")
    return TestRunResult(
        passed=True,
        command=command,
        message="Test running is stubbed in this tracer-bullet slice.",
    )
