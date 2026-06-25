from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]

REQUIRED_PATHS = [
    "README.md",
    "requirements.txt",
    "pyproject.toml",
    "config/sim_config.yaml",
    "config/wash_recipe_basic.yaml",
    "data/vehicles/sedan.json",
    "data/vehicles/suv.json",
    "data/vehicles/mpv.json",
    "scripts/check_vehicle_model_selection.py",
    "scripts/check_all_vehicle_model_selection.py",
    "src/aicar_sim/__init__.py",
    "src/aicar_sim/main.py",
    "src/aicar_sim/vehicle_type_input.py",
    "tests/fixtures/vehicle_type_result_sedan.json",
    "tests/fixtures/vehicle_type_result_suv.json",
    "tests/fixtures/vehicle_type_result_mpv.json",
    "tests/fixtures/vehicle_type_result_unknown.json",
]


def main() -> None:
    missing = [path for path in REQUIRED_PATHS if not (PROJECT_ROOT / path).exists()]
    if missing:
        print("Missing aicar_sim scaffold paths:")
        for path in missing:
            print(f"- {path}")
        raise SystemExit(1)

    print("aicar_sim scaffold OK")


if __name__ == "__main__":
    main()
