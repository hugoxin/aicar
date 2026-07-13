import argparse
import json
import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
WORKSPACE_ROOT = PROJECT_ROOT.parent
SRC_ROOT = PROJECT_ROOT / "src"
sys.path.insert(0, str(SRC_ROOT))

from aicar_sim.motion_model import load_motion_model  # noqa: E402
from aicar_sim.motion_validation_report import build_motion_validation_html  # noqa: E402
from aicar_sim.motion_validator import validate_machine_path  # noqa: E402


DEFAULT_MACHINE_PATH = PROJECT_ROOT / "outputs" / "machine_path" / "machine_path_plan.json"
DEFAULT_MOTION_MODEL = PROJECT_ROOT / "data" / "motion_models" / "demo_cartesian_gantry.json"
DEFAULT_SPACE_MODEL = PROJECT_ROOT / "outputs" / "space_model" / "space_model_report.json"
DEFAULT_NOZZLE_PLAN = PROJECT_ROOT / "outputs" / "nozzle_plan" / "nozzle_coverage_plan.json"
DEFAULT_JSON_OUTPUT = PROJECT_ROOT / "outputs" / "motion_validation" / "motion_validation_report.json"
DEFAULT_HTML_OUTPUT = PROJECT_ROOT / "outputs" / "motion_validation" / "stage4_motion_validation_report.html"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate Stage4 motion validation JSON and HTML reports.")
    parser.add_argument("--machine-path", default=str(DEFAULT_MACHINE_PATH.relative_to(WORKSPACE_ROOT)))
    parser.add_argument("--motion-model", default=str(DEFAULT_MOTION_MODEL.relative_to(WORKSPACE_ROOT)))
    parser.add_argument("--space-model", default=str(DEFAULT_SPACE_MODEL.relative_to(WORKSPACE_ROOT)))
    parser.add_argument("--nozzle-plan", default=str(DEFAULT_NOZZLE_PLAN.relative_to(WORKSPACE_ROOT)))
    parser.add_argument("--json-output", default=str(DEFAULT_JSON_OUTPUT.relative_to(WORKSPACE_ROOT)))
    parser.add_argument("--html-output", default=str(DEFAULT_HTML_OUTPUT.relative_to(WORKSPACE_ROOT)))
    return parser


def resolve(path_text: str) -> Path:
    path = Path(path_text)
    return (path if path.is_absolute() else WORKSPACE_ROOT / path).resolve()


def load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=2)
        file.write("\n")


def ensure_machine_path(path: Path) -> None:
    if path.exists():
        return
    command = [sys.executable, str(PROJECT_ROOT / "scripts" / "generate_machine_path_plan.py"), "--output", str(path)]
    completed = subprocess.run(command, cwd=str(WORKSPACE_ROOT), text=True, capture_output=True)
    if completed.returncode != 0:
        if completed.stdout.strip():
            print(completed.stdout.strip())
        if completed.stderr.strip():
            print(completed.stderr.strip(), file=sys.stderr)
        raise SystemExit(completed.returncode)


def main() -> None:
    args = build_parser().parse_args()
    machine_path_path = resolve(args.machine_path)
    motion_model_path = resolve(args.motion_model)
    space_model_path = resolve(args.space_model)
    nozzle_plan_path = resolve(args.nozzle_plan)
    json_output = resolve(args.json_output)
    html_output = resolve(args.html_output)
    ensure_machine_path(machine_path_path)
    for path in (space_model_path, nozzle_plan_path):
        if not path.exists():
            raise SystemExit(f"missing Stage2 input: {path}")

    machine_path = load_json(machine_path_path)
    motion_model = load_motion_model(motion_model_path)
    space_model = load_json(space_model_path)
    nozzle_plan = load_json(nozzle_plan_path)
    report = validate_machine_path(machine_path, motion_model, space_model, nozzle_plan)
    html_text = build_motion_validation_html(machine_path, motion_model, space_model, report)
    write_json(json_output, report)
    html_output.parent.mkdir(parents=True, exist_ok=True)
    html_output.write_text(html_text, encoding="utf-8")

    summary = report["summary"]
    print(f"validation_status: {report['validation_status']}")
    print(f"violation_count: {report['violation_count']}")
    print(f"warning_count: {report['warning_count']}")
    print(f"trajectory_point_count: {summary['trajectory_point_count']}")
    print(f"path_length_mm: {summary['path_length_mm']}")
    print(f"estimated_motion_duration_s: {summary['estimated_motion_duration_s']}")
    print(f"JSON output: {json_output}")
    print(f"HTML output: {html_output}")


if __name__ == "__main__":
    main()
