from __future__ import annotations

import math
from typing import Any

from aicar_sim.motion_model import (
    get_axis_acceleration_limits,
    get_axis_velocity_limits,
)
from aicar_sim.path_interpolator import calculate_point_distance


def calculate_axis_velocities(
    previous_point: dict[str, Any],
    current_point: dict[str, Any],
    delta_time: float,
) -> dict[str, float]:
    if delta_time <= 0:
        raise ValueError("delta_time must be greater than 0")
    return {
        axis: (float(current_point[f"{axis}_mm"]) - float(previous_point[f"{axis}_mm"])) / delta_time
        for axis in ("x", "y", "z")
    }


def calculate_acceleration(
    previous_velocity: float,
    current_velocity: float,
    delta_time: float,
) -> float:
    if delta_time <= 0:
        raise ValueError("delta_time must be greater than 0")
    return (float(current_velocity) - float(previous_velocity)) / delta_time


def _phase(previous_speed: float, speed: float, point: dict[str, Any]) -> str:
    if point.get("is_transition"):
        return "transition"
    if speed > previous_speed + 1:
        return "accelerate"
    if speed < previous_speed - 1:
        return "decelerate"
    return "cruise"


def parameterize_trajectory(
    points: list[dict[str, Any]],
    motion_model: dict[str, Any],
) -> list[dict[str, Any]]:
    """Assign monotonic timestamps while enforcing axis velocity/acceleration limits."""
    if not points:
        return []

    velocity_limits = get_axis_velocity_limits(motion_model)
    acceleration_limits = get_axis_acceleration_limits(motion_model)
    constraints = motion_model["path_constraints"]
    minimum_dt = float(constraints["minimum_segment_duration_s"])
    transition_scale = float(constraints["transition_velocity_scale"])

    first = dict(points[0])
    first.update(
        {
            "sequence_index": 0,
            "timestamp_s": round(minimum_dt, 6),
            "delta_time_s": round(minimum_dt, 6),
            "velocity_mm_s": 0.0,
            "acceleration_mm_s2": 0.0,
            "velocity_x_mm_s": 0.0,
            "velocity_y_mm_s": 0.0,
            "velocity_z_mm_s": 0.0,
            "motion_phase": "start",
        }
    )
    result = [first]
    previous_axis_velocity = {axis: 0.0 for axis in ("x", "y", "z")}
    previous_speed = 0.0

    for source_point in points[1:]:
        current = dict(source_point)
        previous = result[-1]
        distance = calculate_point_distance(previous, current)
        target_speed = float(current.get("target_speed_mm_s", 200.0))
        if current.get("is_transition") or current.get("state_id") != previous.get("state_id"):
            target_speed *= transition_scale
        target_speed = max(1.0, target_speed)

        deltas = {
            axis: abs(float(current[f"{axis}_mm"]) - float(previous[f"{axis}_mm"]))
            for axis in ("x", "y", "z")
        }
        delta_time = max(
            minimum_dt,
            distance / target_speed if distance > 0 else minimum_dt,
            *(deltas[axis] / velocity_limits[axis] for axis in ("x", "y", "z")),
        )

        axis_velocity = {axis: 0.0 for axis in ("x", "y", "z")}
        axis_acceleration = {axis: 0.0 for axis in ("x", "y", "z")}
        for _ in range(40):
            axis_velocity = calculate_axis_velocities(previous, current, delta_time)
            axis_acceleration = {
                axis: calculate_acceleration(previous_axis_velocity[axis], axis_velocity[axis], delta_time)
                for axis in ("x", "y", "z")
            }
            max_ratio = max(
                abs(axis_acceleration[axis]) / acceleration_limits[axis]
                for axis in ("x", "y", "z")
            )
            if max_ratio <= 1.0 + 1e-9:
                break
            delta_time *= max(1.05, math.sqrt(max_ratio) * 1.02)

        speed = math.sqrt(sum(value**2 for value in axis_velocity.values()))
        acceleration = math.sqrt(sum(value**2 for value in axis_acceleration.values()))
        current.update(
            {
                "sequence_index": len(result),
                "timestamp_s": round(float(previous["timestamp_s"]) + delta_time, 6),
                "delta_time_s": round(delta_time, 6),
                "velocity_mm_s": round(speed, 6),
                "acceleration_mm_s2": round(acceleration, 6),
                "velocity_x_mm_s": round(axis_velocity["x"], 6),
                "velocity_y_mm_s": round(axis_velocity["y"], 6),
                "velocity_z_mm_s": round(axis_velocity["z"], 6),
                "motion_phase": _phase(previous_speed, speed, current),
            }
        )
        result.append(current)
        previous_axis_velocity = axis_velocity
        previous_speed = speed

    last = result[-1]
    stop_delta_time = max(
        minimum_dt,
        *(abs(previous_axis_velocity[axis]) / acceleration_limits[axis] for axis in ("x", "y", "z")),
    )
    stop_acceleration = {
        axis: calculate_acceleration(previous_axis_velocity[axis], 0.0, stop_delta_time)
        for axis in ("x", "y", "z")
    }
    stop = dict(last)
    stop.update(
        {
            "sequence_index": len(result),
            "timestamp_s": round(float(last["timestamp_s"]) + stop_delta_time, 6),
            "delta_time_s": round(stop_delta_time, 6),
            "velocity_mm_s": 0.0,
            "acceleration_mm_s2": round(math.sqrt(sum(value**2 for value in stop_acceleration.values())), 6),
            "velocity_x_mm_s": 0.0,
            "velocity_y_mm_s": 0.0,
            "velocity_z_mm_s": 0.0,
            "motion_phase": "stop",
            "interpolated": True,
        }
    )
    result.append(stop)
    return result
