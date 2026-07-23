import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from aicar_sim.geometry_demo_runner import ensure_prerequisites  # noqa: E402
from aicar_sim.mesh_geometry_adapter import load_mesh_geometry  # noqa: E402

paths = ensure_prerequisites()
profile = json.loads(paths["import_profile"].read_text(encoding="utf-8"))
for name in ("demo_sedan_mesh.obj", "demo_sedan_mesh.stl"):
    mesh = load_mesh_geometry(paths["fixture_dir"] / name, profile)
    assert mesh["adapter_summary"]["vertex_count"] > 0
    assert mesh["adapter_summary"]["triangle_count"] > 0
    assert mesh["adapter_summary"]["degenerate_triangle_count"] == 0
print("mesh geometry adapter check: PASS (ASCII OBJ, ASCII STL)")
