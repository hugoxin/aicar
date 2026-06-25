"""Safety monitor placeholders."""


def safety_status() -> dict[str, bool]:
    """Return a scaffold safety status without connecting hardware."""
    return {
        "emergency_stop_ok": True,
        "hardware_connected": False,
    }

