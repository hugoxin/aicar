# 阶段2.6：抽象路径覆盖率检查与报告

阶段2.6 的目标是基于阶段2.5生成的抽象喷嘴路径点，生成可解释、可检查的覆盖率报告：

```text
abstract_nozzle_path_plan.json
  -> nozzle_coverage_plan.json
  -> space_model_report.json
  -> coverage_report.json
```

本阶段不是动画，不是 PLC，不是硬件控制，也不是真实流体仿真。

## 为什么要做覆盖率报告

阶段2.5已经能生成抽象路径点，但还需要回答这些工程问题：

- 每个清洗区域是否有路径段覆盖。
- 每个区域有多少 segment 和 point。
- 喷嘴覆盖目标是否达标。
- 是否有 zone 缺少喷嘴或缺少路径。
- 整车抽象覆盖率是否达到 demo 阈值。

阶段2.6用报告形式把这些问题固定下来，方便后续可视化、优化和审查。

## 与 path_plan 的关系

`coverage_report.json` 会读取 `abstract_nozzle_path_plan.json` 中的 `path_segments`，按 `zone_id` 统计：

- `segment_count`
- `point_count`

如果某个区域没有 path segment，报告会把该区域标记为未通过。

## 与 nozzle_coverage_plan 的关系

`coverage_report.json` 会读取 `nozzle_coverage_plan.json` 中每个 zone 的：

- `target_coverage_percent`
- `assigned_nozzles`

如果某个区域没有喷嘴，估算覆盖率为 0。如果有喷嘴但没有路径段，则估算覆盖率会低于目标值。

## zone_reports 字段

每个 `zone_report` 包含：

- `zone_id`
- `target_coverage_percent`
- `estimated_coverage_percent`
- `coverage_pass`
- `segment_count`
- `point_count`
- `assigned_nozzles`
- `warnings`

当前 demo 中的区域包括 `roof`、`left_side`、`right_side`、`front`、`rear` 和 `wheels`。

## coverage_pass 判定

当前阶段采用简单规则：

- 每个区域必须有喷嘴。
- 每个区域必须有 path segment。
- 整车 `estimated_actual_coverage_percent` 必须大于等于 90。
- `uncovered_zone_count` 必须为 0。

这些规则只用于阶段2.6的抽象检查，不代表真实清洗效果。

## 当前限制

- 不做真实水流、压力、碰撞或传感器反馈仿真。
- 不代表真实清洗效果。
- 不生成真实硬件路径规划。
- 不做动画。
- 不控制 PLC。
- 不连接真实硬件。

## 后续阶段

下一步可以进入阶段2.D：阶段2完整链路可视化 Demo。也可以进入阶段2.7，生成简单文本或 HTML 报告汇总。

## 验收命令

```powershell
python aicar_sim\scripts\check_coverage_report.py
python aicar_sim\scripts\generate_coverage_report.py --vehicle-type-result vehicle_type_lab\outputs\predictions\vehicle_type_result.json
```
