# src/ai_coder/agent_provider/agent_provider.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol, Sequence

COMPLETE_TOKEN = "<promise>COMPLETE</promise>"


@dataclass(frozen=True)
class AgentResponse:
    output: str
    error: str | None = None


class AgentProvider(Protocol):
    def i_agent_provider_run(self, prompt: str) -> AgentResponse:
        raise NotImplementedError


class AgentSandboxHandle(Protocol):
    def i_sandboxhandle_run(self, command: list[str]) -> Any:
        raise NotImplementedError


class MockAgentProvider:
    def __init__(self, responses: Sequence[str | AgentResponse] | None = None) -> None:
        self._responses = (
            list(responses)
            if responses is not None
            else [AgentResponse(f"Mock agent completed the prompt.\n{COMPLETE_TOKEN}")]
        )
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


class FakeTestAgentProvider:
    """Sandbox-backed fake agent provider for the Release 1 tracer bullet.

    This provider proves that an agent provider can run through the sandbox seam
    without calling a real AI coding-agent service.

    The prompt is stored for tests, but it is not passed into command arguments.
    That keeps untrusted issue text inert.
    """

    def __init__(
        self,
        sandbox_handle: AgentSandboxHandle,
        should_fail: bool = False,
        completion_token: str = COMPLETE_TOKEN,
        success_message: str = "Fake test agent completed.",
        failure_message: str = "Fake test agent failed.",
    ) -> None:
        self.sandbox_handle = sandbox_handle
        self.should_fail = should_fail
        self.completion_token = completion_token
        self.success_message = success_message
        self.failure_message = failure_message
        self.prompts: list[str] = []
        self.run_count = 0

    def i_agent_provider_run(self, prompt: str) -> AgentResponse:
        self.prompts.append(prompt)
        self.run_count += 1

        command = (
            _fake_agent_failure_command(self.failure_message)
            if self.should_fail
            else _fake_agent_success_command(
                completion_token=self.completion_token,
                success_message=self.success_message,
            )
        )

        command_result = self.sandbox_handle.i_sandboxhandle_run(command)

        if command_result.succeeded:
            return AgentResponse(output=command_result.stdout)

        return AgentResponse(
            output=command_result.stdout,
            error=_fake_agent_error_message(command_result),
        )


def _fake_agent_success_command(
    completion_token: str,
    success_message: str,
) -> list[str]:
    return [
        "python",
        "-c",
        (f"print({success_message!r}); " f"print({completion_token!r})"),
    ]


def _fake_agent_failure_command(failure_message: str) -> list[str]:
    return [
        "python",
        "-c",
        ("import sys; " f"sys.stderr.write({failure_message!r}); " "sys.exit(1)"),
    ]


def _fake_agent_error_message(command_result: Any) -> str:
    stderr_text = str(getattr(command_result, "stderr", "")).strip()
    stdout_text = str(getattr(command_result, "stdout", "")).strip()
    exit_code = getattr(command_result, "exit_code", "unknown")

    if stderr_text:
        return stderr_text

    if stdout_text:
        return stdout_text

    return f"Fake test agent command failed with exit code {exit_code}."
