"""Shared schemas for aicar_sim scaffold."""

from dataclasses import dataclass


@dataclass(frozen=True)
class VehicleTypeResult:
    vehicle_detected: bool
    vehicle_type: str
    confidence: float
    bbox: list[int]
    source_image: str
    timestamp: str

