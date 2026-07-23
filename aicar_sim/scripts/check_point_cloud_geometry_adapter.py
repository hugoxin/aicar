import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from aicar_sim.geometry_demo_runner import ensure_prerequisites  # noqa: E402
from aicar_sim.point_cloud_geometry_adapter import load_point_cloud_geometry  # noqa: E402

paths = ensure_prerequisites()
profile = json.loads(paths["import_profile"].read_text(encoding="utf-8"))
counts = []
for name in ("demo_sedan_cloud.ply", "demo_sedan_cloud.xyz", "demo_sedan_cloud.csv"):
    cloud = load_point_cloud_geometry(paths["fixture_dir"] / name, profile)
    assert cloud["adapter_summary"]["point_count"] > 0
    assert all(key in point for point in cloud["points"] for key in ("x_mm", "y_mm", "z_mm"))
    counts.append(cloud["adapter_summary"]["point_count"])
assert len(set(counts)) == 1
print("point cloud geometry adapter check: PASS (ASCII PLY, XYZ, CSV)")
