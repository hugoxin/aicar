from __future__ import annotations

from collections import Counter
from typing import Any


def canonical_patch(label: str, semantic_map: dict[str, Any]) -> str | None:
    normalized = label.strip().lower()
    aliases = semantic_map.get("stage4_5_patch_aliases", {})
    if normalized in aliases:
        return str(aliases[normalized])
    for patch_id, labels in semantic_map.get("explicit_labels", {}).items():
        if normalized in {str(item).lower() for item in labels}:
            return str(patch_id)
    return normalized if normalized in semantic_map.get("required_patches", []) else None


def _heuristic_patch(point: dict[str, Any], dimensions: dict[str, float]) -> str:
    x, y, z = float(point["x_mm"]), float(point["y_mm"]), float(point["z_mm"])
    half_w, half_l, height = dimensions["width_mm"] / 2, dimensions["length_mm"] / 2, dimensions["height_mm"]
    if z > height * 0.78:
        return "roof"
    front = y >= 0
    if z <= dimensions.get("wheel_radius_mm", 335) * 1.45 and abs(x) > half_w * 0.68:
        side = "left" if x < 0 else "right"
        axle = "front" if front else "rear"
        return f"{side}_{axle}_wheel"
    if abs(y) > half_l * 0.86:
        return "front" if y > 0 else "rear"
    return "left_side" if x < 0 else "right_side"


def map_geometry_semantics(geometry: dict[str, Any], semantic_map: dict[str, Any], dimensions: dict[str, float]) -> dict[str, Any]:
    explicit = heuristic = 0
    warnings = list(geometry.get("warnings", []))
    for point in geometry.get("points", []):
        patch = canonical_patch(str(point.get("patch_id", "")), semantic_map)
        if patch:
            explicit += 1
        else:
            patch = _heuristic_patch(point, dimensions)
            heuristic += 1
        point["patch_id"] = patch
    for vertex in geometry.get("vertices", []):
        patch = canonical_patch(str(vertex.get("patch_id", "")), semantic_map)
        if patch:
            explicit += 1
        else:
            patch = _heuristic_patch(vertex, dimensions)
            heuristic += 1
        vertex["patch_id"] = patch
    for triangle in geometry.get("triangles", []):
        patch = canonical_patch(str(triangle.get("patch_id", "")), semantic_map)
        if patch:
            triangle["patch_id"] = patch
    if heuristic:
        warnings.append({"code": semantic_map["heuristic_warning"], "count": heuristic, "message": "Demo dimension heuristic was used; this is not AI segmentation."})
    counts = Counter(item["patch_id"] for item in [*geometry.get("points", []), *geometry.get("vertices", [])])
    required = set(semantic_map["required_patches"])
    missing = sorted(required - set(counts))
    geometry["semantic_patches"] = [
        {"patch_id": patch_id, "sample_count": counts.get(patch_id, 0)}
        for patch_id in semantic_map["required_patches"]
    ]
    geometry["semantic_summary"] = {
        "patch_count": len(required - set(missing)),
        "explicit_label_count": explicit,
        "heuristic_mapping_count": heuristic,
        "missing_patches": missing,
    }
    geometry["warnings"] = warnings
    return geometry
