# aicar_sim

`aicar_sim` 是 AI 智能无人洗车项目的主仿真框架。

当前目标：

- 预留洗车房配置、车辆尺寸配置和基础洗车 recipe。
- 预留车辆模型、路径规划、洗车状态机、喷嘴控制、VirtualPLC、安全监控和可视化模块。
- 提供最小可运行入口，确认 scaffold 正常。

当前阶段不实现复杂算法，不训练模型，不连接真实硬件。

当前已建立 `vehicle_type_lab` -> `aicar_sim` 的 JSON 接口。`aicar_sim` 通过 `src\aicar_sim\vehicle_type_input.py` 读取：

```text
vehicle_type_lab\outputs\predictions\vehicle_type_result.json
```

然后根据 `vehicle_type` 解析到 `data\vehicles\sedan.json`、`data\vehicles\suv.json` 或 `data\vehicles\mpv.json`。如果结果为 `unknown` 或未检测到车辆，当前默认回退到 `suv.json`。

阶段 1.9 中，`aicar_sim` 会进一步加载对应车辆模型 JSON，输出 mock 车辆尺寸和 `wash_profile`。这些参数只用于当前车辆模型选择闭环，不代表真实车辆精确尺寸，也还不是最终洗车路径规划。

阶段 2.1 中，`aicar_sim` 会读取车辆模型中的 `wash_profile`，加载 `data\wash_profiles` 下对应配置，并生成策略层输出：

```text
aicar_sim\outputs\wash_strategy\wash_strategy_plan.json
```

该计划只描述预冲洗、泡沫、停留、车顶清洗、侧面清洗、轮毂重点清洗和风干等阶段参数。不生成喷嘴路径，不控制 PLC，也不连接真实硬件。

阶段 2.2 中，`aicar_sim` 会基于车辆模型、wash profile、wash strategy plan 和 `data\wash_bays\demo_wash_bay.json` 生成静态空间模型：

```text
aicar_sim\outputs\space_model\space_model_report.json
```

该报告描述车辆 `bounding_box`、`safe_envelope`、车顶/侧面/前后/轮毂区域，以及车辆安全包络是否能放入 demo 洗车房。不生成喷嘴路径，不做动画，不控制 PLC，也不连接真实硬件。

阶段 2.3 中，`aicar_sim` 会基于 `space_model_report.json` 的 surface zones、`data\nozzles\demo_nozzle_catalog.json` 和 `demo_nozzle_zone_mapping.json` 生成喷嘴覆盖参数计划：

```text
aicar_sim\outputs\nozzle_plan\nozzle_coverage_plan.json
```

该计划说明每个区域使用哪些 demo 喷嘴、目标覆盖率、建议距离、有效宽度和 pass 数提示。不生成真实喷嘴路径，不做动画，不控制 PLC，也不连接真实硬件。

阶段 2.4 中，`aicar_sim` 会基于 wash strategy、space model 和 nozzle coverage plan 生成洗车流程状态机运行结果：

```text
aicar_sim\outputs\wash_flow\wash_flow_run.json
```

该结果包含 `idle`、`load_vehicle_context`、`pre_rinse`、`foam`、`dwell`、`top_clean`、`side_clean`、`wheel_clean`、`air_dry` 和 `completed` 主流程，同时保留 `aborted` 与 `error` 终止状态。它只描述状态级 timeline 和喷嘴分配，不生成真实喷嘴路径，不做动画，不控制 PLC，也不连接真实硬件。

阶段 2.5 中，`aicar_sim` 会基于 wash flow、space model 和 nozzle coverage plan 生成抽象喷嘴路径点：

```text
aicar_sim\outputs\path_plan\abstract_nozzle_path_plan.json
```

该结果只描述车辆坐标系下的参考点、path segment、喷嘴和区域对应关系。它不是电机坐标，不是 PLC 指令，不生成真实硬件路径规划，也不做动画。

阶段 2.6 中，`aicar_sim` 会基于 abstract path plan、nozzle coverage plan 和 space model 生成抽象覆盖率报告：

```text
aicar_sim\outputs\coverage_report\coverage_report.json
```

该报告统计每个 zone 的 segment、point、目标覆盖率和估算覆盖率。它不是流体仿真，不代表真实清洗效果，不控制 PLC，也不连接真实硬件。

运行 scaffold：

```powershell
python aicar_sim\src\aicar_sim\main.py
```

读取车辆类型结果：

```powershell
python aicar_sim\src\aicar_sim\main.py --vehicle-type-result vehicle_type_lab\outputs\predictions\vehicle_type_result.json
```

检查车辆类型输入：

```powershell
python aicar_sim\scripts\check_vehicle_type_input.py
```

检查车辆模型选择：

```powershell
python aicar_sim\scripts\check_vehicle_model_selection.py
python aicar_sim\scripts\check_all_vehicle_model_selection.py
```

生成阶段2.1洗车策略计划：

```powershell
python aicar_sim\scripts\check_wash_profile_selection.py
python aicar_sim\scripts\check_wash_strategy_plan.py
python aicar_sim\scripts\generate_wash_strategy_plan.py --vehicle-type-result vehicle_type_lab\outputs\predictions\vehicle_type_result.json
```

生成阶段2.2空间模型报告：

```powershell
python aicar_sim\scripts\check_vehicle_envelope.py
python aicar_sim\scripts\check_wash_bay.py
python aicar_sim\scripts\check_space_model.py
python aicar_sim\scripts\generate_space_model.py --vehicle-type-result vehicle_type_lab\outputs\predictions\vehicle_type_result.json
```

生成阶段2.3喷嘴覆盖参数计划：

```powershell
python aicar_sim\scripts\check_nozzle_catalog.py
python aicar_sim\scripts\check_nozzle_zone_mapping.py
python aicar_sim\scripts\check_nozzle_coverage_plan.py
python aicar_sim\scripts\generate_nozzle_coverage_plan.py --vehicle-type-result vehicle_type_lab\outputs\predictions\vehicle_type_result.json
```

生成阶段2.4洗车流程状态机运行结果：

```powershell
python aicar_sim\scripts\check_wash_flow_config.py
python aicar_sim\scripts\check_wash_state_machine.py
python aicar_sim\scripts\check_wash_flow_run.py
python aicar_sim\scripts\generate_wash_flow_run.py --vehicle-type-result vehicle_type_lab\outputs\predictions\vehicle_type_result.json
```

生成阶段2.5抽象喷嘴路径点：

```powershell
python aicar_sim\scripts\check_abstract_path.py
python aicar_sim\scripts\check_path_plan.py
python aicar_sim\scripts\generate_abstract_nozzle_path_plan.py --vehicle-type-result vehicle_type_lab\outputs\predictions\vehicle_type_result.json
```

生成阶段2.6抽象覆盖率报告：

```powershell
python aicar_sim\scripts\check_coverage_report.py
python aicar_sim\scripts\generate_coverage_report.py --vehicle-type-result vehicle_type_lab\outputs\predictions\vehicle_type_result.json
```
