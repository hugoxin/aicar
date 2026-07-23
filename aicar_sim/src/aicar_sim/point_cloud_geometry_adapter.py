from __future__ import annotations

import csv
import math
from pathlib import Path
from typing import Any


def _record(values: dict[str, str]) -> dict[str, Any]:
    point = {f"{axis}_mm": float(values[axis]) for axis in ("x", "y", "z")}
    if not all(math.isfinite(value) for value in point.values()):
        raise ValueError("point cloud contains non-finite values")
    if all(key in values and values[key] not in {"", None} for key in ("nx", "ny", "nz")):
        point["normal"] = {axis: float(values[f"n{axis}"]) for axis in ("x", "y", "z")}
    if values.get("patch_id"):
        point["patch_id"] = str(values["patch_id"])
    return point


def _load_csv(path: Path) -> list[dict[str, Any]]:
    with path.open("r", encoding="utf-8", newline="") as stream:
        reader = csv.DictReader(stream)
        if not reader.fieldnames or not {"x", "y", "z"}.issubset(reader.fieldnames):
            raise ValueError("CSV point cloud requires x,y,z columns")
        return [_record(row) for row in reader]


def _load_xyz(path: Path) -> list[dict[str, Any]]:
    points = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        fields = raw.replace(",", " ").split()
        if len(fields) < 3:
            raise ValueError("XYZ point requires x y z")
        record = {"x": fields[0], "y": fields[1], "z": fields[2]}
        if len(fields) >= 6:
            record.update({"nx": fields[3], "ny": fields[4], "nz": fields[5]})
        if len(fields) >= 7:
            record["patch_id"] = fields[6]
        points.append(_record(record))
    return points


def _load_ply(path: Path) -> list[dict[str, Any]]:
    lines = path.read_text(encoding="utf-8").splitlines()
    if not lines or lines[0].strip() != "ply":
        raise ValueError("PLY header missing")
    if "format ascii 1.0" not in lines[:5]:
        raise ValueError("only ASCII PLY is supported")
    count = 0
    properties = []
    end = None
    for index, line in enumerate(lines):
        fields = line.split()
        if fields[:2] == ["element", "vertex"]:
            count = int(fields[2])
        elif fields[:2] == ["property", "float"] or fields[:2] == ["property", "double"] or fields[:2] == ["property", "string"]:
            properties.append(fields[-1])
        elif line.strip() == "end_header":
            end = index
            break
    if end is None:
        raise ValueError("PLY end_header missing")
    points = []
    for line in lines[end + 1:end + 1 + count]:
        values = line.split()
        points.append(_record(dict(zip(properties, values))))
    return points


def load_point_cloud_geometry(path: str | Path, profile: dict[str, Any]) -> dict[str, Any]:
    source = Path(path)
    if source.suffix.lower() == ".csv":
        points = _load_csv(source)
    elif source.suffix.lower() == ".xyz":
        points = _load_xyz(source)
    elif source.suffix.lower() == ".ply":
        points = _load_ply(source)
    else:
        raise ValueError(f"unsupported point-cloud format: {source.suffix}")
    if not points:
        raise ValueError("point cloud is empty")
    if len(points) > int(profile["point_cloud"]["maximum_points"]):
        raise ValueError("point cloud exceeds configured point limit")
    seen = set()
    unique = []
    duplicate_count = 0
    for point in points:
        key = (round(point["x_mm"], 6), round(point["y_mm"], 6), round(point["z_mm"], 6), point.get("patch_id"))
        if key in seen:
            duplicate_count += 1
        else:
            seen.add(key)
            unique.append(point)
    voxel = float(profile["point_cloud"].get("downsample_voxel_mm", 0))
    downsampled = 0
    if voxel > 0:
        buckets = {}
        for point in unique:
            key = (
                math.floor(point["x_mm"] / voxel),
                math.floor(point["y_mm"] / voxel),
                math.floor(point["z_mm"] / voxel),
                point.get("patch_id"),
            )
            if key in buckets:
                downsampled += 1
            else:
                buckets[key] = point
        unique = list(buckets.values())
    return {
        "source_path": str(source),
        "source_format": source.suffix.lower().lstrip("."),
        "unit": "mm",
        "vertices": [],
        "triangles": [],
        "points": unique,
        "point_normals": [],
        "adapter_summary": {
            "point_count": len(unique),
            "duplicate_point_count": duplicate_count,
            "input_normal_count": sum(1 for point in unique if point.get("normal")),
            "downsampled_point_count": downsampled,
        },
        "warnings": [],
        "limitations": ["No ICP, SLAM, multi-view fusion, or sensor calibration."],
    }
