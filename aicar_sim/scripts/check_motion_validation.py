import json
import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
WORKSPACE_ROOT = PROJECT_ROOT.parent
JSON_PATH = PROJECT_ROOT / "outputs" / "motion_validation" / "motion_validation_report.json"
HTML_PATH = PROJECT_ROOT / "outputs" / "motion_validation" / "stage4_motion_validation_report.html"
VALID_STATUSES = {"PASS", "PASS_WITH_WARNINGS", "FAIL"}
HTML_TOKENS = ["Stage4", "machine-feasible", "validation_status", "workspace", "velocity", "acceleration", "clearance", "Limitations"]


def run_generator() -> None:
    completed = subprocess.run([sys.executable, str(PROJECT_ROOT / "scripts" / "generate_motion_validation_report.py")], cwd=str(WORKSPACE_ROOT), text=True, capture_output=True)
    if completed.returncode != 0:
        print(completed.stdout)
        print(completed.stderr, file=sys.stderr)
        raise SystemExit(completed.returncode)


def assert_git_ignored(path: Path) -> None:
    relative = path.relative_to(WORKSPACE_ROOT)
    completed = subprocess.run(["git", "check-ignore", "-v", str(relative)], cwd=str(WORKSPACE_ROOT), capture_output=True, text=True)
    if completed.returncode != 0:
        raise SystemExit(f"generated output is not ignored: {relative}")


def main() -> None:
    run_generator()
    if not JSON_PATH.exists() or not HTML_PATH.exists():
        raise SystemExit("motion validation JSON or HTML output is missing")
    report = json.loads(JSON_PATH.read_text(encoding="utf-8"))
    if report.get("validation_status") not in VALID_STATUSES:
        raise SystemExit(f"invalid validation_status: {report.get('validation_status')}")
    for key in ("violation_count", "warning_count", "violations", "warnings"):
        if key not in report:
            raise SystemExit(f"motion validation report missing {key}")
    html_text = HTML_PATH.read_text(encoding="utf-8")
    missing = [token for token in HTML_TOKENS if token not in html_text]
    if missing:
        raise SystemExit(f"motion validation HTML missing tokens: {', '.join(missing)}")
    assert_git_ignored(JSON_PATH)
    assert_git_ignored(HTML_PATH)
    print("PASS stage4 motion validation")
    print("AI car motion validation check OK")


if __name__ == "__main__":
    main()
