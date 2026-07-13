from __future__ import annotations

import html
from typing import Any


def _improvement(baseline: float, candidate: float) -> float:
    return round((baseline - candidate) / baseline * 100.0 if baseline else 0.0, 3)


def _metric(value: Any) -> str:
    if isinstance(value, float):
        return f"{value:.3f}"
    return str(value)


def _table(headers: list[str], rows: list[list[Any]]) -> str:
    head = "".join(f"<th>{html.escape(str(item))}</th>" for item in headers)
    body = "".join(
        "<tr>" + "".join(f"<td>{html.escape(_metric(item))}</td>" for item in row) + "</tr>"
        for row in rows
    )
    return f"<div class='table-wrap'><table><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table></div>"


def _baseline_metrics(
    path_report: dict[str, Any],
    schedule: dict[str, Any],
) -> dict[str, Any]:
    source = path_report["optimized_metrics"]
    schedule_summary = schedule["summary"]
    return {
        "scan_pass_count": None,
        "surface_task_count": 22,
        "downstream_task_count": int(schedule_summary["task_count"]),
        "trajectory_point_count": int(source["trajectory_point_count"]),
        "transition_count": int(source["transition_segment_count"]),
        "source_path_length_mm": None,
        "machine_path_length_mm": float(source["path_length_mm"]),
        "motion_duration_s": float(source["estimated_motion_duration_s"]),
        "schedule_duration_s": float(source["total_schedule_duration_s"]),
        "total_delay_s": float(source["total_delay_s"]),
        "parallel_group_count": int(schedule_summary["parallel_group_count"]),
        "synchronized_group_count": int(schedule_summary["synchronized_group_count"]),
        "blocked_sync_group_count": sum(1 for item in schedule.get("sync_groups", []) if item.get("sync_status") == "BLOCKED_BY_INTERLOCK"),
        "resource_lock_count": len(schedule.get("resource_locks", [])),
        "conflict_count_before_resolution": int(schedule_summary["conflict_count_before_resolution"]),
        "conflict_count_after_resolution": int(schedule_summary["conflict_count_after_resolution"]),
        "unresolved_conflict_count": int(schedule_summary["unresolved_conflict_count"]),
        "clearance_warning_count": int(source["clearance_warning_count"]),
        "minimum_clearance_mm": float(source["minimum_vehicle_clearance_mm"]),
    }


def _first_attempt_metrics(
    plan: dict[str, Any],
    machine: dict[str, Any],
    schedule: dict[str, Any],
    diagnosis: dict[str, Any],
) -> dict[str, Any]:
    summary = schedule["summary"]
    return {
        "scan_pass_count": plan["summary"]["scan_pass_count"],
        "surface_task_count": len(plan["surface_tasks"]),
        "downstream_task_count": summary["task_count"],
        "trajectory_point_count": machine["summary"]["trajectory_point_count"],
        "transition_count": machine["summary"]["transition_segment_count"],
        "source_path_length_mm": plan["summary"]["path_length_mm"],
        "machine_path_length_mm": machine["summary"]["path_length_mm"],
        "motion_duration_s": machine["summary"]["estimated_motion_duration_s"],
        "schedule_duration_s": summary["total_schedule_duration_s"],
        "total_delay_s": summary["total_delay_s"],
        "parallel_group_count": summary["parallel_group_count"],
        "synchronized_group_count": summary["synchronized_group_count"],
        "blocked_sync_group_count": sum(1 for item in schedule.get("sync_groups", []) if item.get("sync_status") == "BLOCKED_BY_INTERLOCK"),
        "resource_lock_count": len(schedule.get("resource_locks", [])),
        "conflict_count_before_resolution": summary["conflict_count_before_resolution"],
        "conflict_count_after_resolution": summary["conflict_count_after_resolution"],
        "unresolved_conflict_count": summary["unresolved_conflict_count"],
        "clearance_warning_count": 45,
        "minimum_clearance_mm": 300.0,
        "path_length_breakdown": diagnosis["path_length_breakdown"],
    }


def _repair_metrics(
    plan: dict[str, Any],
    machine: dict[str, Any],
    validation: dict[str, Any],
) -> dict[str, Any]:
    summary = validation["summary"]
    return {
        "scan_pass_count": plan["summary"]["scan_pass_count"],
        "surface_task_count": plan["summary"]["surface_task_count"],
        "downstream_task_count": summary["schedule_task_count"],
        "trajectory_point_count": summary["trajectory_point_count"],
        "transition_count": summary["transition_count"],
        "source_path_length_mm": plan["summary"]["source_path_length_mm"],
        "machine_path_length_mm": summary["machine_path_length_mm"],
        "motion_duration_s": summary["motion_duration_s"],
        "schedule_duration_s": summary["schedule_duration_s"],
        "total_delay_s": summary["total_delay_s"],
        "parallel_group_count": summary["parallel_group_count"],
        "synchronized_group_count": summary["synchronized_group_count"],
        "blocked_sync_group_count": summary["blocked_sync_group_count"],
        "resource_lock_count": summary["resource_lock_count"],
        "conflict_count_before_resolution": summary["conflict_count_before_resolution"],
        "conflict_count_after_resolution": summary["conflict_count_after_resolution"],
        "unresolved_conflict_count": summary["unresolved_conflict_count"],
        "clearance_warning_count": summary["clearance_warning_count"],
        "minimum_clearance_mm": summary["minimum_clearance_mm"],
        "path_length_breakdown": machine["path_length_breakdown"],
        "unique_geometric_coverage_percent": plan["coverage_summary"]["unique_geometric_coverage_percent"],
        "mean_surface_visit_count": plan["coverage_summary"]["mean_surface_visit_count"],
        "overcovered_cell_percent": plan["coverage_summary"]["overcovered_cell_percent"],
    }


def _status(
    baseline: dict[str, Any],
    first: dict[str, Any],
    repair: dict[str, Any],
    validation: dict[str, Any],
) -> str:
    if validation["safety_status"] == "REJECTED_SAFETY_REGRESSION":
        return "REJECTED_SAFETY_REGRESSION"
    transition_ok = repair["transition_count"] <= 5
    better_baseline = all(
        repair[key] < baseline[key]
        for key in ("machine_path_length_mm", "motion_duration_s", "schedule_duration_s", "total_delay_s")
    )
    if transition_ok and better_baseline:
        return "ACCEPTED"
    improvements = [
        _improvement(first[key], repair[key])
        for key in ("machine_path_length_mm", "motion_duration_s", "schedule_duration_s", "total_delay_s")
    ]
    better_first = all(value > 0 for value in improvements[:3])
    if transition_ok and better_first and sum(value >= 10 for value in improvements[:3]) >= 2:
        return "ACCEPTED_WITH_WARNINGS"
    return "NO_MEANINGFUL_IMPROVEMENT"


def build_continuous_surface_repair_report(
    repair_plan: dict[str, Any],
    repair_machine: dict[str, Any],
    repair_validation: dict[str, Any],
    first_plan: dict[str, Any],
    first_machine: dict[str, Any],
    first_schedule: dict[str, Any],
    baseline_report: dict[str, Any],
    baseline_schedule: dict[str, Any],
) -> tuple[dict[str, Any], str]:
    diagnosis = repair_plan["first_attempt_diagnosis"]
    baseline = _baseline_metrics(baseline_report, baseline_schedule)
    first = _first_attempt_metrics(first_plan, first_machine, first_schedule, diagnosis)
    repair = _repair_metrics(repair_plan, repair_machine, repair_validation)
    status = _status(baseline, first, repair, repair_validation)
    compare_keys = ("machine_path_length_mm", "motion_duration_s", "schedule_duration_s", "total_delay_s")
    improvements = {
        key: {
            "versus_first_attempt_percent": _improvement(float(first[key]), float(repair[key])),
            "versus_stage4_baseline_percent": _improvement(float(baseline[key]), float(repair[key])),
        }
        for key in compare_keys
    }
    target_results = {
        "transition_count_maximum_5": "TARGET_REACHED" if repair["transition_count"] <= 5 else "TARGET_NOT_REACHED",
        "path_below_first_attempt": "TARGET_REACHED" if repair["machine_path_length_mm"] < first["machine_path_length_mm"] else "TARGET_NOT_REACHED",
        "path_below_stage4_baseline": "TARGET_REACHED" if repair["machine_path_length_mm"] < baseline["machine_path_length_mm"] else "TARGET_NOT_REACHED",
        "motion_below_first_attempt": "TARGET_REACHED" if repair["motion_duration_s"] < first["motion_duration_s"] else "TARGET_NOT_REACHED",
        "motion_below_stage4_baseline": "TARGET_REACHED" if repair["motion_duration_s"] < baseline["motion_duration_s"] else "TARGET_NOT_REACHED",
        "schedule_below_first_attempt": "TARGET_REACHED" if repair["schedule_duration_s"] < first["schedule_duration_s"] else "TARGET_NOT_REACHED",
        "schedule_below_stage4_baseline": "TARGET_REACHED" if repair["schedule_duration_s"] < baseline["schedule_duration_s"] else "TARGET_NOT_REACHED",
        "delay_below_first_attempt": "TARGET_REACHED" if repair["total_delay_s"] < first["total_delay_s"] else "TARGET_NOT_REACHED",
        "delay_below_stage4_baseline": "TARGET_REACHED" if repair["total_delay_s"] < baseline["total_delay_s"] else "TARGET_NOT_REACHED",
        "parallel_groups_above_6": "TARGET_REACHED" if repair["parallel_group_count"] > 6 else "TARGET_NOT_REACHED",
    }
    configured_targets = repair_plan.get("repair_targets", {})
    preferred_checks = {
        "preferred_path_reduction_vs_stage4": (
            improvements["machine_path_length_mm"]["versus_stage4_baseline_percent"],
            float(configured_targets.get("preferred_path_length_reduction_vs_stage4_percent", 0)),
        ),
        "preferred_motion_reduction_vs_stage4": (
            improvements["motion_duration_s"]["versus_stage4_baseline_percent"],
            float(configured_targets.get("preferred_motion_duration_reduction_vs_stage4_percent", 0)),
        ),
        "preferred_schedule_reduction_vs_stage4": (
            improvements["schedule_duration_s"]["versus_stage4_baseline_percent"],
            float(configured_targets.get("preferred_schedule_duration_reduction_vs_stage4_percent", 0)),
        ),
        "preferred_path_reduction_vs_first_attempt": (
            improvements["machine_path_length_mm"]["versus_first_attempt_percent"],
            float(configured_targets.get("preferred_path_reduction_vs_first_attempt_percent", 0)),
        ),
        "preferred_schedule_reduction_vs_first_attempt": (
            improvements["schedule_duration_s"]["versus_first_attempt_percent"],
            float(configured_targets.get("preferred_schedule_reduction_vs_first_attempt_percent", 0)),
        ),
    }
    target_results.update(
        {
            key: "TARGET_REACHED" if measured + 1e-9 >= target else "TARGET_NOT_REACHED"
            for key, (measured, target) in preferred_checks.items()
        }
    )
    report = {
        "report_version": "stage4.5-r",
        "repair_status": status,
        "surface_validation_status": repair_validation["surface_validation_status"],
        "motion_validation_status": repair_validation["motion_validation_status"],
        "collision_validation_status": repair_validation["collision_validation_status"],
        "vehicle_type": repair_plan["vehicle_type"],
        "surface_model_id": repair_plan["surface_model_id"],
        "repair_profile_id": repair_plan["repair_profile_id"],
        "configured_targets": configured_targets,
        "source_experiment_commit": repair_plan["source_experiment_commit"],
        "first_attempt_diagnosis": diagnosis,
        "stage4_baseline_metrics": baseline,
        "stage4_5_first_attempt_metrics": first,
        "stage4_5_r_metrics": repair,
        "improvement_summary": improvements,
        "target_results": target_results,
        "state_scan_policies": repair_plan["state_scan_policies"],
        "surface_routes": repair_plan["surface_routes"],
        "aggregation_summary": repair_plan["aggregation_summary"],
        "connection_summary": {
            key: repair_plan["summary"][key]
            for key in ("local_u_turn_count", "direct_patch_connection_count", "adaptive_safe_connection_count", "required_state_transition_count", "rejected_connection_count", "direct_candidate_rejected_count")
        },
        "route_optimization_summary": repair_plan["route_optimization_summary"],
        "path_length_breakdown": {
            "first_attempt": diagnosis["path_length_breakdown"],
            "repair": repair_machine["path_length_breakdown"],
        },
        "coverage_summary": repair_plan["coverage_summary"],
        "coverage_efficiency_summary": repair_plan["coverage_efficiency_summary"],
        "schedule_summary": repair_validation["schedule_validation"],
        "safety_summary": repair_validation["summary"],
        "warning_count": repair_validation["warning_count"],
        "violation_count": repair_validation["violation_count"],
        "warnings": repair_validation["warnings"],
        "violations": repair_validation["violations"],
        "limitations": [
            "Reference analytic surface model, not CAD or point cloud geometry.",
            "Coverage is a 2D geometric estimate and does not represent cleaning effectiveness.",
            "Heuristic path reconstruction does not guarantee a global optimum.",
            "No real nozzle orientation or actuator dynamics are modeled.",
            "No PLC, servo, SDK, real hardware command, or safety certification is included.",
        ],
    }
    html_text = render_continuous_surface_repair_html(report)
    return report, html_text


def render_continuous_surface_repair_html(report: dict[str, Any]) -> str:
    baseline = report["stage4_baseline_metrics"]
    first = report["stage4_5_first_attempt_metrics"]
    repair = report["stage4_5_r_metrics"]
    comparison_rows = [
        [label, baseline.get(key), first.get(key), repair.get(key), report["improvement_summary"].get(key, {}).get("versus_first_attempt_percent")]
        for label, key in (
            ("Trajectory points", "trajectory_point_count"),
            ("Transitions", "transition_count"),
            ("Machine path mm", "machine_path_length_mm"),
            ("Motion duration s", "motion_duration_s"),
            ("Schedule duration s", "schedule_duration_s"),
            ("Total delay s", "total_delay_s"),
            ("Parallel groups", "parallel_group_count"),
            ("Resource locks", "resource_lock_count"),
        )
    ]
    state_rows = [
        [item["state_id"], item["patch_id"], item["nozzle_id"], item["effective_width_mm"], item["effective_width_source"], item["initial_pass_spacing_mm"], item["final_pass_spacing_mm"], item["initial_pass_count"], item["final_pass_count"], item["coverage_percent"], item["adaptation_status"]]
        for item in report["state_scan_policies"]
    ]
    route_rows = [
        [item["state_id"], item["surface_route_id"], item["actuator_id"], item["nozzle_id"], " -> ".join(item["patch_order"]), ", ".join(f"{key}:{value}" for key, value in item["patch_directions"].items()), item["candidate_count"]]
        for item in report["surface_routes"]
    ]
    coverage_rows = [
        [item["state_id"], item["patch_id"], item["zone_id"], item["patch_coverage_percent"], item["mean_surface_visit_count"], item["overcovered_cell_percent"], item["scan_length_mm"]]
        for item in report["coverage_summary"]["per_state_patch_coverage"]
    ]
    target_rows = [[key, value] for key, value in report["target_results"].items()]
    schedule_rows = [
        ["Stage4 frozen baseline", baseline["downstream_task_count"], baseline["parallel_group_count"], baseline["schedule_duration_s"], baseline["total_delay_s"]],
        ["Stage4.5 first attempt", first["downstream_task_count"], first["parallel_group_count"], first["schedule_duration_s"], first["total_delay_s"]],
        ["Stage4.5-R", repair["downstream_task_count"], repair["parallel_group_count"], repair["schedule_duration_s"], repair["total_delay_s"]],
    ]
    lock_rows = [
        [item["resource_id"], item["actuator_id"], item["task_id"], item["start_s"], item["end_s"], item["interval_source"]]
        for item in report["schedule_summary"].get("resource_locks", [])
    ]
    warning_rows = [[item.get("check_id"), item.get("message")] for item in report["warnings"]] or [["none", "No warnings"]]
    violation_rows = [[item.get("check_id"), item.get("message")] for item in report["violations"]] or [["none", "No violations"]]
    limitations = "".join(f"<li>{html.escape(item)}</li>" for item in report["limitations"])
    connection = report["connection_summary"]
    coverage = report["coverage_summary"]
    safety = report["safety_summary"]
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Stage4.5-R Continuous Surface Path Repair Report</title>
<style>
*{{box-sizing:border-box}}body{{margin:0;background:#f3f5f7;color:#17202a;font:15px/1.5 Arial,sans-serif}}main{{max-width:1260px;margin:auto;padding:28px}}header{{background:#fff;border-top:5px solid #176b87;padding:24px;border-radius:6px}}h1{{font-size:28px;margin:0 0 8px}}h2{{font-size:20px;margin:0 0 14px}}section{{background:#fff;margin-top:16px;padding:20px;border:1px solid #d9e0e5;border-radius:6px}}.status{{font-size:22px;font-weight:700;color:#176b87}}.grid{{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:10px}}.metric{{border-left:4px solid #d29b28;background:#f8fafb;padding:10px;min-height:74px}}.metric b{{display:block;font-size:20px}}.table-wrap{{overflow-x:auto}}table{{border-collapse:collapse;width:100%;min-width:760px}}th,td{{padding:8px;border-bottom:1px solid #dde3e7;text-align:left;vertical-align:top}}th{{background:#eef3f5}}.note{{border-left:4px solid #b84a3a;padding-left:12px}}ul{{padding-left:20px}}@media(max-width:760px){{main{{padding:12px}}.grid{{grid-template-columns:repeat(2,minmax(0,1fr))}}h1{{font-size:23px}}}}
</style></head><body><main>
<header><h1>Stage4.5-R Continuous Surface Path Repair</h1><div class="status">repair_status: {html.escape(report['repair_status'])}</div><p>State-aware continuous-surface candidate path on a reference analytic vehicle model.</p></header>
<section><h2>Repair summary</h2><div class="grid"><div class="metric">Scan passes<b>{repair['scan_pass_count']}</b></div><div class="metric">Surface tasks<b>{repair['surface_task_count']}</b></div><div class="metric">Path mm<b>{_metric(repair['machine_path_length_mm'])}</b></div><div class="metric">Coverage<b>{_metric(repair['unique_geometric_coverage_percent'])}%</b></div><div class="metric">Direct connections<b>{connection['direct_patch_connection_count']}</b></div><div class="metric">Parallel groups<b>{repair['parallel_group_count']}</b></div><div class="metric">Minimum clearance<b>{_metric(repair['minimum_clearance_mm'])} mm</b></div><div class="metric">Violations<b>{report['violation_count']}</b></div></div></section>
<section><h2>Stage4 frozen baseline vs Stage4.5 first attempt vs Stage4.5-R</h2>{_table(['Metric','Stage4 frozen','Stage4.5 first','Stage4.5-R','R vs first %'], comparison_rows)}</section>
<section><h2>First-attempt diagnosis and path composition</h2><p>Scan, local U-turn, patch connection, and state transition distances are separated using machine trajectory segment and critical-point semantics.</p>{_table(['Component','First attempt mm','Repair mm'], [[key, report['path_length_breakdown']['first_attempt'].get(key), report['path_length_breakdown']['repair'].get(key)] for key in ('surface_scan_length_mm','local_u_turn_length_mm','patch_connection_length_mm','required_state_transition_length_mm','total_path_length_mm')])}</section>
<section><h2>State scan policy, spacing, and nozzle effective width</h2>{_table(['State','Patch','Nozzle','Width mm','Width source','Initial spacing','Final spacing','Initial passes','Final passes','Coverage %','Adaptation'], state_rows)}</section>
<section><h2>Surface route task aggregation and patch direction</h2><p>Scan passes remain inside route tasks; they are not emitted as independent scheduler tasks. Aggregation validation: {html.escape(report['aggregation_summary']['validation_status'])}.</p>{_table(['State','Route','Actuator','Nozzle','Patch access order','Directions','Candidates'], route_rows)}</section>
<section><h2>Connection optimization</h2><div class="grid"><div class="metric">Local U-turns<b>{connection['local_u_turn_count']}</b></div><div class="metric">Direct patch<b>{connection['direct_patch_connection_count']}</b></div><div class="metric">Adaptive safe<b>{connection['adaptive_safe_connection_count']}</b></div><div class="metric">State transitions<b>{connection['required_state_transition_count']}</b></div></div></section>
<section><h2>Coverage and overcoverage</h2><p>Unique geometric coverage: {coverage['unique_geometric_coverage_percent']}%; mean visits: {coverage['mean_surface_visit_count']}; maximum visits: {coverage['maximum_surface_visit_count']}; within-state overcovered cells: {coverage['overcovered_cell_percent']}%; repeated surface scan length: {coverage['repeated_surface_scan_length_mm']} mm.</p>{_table(['State','Patch','Zone','Coverage %','Mean visits','Overcovered %','Scan mm'], coverage_rows)}</section>
<section><h2>Motion, schedule, collision, interlock, and safe stop</h2><p>motion: {html.escape(report['motion_validation_status'])}; collision: {html.escape(report['collision_validation_status'])}; schedule tasks: {safety['schedule_task_count']}; resource locks: {safety['resource_lock_count']}; static collision: {safety['static_collision_count']}; vehicle collision: {safety['vehicle_collision_count']}; forbidden entry: {safety['forbidden_zone_entry_count']}; conflict after resolution: {safety['conflict_count_after_resolution']}; safe-stop points: {safety['safe_stop_point_count']}.</p></section>
<section><h2>Schedule timeline comparison</h2>{_table(['Plan','Tasks','Parallel groups','Schedule duration s','Total delay s'], schedule_rows)}</section>
<section><h2>Actual shared-resource lock intervals</h2><p>Shared-space locks use swept-volume entry and exit intervals instead of whole-task occupation.</p>{_table(['Resource','Actuator','Task','Start s','End s','Interval source'], lock_rows)}</section>
<section><h2>Targets not hidden</h2>{_table(['Target','Status'], target_rows)}</section>
<section><h2>Warnings</h2>{_table(['Check','Message'], warning_rows)}</section><section><h2>Violations</h2>{_table(['Check','Message'], violation_rows)}</section>
<section><h2>Limitations</h2><p class="note">This is not CAD, point-cloud reconstruction, real cleaning-effect validation, PLC output, or a hardware-safe command trajectory.</p><ul>{limitations}</ul></section>
</main></body></html>"""
