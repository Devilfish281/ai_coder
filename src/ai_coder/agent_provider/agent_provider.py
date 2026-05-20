# src/ai_coder/agent_provider/agent_provider.py
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Protocol, Sequence

COMPLETE_TOKEN = "<promise>COMPLETE</promise>"


@dataclass(frozen=True)
class AgentProviderEvent:
    event_type: str
    item_type: str = ""
    text: str = ""
    status: str = ""
    session_id: str = ""
    raw: Mapping[str, object] | None = None


@dataclass(frozen=True)
class AgentResponse:
    output: str
    error: str | None = None
    events: tuple[AgentProviderEvent, ...] = ()


@dataclass(frozen=True)
class _CodexStructuredParseResult:
    structured_output_found: bool
    malformed: bool = False
    events: tuple[AgentProviderEvent, ...] = ()
    raw_events: tuple[dict[str, Any], ...] = ()
    output_text: str = ""
    error_text: str = ""


class AgentProvider(Protocol):
    def i_agent_provider_run(self, prompt: str) -> AgentResponse:
        raise NotImplementedError


class AgentSandboxHandle(Protocol):
    def i_sandboxhandle_run(self, command: list[str], **kwargs: Any) -> Any:
        raise NotImplementedError


def i_agent_provider_create(
    provider_name: str,
    sandbox_handle: AgentSandboxHandle,
    worktree_path: str | Path,
    codex_command: str = "",
    final_output_path: str | Path | None = None,
) -> AgentProvider:
    """Create an agent provider from the public provider-selection seam.

    RALPH should call this seam instead of constructing provider classes
    directly. Provider-specific command construction stays inside each provider.
    """

    cleaned_provider_name = str(provider_name).strip().lower()

    if sandbox_handle is None:
        raise ValueError("sandbox_handle is required to create an agent provider.")

    if cleaned_provider_name == "mock":
        return FakeTestAgentProvider(sandbox_handle=sandbox_handle)

    if cleaned_provider_name == "codex":
        return CodexProvider(
            sandbox_handle=sandbox_handle,
            codex_command=codex_command,
            worktree_path=worktree_path,
            final_output_path=final_output_path,
        )

    raise ValueError(
        "Unsupported agent provider "
        f"{provider_name!r}. Supported providers are: mock, codex."
    )


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
        stdout_text = str(getattr(command_result, "stdout", ""))
        structured_parse_result = _codex_parse_structured_stdout(stdout_text)

        output = _codex_output_from_result(
            stdout_text=stdout_text,
            final_output_path=self.final_output_path,
            structured_parse_result=structured_parse_result,
        )

        if structured_parse_result.malformed:
            return AgentResponse(
                output=output,
                error=structured_parse_result.error_text,
                events=structured_parse_result.events,
            )

        if getattr(command_result, "succeeded", False):
            return AgentResponse(
                output=output,
                events=structured_parse_result.events,
            )

        return AgentResponse(
            output=output,
            error=_codex_error_message(
                command_result=command_result,
                final_output_path=self.final_output_path,
                structured_parse_result=structured_parse_result,
            ),
            events=structured_parse_result.events,
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
    structured_parse_result: _CodexStructuredParseResult | None = None,
) -> str:
    parse_result = structured_parse_result
    if parse_result is None:
        parse_result = _codex_parse_structured_stdout(stdout_text)

    if parse_result.output_text:
        return parse_result.output_text

    final_output_file_text = _read_text_if_file_exists(final_output_path)

    if final_output_file_text:
        return final_output_file_text

    return stdout_text


def _codex_agent_message_from_jsonl(stdout_text: str) -> str:
    parse_result = _codex_parse_structured_stdout(stdout_text)

    if parse_result.malformed:
        return ""

    return parse_result.output_text


def _parse_jsonl_events(stdout_text: str) -> tuple[dict[str, Any], ...]:
    parse_result = _codex_parse_structured_stdout(stdout_text)

    if parse_result.malformed:
        return ()

    return parse_result.raw_events


def _codex_parse_structured_stdout(stdout_text: str) -> _CodexStructuredParseResult:
    events: list[AgentProviderEvent] = []
    raw_events: list[dict[str, Any]] = []
    structured_output_found = False

    for line_number, line in enumerate(stdout_text.splitlines(), start=1):
        cleaned_line = line.strip()

        if not cleaned_line:
            continue

        if not structured_output_found and not _line_looks_like_jsonl(cleaned_line):
            return _CodexStructuredParseResult(structured_output_found=False)

        try:
            parsed_line = json.loads(cleaned_line)
        except json.JSONDecodeError as error:
            return _malformed_codex_parse_result(
                events=tuple(events),
                raw_events=tuple(raw_events),
                line_number=line_number,
                reason=error.msg,
            )

        if not isinstance(parsed_line, dict):
            return _malformed_codex_parse_result(
                events=tuple(events),
                raw_events=tuple(raw_events),
                line_number=line_number,
                reason="expected a JSON object",
            )

        structured_output_found = True
        raw_events.append(parsed_line)
        events.append(_codex_normalize_event(parsed_line))

    if not structured_output_found:
        return _CodexStructuredParseResult(structured_output_found=False)

    event_tuple = tuple(events)
    return _CodexStructuredParseResult(
        structured_output_found=True,
        events=event_tuple,
        raw_events=tuple(raw_events),
        output_text=_codex_final_text_from_events(event_tuple),
        error_text=_codex_error_text_from_events(event_tuple),
    )


def _line_looks_like_jsonl(line: str) -> bool:
    return line.startswith("{") or line.startswith("[")


def _malformed_codex_parse_result(
    *,
    events: tuple[AgentProviderEvent, ...],
    raw_events: tuple[dict[str, Any], ...],
    line_number: int,
    reason: str,
) -> _CodexStructuredParseResult:
    error_text = f"Malformed Codex structured output on line {line_number}: {reason}."
    return _CodexStructuredParseResult(
        structured_output_found=True,
        malformed=True,
        events=events,
        raw_events=raw_events,
        output_text=_codex_final_text_from_events(events),
        error_text=error_text,
    )


def _codex_normalize_event(event: dict[str, Any]) -> AgentProviderEvent:
    event_type = str(event.get("type", ""))
    session_id = _codex_session_id_from_event(event)
    status = str(event.get("status", ""))
    item_type = ""
    text = ""

    if event_type.startswith("item."):
        item = event.get("item", {})
        if isinstance(item, dict):
            item_type = str(item.get("type", ""))
            status = str(item.get("status", status))
            text = _text_from_codex_payload(item)
    elif event_type in {"turn.failed", "error"}:
        text = _codex_error_text_from_event(event)
    else:
        text = _text_from_codex_payload(event)

    return AgentProviderEvent(
        event_type=event_type,
        item_type=item_type,
        text=text,
        status=status,
        session_id=session_id,
        raw=event,
    )


def _codex_session_id_from_event(event: dict[str, Any]) -> str:
    for key in ("thread_id", "session_id"):
        value = event.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()

    thread = event.get("thread")
    if isinstance(thread, dict):
        thread_id = thread.get("id")
        if isinstance(thread_id, str) and thread_id.strip():
            return thread_id.strip()

    return ""


def _codex_final_text_from_events(events: tuple[AgentProviderEvent, ...]) -> str:
    output_parts = [
        event.text
        for event in events
        if _codex_event_is_agent_message(event) and event.text
    ]

    return "\n".join(output_parts).strip()


def _codex_event_is_agent_message(event: AgentProviderEvent) -> bool:
    if event.event_type == "item.completed" and event.item_type in {
        "agent_message",
        "message",
    }:
        return True

    if event.event_type == "turn.completed" and event.text:
        return True

    return False


def _codex_error_text_from_events(events: tuple[AgentProviderEvent, ...]) -> str:
    for event in events:
        if event.event_type in {"turn.failed", "error"} and event.text:
            return event.text

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
    structured_parse_result: _CodexStructuredParseResult | None = None,
) -> str:
    stderr_text = str(getattr(command_result, "stderr", "")).strip()
    stdout_text = str(getattr(command_result, "stdout", "")).strip()
    exit_code = getattr(command_result, "exit_code", "unknown")

    if stderr_text:
        return stderr_text

    parse_result = structured_parse_result
    if parse_result is None:
        parse_result = _codex_parse_structured_stdout(stdout_text)

    if parse_result.malformed:
        return parse_result.error_text

    if parse_result.error_text:
        return parse_result.error_text

    final_output_file_text = _read_text_if_file_exists(final_output_path)

    if final_output_file_text:
        return final_output_file_text

    if stdout_text:
        return stdout_text

    return f"Codex exited with code {exit_code}."


def _codex_error_from_jsonl(stdout_text: str) -> str:
    parse_result = _codex_parse_structured_stdout(stdout_text)

    if parse_result.malformed:
        return parse_result.error_text

    return parse_result.error_text


def _codex_error_text_from_event(event: dict[str, Any]) -> str:
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
