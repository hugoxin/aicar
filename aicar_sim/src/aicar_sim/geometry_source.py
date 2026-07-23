from __future__ import annotations

import copy
from pathlib import Path
from typing import Any

from aicar_sim.geometry_normalizer import calculate_bounding_box, normalize_geometry
from aicar_sim.geometry_semantic_mapper import map_geometry_semantics
from aicar_sim.mesh_geometry_adapter import load_mesh_geometry
from aicar_sim.point_cloud_geometry_adapter import load_point_cloud_geometry
from aicar_sim.surface_normal_estimator import estimate_point_normals


SOURCE_TYPES = {"ANALYTIC_REFERENCE", "CAD_MESH", "POINT_CLOUD"}
PATCHES = ("roof", "left_side", "right_side", "front", "rear", "left_front_wheel", "left_rear_wheel", "right_front_wheel", "right_rear_wheel")


def _sample_range(start: float, stop: float, count: int) -> list[float]:
    return [start + (stop - start) * index / (count - 1) for index in range(count)]


def build_analytic_reference() -> dict[str, Any]:
    width, length, height = 1800.0, 4700.0, 1450.0
    points = []
    def add_patch(patch: str, xs: list[float], ys: list[float], zs: list[float], normal: tuple[float, float, float]) -> None:
        for x in xs:
            for y in ys:
                for z in zs:
                    points.append({"x_mm": x, "y_mm": y, "z_mm": z, "patch_id": patch, "normal": {"x": normal[0], "y": normal[1], "z": normal[2]}})
    add_patch("roof", _sample_range(-width * .42, width * .42, 9), _sample_range(-length * .46, length * .46, 21), [height], (0, 0, 1))
    add_patch("left_side", [-width / 2], _sample_range(-length * .46, length * .46, 21), _sample_range(300, height * .9, 7), (-1, 0, 0))
    add_patch("right_side", [width / 2], _sample_range(-length * .46, length * .46, 21), _sample_range(300, height * .9, 7), (1, 0, 0))
    add_patch("front", _sample_range(-width * .42, width * .42, 9), [length / 2], _sample_range(0, height * .85, 7), (0, 1, 0))
    add_patch("rear", _sample_range(-width * .42, width * .42, 9), [-length / 2], _sample_range(0, height * .85, 7), (0, -1, 0))
    centers = {"left_front_wheel": (-900, 1425), "left_rear_wheel": (-900, -1425), "right_front_wheel": (900, 1425), "right_rear_wheel": (900, -1425)}
    for patch, (x, y) in centers.items():
        normal = (-1, 0, 0) if x < 0 else (1, 0, 0)
        add_patch(patch, [x], _sample_range(y - 260, y + 260, 5), _sample_range(80, 650, 6), normal)
    return {
        "geometry_source_id": "analytic_reference_sedan",
        "geometry_source_type": "ANALYTIC_REFERENCE",
        "unit": "mm",
        "coordinate_system": {"origin": "vehicle_center_floor", "x_axis": "vehicle_width_positive_right", "y_axis": "vehicle_length_positive_front", "z_axis": "up", "handedness": "right"},
        "vertices": [],
        "triangles": [],
        "points": points,
        "point_normals": [],
        "source_metadata": {"generated_from_analytic_reference": True},
        "warnings": [],
        "limitations": ["Reference analytic geometry; not real CAD or scan data."],
    }


def load_geometry_source(source_type: str, source_path: str | Path | None, import_profile: dict[str, Any], dimension_profile: dict[str, Any], semantic_map: dict[str, Any]) -> dict[str, Any]:
    source_type = source_type.upper()
    if source_type not in SOURCE_TYPES:
        raise ValueError(f"unsupported geometry source type: {source_type}")
    if source_type == "ANALYTIC_REFERENCE":
        geometry = build_analytic_reference()
    else:
        if not source_path or not Path(source_path).exists():
            raise FileNotFoundError(f"geometry source does not exist: {source_path}")
        adapter = load_mesh_geometry if source_type == "CAD_MESH" else load_point_cloud_geometry
        geometry = adapter(source_path, import_profile)
        geometry["geometry_source_id"] = Path(source_path).stem
        geometry["geometry_source_type"] = source_type
        geometry["coordinate_system"] = {"origin": "vehicle_center_floor", "x_axis": "vehicle_width_positive_right", "y_axis": "vehicle_length_positive_front", "z_axis": "up", "handedness": "right"}
        geometry["source_metadata"] = {"source_path": str(Path(source_path)), "generated_from_analytic_reference": True, "not_real_scan": True}
    geometry = normalize_geometry(geometry, import_profile, dimension_profile)
    geometry = map_geometry_semantics(geometry, semantic_map, dimension_profile["dimensions"])
    normal_items = geometry["points"] or geometry["vertices"]
    normals, summary = estimate_point_normals(normal_items, (0, 0, float(dimension_profile["dimensions"]["height_mm"]) / 2))
    geometry["point_normals"] = normals
    geometry["normal_summary"] = summary
    geometry.setdefault("adapter_summary", {"point_count": len(geometry["points"]), "vertex_count": len(geometry["vertices"]), "triangle_count": len(geometry["triangles"])})
    validate_geometry_source(geometry)
    return geometry


def validate_geometry_source(source: dict[str, Any]) -> dict[str, Any]:
    errors = []
    if source.get("geometry_source_type") not in SOURCE_TYPES:
        errors.append("invalid geometry_source_type")
    if source.get("unit") != "mm":
        errors.append("geometry unit must be mm")
    if not source.get("points") and not source.get("vertices"):
        errors.append("geometry has no samples")
    required = set(PATCHES)
    actual = {item["patch_id"] for item in source.get("semantic_patches", []) if item.get("sample_count", 0) > 0}
    if required - actual:
        errors.append("missing semantic patches: " + ", ".join(sorted(required - actual)))
    if source.get("normal_summary", {}).get("invalid_normal_count"):
        errors.append("geometry contains invalid normals")
    if errors:
        raise ValueError("; ".join(errors))
    return {"valid": True, "errors": []}


def get_geometry_bounding_box(source: dict[str, Any]) -> dict[str, float]:
    return copy.deepcopy(source.get("bounding_box") or calculate_bounding_box(source["vertices"] or source["points"]))


def get_geometry_dimension_summary(source: dict[str, Any]) -> dict[str, Any]:
    return copy.deepcopy(source["dimension_summary"])


def get_patch_geometry(source: dict[str, Any], patch_id: str) -> dict[str, Any]:
    points = [item for item in (source["points"] or source["vertices"]) if item.get("patch_id") == patch_id]
    triangles = [item for item in source["triangles"] if item.get("patch_id") == patch_id]
    return {"patch_id": patch_id, "points": points, "triangles": triangles}
