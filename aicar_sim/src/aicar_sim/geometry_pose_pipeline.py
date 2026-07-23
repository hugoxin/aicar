from __future__ import annotations

import copy
from typing import Any

from aicar_sim.continuous_surface_path_repair import build_continuous_machine_path_repair
from aicar_sim.continuous_surface_repair_validation import build_continuous_surface_repair_validation
from aicar_sim.geometry_source import load_geometry_source
from aicar_sim.geometry_surface_path_adapter import adapt_stage4_5_path
from aicar_sim.motion_validator import validate_machine_path
from aicar_sim.pose_constraint_validator import validate_nozzle_poses
from aicar_sim.vehicle_envelope import build_vehicle_envelope


def build_dimension_space_model(
    source_space_model: dict[str, Any],
    dimension_profile: dict[str, Any],
    wash_profile: dict[str, Any],
) -> dict[str, Any]:
    result = copy.deepcopy(source_space_model)
    dimensions = dimension_profile["dimensions"]
    vehicle_model = {
        "vehicle_type": dimension_profile["vehicle_class"],
        "wash_profile": wash_profile["wash_profile"],
        "length_mm": dimensions["length_mm"],
        "width_mm": dimensions["width_mm"],
        "height_mm": dimensions["height_mm"],
    }
    result["report_version"] = "stage4.6"
    result["vehicle"].update(vehicle_model)
    result["vehicle_envelope"] = build_vehicle_envelope(vehicle_model, wash_profile)
    result["dimension_profile_id"] = dimension_profile["dimension_profile_id"]
    return result


def _surface_validation(plan: dict[str, Any]) -> dict[str, Any]:
    points = plan["trajectory_points"]
    state_ids = {item["state_id"] for item in plan.get("states", [])}
    zone_ids = {
        zone_id
        for state in plan.get("states", [])
        for zone_id in state.get("target_zone_ids", [])
    }
    checks = {
        "state_count_is_7": len(state_ids) == 7,
        "zone_count_is_6": len(zone_ids) == 6,
        "patch_count_is_9": len({item["patch_id"] for item in points}) == 9,
        "wheel_patch_count_is_4": len({item["patch_id"] for item in points if "wheel" in item["patch_id"]}) == 4,
        "surface_task_count_is_18": len([item for item in plan["path_segments"] if item.get("segment_type") == "process"]) == 18,
        "mapping_complete": all("mapped_geometry_surface_point" in item for item in points),
    }
    violations = [{"check_id": key, "severity": "CRITICAL", "message": "Stage4.6 path semantic check failed."} for key, passed in checks.items() if not passed]
    warnings = [
        {
            "check_id": "offline_geometry_fixture",
            "severity": "WARNING",
            "message": "Geometry fixture is generated from the analytic reference and is not real CAD or scan data.",
        }
    ]
    return {
        "validation_status": "FAIL" if violations else "PASS_WITH_WARNINGS",
        "checks": checks,
        "warning_count": len(warnings),
        "violation_count": len(violations),
        "warnings": warnings,
        "violations": violations,
    }


def build_geometry_pose_pipeline(
    geometry_source_type: str,
    geometry_source_path: str | None,
    geometry_import_profile: dict[str, Any],
    vehicle_dimension_profile: dict[str, Any],
    semantic_map: dict[str, Any],
    nozzle_pose_profile: dict[str, Any],
    stage4_5_continuous_plan: dict[str, Any],
    motion_model: dict[str, Any],
    safety_layout: dict[str, Any],
    *,
    source_space_model: dict[str, Any],
    wash_profile: dict[str, Any],
    nozzle_coverage_plan: dict[str, Any],
    actuator_system: dict[str, Any],
) -> dict[str, Any]:
    geometry = load_geometry_source(
        geometry_source_type,
        geometry_source_path,
        geometry_import_profile,
        vehicle_dimension_profile,
        semantic_map,
    )
    adapted = adapt_stage4_5_path(stage4_5_continuous_plan, geometry, semantic_map, nozzle_pose_profile)
    surface_plan = adapted["surface_plan"]
    poses = adapted["poses"]
    pose_validation = validate_nozzle_poses(poses, nozzle_pose_profile)
    surface_plan["validation"] = _surface_validation(surface_plan)
    machine_plan = build_continuous_machine_path_repair(surface_plan, motion_model)
    space_model = build_dimension_space_model(source_space_model, vehicle_dimension_profile, wash_profile)
    machine_plan["plan_version"] = "stage4.6"
    machine_plan["geometry_source_id"] = geometry["geometry_source_id"]
    machine_plan["dimension_profile_id"] = vehicle_dimension_profile["dimension_profile_id"]
    machine_plan["motion_validation"] = validate_machine_path(
        machine_plan, motion_model, space_model, nozzle_coverage_plan
    )
    safety_report, collision_plan, schedule = build_continuous_surface_repair_validation(
        surface_plan,
        machine_plan,
        motion_model,
        space_model,
        nozzle_coverage_plan,
        safety_layout,
        actuator_system,
    )
    pose_summary = {
        "pose_count": len(poses),
        "invalid_pose_count": pose_validation["invalid_pose_count"],
        "pose_discontinuity_count": pose_validation["pose_discontinuity_count"],
        "reference_axis_fallback_count": sum(1 for item in poses if item["reference_axis_fallback"]),
        "minimum_standoff_mm": pose_validation["minimum_standoff_mm"],
        "maximum_standoff_mm": pose_validation["maximum_standoff_mm"],
        "maximum_incidence_angle_deg": pose_validation["maximum_incidence_angle_deg"],
        "maximum_orientation_step_deg": pose_validation["maximum_orientation_step_deg"],
        "quaternion_invalid_count": pose_validation["quaternion_invalid_count"],
        "unresolved_orientation_flip_count": pose_validation["unresolved_orientation_flip_count"],
    }
    pose_plan = {
        "plan_version": "stage4.6",
        "geometry_source": {
            "geometry_source_id": geometry["geometry_source_id"],
            "geometry_source_type": geometry["geometry_source_type"],
            "source_path": geometry.get("source_metadata", {}).get("source_path"),
            "unit": geometry["unit"],
        },
        "dimension_profile": {
            "dimension_profile_id": vehicle_dimension_profile["dimension_profile_id"],
            "dimensions": vehicle_dimension_profile["dimensions"],
        },
        "normal_summary": geometry["normal_summary"],
        "pose_summary": pose_summary,
        "poses": poses,
        "validation": pose_validation,
        "warnings": list(geometry["warnings"]) + surface_plan["validation"]["warnings"],
        "limitations": [
            "Candidate geometric nozzle pose only; no inverse kinematics or hardware command.",
            "Fixture geometry is not real CAD or point-cloud scan data.",
        ],
    }
    safety_summary = safety_report["summary"]
    hard_conditions = {
        "geometry_valid": geometry["semantic_summary"]["missing_patches"] == [] and geometry["normal_summary"]["invalid_normal_count"] == 0,
        "pose_valid": pose_validation["invalid_pose_count"] == 0,
        "motion_valid": machine_plan["motion_validation"]["violation_count"] == 0,
        "safety_valid": safety_report["violation_count"] == 0,
        "minimum_clearance_at_least_250": safety_summary["minimum_clearance_mm"] >= 250,
        "safe_stop_at_least_3": safety_summary["safe_stop_point_count"] >= 3,
    }
    if not hard_conditions["geometry_valid"]:
        status = "REJECTED_GEOMETRY_INVALID"
    elif not hard_conditions["pose_valid"]:
        status = "REJECTED_POSE_INVALID"
    elif not all(hard_conditions.values()):
        status = "REJECTED_SAFETY_REGRESSION"
    else:
        status = "ACCEPTED_WITH_WARNINGS"
    validation = {
        "report_version": "stage4.6",
        "status": status,
        "geometry_source_id": geometry["geometry_source_id"],
        "geometry_source_type": geometry["geometry_source_type"],
        "summary": {
            "state_count": len({item["state_id"] for item in surface_plan.get("states", [])}),
            "zone_count": len({zone_id for item in surface_plan.get("states", []) for zone_id in item.get("target_zone_ids", [])}),
            "patch_count": len({item["patch_id"] for item in surface_plan["trajectory_points"]}),
            "wheel_patch_count": len({item["patch_id"] for item in surface_plan["trajectory_points"] if "wheel" in item["patch_id"]}),
            "mapped_path_point_count": surface_plan["mapping_summary"]["mapped_point_count"],
            "mean_mapping_distance_mm": surface_plan["mapping_summary"]["mean_mapping_distance_mm"],
            "maximum_mapping_distance_mm": surface_plan["mapping_summary"]["maximum_mapping_distance_mm"],
            "machine_path_length_mm": machine_plan["summary"]["path_length_mm"],
            "motion_duration_s": machine_plan["summary"]["estimated_motion_duration_s"],
            "schedule_duration_s": safety_summary["schedule_duration_s"],
            "minimum_clearance_mm": safety_summary["minimum_clearance_mm"],
            "static_collision_count": safety_summary["static_collision_count"],
            "vehicle_collision_count": safety_summary["vehicle_collision_count"],
            "forbidden_zone_entry_count": safety_summary["forbidden_zone_entry_count"],
            "unassigned_task_count": safety_summary["unassigned_task_count"],
            "unresolved_conflict_count": safety_summary["unresolved_conflict_count"],
            "deadlock_warning_count": safety_summary["deadlock_warning_count"],
            "safe_stop_point_count": safety_summary["safe_stop_point_count"],
            "violation_count": safety_report["violation_count"],
        },
        "safety_conditions": hard_conditions,
        "pose_validation": pose_validation,
        "motion_validation": machine_plan["motion_validation"],
        "safety_validation": safety_report,
        "warnings": pose_plan["warnings"] + safety_report["warnings"],
        "violations": safety_report["violations"] + pose_validation["issues"],
        "limitations": [
            "Offline geometry-aware candidate only.",
            "No native STEP parser, real scan registration, robot IK, PLC, servo, or hardware control.",
        ],
    }
    return {
        "geometry": geometry,
        "surface_plan": surface_plan,
        "pose_plan": pose_plan,
        "machine_plan": machine_plan,
        "collision_plan": collision_plan,
        "schedule": schedule,
        "validation": validation,
        "space_model": space_model,
    }
