import json
import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
WORKSPACE_ROOT = PROJECT_ROOT.parent
JSON_PATH = PROJECT_ROOT / "outputs/collision_safety/collision_safety_validation_report.json"
HTML_PATH = PROJECT_ROOT / "outputs/collision_safety/stage4_collision_safety_report.html"
TOKENS = ["stage4", "collision", "safety", "static obstacle", "forbidden zone", "slow zone", "shared interlock", "safe stop", "multi actuator", "limitations"]


def main() -> None:
    completed = subprocess.run([sys.executable, str(PROJECT_ROOT / "scripts/generate_collision_safety_report.py")], cwd=WORKSPACE_ROOT)
    if completed.returncode:
        raise SystemExit(completed.returncode)
    if not JSON_PATH.exists() or not HTML_PATH.exists():
        raise SystemExit("collision safety validation JSON or HTML is missing")
    report = json.loads(JSON_PATH.read_text(encoding="utf-8"))
    if report.get("validation_status") not in {"PASS", "PASS_WITH_WARNINGS", "FAIL"}:
        raise SystemExit("invalid collision safety validation_status")
    for key in ("violation_count", "warning_count"):
        if key not in report.get("summary", {}):
            raise SystemExit(f"validation report missing {key}")
    html_text = HTML_PATH.read_text(encoding="utf-8").lower()
    missing = [token for token in TOKENS if token not in html_text]
    if missing:
        raise SystemExit("collision safety HTML missing tokens: " + ", ".join(missing))
    for path in (JSON_PATH, HTML_PATH):
        ignored = subprocess.run(["git", "check-ignore", "-v", str(path.relative_to(WORKSPACE_ROOT))], cwd=WORKSPACE_ROOT)
        if ignored.returncode:
            raise SystemExit(f"generated output is not ignored: {path}")
    print("PASS stage4 collision safety validation")
    print("AI car collision safety validation check OK")


if __name__ == "__main__":
    main()
