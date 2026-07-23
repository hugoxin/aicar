from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

from aicar_sim.geometry_source import load_geometry_source


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def build_demo_geometry_fixtures(
    output_dir: str | Path,
    import_profile: dict[str, Any],
    dimension_profile: dict[str, Any],
    semantic_map: dict[str, Any],
) -> dict[str, Any]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    geometry = load_geometry_source("ANALYTIC_REFERENCE", None, import_profile, dimension_profile, semantic_map)
    points = geometry["points"]
    normals = geometry["point_normals"]
    obj_path = output / "demo_sedan_mesh.obj"
    stl_path = output / "demo_sedan_mesh.stl"
    ply_path = output / "demo_sedan_cloud.ply"
    xyz_path = output / "demo_sedan_cloud.xyz"
    csv_path = output / "demo_sedan_cloud.csv"
    obj_lines = ["# Stage4.6 generated analytic-reference fixture; not real CAD"]
    stl_lines = []
    vertex_index = 1
    current_patch = None
    for point, normal in zip(points, normals):
        patch = point["patch_id"]
        if patch != current_patch:
            obj_lines.append(f"g {patch}")
            current_patch = patch
        x, y, z = point["x_mm"], point["y_mm"], point["z_mm"]
        nx, ny, nz = normal["x"], normal["y"], normal["z"]
        if abs(nz) > 0.5:
            offsets = ((-1, -1, 0), (1, -1, 0), (0, 1, 0))
        elif abs(nx) > 0.5:
            offsets = ((0, -1, -1), (0, 1, -1), (0, 0, 1))
        else:
            offsets = ((-1, 0, -1), (1, 0, -1), (0, 0, 1))
        obj_lines.append(f"vn {nx:.9f} {ny:.9f} {nz:.9f}")
        triangle_vertices = []
        for dx, dy, dz in offsets:
            vertex = (x + dx, y + dy, z + dz)
            triangle_vertices.append(vertex)
            obj_lines.append(f"v {vertex[0]:.6f} {vertex[1]:.6f} {vertex[2]:.6f}")
        obj_lines.append(f"f {vertex_index}//{vertex_index} {vertex_index + 1}//{vertex_index} {vertex_index + 2}//{vertex_index}")
        vertex_index += 3
        stl_lines.extend([
            f"solid {patch}",
            f"  facet normal {nx:.9f} {ny:.9f} {nz:.9f}",
            "    outer loop",
            *[f"      vertex {vertex[0]:.6f} {vertex[1]:.6f} {vertex[2]:.6f}" for vertex in triangle_vertices],
            "    endloop",
            "  endfacet",
            f"endsolid {patch}",
        ])
    obj_path.write_text("\n".join(obj_lines) + "\n", encoding="utf-8")
    stl_path.write_text("\n".join(stl_lines) + "\n", encoding="utf-8")

    ply_lines = [
        "ply", "format ascii 1.0", f"element vertex {len(points)}",
        "property float x", "property float y", "property float z",
        "property float nx", "property float ny", "property float nz",
        "property string patch_id", "end_header",
    ]
    xyz_lines = ["# x y z nx ny nz patch_id"]
    for point, normal in zip(points, normals):
        values = (
            point["x_mm"], point["y_mm"], point["z_mm"],
            normal["x"], normal["y"], normal["z"], point["patch_id"],
        )
        line = " ".join(f"{value:.9f}" if isinstance(value, float) else str(value) for value in values)
        ply_lines.append(line)
        xyz_lines.append(line)
    ply_path.write_text("\n".join(ply_lines) + "\n", encoding="utf-8")
    xyz_path.write_text("\n".join(xyz_lines) + "\n", encoding="utf-8")
    with csv_path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(["x", "y", "z", "nx", "ny", "nz", "patch_id"])
        for point, normal in zip(points, normals):
            writer.writerow([point["x_mm"], point["y_mm"], point["z_mm"], normal["x"], normal["y"], normal["z"], point["patch_id"]])
    manifest = {
        "manifest_version": "stage4.6",
        "source": "demo analytic reference surface",
        "files": [str(path) for path in (obj_path, stl_path, ply_path, xyz_path, csv_path)],
        "point_count": len(points),
        "triangle_count": len(points),
        "dimensions": dimension_profile["dimensions"],
        "unit": "mm",
        "coordinate_system": geometry["coordinate_system"],
        "generated_from_analytic_reference": True,
        "not_real_scan": True,
        "not_manufacturer_cad": True,
    }
    manifest_path = output / "demo_geometry_fixture_manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return manifest
