from ai_coder.display import ConsoleDisplay, SilentDisplay


def test_silent_display_stores_messages_without_printing(capsys) -> None:
    display = SilentDisplay()

    display.i_display_message("hello")

    assert display.messages == ["hello"]
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == ""


def test_console_display_prints_message(capsys) -> None:
    display = ConsoleDisplay()

    display.i_display_message("hello")

    captured = capsys.readouterr()
    assert captured.out == "hello\n"
