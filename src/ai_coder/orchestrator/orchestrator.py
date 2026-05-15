# src/ai_coder/orchestrator/orchestrator.py
from __future__ import annotations

from dataclasses import dataclass

from ai_coder.agent_provider import AgentProvider, COMPLETE_TOKEN
from ai_coder.completion_detector import i_completion_detector_detect  #  Added Code

from ai_coder.setup_config import c_setup_config
from ai_coder.my_utils.env_loader import load_dotenv_once

load_dotenv_once()
setup_config = c_setup_config.get_instance()
logger = setup_config.get_logger()


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
    logger.info("Starting orchestrator run.")
    if max_iterations < 1:
        raise ValueError("max_iterations must be at least 1")

    outputs: list[str] = []

    for iteration_number in range(1, max_iterations + 1):
        logger.info(f"Orchestrator iteration {iteration_number} \n")
        response = agent_provider.i_agent_provider_run(prompt)

        if response.error is not None:
            logger.info("Error detected in agent response.")
            return OrchestratorResult(
                completed=False,
                iterations=iteration_number,
                outputs=tuple(outputs),
                final_output="",
                error=response.error,
            )

        logger.info(f"Agent response output: {response.output}")
        outputs.append(response.output)

        logger.info(f"Total outputs collected so far: {len(outputs)}")
        logger.info("Collecting all agent outputs...")
        for idx, output in enumerate(outputs, start=1):
            logger.info(f"Output {idx}: {output}")

        completion_result = i_completion_detector_detect(  #  Added Code
            response.output,  #  Added Code
            completion_token=completion_token,  #  Added Code
        )  #  Added Code

        if completion_result.completed:  #  Changed Code
            logger.info(completion_result.message)  #  Changed Code
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
