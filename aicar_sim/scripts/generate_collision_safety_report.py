import argparse
import json
import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
WORKSPACE_ROOT = PROJECT_ROOT.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from aicar_sim.collision_safety_report import build_collision_safety_html  # noqa: E402


PLAN = PROJECT_ROOT / "outputs/collision_safety/collision_safety_plan.json"
JSON_OUTPUT = PROJECT_ROOT / "outputs/collision_safety/collision_safety_validation_report.json"
HTML_OUTPUT = PROJECT_ROOT / "outputs/collision_safety/stage4_collision_safety_report.html"


def resolve(value: str) -> Path:
    path = Path(value)
    return (path if path.is_absolute() else WORKSPACE_ROOT / path).resolve()


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate Stage4.3 collision safety JSON and HTML reports.")
    parser.add_argument("--plan", default=str(PLAN.relative_to(WORKSPACE_ROOT)))
    parser.add_argument("--json-output", default=str(JSON_OUTPUT.relative_to(WORKSPACE_ROOT)))
    parser.add_argument("--html-output", default=str(HTML_OUTPUT.relative_to(WORKSPACE_ROOT)))
    args = parser.parse_args()
    plan_path = resolve(args.plan)
    if not plan_path.exists():
        completed = subprocess.run([sys.executable, str(PROJECT_ROOT / "scripts/generate_collision_safety_plan.py"), "--output", str(plan_path)], cwd=WORKSPACE_ROOT)
        if completed.returncode:
            raise SystemExit(completed.returncode)
    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    schedule_summary = plan["multi_actuator_schedule"]["summary"]
    report = {
        "report_version": "stage4.3",
        "validation_status": plan["validation_status"],
        "safety_layout_id": plan["safety_layout_id"],
        "actuator_system_id": plan["actuator_system_id"],
        "vehicle_type": plan["vehicle_type"],
        "wash_profile": plan["wash_profile"],
        "summary": plan["summary"],
        "unresolved_conflict_count": schedule_summary["unresolved_conflict_count"],
        "safe_stop_points": plan["safe_stop_points"],
        "warnings": plan["warnings"],
        "violations": plan["violations"],
        "warning_category_counts": plan["warning_category_counts"],
        "violation_category_counts": plan["violation_category_counts"],
        "limitations": plan["limitations"],
    }
    json_output = resolve(args.json_output)
    html_output = resolve(args.html_output)
    json_output.parent.mkdir(parents=True, exist_ok=True)
    html_output.parent.mkdir(parents=True, exist_ok=True)
    json_output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    html_output.write_text(build_collision_safety_html(plan), encoding="utf-8")
    print(f"validation_status: {report['validation_status']}")
    print(f"violation_count: {report['summary']['violation_count']}")
    print(f"warning_count: {report['summary']['warning_count']}")
    print(f"unresolved_conflict_count: {report['unresolved_conflict_count']}")
    print(f"safe_stop_point_count: {report['summary']['safe_stop_point_count']}")
    print(f"JSON path: {json_output}")
    print(f"HTML path: {html_output}")


if __name__ == "__main__":
    main()
