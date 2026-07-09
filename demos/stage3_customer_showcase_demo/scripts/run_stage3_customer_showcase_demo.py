import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path


DEMO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_AICAR_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_OUTPUT_ROOT = DEMO_ROOT / "demo_outputs"
VEHICLE_TYPE_RESULT = Path("vehicle_type_lab/outputs/predictions/vehicle_type_result.json")
STAGE2_JSON_OUTPUTS = {
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
    parser = argparse.ArgumentParser(description="Run the Stage3.3 customer showcase demo.")
    parser.add_argument(
        "--vehicle-type-result",
        default=str(VEHICLE_TYPE_RESULT),
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


def load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def ensure_output_dirs(output_root: Path) -> dict[str, Path]:
    dirs = {
        "reports": output_root / "reports",
        "json": output_root / "json",
    }
    for path in dirs.values():
        path.mkdir(parents=True, exist_ok=True)
    return dirs


def run_generator(aicar_root: Path, vehicle_type_result: Path) -> Path:
    report_path = (
        aicar_root
        / "aicar_sim"
        / "outputs"
        / "customer_showcase"
        / "stage3_customer_showcase_report.html"
    )
    command = [
        sys.executable,
        str(aicar_root / "aicar_sim" / "scripts" / "generate_customer_showcase_report.py"),
        "--vehicle-type-result",
        str(vehicle_type_result),
        "--output",
        str(report_path),
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
    return report_path


def copy_json_outputs(aicar_root: Path, vehicle_type_result: Path, json_dir: Path) -> None:
    if vehicle_type_result.exists():
        shutil.copy2(vehicle_type_result, json_dir / vehicle_type_result.name)
    for relative_path in STAGE2_JSON_OUTPUTS.values():
        source = aicar_root / relative_path
        if source.exists():
            shutil.copy2(source, json_dir / source.name)


def build_summary(aicar_root: Path) -> dict:
    coverage = load_json(aicar_root / STAGE2_JSON_OUTPUTS["coverage_report"])
    return {
        "vehicle_type": coverage["vehicle"]["vehicle_type"],
        "wash_profile": coverage["wash_profile"],
        "coverage_pass": coverage["coverage_summary"]["coverage_pass"],
    }


def main() -> None:
    args = build_parser().parse_args()
    aicar_root = resolve_path(args.aicar_root, Path.cwd())
    output_root = resolve_path(args.output_root, DEMO_ROOT)
    vehicle_type_result = resolve_path(args.vehicle_type_result, aicar_root)

    if not vehicle_type_result.exists():
        print(f"Missing vehicle type result: {vehicle_type_result}")
        print("Run stage1 classify or Stage1 Demo first.")
        raise SystemExit(1)

    dirs = ensure_output_dirs(output_root)
    source_report = run_generator(aicar_root, vehicle_type_result)
    demo_report = dirs["reports"] / "stage3_customer_showcase_report.html"
    shutil.copy2(source_report, demo_report)
    copy_json_outputs(aicar_root, vehicle_type_result, dirs["json"])
    summary = build_summary(aicar_root)

    print(f"report path: {demo_report.resolve()}")
    print(f"vehicle_type: {summary['vehicle_type']}")
    print(f"wash_profile: {summary['wash_profile']}")
    print(f"coverage_pass: {summary['coverage_pass']}")

    if args.open_report:
        if os.name == "nt":
            os.startfile(demo_report)  # type: ignore[attr-defined]
        else:
            print(f"Open this report manually: {demo_report.resolve()}")


if __name__ == "__main__":
    main()
