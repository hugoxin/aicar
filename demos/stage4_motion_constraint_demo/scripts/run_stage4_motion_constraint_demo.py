import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path


DEMO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_AICAR_ROOT = DEMO_ROOT.parents[1]
DEFAULT_OUTPUT_ROOT = DEMO_ROOT / "demo_outputs"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the Stage4 motion constraint demo.")
    parser.add_argument("--aicar-root", default=str(DEFAULT_AICAR_ROOT))
    parser.add_argument("--output-root", default=str(DEFAULT_OUTPUT_ROOT.relative_to(DEMO_ROOT)))
    parser.add_argument("--open-report", action="store_true")
    return parser


def resolve(path_text: str, base: Path) -> Path:
    path = Path(path_text)
    return (path if path.is_absolute() else base / path).resolve()


def run_script(aicar_root: Path, script_name: str) -> None:
    command = [sys.executable, str(aicar_root / "aicar_sim" / "scripts" / script_name)]
    completed = subprocess.run(command, cwd=str(aicar_root), text=True, capture_output=True)
    if completed.stdout.strip():
        print(completed.stdout.strip())
    if completed.stderr.strip():
        print(completed.stderr.strip(), file=sys.stderr)
    if completed.returncode != 0:
        raise SystemExit(completed.returncode)


def load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def main() -> None:
    args = build_parser().parse_args()
    aicar_root = resolve(args.aicar_root, Path.cwd())
    output_root = resolve(args.output_root, DEMO_ROOT)
    json_dir = output_root / "json"
    report_dir = output_root / "reports"
    json_dir.mkdir(parents=True, exist_ok=True)
    report_dir.mkdir(parents=True, exist_ok=True)

    run_script(aicar_root, "generate_machine_path_plan.py")
    run_script(aicar_root, "generate_motion_validation_report.py")

    machine_path = aicar_root / "aicar_sim" / "outputs" / "machine_path" / "machine_path_plan.json"
    validation_path = aicar_root / "aicar_sim" / "outputs" / "motion_validation" / "motion_validation_report.json"
    report_path = aicar_root / "aicar_sim" / "outputs" / "motion_validation" / "stage4_motion_validation_report.html"
    for source in (machine_path, validation_path, report_path):
        if not source.exists():
            raise SystemExit(f"missing Stage4 output: {source}")

    demo_machine_path = json_dir / machine_path.name
    demo_validation_path = json_dir / validation_path.name
    demo_report_path = report_dir / report_path.name
    shutil.copy2(machine_path, demo_machine_path)
    shutil.copy2(validation_path, demo_validation_path)
    shutil.copy2(report_path, demo_report_path)

    machine = load_json(machine_path)
    validation = load_json(validation_path)
    print(f"validation_status: {validation['validation_status']}")
    print(f"motion_model_id: {machine['motion_model_id']}")
    print(f"trajectory_point_count: {machine['summary']['trajectory_point_count']}")
    print(f"violation_count: {validation['violation_count']}")
    print(f"warning_count: {validation['warning_count']}")
    print(f"report path: {demo_report_path.resolve()}")

    if args.open_report:
        if os.name == "nt":
            os.startfile(demo_report_path)  # type: ignore[attr-defined]
        else:
            print(f"Open this report manually: {demo_report_path.resolve()}")


if __name__ == "__main__":
    main()
