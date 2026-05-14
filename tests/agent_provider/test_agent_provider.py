# tests/agent_provider/test_agent_provider.py
from ai_coder.agent_provider import (
    COMPLETE_TOKEN,
    AgentResponse,
    FakeTestAgentProvider,
    MockAgentProvider,
)
from ai_coder.sandbox_provider import CommandResult


class FakeSandboxHandle:
    def __init__(self, command_result: CommandResult) -> None:
        self.command_result = command_result
        self.commands: list[list[str]] = []

    def i_sandboxhandle_run(self, command: list[str]) -> CommandResult:
        self.commands.append(command)
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
