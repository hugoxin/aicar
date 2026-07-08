# Stage3 2D Visual Demo

这是阶段3.1的 2D 可视化 Demo，用于把阶段2仿真结果以图形方式展示出来。

展示内容：

- 洗车房俯视图
- 车辆 `bounding_box`
- `safe_envelope`
- `surface_zones`
- `abstract nozzle path segments`
- `coverage report`
- `wash flow timeline`

运行方式：

```powershell
Set-Location F:\aicar\demos\stage3_2d_visual_demo
python scripts\check_stage3_2d_visual_demo.py
python scripts\run_stage3_2d_visual_demo.py --open-report
```

当前不是 3D，不是动画，不是 PLC，不是硬件控制。
