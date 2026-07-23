from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
required = [
    ROOT / "README.md",
    ROOT / "templates/stage4_geometry_pose_report_template.html",
    ROOT / "docs/STAGE4_GEOMETRY_POSE_DEMO_EXPLANATION.md",
    ROOT / "demo_outputs/json/.gitkeep",
    ROOT / "demo_outputs/reports/.gitkeep",
]
missing = [str(path) for path in required if not path.exists()]
if missing:
    raise SystemExit("missing Stage4.6 demo files: " + ", ".join(missing))
print("Stage4.6 geometry pose demo scaffold check: PASS")
