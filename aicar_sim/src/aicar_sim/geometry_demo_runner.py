from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from aicar_sim.geometry_demo_fixture import build_demo_geometry_fixtures
from aicar_sim.geometry_pose_pipeline import build_geometry_pose_pipeline
from aicar_sim.geometry_pose_report import build_geometry_pose_report
from aicar_sim.vehicle_dimension_profile import get_wheel_centers


PROJECT_ROOT = Path(__file__).resolve().parents[2]
WORKSPACE_ROOT = PROJECT_ROOT.parent


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def defaults() -> dict[str, Path]:
    return {
        "import_profile": PROJECT_ROOT / "data/geometry_profiles/demo_geometry_import_profile.json",
        "dimension_profile": PROJECT_ROOT / "data/vehicle_dimensions/demo_reference_real_size_sedan_dimensions.json",
        "semantic_map": PROJECT_ROOT / "data/geometry_semantic_maps/demo_sedan_semantic_map.json",
        "pose_profile": PROJECT_ROOT / "data/nozzle_pose_profiles/demo_nozzle_pose_profile.json",
        "stage4_5_plan": PROJECT_ROOT / "outputs/continuous_surface_path_r/continuous_surface_path_plan_r.json",
        "motion_model": PROJECT_ROOT / "data/motion_models/demo_cartesian_gantry.json",
        "safety_layout": PROJECT_ROOT / "data/safety_models/demo_wash_bay_safety_layout.json",
        "space_model": PROJECT_ROOT / "outputs/space_model/space_model_report.json",
        "wash_profile": PROJECT_ROOT / "data/wash_profiles/standard_sedan.json",
        "nozzle_plan": PROJECT_ROOT / "outputs/nozzle_plan/nozzle_coverage_plan.json",
        "actuator_system": PROJECT_ROOT / "data/actuator_systems/demo_multi_actuator_system.json",
        "fixture_dir": PROJECT_ROOT / "outputs/geometry_inputs",
    }


def ensure_prerequisites() -> dict[str, Path]:
    paths = defaults()
    missing = [key for key in ("stage4_5_plan", "space_model", "nozzle_plan") if not paths[key].exists()]
    if missing:
        raise FileNotFoundError("missing frozen Stage4.5 prerequisite outputs: " + ", ".join(missing))
    fixture_names = (
        "demo_sedan_mesh.obj",
        "demo_sedan_mesh.stl",
        "demo_sedan_cloud.ply",
        "demo_sedan_cloud.xyz",
        "demo_sedan_cloud.csv",
        "demo_geometry_fixture_manifest.json",
    )
    if not all((paths["fixture_dir"] / name).exists() for name in fixture_names):
        build_demo_geometry_fixtures(
            paths["fixture_dir"],
            load_json(paths["import_profile"]),
            load_json(paths["dimension_profile"]),
            load_json(paths["semantic_map"]),
        )
    return paths


def source_spec(name: str, paths: dict[str, Path]) -> tuple[str, str | None]:
    specs = {
        "analytic": ("ANALYTIC_REFERENCE", None),
        "obj": ("CAD_MESH", str(paths["fixture_dir"] / "demo_sedan_mesh.obj")),
        "stl": ("CAD_MESH", str(paths["fixture_dir"] / "demo_sedan_mesh.stl")),
        "ply": ("POINT_CLOUD", str(paths["fixture_dir"] / "demo_sedan_cloud.ply")),
        "xyz": ("POINT_CLOUD", str(paths["fixture_dir"] / "demo_sedan_cloud.xyz")),
        "csv": ("POINT_CLOUD", str(paths["fixture_dir"] / "demo_sedan_cloud.csv")),
    }
    return specs[name]


def run_source(name: str, paths: dict[str, Path] | None = None) -> dict[str, Any]:
    paths = paths or ensure_prerequisites()
    source_type, source_path = source_spec(name, paths)
    return build_geometry_pose_pipeline(
        source_type,
        source_path,
        load_json(paths["import_profile"]),
        load_json(paths["dimension_profile"]),
        load_json(paths["semantic_map"]),
        load_json(paths["pose_profile"]),
        load_json(paths["stage4_5_plan"]),
        load_json(paths["motion_model"]),
        load_json(paths["safety_layout"]),
        source_space_model=load_json(paths["space_model"]),
        wash_profile=load_json(paths["wash_profile"]),
        nozzle_coverage_plan=load_json(paths["nozzle_plan"]),
        actuator_system=load_json(paths["actuator_system"]),
    )


def run_all(names: tuple[str, ...] = ("analytic", "obj", "stl", "ply", "xyz")) -> tuple[dict[str, Any], dict[str, Any]]:
    paths = ensure_prerequisites()
    results = {name: run_source(name, paths) for name in names}
    source_results = []
    for name, result in results.items():
        validation = result["validation"]
        geometry = result["geometry"]
        source_results.append({
            "name": name,
            "geometry_source_type": geometry["geometry_source_type"],
            "input_file": geometry.get("source_metadata", {}).get("source_path"),
            "unit": geometry["unit"],
            "point_count": len(geometry["points"]),
            "vertex_count": len(geometry["vertices"]),
            "triangle_count": len(geometry["triangles"]),
            "bbox": geometry["bounding_box"],
            "dimension_mismatch": geometry["dimension_summary"]["mismatch_ratio"],
            "normal_summary": geometry["normal_summary"],
            "pose_summary": result["pose_plan"]["pose_summary"],
            "summary": validation["summary"],
            "status": validation["status"],
        })
    baseline_dimensions = {"length_mm": 4700, "width_mm": 1800, "height_mm": 1450, "wheelbase_mm": 2800, "wheel_radius_mm": 330}
    target = load_json(paths["dimension_profile"])["dimensions"]
    target_profile = load_json(paths["dimension_profile"])
    old_wheel_centers = {
        "left_front_wheel": {"x_mm": -800, "y_mm": 1400, "z_mm": 330},
        "right_front_wheel": {"x_mm": 800, "y_mm": 1400, "z_mm": 330},
        "left_rear_wheel": {"x_mm": -800, "y_mm": -1400, "z_mm": 330},
        "right_rear_wheel": {"x_mm": 800, "y_mm": -1400, "z_mm": 330},
    }
    comparison = {
        "report_version": "stage4.6",
        "status": "ACCEPTED_WITH_WARNINGS" if all(item["status"] == "ACCEPTED_WITH_WARNINGS" for item in source_results) else "FAILED",
        "source_results": source_results,
        "dimension_comparison": {
            "stage4_5_demo_dimensions": baseline_dimensions,
            "reference_real_size_dimensions": target,
            "delta": {key: target[key] - baseline_dimensions.get(key, target[key]) for key in target},
            "authority": "PROFILE_WITH_GEOMETRY_CROSS_CHECK",
            "manufacturer_specific": False,
            "wheel_centers": {
                "stage4_5_demo": old_wheel_centers,
                "reference_real_size": get_wheel_centers(target_profile),
            },
            "workspace_fit": all(
                item["summary"]["violation_count"] == 0
                for item in source_results
            ),
        },
        "summary": {
            "source_count": len(source_results),
            "accepted_source_count": sum(item["status"] == "ACCEPTED_WITH_WARNINGS" for item in source_results),
            "violation_count": sum(item["summary"]["violation_count"] for item in source_results),
        },
        "safety_conditions": {
            "all_sources_accepted": all(item["status"] == "ACCEPTED_WITH_WARNINGS" for item in source_results),
            "all_minimum_clearance_at_least_250": all(item["summary"]["minimum_clearance_mm"] >= 250 for item in source_results),
        },
        "warnings": [
            "Fixtures are generated from the analytic reference and are not real CAD or point-cloud scans.",
            "Reference dimensions are not manufacturer-specific.",
            "Normal estimation and nearest-patch mapping are offline demo approximations.",
        ],
        "violations": [],
        "limitations": ["No STEP/IGES, scan registration, robot IK, PLC, servo, or hardware control."],
    }
    return results, comparison


def write_pipeline_outputs(results: dict[str, Any], comparison: dict[str, Any]) -> None:
    normalized_names = {"analytic": "analytic_geometry_normalized.json", "obj": "mesh_geometry_normalized.json", "ply": "point_cloud_geometry_normalized.json"}
    for name, filename in normalized_names.items():
        if name in results:
            write_json(PROJECT_ROOT / "outputs/geometry_normalized" / filename, results[name]["geometry"])
    primary = results["ply"] if "ply" in results else next(iter(results.values()))
    write_json(PROJECT_ROOT / "outputs/geometry_surface/geometry_surface_plan.json", primary["surface_plan"])
    write_json(PROJECT_ROOT / "outputs/geometry_pose/geometry_nozzle_pose_plan.json", primary["pose_plan"])
    write_json(PROJECT_ROOT / "outputs/geometry_machine_path/geometry_machine_path_plan.json", primary["machine_plan"])
    write_json(PROJECT_ROOT / "outputs/geometry_safety/geometry_collision_safety_plan.json", primary["collision_plan"])
    write_json(PROJECT_ROOT / "outputs/geometry_safety/geometry_multi_actuator_schedule.json", primary["schedule"])
    write_json(PROJECT_ROOT / "outputs/geometry_validation/geometry_pose_validation_report.json", comparison)
    report = build_geometry_pose_report(comparison)
    report_path = PROJECT_ROOT / "outputs/geometry_validation/stage4_geometry_pose_report.html"
    report_path.write_text(report, encoding="utf-8")
