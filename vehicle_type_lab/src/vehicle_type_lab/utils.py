"""Utility placeholders for vehicle_type_lab."""

from datetime import datetime, timezone


def utc_timestamp() -> str:
    """Return an ISO timestamp for future result exports."""
    return datetime.now(timezone.utc).isoformat()

