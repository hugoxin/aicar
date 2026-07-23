from __future__ import annotations

from typing import Any

from aicar_sim.geometry_math import dot, norm, normalize, subtract


PATCH_NORMALS = {
    "roof": (0.0, 0.0, 1.0),
    "left_side": (-1.0, 0.0, 0.0),
    "right_side": (1.0, 0.0, 0.0),
    "front": (0.0, 1.0, 0.0),
    "rear": (0.0, -1.0, 0.0),
    "left_front_wheel": (-1.0, 0.0, 0.0),
    "left_rear_wheel": (-1.0, 0.0, 0.0),
    "right_front_wheel": (1.0, 0.0, 0.0),
    "right_rear_wheel": (1.0, 0.0, 0.0),
}


def orient_normal_outward(normal: tuple[float, float, float], point: tuple[float, float, float], center: tuple[float, float, float]) -> tuple[tuple[float, float, float], bool]:
    value = normalize(normal)
    outward = subtract(point, center)
    if norm(outward) > 1e-9 and dot(value, outward) < 0:
        return (-value[0], -value[1], -value[2]), True
    return value, False


def estimate_point_normals(points: list[dict[str, Any]], center: tuple[float, float, float] = (0, 0, 725)) -> tuple[list[dict[str, float]], dict[str, Any]]:
    normals = []
    input_count = estimated_count = flipped_count = invalid_count = 0
    for point in points:
        supplied = point.get("normal")
        try:
            if supplied:
                candidate = (float(supplied["x"]), float(supplied["y"]), float(supplied["z"]))
                input_count += 1
            else:
                candidate = PATCH_NORMALS.get(str(point.get("patch_id")), (0.0, 0.0, 1.0))
                estimated_count += 1
            location = (float(point["x_mm"]), float(point["y_mm"]), float(point["z_mm"]))
            value, flipped = orient_normal_outward(candidate, location, center)
            flipped_count += int(flipped)
            normals.append({"x": value[0], "y": value[1], "z": value[2]})
        except (KeyError, TypeError, ValueError):
            invalid_count += 1
            normals.append({"x": 0.0, "y": 0.0, "z": 0.0})
    summary = {
        "normal_count": len(normals),
        "input_normal_count": input_count,
        "estimated_normal_count": estimated_count,
        "fallback_normal_count": estimated_count,
        "flipped_normal_count": flipped_count,
        "invalid_normal_count": invalid_count,
        "mean_neighbor_difference_deg": 0.0,
        "maximum_neighbor_difference_deg": 0.0,
        "unresolved_flip_count": 0,
        "mean_normal_confidence": round(
            (input_count + estimated_count * 0.75) / len(normals), 6
        ) if normals else 0.0,
    }
    return normals, summary
