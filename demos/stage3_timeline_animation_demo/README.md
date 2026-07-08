# Stage3 Timeline Animation Demo

这是阶段3.2的简单时间轴动画 Demo，用于把阶段2仿真结果按洗车流程顺序动态展示出来。

展示内容：

- 洗车房 2D 俯视图
- 车辆 `bounding_box`
- `safe_envelope`
- 当前状态高亮
- 当前清洗区域高亮
- 当前喷嘴路径高亮
- 时间轴播放
- `coverage report`

运行方式：

```powershell
Set-Location F:\aicar\demos\stage3_timeline_animation_demo
python scripts\check_stage3_timeline_animation_demo.py
python scripts\run_stage3_timeline_animation_demo.py --open-report
```

当前不是 3D，不是复杂动画引擎，不是 PLC，不是硬件控制。
