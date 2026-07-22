import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from aicar_sim.surface_model import REQUIRED_ZONES, all_surface_patches, load_surface_model  # noqa: E402


def main() -> None:
    model = load_surface_model(PROJECT_ROOT / "data/surface_models/demo_sedan_surface_model.json")
    patches = all_surface_patches(model)
    if {item["zone_id"] for item in patches} != REQUIRED_ZONES:
        raise SystemExit("surface model zone set mismatch")
    if len(model["wheel_patches"]) != 4:
        raise SystemExit("surface model must contain four wheel patches")
    print("PASS stage4 continuous surface model")
    print("AI car surface model check OK")


if __name__ == "__main__":
    main()
