import argparse
import json
import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
WORKSPACE_ROOT = PROJECT_ROOT.parent
SRC_ROOT = PROJECT_ROOT / "src"
sys.path.insert(0, str(SRC_ROOT))

from aicar_sim.machine_path_planner import build_machine_feasible_path_plan  # noqa: E402
from aicar_sim.motion_model import load_motion_model  # noqa: E402


DEFAULT_ABSTRACT_PATH = PROJECT_ROOT / "outputs" / "path_plan" / "abstract_nozzle_path_plan.json"
DEFAULT_SPACE_MODEL = PROJECT_ROOT / "outputs" / "space_model" / "space_model_report.json"
DEFAULT_NOZZLE_PLAN = PROJECT_ROOT / "outputs" / "nozzle_plan" / "nozzle_coverage_plan.json"
DEFAULT_MOTION_MODEL = PROJECT_ROOT / "data" / "motion_models" / "demo_cartesian_gantry.json"
DEFAULT_OUTPUT = PROJECT_ROOT / "outputs" / "machine_path" / "machine_path_plan.json"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate a Stage4 machine-feasible candidate path.")
    parser.add_argument("--abstract-path", default=str(DEFAULT_ABSTRACT_PATH.relative_to(WORKSPACE_ROOT)))
    parser.add_argument("--space-model", default=str(DEFAULT_SPACE_MODEL.relative_to(WORKSPACE_ROOT)))
    parser.add_argument("--nozzle-plan", default=str(DEFAULT_NOZZLE_PLAN.relative_to(WORKSPACE_ROOT)))
    parser.add_argument("--motion-model", default=str(DEFAULT_MOTION_MODEL.relative_to(WORKSPACE_ROOT)))
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT.relative_to(WORKSPACE_ROOT)))
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


def ensure_stage2_inputs(paths: list[Path]) -> None:
    if all(path.exists() for path in paths):
        return
    command = [sys.executable, str(PROJECT_ROOT / "scripts" / "generate_abstract_nozzle_path_plan.py")]
    completed = subprocess.run(command, cwd=str(WORKSPACE_ROOT), text=True, capture_output=True)
    if completed.returncode != 0:
        if completed.stdout.strip():
            print(completed.stdout.strip())
        if completed.stderr.strip():
            print(completed.stderr.strip(), file=sys.stderr)
        raise SystemExit(completed.returncode)
    missing = [path for path in paths if not path.exists()]
    if missing:
        raise SystemExit(f"Stage2 generator did not create required inputs: {', '.join(str(path) for path in missing)}")


def main() -> None:
    args = build_parser().parse_args()
    abstract_path = resolve(args.abstract_path)
    space_model = resolve(args.space_model)
    nozzle_plan = resolve(args.nozzle_plan)
    motion_model_path = resolve(args.motion_model)
    output_path = resolve(args.output)
    ensure_stage2_inputs([abstract_path, space_model, nozzle_plan])

    plan = build_machine_feasible_path_plan(
        load_json(abstract_path),
        load_json(space_model),
        load_json(nozzle_plan),
        load_motion_model(motion_model_path),
    )
    write_json(output_path, plan)
    summary = plan["summary"]
    print(f"motion_model_id: {plan['motion_model_id']}")
    for key in (
        "source_segment_count",
        "source_point_count",
        "trajectory_point_count",
        "transition_segment_count",
        "path_length_mm",
        "estimated_motion_duration_s",
        "maximum_velocity_mm_s",
        "maximum_acceleration_mm_s2",
        "warning_count",
    ):
        print(f"{key}: {summary[key]}")
    print(f"output path: {output_path}")


if __name__ == "__main__":
    main()
