import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from aicar_sim.geometry_demo_runner import ensure_prerequisites  # noqa: E402

paths = ensure_prerequisites()
manifest = json.loads((paths["fixture_dir"] / "demo_geometry_fixture_manifest.json").read_text(encoding="utf-8"))
print(f"fixture point count: {manifest['point_count']}")
print(f"fixture triangle count: {manifest['triangle_count']}")
print("generated_from_analytic_reference: true")
print("not_real_scan: true")
print(f"fixture directory: {paths['fixture_dir']}")
