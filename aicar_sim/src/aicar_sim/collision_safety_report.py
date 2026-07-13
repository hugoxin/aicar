from __future__ import annotations

import html
from typing import Any


COLORS = {
    "top_actuator": "#1677ff",
    "left_side_actuator": "#00a870",
    "right_side_actuator": "#e8590c",
}


def _esc(value: Any) -> str:
    return html.escape(str(value))


def _rect(bounds: dict[str, Any], css_class: str, label: str = "") -> str:
    scale = 0.08
    x = 330 + float(bounds["x_min_mm"]) * scale
    y = 340 - float(bounds["y_max_mm"]) * scale
    width = (float(bounds["x_max_mm"]) - float(bounds["x_min_mm"])) * scale
    height = (float(bounds["y_max_mm"]) - float(bounds["y_min_mm"])) * scale
    return (
        f'<rect class="{css_class}" x="{x:.1f}" y="{y:.1f}" width="{width:.1f}" height="{height:.1f}" />'
        f'<text x="{x + 4:.1f}" y="{y + 14:.1f}">{_esc(label)}</text>'
    )


def _top_view(plan: dict[str, Any]) -> str:
    layout = plan["resolved_safety_layout"]
    vehicle = next(zone for zone in layout["safety_zones"] if zone["zone_id"] == "vehicle_forbidden_zone")
    warning = next(zone for zone in layout["safety_zones"] if zone["zone_id"] == "vehicle_warning_band")
    layers = ['<rect class="wash-bay" x="42" y="20" width="576" height="640" />']
    safe = plan["vehicle_envelope"]["safe_envelope"]
    policy = plan["clearance_policy"]

    def expanded(margin: float) -> dict[str, float]:
        return {
            **{f"{axis}_min_mm": float(safe[f"{axis}_min_mm"]) - margin for axis in ("x", "y", "z")},
            **{f"{axis}_max_mm": float(safe[f"{axis}_max_mm"]) + margin for axis in ("x", "y", "z")},
        }

    layers.append(_rect(expanded(float(policy["recommended_mm"])), "recommended-clearance", "recommended envelope"))
    layers.append(_rect(expanded(float(policy["warning_threshold_mm"])), "warning-clearance", "warning envelope"))
    layers.append(_rect(expanded(float(policy["hard_minimum_mm"])), "hard-clearance", "hard clearance envelope"))
    layers.append(_rect(warning["bounds"], "warning-zone", "slow zone"))
    layers.append(_rect(vehicle["bounds"], "forbidden-zone", "forbidden zone"))
    layers.append(_rect(plan["vehicle_envelope"]["bounding_box"], "vehicle-box", "vehicle bounding box"))
    for zone in layout["safety_zones"]:
        if zone.get("zone_type") in {"shared_interlock", "safe_stop"}:
            layers.append(_rect(zone["bounds"], zone["zone_type"].replace("_", "-"), zone["zone_id"]))
    for obstacle in layout["static_obstacles"]:
        layers.append(_rect(obstacle["bounds"], "obstacle", obstacle["obstacle_id"]))
    points_by_actuator: dict[str, list[str]] = {}
    point_map = {int(point["sequence_index"]): point for point in plan["annotated_trajectory_points"]}
    for task in plan["actuator_tasks"]:
        actuator_id = task["assigned_actuator_id"]
        path = points_by_actuator.setdefault(actuator_id, [])
        for index in task["path_point_indices"]:
            point = point_map.get(int(index))
            if point:
                path.append(f"{330 + float(point['x_mm']) * .08:.1f},{340 - float(point['y_mm']) * .08:.1f}")
    for actuator_id, points in points_by_actuator.items():
        color = COLORS.get(actuator_id, "#555")
        layers.append(f'<polyline points="{" ".join(points)}" fill="none" stroke="{color}" stroke-width="1.5" opacity=".7" />')
    for item in plan["safe_stop_points"]:
        point = item["point"]
        layers.append(f'<circle class="safe-stop-point" cx="{330 + float(point["x_mm"]) * .08:.1f}" cy="{340 - float(point["y_mm"]) * .08:.1f}" r="6"><title>{_esc(item["actuator_id"])}</title></circle>')
    return '<svg viewBox="0 0 660 680" role="img" aria-label="Wash bay collision safety top view">' + "".join(layers) + "</svg>"


def _timeline(schedule: dict[str, Any]) -> str:
    total = max(float(schedule["summary"]["total_schedule_duration_s"]), 1.0)
    lanes = []
    for actuator_id, items in schedule["actuator_timelines"].items():
        bars = []
        for item in items:
            left = float(item["adjusted_start_s"]) / total * 100
            width = max(float(item["duration_s"]) / total * 100, 0.35)
            bars.append(
                f'<span class="task" style="left:{left:.3f}%;width:{width:.3f}%;background:{COLORS.get(actuator_id, "#555")}" '
                f'title="{_esc(item["state_id"])} / {_esc(item["zone_id"])} / {_esc(item.get("delay_reason") or "no delay")}"></span>'
            )
        lanes.append(f'<div class="lane"><strong>{_esc(actuator_id)}</strong><div class="track">{"".join(bars)}</div></div>')
    return "".join(lanes)


def _rows(items: list[dict[str, Any]], columns: list[str]) -> str:
    if not items:
        return f'<tr><td colspan="{len(columns)}">None</td></tr>'
    return "".join("<tr>" + "".join(f"<td>{_esc(item.get(column, ''))}</td>" for column in columns) + "</tr>" for item in items)


def _table(title: str, items: list[dict[str, Any]], columns: list[str]) -> str:
    heads = "".join(f"<th>{_esc(column)}</th>" for column in columns)
    return f'<section><h2>{_esc(title)}</h2><div class="table-wrap"><table><thead><tr>{heads}</tr></thead><tbody>{_rows(items, columns)}</tbody></table></div></section>'


def build_collision_safety_html(plan: dict[str, Any]) -> str:
    summary = plan["summary"]
    schedule = plan["multi_actuator_schedule"]
    status = plan["validation_status"]
    cards = {
        "validation_status": status,
        "vehicle_type": plan["vehicle_type"],
        "wash_profile": plan["wash_profile"],
        "actuator_count": summary["actuator_count"],
        "task_count": summary["task_count"],
        "conflict_count": schedule["summary"]["conflict_count_after_resolution"],
        "violation_count": summary["violation_count"],
        "warning_count": summary["warning_count"],
        "safe_stop_point_count": summary["safe_stop_point_count"],
    }
    card_html = "".join(f'<div class="metric"><span>{_esc(key)}</span><b>{_esc(value)}</b></div>' for key, value in cards.items())
    sync = _table("Left/right synchronization", schedule["sync_groups"], ["sync_group_id", "left_task_id", "right_task_id", "start_offset_s", "sync_status", "sync_warning"])
    locks = _table("Shared interlock resource locks", schedule["resource_locks"], ["resource_id", "actuator_id", "task_id", "start_s", "end_s"])
    conflicts = _table("Time interval conflicts after resolution", schedule["conflicts_after_resolution"], ["conflict_id", "resource_id", "task_a_id", "task_b_id", "severity"])
    collisions = _table("Static obstacle and vehicle collision checks", plan["collisions"], ["check_id", "actuator_id", "segment_id", "obstacle_id", "message"])
    clearances = _table("Vehicle safety clearance", [item for item in plan["warnings"] if item.get("check_id") == "vehicle_clearance"], ["severity", "actuator_id", "point_index", "measured_value", "limit_value", "message"])
    stops = _table("Safe stop points", plan["safe_stop_points"], ["safe_stop_id", "actuator_id", "source_type", "inside_workspace", "outside_static_obstacles", "outside_vehicle_forbidden_zone", "validation_status"])
    warnings = _table("Warnings", plan["warnings"], ["check_id", "severity", "actuator_id", "point_index", "message"])
    violations = _table("Violations", plan["violations"], ["check_id", "severity", "actuator_id", "point_index", "message"])
    limitations = "".join(f"<li>{_esc(item)}</li>" for item in plan["limitations"])
    return f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Stage4 collision safety report</title><style>
:root{{--ink:#17202a;--muted:#667085;--line:#d9e0e7;--panel:#fff;--bg:#f3f6f8}}*{{box-sizing:border-box}}body{{margin:0;background:var(--bg);color:var(--ink);font:14px/1.5 Arial,sans-serif}}main{{max-width:1240px;margin:auto;padding:28px}}h1{{font-size:28px;margin:0 0 8px}}h2{{font-size:18px;margin:0 0 14px}}.subtitle{{color:var(--muted);margin-bottom:22px}}.metrics{{display:grid;grid-template-columns:repeat(auto-fit,minmax(145px,1fr));gap:8px;margin-bottom:18px}}.metric,section{{background:var(--panel);border:1px solid var(--line);border-radius:6px;padding:14px}}.metric span{{display:block;color:var(--muted);font-size:12px}}.metric b{{font-size:19px}}.grid{{display:grid;grid-template-columns:minmax(420px,1fr) minmax(420px,1fr);gap:14px;margin-bottom:14px}}section{{margin-bottom:14px}}svg{{width:100%;height:auto;background:#fafbfc}}svg text{{font-size:9px;fill:#344054}}.wash-bay{{fill:#fff;stroke:#667085;stroke-width:2}}.obstacle{{fill:#475467;opacity:.75}}.forbidden-zone{{fill:#ef4444;opacity:.16;stroke:#dc2626}}.warning-zone{{fill:#f59e0b;opacity:.12;stroke:#d97706;stroke-dasharray:5 4}}.shared-interlock{{fill:#8b5cf6;opacity:.12;stroke:#7c3aed}}.safe-stop{{fill:#10b981;opacity:.11;stroke:#059669}}.safe-stop-point{{fill:#fff;stroke:#059669;stroke-width:3}}.lane{{display:grid;grid-template-columns:155px 1fr;gap:10px;align-items:center;margin:10px 0}}.track{{height:28px;background:#eef2f5;position:relative;overflow:hidden}}.task{{position:absolute;top:3px;height:22px;min-width:2px}}.table-wrap{{overflow:auto}}table{{border-collapse:collapse;width:100%;font-size:12px}}th,td{{padding:7px;border-bottom:1px solid #e5e7eb;text-align:left;white-space:nowrap}}th{{background:#f8fafc}}ul{{margin-bottom:0}}@media(max-width:900px){{.grid{{grid-template-columns:1fr}}}}
</style><style>.recommended-clearance{{fill:#22c55e;opacity:.04;stroke:#16a34a;stroke-dasharray:2 5}}.warning-clearance{{fill:#f59e0b;opacity:.04;stroke:#d97706;stroke-dasharray:5 4}}.hard-clearance{{fill:#ef4444;opacity:.04;stroke:#dc2626;stroke-dasharray:8 4}}.vehicle-box{{fill:#2563eb;opacity:.22;stroke:#1d4ed8;stroke-width:2}}</style></head><body><main>
<h1>Stage4 Collision and Safety-Constrained Simulation</h1>
<p class="subtitle">collision-safe candidate plan using static obstacle AABB, forbidden zone, slow zone, shared interlock, safe stop, and multi actuator scheduling.</p>
<div class="metrics">{card_html}</div>
<div class="grid"><section><h2>Wash bay 2D top view</h2>{_top_view(plan)}</section><section><h2>Multi actuator timeline</h2>{_timeline(schedule)}<p>Tasks may be delayed by shared resource lock resolution; no task is deleted to obtain a passing status.</p></section></div>
{sync}{locks}{conflicts}{collisions}{clearances}{stops}{warnings}{violations}
<section><h2>Limitations</h2><ul>{limitations}</ul><p>Generic three-axis and multi-actuator reference models are used. Static obstacle and swept volume geometry use conservative AABB approximation. No real wash-machine geometry or hardware collision validation is included. This report cannot be issued directly to a PLC.</p></section>
</main></body></html>'''
