# 阶段2.5：抽象喷嘴路径点生成

阶段2.5 的目标是生成可检查的抽象喷嘴路径点：

```text
wash_flow_run.json
  -> space_model_report.json
  -> nozzle_coverage_plan.json
  -> abstract_nozzle_path_plan.json
```

本阶段不是真实硬件路径规划，不生成电机轨迹，不做动画，不做 PLC，也不连接真实硬件。

## 什么是抽象喷嘴路径点

抽象路径点是车辆坐标系下的参考点，用于描述某个洗车状态中某个喷嘴大致从哪里扫到哪里。它用于检查流程、区域、喷嘴和时间是否能串起来。

当前坐标系沿用阶段2.2：

- `x`：车辆左右方向。
- `y`：车辆前后方向。
- `z`：高度方向。

这些点不是伺服轴坐标，也不是 PLC 指令。

## 与阶段2.2的关系

阶段2.5使用 `space_model_report.json` 中的：

- `bounding_box`
- `safe_envelope`
- `surface_zones`
- `wheels.sub_zones`

车顶、侧面、车头、车尾和轮毂的路径点都来自这些静态区域边界。

## 与阶段2.3的关系

阶段2.5使用 `nozzle_coverage_plan.json` 中每个 zone 的 `assigned_nozzles`，并按洗车状态筛选喷嘴：

- `pre_rinse` 使用 water 类喷嘴。
- `foam` 使用 `foam_nozzle`。
- `top_clean`、`side_clean`、`wheel_clean` 使用 water 类清洗喷嘴。
- `air_dry` 使用 `air_dry_nozzle`。

## 与阶段2.4的关系

阶段2.5遍历 `wash_flow_run.json` 的 timeline。只有 `wash` 和 `dry` 状态会生成路径段：

- `pre_rinse`
- `foam`
- `top_clean`
- `side_clean`
- `wheel_clean`
- `air_dry`

`idle`、`load_vehicle_context`、`dwell` 和 `completed` 不生成喷嘴路径段。

## path_segment 字段

每个 `path_segment` 记录：

- `segment_id`
- `state_id`
- `zone_id`
- `nozzle_id`
- `media_type`
- `path_type`
- `duration_seconds`
- `recommended_distance_mm`
- `points`
- `notes`

`duration_seconds` 是状态时长按本状态内生成的路径段数量做的抽象分配，不代表真实设备运动时间。

## points 字段

每个 point 记录：

- `point_id`
- `x_mm`
- `y_mm`
- `z_mm`
- `speed_mm_s`

当前 `speed_mm_s` 是 demo 速度提示，不是电机控制速度。

## 当前限制

- 不生成真实喷嘴轨迹。
- 不生成动画。
- 不控制 PLC。
- 不连接真实硬件。
- 不处理避障、加减速、插补、机械臂或龙门运动学。

## 后续阶段

阶段2.6可以在抽象路径点基础上做覆盖率检查与报告。也可以单独做阶段2.D可视化 Demo，用于展示车辆区域、喷嘴分配和抽象路径点。

阶段2.6文档见：

```text
docs\STAGE2_COVERAGE_REPORT.md
```

## 验收命令

```powershell
python aicar_sim\scripts\check_abstract_path.py
python aicar_sim\scripts\check_path_plan.py
python aicar_sim\scripts\generate_abstract_nozzle_path_plan.py --vehicle-type-result vehicle_type_lab\outputs\predictions\vehicle_type_result.json
```
