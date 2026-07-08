import argparse
import json
import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
WORKSPACE_ROOT = PROJECT_ROOT.parent
SRC_ROOT = PROJECT_ROOT / "src"
sys.path.insert(0, str(SRC_ROOT))

from aicar_sim.timeline_animation import build_timeline_animation_report  # noqa: E402


DEFAULT_RESULT_PATH = (
    WORKSPACE_ROOT
    / "vehicle_type_lab"
    / "outputs"
    / "predictions"
    / "vehicle_type_result.json"
)
DEFAULT_OUTPUT_PATH = (
    PROJECT_ROOT / "outputs" / "timeline_animation" / "stage3_timeline_animation_report.html"
)
STAGE2_OUTPUTS = {
    "wash_strategy_plan": PROJECT_ROOT / "outputs" / "wash_strategy" / "wash_strategy_plan.json",
    "space_model_report": PROJECT_ROOT / "outputs" / "space_model" / "space_model_report.json",
    "nozzle_coverage_plan": PROJECT_ROOT / "outputs" / "nozzle_plan" / "nozzle_coverage_plan.json",
    "wash_flow_run": PROJECT_ROOT / "outputs" / "wash_flow" / "wash_flow_run.json",
    "abstract_nozzle_path_plan": PROJECT_ROOT
    / "outputs"
    / "path_plan"
    / "abstract_nozzle_path_plan.json",
    "coverage_report": PROJECT_ROOT / "outputs" / "coverage_report" / "coverage_report.json",
}
GENERATOR_SCRIPTS = [
    "generate_wash_strategy_plan.py",
    "generate_space_model.py",
    "generate_nozzle_coverage_plan.py",
    "generate_wash_flow_run.py",
    "generate_abstract_nozzle_path_plan.py",
    "generate_coverage_report.py",
]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate Stage3.2 timeline animation HTML.")
    parser.add_argument(
        "--vehicle-type-result",
        default=str(DEFAULT_RESULT_PATH.relative_to(WORKSPACE_ROOT)),
        help="Path to vehicle_type_result.json.",
    )
    parser.add_argument(
        "--output",
        default=str(DEFAULT_OUTPUT_PATH.relative_to(WORKSPACE_ROOT)),
        help="Output path for stage3_timeline_animation_report.html.",
    )
    return parser


def resolve_workspace_path(path_text: str) -> Path:
    path = Path(path_text)
    if not path.is_absolute():
        path = WORKSPACE_ROOT / path
    return path.resolve()


def load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def run_stage2_generator(script_name: str, vehicle_type_result_path: Path) -> None:
    command = [
        sys.executable,
        str(PROJECT_ROOT / "scripts" / script_name),
        "--vehicle-type-result",
        str(vehicle_type_result_path),
    ]
    completed = subprocess.run(
        command,
        cwd=str(WORKSPACE_ROOT),
        text=True,
        capture_output=True,
    )
    if completed.returncode != 0:
        if completed.stdout.strip():
            print(completed.stdout.strip())
        if completed.stderr.strip():
            print(completed.stderr.strip(), file=sys.stderr)
        raise SystemExit(completed.returncode)


def ensure_stage2_outputs(vehicle_type_result_path: Path) -> None:
    if all(path.exists() for path in STAGE2_OUTPUTS.values()):
        return
    for script_name in GENERATOR_SCRIPTS:
        run_stage2_generator(script_name, vehicle_type_result_path)


def main() -> None:
    args = build_parser().parse_args()
    vehicle_type_result_path = resolve_workspace_path(args.vehicle_type_result)
    output_path = resolve_workspace_path(args.output)

    if not vehicle_type_result_path.exists():
        raise SystemExit(f"missing vehicle type result: {vehicle_type_result_path}")

    ensure_stage2_outputs(vehicle_type_result_path)
    data = {name: load_json(path) for name, path in STAGE2_OUTPUTS.items()}
    html_text, summary = build_timeline_animation_report(
        data["wash_strategy_plan"],
        data["space_model_report"],
        data["nozzle_coverage_plan"],
        data["wash_flow_run"],
        data["abstract_nozzle_path_plan"],
        data["coverage_report"],
    )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(html_text, encoding="utf-8")

    print(f"vehicle_type: {summary['vehicle_type']}")
    print(f"wash_profile: {summary['wash_profile']}")
    print(f"estimated_total_seconds: {summary['estimated_total_seconds']}")
    print(f"state_count: {summary['state_count']}")
    print(f"segment_count: {summary['segment_count']}")
    print(f"point_count: {summary['point_count']}")
    print(f"coverage_pass: {summary['coverage_pass']}")
    print(f"output path: {output_path}")


if __name__ == "__main__":
    main()
