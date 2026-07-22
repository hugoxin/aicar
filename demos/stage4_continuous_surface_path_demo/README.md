# Stage4.5 Continuous Surface Path Demo

This demo rebuilds the source path from a reference analytic sedan surface, generates boustrophedon and wheel-ring scan passes, and re-runs Stage4 motion, collision, interlock, schedule, and safe-stop validation.

```powershell
Set-Location F:\aicar\demos\stage4_continuous_surface_path_demo
python scripts\check_stage4_continuous_surface_path_demo.py
python scripts\run_stage4_continuous_surface_path_demo.py
python scripts\run_stage4_continuous_surface_path_demo.py --open-report
```

The surface is not CAD or point-cloud geometry. Coverage is not actual cleaning effectiveness. The demo does not connect to a PLC, servo, SDK, or real hardware and cannot replace real vehicle or equipment validation.
