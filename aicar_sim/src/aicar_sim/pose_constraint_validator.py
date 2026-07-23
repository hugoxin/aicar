from __future__ import annotations

import math
from typing import Any

from aicar_sim.geometry_math import angle_between, norm, quaternion_angular_distance


def _quat(pose: dict[str, Any]) -> tuple[float, float, float, float]:
    value = pose["orientation_quaternion"]
    return float(value["w"]), float(value["x"]), float(value["y"]), float(value["z"])


def validate_nozzle_poses(poses: list[dict[str, Any]], profile: dict[str, Any]) -> dict[str, Any]:
    invalid = discontinuities = flips = quaternion_invalid = 0
    maximum_step = maximum_incidence = 0.0
    standoffs = []
    issues = []
    previous = None
    for index, pose in enumerate(poses):
        standoff = float(pose["standoff_mm"])
        standoffs.append(standoff)
        normal = tuple(float(pose["surface_normal"][axis]) for axis in ("x", "y", "z"))
        axis = tuple(float(pose["nozzle_axis_world"][axis]) for axis in ("x", "y", "z"))
        quaternion = _quat(pose)
        incidence = angle_between(axis, tuple(-value for value in normal))
        maximum_incidence = max(maximum_incidence, incidence)
        valid = True
        quaternion_norm = math.sqrt(sum(value * value for value in quaternion))
        if abs(quaternion_norm - 1.0) > 1e-6:
            quaternion_invalid += 1
            valid = False
        if incidence > float(profile["orientation"]["maximum_incidence_angle_deg"]) + 1e-6:
            valid = False
        if standoff < float(profile["position"]["hard_minimum_clearance_mm"]) or standoff > float(profile["position"]["maximum_standoff_mm"]):
            valid = False
        if previous is not None:
            step = quaternion_angular_distance(previous, quaternion)
            boundary = pose.get("is_orientation_boundary", False)
            if not boundary:
                maximum_step = max(maximum_step, step)
            if step > float(profile["orientation"]["maximum_orientation_step_deg"]) and not boundary:
                discontinuities += 1
                valid = False
        if not valid:
            invalid += 1
            issues.append({"pose_index": index, "message": "pose constraint failed"})
        previous = quaternion
    return {
        "validation_status": "FAIL" if invalid else "PASS",
        "invalid_pose_count": invalid,
        "pose_discontinuity_count": discontinuities,
        "unresolved_orientation_flip_count": flips,
        "quaternion_invalid_count": quaternion_invalid,
        "maximum_incidence_angle_deg": round(maximum_incidence, 6),
        "maximum_orientation_step_deg": round(maximum_step, 6),
        "minimum_standoff_mm": min(standoffs) if standoffs else 0,
        "maximum_standoff_mm": max(standoffs) if standoffs else 0,
        "issues": issues,
    }
