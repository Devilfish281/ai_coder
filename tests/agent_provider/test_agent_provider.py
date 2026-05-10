from ai_coder.agent_provider import COMPLETE_TOKEN, AgentResponse, MockAgentProvider


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
