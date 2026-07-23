import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from aicar_sim.geometry_demo_runner import run_source  # noqa: E402

result = run_source("ply")
outputs = {
    PROJECT_ROOT / "outputs/geometry_safety/geometry_collision_safety_plan.json": result["collision_plan"],
    PROJECT_ROOT / "outputs/geometry_safety/geometry_multi_actuator_schedule.json": result["schedule"],
    PROJECT_ROOT / "outputs/geometry_validation/geometry_pose_validation_report.json": result["validation"],
}
for path, value in outputs.items():
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(f"status: {result['validation']['status']}")
print(f"minimum clearance mm: {result['validation']['summary']['minimum_clearance_mm']}")
print(f"violations: {result['validation']['summary']['violation_count']}")
