from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, Sequence

COMPLETE_TOKEN = "<promise>COMPLETE</promise>"


@dataclass(frozen=True)
class AgentResponse:
    output: str
    error: str | None = None


class AgentProvider(Protocol):
    def i_agent_provider_run(self, prompt: str) -> AgentResponse:
        raise NotImplementedError


class MockAgentProvider:
    def __init__(self, responses: Sequence[str | AgentResponse] | None = None) -> None:
        self._responses = list(responses) if responses is not None else [
            AgentResponse(f"Mock agent completed the prompt.\n{COMPLETE_TOKEN}")
        ]
        self.prompts: list[str] = []
        self.run_count = 0

    def i_agent_provider_run(self, prompt: str) -> AgentResponse:
        self.prompts.append(prompt)
        self.run_count += 1

        response_index = min(self.run_count - 1, len(self._responses) - 1)
        response = self._responses[response_index]

        if isinstance(response, AgentResponse):
            return response

        return AgentResponse(output=response)
