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
