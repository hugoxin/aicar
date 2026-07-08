import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
WORKSPACE_ROOT = PROJECT_ROOT.parent
REPORT_PATH = PROJECT_ROOT / "outputs" / "visualization_2d" / "stage3_2d_visual_report.html"
REQUIRED_PATHS = [
    PROJECT_ROOT / "src" / "aicar_sim" / "visualization_2d.py",
    PROJECT_ROOT / "scripts" / "generate_2d_visualization_report.py",
    PROJECT_ROOT / "schemas" / "visualization_2d_report.schema.json",
]
REQUIRED_HTML_TOKENS = [
    "Stage3.1",
    "SVG",
    "vehicle_type",
    "wash_profile",
    "coverage_pass",
    "limitations",
]


def run_generator() -> None:
    command = [
        sys.executable,
        str(PROJECT_ROOT / "scripts" / "generate_2d_visualization_report.py"),
    ]
    completed = subprocess.run(
        command,
        cwd=str(WORKSPACE_ROOT),
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        print(completed.stdout)
        print(completed.stderr, file=sys.stderr)
        raise SystemExit(completed.returncode)


def assert_git_ignored(path: Path) -> None:
    relative = path.relative_to(WORKSPACE_ROOT)
    completed = subprocess.run(
        ["git", "check-ignore", "-v", str(relative)],
        cwd=str(WORKSPACE_ROOT),
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        raise SystemExit(f"output HTML is not ignored by .gitignore: {relative}")


def main() -> None:
    missing = [path for path in REQUIRED_PATHS if not path.exists()]
    if missing:
        print("Missing Stage3.1 visualization files:")
        for path in missing:
            print(f"- {path}")
        raise SystemExit(1)

    run_generator()
    if not REPORT_PATH.exists():
        raise SystemExit(f"missing generated HTML: {REPORT_PATH}")

    html_text = REPORT_PATH.read_text(encoding="utf-8")
    missing_tokens = [token for token in REQUIRED_HTML_TOKENS if token not in html_text]
    if missing_tokens:
        raise SystemExit(f"generated HTML missing tokens: {', '.join(missing_tokens)}")

    assert_git_ignored(REPORT_PATH)

    print("PASS stage3 2D visualization report")
    print("AI car 2D visualization check OK")


if __name__ == "__main__":
    main()
