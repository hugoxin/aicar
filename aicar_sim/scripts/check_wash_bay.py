import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
sys.path.insert(0, str(SRC_ROOT))

from aicar_sim.wash_bay import load_wash_bay, validate_wash_bay  # noqa: E402


def main() -> None:
    bay = load_wash_bay("demo_wash_bay")
    validate_wash_bay(bay)

    required = ("bay_dimensions", "gantry", "safety_margin", "coordinate_system")
    missing = [field for field in required if field not in bay]
    if missing:
        raise AssertionError(f"demo_wash_bay missing fields: {missing}")

    print("PASS demo_wash_bay")
    print("AI car wash bay check OK")


if __name__ == "__main__":
    main()
