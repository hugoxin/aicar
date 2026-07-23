import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from aicar_sim.geometry_demo_runner import run_all, write_pipeline_outputs  # noqa: E402

results, comparison = run_all()
write_pipeline_outputs(results, comparison)
path = ROOT / "outputs/geometry_validation/stage4_geometry_pose_report.html"
text = path.read_text(encoding="utf-8")
for phrase in ("Stage4.6", "Geometry source comparison", "Dimension replacement", "Normals and poses", "Motion and safety", "not real CAD", "cannot control hardware"):
    assert phrase in text
assert comparison["status"] == "ACCEPTED_WITH_WARNINGS"
print("geometry pose report check: PASS")
