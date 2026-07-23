import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from aicar_sim.geometry_demo_runner import run_source  # noqa: E402

parser = argparse.ArgumentParser()
parser.add_argument("--source", choices=["analytic", "obj", "stl", "ply", "xyz", "csv"], default="analytic")
parser.add_argument("--geometry")
parser.add_argument("--pose-profile")
parser.add_argument("--stage4-5-plan")
parser.add_argument("--output", default=str(PROJECT_ROOT / "outputs/geometry_pose/geometry_nozzle_pose_plan.json"))
args = parser.parse_args()
result = run_source(args.source)
Path(args.output).parent.mkdir(parents=True, exist_ok=True)
Path(args.output).write_text(json.dumps(result["pose_plan"], ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(f"pose count: {result['pose_plan']['pose_summary']['pose_count']}")
print(f"invalid pose count: {result['pose_plan']['pose_summary']['invalid_pose_count']}")
print(f"output path: {Path(args.output).resolve()}")
