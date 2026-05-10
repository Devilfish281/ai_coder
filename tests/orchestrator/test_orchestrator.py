import pytest

from ai_coder.agent_provider import AgentResponse, MockAgentProvider
from ai_coder.orchestrator import i_orchestrator_run


def test_orchestrator_stops_when_agent_outputs_complete_token() -> None:
    provider = MockAgentProvider(
        responses=[
            "Working on it",
            "Finished\n<promise>COMPLETE</promise>",
        ]
    )

    result = i_orchestrator_run(provider, "prompt", max_iterations=3)

    assert result.completed is True
    assert result.iterations == 2
    assert result.error is None
    assert result.outputs == ("Working on it", "Finished\n<promise>COMPLETE</promise>")


def test_orchestrator_stops_at_max_iterations() -> None:
    provider = MockAgentProvider(responses=["Still not done"])

    result = i_orchestrator_run(provider, "prompt", max_iterations=2)

    assert result.completed is False
    assert result.iterations == 2
    assert result.error == "Maximum iterations reached before completion."
    assert result.outputs == ("Still not done", "Still not done")


def test_orchestrator_stops_when_agent_returns_error() -> None:
    provider = MockAgentProvider(
        responses=[AgentResponse(output="", error="agent failed")]
    )

    result = i_orchestrator_run(provider, "prompt", max_iterations=3)

    assert result.completed is False
    assert result.iterations == 1
    assert result.error == "agent failed"
    assert result.outputs == ()


def test_orchestrator_rejects_invalid_iteration_limit() -> None:
    provider = MockAgentProvider()

    with pytest.raises(ValueError, match="max_iterations"):
        i_orchestrator_run(provider, "prompt", max_iterations=0)
