# Stage4 Collision Safety Demo

本 Demo 展示阶段4.3的碰撞和安全约束仿真：静态障碍 AABB、车辆安全包络、禁入/减速/共享互锁区、三执行机构任务分配、资源锁、冲突消解和安全停机点。

```powershell
Set-Location F:\aicar\demos\stage4_collision_safety_demo
python scripts\check_stage4_collision_safety_demo.py
python scripts\run_stage4_collision_safety_demo.py
python scripts\run_stage4_collision_safety_demo.py --open-report
```

输出位于 `demo_outputs\json` 和 `demo_outputs\reports`，均为可重建运行产物，不提交 Git。

当前使用通用多执行机构参考模型和保守 AABB 近似，不是 PLC 程序，不控制真实硬件，不能替代设备安全认证。
