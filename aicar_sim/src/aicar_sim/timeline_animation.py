from __future__ import annotations

import html
import json
from collections import Counter
from typing import Any

from aicar_sim.visualization_2d import ZONE_CLASSES, esc, table, text, value


def json_script(data: Any) -> str:
    return json.dumps(data, ensure_ascii=False).replace("</", "<\\/")


def build_summary(
    wash_strategy_plan: dict[str, Any],
    space_model_report: dict[str, Any],
    wash_flow_run: dict[str, Any],
    abstract_nozzle_path_plan: dict[str, Any],
    coverage_report: dict[str, Any],
) -> dict[str, Any]:
    timeline = wash_flow_run.get("timeline", [])
    return {
        "report_version": "stage3.2",
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
        "state_count": len(timeline),
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
        "state_count",
        "segment_count",
        "point_count",
        "estimated_actual_coverage_percent",
        "coverage_pass",
    ]
    return "\n".join(metric_card(key, summary.get(key)) for key in keys)


def svg_rect_from_bounds(
    bounds: dict[str, Any],
    tx,
    ty,
    class_name: str,
    label: str | None = None,
    data_attrs: dict[str, str] | None = None,
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
    attrs = ""
    if data_attrs:
        attrs = " " + " ".join(f'{key}="{html.escape(val, quote=True)}"' for key, val in data_attrs.items())
    label_svg = ""
    if label:
        label_svg = (
            f'<text class="zone-label" x="{x + width / 2:.1f}" '
            f'y="{y + height / 2:.1f}">{esc(label)}</text>'
        )
    return (
        f'<rect class="{class_name}"{attrs} x="{x:.1f}" y="{y:.1f}" '
        f'width="{width:.1f}" height="{height:.1f}" />{label_svg}'
    )


def render_interactive_top_view_svg(
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
    svg_w, svg_h = 940, 640
    margin = 55
    plot_w, plot_h = svg_w - margin * 2, svg_h - margin * 2

    def tx(x_mm: float) -> float:
        return margin + ((x_mm - x_min) / (x_max - x_min)) * plot_w

    def ty(y_mm: float) -> float:
        return margin + ((y_max - y_mm) / (y_max - y_min)) * plot_h

    lines = [
        f'<svg class="timeline-svg" viewBox="0 0 {svg_w} {svg_h}" role="img" '
        'aria-label="Stage3.2 timeline animation SVG">',
        '<text class="svg-title" x="34" y="32">Stage3.2 Timeline Animation SVG</text>',
        f'<rect class="bay" x="{margin}" y="{margin}" width="{plot_w}" height="{plot_h}" />',
        '<text class="axis-label" x="790" y="616">x: left / right</text>',
        '<text class="axis-label" x="34" y="78">y: front / rear</text>',
    ]
    if isinstance(safe_envelope, dict):
        lines.append(svg_rect_from_bounds(safe_envelope, tx, ty, "safe-envelope", "safe envelope"))
    if isinstance(bounding_box, dict):
        lines.append(svg_rect_from_bounds(bounding_box, tx, ty, "vehicle-box", "vehicle"))

    for zone in surface_zones:
        if not isinstance(zone, dict):
            continue
        zone_id = text(zone.get("zone_id", "zone"))
        display_name = text(zone.get("display_name", zone_id))
        lines.append(
            svg_rect_from_bounds(
                zone.get("bounds", {}),
                tx,
                ty,
                f"surface-zone {ZONE_CLASSES.get(zone_id, 'zone-default')}",
                display_name,
                data_attrs={"data-zone-id": zone_id},
                min_mm=140,
            )
        )

    for index, segment in enumerate(path_segments, start=1):
        if not isinstance(segment, dict):
            continue
        points = segment.get("points", [])
        if len(points) < 2:
            continue
        point_text = " ".join(
            f"{tx(float(point.get('x_mm', 0))):.1f},{ty(float(point.get('y_mm', 0))):.1f}"
            for point in points
            if isinstance(point, dict)
        )
        zone_id = text(segment.get("zone_id", "unknown"))
        state_id = text(segment.get("state_id", "unknown"))
        nozzle_id = text(segment.get("nozzle_id", "unknown"))
        segment_id = text(segment.get("segment_id", f"segment_{index}"))
        lines.append(
            f'<polyline class="path-line {ZONE_CLASSES.get(zone_id, "zone-default")}" '
            f'data-segment-id="{esc(segment_id)}" data-state-id="{esc(state_id)}" '
            f'data-zone-id="{esc(zone_id)}" data-nozzle-id="{esc(nozzle_id)}" '
            f'points="{point_text}" />'
        )

    lines.append("</svg>")
    return "\n".join(lines)


def collect_nozzle_ids(nozzle_coverage_plan: dict[str, Any]) -> list[str]:
    ids: list[str] = []
    for zone in nozzle_coverage_plan.get("zone_coverage", []):
        for nozzle in zone.get("assigned_nozzles", []):
            nozzle_id = text(nozzle.get("nozzle_id"))
            if nozzle_id != "-" and nozzle_id not in ids:
                ids.append(nozzle_id)
    return ids


def render_nozzle_panel(nozzle_coverage_plan: dict[str, Any]) -> str:
    items = [
        f'<li class="nozzle-item" data-nozzle-id="{esc(nozzle_id)}">{esc(nozzle_id)}</li>'
        for nozzle_id in collect_nozzle_ids(nozzle_coverage_plan)
    ]
    return "<ul class=\"nozzle-list\">" + "\n".join(items) + "</ul>"


def render_state_list(wash_flow_run: dict[str, Any]) -> str:
    items = []
    for state in wash_flow_run.get("timeline", []):
        state_id = text(state.get("state_id"))
        items.append(
            '<li class="state-item" '
            f'data-state-id="{esc(state_id)}">'
            f'<strong>{esc(state_id)}</strong>'
            f'<span>{esc(state.get("display_name"))}</span>'
            f'<em>{esc(state.get("start_time_s"))}s - {esc(state.get("end_time_s"))}s</em>'
            "</li>"
        )
    return "<ol class=\"state-list\">" + "\n".join(items) + "</ol>"


def render_coverage_panel(coverage_report: dict[str, Any]) -> str:
    rows = [
        [
            report.get("zone_id"),
            report.get("estimated_coverage_percent"),
            report.get("coverage_pass"),
            ", ".join(report.get("warnings", [])),
        ]
        for report in coverage_report.get("zone_reports", [])
    ]
    suggestions = coverage_report.get("improvement_suggestions", [])
    warning_items = "".join(f"<li>{esc(item)}</li>" for item in suggestions)
    return (
        table(["zone", "estimated_coverage_percent", "coverage_pass", "warnings"], rows)
        + f'<ul class="suggestions">{warning_items}</ul>'
    )


def render_path_statistics(abstract_nozzle_path_plan: dict[str, Any]) -> str:
    segments = abstract_nozzle_path_plan.get("path_segments", [])
    state_counter = Counter(text(segment.get("state_id")) for segment in segments)
    zone_counter = Counter(text(segment.get("zone_id")) for segment in segments)
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
        ]
    )


def timeline_data(wash_flow_run: dict[str, Any]) -> list[dict[str, Any]]:
    data = []
    for state in wash_flow_run.get("timeline", []):
        data.append(
            {
                "state_id": state.get("state_id"),
                "display_name": state.get("display_name"),
                "state_type": state.get("state_type"),
                "start_time_s": state.get("start_time_s", 0),
                "end_time_s": state.get("end_time_s", 0),
                "duration_seconds": state.get("duration_seconds", 0),
                "target_zone_ids": state.get("target_zone_ids", []),
                "assigned_nozzles": state.get("assigned_nozzles", []),
            }
        )
    return data


def path_segment_data(abstract_nozzle_path_plan: dict[str, Any]) -> list[dict[str, Any]]:
    data = []
    for segment in abstract_nozzle_path_plan.get("path_segments", []):
        data.append(
            {
                "segment_id": segment.get("segment_id"),
                "state_id": segment.get("state_id"),
                "zone_id": segment.get("zone_id"),
                "nozzle_id": segment.get("nozzle_id"),
                "media_type": segment.get("media_type"),
                "point_count": len(segment.get("points", [])),
            }
        )
    return data


def render_limitations() -> str:
    items = [
        "Stage3.2 是简单时间轴动画 Demo。",
        "当前不是 3D。",
        "当前不是真实运动控制。",
        "当前不是真实流体仿真。",
        "当前不是 PLC。",
        "当前不会控制任何硬件。",
    ]
    return "<ul>" + "".join(f"<li>{esc(item)}</li>" for item in items) + "</ul>"


def build_timeline_animation_report(
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
    total_seconds = int(float(summary["estimated_total_seconds"]))
    timeline = timeline_data(wash_flow_run)
    path_segments = path_segment_data(abstract_nozzle_path_plan)
    top_view_svg = render_interactive_top_view_svg(
        space_model_report,
        abstract_nozzle_path_plan,
    )

    html_text = f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Stage3.2 Timeline Animation Report</title>
  <style>
    :root {{
      --ink: #17202a;
      --muted: #637184;
      --line: #d5dde8;
      --panel: #f7f9fc;
      --active: #d04224;
      --active-soft: #fff1ec;
      --accent: #127c72;
      --blue: #3657d8;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      color: var(--ink);
      background: #fff;
      font-family: Arial, "Microsoft YaHei", sans-serif;
      line-height: 1.55;
    }}
    header {{
      padding: 32px 40px 18px;
      border-bottom: 1px solid var(--line);
      background: #f3f7fb;
    }}
    main {{ padding: 26px 40px 48px; }}
    h1 {{ margin: 0 0 8px; font-size: 30px; }}
    h2 {{ margin: 30px 0 14px; font-size: 21px; }}
    h3 {{ margin: 14px 0 9px; font-size: 16px; }}
    p {{ color: var(--muted); }}
    .metrics {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
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
    .layout {{
      display: grid;
      grid-template-columns: minmax(620px, 1.4fr) minmax(300px, 0.6fr);
      gap: 18px;
      align-items: start;
    }}
    .panel {{
      border: 1px solid var(--line);
      border-radius: 8px;
      background: #fff;
      padding: 14px;
      overflow-x: auto;
    }}
    .current-panel {{
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 14px;
      margin-bottom: 14px;
    }}
    .current-grid {{
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 8px 12px;
      font-size: 14px;
    }}
    .current-grid strong {{ display: block; color: var(--muted); font-size: 12px; }}
    .timeline-svg {{
      width: 100%;
      min-width: 720px;
      height: auto;
      background: #fbfcfe;
    }}
    .bay {{ fill: #f6f8fb; stroke: #526071; stroke-width: 2; }}
    .safe-envelope {{ fill: rgba(18, 124, 114, 0.08); stroke: #127c72; stroke-width: 3; stroke-dasharray: 9 7; }}
    .vehicle-box {{ fill: rgba(54, 87, 216, 0.13); stroke: #3657d8; stroke-width: 3; }}
    .surface-zone {{ stroke-width: 1.5; opacity: 0.28; transition: opacity 160ms, stroke-width 160ms; }}
    .surface-zone.active-zone {{ opacity: 0.78; stroke-width: 4; }}
    .zone-roof {{ fill: #a7d8ff; stroke: #2b75b9; }}
    .zone-left {{ fill: #d7c6ff; stroke: #7256c8; }}
    .zone-right {{ fill: #c9efd8; stroke: #36845c; }}
    .zone-front {{ fill: #ffd6a7; stroke: #ba6d1e; }}
    .zone-rear {{ fill: #ffc9d4; stroke: #bd4359; }}
    .zone-wheels {{ fill: #d8dbe3; stroke: #68717f; }}
    .zone-default {{ fill: #e8edf5; stroke: #7a8797; }}
    .path-line {{
      fill: none;
      stroke-width: 2.2;
      opacity: 0.2;
      transition: opacity 160ms, stroke-width 160ms;
    }}
    .path-line.active-path {{
      opacity: 1;
      stroke-width: 6;
      filter: drop-shadow(0 0 4px rgba(208, 66, 36, 0.4));
    }}
    .zone-label, .axis-label {{
      fill: #243241;
      font-size: 12px;
      text-anchor: middle;
      pointer-events: none;
    }}
    .svg-title {{ fill: var(--ink); font-size: 17px; font-weight: 700; }}
    .controls {{
      display: grid;
      grid-template-columns: auto auto auto 1fr auto;
      gap: 10px;
      align-items: center;
      margin: 14px 0 0;
    }}
    button {{
      border: 1px solid var(--line);
      border-radius: 8px;
      background: #fff;
      color: var(--ink);
      padding: 8px 12px;
      font-weight: 700;
      cursor: pointer;
    }}
    button:hover {{ border-color: var(--active); color: var(--active); }}
    input[type="range"] {{ width: 100%; }}
    .time-readout {{ font-weight: 700; white-space: nowrap; }}
    .state-list, .nozzle-list {{
      list-style: none;
      padding: 0;
      margin: 0;
      display: grid;
      gap: 8px;
    }}
    .state-item, .nozzle-item {{
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 9px 10px;
      background: #fff;
    }}
    .state-item strong, .state-item span, .state-item em {{ display: block; }}
    .state-item span {{ color: var(--muted); font-size: 13px; }}
    .state-item em {{ color: var(--muted); font-size: 12px; font-style: normal; }}
    .state-item.active-state, .nozzle-item.active-nozzle {{
      border-color: var(--active);
      background: var(--active-soft);
      box-shadow: inset 4px 0 0 var(--active);
    }}
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
    .limitations {{
      border: 1px solid #e8d3b8;
      background: #fff8ef;
      border-radius: 8px;
      padding: 12px 18px;
    }}
    @media (max-width: 980px) {{
      main, header {{ padding-left: 20px; padding-right: 20px; }}
      .layout {{ grid-template-columns: 1fr; }}
      .controls {{ grid-template-columns: 1fr 1fr 1fr; }}
      .controls input, .controls .time-readout {{ grid-column: 1 / -1; }}
    }}
  </style>
</head>
<body>
  <header>
    <h1>Stage3.2 Timeline Animation Report</h1>
    <p>基于阶段2 JSON 和阶段3.1 2D图形逻辑生成的轻量时间轴动画。单文件 HTML，不依赖外网 CDN。</p>
    <section class="metrics">{render_summary_cards(summary)}</section>
  </header>
  <main>
    <section class="layout">
      <div>
        <div class="panel">
          {top_view_svg}
          <div class="controls" aria-label="timeline controls">
            <button id="playButton" type="button">Play</button>
            <button id="pauseButton" type="button">Pause</button>
            <button id="resetButton" type="button">Reset</button>
            <input id="timeSlider" class="slider" type="range" min="0" max="{total_seconds}" step="1" value="0" aria-label="timeline slider">
            <span id="timeReadout" class="time-readout">0s / {total_seconds}s</span>
          </div>
        </div>
        <section>
          <h2>覆盖率面板</h2>
          {render_coverage_panel(coverage_report)}
        </section>
        <section>
          <h2>路径统计面板</h2>
          {render_path_statistics(abstract_nozzle_path_plan)}
        </section>
      </div>
      <aside>
        <div class="current-panel">
          <h2>当前状态面板</h2>
          <div class="current-grid">
            <div><strong>current state_id</strong><span id="currentStateId">-</span></div>
            <div><strong>display_name</strong><span id="currentDisplayName">-</span></div>
            <div><strong>state_type</strong><span id="currentStateType">-</span></div>
            <div><strong>duration_seconds</strong><span id="currentDuration">-</span></div>
            <div><strong>start_time_s</strong><span id="currentStart">-</span></div>
            <div><strong>end_time_s</strong><span id="currentEnd">-</span></div>
            <div><strong>target_zone_ids</strong><span id="currentZones">-</span></div>
            <div><strong>assigned_nozzles</strong><span id="currentNozzles">-</span></div>
          </div>
        </div>
        <section>
          <h2>状态列表 timeline</h2>
          {render_state_list(wash_flow_run)}
        </section>
        <section>
          <h2>喷嘴列表</h2>
          {render_nozzle_panel(nozzle_coverage_plan)}
        </section>
      </aside>
    </section>

    <section class="limitations">
      <h2>limitations</h2>
      {render_limitations()}
    </section>
  </main>

  <script type="application/json" id="timeline-data">{json_script(timeline)}</script>
  <script type="application/json" id="path-segment-data">{json_script(path_segments)}</script>
  <script>
    const timelineData = JSON.parse(document.getElementById('timeline-data').textContent);
    const pathSegments = JSON.parse(document.getElementById('path-segment-data').textContent);
    const totalSeconds = {total_seconds};
    const playbackSpeed = 5;
    let currentTime = 0;
    let playing = false;
    let rafId = null;
    let lastTickMs = null;

    const slider = document.getElementById('timeSlider');
    const timeReadout = document.getElementById('timeReadout');
    const playButton = document.getElementById('playButton');
    const pauseButton = document.getElementById('pauseButton');
    const resetButton = document.getElementById('resetButton');

    function findCurrentState(timeValue) {{
      if (!timelineData.length) return null;
      if (timeValue <= 0) return timelineData[0];
      if (timeValue >= totalSeconds) return timelineData[timelineData.length - 1];
      const matched = timelineData.find((item) => {{
        const start = Number(item.start_time_s || 0);
        const end = Number(item.end_time_s || 0);
        return timeValue > start && timeValue <= end;
      }});
      if (matched) return matched;
      return timelineData[timelineData.length - 1];
    }}

    function cssEscape(value) {{
      if (window.CSS && typeof CSS.escape === 'function') return CSS.escape(String(value));
      return String(value).replace(/"/g, '\\"');
    }}

    function setText(id, value) {{
      document.getElementById(id).textContent = Array.isArray(value) ? value.join(', ') || '-' : String(value ?? '-');
    }}

    function clearActive(selector, className) {{
      document.querySelectorAll(selector).forEach((node) => node.classList.remove(className));
    }}

    function updateActiveState(state) {{
      clearActive('.state-item', 'active-state');
      clearActive('.surface-zone', 'active-zone');
      clearActive('.path-line', 'active-path');
      clearActive('.nozzle-item', 'active-nozzle');
      if (!state) return;

      const stateId = state.state_id;
      const zones = state.target_zone_ids || [];
      const nozzles = state.assigned_nozzles || [];

      document.querySelectorAll(`[data-state-id="${{cssEscape(stateId)}}"]`).forEach((node) => {{
        if (node.classList.contains('state-item')) node.classList.add('active-state');
        if (node.classList.contains('path-line')) node.classList.add('active-path');
      }});
      zones.forEach((zoneId) => {{
        document.querySelectorAll(`[data-zone-id="${{cssEscape(zoneId)}}"]`).forEach((node) => {{
          if (node.classList.contains('surface-zone')) node.classList.add('active-zone');
        }});
      }});
      nozzles.forEach((nozzleId) => {{
        document.querySelectorAll(`[data-nozzle-id="${{cssEscape(nozzleId)}}"]`).forEach((node) => {{
          if (node.classList.contains('nozzle-item')) node.classList.add('active-nozzle');
        }});
      }});
    }}

    function renderAt(timeValue) {{
      currentTime = Math.max(0, Math.min(totalSeconds, timeValue));
      const rounded = Math.round(currentTime);
      slider.value = String(rounded);
      timeReadout.textContent = `${{rounded}}s / ${{totalSeconds}}s`;
      const state = findCurrentState(currentTime);
      if (!state) return;
      setText('currentStateId', state.state_id);
      setText('currentDisplayName', state.display_name);
      setText('currentStateType', state.state_type);
      setText('currentDuration', state.duration_seconds);
      setText('currentStart', state.start_time_s);
      setText('currentEnd', state.end_time_s);
      setText('currentZones', state.target_zone_ids || []);
      setText('currentNozzles', state.assigned_nozzles || []);
      updateActiveState(state);
    }}

    function pause() {{
      playing = false;
      lastTickMs = null;
      if (rafId !== null) cancelAnimationFrame(rafId);
      rafId = null;
    }}

    function tick(timestamp) {{
      if (!playing) return;
      if (lastTickMs === null) lastTickMs = timestamp;
      const deltaSeconds = ((timestamp - lastTickMs) / 1000) * playbackSpeed;
      lastTickMs = timestamp;
      renderAt(currentTime + deltaSeconds);
      if (currentTime >= totalSeconds) {{
        pause();
        return;
      }}
      rafId = requestAnimationFrame(tick);
    }}

    playButton.addEventListener('click', () => {{
      if (playing) return;
      playing = true;
      rafId = requestAnimationFrame(tick);
    }});
    pauseButton.addEventListener('click', pause);
    resetButton.addEventListener('click', () => {{
      pause();
      renderAt(0);
    }});
    slider.addEventListener('input', (event) => {{
      pause();
      renderAt(Number(event.target.value));
    }});

    renderAt(0);
  </script>
</body>
</html>
"""
    summary["state_count"] = len(timeline)
    return html_text, summary
