# Stage3 Timeline Animation Plan

## 1. 阶段3.2定位

阶段3.2只做简单时间轴动画 Demo。它基于阶段2 JSON 和阶段3.1的 2D 可视化结果，将洗车流程按时间顺序动态展示出来。

## 2. 为什么在 2D 可视化后增加时间轴动画

阶段3.1已经能静态展示洗车房、车辆包络、安全包络、抽象路径和覆盖率。阶段3.2进一步把 `wash_flow_run.timeline` 接入展示层，让项目组能看到状态从 `idle` 到 `completed` 的变化，以及每个状态对应的区域、喷嘴和路径。

## 3. 输入 JSON

阶段3.2读取以下阶段2输出：

- `aicar_sim\outputs\wash_strategy\wash_strategy_plan.json`
- `aicar_sim\outputs\space_model\space_model_report.json`
- `aicar_sim\outputs\nozzle_plan\nozzle_coverage_plan.json`
- `aicar_sim\outputs\wash_flow\wash_flow_run.json`
- `aicar_sim\outputs\path_plan\abstract_nozzle_path_plan.json`
- `aicar_sim\outputs\coverage_report\coverage_report.json`

如果这些 JSON 不存在，生成脚本会调用阶段2生成脚本补齐。

## 4. 时间轴如何使用 wash_flow_run

HTML 中嵌入 `wash_flow_run.timeline`。原生 JavaScript 根据当前 slider 时间查找当前状态，并同步更新状态面板、状态列表高亮和时间读数。

## 5. 路径高亮如何使用 abstract_nozzle_path_plan

每条 `path_segment` 在 SVG 中以 `data-state-id`、`data-zone-id` 和 `data-nozzle-id` 标记。当前状态变化时，JavaScript 会高亮相同 `state_id` 的路径段。

## 6. 区域覆盖如何使用 coverage_report

覆盖率面板显示每个 zone 的估算覆盖率、是否通过、warning 和改进建议。当前状态变化时，目标 zone 会在 2D 图中高亮。

## 7. 当前不是 3D

阶段3.2仍是 2D 俯视图，不建立 3D 场景。

## 8. 当前不是真实路径规划

当前显示的是阶段2抽象路径点，不是电机轨迹、机构轨迹或真实路径规划。

## 9. 当前不是动画引擎

当前只使用原生 HTML/CSS/JavaScript 和轻量 `requestAnimationFrame`，不引入复杂动画库。

## 10. 当前不是 PLC 或硬件控制

时间轴只是展示层，不会连接 PLC，也不会控制任何真实硬件。

## 11. 后续阶段

后续阶段3.F可以冻结阶段3可视化基线，并建议使用 tag：`stage3-visual-baseline`。
