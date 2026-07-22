from __future__ import annotations

import html
from typing import Any


def _esc(value: Any) -> str:
    return html.escape(str(value))


def _improvement(baseline: float, continuous: float) -> float:
    if baseline == 0:
        return 0.0
    return round((baseline - continuous) / baseline * 100.0, 3)


def _polyline(points: list[dict[str, Any]], color: str, css_class: str) -> str:
    sampled = points[:: max(1, len(points) // 900)]
    coords = " ".join(f"{330 + float(item['x_mm']) * .08:.1f},{340 - float(item['y_mm']) * .08:.1f}" for item in sampled)
    return f'<polyline class="{css_class}" points="{coords}" fill="none" stroke="{color}" stroke-width="1.6" />'


def _top_view(baseline_path: dict[str, Any], continuous_path: dict[str, Any], space_model: dict[str, Any], safety_layout: dict[str, Any]) -> str:
    safe = space_model["vehicle_envelope"]["safe_envelope"]
    x = 330 + float(safe["x_min_mm"]) * .08
    y = 340 - float(safe["y_max_mm"]) * .08
    width = (float(safe["x_max_mm"]) - float(safe["x_min_mm"])) * .08
    height = (float(safe["y_max_mm"]) - float(safe["y_min_mm"])) * .08
    obstacles = []
    for item in safety_layout.get("static_obstacles", []):
        bounds = item["bounds"]
        ox = 330 + float(bounds["x_min_mm"]) * .08
        oy = 340 - float(bounds["y_max_mm"]) * .08
        ow = (float(bounds["x_max_mm"]) - float(bounds["x_min_mm"])) * .08
        oh = (float(bounds["y_max_mm"]) - float(bounds["y_min_mm"])) * .08
        obstacles.append(f'<rect class="obstacle" x="{ox:.1f}" y="{oy:.1f}" width="{ow:.1f}" height="{oh:.1f}"/>')
    return (
        '<svg viewBox="0 0 660 680" aria-label="Stage4.5 wash bay top view">'
        '<rect class="bay" x="42" y="20" width="576" height="640"/>'
        f'<rect class="safe-envelope" x="{x:.1f}" y="{y:.1f}" width="{width:.1f}" height="{height:.1f}"/>'
        + "".join(obstacles)
        + _polyline(baseline_path["trajectory_points"], "#98a2b3", "baseline-path")
        + _polyline(continuous_path["trajectory_points"], "#087f5b", "continuous-path")
        + "</svg>"
    )


def _side_view(continuous_path: dict[str, Any]) -> str:
    sampled = continuous_path["trajectory_points"][:: max(1, len(continuous_path["trajectory_points"]) // 900)]
    coords = " ".join(f"{50 + (float(item['y_mm']) + 3800) * .07:.1f},{330 - float(item['z_mm']) * .1:.1f}" for item in sampled)
    return f'<svg viewBox="0 0 640 360" aria-label="Stage4.5 side view"><rect class="bay" x="40" y="20" width="552" height="310"/><rect class="vehicle-side" x="141" y="185" width="329" height="145"/><polyline points="{coords}" fill="none" stroke="#087f5b" stroke-width="1.5"/></svg>'


def _metric_cards(report: dict[str, Any]) -> str:
    labels = [
        ("trajectory_point_count", "trajectory points"),
        ("transition_segment_count", "transition"),
        ("path_length_mm", "path length mm"),
        ("motion_duration_s", "motion duration s"),
        ("schedule_duration_s", "schedule duration s"),
        ("total_delay_s", "total delay s"),
    ]
    cards = []
    for key, label in labels:
        item = report["improvement_summary"][key]
        cards.append(f'<div class="metric"><span>{_esc(label)}</span><b>{_esc(item["baseline"])} → {_esc(item["continuous"])}</b><em>{_esc(item["improvement_percent"])}%</em></div>')
    return "".join(cards)


def build_continuous_surface_report(
    surface_plan: dict[str, Any],
    continuous_machine_path: dict[str, Any],
    validation_report: dict[str, Any],
    baseline_path: dict[str, Any],
    baseline_report: dict[str, Any],
    surface_model: dict[str, Any],
    scan_profile: dict[str, Any],
    space_model: dict[str, Any],
    safety_layout: dict[str, Any],
) -> tuple[dict[str, Any], str]:
    baseline = baseline_report["optimized_metrics"]
    summary = validation_report["summary"]
    continuous = {
        "trajectory_point_count": continuous_machine_path["summary"]["trajectory_point_count"],
        "source_path_segment_count": surface_plan["summary"]["surface_path_segment_count"],
        "scan_pass_count": surface_plan["summary"]["scan_pass_count"],
        "connection_count": surface_plan["summary"]["connection_count"],
        "transition_segment_count": continuous_machine_path["summary"]["transition_segment_count"],
        "path_length_mm": continuous_machine_path["summary"]["path_length_mm"],
        "motion_duration_s": continuous_machine_path["summary"]["estimated_motion_duration_s"],
        "schedule_duration_s": summary["schedule_duration_s"],
        "total_delay_s": summary["total_delay_s"],
        "synchronized_group_count": validation_report["schedule_validation"]["summary"]["synchronized_group_count"],
        "parallel_group_count": validation_report["schedule_validation"]["summary"]["parallel_group_count"],
        "minimum_clearance_mm": summary["minimum_clearance_mm"],
        "clearance_warning_count": summary["clearance_warning_count"],
        "coverage_percent": summary["coverage_percent"],
    }
    baseline_metrics = {
        "trajectory_point_count": baseline["trajectory_point_count"],
        "transition_segment_count": baseline["transition_segment_count"],
        "path_length_mm": baseline["path_length_mm"],
        "motion_duration_s": baseline["estimated_motion_duration_s"],
        "schedule_duration_s": baseline["total_schedule_duration_s"],
        "total_delay_s": baseline["total_delay_s"],
        "synchronized_group_count": baseline["synchronized_group_count"],
        "parallel_group_count": baseline_report.get("safety_validation", {}).get("schedule_validation", {}).get("parallel_group_count", 18),
        "minimum_clearance_mm": baseline["minimum_vehicle_clearance_mm"],
        "clearance_warning_count": baseline["clearance_warning_count"],
    }
    pairs = {
        "trajectory_point_count": (baseline_metrics["trajectory_point_count"], continuous["trajectory_point_count"]),
        "transition_segment_count": (baseline_metrics["transition_segment_count"], continuous["transition_segment_count"]),
        "path_length_mm": (baseline_metrics["path_length_mm"], continuous["path_length_mm"]),
        "motion_duration_s": (baseline_metrics["motion_duration_s"], continuous["motion_duration_s"]),
        "schedule_duration_s": (baseline_metrics["schedule_duration_s"], continuous["schedule_duration_s"]),
        "total_delay_s": (baseline_metrics["total_delay_s"], continuous["total_delay_s"]),
    }
    improvements = {key: {"baseline": round(float(values[0]), 3), "continuous": round(float(values[1]), 3), "improvement_percent": _improvement(float(values[0]), float(values[1]))} for key, values in pairs.items()}
    target_map = {
        "path_length_mm": float(scan_profile["targets"]["preferred_path_length_reduction_percent"]),
        "transition_segment_count": float(scan_profile["targets"]["preferred_transition_reduction_percent"]),
        "motion_duration_s": float(scan_profile["targets"]["preferred_motion_duration_reduction_percent"]),
        "schedule_duration_s": float(scan_profile["targets"]["preferred_schedule_duration_reduction_percent"]),
    }
    targets = {
        key: {
            "target_percent": target,
            "actual_percent": improvements[key]["improvement_percent"],
            "status": "TARGET_REACHED" if improvements[key]["improvement_percent"] >= target else "TARGET_NOT_REACHED",
        }
        for key, target in target_map.items()
    }
    report = {
        "report_version": "stage4.5",
        "reconstruction_status": validation_report["reconstruction_status"],
        "surface_validation_status": validation_report["surface_validation_status"],
        "motion_validation_status": validation_report["motion_validation_status"],
        "collision_validation_status": validation_report["collision_validation_status"],
        "vehicle_type": surface_plan["vehicle_type"],
        "surface_model_id": surface_plan["surface_model_id"],
        "scan_profile_id": surface_plan["scan_profile_id"],
        "baseline_metrics": baseline_metrics,
        "continuous_metrics": continuous,
        "improvement_summary": improvements,
        "target_results": targets,
        "coverage_summary": surface_plan["coverage_summary"],
        "connection_summary": {
            key: surface_plan["summary"][key]
            for key in ("local_connection_count", "direct_patch_connection_count", "adaptive_safe_connection_count", "required_state_transition_count", "rejected_connection_count")
        },
        "safety_summary": summary,
        "warning_count": validation_report["warning_count"],
        "violation_count": validation_report["violation_count"],
        "warnings": validation_report["warnings"],
        "violations": validation_report["violations"],
        "limitations": [*surface_plan["limitations"], *validation_report["limitations"]],
    }

    patch_cards = "".join(f'<div class="patch"><b>{_esc(item["patch_id"])}</b><span>{_esc(item["zone_id"])}</span><em>{_esc(item["surface_type"])}</em></div>' for item in [*surface_model["surface_patches"], *surface_model["wheel_patches"]])
    coverage_rows = "".join(f'<tr><td>{_esc(item["patch_id"])}</td><td>{_esc(item["zone_id"])}</td><td>{item["patch_coverage_percent"]}%</td><td>{item["uncovered_cell_count"]}</td><td>{item["pass_spacing_mm"]}</td><td>{item["effective_width_mm"]}</td></tr>' for item in surface_plan["coverage_summary"]["patch_coverage"])
    connection_rows = "".join(f'<tr><td>{_esc(item["connection_id"])}</td><td>{_esc(item["connection_type"])}</td><td>{_esc(item["source_patch_id"])}</td><td>{_esc(item["target_patch_id"])}</td><td>{_esc(item["length_mm"])}</td><td>{_esc(item["safety_status"])}</td></tr>' for item in surface_plan["connections"])
    target_rows = "".join(f'<tr><td>{_esc(key)}</td><td>{item["target_percent"]}%</td><td>{item["actual_percent"]}%</td><td class="{item["status"].lower()}">{item["status"]}</td></tr>' for key, item in targets.items())
    warning_items = "".join(f'<li><b>{_esc(item.get("check_id"))}</b> {_esc(item.get("message"))}</li>' for item in validation_report["warnings"])
    violation_items = "".join(f'<li>{_esc(item)}</li>' for item in validation_report["violations"]) or "<li>None</li>"
    limitation_items = "".join(f'<li>{_esc(item)}</li>' for item in report["limitations"])
    html_text = f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Stage4.5 Continuous Surface Path Report</title><style>
*{{box-sizing:border-box}}body{{margin:0;background:#f2f5f4;color:#17221f;font:14px/1.5 Arial,sans-serif}}main{{max-width:1280px;margin:auto;padding:26px}}h1{{margin:0;font-size:28px}}h2{{font-size:18px}}section{{background:#fff;border:1px solid #d8e1de;border-radius:6px;padding:15px;margin:12px 0}}.status{{font-size:17px;font-weight:700;color:#087f5b}}.metrics,.patches{{display:grid;grid-template-columns:repeat(auto-fit,minmax(190px,1fr));gap:8px}}.metric,.patch{{border:1px solid #dce5e2;padding:10px;min-height:82px}}.metric span,.metric em,.patch span,.patch em{{display:block;color:#66736e;font-size:12px}}.metric b{{display:block;font-size:16px;margin:5px 0}}.grid{{display:grid;grid-template-columns:1fr 1fr;gap:12px}}svg{{width:100%;background:#fafcfb}}.bay{{fill:#fff;stroke:#66736e;stroke-width:2}}.safe-envelope{{fill:#f59e0b;opacity:.12;stroke:#d97706}}.obstacle{{fill:#475467;opacity:.72}}.vehicle-side{{fill:#2563eb;opacity:.18;stroke:#1d4ed8}}.baseline-path{{opacity:.55}}.continuous-path{{opacity:.82}}table{{width:100%;border-collapse:collapse;font-size:12px}}th,td{{padding:7px;border-bottom:1px solid #e5e9e7;text-align:left}}.table-wrap{{overflow:auto;max-height:420px}}.target_not_reached{{font-weight:700;color:#b54708}}.target_reached{{font-weight:700;color:#067647}}@media(max-width:900px){{.grid{{grid-template-columns:1fr}}}}
</style></head><body><main><h1>Stage4.5 Continuous Surface Candidate Path</h1><p>Continuous surface reconstruction, scan pass, coverage, transition, motion, collision, interlock, safety, and limitations report.</p>
<section><h2>Result</h2><p class="status">reconstruction_status: {_esc(report["reconstruction_status"])}</p><p>surface: {_esc(report["surface_validation_status"])} | motion: {_esc(report["motion_validation_status"])} | collision: {_esc(report["collision_validation_status"])} | violations: {report["violation_count"]} | warnings: {report["warning_count"]}</p></section>
<section><h2>Baseline versus continuous path</h2><div class="metrics">{_metric_cards(report)}</div></section>
<section><h2>Reference analytic surface patches</h2><div class="patches">{patch_cards}</div><p>Roof uses an arched rectangle, body sides/front/rear use vertical rectangles, and wheels use circular disks. This is not CAD or point cloud geometry.</p></section>
<div class="grid"><section><h2>Wash bay top view</h2>{_top_view(baseline_path, continuous_machine_path, space_model, safety_layout)}<p>Gray: Stage4 frozen baseline. Green: Stage4.5 continuous machine candidate. Safe-stop points remain validated by the existing safety planner.</p></section><section><h2>Side view and standoff</h2>{_side_view(continuous_machine_path)}<p>Reference surface normal and standoff are analytic approximations. No real nozzle pose or angle control is modeled.</p></section></div>
<section><h2>Coverage grid</h2><div class="table-wrap"><table><thead><tr><th>patch</th><th>zone</th><th>coverage</th><th>uncovered cells</th><th>pass spacing</th><th>effective width</th></tr></thead><tbody>{coverage_rows}</tbody></table></div><p>Coverage is a local 2D grid estimate, not water-flow CFD and not actual cleaning effectiveness.</p></section>
<section><h2>Scan pass and connection table</h2><p>scan pass: {surface_plan["summary"]["scan_pass_count"]} | local U-turn: {surface_plan["summary"]["local_connection_count"]} | adaptive safe connection: {surface_plan["summary"]["adaptive_safe_connection_count"]} | required state transition: {surface_plan["summary"]["required_state_transition_count"]}</p><div class="table-wrap"><table><thead><tr><th>connection</th><th>type</th><th>source patch</th><th>target patch</th><th>length mm</th><th>safety</th></tr></thead><tbody>{connection_rows}</tbody></table></div></section>
<section><h2>Motion, collision, interlock, and schedule safety</h2><p>minimum clearance: {summary["minimum_clearance_mm"]} mm | static collision: {summary["static_collision_count"]} | vehicle collision: {summary["vehicle_collision_count"]} | forbidden entry: {summary["forbidden_zone_entry_count"]} | unresolved conflict: {summary["unresolved_conflict_count"]} | deadlock: {summary["deadlock_warning_count"]} | safe stop: {summary["safe_stop_point_count"]}</p></section>
<section><h2>Targets</h2><table><thead><tr><th>metric</th><th>target</th><th>actual</th><th>status</th></tr></thead><tbody>{target_rows}</tbody></table></section>
<section><h2>Warnings</h2><ul>{warning_items}</ul></section><section><h2>Violations</h2><ul>{violation_items}</ul></section><section><h2>Limitations</h2><ul>{limitation_items}</ul><p>No PLC, servo, device SDK, or real hardware is connected. This candidate cannot replace real vehicle or machine validation.</p></section>
</main></body></html>'''
    return report, html_text
