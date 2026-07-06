# 阶段2.3：喷嘴模型与喷嘴覆盖参数

阶段2.3 的目标是建立喷嘴参数层：

```text
space_model_report.json
  -> surface_zones
  -> nozzle_catalog.json
  -> nozzle_zone_mapping.json
  -> nozzle_coverage_plan.json
```

本阶段不是路径规划，不生成喷嘴运动轨迹，不做动画，不做 PLC，也不连接真实硬件。

## 喷嘴模型是什么

喷嘴模型描述“有哪些喷嘴”和“每种喷嘴的基础参数”。当前 demo 包含：

- 顶部高压喷嘴
- 侧面高压喷嘴
- 泡沫喷嘴
- 轮毂重点喷嘴
- 风干喷嘴

每个喷嘴记录喷射介质、压力级别、喷射角、建议距离、有效覆盖宽度、流量和目标区域。

## nozzle_catalog 的作用

`aicar_sim\data\nozzles\demo_nozzle_catalog.json` 是喷嘴参数目录。它不代表真实硬件最终参数，只用于阶段2.3打通参数闭环。

## nozzle_zone_mapping 的作用

`aicar_sim\data\nozzles\demo_nozzle_zone_mapping.json` 把阶段2.2的 surface zones 映射到喷嘴策略。

当前覆盖区域包括：

- `roof`
- `left_side`
- `right_side`
- `front`
- `rear`
- `wheels`

## nozzle_coverage_plan 的作用

`aicar_sim\outputs\nozzle_plan\nozzle_coverage_plan.json` 是阶段2.3运行输出。它把每个 zone 的目标覆盖率、优先级、pass 数提示和喷嘴参数整理成一个可检查计划。

该文件是运行输出，不进入 Git。

## coverage_target_percent

`coverage_target_percent` 表示当前 demo 希望该区域达到的抽象覆盖目标。例如车顶为 95，侧面和前后为 92，轮毂为 90。

这不是实际测量覆盖率，也不是路径规划结果。后续阶段需要结合喷嘴轨迹、速度、重叠率和设备约束重新校准。

## 当前为什么不是路径规划

阶段2.3只回答“哪个区域用哪些喷嘴参数”。它不计算喷嘴从哪里走、走多快、如何避障，也不生成控制指令。

## 当前为什么不是真实硬件参数

当前喷射角、距离、宽度和流量均为 demo 参数，只用于软件链路验证。真实设备需要结合喷嘴型号、泵压、安装角度、实验数据和安全规范确定。

## 后续阶段

- 阶段2.4：洗车流程状态机。
- 阶段2.5：基于车辆包络、洗车空间、喷嘴参数和流程状态进入抽象喷嘴路径点规划。

## 验收命令

```powershell
python aicar_sim\scripts\check_nozzle_catalog.py
python aicar_sim\scripts\check_nozzle_zone_mapping.py
python aicar_sim\scripts\check_nozzle_coverage_plan.py
python aicar_sim\scripts\generate_nozzle_coverage_plan.py --vehicle-type-result vehicle_type_lab\outputs\predictions\vehicle_type_result.json
```

