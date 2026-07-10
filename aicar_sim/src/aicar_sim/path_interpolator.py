from __future__ import annotations

import math
from typing import Any


def calculate_point_distance(point_a: dict[str, Any], point_b: dict[str, Any]) -> float:
    """Return Euclidean distance between two Cartesian points in millimeters."""
    return math.sqrt(
        (float(point_b["x_mm"]) - float(point_a["x_mm"])) ** 2
        + (float(point_b["y_mm"]) - float(point_a["y_mm"])) ** 2
        + (float(point_b["z_mm"]) - float(point_a["z_mm"])) ** 2
    )


def _point_with_metadata(
    point: dict[str, Any],
    source_point_index: int,
    interpolated: bool,
) -> dict[str, Any]:
    result = dict(point)
    result.update(
        {
            "x_mm": float(point["x_mm"]),
            "y_mm": float(point["y_mm"]),
            "z_mm": float(point["z_mm"]),
            "source_point_index": int(source_point_index),
            "interpolated": bool(interpolated),
        }
    )
    return result


def interpolate_segment(
    points: list[dict[str, Any]],
    max_spacing_mm: float,
) -> list[dict[str, Any]]:
    """Linearly interpolate a segment so adjacent points stay within spacing."""
    if max_spacing_mm <= 0:
        raise ValueError("max_spacing_mm must be greater than 0")
    if not points:
        return []

    result = [_point_with_metadata(points[0], 0, False)]
    for index in range(1, len(points)):
        start = points[index - 1]
        end = points[index]
        distance = calculate_point_distance(start, end)
        if distance == 0:
            result.append(_point_with_metadata(end, index, False))
            continue
        step_count = max(1, int(math.ceil(distance / max_spacing_mm)))
        for step in range(1, step_count + 1):
            ratio = step / step_count
            point = dict(start)
            point.update(
                {
                    "x_mm": float(start["x_mm"]) + (float(end["x_mm"]) - float(start["x_mm"])) * ratio,
                    "y_mm": float(start["y_mm"]) + (float(end["y_mm"]) - float(start["y_mm"])) * ratio,
                    "z_mm": float(start["z_mm"]) + (float(end["z_mm"]) - float(start["z_mm"])) * ratio,
                }
            )
            if step == step_count:
                point.update(end)
                point["x_mm"] = float(end["x_mm"])
                point["y_mm"] = float(end["y_mm"])
                point["z_mm"] = float(end["z_mm"])
            result.append(_point_with_metadata(point, index - 1, step != step_count))

    for sequence_index, point in enumerate(result):
        point["sequence_index"] = sequence_index
    return result


def interpolate_path_segments(
    path_segments: list[dict[str, Any]],
    max_spacing_mm: float,
) -> list[dict[str, Any]]:
    """Interpolate every path segment while preserving segment metadata."""
    result = []
    for segment in path_segments:
        points = segment.get("points", [])
        interpolated_points = interpolate_segment(points, max_spacing_mm)
        item = dict(segment)
        item["source_point_count"] = len(points)
        item["points"] = interpolated_points
        result.append(item)
    return result
