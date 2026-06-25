"""Shared schemas for vehicle type recognition scaffold."""

from dataclasses import dataclass


@dataclass(frozen=True)
class VehicleTypeResult:
    vehicle_detected: bool
    vehicle_type: str
    confidence: float
    bbox: list[int]
    source_image: str
    timestamp: str

