# Stage4.4 Path Optimization Demo Explanation

Demo 从阶段4.2机械候选路径和阶段4.3碰撞安全结果开始，在不删除任务、不改变 wash state 顺序、不降低250 mm硬安全下限的前提下清理冗余点、分析transition并比较多种安全调度候选。

`ACCEPTED_WITH_WARNINGS` 只表示当前参考模型下候选没有安全回归。未达到15%或20%目标的指标会明确显示 `TARGET_NOT_REACHED`，不会伪造改善。报告不是PLC程序，也不是经过真实设备认证的轨迹。
