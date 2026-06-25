from pathlib import Path


def test_main_script_exists() -> None:
    root = Path(__file__).resolve().parents[1]
    assert (root / "src" / "vehicle_type_lab" / "main.py").exists()

