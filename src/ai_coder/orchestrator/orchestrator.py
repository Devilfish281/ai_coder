from __future__ import annotations

from dataclasses import dataclass

from ai_coder.agent_provider import AgentProvider, COMPLETE_TOKEN


@dataclass(frozen=True)
class OrchestratorResult:
    completed: bool
    iterations: int
    outputs: tuple[str, ...]
    final_output: str
    error: str | None = None


def i_orchestrator_run(
    agent_provider: AgentProvider,
    prompt: str,
    max_iterations: int = 3,
    completion_token: str = COMPLETE_TOKEN,
) -> OrchestratorResult:
    if max_iterations < 1:
        raise ValueError("max_iterations must be at least 1")

    outputs: list[str] = []

    for iteration_number in range(1, max_iterations + 1):
        response = agent_provider.i_agent_provider_run(prompt)

        if response.error is not None:
            return OrchestratorResult(
                completed=False,
                iterations=iteration_number,
                outputs=tuple(outputs),
                final_output="",
                error=response.error,
            )

        outputs.append(response.output)

        if completion_token in response.output:
            return OrchestratorResult(
                completed=True,
                iterations=iteration_number,
                outputs=tuple(outputs),
                final_output=response.output,
            )

    return OrchestratorResult(
        completed=False,
        iterations=max_iterations,
        outputs=tuple(outputs),
        final_output=outputs[-1] if outputs else "",
        error="Maximum iterations reached before completion.",
    )
