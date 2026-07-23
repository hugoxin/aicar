# Stage4.6 Geometry and Nozzle Pose Demo

This offline demo validates the unified analytic, ASCII mesh, and ASCII point-cloud geometry interfaces. It applies the reference dimension profile, maps the frozen Stage4.5-R path, estimates outward normals, builds candidate nozzle poses, and reruns motion and safety checks.

```powershell
python demos\stage4_geometry_pose_demo\scripts\run_stage4_geometry_pose_demo.py --source all
python demos\stage4_geometry_pose_demo\scripts\check_stage4_geometry_pose_demo.py
```

The generated fixtures are derived from the analytic reference. They are not manufacturer CAD or real scans. The pose is not robot inverse kinematics and the demo cannot control hardware.
