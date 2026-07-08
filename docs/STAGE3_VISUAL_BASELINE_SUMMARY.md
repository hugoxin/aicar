# Stage3 Visual Baseline Summary

## 1. 阶段3冻结版本说明

- tag: `stage3-visual-baseline`
- 阶段3定位：AI智能无人洗车仿真结果可视化展示层。
- 当前仍然不是真实硬件控制，不是 PLC，不是 3D 引擎，不是真实运动轨迹。

阶段3的核心目标，是把阶段2已经生成的策略、空间、喷嘴、流程、抽象路径和覆盖率 JSON，用更直观的 HTML 可视化方式展示出来，方便项目组、客户或合作方理解系统链路。

## 2. 阶段3完成内容

- Stage3.1 2D Visualization Demo：生成静态 2D 俯视图、侧视图、覆盖率表、喷嘴分配表和流程时间线。
- Stage3.2 Timeline Animation Demo：生成轻量时间轴动画，支持 Play、Pause、Reset、slider、当前状态高亮、当前区域高亮和当前抽象路径高亮。

## 3. 当前完整展示链路

```text
vehicle_type_result.json
  -> Stage2 六个仿真 JSON
  -> Stage3.1 2D visual report
  -> Stage3.2 timeline animation report
```

Stage2 六个仿真 JSON 包括：

- `wash_strategy_plan.json`
- `space_model_report.json`
- `nozzle_coverage_plan.json`
- `wash_flow_run.json`
- `abstract_nozzle_path_plan.json`
- `coverage_report.json`

## 4. 当前 Stage3.2 Demo 摘要

- vehicle_type: `sedan`
- wash_profile: `standard_sedan`
- estimated_total_seconds: `141`
- state_count: `10`
- segment_count: `22`
- point_count: `112`
- coverage_pass: `true`

## 5. 当前展示能力

- 能展示洗车房俯视图。
- 能展示车辆 `bounding_box`。
- 能展示 `safe_envelope`。
- 能展示抽象喷嘴路径。
- 能展示覆盖率表。
- 能展示流程时间线。
- 能播放简单时间轴动画。
- 能按状态高亮当前区域和路径。

## 6. 当前边界

- 不是 3D。
- 不是复杂动画引擎。
- 不是真实机械路径。
- 不是真实流体仿真。
- 不是 PLC。
- 不控制硬件。
- 不代表真实清洗效果。

## 7. 后续建议

- 阶段4：真实路径规划与运动约束。
- 阶段5：PLC/硬件联调。
- 阶段6：商业化后台与设备管理。
- 阶段3.3：更精细的前端展示和客户演示页。
