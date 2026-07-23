import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from aicar_sim.geometry_demo_runner import ensure_prerequisites  # noqa: E402

paths = ensure_prerequisites()
expected = ["demo_sedan_mesh.obj", "demo_sedan_mesh.stl", "demo_sedan_cloud.ply", "demo_sedan_cloud.xyz", "demo_sedan_cloud.csv"]
assert all((paths["fixture_dir"] / name).exists() for name in expected)
manifest = json.loads((paths["fixture_dir"] / "demo_geometry_fixture_manifest.json").read_text(encoding="utf-8"))
assert manifest["generated_from_analytic_reference"] and manifest["not_real_scan"]
assert manifest["point_count"] > 0 and manifest["triangle_count"] > 0
print("geometry fixtures check: PASS")
print("fixtures are generated analytic references, not real CAD or scan data")
