import json
import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
WORKSPACE_ROOT = PROJECT_ROOT.parent
JSON_OUTPUT = PROJECT_ROOT / "outputs/continuous_surface_validation/continuous_surface_comparison_report.json"
HTML_OUTPUT = PROJECT_ROOT / "outputs/continuous_surface_validation/stage4_continuous_surface_path_report.html"


def main() -> None:
    if not JSON_OUTPUT.exists() or not HTML_OUTPUT.exists():
        completed = subprocess.run([sys.executable, str(PROJECT_ROOT / "scripts/generate_continuous_surface_report.py")], cwd=WORKSPACE_ROOT)
        if completed.returncode:
            raise SystemExit(completed.returncode)
    report = json.loads(JSON_OUTPUT.read_text(encoding="utf-8"))
    if report["reconstruction_status"] not in {"ACCEPTED", "ACCEPTED_WITH_WARNINGS", "NO_MEANINGFUL_IMPROVEMENT", "REJECTED_SAFETY_REGRESSION", "FAILED"}:
        raise SystemExit("invalid reconstruction_status")
    html_text = HTML_OUTPUT.read_text(encoding="utf-8").lower()
    missing = [term for term in ("stage4.5", "continuous surface", "coverage", "scan pass", "transition", "motion", "collision", "interlock", "safety", "limitations") if term not in html_text]
    if missing:
        raise SystemExit("continuous surface report missing terms: " + ", ".join(missing))
    for path in (JSON_OUTPUT, HTML_OUTPUT):
        relative = str(path.relative_to(WORKSPACE_ROOT))
        if subprocess.run(["git", "check-ignore", "-q", relative], cwd=WORKSPACE_ROOT).returncode:
            raise SystemExit(f"generated report is not ignored: {relative}")
    print("PASS stage4 continuous surface report")
    print("AI car continuous surface report check OK")


if __name__ == "__main__":
    main()
