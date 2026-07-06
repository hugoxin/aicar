# 阶段2.1：洗车策略配置与车辆数字模型接入

阶段2.1 的目标是打通策略层基础闭环：

```text
vehicle_type_result.json
  -> aicar_sim 解析 vehicle_type
  -> 读取车辆数字模型
  -> 读取 wash_profile 配置
  -> 生成 wash_strategy_plan.json
```

本阶段不是路径规划，不生成喷嘴轨迹，不做动画，不做 PLC，也不连接真实硬件。

## 输入

输入来自阶段1车辆识别小闭环：

```text
vehicle_type_lab\outputs\predictions\vehicle_type_result.json
```

`aicar_sim` 通过 `vehicle_type_input.py` 读取该 JSON，并解析到：

```text
aicar_sim\data\vehicles\sedan.json
aicar_sim\data\vehicles\suv.json
aicar_sim\data\vehicles\mpv.json
```

如果 `vehicle_type=unknown` 或 `vehicle_detected=false`，当前沿用阶段1.9逻辑回退到 `suv.json`。

## wash_profile

车辆模型中的 `wash_profile` 字段用于选择洗车策略配置：

```text
aicar_sim\data\wash_profiles\standard_sedan.json
aicar_sim\data\wash_profiles\standard_suv.json
aicar_sim\data\wash_profiles\standard_mpv.json
```

`wash_profile` 定义安全距离、顶部/侧面/前后清洗间距、龙门速度、喷嘴移动速度，以及泡沫、停留、冲洗、风干、轮毂重点清洗等时间参数。

这些参数是阶段2.1 demo 参数，不代表真实设备最终参数。

## 输出

阶段2.1 输出：

```text
aicar_sim\outputs\wash_strategy\wash_strategy_plan.json
```

该文件包含：

- `plan_version`
- `vehicle`
- `profile`
- `strategy_summary`
- `stages`
- `limitations`

`estimated_total_seconds` 由所有 stage 的 `duration_seconds` 自动求和。

## 当前限制

- 不生成车辆包络模型。
- 不生成洗车空间模型。
- 不生成喷嘴路径。
- 不控制 PLC。
- 不连接真实硬件。

## 后续阶段

- 阶段2.2：建立车辆包络模型和洗车空间模型。
- 阶段2.3：建立喷嘴模型。
- 阶段2.5：进入路径规划。

## 验收命令

```powershell
python aicar_sim\scripts\check_wash_profile_selection.py
python aicar_sim\scripts\check_wash_strategy_plan.py
python aicar_sim\scripts\generate_wash_strategy_plan.py --vehicle-type-result vehicle_type_lab\outputs\predictions\vehicle_type_result.json
```

