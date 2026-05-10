from __future__ import annotations


class SilentDisplay:
    def __init__(self) -> None:
        self.messages: list[str] = []

    def i_display_message(self, message: str) -> None:
        self.messages.append(message)


class ConsoleDisplay:
    def i_display_message(self, message: str) -> None:
        print(message)
