import json
import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
WORKSPACE_ROOT = PROJECT_ROOT.parent
OUTPUT = PROJECT_ROOT / "outputs/continuous_surface_path/continuous_surface_path_plan.json"


def main() -> None:
    if not OUTPUT.exists():
        completed = subprocess.run([sys.executable, str(PROJECT_ROOT / "scripts/generate_continuous_surface_path.py")], cwd=WORKSPACE_ROOT)
        if completed.returncode:
            raise SystemExit(completed.returncode)
    plan = json.loads(OUTPUT.read_text(encoding="utf-8"))
    validation = plan["validation"]
    if validation["validation_status"] not in {"PASS", "PASS_WITH_WARNINGS"} or validation["violation_count"]:
        raise SystemExit(f"continuous surface path validation failed: {validation}")
    if plan["summary"]["trajectory_point_count"] > 5000:
        raise SystemExit("continuous surface path exceeds 5000 points")
    if plan["coverage_summary"]["total_coverage_percent"] < 92:
        raise SystemExit("continuous surface total coverage is below 92 percent")
    completed = subprocess.run(["git", "check-ignore", "-q", str(OUTPUT.relative_to(WORKSPACE_ROOT))], cwd=WORKSPACE_ROOT)
    if completed.returncode:
        raise SystemExit("continuous surface output JSON is not ignored")
    print("PASS stage4 continuous surface path")
    print("AI car continuous surface path check OK")


if __name__ == "__main__":
    main()
