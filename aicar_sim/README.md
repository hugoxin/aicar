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

阶段 2.F 中，阶段2已形成 simulation baseline。冻结总结见：

```text
docs\STAGE2_SIMULATION_BASELINE_SUMMARY.md
```

阶段 3.1 中，`aicar_sim` 会读取阶段2六个 JSON 输出，并生成静态 2D HTML/SVG 可视化报告：

```text
aicar_sim\outputs\visualization_2d\stage3_2d_visual_report.html
```

报告包含洗车房俯视图、车辆 `bounding_box`、`safe_envelope`、surface zones、抽象喷嘴路径、覆盖率表、喷嘴分配表和流程时间线。该阶段不是 3D，不是动画引擎，不是真实路径规划，不是 PLC，也不连接硬件。

阶段 3.2 中，`aicar_sim` 会读取阶段2六个 JSON 输出，并生成简单时间轴动画 HTML 报告：

```text
aicar_sim\outputs\timeline_animation\stage3_timeline_animation_report.html
```

报告使用原生 HTML/CSS/JavaScript，支持 Play、Pause、Reset、slider、当前状态面板、当前区域高亮和当前抽象路径高亮。该阶段不是 3D，不是复杂动画引擎，不是真实运动控制，不是 PLC，也不连接硬件。

阶段 3.F 中，阶段3已形成 visual baseline。冻结总结见：

```text
docs\STAGE3_VISUAL_BASELINE_SUMMARY.md
```

阶段 3.3 中，`aicar_sim` 会读取阶段1识别结果和阶段2六个 JSON 输出，并生成面向客户/领导/项目组的一页式展示报告：

```text
aicar_sim\outputs\customer_showcase\stage3_customer_showcase_report.html
```

该报告用于说明项目定位、当前能力、完整链路、Demo 数据摘要、阶段进度、业务价值、技术边界和后续路线。它不做新算法、不做 3D、不做 PLC 或硬件控制。

阶段 3.4 中，项目新增 `business_docs\stage3_customer_materials` 客户演示材料包，用于配合 Stage3.3 展示页进行对外沟通。该阶段只整理 Markdown/文本材料，不修改 `aicar_sim` 核心代码。

阶段 4.1 / 4.2 中，`aicar_sim` 使用 `data\motion_models\demo_cartesian_gantry.json` 通用三轴参考模型，把阶段2抽象路径转换为机械可行候选轨迹，并生成：

```text
aicar_sim\outputs\machine_path\machine_path_plan.json
aicar_sim\outputs\motion_validation\motion_validation_report.json
aicar_sim\outputs\motion_validation\stage4_motion_validation_report.html
```

当前检查工作空间、洗车房、速度、加速度、连续性、时间戳和安全距离。车辆安全距离及喷嘴距离使用近似参考面。输出不能直接下发 PLC、伺服或真实设备。

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

生成阶段3.1 2D 可视化报告：

```powershell
python aicar_sim\scripts\check_visualization_2d.py
python aicar_sim\scripts\generate_2d_visualization_report.py --vehicle-type-result vehicle_type_lab\outputs\predictions\vehicle_type_result.json
```

生成阶段3.2时间轴动画报告：

```powershell
python aicar_sim\scripts\check_timeline_animation.py
python aicar_sim\scripts\generate_timeline_animation_report.py --vehicle-type-result vehicle_type_lab\outputs\predictions\vehicle_type_result.json
```

生成阶段3.3客户展示页：

```powershell
python aicar_sim\scripts\check_customer_showcase.py
python aicar_sim\scripts\generate_customer_showcase_report.py --vehicle-type-result vehicle_type_lab\outputs\predictions\vehicle_type_result.json
```

检查阶段3.4客户演示材料：

```powershell
python tools\check_customer_materials.py
```

生成并检查阶段4候选轨迹：

```powershell
python aicar_sim\scripts\check_motion_model.py
python aicar_sim\scripts\generate_machine_path_plan.py
python aicar_sim\scripts\check_machine_path_plan.py
python aicar_sim\scripts\generate_motion_validation_report.py
python aicar_sim\scripts\check_motion_validation.py
```

生成并检查阶段4.3碰撞、安全约束和多执行机构候选调度：

```powershell
python aicar_sim\scripts\check_safety_layout.py
python aicar_sim\scripts\generate_collision_safety_plan.py
python aicar_sim\scripts\check_collision_safety_plan.py
python aicar_sim\scripts\generate_multi_actuator_schedule.py
python aicar_sim\scripts\check_multi_actuator_schedule.py
python aicar_sim\scripts\generate_collision_safety_report.py
python aicar_sim\scripts\check_collision_safety_validation.py
```

输出位于 `outputs\collision_safety` 和 `outputs\multi_actuator_schedule`。当前静态障碍、扫掠体、车辆曲面和三执行机构均使用参考近似；这是安全约束仿真，不是 PLC、伺服或真实硬件控制，也不能替代设备碰撞认证。

生成并检查阶段4.4安全优先路径与周期优化：

```powershell
python aicar_sim\scripts\check_path_optimization_profile.py
python aicar_sim\scripts\generate_optimized_machine_path.py
python aicar_sim\scripts\check_optimized_machine_path.py
python aicar_sim\scripts\generate_optimized_schedule.py
python aicar_sim\scripts\check_optimized_schedule.py
python aicar_sim\scripts\generate_path_optimization_report.py
python aicar_sim\scripts\check_path_optimization_report.py
```

输出位于 `outputs\path_optimization` 和 `outputs\optimized_schedule`。优化保持task集合、wash state顺序、碰撞检查、互锁、安全停机点和250 mm硬下限；报告会如实显示 `NO_IMPROVEMENT` 与 `TARGET_NOT_REACHED`。

阶段4.1至4.4已形成 motion and safety baseline，冻结 tag 为 `stage4-motion-safety-baseline`，总说明见 `docs\STAGE4_MOTION_SAFETY_BASELINE_SUMMARY.md`。完整运行入口依次为：

1. 生成并检查 machine path 与 motion validation。
2. 生成并检查 collision safety plan 与 multi-actuator schedule。
3. 生成并检查 optimized path、optimized schedule 与 optimization report。
4. 运行三个 Stage4 Demo 的 check 和 run 脚本。

该基线使用通用三轴参考参数、AABB/safe envelope近似和启发式调度。它不是PLC或伺服程序，不能直接控制设备，也不能替代真实机械动力学验证或安全认证。

阶段4.5连续清洗面路径重构：

```powershell
python aicar_sim\scripts\check_surface_model.py
python aicar_sim\scripts\check_continuous_path_profile.py
python aicar_sim\scripts\generate_continuous_surface_path.py
python aicar_sim\scripts\check_continuous_surface_path.py
python aicar_sim\scripts\generate_continuous_machine_path.py
python aicar_sim\scripts\check_continuous_machine_path.py
python aicar_sim\scripts\generate_continuous_surface_validation.py
python aicar_sim\scripts\check_continuous_surface_validation.py
python aicar_sim\scripts\generate_continuous_surface_report.py
python aicar_sim\scripts\check_continuous_surface_report.py
```

输入为参考解析sedan surface model和continuous scan profile，输出位于 `outputs\continuous_surface_path`、`continuous_machine_path`、`continuous_collision_safety`、`continuous_schedule` 与 `continuous_surface_validation`。所有输出均为离线候选和近似验证，不连接PLC、伺服、SDK或真实硬件。

阶段4.5第一次实验结论为 `NO_MEANINGFUL_IMPROVEMENT`。阶段4.5-R新增state-aware spacing、adaptive coverage、patch route优化、surface task聚合和实际共享区间调度适配器，输出位于对应的 `_r` 目录。运行：

```powershell
python aicar_sim\scripts\check_continuous_surface_repair_profile.py
python aicar_sim\scripts\generate_continuous_surface_path_r.py
python aicar_sim\scripts\generate_continuous_machine_path_r.py
python aicar_sim\scripts\generate_continuous_surface_validation_r.py
python aicar_sim\scripts\generate_continuous_surface_report_r.py
python aicar_sim\scripts\check_continuous_surface_report_r.py
```

当前修正版实验结果为 `ACCEPTED`。这是参考解析表面下的离线路径与多执行机构候选调度，不是CAD/点云路径，不代表真实清洗效果，不保证全局最优，也不能下发PLC或控制硬件。Stage4.5与Stage4.5-R均未合并main，Stage4冻结基线不变。
