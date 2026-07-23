from __future__ import annotations

from typing import Any

from aicar_sim.geometry_math import dot, orthonormal_basis, quaternion_normalize, rotation_matrix_to_quaternion, scale, add


def _quaternion_for_normal(normal: tuple[float, float, float]) -> tuple[float, float, float, float]:
    x_axis, y_axis, z_axis = orthonormal_basis(normal)
    matrix = (
        (x_axis[0], y_axis[0], z_axis[0]),
        (x_axis[1], y_axis[1], z_axis[1]),
        (x_axis[2], y_axis[2], z_axis[2]),
    )
    return rotation_matrix_to_quaternion(matrix)


def generate_nozzle_pose(
    surface_point: dict[str, float],
    normal: dict[str, float],
    profile: dict[str, Any],
    previous_quaternion: tuple[float, float, float, float] | None = None,
) -> dict[str, Any]:
    n = (float(normal["x"]), float(normal["y"]), float(normal["z"]))
    point = (float(surface_point["x_mm"]), float(surface_point["y_mm"]), float(surface_point["z_mm"]))
    standoff = float(profile["position"]["preferred_standoff_mm"])
    position = add(point, scale(n, standoff))
    quaternion = _quaternion_for_normal(n)
    if previous_quaternion and dot(quaternion[:3], previous_quaternion[:3]) + quaternion[3] * previous_quaternion[3] < 0:
        quaternion = tuple(-value for value in quaternion)  # type: ignore[assignment]
    quaternion = quaternion_normalize(quaternion)
    return {
        "position": {"x_mm": position[0], "y_mm": position[1], "z_mm": position[2]},
        "orientation_quaternion": {"w": quaternion[0], "x": quaternion[1], "y": quaternion[2], "z": quaternion[3]},
        "surface_normal": {"x": n[0], "y": n[1], "z": n[2]},
        "nozzle_axis_world": {"x": -n[0], "y": -n[1], "z": -n[2]},
        "standoff_mm": standoff,
        "incidence_angle_deg": 0.0,
        "orientation_method": "surface_normal_frame",
        "reference_axis_fallback": abs(n[2]) > 0.98,
    }
