from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CompletionDetectionResult:
    completed: bool
    message: str


def i_completion_detector_detect(completed: bool) -> CompletionDetectionResult:
    if completed:
        return CompletionDetectionResult(
            completed=True,
            message="The orchestrator detected the completion signal.",
        )

    return CompletionDetectionResult(
        completed=False,
        message="The orchestrator did not detect the completion signal.",
    )
