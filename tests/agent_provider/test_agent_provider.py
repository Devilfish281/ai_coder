# tests/agent_provider/test_agent_provider.py
import json

import pytest

from ai_coder.agent_provider import (
    COMPLETE_TOKEN,
    AgentProviderEvent,
    AgentResponse,
    CodexProvider,
    FakeTestAgentProvider,
    MockAgentProvider,
    i_agent_provider_create,
    NORMALIZED_EVENT_TYPE_ERROR,
    NORMALIZED_EVENT_TYPE_RESULT,
    NORMALIZED_EVENT_TYPE_SESSION,
    NORMALIZED_EVENT_TYPE_TEXT,
    NORMALIZED_EVENT_TYPE_TOOL_CALL,
)


from ai_coder.orchestrator import i_orchestrator_run

from ai_coder.sandbox_provider import CommandResult


class FakeSandboxHandle:
    def __init__(self, command_result: CommandResult) -> None:
        self.command_result = command_result
        self.commands: list[list[str]] = []

    def i_sandboxhandle_run(self, command: list[str]) -> CommandResult:
        self.commands.append(command)
        return self.command_result


class FakeCodexSandboxHandle:
    def __init__(self, command_result: CommandResult) -> None:
        self.command_result = command_result
        self.calls: list[dict[str, object]] = []

    def i_sandboxhandle_run(
        self,
        command: list[str],
        stdin_text: str = "",
    ) -> CommandResult:
        self.calls.append(
            {
                "command": command,
                "stdin_text": stdin_text,
            }
        )
        return self.command_result


def test_mock_agent_returns_deterministic_complete_response() -> None:
    provider = MockAgentProvider()

    result = provider.i_agent_provider_run("Fix issue #1")

    assert result.error is None
    assert COMPLETE_TOKEN in result.output
    assert provider.prompts == ["Fix issue #1"]
    assert provider.run_count == 1


def test_mock_agent_uses_scripted_responses_in_order() -> None:
    provider = MockAgentProvider(
        responses=[
            "Still working",
            AgentResponse(output="Done\n<promise>COMPLETE</promise>"),
        ]
    )

    first_result = provider.i_agent_provider_run("prompt")
    second_result = provider.i_agent_provider_run("prompt")

    assert first_result.output == "Still working"
    assert second_result.output == "Done\n<promise>COMPLETE</promise>"
    assert provider.run_count == 2


def test_agent_response_defaults_to_empty_events() -> None:
    response = AgentResponse(output="Done")

    assert response.output == "Done"
    assert response.error is None
    assert response.events == ()


def test_agent_provider_event_stores_normalized_provider_data() -> None:
    event = AgentProviderEvent(
        event_type="item.completed",
        item_type="agent_message",
        text="Done",
        status="completed",
        session_id="thread_123",
        normalized_type=NORMALIZED_EVENT_TYPE_TEXT,
        raw={"type": "item.completed"},
    )

    assert event.event_type == "item.completed"
    assert event.item_type == "agent_message"
    assert event.text == "Done"
    assert event.status == "completed"
    assert event.session_id == "thread_123"
    assert event.normalized_type == NORMALIZED_EVENT_TYPE_TEXT
    assert event.raw == {"type": "item.completed"}


def test_fake_test_agent_runs_success_command_through_sandbox_seam() -> None:
    sandbox_handle = FakeSandboxHandle(
        CommandResult(
            stdout="Fake test agent completed.\n<promise>COMPLETE</promise>\n",
            stderr="",
            exit_code=0,
        )
    )
    provider = FakeTestAgentProvider(sandbox_handle)

    result = provider.i_agent_provider_run("Fix issue #20")

    assert result.error is None
    assert COMPLETE_TOKEN in result.output
    assert len(sandbox_handle.commands) == 1
    assert provider.prompts == ["Fix issue #20"]
    assert provider.run_count == 1


def test_fake_test_agent_converts_failed_sandbox_command_to_agent_error() -> None:
    sandbox_handle = FakeSandboxHandle(
        CommandResult(
            stdout="",
            stderr="fake failure",
            exit_code=7,
        )
    )
    provider = FakeTestAgentProvider(
        sandbox_handle=sandbox_handle,
        should_fail=True,
    )

    result = provider.i_agent_provider_run("Fix issue #20")

    assert result.output == ""
    assert result.error is not None
    assert "fake failure" in result.error
    assert len(sandbox_handle.commands) == 1
    assert provider.prompts == ["Fix issue #20"]
    assert provider.run_count == 1


def test_fake_test_agent_does_not_put_prompt_text_in_command_arguments() -> None:
    sandbox_handle = FakeSandboxHandle(
        CommandResult(
            stdout="Fake test agent completed.\n<promise>COMPLETE</promise>\n",
            stderr="",
            exit_code=0,
        )
    )
    provider = FakeTestAgentProvider(sandbox_handle)

    unsafe_prompt = (
        r'Issue title !`echo title` $(Write-Output "title") '
        r"&& echo title | whoami %PATH% ^ C:\Temp\RALPH"
    )

    result = provider.i_agent_provider_run(unsafe_prompt)

    command_text = " ".join(sandbox_handle.commands[0])

    assert result.error is None
    assert COMPLETE_TOKEN in result.output
    assert provider.prompts == [unsafe_prompt]
    assert unsafe_prompt not in command_text
    assert len(sandbox_handle.commands) == 1


def test_codex_provider_builds_non_interactive_command(tmp_path) -> None:
    final_output_path = tmp_path / "codex-last-message.md"
    sandbox_handle = FakeCodexSandboxHandle(
        CommandResult(
            stdout="Plain Codex output\n<promise>COMPLETE</promise>",
            stderr="",
            exit_code=0,
        )
    )
    provider = CodexProvider(
        sandbox_handle=sandbox_handle,
        codex_command="codex",
        worktree_path=tmp_path,
        final_output_path=final_output_path,
    )

    prompt = "Fix issue #37 without putting this prompt in command args."

    result = provider.i_agent_provider_run(prompt)

    command = sandbox_handle.calls[0]["command"]

    assert result.error is None
    assert result.output == "Plain Codex output\n<promise>COMPLETE</promise>"
    assert command == [
        "codex",
        "exec",
        "--cd",
        str(tmp_path),
        "--sandbox",
        "workspace-write",
        "--color",
        "never",
        "--json",
        "--output-last-message",
        str(final_output_path),
        "-",
    ]
    assert "--full-auto" not in command
    assert "--dangerously-bypass-approvals-and-sandbox" not in command
    assert "--yolo" not in command
    assert "--ignore-user-config" not in command
    assert "--ignore-rules" not in command
    assert "--ephemeral" not in command
    assert prompt not in command


def test_codex_provider_passes_prompt_through_stdin(tmp_path) -> None:
    sandbox_handle = FakeCodexSandboxHandle(
        CommandResult(
            stdout="Codex done\n<promise>COMPLETE</promise>",
            stderr="",
            exit_code=0,
        )
    )
    provider = CodexProvider(
        sandbox_handle=sandbox_handle,
        codex_command="codex",
        worktree_path=tmp_path,
        final_output_path=tmp_path / "codex-last-message.md",
    )

    prompt = (
        "Long Windows prompt text " * 100
        + r' !`echo unsafe` $(Write-Output "title") && echo title | whoami %PATH% ^ C:\Temp\RALPH'
    )

    result = provider.i_agent_provider_run(prompt)

    command = sandbox_handle.calls[0]["command"]
    command_text = " ".join(command)

    assert result.error is None
    assert sandbox_handle.calls[0]["stdin_text"] == prompt
    assert provider.prompts == [prompt]
    assert provider.run_count == 1
    assert prompt not in command
    assert prompt not in command_text
    assert command[-1] == "-"


def test_codex_provider_parses_jsonl_agent_message(tmp_path) -> None:
    final_text = "Codex completed the issue.\n<promise>COMPLETE</promise>"
    stdout = (
        json.dumps(
            {
                "type": "thread.started",
                "thread_id": "thread_123",
            }
        )
        + "\n"
        + json.dumps(
            {
                "type": "item.completed",
                "item": {
                    "type": "agent_message",
                    "text": final_text,
                },
            }
        )
        + "\n"
    )
    sandbox_handle = FakeCodexSandboxHandle(
        CommandResult(
            stdout=stdout,
            stderr="",
            exit_code=0,
        )
    )
    provider = CodexProvider(
        sandbox_handle=sandbox_handle,
        codex_command="codex",
        worktree_path=tmp_path,
        final_output_path=tmp_path / "codex-last-message.md",
    )

    result = provider.i_agent_provider_run("Fix issue #37")

    assert result.error is None
    assert result.output == final_text
    assert COMPLETE_TOKEN in result.output


def test_codex_provider_prefers_final_message_file_over_structured_jsonl(
    tmp_path,
) -> None:
    final_output_path = tmp_path / "codex-last-message.md"
    final_message_text = "Final message from file wins.\n<promise>COMPLETE</promise>"
    final_output_path.write_text(
        final_message_text,
        encoding="utf-8",
    )
    jsonl_message_text = (
        "Structured JSONL message should not win.\n<promise>COMPLETE</promise>"
    )
    stdout = (
        json.dumps(
            {
                "type": "thread.started",
                "thread_id": "thread_041",
            }
        )
        + "\n"
        + json.dumps(
            {
                "type": "item.completed",
                "item": {
                    "type": "agent_message",
                    "text": jsonl_message_text,
                },
            }
        )
        + "\n"
    )
    sandbox_handle = FakeCodexSandboxHandle(
        CommandResult(
            stdout=stdout,
            stderr="",
            exit_code=0,
        )
    )
    provider = CodexProvider(
        sandbox_handle=sandbox_handle,
        codex_command="codex",
        worktree_path=tmp_path,
        final_output_path=final_output_path,
    )

    result = provider.i_agent_provider_run("Fix issue #41")

    assert result.error is None
    assert result.output == final_message_text
    assert result.output != jsonl_message_text
    assert len(result.events) >= 2
    assert result.events[0].event_type == "thread.started"
    assert result.events[1].event_type == "item.completed"
    assert result.events[1].item_type == "agent_message"
    assert result.events[1].text == jsonl_message_text
    assert result.events[0].normalized_type == NORMALIZED_EVENT_TYPE_SESSION
    assert result.events[1].normalized_type == NORMALIZED_EVENT_TYPE_TEXT


def test_codex_provider_falls_back_to_jsonl_when_final_message_file_is_missing(
    tmp_path,
) -> None:
    missing_final_output_path = tmp_path / "missing-codex-last-message.md"
    jsonl_message_text = "Structured JSONL fallback.\n<promise>COMPLETE</promise>"
    stdout = (
        json.dumps(
            {
                "type": "thread.started",
                "thread_id": "thread_067",
            }
        )
        + "\n"
        + json.dumps(
            {
                "type": "item.completed",
                "item": {
                    "type": "agent_message",
                    "text": jsonl_message_text,
                },
            }
        )
        + "\n"
    )
    sandbox_handle = FakeCodexSandboxHandle(
        CommandResult(
            stdout=stdout,
            stderr="",
            exit_code=0,
        )
    )
    provider = CodexProvider(
        sandbox_handle=sandbox_handle,
        codex_command="codex",
        worktree_path=tmp_path,
        final_output_path=missing_final_output_path,
    )

    result = provider.i_agent_provider_run("Fix issue #67")

    assert result.error is None
    assert result.output == jsonl_message_text
    assert len(result.events) == 2
    assert result.events[0].event_type == "thread.started"
    assert result.events[0].normalized_type == NORMALIZED_EVENT_TYPE_SESSION
    assert result.events[0].session_id == "thread_067"
    assert result.events[1].event_type == "item.completed"
    assert result.events[1].item_type == "agent_message"
    assert result.events[1].text == jsonl_message_text
    assert result.events[1].normalized_type == NORMALIZED_EVENT_TYPE_TEXT


def test_codex_provider_returns_normalized_events_from_jsonl(tmp_path) -> None:
    final_text = "Codex finished from normalized events.\n<promise>COMPLETE</promise>"
    stdout = (
        json.dumps(
            {
                "type": "thread.started",
                "thread_id": "thread_041",
            }
        )
        + "\n"
        + json.dumps(
            {
                "type": "turn.started",
            }
        )
        + "\n"
        + json.dumps(
            {
                "type": "item.started",
                "item": {
                    "type": "command_execution",
                    "status": "in_progress",
                    "command": "poetry run pytest",
                },
            }
        )
        + "\n"
        + json.dumps(
            {
                "type": "item.completed",
                "item": {
                    "type": "command_execution",
                    "status": "completed",
                    "output": "pytest passed",
                },
            }
        )
        + "\n"
        + json.dumps(
            {
                "type": "item.completed",
                "item": {
                    "type": "agent_message",
                    "text": final_text,
                },
            }
        )
        + "\n"
        + json.dumps(
            {
                "type": "turn.completed",
                "status": "completed",
            }
        )
        + "\n"
    )
    sandbox_handle = FakeCodexSandboxHandle(
        CommandResult(
            stdout=stdout,
            stderr="",
            exit_code=0,
        )
    )
    provider = CodexProvider(
        sandbox_handle=sandbox_handle,
        codex_command="codex",
        worktree_path=tmp_path,
        final_output_path=tmp_path / "codex-last-message.md",
    )

    result = provider.i_agent_provider_run("Fix issue #43")

    assert result.error is None
    assert result.output == final_text
    assert COMPLETE_TOKEN in result.output
    assert len(result.events) == 6

    assert result.events[0].event_type == "thread.started"
    assert result.events[0].normalized_type == NORMALIZED_EVENT_TYPE_SESSION
    assert result.events[0].session_id == "thread_041"

    assert result.events[2].event_type == "item.started"
    assert result.events[2].item_type == "command_execution"
    assert result.events[2].status == "in_progress"
    assert result.events[2].normalized_type == NORMALIZED_EVENT_TYPE_TOOL_CALL

    assert result.events[3].event_type == "item.completed"
    assert result.events[3].item_type == "command_execution"
    assert result.events[3].text == "pytest passed"
    assert result.events[3].normalized_type == NORMALIZED_EVENT_TYPE_RESULT

    assert result.events[4].event_type == "item.completed"
    assert result.events[4].item_type == "agent_message"
    assert result.events[4].text == final_text
    assert result.events[4].normalized_type == NORMALIZED_EVENT_TYPE_TEXT

    assert result.events[5].event_type == "turn.completed"
    assert result.events[5].normalized_type == NORMALIZED_EVENT_TYPE_RESULT


def test_codex_provider_returns_clear_error_for_malformed_jsonl(tmp_path) -> None:
    stdout = (
        json.dumps(
            {
                "type": "thread.started",
                "thread_id": "thread_041",
            }
        )
        + "\n"
        + "{malformed json line\n"
    )
    sandbox_handle = FakeCodexSandboxHandle(
        CommandResult(
            stdout=stdout,
            stderr="",
            exit_code=0,
        )
    )
    provider = CodexProvider(
        sandbox_handle=sandbox_handle,
        codex_command="codex",
        worktree_path=tmp_path,
        final_output_path=tmp_path / "codex-last-message.md",
    )

    result = provider.i_agent_provider_run("Fix issue #43")

    assert result.output == stdout
    assert COMPLETE_TOKEN not in result.output
    assert result.error is not None
    assert "Malformed Codex structured output" in result.error
    assert "line 2" in result.error
    assert result.stdout == stdout
    assert result.stderr == ""
    assert result.exit_code == 0
    assert len(result.events) == 2
    assert result.events[0].event_type == "thread.started"
    assert result.events[0].normalized_type == NORMALIZED_EVENT_TYPE_SESSION
    assert result.events[0].session_id == "thread_041"
    assert result.events[1].event_type == "parse.error"
    assert result.events[1].normalized_type == NORMALIZED_EVENT_TYPE_ERROR
    assert "Malformed Codex structured output" in result.events[1].text


def test_codex_provider_returns_clear_error_when_first_jsonl_line_is_malformed(
    tmp_path,
) -> None:
    stdout = "{malformed json line\n"
    sandbox_handle = FakeCodexSandboxHandle(
        CommandResult(
            stdout=stdout,
            stderr="",
            exit_code=0,
        )
    )
    provider = CodexProvider(
        sandbox_handle=sandbox_handle,
        codex_command="codex",
        worktree_path=tmp_path,
        final_output_path=tmp_path / "codex-last-message.md",
    )

    result = provider.i_agent_provider_run("Fix issue #41")

    assert result.output == stdout
    assert COMPLETE_TOKEN not in result.output
    assert result.error is not None
    assert "Malformed Codex structured output" in result.error
    assert "line 1" in result.error
    assert result.stdout == stdout
    assert result.stderr == ""
    assert result.exit_code == 0
    assert len(result.events) == 1
    assert result.events[0].event_type == "parse.error"
    assert result.events[0].normalized_type == NORMALIZED_EVENT_TYPE_ERROR
    assert "Malformed Codex structured output" in result.events[0].text


def test_codex_provider_uses_final_message_file_when_jsonl_is_malformed(
    tmp_path,
) -> None:
    final_output_path = tmp_path / "codex-last-message.md"
    final_message_text = "Trusted final message.\n<promise>COMPLETE</promise>"
    final_output_path.write_text(
        final_message_text,
        encoding="utf-8",
    )
    stdout = (
        json.dumps(
            {
                "type": "thread.started",
                "thread_id": "thread_067",
            }
        )
        + "\n"
        + "{malformed json line\n"
    )
    sandbox_handle = FakeCodexSandboxHandle(
        CommandResult(
            stdout=stdout,
            stderr="",
            exit_code=0,
        )
    )
    provider = CodexProvider(
        sandbox_handle=sandbox_handle,
        codex_command="codex",
        worktree_path=tmp_path,
        final_output_path=final_output_path,
    )

    result = provider.i_agent_provider_run("Fix issue #67")

    assert result.error is None
    assert result.output == final_message_text
    assert COMPLETE_TOKEN in result.output
    assert result.stdout == stdout
    assert result.stderr == ""
    assert result.exit_code == 0
    assert any(
        event.event_type == "final_message_file"
        and event.normalized_type == NORMALIZED_EVENT_TYPE_TEXT
        and event.text == final_message_text
        for event in result.events
    )
    assert any(
        event.event_type == "parse.error"
        and event.normalized_type == NORMALIZED_EVENT_TYPE_ERROR
        and "Malformed Codex structured output" in event.text
        for event in result.events
    )


def test_codex_provider_recovers_from_malformed_jsonl_when_stdout_fallback_has_complete_token(
    tmp_path,
) -> None:
    stdout = (
        json.dumps(
            {
                "type": "thread.started",
                "thread_id": "thread_070",
            }
        )
        + "\n"
        + "{malformed json line\n"
        + f"Recovered through stdout fallback.\n{COMPLETE_TOKEN}"
    )
    sandbox_handle = FakeCodexSandboxHandle(
        CommandResult(
            stdout=stdout,
            stderr="",
            exit_code=0,
        )
    )
    provider = CodexProvider(
        sandbox_handle=sandbox_handle,
        codex_command="codex",
        worktree_path=tmp_path,
        final_output_path=tmp_path / "missing-codex-last-message.md",
    )

    result = provider.i_agent_provider_run("Fix issue #70")

    assert result.error is None
    assert result.output == stdout
    assert COMPLETE_TOKEN in result.output
    assert result.stdout == stdout
    assert result.stderr == ""
    assert result.exit_code == 0
    assert any(
        event.event_type == "parse.error"
        and event.normalized_type == NORMALIZED_EVENT_TYPE_ERROR
        and "Malformed Codex structured output" in event.text
        for event in result.events
    )


def test_codex_provider_malformed_jsonl_stdout_fallback_completion_reaches_orchestrator(
    tmp_path,
) -> None:
    stdout = (
        json.dumps(
            {
                "type": "thread.started",
                "thread_id": "thread_070",
            }
        )
        + "\n"
        + "{malformed json line\n"
        + f"Recovered through orchestrator.\n{COMPLETE_TOKEN}"
    )
    sandbox_handle = FakeCodexSandboxHandle(
        CommandResult(
            stdout=stdout,
            stderr="",
            exit_code=0,
        )
    )
    provider = CodexProvider(
        sandbox_handle=sandbox_handle,
        codex_command="codex",
        worktree_path=tmp_path,
        final_output_path=tmp_path / "missing-codex-last-message.md",
    )

    result = i_orchestrator_run(
        provider,
        "Fix issue #70",
        max_iterations=1,
    )

    assert result.completed is True
    assert result.error is None
    assert result.final_output == stdout
    assert COMPLETE_TOKEN in result.final_output
    assert any(
        event.event_type == "parse.error"
        and event.normalized_type == NORMALIZED_EVENT_TYPE_ERROR
        and "Malformed Codex structured output" in event.text
        for event in result.events
    )


def test_codex_provider_nonzero_exit_still_fails_when_malformed_jsonl_has_completion_fallback(
    tmp_path,
) -> None:
    stdout = (
        json.dumps(
            {
                "type": "thread.started",
                "thread_id": "thread_070",
            }
        )
        + "\n"
        + "{malformed json line\n"
        + f"Partial stdout fallback.\n{COMPLETE_TOKEN}"
    )
    sandbox_handle = FakeCodexSandboxHandle(
        CommandResult(
            stdout=stdout,
            stderr="Codex failed",
            exit_code=1,
        )
    )
    provider = CodexProvider(
        sandbox_handle=sandbox_handle,
        codex_command="codex",
        worktree_path=tmp_path,
        final_output_path=tmp_path / "missing-codex-last-message.md",
    )

    result = provider.i_agent_provider_run("Fix issue #70")

    assert result.error is not None
    assert "Codex failed" in result.error
    assert result.output == stdout
    assert COMPLETE_TOKEN in result.output
    assert result.stdout == stdout
    assert result.stderr == "Codex failed"
    assert result.exit_code == 1
    assert "Codex failed" in result.diagnostics
    assert "Exit code: 1." in result.diagnostics
    assert any(
        event.event_type == "parse.error"
        and event.normalized_type == NORMALIZED_EVENT_TYPE_ERROR
        and "Malformed Codex structured output" in event.text
        for event in result.events
    )


def test_codex_provider_returns_text_event_for_plain_stdout(tmp_path) -> None:
    sandbox_handle = FakeCodexSandboxHandle(
        CommandResult(
            stdout="Plain stdout result.\n<promise>COMPLETE</promise>",
            stderr="",
            exit_code=0,
        )
    )
    provider = CodexProvider(
        sandbox_handle=sandbox_handle,
        codex_command="codex",
        worktree_path=tmp_path,
        final_output_path=tmp_path / "missing-codex-last-message.md",
    )

    result = provider.i_agent_provider_run("Fix issue #41")

    assert result.error is None
    assert result.output == "Plain stdout result.\n<promise>COMPLETE</promise>"
    assert len(result.events) == 1
    assert result.events[0].event_type == "plain.stdout"
    assert result.events[0].normalized_type == NORMALIZED_EVENT_TYPE_TEXT
    assert result.events[0].text == "Plain stdout result.\n<promise>COMPLETE</promise>"
    assert COMPLETE_TOKEN in result.events[0].text


def test_codex_provider_prefers_final_message_file_over_plain_stdout(
    tmp_path,
) -> None:
    final_output_path = tmp_path / "codex-last-message.md"
    final_message_text = "Final message file wins.\n<promise>COMPLETE</promise>"
    plain_stdout_text = "Plain stdout should not win.\n<promise>COMPLETE</promise>"
    final_output_path.write_text(
        final_message_text,
        encoding="utf-8",
    )
    sandbox_handle = FakeCodexSandboxHandle(
        CommandResult(
            stdout=plain_stdout_text,
            stderr="",
            exit_code=0,
        )
    )
    provider = CodexProvider(
        sandbox_handle=sandbox_handle,
        codex_command="codex",
        worktree_path=tmp_path,
        final_output_path=final_output_path,
    )

    result = provider.i_agent_provider_run("Fix issue #42")

    assert result.error is None
    assert result.output == final_message_text
    assert result.output != plain_stdout_text
    assert any(
        event.event_type == "final_message_file"
        and event.normalized_type == NORMALIZED_EVENT_TYPE_TEXT
        and event.text == final_message_text
        for event in result.events
    )


def test_codex_provider_plain_stdout_completion_reaches_orchestrator(
    tmp_path,
) -> None:
    sandbox_handle = FakeCodexSandboxHandle(
        CommandResult(
            stdout="Plain stdout result.\n<promise>COMPLETE</promise>",
            stderr="",
            exit_code=0,
        )
    )
    provider = CodexProvider(
        sandbox_handle=sandbox_handle,
        codex_command="codex",
        worktree_path=tmp_path,
        final_output_path=tmp_path / "missing-codex-last-message.md",
    )

    result = i_orchestrator_run(
        provider,
        "Fix issue #42",
        max_iterations=1,
    )

    assert result.completed is True
    assert result.final_output == "Plain stdout result.\n<promise>COMPLETE</promise>"
    assert COMPLETE_TOKEN in result.final_output
    assert result.error is None


def test_codex_provider_final_message_file_completion_reaches_orchestrator(
    tmp_path,
) -> None:
    final_output_path = tmp_path / "codex-last-message.md"
    final_message_text = "Final message from file.\n<promise>COMPLETE</promise>"
    final_output_path.write_text(
        final_message_text,
        encoding="utf-8",
    )
    sandbox_handle = FakeCodexSandboxHandle(
        CommandResult(
            stdout="Plain stdout without completion.",
            stderr="",
            exit_code=0,
        )
    )
    provider = CodexProvider(
        sandbox_handle=sandbox_handle,
        codex_command="codex",
        worktree_path=tmp_path,
        final_output_path=final_output_path,
    )

    result = i_orchestrator_run(
        provider,
        "Fix issue #42",
        max_iterations=1,
    )

    assert result.completed is True
    assert result.final_output == final_message_text
    assert COMPLETE_TOKEN in result.final_output
    assert result.error is None


def test_codex_provider_keeps_events_when_final_output_file_is_used(
    tmp_path,
) -> None:
    final_output_path = tmp_path / "codex-last-message.md"
    final_message_text = "Final message from file.\n<promise>COMPLETE</promise>"
    final_output_path.write_text(
        final_message_text,
        encoding="utf-8",
    )
    stdout = json.dumps({"type": "turn.completed"}) + "\n"
    sandbox_handle = FakeCodexSandboxHandle(
        CommandResult(
            stdout=stdout,
            stderr="",
            exit_code=0,
        )
    )
    provider = CodexProvider(
        sandbox_handle=sandbox_handle,
        codex_command="codex",
        worktree_path=tmp_path,
        final_output_path=final_output_path,
    )

    result = provider.i_agent_provider_run("Fix issue #41")

    assert result.error is None
    assert result.output == final_message_text
    assert len(result.events) == 2
    assert result.events[0].event_type == "turn.completed"
    assert result.events[1].event_type == "final_message_file"
    assert result.events[1].normalized_type == NORMALIZED_EVENT_TYPE_TEXT
    assert result.events[1].text == final_message_text


def test_codex_provider_normalizes_final_message_file_into_text_event(
    tmp_path,
) -> None:
    final_output_path = tmp_path / "codex-last-message.md"
    final_message_text = "Normalized final message file.\n<promise>COMPLETE</promise>"
    final_output_path.write_text(
        final_message_text,
        encoding="utf-8",
    )
    sandbox_handle = FakeCodexSandboxHandle(
        CommandResult(
            stdout="Unrelated stdout text.",
            stderr="",
            exit_code=0,
        )
    )
    provider = CodexProvider(
        sandbox_handle=sandbox_handle,
        codex_command="codex",
        worktree_path=tmp_path,
        final_output_path=final_output_path,
    )

    result = provider.i_agent_provider_run("Fix issue #67")

    assert result.error is None
    assert result.output == final_message_text
    assert any(
        event.event_type == "final_message_file"
        and event.normalized_type == NORMALIZED_EVENT_TYPE_TEXT
        and event.text == final_message_text
        for event in result.events
    )


def test_codex_provider_returns_normalized_error_event_from_jsonl(tmp_path) -> None:
    stdout = (
        json.dumps(
            {
                "type": "error",
                "thread_id": "thread_041",
                "error": {
                    "message": "Codex JSONL failure.",
                },
            }
        )
        + "\n"
    )
    sandbox_handle = FakeCodexSandboxHandle(
        CommandResult(
            stdout=stdout,
            stderr="",
            exit_code=2,
        )
    )
    provider = CodexProvider(
        sandbox_handle=sandbox_handle,
        codex_command="codex",
        worktree_path=tmp_path,
        final_output_path=tmp_path / "codex-last-message.md",
    )

    result = provider.i_agent_provider_run("Fix issue #41")

    assert result.output == stdout
    assert result.error == "Codex JSONL failure."
    assert len(result.events) == 1
    assert result.events[0].event_type == "error"
    assert result.events[0].normalized_type == NORMALIZED_EVENT_TYPE_ERROR
    assert result.events[0].text == "Codex JSONL failure."
    assert result.events[0].session_id == "thread_041"


def test_codex_provider_uses_output_last_message_file_when_jsonl_has_no_final_text(
    tmp_path,
) -> None:
    final_output_path = tmp_path / "codex-last-message.md"
    final_output_path.write_text(
        "Final message from file.\n<promise>COMPLETE</promise>",
        encoding="utf-8",
    )
    stdout = json.dumps({"type": "turn.completed"}) + "\n"
    sandbox_handle = FakeCodexSandboxHandle(
        CommandResult(
            stdout=stdout,
            stderr="",
            exit_code=0,
        )
    )
    provider = CodexProvider(
        sandbox_handle=sandbox_handle,
        codex_command="codex",
        worktree_path=tmp_path,
        final_output_path=final_output_path,
    )

    result = provider.i_agent_provider_run("Fix issue #37")

    assert result.error is None
    assert result.output == "Final message from file.\n<promise>COMPLETE</promise>"


def test_codex_provider_falls_back_to_plain_stdout(tmp_path) -> None:
    sandbox_handle = FakeCodexSandboxHandle(
        CommandResult(
            stdout="Plain stdout result.\n<promise>COMPLETE</promise>",
            stderr="",
            exit_code=0,
        )
    )
    provider = CodexProvider(
        sandbox_handle=sandbox_handle,
        codex_command="codex",
        worktree_path=tmp_path,
        final_output_path=tmp_path / "missing-codex-last-message.md",
    )

    result = provider.i_agent_provider_run("Fix issue #37")

    assert result.error is None
    assert result.output == "Plain stdout result.\n<promise>COMPLETE</promise>"


def test_codex_provider_stdout_fallback_exposes_command_result_data(tmp_path) -> None:
    missing_final_output_path = tmp_path / "missing-codex-last-message.md"
    stdout_text = "Plain stdout result.\n<promise>COMPLETE</promise>"
    stderr_text = "codex warning: partial diagnostic"
    sandbox_handle = FakeCodexSandboxHandle(
        CommandResult(
            stdout=stdout_text,
            stderr=stderr_text,
            exit_code=0,
        )
    )
    provider = CodexProvider(
        sandbox_handle=sandbox_handle,
        codex_command="codex",
        worktree_path=tmp_path,
        final_output_path=missing_final_output_path,
    )

    result = provider.i_agent_provider_run("Fix issue #69")

    assert result.error is None
    assert result.output == stdout_text
    assert COMPLETE_TOKEN in result.output
    assert result.stdout == stdout_text
    assert result.stderr == stderr_text
    assert result.exit_code == 0
    assert stderr_text in result.diagnostics
    assert stderr_text not in result.output
    assert len(result.events) == 1
    assert result.events[0].event_type == "plain.stdout"
    assert result.events[0].normalized_type == NORMALIZED_EVENT_TYPE_TEXT


def test_codex_provider_does_not_treat_stderr_as_completion_output(tmp_path) -> None:
    stderr_text = f"stderr-only diagnostic {COMPLETE_TOKEN}"
    sandbox_handle = FakeCodexSandboxHandle(
        CommandResult(
            stdout="",
            stderr=stderr_text,
            exit_code=0,
        )
    )
    provider = CodexProvider(
        sandbox_handle=sandbox_handle,
        codex_command="codex",
        worktree_path=tmp_path,
        final_output_path=tmp_path / "missing-codex-last-message.md",
    )

    result = provider.i_agent_provider_run("Fix issue #69")

    assert result.error is None
    assert result.output == ""
    assert COMPLETE_TOKEN not in result.output
    assert result.stdout == ""
    assert result.stderr == stderr_text
    assert COMPLETE_TOKEN in result.diagnostics
    assert all(event.event_type != "plain.stdout" for event in result.events)


def test_codex_provider_uses_stdout_not_stderr_when_jsonl_is_missing(tmp_path) -> None:
    stdout_text = "Plain stdout fallback wins.\n<promise>COMPLETE</promise>"
    stderr_text = "stderr diagnostic should not become output"
    sandbox_handle = FakeCodexSandboxHandle(
        CommandResult(
            stdout=stdout_text,
            stderr=stderr_text,
            exit_code=0,
        )
    )
    provider = CodexProvider(
        sandbox_handle=sandbox_handle,
        codex_command="codex",
        worktree_path=tmp_path,
        final_output_path=tmp_path / "missing-codex-last-message.md",
    )

    result = provider.i_agent_provider_run("Fix issue #69")

    assert result.error is None
    assert result.output == stdout_text
    assert result.output != stderr_text
    assert result.stderr == stderr_text
    assert stderr_text in result.diagnostics


def test_codex_provider_preserves_diagnostics_when_nonzero_exit_has_stdout_completion(
    tmp_path,
) -> None:
    stdout_text = "Plain stdout says complete.\n<promise>COMPLETE</promise>"
    stderr_text = "codex failed after partial output"
    nonzero_exit_code = 5
    sandbox_handle = FakeCodexSandboxHandle(
        CommandResult(
            stdout=stdout_text,
            stderr=stderr_text,
            exit_code=nonzero_exit_code,
        )
    )
    provider = CodexProvider(
        sandbox_handle=sandbox_handle,
        codex_command="codex",
        worktree_path=tmp_path,
        final_output_path=tmp_path / "missing-codex-last-message.md",
    )

    result = provider.i_agent_provider_run("Fix issue #69")

    assert result.output == stdout_text
    assert result.error == stderr_text
    assert result.stdout == stdout_text
    assert result.stderr == stderr_text
    assert result.exit_code == nonzero_exit_code
    assert stderr_text in result.diagnostics
    assert f"Exit code: {nonzero_exit_code}." in result.diagnostics


def test_codex_provider_returns_error_on_nonzero_exit(tmp_path) -> None:
    sandbox_handle = FakeCodexSandboxHandle(
        CommandResult(
            stdout="",
            stderr="codex failed",
            exit_code=7,
        )
    )
    provider = CodexProvider(
        sandbox_handle=sandbox_handle,
        codex_command="codex",
        worktree_path=tmp_path,
        final_output_path=tmp_path / "codex-last-message.md",
    )

    result = provider.i_agent_provider_run("Fix issue #37")

    assert result.output == ""
    assert result.error == "codex failed"
    assert provider.prompts == ["Fix issue #37"]
    assert provider.run_count == 1


def test_codex_provider_represents_mcp_tool_call_like_event(tmp_path) -> None:
    stdout = (
        json.dumps(
            {
                "type": "item.started",
                "item": {
                    "type": "mcp_tool_call",
                    "status": "in_progress",
                    "name": "list_files",
                },
            }
        )
        + "\n"
    )
    sandbox_handle = FakeCodexSandboxHandle(
        CommandResult(
            stdout=stdout,
            stderr="",
            exit_code=0,
        )
    )
    provider = CodexProvider(
        sandbox_handle=sandbox_handle,
        codex_command="codex",
        worktree_path=tmp_path,
        final_output_path=tmp_path / "codex-last-message.md",
    )

    result = provider.i_agent_provider_run("Fix issue #43")

    assert result.error is None
    assert len(result.events) == 1
    assert result.events[0].event_type == "item.started"
    assert result.events[0].item_type == "mcp_tool_call"
    assert result.events[0].normalized_type == NORMALIZED_EVENT_TYPE_TOOL_CALL


def test_agent_provider_create_builds_fake_provider_for_mock(tmp_path) -> None:
    sandbox_handle = FakeSandboxHandle(
        CommandResult(
            stdout="Fake test agent completed.\n<promise>COMPLETE</promise>\n",
            stderr="",
            exit_code=0,
        )
    )

    provider = i_agent_provider_create(
        provider_name="mock",
        sandbox_handle=sandbox_handle,
        worktree_path=tmp_path,
    )

    assert isinstance(provider, FakeTestAgentProvider)


def test_agent_provider_create_builds_codex_provider_for_codex(tmp_path) -> None:
    sandbox_handle = FakeCodexSandboxHandle(
        CommandResult(
            stdout="Codex completed.\n<promise>COMPLETE</promise>",
            stderr="",
            exit_code=0,
        )
    )

    provider = i_agent_provider_create(
        provider_name="codex",
        sandbox_handle=sandbox_handle,
        worktree_path=tmp_path,
        codex_command="codex",
    )

    assert isinstance(provider, CodexProvider)


def test_agent_provider_create_rejects_unknown_provider(tmp_path) -> None:
    sandbox_handle = FakeSandboxHandle(
        CommandResult(
            stdout="",
            stderr="",
            exit_code=0,
        )
    )

    with pytest.raises(ValueError, match="Unsupported agent provider") as error_info:
        i_agent_provider_create(
            provider_name="unknown",
            sandbox_handle=sandbox_handle,
            worktree_path=tmp_path,
        )

    assert "mock" in str(error_info.value)
    assert "codex" in str(error_info.value)


def test_agent_provider_create_fake_provider_runs_through_sandbox(tmp_path) -> None:
    sandbox_handle = FakeSandboxHandle(
        CommandResult(
            stdout="Fake test agent completed.\n<promise>COMPLETE</promise>\n",
            stderr="",
            exit_code=0,
        )
    )
    provider = i_agent_provider_create(
        provider_name="mock",
        sandbox_handle=sandbox_handle,
        worktree_path=tmp_path,
    )

    result = provider.i_agent_provider_run("Fix issue #38")

    assert result.error is None
    assert COMPLETE_TOKEN in result.output
    assert len(sandbox_handle.commands) == 1


def test_agent_provider_create_codex_keeps_prompt_out_of_command_args(tmp_path) -> None:
    sandbox_handle = FakeCodexSandboxHandle(
        CommandResult(
            stdout="Codex done\n<promise>COMPLETE</promise>",
            stderr="",
            exit_code=0,
        )
    )
    provider = i_agent_provider_create(
        provider_name="codex",
        sandbox_handle=sandbox_handle,
        worktree_path=tmp_path,
        codex_command="codex",
    )
    prompt = "Issue body with shell-looking text !`echo unsafe` && whoami"

    result = provider.i_agent_provider_run(prompt)

    command = sandbox_handle.calls[0]["command"]
    command_text = " ".join(command)

    assert result.error is None
    assert sandbox_handle.calls[0]["stdin_text"] == prompt
    assert prompt not in command
    assert prompt not in command_text


def test_codex_provider_uses_jsonl_error_when_stderr_is_empty(tmp_path) -> None:
    stdout = (
        json.dumps(
            {
                "type": "error",
                "error": {
                    "message": "Codex JSONL failure.",
                },
            }
        )
        + "\n"
    )
    sandbox_handle = FakeCodexSandboxHandle(
        CommandResult(
            stdout=stdout,
            stderr="",
            exit_code=2,
        )
    )
    provider = CodexProvider(
        sandbox_handle=sandbox_handle,
        codex_command="codex",
        worktree_path=tmp_path,
        final_output_path=tmp_path / "codex-last-message.md",
    )

    result = provider.i_agent_provider_run("Fix issue #39")

    assert result.output == stdout
    assert result.error == "Codex JSONL failure."


def test_codex_provider_uses_output_last_message_file_as_error_when_command_fails(
    tmp_path,
) -> None:
    final_output_path = tmp_path / "codex-last-message.md"
    final_output_path.write_text(
        "Failure details from Codex final message file.",
        encoding="utf-8",
    )
    stdout = json.dumps({"type": "thread.started"}) + "\n"
    sandbox_handle = FakeCodexSandboxHandle(
        CommandResult(
            stdout=stdout,
            stderr="",
            exit_code=4,
        )
    )
    provider = CodexProvider(
        sandbox_handle=sandbox_handle,
        codex_command="codex",
        worktree_path=tmp_path,
        final_output_path=final_output_path,
    )

    result = provider.i_agent_provider_run("Fix issue #39")

    assert result.output == "Failure details from Codex final message file."
    assert result.error == "Failure details from Codex final message file."


def test_codex_provider_uses_plain_stdout_as_error_when_stderr_is_empty(
    tmp_path,
) -> None:
    sandbox_handle = FakeCodexSandboxHandle(
        CommandResult(
            stdout="Plain Codex failure output.",
            stderr="",
            exit_code=3,
        )
    )
    provider = CodexProvider(
        sandbox_handle=sandbox_handle,
        codex_command="codex",
        worktree_path=tmp_path,
        final_output_path=tmp_path / "codex-last-message.md",
    )

    result = provider.i_agent_provider_run("Fix issue #39")

    assert result.output == "Plain Codex failure output."
    assert result.error == "Plain Codex failure output."


def test_codex_provider_uses_exit_code_error_when_no_failure_output_exists(
    tmp_path,
) -> None:
    sandbox_handle = FakeCodexSandboxHandle(
        CommandResult(
            stdout="",
            stderr="",
            exit_code=9,
        )
    )
    provider = CodexProvider(
        sandbox_handle=sandbox_handle,
        codex_command="codex",
        worktree_path=tmp_path,
        final_output_path=tmp_path / "codex-last-message.md",
    )

    result = provider.i_agent_provider_run("Fix issue #39")

    assert result.output == ""
    assert result.error == "Codex exited with code 9."


def test_agent_provider_create_rejects_empty_codex_command(tmp_path) -> None:
    sandbox_handle = FakeCodexSandboxHandle(
        CommandResult(
            stdout="",
            stderr="",
            exit_code=0,
        )
    )

    with pytest.raises(ValueError, match="codex_command cannot be empty"):
        i_agent_provider_create(
            provider_name="codex",
            sandbox_handle=sandbox_handle,
            worktree_path=tmp_path,
            codex_command="   ",
        )


def _issue_044_windows_special_character_prompt() -> str:
    issue_body_lines = [
        "# Issue 044 — Add CodexProvider Windows special-character tests",
        "",
        "## Labels",
        "tracer bullet, codex, windows, security",
        "",
        "## Windows paths",
        r"Trusted-looking project path: C:\Users\ME\Documents\Python\2026\Projects\ai_coder",
        r"Untrusted issue path marker: C:\Users\ME\Documents\Python\2026\Projects\ISSUE_044_UNTRUSTED_PATH_MARKER",
        r"Untrusted issue path with spaces: C:\Users\ME\Documents\Python\2026\Projects\ai coder with spaces\ISSUE_044_PATH_WITH_SPACES_MARKER",
        "",
        'Issue title marker: "UNIQUE_ISSUE_044_QUOTED_TITLE_MARKER"',
        "Single quoted marker: 'UNIQUE_ISSUE_044_SINGLE_QUOTED_LABEL_MARKER'",
        'Double quoted marker: "UNIQUE_ISSUE_044_DOUBLE_QUOTED_PHRASE_MARKER"',
        "PowerShell marker: $(Write-Output unsafe)",
        "Remove marker: ; Remove-Item -Recurse",
        "Command chaining marker: && whoami",
        "Environment marker: %PATH%",
        "Operator marker: ^ | & < >",
        "Backtick marker: `echo unsafe`",
        "Unicode marker: RALPH 🚀 café naïve résumé 中文",
        "",
    ]

    repeated_body = "\n".join(
        f"Issue 044 long body line {line_number}: keep Windows issue text out of command args."
        for line_number in range(1, 301)
    )

    return "\n".join(issue_body_lines) + "\n" + repeated_body


def test_codex_provider_keeps_windows_paths_in_stdin_not_command_args(tmp_path) -> None:
    sandbox_handle = FakeCodexSandboxHandle(
        CommandResult(
            stdout="Codex completed\n<promise>COMPLETE</promise>",
            stderr="",
            exit_code=0,
        )
    )
    provider_worktree_path = r"C:\Users\ME\Documents\Python\2026\Projects\ai_coder"
    issue_path_marker = (
        r"C:\Users\ME\Documents\Python\2026\Projects\ISSUE_044_UNTRUSTED_PATH_MARKER"
    )
    issue_path_with_spaces_marker = r"C:\Users\ME\Documents\Python\2026\Projects\ai coder with spaces\ISSUE_044_PATH_WITH_SPACES_MARKER"
    final_output_path = tmp_path / "codex-last-message.md"
    provider = CodexProvider(
        sandbox_handle=sandbox_handle,
        codex_command="codex",
        worktree_path=provider_worktree_path,
        final_output_path=final_output_path,
    )

    prompt = _issue_044_windows_special_character_prompt()

    result = provider.i_agent_provider_run(prompt)

    command = sandbox_handle.calls[0]["command"]
    command_text = " ".join(command)

    assert result.error is None
    assert sandbox_handle.calls[0]["stdin_text"] == prompt
    assert provider.prompts == [prompt]
    assert provider.run_count == 1
    assert str(provider_worktree_path) in command
    assert issue_path_marker in prompt
    assert issue_path_with_spaces_marker in prompt
    assert issue_path_marker not in command
    assert issue_path_marker not in command_text
    assert issue_path_with_spaces_marker not in command
    assert issue_path_with_spaces_marker not in command_text
    assert prompt not in command
    assert prompt not in command_text
    assert command[-1] == "-"


def test_codex_provider_keeps_quotes_and_shell_like_text_inert(tmp_path) -> None:
    sandbox_handle = FakeCodexSandboxHandle(
        CommandResult(
            stdout="Codex completed\n<promise>COMPLETE</promise>",
            stderr="",
            exit_code=0,
        )
    )
    provider = CodexProvider(
        sandbox_handle=sandbox_handle,
        codex_command="codex",
        worktree_path=tmp_path,
        final_output_path=tmp_path / "codex-last-message.md",
    )
    dangerous_markers = (
        "$(Write-Output unsafe)",
        "&& whoami",
        "; Remove-Item -Recurse",
        "`echo unsafe`",
        "%PATH%",
        "^ | & < >",
        '"quoted title"',
        "'single quoted label'",
    )
    prompt = "\n".join(
        (
            "# Issue 044 shell-like inert text test",
            "Title: " + dangerous_markers[6],
            "Label: " + dangerous_markers[7],
            "Body markers:",
            *dangerous_markers,
        )
    )

    result = provider.i_agent_provider_run(prompt)

    command = sandbox_handle.calls[0]["command"]
    command_text = " ".join(command)
    stdin_text = sandbox_handle.calls[0]["stdin_text"]

    assert result.error is None
    assert stdin_text == prompt
    for marker in dangerous_markers:
        assert marker in stdin_text
        assert marker not in command
        assert marker not in command_text
    assert prompt not in command
    assert prompt not in command_text
    assert command[-1] == "-"


def test_codex_provider_keeps_long_issue_title_body_and_labels_out_of_command_args(
    tmp_path,
) -> None:
    sandbox_handle = FakeCodexSandboxHandle(
        CommandResult(
            stdout="Codex completed\n<promise>COMPLETE</promise>",
            stderr="",
            exit_code=0,
        )
    )
    provider = CodexProvider(
        sandbox_handle=sandbox_handle,
        codex_command="codex",
        worktree_path=tmp_path,
        final_output_path=tmp_path / "codex-last-message.md",
    )
    title_marker = "UNIQUE_ISSUE_044_TITLE_MARKER"
    body_marker = "UNIQUE_ISSUE_044_BODY_MARKER"
    label_marker = "UNIQUE_ISSUE_044_LABEL_MARKER"
    long_body = "\n".join(
        f"Issue 044 long body line {line_number}: {body_marker} stays inert."
        for line_number in range(1, 301)
    )
    prompt = (
        "# GitHub Issue\n\n"
        f'Title: {title_marker} "quoted issue title"\n'
        f"Labels: tracer bullet, codex, windows, security, {label_marker}\n\n"
        f"{body_marker}\n"
        f"{long_body}"
    )

    result = provider.i_agent_provider_run(prompt)

    command = sandbox_handle.calls[0]["command"]
    command_text = " ".join(command)
    stdin_text = sandbox_handle.calls[0]["stdin_text"]

    assert result.error is None
    assert stdin_text == prompt
    assert title_marker in stdin_text
    assert body_marker in stdin_text
    assert label_marker in stdin_text
    assert title_marker not in command_text
    assert body_marker not in command_text
    assert label_marker not in command_text
    assert "Issue 044 long body line 275" in stdin_text
    assert "Issue 044 long body line 275" not in command_text
    assert prompt not in command
    assert prompt not in command_text
    assert command[-1] == "-"


def test_agent_provider_create_codex_keeps_windows_special_character_prompt_in_stdin(
    tmp_path,
) -> None:
    sandbox_handle = FakeCodexSandboxHandle(
        CommandResult(
            stdout="Codex completed\n<promise>COMPLETE</promise>",
            stderr="",
            exit_code=0,
        )
    )
    provider = i_agent_provider_create(
        provider_name="codex",
        sandbox_handle=sandbox_handle,
        worktree_path=tmp_path,
        codex_command="codex",
        final_output_path=tmp_path / "codex-last-message.md",
    )
    prompt = _issue_044_windows_special_character_prompt()
    dangerous_marker = "$(Write-Output unsafe)"

    result = provider.i_agent_provider_run(prompt)

    command = sandbox_handle.calls[0]["command"]
    command_text = " ".join(command)

    assert result.error is None
    assert sandbox_handle.calls[0]["stdin_text"] == prompt
    assert dangerous_marker in prompt
    assert prompt not in command
    assert prompt not in command_text
    assert dangerous_marker not in command
    assert dangerous_marker not in command_text
    assert command[-1] == "-"


def _issue_040_large_codex_prompt() -> str:
    issue_body_lines = [
        "# Issue 040 — Add CodexProvider prompt passing for long prompts",
        "",
        "## Labels",
        "tracer bullet, codex, windows",
        "",
        "## Full GitHub issue body",
        "This prompt simulates a large GitHub issue body.",
        r"Windows path: C:\Users\ME\Documents\Python\2026\Projects\ai_coder",
        r"Shell-looking text: !`echo unsafe` $(Write-Output " "unsafe" ") && whoami",
        r"More shell-looking text: echo %PATH% ^ | & < > "
        "quoted text"
        " 'single quoted text'",
        "Unicode text: RALPH 🚀 café naïve résumé 中文",
        "",
    ]

    repeated_body = "\n".join(
        f"Large issue body line {line_number}: keep this text out of command args."
        for line_number in range(1, 301)
    )

    return "\n".join(issue_body_lines) + "\n" + repeated_body


def test_codex_provider_passes_large_prompt_through_stdin_only(tmp_path) -> None:
    sandbox_handle = FakeCodexSandboxHandle(
        CommandResult(
            stdout="Codex done\n<promise>COMPLETE</promise>",
            stderr="",
            exit_code=0,
        )
    )
    provider = CodexProvider(
        sandbox_handle=sandbox_handle,
        codex_command="codex",
        worktree_path=tmp_path,
        final_output_path=tmp_path / "codex-last-message.md",
    )

    prompt = _issue_040_large_codex_prompt()

    result = provider.i_agent_provider_run(prompt)

    command = sandbox_handle.calls[0]["command"]
    command_text = " ".join(command)

    assert result.error is None
    assert sandbox_handle.calls[0]["stdin_text"] == prompt
    assert provider.prompts == [prompt]
    assert provider.run_count == 1
    assert prompt not in command
    assert prompt not in command_text
    assert "Large issue body line 250" not in command_text
    assert r"C:\Users\ME\Documents\Python\2026\Projects\ai_coder" not in command_text
    assert command[-1] == "-"


def test_codex_provider_keeps_full_issue_body_out_of_command_args(tmp_path) -> None:
    sandbox_handle = FakeCodexSandboxHandle(
        CommandResult(
            stdout="Codex completed\n<promise>COMPLETE</promise>",
            stderr="",
            exit_code=0,
        )
    )
    final_output_path = tmp_path / "codex-last-message.md"
    provider = CodexProvider(
        sandbox_handle=sandbox_handle,
        codex_command="codex",
        worktree_path=tmp_path,
        final_output_path=final_output_path,
    )

    issue_body_marker = "UNIQUE_ISSUE_040_BODY_MARKER_DO_NOT_LOG_OR_ARG"
    prompt = (
        "# GitHub Issue\n\n"
        "Title: Add CodexProvider prompt passing for long prompts\n"
        "Labels: tracer bullet, codex\n\n"
        f"{issue_body_marker}\n" + _issue_040_large_codex_prompt()
    )

    result = provider.i_agent_provider_run(prompt)

    command = sandbox_handle.calls[0]["command"]
    command_text = " ".join(command)

    assert result.error is None
    assert sandbox_handle.calls[0]["stdin_text"] == prompt
    assert command == [
        "codex",
        "exec",
        "--cd",
        str(tmp_path),
        "--sandbox",
        "workspace-write",
        "--color",
        "never",
        "--json",
        "--output-last-message",
        str(final_output_path),
        "-",
    ]
    assert prompt not in command
    assert prompt not in command_text
    assert issue_body_marker not in command_text


def test_codex_provider_does_not_log_raw_full_prompt_by_default(
    tmp_path,
    caplog,
) -> None:
    sandbox_handle = FakeCodexSandboxHandle(
        CommandResult(
            stdout="Codex completed\n<promise>COMPLETE</promise>",
            stderr="",
            exit_code=0,
        )
    )
    provider = CodexProvider(
        sandbox_handle=sandbox_handle,
        codex_command="codex",
        worktree_path=tmp_path,
        final_output_path=tmp_path / "codex-last-message.md",
    )

    prompt_marker = "UNIQUE_RAW_PROMPT_MARKER_ISSUE_040_SHOULD_NOT_BE_LOGGED"
    prompt = prompt_marker + "\n" + _issue_040_large_codex_prompt()

    with caplog.at_level("INFO"):
        result = provider.i_agent_provider_run(prompt)

    assert result.error is None
    assert sandbox_handle.calls[0]["stdin_text"] == prompt
    assert prompt not in caplog.text
    assert prompt_marker not in caplog.text


def test_codex_provider_does_not_log_raw_full_prompt_when_final_message_file_wins(
    tmp_path,
    caplog,
) -> None:
    final_output_path = tmp_path / "codex-last-message.md"
    final_message_text = "Final message from file.\n<promise>COMPLETE</promise>"
    final_output_path.write_text(
        final_message_text,
        encoding="utf-8",
    )

    sandbox_handle = FakeCodexSandboxHandle(
        CommandResult(
            stdout="Plain stdout should not win.\n<promise>COMPLETE</promise>",
            stderr="",
            exit_code=0,
        )
    )
    provider = CodexProvider(
        sandbox_handle=sandbox_handle,
        codex_command="codex",
        worktree_path=tmp_path,
        final_output_path=final_output_path,
    )

    prompt_marker = "UNIQUE_RAW_PROMPT_MARKER_ISSUE_067_SHOULD_NOT_BE_LOGGED"
    prompt = (
        "# GitHub Issue\n\n"
        "Title: Normalize Codex final message file output\n"
        "Labels: tracer bullet, codex\n\n"
        f"{prompt_marker}\n" + _issue_040_large_codex_prompt()
    )

    with caplog.at_level("INFO"):
        result = provider.i_agent_provider_run(prompt)

    command = sandbox_handle.calls[0]["command"]
    command_text = " ".join(command)

    assert result.error is None
    assert result.output == final_message_text
    assert sandbox_handle.calls[0]["stdin_text"] == prompt
    assert prompt not in command
    assert prompt not in command_text
    assert prompt_marker not in command_text
    assert prompt not in caplog.text
    assert prompt_marker not in caplog.text


def test_codex_provider_nonzero_exit_fails_even_when_final_message_has_complete_token(
    tmp_path,
) -> None:
    final_output_path = tmp_path / "codex-last-message.md"
    final_message_text = f"Final message says complete.\n{COMPLETE_TOKEN}"
    stdout_text = "Codex stdout before crash."
    stderr_text = "Codex crashed after partial output."
    nonzero_exit_code = 2

    final_output_path.write_text(
        final_message_text,
        encoding="utf-8",
    )

    sandbox_handle = FakeCodexSandboxHandle(
        CommandResult(
            stdout=stdout_text,
            stderr=stderr_text,
            exit_code=nonzero_exit_code,
        )
    )
    provider = CodexProvider(
        sandbox_handle=sandbox_handle,
        codex_command="codex",
        worktree_path=tmp_path,
        final_output_path=final_output_path,
    )

    result = provider.i_agent_provider_run("Fix issue #71")

    assert result.error is not None
    assert result.error == stderr_text
    assert result.output == final_message_text
    assert COMPLETE_TOKEN in result.output
    assert result.stdout == stdout_text
    assert result.stderr == stderr_text
    assert result.exit_code == nonzero_exit_code
    assert stderr_text in result.diagnostics
    assert "Exit code: 2." in result.diagnostics


def test_codex_provider_nonzero_exit_fails_even_when_jsonl_has_complete_token(
    tmp_path,
) -> None:
    jsonl_message_text = f"Structured JSONL says complete.\n{COMPLETE_TOKEN}"
    stdout_text = (
        json.dumps(
            {
                "type": "item.completed",
                "item": {
                    "type": "agent_message",
                    "status": "completed",
                    "text": jsonl_message_text,
                },
            }
        )
        + "\n"
    )
    stderr_text = "Codex crashed after structured output."
    nonzero_exit_code = 3

    sandbox_handle = FakeCodexSandboxHandle(
        CommandResult(
            stdout=stdout_text,
            stderr=stderr_text,
            exit_code=nonzero_exit_code,
        )
    )
    provider = CodexProvider(
        sandbox_handle=sandbox_handle,
        codex_command="codex",
        worktree_path=tmp_path,
        final_output_path=tmp_path / "missing-codex-last-message.md",
    )

    result = provider.i_agent_provider_run("Fix issue #71")

    assert result.error is not None
    assert result.error == stderr_text
    assert result.output == jsonl_message_text
    assert COMPLETE_TOKEN in result.output
    assert result.stdout == stdout_text
    assert result.stderr == stderr_text
    assert result.exit_code == nonzero_exit_code
    assert stderr_text in result.diagnostics
    assert "Exit code: 3." in result.diagnostics
    assert any(
        event.event_type == "item.completed"
        and event.normalized_type == NORMALIZED_EVENT_TYPE_TEXT
        and event.text == jsonl_message_text
        for event in result.events
    )


def test_codex_provider_nonzero_exit_completion_does_not_reach_orchestrator_success(
    tmp_path,
) -> None:
    stdout_text = f"Plain stdout says complete.\n{COMPLETE_TOKEN}"
    stderr_text = "Codex failed after partial completion output."

    sandbox_handle = FakeCodexSandboxHandle(
        CommandResult(
            stdout=stdout_text,
            stderr=stderr_text,
            exit_code=4,
        )
    )
    provider = CodexProvider(
        sandbox_handle=sandbox_handle,
        codex_command="codex",
        worktree_path=tmp_path,
        final_output_path=tmp_path / "missing-codex-last-message.md",
    )

    result = i_orchestrator_run(
        provider,
        "Fix issue #71",
        max_iterations=1,
    )

    assert result.completed is False
    assert result.error is not None
    assert stderr_text in result.error
    assert result.outputs == ()
    assert result.final_output == ""


def test_agent_provider_create_codex_passes_large_prompt_through_stdin(
    tmp_path,
) -> None:
    sandbox_handle = FakeCodexSandboxHandle(
        CommandResult(
            stdout="Codex completed\n<promise>COMPLETE</promise>",
            stderr="",
            exit_code=0,
        )
    )
    provider = i_agent_provider_create(
        provider_name="codex",
        sandbox_handle=sandbox_handle,
        worktree_path=tmp_path,
        codex_command="codex",
        final_output_path=tmp_path / "codex-last-message.md",
    )

    prompt = _issue_040_large_codex_prompt()

    result = provider.i_agent_provider_run(prompt)

    command = sandbox_handle.calls[0]["command"]
    command_text = " ".join(command)

    assert result.error is None
    assert sandbox_handle.calls[0]["stdin_text"] == prompt
    assert prompt not in command
    assert prompt not in command_text
    assert command[-1] == "-"
