# Wash Profile 配置说明

`wash_profile` 是阶段2.1洗车策略配置文件。它把车辆大类和车辆数字模型连接到抽象洗车流程参数。

配置文件位于：

```text
aicar_sim\data\wash_profiles
```

当前支持：

- `standard_sedan`
- `standard_suv`
- `standard_mpv`

## 字段说明

- `wash_profile`：策略配置名称。
- `description`：简短说明。
- `vehicle_type`：适用车型大类。
- `safe_distance_mm`：抽象安全距离。
- `top_clearance_mm`：顶部清洗保留距离。
- `side_clearance_mm`：侧面清洗保留距离。
- `front_rear_clearance_mm`：前后清洗保留距离。
- `gantry_speed_mm_s`：龙门移动速度 demo 参数。
- `nozzle_travel_speed_mm_s`：喷嘴移动速度 demo 参数。
- `foam_seconds`：泡沫覆盖时长。
- `dwell_seconds`：泡沫停留时长。
- `rinse_seconds`：冲洗总参考时长。
- `dry_seconds`：风干时长。
- `wheel_focus_seconds`：轮毂重点清洗时长。
- `notes`：参数说明。

## 三类差异

`standard_sedan` 的安全距离和清洗时长较短，适合阶段2.1中的普通轿车 demo 模型。

`standard_suv` 的顶部和侧面保留距离更大，泡沫、冲洗、风干时间也略长。

`standard_mpv` 的车身更长更高，因此采用更大的安全距离和更长的清洗、风干时间。

## 注意

当前参数仅用于阶段2.1策略层 demo，不代表真实洗车设备最终参数。后续进入车辆包络、喷嘴模型和路径规划后，需要重新结合机械结构、安全规范和实验结果校准。

