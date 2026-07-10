from __future__ import annotations

import html
import json
from typing import Any


def esc(value: Any) -> str:
    if value is None:
        return "-"
    return html.escape(str(value), quote=True)


def _metric_card(label: str, value: Any) -> str:
    return f'<div class="metric"><small>{esc(label)}</small><strong>{esc(value)}</strong></div>'


def _check_cards(metric_summary: dict[str, Any]) -> str:
    cards = []
    for key in ("workspace", "velocity", "acceleration", "clearance", "continuity", "timestamp", "standoff"):
        item = metric_summary.get(key, {})
        status = "PASS" if item.get("passed") else "FAIL"
        cards.append(f'<article class="check-card {status.lower()}"><h3>{esc(key)}</h3><strong>{status}</strong><pre>{esc(json.dumps(item, ensure_ascii=False, indent=2))}</pre></article>')
    return "".join(cards)


def _polyline(points: list[dict[str, Any]], x_key: str, y_key: str, width: int, height: int, color: str) -> str:
    if not points:
        return ""
    sample_step = max(1, len(points) // 900)
    sampled = points[::sample_step]
    if sampled[-1] is not points[-1]:
        sampled.append(points[-1])
    xs = [float(point.get(x_key, 0)) for point in sampled]
    ys = [float(point.get(y_key, 0)) for point in sampled]
    x_min, x_max = min(xs), max(xs)
    y_min, y_max = min(ys), max(ys)
    x_span = x_max - x_min or 1.0
    y_span = y_max - y_min or 1.0
    coords = " ".join(f"{30 + (x - x_min) / x_span * (width - 60):.1f},{height - 30 - (y - y_min) / y_span * (height - 60):.1f}" for x, y in zip(xs, ys))
    return f'<polyline fill="none" stroke="{color}" stroke-width="2" points="{coords}" />'


def _top_view(
    machine_path_plan: dict[str, Any],
    space_model_report: dict[str, Any],
    validation_report: dict[str, Any],
) -> str:
    width, height = 900, 520
    dimensions = space_model_report["wash_bay"]["bay_dimensions"]
    bay_width = float(dimensions["width_mm"])
    bay_length = float(dimensions["length_mm"])
    margin = 38

    def tx(value: float) -> float:
        return margin + (value + bay_width / 2) / bay_width * (width - margin * 2)

    def ty(value: float) -> float:
        return margin + (bay_length / 2 - value) / bay_length * (height - margin * 2)

    def rect(bounds: dict[str, Any], cls: str) -> str:
        x1, x2 = tx(float(bounds["x_min_mm"])), tx(float(bounds["x_max_mm"]))
        y1, y2 = ty(float(bounds["y_min_mm"])), ty(float(bounds["y_max_mm"]))
        return f'<rect class="{cls}" x="{min(x1,x2):.1f}" y="{min(y1,y2):.1f}" width="{abs(x2-x1):.1f}" height="{abs(y2-y1):.1f}" />'

    trajectory = machine_path_plan.get("trajectory_points", [])
    sample_step = max(1, len(trajectory) // 1200)
    candidate = trajectory[::sample_step]
    candidate_points = " ".join(f"{tx(float(point['x_mm'])):.1f},{ty(float(point['y_mm'])):.1f}" for point in candidate)
    original_lines = []
    for segment in machine_path_plan.get("source_path_segments", []):
        points = segment.get("points", [])
        if len(points) >= 2:
            coords = " ".join(f"{tx(float(point['x_mm'])):.1f},{ty(float(point['y_mm'])):.1f}" for point in points)
            original_lines.append(f'<polyline class="original-path" points="{coords}" />')
    issue_points = []
    for issue in validation_report.get("violations", []) + validation_report.get("warnings", []):
        index = issue.get("point_index")
        if isinstance(index, int) and 0 <= index < len(trajectory):
            point = trajectory[index]
            cls = "violation-point" if issue.get("severity") == "violation" else "warning-point"
            issue_points.append(f'<circle class="{cls}" cx="{tx(float(point["x_mm"])):.1f}" cy="{ty(float(point["y_mm"])):.1f}" r="4" />')
    envelope = space_model_report["vehicle_envelope"]
    return f'''<svg viewBox="0 0 {width} {height}" role="img" aria-label="Stage4 top view candidate path">
      <rect class="bay" x="{margin}" y="{margin}" width="{width-margin*2}" height="{height-margin*2}" />
      {rect(envelope['safe_envelope'], 'safe-envelope')}
      {rect(envelope['bounding_box'], 'vehicle-box')}
      {''.join(original_lines)}
      <polyline class="candidate-path" points="{candidate_points}" />
      {''.join(issue_points)}
    </svg>'''


def _issue_table(items: list[dict[str, Any]], empty_text: str) -> str:
    if not items:
        return f"<p>{esc(empty_text)}</p>"
    rows = []
    for item in items:
        rows.append("<tr>" + "".join(f"<td>{esc(item.get(key))}</td>" for key in ("check_id", "severity", "message", "point_index", "segment_id", "state_id", "zone_id", "measured_value", "limit_value")) + "</tr>")
    return '<table><thead><tr><th>check_id</th><th>severity</th><th>message</th><th>point</th><th>segment</th><th>state</th><th>zone</th><th>measured</th><th>limit</th></tr></thead><tbody>' + "".join(rows) + "</tbody></table>"


def _summary_table(items: list[dict[str, Any]], key: str) -> str:
    rows = "".join(f"<tr><td>{esc(item.get(key))}</td><td>{esc(item.get('trajectory_point_count'))}</td></tr>" for item in items)
    return f"<table><thead><tr><th>{esc(key)}</th><th>trajectory_point_count</th></tr></thead><tbody>{rows}</tbody></table>"


def build_motion_validation_html(
    machine_path_plan: dict[str, Any],
    motion_model: dict[str, Any],
    space_model_report: dict[str, Any],
    validation_report: dict[str, Any],
) -> str:
    summary = validation_report["summary"]
    points = machine_path_plan.get("trajectory_points", [])
    cards = "".join(
        _metric_card(label, value)
        for label, value in (
            ("validation_status", validation_report["validation_status"]),
            ("vehicle_type", validation_report["vehicle_type"]),
            ("motion_model_id", validation_report["motion_model_id"]),
            ("trajectory_point_count", summary["trajectory_point_count"]),
            ("path_length_mm", summary["path_length_mm"]),
            ("estimated_motion_duration_s", summary["estimated_motion_duration_s"]),
            ("violation_count", summary["violation_count"]),
            ("warning_count", summary["warning_count"]),
        )
    )
    limitations = "".join(f"<li>{esc(item)}</li>" for item in validation_report.get("limitations", []))
    return f'''<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Stage4 Motion Validation Report</title><style>
:root{{--ink:#172033;--muted:#64748b;--line:#cbd5e1;--blue:#2563eb;--green:#0f8a72;--red:#be123c;--orange:#d97706;--panel:#f8fafc}}
*{{box-sizing:border-box}}body{{margin:0;font-family:Arial,"Microsoft YaHei",sans-serif;color:var(--ink);background:white;line-height:1.5}}
header{{background:#142d4e;color:white;padding:34px 44px}}header h1{{margin:0 0 8px;font-size:32px}}header p{{margin:0;color:#d9e6f5}}
main{{max-width:1220px;margin:auto;padding:28px 34px 60px}}section{{margin-bottom:34px}}h2{{font-size:24px;margin:0 0 12px}}.metrics,.checks{{display:grid;grid-template-columns:repeat(auto-fit,minmax(190px,1fr));gap:12px}}
.metric,.check-card{{border:1px solid var(--line);border-radius:7px;padding:14px;background:white}}.metric small{{display:block;color:var(--muted)}}.metric strong{{font-size:22px;display:block;margin-top:5px}}
.check-card.pass{{border-top:4px solid var(--green)}}.check-card.fail{{border-top:4px solid var(--red)}}pre{{white-space:pre-wrap;font-size:10px;color:var(--muted)}}
.chart{{border:1px solid var(--line);background:var(--panel);padding:10px;border-radius:7px;overflow:auto}}svg{{width:100%;height:auto}}.bay{{fill:#f8fafc;stroke:#64748b;stroke-width:2}}.safe-envelope{{fill:#dbeafe;fill-opacity:.55;stroke:#2563eb;stroke-dasharray:8 5}}.vehicle-box{{fill:#cbd5e1;stroke:#334155;stroke-width:2}}.original-path{{fill:none;stroke:#94a3b8;stroke-width:1;stroke-dasharray:4 4}}.candidate-path{{fill:none;stroke:#0f8a72;stroke-width:2}}.violation-point{{fill:#be123c}}.warning-point{{fill:#d97706}}
table{{border-collapse:collapse;width:100%;font-size:12px}}th,td{{border:1px solid var(--line);padding:7px;text-align:left;vertical-align:top}}th{{background:#eaf0f8}}.two{{display:grid;grid-template-columns:1fr 1fr;gap:16px}}.boundary{{border-left:5px solid var(--orange);padding:14px;background:#fff8ed}}@media(max-width:800px){{.two{{grid-template-columns:1fr}}}}
</style></head><body><header><h1>Stage4 Motion Validation Report</h1><p>machine-feasible candidate path / 运动约束仿真结果</p></header><main>
<section><div class="metrics">{cards}</div></section>
<section><h2>Constraint Checks</h2><div class="checks">{_check_cards(validation_report['metric_summary'])}</div></section>
<section><h2>2D Top View</h2><div class="chart">{_top_view(machine_path_plan, space_model_report, validation_report)}</div></section>
<section><h2>Height / Side View</h2><div class="chart"><svg viewBox="0 0 900 330">{_polyline(points, 'y_mm', 'z_mm', 900, 330, '#2563eb')}</svg><p>workspace z: {esc(motion_model['workspace']['z_min_mm'])} to {esc(motion_model['workspace']['z_max_mm'])} mm</p></div></section>
<section><h2>Velocity</h2><div class="chart"><svg viewBox="0 0 900 330">{_polyline(points, 'timestamp_s', 'velocity_mm_s', 900, 330, '#0f8a72')}{_polyline(points, 'timestamp_s', 'velocity_x_mm_s', 900, 330, '#2563eb')}{_polyline(points, 'timestamp_s', 'velocity_y_mm_s', 900, 330, '#d97706')}{_polyline(points, 'timestamp_s', 'velocity_z_mm_s', 900, 330, '#be123c')}</svg></div></section>
<section><h2>Acceleration</h2><div class="chart"><svg viewBox="0 0 900 330">{_polyline(points, 'timestamp_s', 'acceleration_mm_s2', 900, 330, '#be123c')}</svg></div></section>
<section><h2>Violations</h2>{_issue_table(validation_report['violations'], 'No violations.')}</section>
<section><h2>Warnings</h2>{_issue_table(validation_report['warnings'], 'No warnings.')}</section>
<section class="two"><div><h2>Zone Summary</h2>{_summary_table(validation_report['zone_summary'], 'zone_id')}</div><div><h2>State Summary</h2>{_summary_table(validation_report['state_summary'], 'state_id')}</div></section>
<section class="boundary"><h2>Limitations</h2><ul>{limitations}</ul><p><strong>当前是候选轨迹；通用三轴参考模型尚未使用真实执行机构参数，也未完成动力学验证，不能直接下发 PLC 或设备。</strong></p></section>
</main></body></html>'''
