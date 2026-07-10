# Stage4 Motion Constraint Demo

这是阶段4运动约束 Demo。它把阶段2抽象喷嘴路径转换为机械可行候选轨迹，并检查工作空间、速度、加速度、连续性、时间戳和安全距离。

当前输出只能称为：

- 机械可行候选轨迹
- machine-feasible candidate path
- 运动约束仿真结果

当前不是 PLC，不控制真实硬件，也不是经过真实设备标定和动力学验证的机械轨迹。

运行方式：

```powershell
Set-Location F:\aicar\demos\stage4_motion_constraint_demo
python scripts\check_stage4_motion_constraint_demo.py
python scripts\run_stage4_motion_constraint_demo.py
python scripts\run_stage4_motion_constraint_demo.py --open-report
```

运行后会复制候选路径 JSON、验证 JSON 和单文件 HTML 报告到 `demo_outputs`。这些运行输出不进入 Git。
