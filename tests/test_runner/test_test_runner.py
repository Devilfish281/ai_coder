from ai_coder.test_runner import i_test_runner_run


def test_test_runner_stub_returns_passed_result() -> None:
    result = i_test_runner_run()

    assert result.passed is True
    assert result.command == ("poetry", "run", "pytest")
    assert "stubbed" in result.message
