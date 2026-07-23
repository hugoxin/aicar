from __future__ import annotations

import html
import json
from typing import Any


def build_geometry_pose_report(comparison: dict[str, Any]) -> str:
    rows = []
    for item in comparison["source_results"]:
        summary = item["summary"]
        rows.append(
            "<tr>"
            f"<td>{html.escape(item['geometry_source_type'])}</td>"
            f"<td>{html.escape(str(item.get('input_file') or 'analytic'))}</td>"
            f"<td>{summary['patch_count']}</td>"
            f"<td>{summary['mapped_path_point_count']}</td>"
            f"<td>{summary['mean_mapping_distance_mm']:.3f}</td>"
            f"<td>{summary['machine_path_length_mm']:.3f}</td>"
            f"<td>{summary['minimum_clearance_mm']:.3f}</td>"
            f"<td>{summary['violation_count']}</td>"
            f"<td>{html.escape(item['status'])}</td>"
            "</tr>"
        )
    details = []
    for item in comparison["source_results"]:
        details.append(
            f"<details><summary>{html.escape(item['name'])}: geometry, normal, pose and safety data</summary>"
            f"<h3>Bounding box and dimensions</h3><pre>{html.escape(json.dumps({'bbox': item.get('bbox'), 'dimension_mismatch': item.get('dimension_mismatch')}, indent=2))}</pre>"
            f"<h3>Normal source statistics and confidence</h3><pre>{html.escape(json.dumps(item.get('normal_summary', {}), indent=2))}</pre>"
            f"<h3>Nozzle pose, standoff, incidence, orientation and quaternion continuity</h3><pre>{html.escape(json.dumps(item.get('pose_summary', {}), indent=2))}</pre>"
            f"<h3>Path mapping, motion, collision, interlock and safe-stop</h3><pre>{html.escape(json.dumps(item.get('summary', {}), indent=2))}</pre></details>"
        )
    warnings = "".join(f"<li>{html.escape(str(item))}</li>" for item in comparison.get("warnings", []))
    violations = "".join(f"<li>{html.escape(str(item))}</li>" for item in comparison.get("violations", [])) or "<li>None</li>"
    limitations = "".join(f"<li>{html.escape(str(item))}</li>" for item in comparison.get("limitations", []))
    payload = html.escape(json.dumps(comparison.get("dimension_comparison", {}), ensure_ascii=False, indent=2))
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><title>Stage4.6 Geometry and Pose Report</title>
<style>body{{font:15px/1.5 Arial,sans-serif;margin:32px;color:#17202a}}table{{border-collapse:collapse;width:100%}}th,td{{border:1px solid #adb5bd;padding:8px;text-align:left}}th{{background:#e9ecef}}.status{{font-size:24px;font-weight:700}}pre{{background:#f6f8fa;padding:16px;overflow:auto}}.boundary{{border-left:5px solid #d97706;padding:12px;background:#fff7ed}}</style></head>
<body><h1>Stage4.6 Geometry and Nozzle Pose Interface</h1><p class="status">{html.escape(comparison['status'])}</p>
<h2>Geometry source comparison</h2><table><thead><tr><th>Source</th><th>Input</th><th>Patches</th><th>Mapped points</th><th>Mean map mm</th><th>Machine path mm</th><th>Clearance mm</th><th>Violations</th><th>Status</th></tr></thead><tbody>{''.join(rows)}</tbody></table>
<h2>Dimension replacement</h2><pre>{payload}</pre>
<h2>Source detail</h2>{''.join(details)}
<h2>Normals and poses</h2><p>Normals are input or locally estimated, oriented outward, then used to build candidate nozzle frames and normalized quaternions. Local -Z points toward the surface.</p>
<h2>Motion and safety</h2><p>The mapped path is re-time-parameterized and passed through workspace, velocity, acceleration, collision, forbidden-zone, resource-lock interlock, schedule, and safe-stop checks.</p>
<h2>Warnings</h2><ul>{warnings}</ul>
<h2>Violations</h2><ul>{violations}</ul>
<h2>Limitations</h2><ul>{limitations}</ul>
<div class="boundary"><strong>Boundary:</strong> fixtures are generated from the analytic reference. They are not real CAD or point-cloud scans. OBJ/STL/PLY validate offline interfaces only. Poses are not robot inverse-kinematics results and cannot control hardware.</div>
</body></html>"""
