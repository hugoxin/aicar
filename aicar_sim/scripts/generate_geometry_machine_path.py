import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from aicar_sim.geometry_demo_runner import run_source  # noqa: E402

result = run_source("ply")
output = PROJECT_ROOT / "outputs/geometry_machine_path/geometry_machine_path_plan.json"
output.parent.mkdir(parents=True, exist_ok=True)
output.write_text(json.dumps(result["machine_plan"], ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(f"trajectory point count: {result['machine_plan']['summary']['trajectory_point_count']}")
print(f"motion duration s: {result['machine_plan']['summary']['estimated_motion_duration_s']}")
print(f"output path: {output}")
