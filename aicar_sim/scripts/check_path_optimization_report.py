import json
import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
WORKSPACE_ROOT = PROJECT_ROOT.parent
JSON_PATH = PROJECT_ROOT / "outputs/path_optimization/path_optimization_report.json"
HTML_PATH = PROJECT_ROOT / "outputs/path_optimization/stage4_path_optimization_report.html"
TOKENS = ["stage4.4", "path optimization", "transition", "schedule", "clearance", "collision", "interlock", "safety", "limitations"]


def main() -> None:
    completed = subprocess.run([sys.executable, str(PROJECT_ROOT / "scripts/generate_path_optimization_report.py")], cwd=WORKSPACE_ROOT)
    if completed.returncode:
        raise SystemExit(completed.returncode)
    if not JSON_PATH.exists() or not HTML_PATH.exists():
        raise SystemExit("path optimization JSON or HTML report is missing")
    report = json.loads(JSON_PATH.read_text(encoding="utf-8"))
    valid_statuses = {"ACCEPTED", "ACCEPTED_WITH_WARNINGS", "NO_MEANINGFUL_IMPROVEMENT", "REJECTED_SAFETY_REGRESSION", "FAILED"}
    if report.get("optimization_status") not in valid_statuses:
        raise SystemExit("invalid optimization_status")
    if not report.get("baseline_metrics") or not report.get("optimized_metrics"):
        raise SystemExit("report is missing baseline or optimized metrics")
    text = HTML_PATH.read_text(encoding="utf-8").lower()
    missing = [token for token in TOKENS if token not in text]
    if missing:
        raise SystemExit("optimization HTML missing tokens: " + ", ".join(missing))
    for path in (JSON_PATH, HTML_PATH):
        ignored = subprocess.run(["git", "check-ignore", "-v", str(path.relative_to(WORKSPACE_ROOT))], cwd=WORKSPACE_ROOT)
        if ignored.returncode:
            raise SystemExit(f"generated report is not ignored: {path}")
    print("PASS stage4 path optimization report")
    print("AI car path optimization report check OK")


if __name__ == "__main__":
    main()
