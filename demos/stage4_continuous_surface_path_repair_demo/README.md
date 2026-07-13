# Stage4.5-R Continuous Surface Path Repair Demo

This demo rebuilds the Stage4.5-R state-aware continuous-surface candidate path, validates it with the frozen Stage4 motion and safety pipeline, and exports a local single-file HTML report.

Run from this directory:

```powershell
python scripts\check_stage4_continuous_surface_path_repair_demo.py
python scripts\run_stage4_continuous_surface_path_repair_demo.py
python scripts\run_stage4_continuous_surface_path_repair_demo.py --open-report
```

Generated JSON files are copied to `demo_outputs/json`. The HTML report is copied to `demo_outputs/reports`. Generated files are ignored by Git; `.gitkeep` files preserve the folders.

This is an offline reference-surface path optimization demo. It is not CAD or point-cloud reconstruction, does not measure real cleaning effectiveness, and cannot control PLC, servo, SDK, or real hardware.
