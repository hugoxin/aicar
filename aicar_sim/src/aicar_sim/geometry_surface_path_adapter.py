from __future__ import annotations

import copy
from collections import defaultdict
from typing import Any

from aicar_sim.geometry_math import distance
from aicar_sim.geometry_semantic_mapper import canonical_patch
from aicar_sim.nozzle_pose_generator import generate_nozzle_pose


def _tuple(point: dict[str, float]) -> tuple[float, float, float]:
    return float(point["x_mm"]), float(point["y_mm"]), float(point["z_mm"])


def adapt_stage4_5_path(
    stage4_5_plan: dict[str, Any],
    geometry: dict[str, Any],
    semantic_map: dict[str, Any],
    pose_profile: dict[str, Any],
) -> dict[str, Any]:
    samples = geometry["points"] or geometry["vertices"]
    normals = geometry["point_normals"]
    by_patch: dict[str, list[tuple[dict[str, Any], dict[str, float]]]] = defaultdict(list)
    for point, normal in zip(samples, normals):
        by_patch[str(point["patch_id"])].append((point, normal))
    reference_scales = {
        "x": float(geometry["dimension_summary"]["target_dimensions"]["width_mm"]) / 1800.0,
        "y": float(geometry["dimension_summary"]["target_dimensions"]["length_mm"]) / 4700.0,
        "z": float(geometry["dimension_summary"]["target_dimensions"]["height_mm"]) / 1450.0,
    }
    mapped_segments = []
    poses = []
    mapping_distances = []
    previous_patch = previous_state = None
    previous_quaternion = None
    sequence = 0
    for segment in stage4_5_plan["path_segments"]:
        mapped_segment = copy.deepcopy(segment)
        mapped_segment["points"] = []
        for source_point in segment["points"]:
            patch = canonical_patch(str(source_point["patch_id"]), semantic_map)
            if not patch or not by_patch.get(patch):
                raise ValueError(f"target geometry missing patch samples for {source_point['patch_id']}")
            original = source_point["surface_point"]
            target_reference = {
                "x_mm": float(original["x_mm"]) * reference_scales["x"],
                "y_mm": float(original["y_mm"]) * reference_scales["y"],
                "z_mm": float(original["z_mm"]) * reference_scales["z"],
            }
            is_process = str(segment.get("segment_type", "process")) == "process"
            is_surface_scan = is_process and source_point.get("critical_point_type") not in {"PATCH_CONNECTION", "STATE_BOUNDARY"}
            if not is_surface_scan:
                mapped = target_reference
                _, normal = min(by_patch[patch], key=lambda item: distance(_tuple(item[0]), _tuple(target_reference)))
                mapping_distance = 0.0
                method = "scaled_stage4_5_transition"
            elif geometry["geometry_source_type"] == "ANALYTIC_REFERENCE":
                mapped = target_reference
                _, normal = min(by_patch[patch], key=lambda item: distance(_tuple(item[0]), _tuple(target_reference)))
                mapping_distance = 0.0
                method = "analytic_dimension_transform"
            else:
                nearest, normal = min(by_patch[patch], key=lambda item: distance(_tuple(item[0]), _tuple(target_reference)))
                mapped = {axis: float(nearest[axis]) for axis in ("x_mm", "y_mm", "z_mm")}
                mapping_distance = distance(_tuple(mapped), _tuple(target_reference))
                method = "nearest_patch_sample"
            boundary = previous_patch is not None and (patch != previous_patch or source_point["state_id"] != previous_state)
            pose = generate_nozzle_pose(mapped, normal, pose_profile, previous_quaternion)
            pose.update({
                "sequence_index": sequence,
                "state_id": source_point["state_id"],
                "zone_id": source_point["zone_id"],
                "patch_id": patch,
                "source_patch_id": source_point["patch_id"],
                "nozzle_id": source_point["nozzle_id"],
                "actuator_id": segment.get("preferred_actuator_id"),
                "surface_task_id": segment["segment_id"],
                "scan_pass_id": source_point.get("scan_pass_id"),
                "segment_id": segment["segment_id"],
                "is_orientation_boundary": boundary or source_point.get("critical_point_type") in {"PATCH_CONNECTION", "STATE_BOUNDARY"},
            })
            previous_quaternion = tuple(pose["orientation_quaternion"][key] for key in ("w", "x", "y", "z"))
            if is_surface_scan:
                machine_distance = float(pose_profile["position"]["preferred_standoff_mm"]) + 210.0
                machine = {
                    "x_mm": mapped["x_mm"] + float(normal["x"]) * machine_distance,
                    "y_mm": mapped["y_mm"] + float(normal["y"]) * machine_distance,
                    "z_mm": max(300.0, mapped["z_mm"] + float(normal["z"]) * machine_distance),
                }
            else:
                original_machine = source_point["machine_point"]
                machine = {
                    "x_mm": float(original_machine["x_mm"]),
                    "y_mm": float(original_machine["y_mm"]),
                    "z_mm": float(original_machine["z_mm"]),
                }
            mapped_point = copy.deepcopy(source_point)
            mapped_point.update({
                "patch_id": patch,
                "original_analytic_surface_point": copy.deepcopy(original),
                "mapped_geometry_surface_point": mapped,
                "surface_point": mapped,
                "mapping_distance_mm": round(mapping_distance, 6),
                "geometry_normal": normal,
                "normal": normal,
                "nozzle_pose": pose,
                "nozzle_point": pose["position"],
                "standoff_mm": pose["standoff_mm"],
                "machine_point": machine,
                "mapping_method": method,
                "mapping_confidence": round(max(0.0, 1.0 - mapping_distance / 500.0), 6),
                "sequence_index": sequence,
                "actuator_id": segment.get("preferred_actuator_id"),
                "surface_task_id": segment["segment_id"],
            })
            mapped_segment["points"].append(mapped_point)
            poses.append(pose)
            mapping_distances.append(mapping_distance)
            previous_patch, previous_state = patch, source_point["state_id"]
            sequence += 1
        mapped_segment["patch_ids"] = sorted({item["patch_id"] for item in mapped_segment["points"]})
        mapped_segments.append(mapped_segment)
    mapped_plan = copy.deepcopy(stage4_5_plan)
    mapped_plan["plan_version"] = "stage4.6"
    mapped_plan["geometry_source_id"] = geometry["geometry_source_id"]
    mapped_plan["geometry_source_type"] = geometry["geometry_source_type"]
    mapped_plan["path_segments"] = mapped_segments
    mapped_plan["trajectory_points"] = [point for segment in mapped_segments for point in segment["points"]]
    mapped_plan["summary"]["trajectory_point_count"] = len(mapped_plan["trajectory_points"])
    mapped_plan["mapping_summary"] = {
        "mapped_point_count": len(mapping_distances),
        "mean_mapping_distance_mm": round(sum(mapping_distances) / len(mapping_distances), 6),
        "maximum_mapping_distance_mm": round(max(mapping_distances), 6),
        "mapping_method": "analytic_dimension_transform" if geometry["geometry_source_type"] == "ANALYTIC_REFERENCE" else "nearest_patch_sample",
    }
    return {"surface_plan": mapped_plan, "poses": poses}
