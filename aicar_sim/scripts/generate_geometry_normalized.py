import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
WORKSPACE_ROOT = PROJECT_ROOT.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from aicar_sim.geometry_source import load_geometry_source  # noqa: E402

parser = argparse.ArgumentParser()
parser.add_argument("--source-type", choices=["ANALYTIC_REFERENCE", "CAD_MESH", "POINT_CLOUD"], default="ANALYTIC_REFERENCE")
parser.add_argument("--source-path")
parser.add_argument("--geometry-profile", default=str(PROJECT_ROOT / "data/geometry_profiles/demo_geometry_import_profile.json"))
parser.add_argument("--dimension-profile", default=str(PROJECT_ROOT / "data/vehicle_dimensions/demo_reference_real_size_sedan_dimensions.json"))
parser.add_argument("--semantic-map", default=str(PROJECT_ROOT / "data/geometry_semantic_maps/demo_sedan_semantic_map.json"))
parser.add_argument("--output", default=str(PROJECT_ROOT / "outputs/geometry_normalized/analytic_geometry_normalized.json"))
args = parser.parse_args()
load = lambda value: json.loads(Path(value).read_text(encoding="utf-8"))
geometry = load_geometry_source(args.source_type, args.source_path, load(args.geometry_profile), load(args.dimension_profile), load(args.semantic_map))
Path(args.output).parent.mkdir(parents=True, exist_ok=True)
Path(args.output).write_text(json.dumps(geometry, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(f"source type: {geometry['geometry_source_type']}")
print(f"unit: {geometry['unit']}")
print(f"patch count: {geometry['semantic_summary']['patch_count']}")
print(f"output path: {Path(args.output).resolve()}")
