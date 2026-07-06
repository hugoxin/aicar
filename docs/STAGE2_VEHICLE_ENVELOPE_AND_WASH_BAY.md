# 阶段2.2：车辆包络模型与洗车空间模型

阶段2.2 的目标是建立静态几何基础：

```text
vehicle_type_result.json
  -> vehicle model
  -> wash_strategy_plan.json
  -> vehicle_envelope.json
  -> wash_bay.json
  -> space_model_report.json
```

本阶段不是路径规划，不生成喷嘴轨迹，不做动画，不做 PLC，也不连接真实硬件。

## 为什么要有车辆包络模型

车辆包络模型回答一个基础问题：车辆在洗车房坐标系里占据多大空间。

它把车辆数字模型中的 `length_mm`、`width_mm`、`height_mm` 转换成：

- `bounding_box`：车辆本体几何边界。
- `safe_envelope`：结合 `wash_profile` 清洗安全距离后的扩展边界。
- `surface_zones`：车顶、左右侧、车头、车尾、轮毂等后续清洗目标区域。

## 为什么要有洗车空间模型

洗车空间模型回答另一个基础问题：洗车房可用空间和安全边界在哪里。

`demo_wash_bay.json` 描述：

- 洗车房尺寸。
- 坐标系。
- 车辆停放对齐方式。
- 龙门轨道范围。
- 安全边界。

这些数据给后续喷嘴模型和路径规划提供静态约束。

## 坐标系定义

当前阶段采用毫米为单位：

- `x`：车辆左右方向。
- `y`：车辆前后方向。
- `z`：竖直向上。

车辆包络坐标原点为 `vehicle_center_floor`。洗车房坐标原点为 `bay_center_floor`。

## bounding_box 与 safe_envelope

`bounding_box` 是车辆本体尺寸对应的几何边界。

`safe_envelope` 在 `bounding_box` 基础上加入：

- `side_clearance_mm`
- `front_rear_clearance_mm`
- `top_clearance_mm`

因此 `safe_envelope` 比车辆本体更大，用于做安全空间检查。

## surface_zones 的作用

`surface_zones` 把车辆包络拆成后续清洗区域：

- `roof`
- `left_side`
- `right_side`
- `front`
- `rear`
- `wheels`

轮毂区域当前是 demo 近似区域，不来自真实轮胎检测。

## wash_bay 的作用

`wash_bay` 记录洗车房尺寸、龙门轨道、车辆对齐方式和安全边界。阶段2.2只使用这些参数做静态空间检查。

## clearance_check 的意义

`clearance_check` 比较车辆 `safe_envelope` 和洗车房尺寸，输出：

- `fits_in_bay`
- `x_clearance_each_side_mm`
- `y_clearance_front_rear_mm`
- `z_clearance_top_mm`
- `warnings`

如果任一方向空间不足，`fits_in_bay=false`，并在 `warnings` 中说明原因。

## 当前限制

- 当前不是路径规划。
- 当前不是动画。
- 当前不是 PLC 或硬件控制。
- 当前车辆和洗车房尺寸均为 demo 参数。

## 下一阶段

阶段2.3 可以基于 `surface_zones` 和 `wash_bay` 增加喷嘴模型与喷嘴覆盖参数。阶段2.5 再进入路径规划。

## 验收命令

```powershell
python aicar_sim\scripts\check_vehicle_envelope.py
python aicar_sim\scripts\check_wash_bay.py
python aicar_sim\scripts\check_space_model.py
python aicar_sim\scripts\generate_space_model.py --vehicle-type-result vehicle_type_lab\outputs\predictions\vehicle_type_result.json
```

