from __future__ import annotations

import html
from collections import Counter
from typing import Any


ZONE_CLASSES = {
    "roof": "zone-roof",
    "left_side": "zone-left",
    "right_side": "zone-right",
    "front": "zone-front",
    "rear": "zone-rear",
    "wheels": "zone-wheels",
}


def text(value: Any) -> str:
    if value is None:
        return "-"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, float):
        return f"{value:.2f}".rstrip("0").rstrip(".")
    return str(value)


def esc(value: Any) -> str:
    return html.escape(text(value), quote=True)


def value(data: dict[str, Any] | None, path: list[str], default: Any = "-") -> Any:
    current: Any = data or {}
    for part in path:
        if not isinstance(current, dict) or part not in current:
            return default
        current = current[part]
    return current


def build_summary(
    wash_strategy_plan: dict[str, Any],
    space_model_report: dict[str, Any],
    wash_flow_run: dict[str, Any],
    abstract_nozzle_path_plan: dict[str, Any],
    coverage_report: dict[str, Any],
) -> dict[str, Any]:
    return {
        "report_version": "stage3.1",
        "vehicle_type": value(
            coverage_report,
            ["vehicle", "vehicle_type"],
            value(wash_strategy_plan, ["vehicle", "vehicle_type"]),
        ),
        "wash_profile": value(
            coverage_report,
            ["wash_profile"],
            value(wash_strategy_plan, ["vehicle", "wash_profile"]),
        ),
        "wash_bay_id": value(
            coverage_report,
            ["wash_bay_id"],
            value(space_model_report, ["wash_bay", "wash_bay_id"]),
        ),
        "estimated_total_seconds": value(
            wash_flow_run,
            ["summary", "estimated_total_seconds"],
            value(abstract_nozzle_path_plan, ["summary", "estimated_total_seconds"]),
        ),
        "segment_count": value(abstract_nozzle_path_plan, ["summary", "segment_count"]),
        "point_count": value(abstract_nozzle_path_plan, ["summary", "point_count"]),
        "estimated_actual_coverage_percent": value(
            coverage_report,
            ["coverage_summary", "estimated_actual_coverage_percent"],
        ),
        "coverage_pass": value(coverage_report, ["coverage_summary", "coverage_pass"]),
    }


def metric_card(label: str, item: Any) -> str:
    return (
        '<div class="metric-card">'
        f'<span class="metric-label">{esc(label)}</span>'
        f'<strong>{esc(item)}</strong>'
        "</div>"
    )


def render_summary_cards(summary: dict[str, Any]) -> str:
    keys = [
        "vehicle_type",
        "wash_profile",
        "wash_bay_id",
        "estimated_total_seconds",
        "segment_count",
        "point_count",
        "estimated_actual_coverage_percent",
        "coverage_pass",
    ]
    return "\n".join(metric_card(key, summary.get(key)) for key in keys)


def render_stage_chain() -> str:
    stages = [
        ("Stage2.1", "策略"),
        ("Stage2.2", "空间"),
        ("Stage2.3", "喷嘴"),
        ("Stage2.4", "流程"),
        ("Stage2.5", "路径"),
        ("Stage2.6", "覆盖率"),
        ("Stage3.1", "2D可视化"),
    ]
    return "\n".join(
        (
            '<div class="chain-step">'
            f"<strong>{esc(code)}</strong>"
            f"<span>{esc(name)}</span>"
            "</div>"
        )
        for code, name in stages
    )


def table(headers: list[str], rows: list[list[Any]], empty_text: str = "暂无数据") -> str:
    if not rows:
        return f'<p class="empty">{esc(empty_text)}</p>'
    lines = ["<table>", "<thead><tr>"]
    lines.extend(f"<th>{esc(header)}</th>" for header in headers)
    lines.append("</tr></thead><tbody>")
    for row in rows:
        lines.append("<tr>")
        lines.extend(f"<td>{esc(cell)}</td>" for cell in row)
        lines.append("</tr>")
    lines.append("</tbody></table>")
    return "\n".join(lines)


def rect_from_bounds(
    bounds: dict[str, Any],
    tx,
    ty,
    class_name: str,
    label: str | None = None,
    min_mm: int = 80,
) -> str:
    x1 = float(bounds.get("x_min_mm", 0))
    x2 = float(bounds.get("x_max_mm", 0))
    y1 = float(bounds.get("y_min_mm", 0))
    y2 = float(bounds.get("y_max_mm", 0))
    if abs(x2 - x1) < min_mm:
        center = (x1 + x2) / 2
        x1 = center - min_mm / 2
        x2 = center + min_mm / 2
    if abs(y2 - y1) < min_mm:
        center = (y1 + y2) / 2
        y1 = center - min_mm / 2
        y2 = center + min_mm / 2
    sx1, sx2 = tx(x1), tx(x2)
    sy1, sy2 = ty(y1), ty(y2)
    x = min(sx1, sx2)
    y = min(sy1, sy2)
    width = abs(sx2 - sx1)
    height = abs(sy2 - sy1)
    label_svg = ""
    if label:
        label_svg = (
            f'<text class="zone-label" x="{x + width / 2:.1f}" '
            f'y="{y + height / 2:.1f}">{esc(label)}</text>'
        )
    return (
        f'<rect class="{class_name}" x="{x:.1f}" y="{y:.1f}" '
        f'width="{width:.1f}" height="{height:.1f}" />{label_svg}'
    )


def render_top_view_svg(
    space_model_report: dict[str, Any],
    abstract_nozzle_path_plan: dict[str, Any],
) -> str:
    bay_dimensions = value(space_model_report, ["wash_bay", "bay_dimensions"], {})
    envelope = value(space_model_report, ["vehicle_envelope"], {})
    bounding_box = envelope.get("bounding_box", {}) if isinstance(envelope, dict) else {}
    safe_envelope = envelope.get("safe_envelope", {}) if isinstance(envelope, dict) else {}
    surface_zones = envelope.get("surface_zones", []) if isinstance(envelope, dict) else []
    path_segments = abstract_nozzle_path_plan.get("path_segments", [])

    bay_length = float(bay_dimensions.get("length_mm", 8000))
    bay_width = float(bay_dimensions.get("width_mm", 3600))
    x_min, x_max = -bay_width / 2, bay_width / 2
    y_min, y_max = -bay_length / 2, bay_length / 2
    svg_w, svg_h = 920, 620
    margin = 50
    plot_w, plot_h = svg_w - margin * 2, svg_h - margin * 2

    def tx(x_mm: float) -> float:
        return margin + ((x_mm - x_min) / (x_max - x_min)) * plot_w

    def ty(y_mm: float) -> float:
        return margin + ((y_max - y_mm) / (y_max - y_min)) * plot_h

    lines = [
        f'<svg class="viz-svg" viewBox="0 0 {svg_w} {svg_h}" role="img" '
        'aria-label="Stage3.1 top view SVG">',
        '<text class="svg-title" x="32" y="30">Stage3.1 2D Top View SVG</text>',
        f'<rect class="bay" x="{margin}" y="{margin}" width="{plot_w}" height="{plot_h}" />',
        '<text class="axis-label" x="760" y="600">x: left / right</text>',
        '<text class="axis-label" x="32" y="70">y: front / rear</text>',
    ]
    if isinstance(safe_envelope, dict):
        lines.append(rect_from_bounds(safe_envelope, tx, ty, "safe-envelope", "safe envelope"))
    if isinstance(bounding_box, dict):
        lines.append(rect_from_bounds(bounding_box, tx, ty, "vehicle-box", "vehicle"))

    for zone in surface_zones:
        if not isinstance(zone, dict):
            continue
        bounds = zone.get("bounds", {})
        zone_id = zone.get("zone_id", "zone")
        display_name = zone.get("display_name", zone_id)
        lines.append(
            rect_from_bounds(
                bounds,
                tx,
                ty,
                f"surface-zone {ZONE_CLASSES.get(zone_id, 'zone-default')}",
                display_name,
                min_mm=140,
            )
        )

    for index, segment in enumerate(path_segments, start=1):
        points = segment.get("points", []) if isinstance(segment, dict) else []
        if len(points) < 2:
            continue
        point_text = " ".join(
            f"{tx(float(point.get('x_mm', 0))):.1f},{ty(float(point.get('y_mm', 0))):.1f}"
            for point in points
            if isinstance(point, dict)
        )
        zone_id = segment.get("zone_id", "unknown")
        lines.append(
            f'<polyline class="path-line {ZONE_CLASSES.get(zone_id, "zone-default")}" '
            f'points="{point_text}" />'
        )
        first = points[0]
        if isinstance(first, dict) and index <= 8:
            lines.append(
                f'<text class="path-label" x="{tx(float(first.get("x_mm", 0))) + 5:.1f}" '
                f'y="{ty(float(first.get("y_mm", 0))) - 5:.1f}">{esc(zone_id)}</text>'
            )

    lines.append("</svg>")
    return "\n".join(lines)


def render_side_view_svg(
    space_model_report: dict[str, Any],
    abstract_nozzle_path_plan: dict[str, Any],
) -> str:
    bay_dimensions = value(space_model_report, ["wash_bay", "bay_dimensions"], {})
    envelope = value(space_model_report, ["vehicle_envelope"], {})
    bounding_box = envelope.get("bounding_box", {}) if isinstance(envelope, dict) else {}
    safe_envelope = envelope.get("safe_envelope", {}) if isinstance(envelope, dict) else {}
    path_segments = abstract_nozzle_path_plan.get("path_segments", [])

    bay_length = float(bay_dimensions.get("length_mm", 8000))
    bay_height = float(bay_dimensions.get("height_mm", 3000))
    y_min, y_max = -bay_length / 2, bay_length / 2
    z_min, z_max = 0, bay_height
    svg_w, svg_h = 920, 460
    margin = 50
    plot_w, plot_h = svg_w - margin * 2, svg_h - margin * 2

    def ty(y_mm: float) -> float:
        return margin + ((y_mm - y_min) / (y_max - y_min)) * plot_w

    def tz(z_mm: float) -> float:
        return margin + ((z_max - z_mm) / (z_max - z_min)) * plot_h

    def side_rect(bounds: dict[str, Any], class_name: str, label: str) -> str:
        y1 = float(bounds.get("y_min_mm", 0))
        y2 = float(bounds.get("y_max_mm", 0))
        z1 = float(bounds.get("z_min_mm", 0))
        z2 = float(bounds.get("z_max_mm", 0))
        x = min(ty(y1), ty(y2))
        y = min(tz(z1), tz(z2))
        width = abs(ty(y2) - ty(y1))
        height = abs(tz(z2) - tz(z1))
        return (
            f'<rect class="{class_name}" x="{x:.1f}" y="{y:.1f}" '
            f'width="{width:.1f}" height="{height:.1f}" />'
            f'<text class="zone-label" x="{x + width / 2:.1f}" '
            f'y="{y + height / 2:.1f}">{esc(label)}</text>'
        )

    lines = [
        f'<svg class="viz-svg" viewBox="0 0 {svg_w} {svg_h}" role="img" '
        'aria-label="Stage3.1 side view SVG">',
        '<text class="svg-title" x="32" y="30">Stage3.1 2D Side View SVG</text>',
        f'<rect class="bay" x="{margin}" y="{margin}" width="{plot_w}" height="{plot_h}" />',
        '<text class="axis-label" x="760" y="440">y: front / rear</text>',
        '<text class="axis-label" x="32" y="72">z: height</text>',
    ]
    if isinstance(safe_envelope, dict):
        lines.append(side_rect(safe_envelope, "safe-envelope", "safe envelope height"))
    if isinstance(bounding_box, dict):
        lines.append(side_rect(bounding_box, "vehicle-box", "vehicle height"))

    for segment in path_segments:
        points = segment.get("points", []) if isinstance(segment, dict) else []
        if len(points) < 2:
            continue
        point_text = " ".join(
            f"{ty(float(point.get('y_mm', 0))):.1f},{tz(float(point.get('z_mm', 0))):.1f}"
            for point in points
            if isinstance(point, dict)
        )
        zone_id = segment.get("zone_id", "unknown")
        lines.append(
            f'<polyline class="path-line {ZONE_CLASSES.get(zone_id, "zone-default")}" '
            f'points="{point_text}" />'
        )
    lines.append("</svg>")
    return "\n".join(lines)


def render_coverage_table(coverage_report: dict[str, Any]) -> str:
    rows = [
        [
            report.get("zone_id"),
            report.get("estimated_coverage_percent"),
            report.get("target_coverage_percent"),
            report.get("segment_count"),
            report.get("point_count"),
            report.get("coverage_pass"),
        ]
        for report in coverage_report.get("zone_reports", [])
    ]
    return table(
        [
            "zone_id",
            "estimated_coverage_percent",
            "target_coverage_percent",
            "segment_count",
            "point_count",
            "coverage_pass",
        ],
        rows,
    )


def render_nozzle_table(nozzle_coverage_plan: dict[str, Any]) -> str:
    rows: list[list[Any]] = []
    for zone in nozzle_coverage_plan.get("zone_coverage", []):
        assigned = zone.get("assigned_nozzles", [])
        rows.append(
            [
                zone.get("zone_id"),
                ", ".join(nozzle.get("nozzle_id", "-") for nozzle in assigned),
                ", ".join(sorted({text(nozzle.get("media_type")) for nozzle in assigned})),
                ", ".join(text(nozzle.get("recommended_distance_mm")) for nozzle in assigned),
                ", ".join(text(nozzle.get("effective_width_mm")) for nozzle in assigned),
            ]
        )
    return table(
        [
            "zone_id",
            "assigned_nozzles",
            "media_type",
            "recommended_distance_mm",
            "effective_width_mm",
        ],
        rows,
    )


def render_timeline_table(wash_flow_run: dict[str, Any]) -> str:
    rows = [
        [
            item.get("state_id"),
            item.get("display_name"),
            item.get("duration_seconds"),
            item.get("start_time_s"),
            item.get("end_time_s"),
            ", ".join(item.get("assigned_nozzles", [])),
        ]
        for item in wash_flow_run.get("timeline", [])
    ]
    return table(
        [
            "state_id",
            "display_name",
            "duration_seconds",
            "start_time_s",
            "end_time_s",
            "assigned_nozzles",
        ],
        rows,
    )


def render_path_statistics(abstract_nozzle_path_plan: dict[str, Any]) -> str:
    segments = abstract_nozzle_path_plan.get("path_segments", [])
    state_counter = Counter(segment.get("state_id", "-") for segment in segments)
    zone_counter = Counter(segment.get("zone_id", "-") for segment in segments)
    sample_rows = [
        [
            segment.get("segment_id"),
            segment.get("state_id"),
            segment.get("zone_id"),
            segment.get("nozzle_id"),
            segment.get("media_type"),
            len(segment.get("points", [])),
        ]
        for segment in segments[:5]
    ]
    return "\n".join(
        [
            '<div class="two-col">',
            "<div>",
            "<h3>按 state_id 聚合</h3>",
            table(["state_id", "segment_count"], [[key, count] for key, count in state_counter.items()]),
            "</div>",
            "<div>",
            "<h3>按 zone_id 聚合</h3>",
            table(["zone_id", "segment_count"], [[key, count] for key, count in zone_counter.items()]),
            "</div>",
            "</div>",
            "<h3>示例 path_segment</h3>",
            table(
                ["segment_id", "state_id", "zone_id", "nozzle_id", "media_type", "point_count"],
                sample_rows,
            ),
        ]
    )


def render_limitations() -> str:
    items = [
        "这是 Stage3.1 2D 可视化，只用于展示阶段2仿真链路。",
        "坐标是仿真参考坐标，不是设备标定坐标。",
        "抽象喷嘴路径不是真实机械轨迹。",
        "覆盖率是规则估算，不是真实流体仿真结果。",
        "本报告不是 PLC 指令，也不会控制任何硬件。",
    ]
    return "<ul>" + "".join(f"<li>{esc(item)}</li>" for item in items) + "</ul>"


def build_2d_visualization_report(
    wash_strategy_plan: dict[str, Any],
    space_model_report: dict[str, Any],
    nozzle_coverage_plan: dict[str, Any],
    wash_flow_run: dict[str, Any],
    abstract_nozzle_path_plan: dict[str, Any],
    coverage_report: dict[str, Any],
) -> tuple[str, dict[str, Any]]:
    summary = build_summary(
        wash_strategy_plan,
        space_model_report,
        wash_flow_run,
        abstract_nozzle_path_plan,
        coverage_report,
    )
    top_view_svg = render_top_view_svg(space_model_report, abstract_nozzle_path_plan)
    side_view_svg = render_side_view_svg(space_model_report, abstract_nozzle_path_plan)

    html_text = f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Stage3.1 2D Visualization Report</title>
  <style>
    :root {{
      --ink: #16202a;
      --muted: #647184;
      --line: #d7dee8;
      --panel: #f7f9fc;
      --accent: #127c72;
      --accent-2: #3657d8;
      --warn: #b35a00;
      --ok: #1d7f45;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      color: var(--ink);
      background: #ffffff;
      font-family: Arial, "Microsoft YaHei", sans-serif;
      line-height: 1.55;
    }}
    header {{
      padding: 32px 40px 18px;
      border-bottom: 1px solid var(--line);
      background: #f3f7fb;
    }}
    main {{ padding: 28px 40px 48px; }}
    h1 {{ margin: 0 0 8px; font-size: 30px; }}
    h2 {{ margin: 32px 0 14px; font-size: 21px; }}
    h3 {{ margin: 18px 0 10px; font-size: 16px; }}
    p {{ color: var(--muted); }}
    .metrics {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(190px, 1fr));
      gap: 12px;
      margin-top: 18px;
    }}
    .metric-card {{
      border: 1px solid var(--line);
      border-radius: 8px;
      background: #fff;
      padding: 12px 14px;
    }}
    .metric-label {{
      display: block;
      color: var(--muted);
      font-size: 12px;
      margin-bottom: 6px;
    }}
    .metric-card strong {{ font-size: 20px; }}
    .chain {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
      gap: 10px;
    }}
    .chain-step {{
      border: 1px solid var(--line);
      border-radius: 8px;
      background: var(--panel);
      padding: 12px;
    }}
    .chain-step strong {{ display: block; color: var(--accent-2); }}
    .viz-grid {{
      display: grid;
      grid-template-columns: 1fr;
      gap: 18px;
    }}
    .viz-panel {{
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 14px;
      overflow-x: auto;
      background: #fff;
    }}
    .viz-svg {{
      width: 100%;
      min-width: 720px;
      height: auto;
      background: #fbfcfe;
    }}
    .bay {{ fill: #f6f8fb; stroke: #526071; stroke-width: 2; }}
    .safe-envelope {{ fill: rgba(18, 124, 114, 0.08); stroke: #127c72; stroke-width: 3; stroke-dasharray: 9 7; }}
    .vehicle-box {{ fill: rgba(54, 87, 216, 0.13); stroke: #3657d8; stroke-width: 3; }}
    .surface-zone {{ stroke-width: 1.5; opacity: 0.46; }}
    .zone-roof {{ fill: #a7d8ff; stroke: #2b75b9; }}
    .zone-left {{ fill: #d7c6ff; stroke: #7256c8; }}
    .zone-right {{ fill: #c9efd8; stroke: #36845c; }}
    .zone-front {{ fill: #ffd6a7; stroke: #ba6d1e; }}
    .zone-rear {{ fill: #ffc9d4; stroke: #bd4359; }}
    .zone-wheels {{ fill: #d8dbe3; stroke: #68717f; }}
    .zone-default {{ fill: #e8edf5; stroke: #7a8797; }}
    .path-line {{ fill: none; stroke-width: 3; opacity: 0.75; }}
    .path-label, .zone-label, .axis-label {{
      fill: #243241;
      font-size: 12px;
      text-anchor: middle;
      pointer-events: none;
    }}
    .path-label {{ text-anchor: start; font-size: 11px; }}
    .svg-title {{ fill: var(--ink); font-size: 17px; font-weight: 700; }}
    table {{
      width: 100%;
      border-collapse: collapse;
      margin: 10px 0 20px;
      font-size: 14px;
    }}
    th, td {{
      border: 1px solid var(--line);
      padding: 8px 9px;
      text-align: left;
      vertical-align: top;
    }}
    th {{ background: var(--panel); }}
    .two-col {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
      gap: 16px;
    }}
    .empty {{
      border: 1px dashed var(--line);
      border-radius: 8px;
      padding: 12px;
      color: var(--muted);
    }}
    .limitations {{
      border: 1px solid #e8d3b8;
      background: #fff8ef;
      border-radius: 8px;
      padding: 12px 18px;
    }}
    footer {{
      margin-top: 34px;
      color: var(--muted);
      font-size: 12px;
    }}
  </style>
</head>
<body>
  <header>
    <h1>Stage3.1 2D Visualization Report</h1>
    <p>基于阶段2 JSON 生成的 2D 俯视图、侧视图、覆盖率表、喷嘴分配表和流程时间线。本报告不依赖外网 CDN。</p>
    <section class="metrics">{render_summary_cards(summary)}</section>
  </header>
  <main>
    <section>
      <h2>阶段链路图</h2>
      <div class="chain">{render_stage_chain()}</div>
    </section>

    <section>
      <h2>2D SVG 可视化</h2>
      <div class="viz-grid">
        <div class="viz-panel">{top_view_svg}</div>
        <div class="viz-panel">{side_view_svg}</div>
      </div>
    </section>

    <section>
      <h2>覆盖率区域表</h2>
      {render_coverage_table(coverage_report)}
    </section>

    <section>
      <h2>喷嘴分配表</h2>
      {render_nozzle_table(nozzle_coverage_plan)}
    </section>

    <section>
      <h2>流程时间线</h2>
      {render_timeline_table(wash_flow_run)}
    </section>

    <section>
      <h2>路径统计</h2>
      {render_path_statistics(abstract_nozzle_path_plan)}
    </section>

    <section class="limitations">
      <h2>limitations</h2>
      {render_limitations()}
    </section>

    <footer>
      report_version: stage3.1 | generated from Stage2 simulation JSON
    </footer>
  </main>
</body>
</html>
"""
    return html_text, summary
