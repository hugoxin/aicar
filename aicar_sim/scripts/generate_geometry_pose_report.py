import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from aicar_sim.geometry_demo_runner import run_all, write_pipeline_outputs  # noqa: E402

results, comparison = run_all()
write_pipeline_outputs(results, comparison)
print(f"status: {comparison['status']}")
print(f"source count: {len(comparison['source_results'])}")
print(f"report path: {PROJECT_ROOT / 'outputs/geometry_validation/stage4_geometry_pose_report.html'}")
