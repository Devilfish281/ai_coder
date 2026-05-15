# src/ai_coder/test_runner/test_runner.py
from __future__ import annotations

import shlex
from dataclasses import dataclass

from ai_coder.setup_config import c_setup_config
from ai_coder.my_utils.env_loader import load_dotenv_once

load_dotenv_once()
setup_config = c_setup_config.get_instance()
logger = setup_config.get_logger()


@dataclass(frozen=True)
class TestRunResult:
    __test__ = False
    passed: bool
    command: tuple[str, ...]
    message: str
    stdout: str = ""
    stderr: str = ""
    exit_code: int = 0
    blocked: bool = False


def i_test_runner_run(
    sandbox_handle=None,
    command: tuple[str, ...] | None = None,
) -> TestRunResult:
    logger.info("Starting test runner.")
    resolved_command = _resolve_test_command(command)

    logger.info(f"Received test command: {resolved_command}")

    if not resolved_command:
        message = (
            "Test command is missing. Configure TEST_COMMAND or pass a test command "
            "before running RALPH verification."
        )
        logger.error(message)
        return TestRunResult(
            passed=False,
            command=(),
            message=message,
            exit_code=1,
            blocked=True,
        )

    if sandbox_handle is None:
        logger.info("Test running is stubbed in this tracer-bullet slice.")
        return TestRunResult(
            passed=True,
            command=resolved_command,
            message="Test running is stubbed in this tracer-bullet slice.",
        )

    command_result = sandbox_handle.i_sandboxhandle_run(
        list(resolved_command),
    )

    tests_passed = command_result.succeeded
    message = (
        "Tests passed through the sandbox seam."
        if tests_passed
        else "Tests failed through the sandbox seam."
    )

    logger.info(message)

    return TestRunResult(
        passed=tests_passed,
        command=resolved_command,
        message=message,
        stdout=command_result.stdout,
        stderr=command_result.stderr,
        exit_code=command_result.exit_code,
    )


def _resolve_test_command(
    command: tuple[str, ...] | None,
) -> tuple[str, ...]:
    if command is not None:
        return tuple(str(command_part) for command_part in command if str(command_part))

    configured_command = getattr(setup_config, "test_command", "").strip()

    if not configured_command:
        return ()

    return tuple(shlex.split(configured_command))
