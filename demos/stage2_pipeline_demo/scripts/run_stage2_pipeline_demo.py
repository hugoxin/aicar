import argparse
import html
import json
import os
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path


DEMO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_AICAR_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_OUTPUT_ROOT = DEMO_ROOT / "demo_outputs"
JSON_OUTPUTS = {
    "wash_strategy_plan": Path("aicar_sim/outputs/wash_strategy/wash_strategy_plan.json"),
    "space_model_report": Path("aicar_sim/outputs/space_model/space_model_report.json"),
    "nozzle_coverage_plan": Path("aicar_sim/outputs/nozzle_plan/nozzle_coverage_plan.json"),
    "wash_flow_run": Path("aicar_sim/outputs/wash_flow/wash_flow_run.json"),
    "abstract_nozzle_path_plan": Path(
        "aicar_sim/outputs/path_plan/abstract_nozzle_path_plan.json"
    ),
    "coverage_report": Path("aicar_sim/outputs/coverage_report/coverage_report.json"),
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the AI car stage2 pipeline demo.")
    parser.add_argument(
        "--vehicle-type-result",
        default="vehicle_type_lab/outputs/predictions/vehicle_type_result.json",
        help="Path to vehicle_type_result.json. Relative paths are resolved from F:\\aicar.",
    )
    parser.add_argument(
        "--aicar-root",
        default=str(DEFAULT_AICAR_ROOT),
        help="AI car workspace root.",
    )
    parser.add_argument(
        "--output-root",
        default=str(DEFAULT_OUTPUT_ROOT.relative_to(DEMO_ROOT)),
        help="Demo output root. Relative paths are resolved from the demo root.",
    )
    parser.add_argument(
        "--open-report",
        action="store_true",
        help="Open the generated HTML report after completion.",
    )
    return parser


def resolve_path(path_text: str, base: Path) -> Path:
    path = Path(path_text)
    if not path.is_absolute():
        path = base / path
    return path.resolve()


def resolve_workspace_path(path_text: str, aicar_root: Path) -> Path:
    return resolve_path(path_text, aicar_root)


def ensure_output_dirs(output_root: Path) -> dict[str, Path]:
    dirs = {
        "reports": output_root / "reports",
        "json": output_root / "json",
    }
    for path in dirs.values():
        path.mkdir(parents=True, exist_ok=True)
    return dirs


def run_generator(aicar_root: Path, script_name: str, vehicle_type_result: Path) -> None:
    script_path = aicar_root / "aicar_sim" / "scripts" / script_name
    command = [
        sys.executable,
        str(script_path),
        "--vehicle-type-result",
        str(vehicle_type_result),
    ]
    completed = subprocess.run(
        command,
        cwd=str(aicar_root),
        text=True,
        capture_output=True,
    )
    if completed.stdout.strip():
        print(completed.stdout.strip())
    if completed.stderr.strip():
        print(completed.stderr.strip(), file=sys.stderr)
    if completed.returncode != 0:
        raise SystemExit(completed.returncode)


def load_json_optional(path: Path) -> tuple[dict | None, str | None]:
    if not path.exists():
        return None, f"Missing JSON: {path}"
    try:
        with path.open("r", encoding="utf-8") as file:
            return json.load(file), None
    except Exception as exc:
        return None, f"Failed to load JSON: {path} ({exc})"


def copy_json_outputs(aicar_root: Path, json_dir: Path) -> dict[str, tuple[dict | None, str | None]]:
    loaded = {}
    for key, relative_path in JSON_OUTPUTS.items():
        source = aicar_root / relative_path
        data, error = load_json_optional(source)
        loaded[key] = (data, error)
        if source.exists():
            shutil.copy2(source, json_dir / source.name)
    return loaded


def value(data: dict | None, path: list[str], default: object = "-") -> object:
    current: object = data or {}
    for part in path:
        if not isinstance(current, dict) or part not in current:
            return default
        current = current[part]
    return current


def format_value(item: object) -> str:
    if item is None or item == "":
        return "-"
    if isinstance(item, bool):
        return "true" if item else "false"
    if isinstance(item, float):
        return f"{item:.4f}"
    return str(item)


def metric_card(label: str, item: object) -> str:
    return (
        '<div class="metric">'
        f'<div class="metric-label">{html.escape(label)}</div>'
        f'<div class="metric-value">{html.escape(format_value(item))}</div>'
        "</div>"
    )


def table(headers: list[str], rows: list[list[object]]) -> str:
    if not rows:
        return '<div class="missing">暂无数据</div>'
    lines = ["<table>", "<thead><tr>"]
    for header in headers:
        lines.append(f"<th>{html.escape(header)}</th>")
    lines.append("</tr></thead><tbody>")
    for row in rows:
        lines.append("<tr>")
        for cell in row:
            text = format_value(cell)
            if text.startswith('<div class="progress">'):
                lines.append(f"<td>{text}</td>")
            else:
                lines.append(f"<td>{html.escape(text)}</td>")
        lines.append("</tr>")
    lines.append("</tbody></table>")
    return "\n".join(lines)


def key_value_table(rows: list[tuple[str, object]]) -> str:
    return table(["字段", "值"], [[key, val] for key, val in rows])


def progress_bar(percent: object) -> str:
    try:
        value_percent = max(0, min(100, int(percent)))
    except Exception:
        value_percent = 0
    return (
        '<div class="progress">'
        f'<span style="width:{value_percent}%"></span>'
        "</div>"
    )


def missing_notice(loaded: dict[str, tuple[dict | None, str | None]]) -> str:
    errors = [error for _, error in loaded.values() if error]
    if not errors:
        return ""
    items = "".join(f"<li>{html.escape(error)}</li>" for error in errors)
    return f'<div class="missing"><strong>部分 JSON 缺失：</strong><ul>{items}</ul></div>'


def render_flow_steps() -> str:
    steps = [
        ("阶段2.1", "洗车策略计划"),
        ("阶段2.2", "车辆包络与洗车空间"),
        ("阶段2.3", "喷嘴模型与覆盖参数"),
        ("阶段2.4", "洗车流程状态机"),
        ("阶段2.5", "抽象喷嘴路径点"),
        ("阶段2.6", "覆盖率报告"),
    ]
    return "\n".join(
        f'<div class="flow-step"><strong>{html.escape(code)}</strong>{html.escape(name)}</div>'
        for code, name in steps
    )


def render_strategy(strategy: dict | None) -> str:
    rows = [
        [
            stage.get("stage_id"),
            stage.get("display_name", stage.get("stage_id")),
            stage.get("target_area"),
            stage.get("duration_seconds"),
        ]
        for stage in (strategy or {}).get("stages", [])
    ]
    summary = key_value_table(
        [
            ("plan_version", value(strategy, ["plan_version"])),
            (
                "estimated_total_seconds",
                value(strategy, ["strategy_summary", "estimated_total_seconds"]),
            ),
            ("stage_count", value(strategy, ["strategy_summary", "stage_count"])),
        ]
    )
    return summary + table(["stage_id", "名称", "目标区域", "秒"], rows)


def render_space(space_model: dict | None) -> str:
    envelope = value(space_model, ["vehicle_envelope", "safe_envelope"], {})
    bay = value(space_model, ["wash_bay", "bay_dimensions"], {})
    zones = value(space_model, ["zone_summary", "zones"], [])
    return key_value_table(
        [
            ("wash_bay_id", value(space_model, ["wash_bay", "wash_bay_id"])),
            ("bay length_mm", bay.get("length_mm") if isinstance(bay, dict) else "-"),
            ("bay width_mm", bay.get("width_mm") if isinstance(bay, dict) else "-"),
            ("bay height_mm", bay.get("height_mm") if isinstance(bay, dict) else "-"),
            ("fits_in_bay", value(space_model, ["clearance_check", "fits_in_bay"])),
            ("safe_envelope", envelope),
            ("surface_zones", ", ".join(zones) if isinstance(zones, list) else "-"),
        ]
    )


def render_vehicle_map(coverage_report: dict | None) -> str:
    by_zone = {
        report.get("zone_id"): report
        for report in (coverage_report or {}).get("zone_reports", [])
    }

    def label(zone_id: str, title: str) -> str:
        report = by_zone.get(zone_id, {})
        coverage = report.get("estimated_coverage_percent", "-")
        return f"{title}<br>{coverage}%"

    return (
        '<div class="vehicle-map">'
        f'<div class="zone front">{label("front", "车头")}</div>'
        f'<div class="zone left">{label("left_side", "左侧")}</div>'
        f'<div class="zone roof">{label("roof", "车顶")}</div>'
        f'<div class="zone right">{label("right_side", "右侧")}</div>'
        f'<div class="zone rear">{label("rear", "车尾")}</div>'
        f'<div class="zone wheels">{label("wheels", "轮毂")}</div>'
        "</div>"
    )


def render_nozzle(nozzle_plan: dict | None) -> str:
    rows = []
    for zone in (nozzle_plan or {}).get("zone_coverage", []):
        rows.append(
            [
                zone.get("zone_id"),
                zone.get("target_coverage_percent"),
                ", ".join(
                    nozzle.get("nozzle_id", "-")
                    for nozzle in zone.get("assigned_nozzles", [])
                ),
            ]
        )
    summary = key_value_table(
        [
            ("zone_count", value(nozzle_plan, ["coverage_summary", "zone_count"])),
            ("nozzle_count", value(nozzle_plan, ["coverage_summary", "nozzle_count"])),
            (
                "estimated_coverage_percent",
                value(nozzle_plan, ["coverage_summary", "estimated_coverage_percent"]),
            ),
        ]
    )
    return summary + table(["zone", "目标覆盖率", "喷嘴"], rows)


def render_flow(flow_run: dict | None) -> str:
    rows = [
        [
            item.get("order"),
            item.get("state_id"),
            item.get("duration_seconds"),
            ", ".join(item.get("target_zone_ids", [])),
            ", ".join(item.get("assigned_nozzles", [])),
        ]
        for item in (flow_run or {}).get("timeline", [])
    ]
    return table(["顺序", "状态", "秒", "区域", "喷嘴"], rows)


def render_path(path_plan: dict | None) -> str:
    summary_rows = [
        [
            item.get("state_id"),
            item.get("segment_count"),
            ", ".join(item.get("target_zone_ids", [])),
        ]
        for item in (path_plan or {}).get("state_path_summary", [])
    ]
    examples = [
        [
            segment.get("segment_id"),
            segment.get("state_id"),
            segment.get("zone_id"),
            segment.get("nozzle_id"),
            segment.get("path_type"),
            len(segment.get("points", [])),
        ]
        for segment in (path_plan or {}).get("path_segments", [])[:5]
    ]
    block = key_value_table(
        [
            ("segment_count", value(path_plan, ["summary", "segment_count"])),
            ("point_count", value(path_plan, ["summary", "point_count"])),
        ]
    )
    block += table(["状态", "segment 数", "区域"], summary_rows)
    block += "<h3>示例 path_segment</h3>"
    block += table(["segment_id", "状态", "zone", "nozzle", "path_type", "points"], examples)
    return block


def render_coverage(coverage_report: dict | None) -> str:
    zone_rows = []
    for report in (coverage_report or {}).get("zone_reports", []):
        zone_rows.append(
            [
                report.get("zone_id"),
                report.get("target_coverage_percent"),
                report.get("estimated_coverage_percent"),
                report.get("coverage_pass"),
                report.get("segment_count"),
                report.get("point_count"),
                progress_bar(report.get("estimated_coverage_percent")),
            ]
        )
    summary = key_value_table(
        [
            ("coverage_pass", value(coverage_report, ["coverage_summary", "coverage_pass"])),
            (
                "estimated_actual_coverage_percent",
                value(
                    coverage_report,
                    ["coverage_summary", "estimated_actual_coverage_percent"],
                ),
            ),
            ("warnings", value(coverage_report, ["warnings"])),
            ("improvement_suggestions", value(coverage_report, ["improvement_suggestions"])),
        ]
    )
    return summary + table(
        ["zone", "目标", "估算", "通过", "segments", "points", "进度"],
        zone_rows,
    )


def render_report(
    template_path: Path,
    report_path: Path,
    loaded: dict[str, tuple[dict | None, str | None]],
    vehicle_type_result: Path,
) -> dict[str, object]:
    template = template_path.read_text(encoding="utf-8")
    strategy = loaded["wash_strategy_plan"][0]
    space = loaded["space_model_report"][0]
    nozzle = loaded["nozzle_coverage_plan"][0]
    flow = loaded["wash_flow_run"][0]
    path_plan = loaded["abstract_nozzle_path_plan"][0]
    coverage = loaded["coverage_report"][0]

    summary = {
        "vehicle_type": value(coverage, ["vehicle", "vehicle_type"], value(strategy, ["vehicle", "vehicle_type"])),
        "wash_profile": value(coverage, ["wash_profile"], value(strategy, ["vehicle", "wash_profile"])),
        "wash_bay_id": value(coverage, ["wash_bay_id"], value(space, ["wash_bay", "wash_bay_id"])),
        "estimated_total_seconds": value(path_plan, ["summary", "estimated_total_seconds"]),
        "state_count": value(flow, ["summary", "timeline_state_count"]),
        "segment_count": value(path_plan, ["summary", "segment_count"]),
        "point_count": value(path_plan, ["summary", "point_count"]),
        "estimated_actual_coverage_percent": value(
            coverage,
            ["coverage_summary", "estimated_actual_coverage_percent"],
        ),
        "coverage_pass": value(coverage, ["coverage_summary", "coverage_pass"]),
    }

    summary_cards = "\n".join(
        [
            metric_card("vehicle_type", summary["vehicle_type"]),
            metric_card("wash_profile", summary["wash_profile"]),
            metric_card("wash_bay_id", summary["wash_bay_id"]),
            metric_card("estimated_total_seconds", summary["estimated_total_seconds"]),
            metric_card("state_count", summary["state_count"]),
            metric_card("segment_count", summary["segment_count"]),
            metric_card("point_count", summary["point_count"]),
            metric_card(
                "estimated_actual_coverage_percent",
                summary["estimated_actual_coverage_percent"],
            ),
            metric_card("coverage_pass", summary["coverage_pass"]),
        ]
    )

    html_text = (
        template.replace("{{SUMMARY_CARDS}}", summary_cards)
        .replace("{{MISSING_NOTICE}}", missing_notice(loaded))
        .replace("{{FLOW_STEPS}}", render_flow_steps())
        .replace("{{STRATEGY_SECTION}}", render_strategy(strategy))
        .replace("{{SPACE_SECTION}}", render_space(space))
        .replace("{{VEHICLE_MAP}}", render_vehicle_map(coverage))
        .replace("{{NOZZLE_SECTION}}", render_nozzle(nozzle))
        .replace("{{FLOW_SECTION}}", render_flow(flow))
        .replace("{{PATH_SECTION}}", render_path(path_plan))
        .replace("{{COVERAGE_SECTION}}", render_coverage(coverage))
    )
    generated_note = (
        f"\n<!-- generated_at={datetime.now().isoformat(timespec='seconds')} "
        f"vehicle_type_result={vehicle_type_result} -->\n"
    )
    report_path.write_text(html_text + generated_note, encoding="utf-8")
    return summary


def main() -> None:
    args = build_parser().parse_args()
    aicar_root = resolve_path(args.aicar_root, Path.cwd())
    output_root = resolve_path(args.output_root, DEMO_ROOT)
    vehicle_type_result = resolve_workspace_path(args.vehicle_type_result, aicar_root)

    if not vehicle_type_result.exists():
        print(f"Missing vehicle type result: {vehicle_type_result}")
        print("Run stage1 classify or stage1 visual demo first.")
        raise SystemExit(1)

    dirs = ensure_output_dirs(output_root)
    for script_name in [
        "generate_wash_strategy_plan.py",
        "generate_space_model.py",
        "generate_nozzle_coverage_plan.py",
        "generate_wash_flow_run.py",
        "generate_abstract_nozzle_path_plan.py",
        "generate_coverage_report.py",
    ]:
        run_generator(aicar_root, script_name, vehicle_type_result)

    loaded = copy_json_outputs(aicar_root, dirs["json"])
    report_path = dirs["reports"] / "stage2_pipeline_report.html"
    summary = render_report(
        DEMO_ROOT / "templates" / "stage2_pipeline_report_template.html",
        report_path,
        loaded,
        vehicle_type_result,
    )

    print(f"stage2 pipeline report saved: {report_path.resolve()}")
    print(f"demo json outputs saved: {dirs['json'].resolve()}")
    print(f"vehicle_type: {summary['vehicle_type']}")
    print(f"wash_profile: {summary['wash_profile']}")
    print(f"estimated_total_seconds: {summary['estimated_total_seconds']}")
    print(f"segment_count: {summary['segment_count']}")
    print(f"point_count: {summary['point_count']}")
    print(
        "estimated_actual_coverage_percent: "
        f"{summary['estimated_actual_coverage_percent']}"
    )
    print(f"coverage_pass: {summary['coverage_pass']}")

    if args.open_report:
        if os.name == "nt":
            os.startfile(report_path)  # type: ignore[attr-defined]
        else:
            print(f"Open this report manually: {report_path.resolve()}")


if __name__ == "__main__":
    main()
