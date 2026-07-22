import subprocess
from pathlib import Path


DEMO_ROOT = Path(__file__).resolve().parents[1]
WORKSPACE_ROOT = DEMO_ROOT.parents[1]


def main() -> None:
    required = (
        "README.md",
        "scripts/run_stage4_continuous_surface_path_repair_demo.py",
        "scripts/check_stage4_continuous_surface_path_repair_demo.py",
        "templates/stage4_continuous_surface_path_repair_report_template.html",
        "docs/STAGE4_CONTINUOUS_SURFACE_PATH_REPAIR_DEMO_EXPLANATION.md",
        "demo_outputs/json/.gitkeep",
        "demo_outputs/reports/.gitkeep",
    )
    missing = [path for path in required if not (DEMO_ROOT / path).exists()]
    if missing:
        raise SystemExit("repair demo scaffold missing: " + ", ".join(missing))
    ignored_samples = (
        "demos/stage4_continuous_surface_path_repair_demo/demo_outputs/json/check.json",
        "demos/stage4_continuous_surface_path_repair_demo/demo_outputs/reports/check.html",
    )
    for sample in ignored_samples:
        if subprocess.run(["git", "check-ignore", "-q", sample], cwd=WORKSPACE_ROOT).returncode:
            raise SystemExit(f"repair demo generated output is not ignored: {sample}")
    print("PASS stage4 continuous surface path repair demo")
    print("AI car continuous surface path repair demo check OK")


if __name__ == "__main__":
    main()
