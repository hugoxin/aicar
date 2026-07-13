from __future__ import annotations

import math
from typing import Any

from aicar_sim.path_interpolator import calculate_point_distance, interpolate_segment


def preserve_critical_points(points: list[dict[str, Any]], annotations: dict[str, Any] | None = None) -> set[int]:
    annotations = annotations or {}
    preserved = {0, len(points) - 1} if points else set()
    preserved.update(int(index) for index in annotations.get("critical_indices", []) if 0 <= int(index) < len(points))
    for index in range(1, len(points)):
        previous, current = points[index - 1], points[index]
        keys = ("state_id", "zone_id", "nozzle_id", "segment_id", "is_transition", "safety_zone_ids", "requires_interlock", "forbidden")
        if any(previous.get(key) != current.get(key) for key in keys):
            preserved.update({index - 1, index})
    return preserved


def remove_duplicate_points(points: list[dict[str, Any]], tolerance_mm: float) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    if tolerance_mm <= 0:
        raise ValueError("duplicate point tolerance must be positive")
    if not points:
        return [], []
    result = [dict(points[0])]
    removals = []
    for index, point in enumerate(points[1:], 1):
        if calculate_point_distance(result[-1], point) <= tolerance_mm:
            removals.append({"point_index": point.get("sequence_index", index), "removal_reason": "duplicate_or_within_tolerance", "related_segment_id": point.get("segment_id"), "safety_checked": True})
        else:
            result.append(dict(point))
    return result, removals


def _line_distance(point: dict[str, Any], start: dict[str, Any], end: dict[str, Any]) -> float:
    ax, ay, az = (float(start[f"{axis}_mm"]) for axis in ("x", "y", "z"))
    bx, by, bz = (float(end[f"{axis}_mm"]) for axis in ("x", "y", "z"))
    px, py, pz = (float(point[f"{axis}_mm"]) for axis in ("x", "y", "z"))
    ab = (bx - ax, by - ay, bz - az)
    ap = (px - ax, py - ay, pz - az)
    denominator = sum(value * value for value in ab)
    if denominator <= 1e-12:
        return calculate_point_distance(point, start)
    ratio = max(0.0, min(1.0, sum(ap[i] * ab[i] for i in range(3)) / denominator))
    projection = {"x_mm": ax + ratio * ab[0], "y_mm": ay + ratio * ab[1], "z_mm": az + ratio * ab[2]}
    return calculate_point_distance(point, projection)


def _turn_angle(a: dict[str, Any], b: dict[str, Any], c: dict[str, Any]) -> float:
    left = tuple(float(b[f"{axis}_mm"]) - float(a[f"{axis}_mm"]) for axis in ("x", "y", "z"))
    right = tuple(float(c[f"{axis}_mm"]) - float(b[f"{axis}_mm"]) for axis in ("x", "y", "z"))
    lengths = (math.sqrt(sum(value * value for value in left)), math.sqrt(sum(value * value for value in right)))
    if min(lengths) <= 1e-12:
        return 0.0
    cosine = max(-1.0, min(1.0, sum(left[i] * right[i] for i in range(3)) / (lengths[0] * lengths[1])))
    return math.degrees(math.acos(cosine))


def simplify_collinear_points(
    points: list[dict[str, Any]],
    distance_tolerance_mm: float,
    angle_tolerance_deg: float,
    preserved_indices: set[int] | None = None,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    if len(points) < 3:
        return [dict(item) for item in points], []
    preserved_indices = preserved_indices or {0, len(points) - 1}
    kept = [dict(points[0])]
    removals = []
    for index in range(1, len(points) - 1):
        point = points[index]
        removable = index not in preserved_indices and _line_distance(point, kept[-1], points[index + 1]) <= distance_tolerance_mm and _turn_angle(kept[-1], point, points[index + 1]) <= angle_tolerance_deg
        if removable:
            removals.append({"point_index": point.get("sequence_index", index), "removal_reason": "approximately_collinear", "related_segment_id": point.get("segment_id"), "safety_checked": True})
        else:
            kept.append(dict(point))
    kept.append(dict(points[-1]))
    return kept, removals


def resample_path(points: list[dict[str, Any]], maximum_spacing_mm: float) -> list[dict[str, Any]]:
    if not points:
        return []
    return interpolate_segment(points, maximum_spacing_mm)
