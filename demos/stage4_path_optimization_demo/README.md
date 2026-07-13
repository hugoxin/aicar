# Stage4 Path Optimization Demo

本 Demo 展示阶段4.4安全优先的启发式路径与周期优化，包括冗余轨迹点清理、transition候选验证、局部调度比较、安全复验和目标达成情况。

```powershell
Set-Location F:\aicar\demos\stage4_path_optimization_demo
python scripts\check_stage4_path_optimization_demo.py
python scripts\run_stage4_path_optimization_demo.py
python scripts\run_stage4_path_optimization_demo.py --open-report
```

输出位于 `demo_outputs\json` 和 `demo_outputs\reports`，是可重建运行产物，不提交 Git。

当前不保证全局最优，使用通用执行机构和AABB/车辆包络近似，不连接PLC，不控制真实硬件，不能替代真实设备验证。
