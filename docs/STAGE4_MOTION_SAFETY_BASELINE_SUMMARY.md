# Stage4 Motion and Safety Baseline Summary

## 1. 阶段4冻结说明

- 冻结 tag：`stage4-motion-safety-baseline`
- 阶段4定位：将阶段2抽象喷嘴路径推进为通用参考执行机构模型下的机械可行候选轨迹，并完成基础运动约束、碰撞安全、多执行机构调度和安全优先的启发式优化。

当前仍然不是：

- 真实洗车机轨迹
- 真实机械动力学验证
- 真实车身曲面路径
- PLC控制
- 伺服控制
- 真实硬件安全认证
- 可直接下发设备的控制指令

## 2. 阶段4完成内容

### Stage4.1 Motion Constraint Model

完成：

- 通用三轴参考运动模型
- 工作空间
- 轴速度限制
- 轴加速度限制
- 车辆最小安全距离
- 采样间隔
- 坐标系统定义

参考模型：`demo_cartesian_gantry`

工作空间：

- x：`[-1700, 1700] mm`
- y：`[-3800, 3800] mm`
- z：`[300, 2800] mm`

最大速度：

- x：`500 mm/s`
- y：`650 mm/s`
- z：`350 mm/s`

最大加速度：

- x：`350 mm/s²`
- y：`450 mm/s²`
- z：`250 mm/s²`

`minimum_vehicle_clearance_mm`：`250 mm`

### Stage4.2 Machine-Feasible Candidate Path

完成：

- 抽象路径插值
- 路径连续性处理
- transition生成
- 时间参数化
- 工作空间验证
- 速度验证
- 加速度验证
- 安全距离近似验证
- 候选轨迹报告

基线结果：

- `source_segment_count`：22
- `source_point_count`：112
- `trajectory_point_count`：2695
- `transition_segment_count`：21
- `path_length_mm`：361236.112
- `estimated_motion_duration_s`：2872.819
- `validation_status`：`PASS_WITH_WARNINGS`
- `violations`：0

### Stage4.3 Collision Safety and Multi-Actuator Constraints

完成：

- 静态障碍物模型
- forbidden zone
- slow zone
- shared interlock zone
- safe-stop zones
- 车辆安全余量分级
- conservative AABB swept volume
- 静态碰撞检查
- 车辆碰撞检查
- 多执行机构任务分配
- 左右执行机构同步规则
- 共享空间资源锁
- 时间区间冲突检查
- 安全停机点
- 碰撞安全报告

结果：

- `actuator_count`：3
- `task_count`：45
- `assigned_task_count`：45
- `unassigned_task_count`：0
- `swept_volume_count`：2650
- `static_collision_count`：0
- `vehicle_collision_count`：0
- `forbidden_zone_entry_count`：0
- `conflict_count_before_resolution`：33
- `conflict_count_after_resolution`：0
- `unresolved_conflict_count`：0
- `deadlock_warning_count`：0
- `safe_stop_point_count`：3
- `validation_status`：`PASS_WITH_WARNINGS`
- `violations`：0

### Stage4.4 Path and Cycle-Time Optimization

完成：

- 路径质量指标
- 重复点处理
- 共线点简化
- transition分类
- transition优化候选
- clearance-aware优化
- 同state任务顺序局部优化
- earliest feasible start调度
- 局部并行调度
- 共享资源占用优化
- 优化前后对比报告

结果：

- `optimization_status`：`ACCEPTED_WITH_WARNINGS`
- `safety_validation_status`：`PASS_WITH_WARNINGS`
- `violations`：0

| 指标 | 基线 | 优化后 | 变化 |
| --- | ---: | ---: | ---: |
| 轨迹点 | 2695 | 2575 | 减少 4.453% |
| transition | 21 | 21 | 减少 0% |
| 路径长度 | 361236.112 mm | 361236.112 mm | 减少 0% |
| 运动时间 | 2872.819 s | 2870.414 s | 减少 0.084% |
| 调度周期 | 2487.011 s | 2339.304 s | 减少 5.939% |
| 累计任务延迟 | 20365.367 s | 16920.251 s | 减少 16.917% |
| 同步组 | 0 | 0 | 无变化 |

## 3. 当前完整数据链路

```text
abstract_nozzle_path_plan.json
  -> machine_path_plan.json
  -> motion_validation_report.json
  -> collision_safety_plan.json
  -> multi_actuator_schedule.json
  -> collision_safety_validation_report.json
  -> optimized_machine_path_plan.json
  -> optimized_multi_actuator_schedule.json
  -> path_optimization_report.json
  -> Stage4 HTML reports
```

## 4. 阶段4当前能力

- 已完成通用三轴参考模型下的机械可行候选轨迹
- 已完成工作空间、速度、加速度和时间连续性验证
- 已完成静态障碍物和车辆禁入区检查
- 已完成保守AABB扫掠区域近似
- 已完成多执行机构任务分配
- 已完成共享空间互锁和时间冲突消解
- 已完成安全停机点验证
- 已完成安全优先的启发式调度优化
- 可作为后续真实参数替换和硬件联调前置基础

## 5. 阶段4当前边界

- 当前执行机构参数是通用参考值
- 当前车辆几何是bounding box和safe envelope近似
- 当前静态障碍物使用AABB近似
- 当前扫掠体使用conservative AABB近似
- 当前喷嘴距离使用zone reference surface近似
- 当前没有真实车身曲面法向
- 当前没有真实机械动力学
- 当前没有电机、减速器、惯量和负载模型
- 当前没有真实传感器误差模型
- 当前没有车辆停放误差模型
- 当前没有PLC或伺服通信
- 当前不能直接控制真实设备
- 当前不能替代机械安全认证

## 6. 未解决问题

- 路径长度仍约361米
- 原始候选运动周期仍约47.9分钟
- transition仍为21个
- 路径长度没有获得有效缩短
- 左右同步组仍为0
- 2个同步候选被互锁阻断
- `minimum_vehicle_clearance_mm` 仍为250 mm硬下限
- `vehicle_clearance` warnings仍为59
- 调度周期只降低5.939%
- 累计延迟只降低16.917%
- 所有预设优化目标均未达到

优化目标状态：

- 路径长度减少15%：`TARGET_NOT_REACHED`
- 运动时间减少15%：`TARGET_NOT_REACHED`
- 调度周期减少10%：`TARGET_NOT_REACHED`
- transition减少20%：`TARGET_NOT_REACHED`
- 累计延迟减少20%：`TARGET_NOT_REACHED`

这些结果不能表述为“已经完成最优路径规划”。

## 7. 为什么仍然冻结为基线

- 阶段4已建立完整、可重复、可检查的运动与安全验证链路
- 所有安全硬约束均保持
- violations为0
- 任务没有删除
- 冲突全部被明确发现并消解
- 优化目标未达到时系统能够如实输出
- 当前成果可以作为后续连续表面路径重构和真实设备参数替换的基线

冻结的是可重复的参考模型、数据契约、安全检查和验证结果，不是对路径最优性、商业节拍或真实设备安全性的承诺。

## 8. 后续建议

### Stage4.5 Continuous Surface Path Reconstruction

重点：

- 从路径生成源头重新设计连续清洗轨迹
- 车顶连续扫描
- 左右侧面连续扫描
- 前后区域分块连续路径
- 车轮独立局部路径
- 减少区域间跳转
- 减少安全平面往返
- 从源头减少transition
- 使用更真实的车辆曲面或点云模型

### Stage5 Real Parameter Integration

- 替换真实洗车房尺寸
- 替换真实执行机构行程
- 替换真实速度和加速度
- 替换真实喷嘴尺寸
- 加入实际控制周期
- 加入传感器和停车误差

### Stage6 PLC and Hardware Integration

仅在真实参数、安全评审和离线验证完成后进入。
