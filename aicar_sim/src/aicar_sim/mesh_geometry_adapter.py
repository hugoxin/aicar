from __future__ import annotations

import math
from pathlib import Path
from typing import Any

from aicar_sim.geometry_math import triangle_normal


def _point(values: list[str], patch_id: str) -> dict[str, Any]:
    coordinates = [float(item) for item in values[:3]]
    if len(coordinates) != 3 or not all(math.isfinite(item) for item in coordinates):
        raise ValueError("mesh contains non-finite or incomplete vertex coordinates")
    return {"x_mm": coordinates[0], "y_mm": coordinates[1], "z_mm": coordinates[2], "patch_id": patch_id}


def load_obj_ascii(path: str | Path, profile: dict[str, Any]) -> dict[str, Any]:
    vertices: list[dict[str, Any]] = []
    triangles: list[dict[str, Any]] = []
    input_normals: list[tuple[float, float, float]] = []
    group = "unlabeled"
    for raw in Path(path).read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        fields = line.split()
        if fields[0] in {"g", "o"} and len(fields) > 1:
            group = fields[1]
        elif fields[0] == "v":
            vertices.append(_point(fields[1:], group))
        elif fields[0] == "vn":
            input_normals.append(tuple(float(item) for item in fields[1:4]))
        elif fields[0] == "f":
            indices = []
            for token in fields[1:]:
                raw_index = int(token.split("/")[0])
                index = raw_index - 1 if raw_index > 0 else len(vertices) + raw_index
                if index < 0 or index >= len(vertices):
                    raise ValueError("OBJ face index is out of range")
                indices.append(index)
            for offset in range(1, len(indices) - 1):
                triangles.append({"indices": [indices[0], indices[offset], indices[offset + 1]], "patch_id": group})
    return _mesh_result(path, vertices, triangles, len(input_normals), profile, "obj_ascii")


def load_stl_ascii(path: str | Path, profile: dict[str, Any]) -> dict[str, Any]:
    raw_bytes = Path(path).read_bytes()
    if b"\x00" in raw_bytes[:512] or not raw_bytes.lstrip().lower().startswith(b"solid"):
        raise ValueError("UNSUPPORTED_BINARY_STL")
    lines = raw_bytes.decode("utf-8").splitlines()
    vertices: list[dict[str, Any]] = []
    triangles: list[dict[str, Any]] = []
    patch_id = "unlabeled"
    facet: list[int] = []
    input_normals = 0
    for raw in lines:
        fields = raw.strip().split()
        if not fields:
            continue
        if fields[0].lower() == "solid" and len(fields) > 1:
            patch_id = fields[1]
        elif fields[:2] == ["facet", "normal"]:
            input_normals += 1
        elif fields[0].lower() == "vertex":
            vertices.append(_point(fields[1:], patch_id))
            facet.append(len(vertices) - 1)
        elif fields[0].lower() == "endfacet":
            if len(facet) != 3:
                raise ValueError("STL facet must contain exactly three vertices")
            triangles.append({"indices": facet, "patch_id": patch_id})
            facet = []
    return _mesh_result(path, vertices, triangles, input_normals, profile, "stl_ascii")


def _mesh_result(path: str | Path, vertices: list[dict[str, Any]], triangles: list[dict[str, Any]], input_normals: int, profile: dict[str, Any], source_format: str) -> dict[str, Any]:
    if not vertices or not triangles:
        raise ValueError("mesh geometry is empty")
    limits = profile["mesh"]
    if len(vertices) > int(limits["maximum_vertices"]) or len(triangles) > int(limits["maximum_triangles"]):
        raise ValueError("mesh geometry exceeds configured limits")
    duplicate_merge_count = 0
    if limits.get("merge_duplicate_vertices"):
        tolerance = float(limits.get("duplicate_vertex_tolerance_mm", 0.01))
        merged = []
        remap = {}
        buckets = {}
        for index, vertex in enumerate(vertices):
            key = (
                round(float(vertex["x_mm"]) / tolerance),
                round(float(vertex["y_mm"]) / tolerance),
                round(float(vertex["z_mm"]) / tolerance),
                vertex.get("patch_id"),
            )
            if key in buckets:
                remap[index] = buckets[key]
                duplicate_merge_count += 1
            else:
                remap[index] = len(merged)
                buckets[key] = len(merged)
                merged.append(vertex)
        for triangle in triangles:
            triangle["indices"] = [remap[index] for index in triangle["indices"]]
        vertices = merged
    degenerate = 0
    calculated = []
    valid_triangles = []
    for triangle in triangles:
        try:
            points = [vertices[index] for index in triangle["indices"]]
            normal = triangle_normal(
                (points[0]["x_mm"], points[0]["y_mm"], points[0]["z_mm"]),
                (points[1]["x_mm"], points[1]["y_mm"], points[1]["z_mm"]),
                (points[2]["x_mm"], points[2]["y_mm"], points[2]["z_mm"]),
            )
        except ValueError:
            degenerate += 1
            continue
        triangle["normal"] = {"x": normal[0], "y": normal[1], "z": normal[2]}
        calculated.append(triangle["normal"])
        valid_triangles.append(triangle)
    if not valid_triangles:
        raise ValueError("mesh contains no valid triangles")
    points = [dict(item) for item in vertices]
    return {
        "source_path": str(Path(path)),
        "source_format": source_format,
        "unit": "mm",
        "vertices": vertices,
        "triangles": valid_triangles,
        "points": points,
        "point_normals": [],
        "adapter_summary": {
            "vertex_count": len(vertices),
            "triangle_count": len(valid_triangles),
            "degenerate_triangle_count": degenerate,
            "duplicate_vertex_merge_count": duplicate_merge_count,
            "input_normal_count": input_normals,
            "calculated_normal_count": len(calculated),
        },
        "warnings": [],
        "limitations": ["Tessellated ASCII mesh interface; no native STEP/IGES semantics."],
    }


def load_mesh_geometry(path: str | Path, profile: dict[str, Any]) -> dict[str, Any]:
    suffix = Path(path).suffix.lower()
    if suffix == ".obj":
        return load_obj_ascii(path, profile)
    if suffix == ".stl":
        return load_stl_ascii(path, profile)
    raise ValueError(f"unsupported mesh format: {suffix}")
