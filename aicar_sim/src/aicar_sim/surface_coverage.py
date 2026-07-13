from __future__ import annotations

import math
from collections import defaultdict
from typing import Any

from aicar_sim.surface_model import patch_local_bounds


def build_surface_grid(patch: dict[str, Any], resolution_mm: float) -> dict[str, Any]:
    if resolution_mm <= 0:
        raise ValueError("surface grid resolution must be greater than 0")
    bounds = patch_local_bounds(patch)
    u_count = max(1, int(math.ceil((bounds["u_max_mm"] - bounds["u_min_mm"]) / resolution_mm)))
    v_count = max(1, int(math.ceil((bounds["v_max_mm"] - bounds["v_min_mm"]) / resolution_mm)))
    cells = []
    for u_index in range(u_count):
        u = bounds["u_min_mm"] + (u_index + 0.5) * (bounds["u_max_mm"] - bounds["u_min_mm"]) / u_count
        for v_index in range(v_count):
            v = bounds["v_min_mm"] + (v_index + 0.5) * (bounds["v_max_mm"] - bounds["v_min_mm"]) / v_count
            if patch["surface_type"] == "circular_disk" and u * u + v * v > float(patch["radius_mm"]) ** 2:
                continue
            cells.append({"u_mm": round(u, 6), "v_mm": round(v, 6), "covered": False})
    return {
        "patch_id": patch["patch_id"],
        "zone_id": patch["zone_id"],
        "resolution_mm": float(resolution_mm),
        "cell_count": len(cells),
        "cells": cells,
    }


def mark_scan_coverage(grid: dict[str, Any], scan_path: list[dict[str, Any]], effective_width_mm: float) -> dict[str, Any]:
    if effective_width_mm <= 0:
        raise ValueError("effective nozzle width must be greater than 0")
    samples = [(float(point["u_mm"]), float(point["v_mm"])) for point in scan_path if "u_mm" in point and "v_mm" in point]
    radius_squared = (effective_width_mm / 2.0) ** 2
    for cell in grid["cells"]:
        cell["covered"] = any((float(cell["u_mm"]) - u) ** 2 + (float(cell["v_mm"]) - v) ** 2 <= radius_squared for u, v in samples)
    return grid


def calculate_patch_coverage(grid: dict[str, Any]) -> dict[str, Any]:
    total = len(grid["cells"])
    covered = sum(1 for item in grid["cells"] if item["covered"])
    uncovered = total - covered
    return {
        "patch_id": grid["patch_id"],
        "zone_id": grid["zone_id"],
        "cell_count": total,
        "covered_cell_count": covered,
        "uncovered_cell_count": uncovered,
        "patch_coverage_percent": round(covered / total * 100.0 if total else 0.0, 3),
    }


def calculate_zone_coverage(patch_results: list[dict[str, Any]]) -> dict[str, Any]:
    totals: dict[str, dict[str, int]] = defaultdict(lambda: {"cells": 0, "covered": 0})
    for item in patch_results:
        zone = totals[item["zone_id"]]
        zone["cells"] += int(item["cell_count"])
        zone["covered"] += int(item["covered_cell_count"])
    zone_results = []
    for zone_id in sorted(totals):
        cells = totals[zone_id]["cells"]
        covered = totals[zone_id]["covered"]
        zone_results.append(
            {
                "zone_id": zone_id,
                "cell_count": cells,
                "covered_cell_count": covered,
                "uncovered_cell_count": cells - covered,
                "zone_coverage_percent": round(covered / cells * 100.0 if cells else 0.0, 3),
            }
        )
    total_cells = sum(item["cell_count"] for item in zone_results)
    total_covered = sum(item["covered_cell_count"] for item in zone_results)
    return {
        "patch_coverage": patch_results,
        "zone_coverage": zone_results,
        "total_cell_count": total_cells,
        "covered_cell_count": total_covered,
        "uncovered_cell_count": total_cells - total_covered,
        "total_coverage_percent": round(total_covered / total_cells * 100.0 if total_cells else 0.0, 3),
        "coverage_model": "local_2d_surface_grid_approximation",
    }
