# src/ai_coder/agent_provider/agent_provider.py
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
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
    def i_sandboxhandle_run(self, command: list[str], **kwargs: Any) -> Any:
        raise NotImplementedError


@dataclass(frozen=True)
class CodexCommandContract:
    codex_command: str
    worktree_path: Path
    final_output_path: Path

    def i_codex_command_contract_build(self) -> list[str]:
        return [
            self.codex_command,
            "exec",
            "--cd",
            str(self.worktree_path),
            "--sandbox",
            "workspace-write",
            "--color",
            "never",
            "--json",
            "--output-last-message",
            str(self.final_output_path),
            "-",
        ]


class CodexProvider:
    def __init__(
        self,
        sandbox_handle: AgentSandboxHandle,
        codex_command: str,
        worktree_path: str | Path,
        final_output_path: str | Path | None = None,
    ) -> None:
        cleaned_codex_command = codex_command.strip()

        if not cleaned_codex_command:
            raise ValueError("codex_command cannot be empty.")

        self.sandbox_handle = sandbox_handle
        self.worktree_path = Path(worktree_path)
        self.final_output_path = (
            Path(final_output_path)
            if final_output_path is not None
            else self.worktree_path / ".ai_coder" / "codex-last-message.md"
        )
        self.command_contract = CodexCommandContract(
            codex_command=cleaned_codex_command,
            worktree_path=self.worktree_path,
            final_output_path=self.final_output_path,
        )
        self.prompts: list[str] = []
        self.run_count = 0

    def i_agent_provider_run(self, prompt: str) -> AgentResponse:
        self.prompts.append(prompt)
        self.run_count += 1

        command = self.command_contract.i_codex_command_contract_build()
        command_result = self.sandbox_handle.i_sandboxhandle_run(
            command,
            stdin_text=prompt,
        )

        output = _codex_output_from_result(
            stdout_text=str(getattr(command_result, "stdout", "")),
            final_output_path=self.final_output_path,
        )

        if getattr(command_result, "succeeded", False):
            return AgentResponse(output=output)

        return AgentResponse(
            output=output,
            error=_codex_error_message(
                command_result=command_result,
                final_output_path=self.final_output_path,
            ),
        )


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


def _codex_output_from_result(
    stdout_text: str,
    final_output_path: Path,
) -> str:
    jsonl_output = _codex_agent_message_from_jsonl(stdout_text)

    if jsonl_output:
        return jsonl_output

    final_output_file_text = _read_text_if_file_exists(final_output_path)

    if final_output_file_text:
        return final_output_file_text

    return stdout_text


def _codex_agent_message_from_jsonl(stdout_text: str) -> str:
    events = _parse_jsonl_events(stdout_text)

    if not events:
        return ""

    agent_messages: list[str] = []

    for event in events:
        message_text = _agent_message_text_from_event(event)

        if message_text:
            agent_messages.append(message_text)

    return "\n".join(agent_messages).strip()


def _parse_jsonl_events(stdout_text: str) -> tuple[dict[str, Any], ...]:
    events: list[dict[str, Any]] = []

    for line in stdout_text.splitlines():
        cleaned_line = line.strip()

        if not cleaned_line:
            continue

        try:
            parsed_line = json.loads(cleaned_line)
        except json.JSONDecodeError:
            return ()

        if isinstance(parsed_line, dict):
            events.append(parsed_line)

    return tuple(events)


def _agent_message_text_from_event(event: dict[str, Any]) -> str:
    event_type = str(event.get("type", ""))

    if event_type == "item.completed":
        item = event.get("item", {})

        if not isinstance(item, dict):
            return ""

        item_type = str(item.get("type", ""))
        item_role = str(item.get("role", ""))

        if item_type not in {"agent_message", "message"} and item_role != "assistant":
            return ""

        return _text_from_codex_payload(item)

    if event_type == "turn.completed":
        return _text_from_codex_payload(event)

    return ""


def _text_from_codex_payload(payload: dict[str, Any]) -> str:
    for text_key in ("text", "message", "output"):
        text_value = payload.get(text_key)

        if isinstance(text_value, str) and text_value.strip():
            return text_value.strip()

    content = payload.get("content")

    if isinstance(content, str):
        return content.strip()

    if not isinstance(content, list):
        return ""

    content_parts: list[str] = []

    for content_item in content:
        if isinstance(content_item, str) and content_item.strip():
            content_parts.append(content_item.strip())
            continue

        if not isinstance(content_item, dict):
            continue

        item_text = content_item.get("text") or content_item.get("content")

        if isinstance(item_text, str) and item_text.strip():
            content_parts.append(item_text.strip())

    return "\n".join(content_parts).strip()


def _codex_error_message(
    command_result: Any,
    final_output_path: Path,
) -> str:
    stderr_text = str(getattr(command_result, "stderr", "")).strip()
    stdout_text = str(getattr(command_result, "stdout", "")).strip()
    exit_code = getattr(command_result, "exit_code", "unknown")

    if stderr_text:
        return stderr_text

    jsonl_error = _codex_error_from_jsonl(stdout_text)

    if jsonl_error:
        return jsonl_error

    final_output_file_text = _read_text_if_file_exists(final_output_path)

    if final_output_file_text:
        return final_output_file_text

    if stdout_text:
        return stdout_text

    return f"Codex exited with code {exit_code}."


def _codex_error_from_jsonl(stdout_text: str) -> str:
    events = _parse_jsonl_events(stdout_text)

    for event in events:
        event_type = str(event.get("type", ""))

        if event_type not in {"turn.failed", "error"}:
            continue

        error_value = event.get("error")

        if isinstance(error_value, str) and error_value.strip():
            return error_value.strip()

        if isinstance(error_value, dict):
            error_message = error_value.get("message")

            if isinstance(error_message, str) and error_message.strip():
                return error_message.strip()

        message = event.get("message")

        if isinstance(message, str) and message.strip():
            return message.strip()

    return ""


def _read_text_if_file_exists(path: Path) -> str:
    if not path.exists():
        return ""

    if not path.is_file():
        return ""

    return path.read_text(encoding="utf-8").strip()


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
