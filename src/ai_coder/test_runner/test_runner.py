from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class TestRunResult:
    passed: bool
    command: tuple[str, ...]
    message: str


def i_test_runner_run(command: tuple[str, ...] = ("poetry", "run", "pytest")) -> TestRunResult:
    return TestRunResult(
        passed=True,
        command=command,
        message="Test running is stubbed in this tracer-bullet slice.",
    )
