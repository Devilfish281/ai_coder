from ai_coder.completion_detector import i_completion_detector_detect


def test_completion_detector_returns_completed_result() -> None:
    result = i_completion_detector_detect(True)

    assert result.completed is True
    assert "detected" in result.message


def test_completion_detector_returns_not_completed_result() -> None:
    result = i_completion_detector_detect(False)

    assert result.completed is False
    assert "did not detect" in result.message
