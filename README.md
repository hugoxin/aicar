# AI Car Wash Workspace

这是 AI 智能无人洗车项目的总工作区。

当前状态：

- 阶段1：车辆识别小闭环已完成，可冻结。
- 阶段1.D：车辆识别可视化 Demo 已创建，用于展示阶段1成果。
- 阶段2.1：洗车策略配置与车辆数字模型接入已开始，当前只生成策略计划 JSON，不做路径规划、PLC 或硬件控制。
- 阶段2.2：车辆包络模型与洗车空间模型已开始，当前只做静态空间 JSON，不做喷嘴路径规划、动画、PLC 或硬件控制。
- 阶段2.3：喷嘴模型与喷嘴覆盖参数已开始，当前只生成覆盖参数 JSON，不做真实路径规划、动画、PLC 或硬件控制。
- 阶段2.4：洗车流程状态机已开始，当前只生成状态机运行 JSON，不做真实喷嘴路径、动画、PLC 或硬件控制。
- 阶段2.5：抽象喷嘴路径点生成已开始，当前只生成可检查路径点 JSON，不做真实硬件路径规划、动画、PLC 或硬件控制。
- 阶段2.6：抽象路径覆盖率检查与报告已开始，当前只生成覆盖率报告 JSON，不做真实流体仿真、动画、PLC 或硬件控制。
- 阶段2.D：阶段2完整链路可视化 Demo 已开始，当前只做本地 HTML 展示层，不做新算法、动画引擎、PLC 或硬件控制。
- 阶段2.F：阶段2已形成 simulation baseline，冻结总结见 `docs\STAGE2_SIMULATION_BASELINE_SUMMARY.md`。
- 阶段3.1：阶段2结果 2D 可视化已开始，当前只生成静态 HTML/SVG 报告，不做 3D、动画引擎、PLC 或硬件控制。
- 阶段3.2：简单时间轴动画 Demo 已开始，当前只做原生 HTML/CSS/JavaScript 播放展示，不做 3D、复杂动画引擎、PLC 或硬件控制。
- 阶段3.F：阶段3已形成 visual baseline，冻结总结见 `docs\STAGE3_VISUAL_BASELINE_SUMMARY.md`。
- 阶段3.3：客户展示页优化已开始，当前只生成一页式 HTML 展示报告，不做新算法、3D、PLC 或硬件控制。
- 阶段3.4：客户演示材料整理已开始，当前只整理 Markdown/文本材料，不生成 PPTX，不修改核心代码。
- 阶段4.1：运动约束模型已开始，当前使用通用三轴参考模型，不连接真实硬件。
- 阶段4.2：机械可行候选路径生成与验证已开始，当前输出不能直接下发 PLC 或伺服。
- 阶段4.3：碰撞安全与多执行机构约束已完成，当前使用保守几何近似和共享空间互锁。
- 阶段4.4：安全优先路径与周期优化已完成，未达到的优化目标保留为 `TARGET_NOT_REACHED`。
- 阶段4.F：Stage4 motion and safety baseline completed，冻结 tag 为 `stage4-motion-safety-baseline`。当前是候选轨迹和安全约束仿真，不是真实设备控制。

阶段1最终链路：

```text
test_car.jpg
  -> YOLO 检测
  -> crop
  -> best.pt 分类 sedan/suv/mpv
  -> vehicle_type_result.json
  -> aicar_sim
  -> 车辆模型
  -> wash_profile
```

重要说明：

- 当前 `best.pt` 不进入 Git，需要单独备份。
- 当前车辆尺寸是 mock 参数。
- 当前模型是小样本 demo，不代表商业精度。
- 所有项目内容统一归入 `F:\aicar`。
- 不建议在 `F:\aicar` 外创建散落目录。

阶段1冻结前关键文档：

- [docs\PROJECT_DIRECTORY_STRATEGY.md](docs/PROJECT_DIRECTORY_STRATEGY.md)
- [docs\INDEX.md](docs/INDEX.md)
- [docs\MODEL_ARTIFACTS.md](docs/MODEL_ARTIFACTS.md)
- [docs\STAGE1_FINAL_FIX_NOTES.md](docs/STAGE1_FINAL_FIX_NOTES.md)
- [docs\STAGE1_VEHICLE_RECOGNITION_SUMMARY.md](docs/STAGE1_VEHICLE_RECOGNITION_SUMMARY.md)

当前包含：

- `aicar_sim`：主仿真框架，用于无人洗车纯仿真、路径规划占位、洗车状态机占位、VirtualPLC 占位、喷嘴动画占位、日志和配置。
- `vehicle_type_lab`：车辆识别小闭环项目，后续用于 sedan / SUV / MPV 三分类识别。
- `demos\stage1_visual_demo`：阶段1车辆识别可视化 Demo。它是展示层，只调用已有阶段1识别能力，不修改 `vehicle_type_lab` / `aicar_sim` 核心逻辑。
- `demos\stage3_2d_visual_demo`：阶段3.1 2D 可视化 Demo。它读取阶段2 JSON，生成俯视图、侧视图、覆盖率表和流程时间线 HTML。
- `demos\stage3_timeline_animation_demo`：阶段3.2 时间轴动画 Demo。它读取阶段2 JSON，按 wash flow timeline 高亮当前状态、区域和抽象路径。
- `demos\stage3_customer_showcase_demo`：阶段3.3 客户展示页 Demo。它把阶段1/2/3结果整理成客户、领导和项目组能快速理解的一页式 HTML。
- `business_docs\stage3_customer_materials`：阶段3.4 客户演示材料包，包含一页介绍、演示话术、PPT大纲、FAQ、价值主张、技术边界和后续路线图。
- `demos\stage4_motion_constraint_demo`：阶段4运动约束 Demo，把抽象路径转换为机械可行候选轨迹，并生成约束验证 JSON/HTML。
- `demos\stage4_collision_safety_demo`：阶段4碰撞安全与多执行机构约束 Demo。
- `demos\stage4_path_optimization_demo`：阶段4安全优先路径与周期优化 Demo。
- `external_repos`：开源参考项目存放区，只做参考，不把第三方源码复制进主项目。
- `datasets`：统一数据目录，当前只预留结构，不下载大数据集。
- `models`：统一模型目录，当前只预留结构，不下载大模型。
- `docs`：总文档，记录路线、架构、边界、数据、模型、协作策略。
- `tools`：总工作区工具脚本。

建议第一步验收命令：

```powershell
python tools\check_workspace.py
python aicar_sim\src\aicar_sim\main.py
python vehicle_type_lab\src\vehicle_type_lab\main.py
```

车辆类型接口验收命令：

```powershell
python vehicle_type_lab\src\vehicle_type_lab\main.py --mock-type suv
python aicar_sim\src\aicar_sim\main.py --vehicle-type-result vehicle_type_lab\outputs\predictions\vehicle_type_result.json
python vehicle_type_lab\scripts\check_interface.py
python aicar_sim\scripts\check_vehicle_type_input.py
```

YOLO 车辆检测模式：

```powershell
python vehicle_type_lab\src\vehicle_type_lab\main.py --mode detect --image vehicle_type_lab\data\input_images\test_car.jpg --save-history
python vehicle_type_lab\scripts\check_yolo_detect.py
```

三分类数据目录检查：

```powershell
python vehicle_type_lab\scripts\check_vehicle_type_dataset.py
```

三分类图片标准化预处理：

```powershell
python vehicle_type_lab\scripts\prepare_vehicle_type_images.py --dry-run
python vehicle_type_lab\scripts\prepare_vehicle_type_images.py --use-yolo-crop --clean-output
```

三分类 train / val 切分：

```powershell
python vehicle_type_lab\scripts\split_vehicle_type_dataset.py --dry-run
python vehicle_type_lab\scripts\split_vehicle_type_dataset.py --clean-split
python vehicle_type_lab\scripts\check_vehicle_type_dataset.py
```

生成 split 质检总览图：

```powershell
python vehicle_type_lab\scripts\make_vehicle_type_split_contact_sheets.py
```

三分类小模型训练：

```powershell
python vehicle_type_lab\scripts\train_vehicle_type_classifier.py --dry-run
python vehicle_type_lab\scripts\train_vehicle_type_classifier.py --copy-best
python vehicle_type_lab\scripts\eval_vehicle_type_classifier.py --save-report
```

阶段 1.8 已增加 YOLO 检测框 + 三分类模型推理接入验证：`classify` 模式会先检测车辆 bbox，再裁切车辆区域，并调用 `vehicle_type_lab\models\vehicle_type_classifier\best.pt` 输出 `sedan` / `suv` / `mpv` / `unknown`。当前仍是小样本 demo，不代表商业精度，且本阶段不修改 `aicar_sim`。

```powershell
python vehicle_type_lab\src\vehicle_type_lab\main.py --mode classify --image vehicle_type_lab\data\input_images\test_car.jpg --save-history
python vehicle_type_lab\scripts\check_vehicle_type_classify.py
```

阶段 1.9 已增加 `aicar_sim` 车辆模型选择闭环：`aicar_sim` 会读取 `vehicle_type_result.json` 中的 `sedan` / `suv` / `mpv`，加载 `aicar_sim\data\vehicles` 下对应车辆尺寸和 `wash_profile`。如果 `vehicle_type=unknown` 或未检测到车辆，则回退到 `suv.json`。

```powershell
python aicar_sim\src\aicar_sim\main.py --vehicle-type-result vehicle_type_lab\outputs\predictions\vehicle_type_result.json
python aicar_sim\scripts\check_vehicle_model_selection.py
python aicar_sim\scripts\check_all_vehicle_model_selection.py
```

阶段 1 已冻结为车辆识别小闭环，冻结总结见：

- [docs\STAGE1_VEHICLE_RECOGNITION_SUMMARY.md](docs/STAGE1_VEHICLE_RECOGNITION_SUMMARY.md)

阶段 1.D 可视化 Demo：

```powershell
Set-Location F:\aicar\demos\stage1_visual_demo
python scripts\check_demo.py
python scripts\run_stage1_demo.py --image demo_inputs\car_demo.jpg --open-report
```

Demo 会生成本地 HTML 报告：`demos\stage1_visual_demo\demo_outputs\reports\stage1_demo_report.html`。`demo_inputs` 和 `demo_outputs` 中的真实图片、HTML、JSON 不进入 Git。

阶段 2.1 洗车策略计划：

```powershell
python aicar_sim\scripts\check_wash_profile_selection.py
python aicar_sim\scripts\check_wash_strategy_plan.py
python aicar_sim\scripts\generate_wash_strategy_plan.py --vehicle-type-result vehicle_type_lab\outputs\predictions\vehicle_type_result.json
```

阶段2.1会读取车辆模型中的 `wash_profile`，生成 `aicar_sim\outputs\wash_strategy\wash_strategy_plan.json`。该 JSON 是运行输出，不进入 Git。

阶段 2.2 车辆包络与洗车空间模型：

```powershell
python aicar_sim\scripts\check_vehicle_envelope.py
python aicar_sim\scripts\check_wash_bay.py
python aicar_sim\scripts\check_space_model.py
python aicar_sim\scripts\generate_space_model.py --vehicle-type-result vehicle_type_lab\outputs\predictions\vehicle_type_result.json
```

阶段2.2会生成 `aicar_sim\outputs\space_model\space_model_report.json`。该 JSON 是运行输出，不进入 Git。

阶段 2.3 喷嘴模型与喷嘴覆盖参数：

```powershell
python aicar_sim\scripts\check_nozzle_catalog.py
python aicar_sim\scripts\check_nozzle_zone_mapping.py
python aicar_sim\scripts\check_nozzle_coverage_plan.py
python aicar_sim\scripts\generate_nozzle_coverage_plan.py --vehicle-type-result vehicle_type_lab\outputs\predictions\vehicle_type_result.json
```

阶段2.3会生成 `aicar_sim\outputs\nozzle_plan\nozzle_coverage_plan.json`。该 JSON 是运行输出，不进入 Git。

阶段 2.4 洗车流程状态机：

```powershell
python aicar_sim\scripts\check_wash_flow_config.py
python aicar_sim\scripts\check_wash_state_machine.py
python aicar_sim\scripts\check_wash_flow_run.py
python aicar_sim\scripts\generate_wash_flow_run.py --vehicle-type-result vehicle_type_lab\outputs\predictions\vehicle_type_result.json
```

阶段2.4会生成 `aicar_sim\outputs\wash_flow\wash_flow_run.json`。该 JSON 是运行输出，不进入 Git。

阶段 2.5 抽象喷嘴路径点生成：

```powershell
python aicar_sim\scripts\check_abstract_path.py
python aicar_sim\scripts\check_path_plan.py
python aicar_sim\scripts\generate_abstract_nozzle_path_plan.py --vehicle-type-result vehicle_type_lab\outputs\predictions\vehicle_type_result.json
```

阶段2.5会生成 `aicar_sim\outputs\path_plan\abstract_nozzle_path_plan.json`。该 JSON 是运行输出，不进入 Git。

阶段 2.6 抽象路径覆盖率检查与报告：

```powershell
python aicar_sim\scripts\check_coverage_report.py
python aicar_sim\scripts\generate_coverage_report.py --vehicle-type-result vehicle_type_lab\outputs\predictions\vehicle_type_result.json
```

阶段2.6会生成 `aicar_sim\outputs\coverage_report\coverage_report.json`。该 JSON 是运行输出，不进入 Git。

阶段 2.D 完整链路可视化 Demo：

```powershell
Set-Location F:\aicar\demos\stage2_pipeline_demo
python scripts\check_stage2_pipeline_demo.py
python scripts\run_stage2_pipeline_demo.py --open-report
```

Demo 会生成 `demos\stage2_pipeline_demo\demo_outputs\reports\stage2_pipeline_report.html`，并复制六个阶段2 JSON 到 `demo_outputs\json`。这些 HTML 和 JSON 是运行输出，不进入 Git。

阶段2 simulation baseline 总结：

- [docs\STAGE2_SIMULATION_BASELINE_SUMMARY.md](docs/STAGE2_SIMULATION_BASELINE_SUMMARY.md)

阶段3 visual baseline 总结：

- [docs\STAGE3_VISUAL_BASELINE_SUMMARY.md](docs/STAGE3_VISUAL_BASELINE_SUMMARY.md)

阶段 3.1 2D 可视化：

```powershell
python aicar_sim\scripts\check_visualization_2d.py
python aicar_sim\scripts\generate_2d_visualization_report.py --vehicle-type-result vehicle_type_lab\outputs\predictions\vehicle_type_result.json
```

输出 HTML：`aicar_sim\outputs\visualization_2d\stage3_2d_visual_report.html`。该 HTML 是运行输出，不进入 Git。

阶段 3.1 Demo：

```powershell
Set-Location F:\aicar\demos\stage3_2d_visual_demo
python scripts\check_stage3_2d_visual_demo.py
python scripts\run_stage3_2d_visual_demo.py --open-report
```

Demo 输出：`demos\stage3_2d_visual_demo\demo_outputs\reports\stage3_2d_visual_report.html`。Demo HTML 和 JSON 不进入 Git。

阶段 3.2 时间轴动画 Demo：

```powershell
python aicar_sim\scripts\check_timeline_animation.py
python aicar_sim\scripts\generate_timeline_animation_report.py --vehicle-type-result vehicle_type_lab\outputs\predictions\vehicle_type_result.json
```

输出 HTML：`aicar_sim\outputs\timeline_animation\stage3_timeline_animation_report.html`。该 HTML 是运行输出，不进入 Git。

```powershell
Set-Location F:\aicar\demos\stage3_timeline_animation_demo
python scripts\check_stage3_timeline_animation_demo.py
python scripts\run_stage3_timeline_animation_demo.py --open-report
```

Demo 输出：`demos\stage3_timeline_animation_demo\demo_outputs\reports\stage3_timeline_animation_report.html`。Demo HTML 和 JSON 不进入 Git。

阶段 3.3 客户展示页：

```powershell
python aicar_sim\scripts\check_customer_showcase.py
python aicar_sim\scripts\generate_customer_showcase_report.py --vehicle-type-result vehicle_type_lab\outputs\predictions\vehicle_type_result.json
```

输出 HTML：`aicar_sim\outputs\customer_showcase\stage3_customer_showcase_report.html`。该 HTML 是运行输出，不进入 Git。

```powershell
Set-Location F:\aicar\demos\stage3_customer_showcase_demo
python scripts\check_stage3_customer_showcase_demo.py
python scripts\run_stage3_customer_showcase_demo.py --open-report
```

Demo 输出：`demos\stage3_customer_showcase_demo\demo_outputs\reports\stage3_customer_showcase_report.html`。Demo HTML 和 JSON 不进入 Git。

阶段 3.4 客户演示材料：

```powershell
python tools\check_customer_materials.py
```

材料目录：`business_docs\stage3_customer_materials`。当前只整理 Markdown/文本材料，不生成 PPTX。PPT 正式生成前方案见 `business_docs\stage3_customer_materials\PPT_GENERATION_PLAN.md`。

阶段 4.1 / 4.2 运动约束与候选路径：

```powershell
python aicar_sim\scripts\check_motion_model.py
python aicar_sim\scripts\generate_machine_path_plan.py
python aicar_sim\scripts\check_machine_path_plan.py
python aicar_sim\scripts\generate_motion_validation_report.py
python aicar_sim\scripts\check_motion_validation.py
```

Stage4 Demo：

```powershell
Set-Location F:\aicar\demos\stage4_motion_constraint_demo
python scripts\check_stage4_motion_constraint_demo.py
python scripts\run_stage4_motion_constraint_demo.py --open-report
```

输出只能称为机械可行候选轨迹或运动约束仿真结果，不是已验证真实设备轨迹，也不能直接控制 PLC、伺服或硬件。

阶段 4.3 碰撞、安全约束和多执行机构候选调度：

```powershell
python aicar_sim\scripts\check_safety_layout.py
python aicar_sim\scripts\generate_collision_safety_plan.py
python aicar_sim\scripts\check_collision_safety_plan.py
python aicar_sim\scripts\generate_multi_actuator_schedule.py
python aicar_sim\scripts\check_multi_actuator_schedule.py
python aicar_sim\scripts\generate_collision_safety_report.py
python aicar_sim\scripts\check_collision_safety_validation.py
```

Demo：

```powershell
Set-Location F:\aicar\demos\stage4_collision_safety_demo
python scripts\check_stage4_collision_safety_demo.py
python scripts\run_stage4_collision_safety_demo.py --open-report
```

当前使用参考洗车房、三执行机构模型和保守 AABB，不是实际设备碰撞认证，不能直接下发 PLC。

阶段 4.4 安全优先的路径与周期优化：

```powershell
python aicar_sim\scripts\check_path_optimization_profile.py
python aicar_sim\scripts\generate_optimized_machine_path.py
python aicar_sim\scripts\check_optimized_machine_path.py
python aicar_sim\scripts\generate_optimized_schedule.py
python aicar_sim\scripts\check_optimized_schedule.py
python aicar_sim\scripts\generate_path_optimization_report.py
python aicar_sim\scripts\check_path_optimization_report.py
```

Demo 位于 `demos\stage4_path_optimization_demo`。优化不删除任务、不跨 wash state 重排、不降低250 mm硬安全下限；未达到的目标在报告中明确标记 `TARGET_NOT_REACHED`。

阶段4运动与安全基线已冻结，完整结果、限制和后续路线见：

- [docs\STAGE4_MOTION_SAFETY_BASELINE_SUMMARY.md](docs/STAGE4_MOTION_SAFETY_BASELINE_SUMMARY.md)

冻结 tag 为 `stage4-motion-safety-baseline`。该基线只表示通用参考模型下的候选轨迹与安全约束链路可重复、可检查，不代表真实设备控制、机械安全认证或最优路径规划。
