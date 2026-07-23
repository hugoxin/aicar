import argparse
import json
import shutil
import sys
import webbrowser
from pathlib import Path

DEMO_ROOT = Path(__file__).resolve().parents[1]
WORKSPACE_ROOT = DEMO_ROOT.parents[1]
PROJECT_ROOT = WORKSPACE_ROOT / "aicar_sim"
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from aicar_sim.geometry_demo_runner import run_all, run_source, write_pipeline_outputs  # noqa: E402
from aicar_sim.geometry_pose_report import build_geometry_pose_report  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", choices=["analytic", "obj", "stl", "ply", "xyz", "csv", "all"], default="all")
    parser.add_argument("--open-report", action="store_true")
    args = parser.parse_args()
    if args.source == "all":
        results, comparison = run_all()
    else:
        result = run_source(args.source)
        results = {args.source: result}
        geometry = result["geometry"]
        comparison = {
            "report_version": "stage4.6",
            "status": result["validation"]["status"],
            "source_results": [{
                "name": args.source,
                "geometry_source_type": geometry["geometry_source_type"],
                "input_file": geometry.get("source_metadata", {}).get("source_path"),
                "summary": result["validation"]["summary"],
                "status": result["validation"]["status"],
            }],
            "dimension_comparison": {"reference_real_size_dimensions": result["pose_plan"]["dimension_profile"]["dimensions"]},
            "warnings": result["validation"]["warnings"],
            "violations": result["validation"]["violations"],
            "limitations": result["validation"]["limitations"],
        }
    write_pipeline_outputs(results, comparison)
    json_dir = DEMO_ROOT / "demo_outputs/json"
    report_dir = DEMO_ROOT / "demo_outputs/reports"
    json_dir.mkdir(parents=True, exist_ok=True)
    report_dir.mkdir(parents=True, exist_ok=True)
    source_report = PROJECT_ROOT / "outputs/geometry_validation/geometry_pose_validation_report.json"
    if not source_report.exists():
        source_report.write_text(json.dumps(comparison, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    shutil.copy2(source_report, json_dir / "geometry_pose_validation_report.json")
    html_path = report_dir / "stage4_geometry_pose_report.html"
    html_path.write_text(build_geometry_pose_report(comparison), encoding="utf-8")
    print(f"source mode: {args.source}")
    print(f"status: {comparison['status']}")
    print(f"report: {html_path}")
    if args.open_report:
        print(f"open report requested: {html_path.resolve().as_uri()}")
        webbrowser.open(html_path.resolve().as_uri())


if __name__ == "__main__":
    main()
