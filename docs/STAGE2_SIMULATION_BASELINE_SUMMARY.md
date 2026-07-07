# Stage2 Simulation Baseline Summary

## 1. 阶段2冻结版本说明

- tag: `stage2-simulation-baseline`
- 阶段2定位：AI智能无人洗车仿真主链路。
- 当前仍然不是硬件控制，不是 PLC，不是真实轨迹。

阶段2的核心目标，是把阶段1输出的车型识别结果接入无人洗车仿真链路，并生成一套从策略到报告的可检查 JSON 与 HTML 展示结果。

## 2. 阶段2完成内容

- Stage2.1 Wash Strategy Plan：根据车型和 `wash_profile` 生成洗车策略计划。
- Stage2.2 Vehicle Envelope and Wash Bay：建立车辆包络、洗车空间和静态区域模型。
- Stage2.3 Nozzle Model and Coverage：建立喷嘴配置和区域覆盖参数映射。
- Stage2.4 Wash Flow State Machine：生成洗车流程状态机和 timeline。
- Stage2.5 Abstract Nozzle Path Plan：生成车辆坐标系下的抽象喷嘴路径点。
- Stage2.6 Coverage Report：基于抽象路径和覆盖目标生成覆盖率检查报告。
- Stage2.D Pipeline Visual Demo：生成阶段2完整链路 HTML 展示报告。

## 3. 当前完整链路

```text
vehicle_type_result.json
  -> wash_strategy_plan.json
  -> space_model_report.json
  -> nozzle_coverage_plan.json
  -> wash_flow_run.json
  -> abstract_nozzle_path_plan.json
  -> coverage_report.json
  -> stage2_pipeline_report.html
```

## 4. 当前 Demo 输出摘要

- vehicle_type: `sedan`
- wash_profile: `standard_sedan`
- estimated_total_seconds: `141`
- segment_count: `22`
- point_count: `112`
- estimated_actual_coverage_percent: `92`
- coverage_pass: `true`

## 5. 当前能力边界

当前能做：

- 策略级仿真。
- 空间级建模。
- 喷嘴配置映射。
- 流程状态机。
- 抽象路径点。
- 覆盖率报告。
- HTML 展示。

但当前不能代表：

- 真实清洗效果。
- 流体仿真。
- 机械轨迹。
- PLC 控制。
- 硬件联调。

## 6. 后续阶段建议

- 阶段3：简单可视化/2D动画。
- 阶段4：真实路径规划与运动约束。
- 阶段5：PLC/硬件联调。
- 阶段6：商业化后台和设备管理。
