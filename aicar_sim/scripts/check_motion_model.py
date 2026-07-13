import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
sys.path.insert(0, str(SRC_ROOT))

from aicar_sim.motion_model import load_motion_model, validate_motion_model  # noqa: E402


MOTION_MODEL_PATH = PROJECT_ROOT / "data" / "motion_models" / "demo_cartesian_gantry.json"


def main() -> None:
    model = load_motion_model(MOTION_MODEL_PATH)
    validate_motion_model(model)
    print("PASS stage4 motion model")
    print("AI car motion model check OK")


if __name__ == "__main__":
    main()
