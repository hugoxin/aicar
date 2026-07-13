from __future__ import annotations

import html
from collections import Counter
from typing import Any


def _esc(value: Any) -> str:
    return html.escape(str(value))


def _polyline(points: list[dict[str, Any]], color: str, css_class: str) -> str:
    sampled = points[:: max(1, len(points) // 700)]
    coords = " ".join(f"{330 + float(point['x_mm']) * .08:.1f},{340 - float(point['y_mm']) * .08:.1f}" for point in sampled)
    return f'<polyline class="{css_class}" points="{coords}" fill="none" stroke="{color}" stroke-width="1.8" />'


def _rect(bounds: dict[str, Any], css_class: str, label: str) -> str:
    x = 330 + float(bounds["x_min_mm"]) * .08
    y = 340 - float(bounds["y_max_mm"]) * .08
    width = (float(bounds["x_max_mm"]) - float(bounds["x_min_mm"])) * .08
    height = (float(bounds["y_max_mm"]) - float(bounds["y_min_mm"])) * .08
    return f'<rect class="{css_class}" x="{x:.1f}" y="{y:.1f}" width="{width:.1f}" height="{height:.1f}"/><text x="{x+3:.1f}" y="{y+12:.1f}">{_esc(label)}</text>'


def _top_view(baseline: dict[str, Any], optimized: dict[str, Any], safety_layout: dict[str, Any], space_model: dict[str, Any]) -> str:
    layers = ['<rect class="wash-bay" x="42" y="20" width="576" height="640"/>']
    safe = space_model["vehicle_envelope"]["safe_envelope"]
    policy = safety_layout["vehicle_clearance_policy"]
    for css, label, margin in (
        ("recommended", "recommended envelope", policy["recommended_mm"]),
        ("warning", "warning envelope", policy["warning_threshold_mm"]),
        ("hard", "hard envelope", policy["hard_minimum_mm"]),
    ):
        bounds = {**{f"{axis}_min_mm": float(safe[f"{axis}_min_mm"]) - float(margin) for axis in ("x", "y", "z")}, **{f"{axis}_max_mm": float(safe[f"{axis}_max_mm"]) + float(margin) for axis in ("x", "y", "z")}}
        layers.append(_rect(bounds, css, label))
    layers.append(_rect(space_model["vehicle_envelope"]["bounding_box"], "vehicle", "vehicle"))
    for obstacle in safety_layout["static_obstacles"]:
        layers.append(_rect(obstacle["bounds"], "obstacle", obstacle["obstacle_id"]))
    layers.append(_polyline(baseline["trajectory_points"], "#98a2b3", "baseline-path"))
    layers.append(_polyline(optimized["trajectory_points"], "#1677ff", "optimized-path"))
    return '<svg viewBox="0 0 660 680" aria-label="Stage4.4 baseline and optimized path comparison">' + "".join(layers) + "</svg>"


def _metric_cards(plan: dict[str, Any]) -> str:
    labels = (
        "trajectory_point_count", "transition_segment_count", "path_length_mm",
        "estimated_motion_duration_s", "total_schedule_duration_s", "total_delay_s",
        "clearance_warning_count", "synchronized_group_count",
    )
    cards = []
    for metric in labels:
        item = plan["improvement_summary"][metric]
        improvement = item["improvement_percent"]
        display = "NO_IMPROVEMENT" if improvement is None or improvement <= 0 else f"{improvement}%"
        cards.append(f'<div class="metric"><span>{_esc(metric)}</span><b>{_esc(item["baseline"])} → {_esc(item["optimized"])}</b><em>{_esc(display)}</em></div>')
    return "".join(cards)


def _transition_table(plan: dict[str, Any]) -> str:
    rows = []
    for item in plan["transition_results"]:
        rows.append("<tr>" + "".join(f"<td>{_esc(item.get(key))}</td>" for key in ("segment_id", "transition_classification", "original_length_mm", "optimized_length_mm", "reduction_percent", "optimization_status", "rejection_reason")) + "</tr>")
    return "".join(rows)


def _timeline(schedule: dict[str, Any], css_class: str) -> str:
    total = max(float(schedule["summary"]["total_schedule_duration_s"]), 1.0)
    rows = []
    for actuator_id, items in schedule["actuator_timelines"].items():
        bars = "".join(f'<span class="bar {css_class}" style="left:{float(item["adjusted_start_s"])/total*100:.3f}%;width:{max(float(item["duration_s"])/total*100,.25):.3f}%" title="{_esc(item["state_id"])} / {_esc(item["zone_id"])}"></span>' for item in items)
        rows.append(f'<div class="lane"><strong>{_esc(actuator_id)}</strong><div class="track">{bars}</div></div>')
    return "".join(rows)


def build_path_optimization_report(
    baseline_path: dict[str, Any],
    optimized_plan: dict[str, Any],
    baseline_schedule: dict[str, Any],
    safety_layout: dict[str, Any],
    space_model: dict[str, Any],
) -> tuple[dict[str, Any], str]:
    transition_counts = dict(Counter(item["optimization_status"] for item in optimized_plan["transition_results"]))
    report = {
        "report_version": "stage4.4",
        "optimization_profile_id": optimized_plan["optimization_profile_id"],
        "optimization_status": optimized_plan["optimization_status"],
        "safety_validation_status": optimized_plan["safety_validation_status"],
        "baseline_validation_status": optimized_plan["baseline_validation_status"],
        "optimized_validation_status": optimized_plan["optimized_validation_status"],
        "accepted_optimization": optimized_plan["accepted_optimization"],
        "baseline_metrics": optimized_plan["baseline_summary"],
        "optimized_metrics": optimized_plan["optimized_summary"],
        "improvement_summary": optimized_plan["improvement_summary"],
        "transition_status_counts": transition_counts,
        "target_results": optimized_plan["target_results"],
        "safety_validation": optimized_plan["safety_validation"],
        "violation_count": len(optimized_plan["violations"]),
        "warning_count": len(optimized_plan["warnings"]),
        "warnings": optimized_plan["warnings"],
        "violations": optimized_plan["violations"],
        "limitations": optimized_plan["limitations"],
    }
    target_rows = "".join(f'<tr><td>{_esc(metric)}</td><td>{item["target_percent"]}%</td><td>{_esc(item["actual_percent"])}</td><td class="{item["status"].lower()}">{item["status"]}</td></tr>' for metric, item in optimized_plan["target_results"].items())
    safety = optimized_plan["safety_validation"]["collision_validation"]
    transition_counts_text = ", ".join(f"{key}: {value}" for key, value in sorted(transition_counts.items()))
    limitations = "".join(f"<li>{_esc(item)}</li>" for item in optimized_plan["limitations"])
    html_text = f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Stage4.4 path optimization report</title><style>
*{{box-sizing:border-box}}body{{margin:0;background:#f3f6f8;color:#17202a;font:14px/1.5 Arial,sans-serif}}main{{max-width:1240px;margin:auto;padding:28px}}h1{{margin:0 0 6px;font-size:28px}}h2{{font-size:18px}}section{{background:#fff;border:1px solid #d9e0e7;border-radius:6px;padding:15px;margin:12px 0}}.status{{font-weight:700;color:#096}}.metrics{{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:8px}}.metric{{border:1px solid #e3e8ee;padding:10px;min-height:92px}}.metric span,.metric em{{display:block;color:#667085;font-size:12px}}.metric b{{display:block;font-size:16px;margin:5px 0}}.grid{{display:grid;grid-template-columns:1fr 1fr;gap:12px}}svg{{width:100%;background:#fafbfc}}svg text{{font-size:8px}}.wash-bay{{fill:#fff;stroke:#667085;stroke-width:2}}.obstacle{{fill:#475467;opacity:.7}}.vehicle{{fill:#2563eb;opacity:.2;stroke:#1d4ed8}}.hard{{fill:#ef4444;opacity:.03;stroke:#dc2626}}.warning{{fill:#f59e0b;opacity:.03;stroke:#d97706;stroke-dasharray:5 4}}.recommended{{fill:#22c55e;opacity:.03;stroke:#16a34a;stroke-dasharray:2 5}}.baseline-path{{opacity:.65}}.optimized-path{{opacity:.78}}table{{width:100%;border-collapse:collapse;font-size:12px}}th,td{{padding:7px;border-bottom:1px solid #e5e7eb;text-align:left}}.table-wrap{{overflow:auto}}.lane{{display:grid;grid-template-columns:155px 1fr;gap:8px;align-items:center;margin:8px 0}}.track{{height:25px;background:#eef2f5;position:relative}}.bar{{position:absolute;top:3px;height:19px}}.baseline{{background:#98a2b3}}.optimized{{background:#1677ff}}.target_not_reached{{color:#b54708;font-weight:700}}.target_reached{{color:#067647;font-weight:700}}@media(max-width:900px){{.grid{{grid-template-columns:1fr}}}}
</style></head><body><main><h1>Stage4.4 Path Optimization and Cycle Time Report</h1><p>Safety-first heuristic path optimization, transition analysis, schedule optimization, clearance, collision, shared interlock, and safety validation.</p>
<section><h2>Result</h2><p class="status">optimization_status: {_esc(optimized_plan["optimization_status"])} | safety_validation_status: {_esc(optimized_plan["safety_validation_status"])}</p><p>baseline: {_esc(optimized_plan["baseline_validation_status"])} | optimized: {_esc(optimized_plan["optimized_validation_status"])} | violations: {len(optimized_plan["violations"])} | warnings: {len(optimized_plan["warnings"])}</p></section>
<section><h2>Core comparison</h2><div class="metrics">{_metric_cards(optimized_plan)}</div></section>
<div class="grid"><section><h2>Path comparison</h2>{_top_view(baseline_path, optimized_plan, safety_layout, space_model)}<p>Gray: baseline. Blue: accepted optimized candidate. Rejected direct transition candidates remain documented and are not drawn as accepted paths.</p></section><section><h2>Schedule comparison</h2><h3>Baseline timeline</h3>{_timeline(baseline_schedule,"baseline")}<h3>Optimized timeline</h3>{_timeline(optimized_plan["optimized_schedule"],"optimized")}</section></div>
<section><h2>Transition results</h2><p>{_esc(transition_counts_text)}</p><div class="table-wrap"><table><thead><tr><th>transition</th><th>type</th><th>original mm</th><th>optimized mm</th><th>reduction</th><th>status</th><th>rejection reason</th></tr></thead><tbody>{_transition_table(optimized_plan)}</tbody></table></div></section>
<section><h2>Task order and schedule adjustments</h2><p>Task IDs and wash-state order are preserved. Local forced-sync candidate was accepted only when its weighted objective was better; otherwise its adjustment is recorded as rejected.</p></section>
<section><h2>Safety comparison</h2><p>minimum clearance: {_esc(optimized_plan["optimized_summary"]["minimum_vehicle_clearance_mm"])} mm | static collision: {safety["static_collision_count"]} | vehicle collision: {safety["vehicle_collision_count"]} | forbidden entry: {safety["forbidden_zone_entry_count"]} | unresolved interlock: {optimized_plan["optimized_schedule"]["summary"]["unresolved_conflict_count"]} | safe stop: {safety["safe_stop_point_count"]}</p></section>
<section><h2>Optimization targets</h2><table><thead><tr><th>metric</th><th>target</th><th>actual</th><th>status</th></tr></thead><tbody>{target_rows}</tbody></table></section>
<section><h2>Limitations</h2><ul>{limitations}</ul><p>Current geometry remains an AABB and vehicle-envelope approximation using generic actuators. No global optimum is guaranteed. No real wash-machine calibration is loaded. This output cannot be issued to a PLC, servo, SDK, or real hardware.</p></section>
</main></body></html>'''
    return report, html_text
