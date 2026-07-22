import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from aicar_sim.continuous_surface_path_planner import load_continuous_path_profile  # noqa: E402


def main() -> None:
    load_continuous_path_profile(PROJECT_ROOT / "data/continuous_path_profiles/demo_continuous_surface_scan_profile.json")
    print("PASS stage4 continuous path profile")
    print("AI car continuous path profile check OK")


if __name__ == "__main__":
    main()
