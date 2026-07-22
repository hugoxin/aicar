import json
import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
WORKSPACE_ROOT = PROJECT_ROOT.parent
JSON_OUTPUT = PROJECT_ROOT / "outputs/continuous_surface_validation_r/continuous_surface_repair_report.json"
HTML_OUTPUT = PROJECT_ROOT / "outputs/continuous_surface_validation_r/stage4_continuous_surface_path_repair_report.html"


def main() -> None:
    if not JSON_OUTPUT.exists() or not HTML_OUTPUT.exists():
        completed = subprocess.run([sys.executable, str(PROJECT_ROOT / "scripts/generate_continuous_surface_report_r.py")], cwd=WORKSPACE_ROOT)
        if completed.returncode:
            raise SystemExit(completed.returncode)
    report = json.loads(JSON_OUTPUT.read_text(encoding="utf-8"))
    valid_statuses = {"ACCEPTED", "ACCEPTED_WITH_WARNINGS", "NO_MEANINGFUL_IMPROVEMENT", "REJECTED_SAFETY_REGRESSION", "FAILED"}
    if report["repair_status"] not in valid_statuses:
        raise SystemExit("invalid Stage4.5-R repair status")
    required_sections = {
        "stage4_baseline_metrics", "stage4_5_first_attempt_metrics", "stage4_5_r_metrics",
        "path_length_breakdown", "state_scan_policies", "aggregation_summary", "connection_summary",
        "schedule_summary", "safety_summary", "coverage_summary", "limitations",
    }
    if not required_sections <= set(report):
        raise SystemExit("repair report JSON is missing required comparison sections")
    html = HTML_OUTPUT.read_text(encoding="utf-8").lower()
    required_terms = (
        "stage4 frozen baseline", "stage4.5 first attempt", "stage4.5-r", "state scan",
        "coverage", "surface task", "direct", "adaptive", "schedule", "collision",
        "interlock", "warning", "violation", "limitations", "cad", "plc",
    )
    missing = [term for term in required_terms if term not in html]
    if missing:
        raise SystemExit("repair HTML is missing terms: " + ", ".join(missing))
    for path in (JSON_OUTPUT, HTML_OUTPUT):
        relative = str(path.relative_to(WORKSPACE_ROOT))
        if subprocess.run(["git", "check-ignore", "-q", relative], cwd=WORKSPACE_ROOT).returncode:
            raise SystemExit(f"generated repair report is not ignored: {relative}")
    print("PASS stage4 continuous surface repair report")
    print("AI car continuous surface repair report check OK")


if __name__ == "__main__":
    main()
