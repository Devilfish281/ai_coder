# src/ai_coder/orchestrator/orchestrator.py
"""Orchestrate an agent run until completion, failure, or max iterations.

This module provides the small public orchestration seam for RALPH. The
orchestrator repeatedly asks an agent provider to work on the same prompt and
stops when the configured completion token is detected, an agent error occurs,
or the maximum iteration limit is reached.
"""

from __future__ import annotations

from dataclasses import dataclass

from ai_coder.agent_provider import AgentProvider, AgentProviderEvent, COMPLETE_TOKEN


from ai_coder.completion_detector import i_completion_detector_detect

from ai_coder.setup_config import c_setup_config
from ai_coder.my_utils.env_loader import load_dotenv_once

load_dotenv_once()
setup_config = c_setup_config.get_instance()
logger = setup_config.get_logger()


@dataclass(frozen=True)
class OrchestratorResult:
    """Store the final result of an orchestrator run.

    :ivar completed: Whether the agent produced the expected completion token.
    :vartype completed: bool
    :ivar iterations: Number of agent iterations that were attempted.
    :vartype iterations: int
    :ivar outputs: Agent outputs collected during successful iterations.
    :vartype outputs: tuple[str, ...]
    :ivar final_output: Last useful agent output. This is empty when the agent
        fails before producing output.
    :vartype final_output: str
    :ivar error: Error message when the agent fails or the run reaches the
        maximum iteration limit before completion.
    :vartype error: str | None
    :ivar events: Normalized provider events collected during the run.
    :vartype events: tuple[AgentProviderEvent, ...]
    """

    completed: bool
    iterations: int
    outputs: tuple[str, ...]
    final_output: str
    error: str | None = None
    events: tuple[AgentProviderEvent, ...] = ()


def i_orchestrator_run(
    agent_provider: AgentProvider,
    prompt: str,
    max_iterations: int = 3,
    completion_token: str = COMPLETE_TOKEN,
) -> OrchestratorResult:
    """Run the agent loop until completion, error, or max iterations.

    The orchestrator sends the same prompt to the configured agent provider on
    each iteration. After every successful agent response, it checks the output
    with the completion detector. The run completes only when the completion
    detector finds the expected token.

    :param agent_provider: Adapter that satisfies the agent provider seam.
    :type agent_provider: AgentProvider
    :param prompt: Prompt text sent to the agent on each iteration.
    :type prompt: str
    :param max_iterations: Maximum number of times to call the agent provider.
    :type max_iterations: int
    :param completion_token: Token that marks the task as complete.
    :type completion_token: str
    :return: Result describing completion state, collected outputs, events, and errors.
    :rtype: OrchestratorResult
    :raises ValueError: If ``max_iterations`` is less than ``1``.
    """

    logger.info("Starting orchestrator run.")
    if max_iterations < 1:
        raise ValueError("max_iterations must be at least 1")

    outputs: list[str] = []
    events: list[AgentProviderEvent] = []

    for iteration_number in range(1, max_iterations + 1):
        logger.info(f"Orchestrator iteration {iteration_number} \n")
        response = agent_provider.i_agent_provider_run(prompt)
        events.extend(response.events)

        if response.error is not None:
            logger.info("Error detected in agent response.")
            return OrchestratorResult(
                completed=False,
                iterations=iteration_number,
                outputs=tuple(outputs),
                final_output="",
                error=response.error,
                events=tuple(events),
            )

        logger.info(f"Agent response output: {response.output}")
        outputs.append(response.output)

        logger.info(f"Total outputs collected so far: {len(outputs)}")
        logger.info("Collecting all agent outputs...")
        for idx, output in enumerate(outputs, start=1):
            logger.info(f"Output {idx}: {output}")

        completion_result = i_completion_detector_detect(
            response.output,
            completion_token=completion_token,
        )

        if completion_result.completed:
            logger.info(completion_result.message)
            return OrchestratorResult(
                completed=True,
                iterations=iteration_number,
                outputs=tuple(outputs),
                final_output=response.output,
                events=tuple(events),
            )

    return OrchestratorResult(
        completed=False,
        iterations=max_iterations,
        outputs=tuple(outputs),
        final_output=outputs[-1] if outputs else "",
        error="Maximum iterations reached before completion.",
        events=tuple(events),
    )
