"""Wash state machine placeholders."""


class WashStateMachine:
    """Minimal state holder for future wash process logic."""

    def __init__(self) -> None:
        self.state = "idle"

    def current_state(self) -> str:
        return self.state

