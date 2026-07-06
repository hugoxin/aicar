import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
sys.path.insert(0, str(SRC_ROOT))

from aicar_sim.wash_profile import REQUIRED_FIELDS, load_wash_profile  # noqa: E402


PROFILES = ("standard_sedan", "standard_suv", "standard_mpv")


def main() -> None:
    for profile_name in PROFILES:
        profile = load_wash_profile(profile_name)
        missing = [field for field in REQUIRED_FIELDS if field not in profile]
        if missing:
            raise AssertionError(f"{profile_name} missing fields: {missing}")
        if profile["wash_profile"] != profile_name:
            raise AssertionError(
                f"{profile_name}: expected wash_profile={profile_name}, got {profile['wash_profile']}"
            )
        if profile.get("fallback_used"):
            raise AssertionError(f"{profile_name}: unexpected fallback")
        print(f"PASS {profile_name}")

    print("AI car wash profile selection check OK")


if __name__ == "__main__":
    main()
