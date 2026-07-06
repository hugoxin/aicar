"""Load Stage2.1 wash profile configuration."""

import json
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_PROFILES_DIR = PROJECT_ROOT / "data" / "wash_profiles"
DEFAULT_PROFILE = "standard_suv"
SUPPORTED_PROFILES = {"standard_sedan", "standard_suv", "standard_mpv"}
REQUIRED_FIELDS = (
    "wash_profile",
    "vehicle_type",
    "safe_distance_mm",
    "top_clearance_mm",
    "side_clearance_mm",
    "front_rear_clearance_mm",
    "gantry_speed_mm_s",
    "nozzle_travel_speed_mm_s",
    "foam_seconds",
    "dwell_seconds",
    "rinse_seconds",
    "dry_seconds",
    "wheel_focus_seconds",
)


def _profile_path(profile_name: str, profiles_dir: Path) -> Path:
    return profiles_dir / f"{profile_name}.json"


def _validate_profile(profile: dict, path: Path) -> None:
    missing = [field for field in REQUIRED_FIELDS if field not in profile]
    if missing:
        raise ValueError(f"wash profile missing required fields in {path}: {missing}")


def load_wash_profile(profile_name: str | None, profiles_dir: str | Path | None = None) -> dict:
    """Load a wash profile JSON, falling back to standard_suv when needed."""
    profiles_root = Path(profiles_dir) if profiles_dir else DEFAULT_PROFILES_DIR
    requested_profile = str(profile_name or "").strip()
    fallback_used = False
    fallback_reason = ""

    if not requested_profile:
        fallback_used = True
        fallback_reason = "empty wash_profile; fallback to standard_suv"
        selected_profile = DEFAULT_PROFILE
    elif requested_profile not in SUPPORTED_PROFILES:
        fallback_used = True
        fallback_reason = (
            f"unsupported wash_profile '{requested_profile}'; fallback to standard_suv"
        )
        selected_profile = DEFAULT_PROFILE
    else:
        selected_profile = requested_profile

    path = _profile_path(selected_profile, profiles_root)
    if not path.exists():
        fallback_used = True
        fallback_reason = f"wash profile file not found: {path}; fallback to standard_suv"
        selected_profile = DEFAULT_PROFILE
        path = _profile_path(selected_profile, profiles_root)

    if not path.exists():
        raise FileNotFoundError(f"fallback wash profile file not found: {path}")

    with path.open("r", encoding="utf-8") as file:
        profile = json.load(file)

    _validate_profile(profile, path)
    profile["fallback_used"] = fallback_used
    profile["fallback_reason"] = fallback_reason
    profile["profile_path"] = str(path.resolve())
    return profile
