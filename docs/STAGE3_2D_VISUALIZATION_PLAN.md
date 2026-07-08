# Stage3 2D Visualization Plan

## 1. 阶段3.1定位

阶段3.1只做阶段2结果的 2D 可视化展示。它不是新算法，不是 3D，不是动画引擎，不是真实路径规划，不是 PLC，也不控制硬件。

## 2. 为什么阶段3先做2D可视化

阶段2已经生成了完整仿真链路 JSON，但纯 JSON 不直观。2D 可视化能快速展示车辆包络、洗车房空间、抽象喷嘴路径、覆盖率和流程时间线，帮助项目组在进入更复杂动画或真实路径规划前先检查数据是否一致。

## 3. 输入 JSON

阶段3.1读取以下阶段2输出：

- `aicar_sim\outputs\wash_strategy\wash_strategy_plan.json`
- `aicar_sim\outputs\space_model\space_model_report.json`
- `aicar_sim\outputs\nozzle_plan\nozzle_coverage_plan.json`
- `aicar_sim\outputs\wash_flow\wash_flow_run.json`
- `aicar_sim\outputs\path_plan\abstract_nozzle_path_plan.json`
- `aicar_sim\outputs\coverage_report\coverage_report.json`

如果这些 JSON 不存在，生成脚本会调用阶段2生成脚本补齐。

## 4. 俯视图展示什么

俯视图使用 SVG 展示洗车房边界、车辆 `bounding_box`、`safe_envelope`、车顶/左右侧/前后/轮毂区域，以及抽象喷嘴 path segment 的平面投影。

## 5. 侧视图展示什么

侧视图使用 SVG 展示车辆高度、安全包络高度和喷嘴路径点高度，用于检查 z 方向的参考关系。

## 6. 覆盖率表展示什么

覆盖率表展示每个 `zone_id` 的目标覆盖率、估算覆盖率、segment 数、point 数和是否通过。

## 7. 流程时间线展示什么

流程时间线展示 `wash_flow_run.timeline` 中的 `state_id`、显示名称、持续时间、起止时间和分配喷嘴。

## 8. 当前不是真实路径规划

阶段3.1只显示阶段2抽象路径点。它不是电机轨迹，不包含速度规划、加速度约束、碰撞检测或机构逆解。

## 9. 当前不是动画引擎

当前报告是静态 HTML 和 SVG，不包含时间轴动画和交互播放。

## 10. 当前不是 PLC 或硬件控制

报告中的喷嘴、流程和路径只是仿真数据展示，不会连接 PLC，也不会控制任何真实设备。

## 11. 后续阶段

后续阶段3.2可以进入简单时间轴动画 Demo，在不接硬件的前提下把 path segment 按流程顺序做成可播放展示。
