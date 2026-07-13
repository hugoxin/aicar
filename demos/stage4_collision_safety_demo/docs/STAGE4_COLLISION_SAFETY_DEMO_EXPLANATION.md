# Stage4.3 Collision Safety Demo Explanation

Demo 从阶段4.2候选机械路径开始，加载参考洗车房安全布局与三执行机构模型，执行任务分配、扫掠 AABB 生成、碰撞与安全距离检查、共享空间互锁调度、安全停机点选择，并输出 JSON 与单文件 HTML。

报告中的 `PASS_WITH_WARNINGS` 表示当前参考数据没有关键 violation，但仍存在几何近似、通用执行机构参数、同步退化或互锁等待等限制。它不等于真实设备碰撞验证，不可直接下发 PLC、伺服或机器人控制器。
