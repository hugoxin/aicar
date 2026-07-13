# Project Structure

`F:\aicar` 是 AI 智能无人洗车项目的总工作区。它不是默认的大一统代码仓库，而是为多个后续可独立维护、可独立 git 的子项目预留边界。

## Root Files

- `README.md`：总工作区说明。
- `PROJECT_STRUCTURE.md`：目录职责和拆分策略。
- `ENVIRONMENT.md`：基础开发环境计划。
- `GIT_STRATEGY.md`：后续 git 和 GitHub 管理策略。
- `.gitignore`：总工作区默认忽略规则。

## docs

`docs` 保存总文档，包括路线图、系统架构、模块边界、车辆类型接口、开源参考计划、数据集计划、模型计划、协作注意事项、目录策略、文档索引、模型产物说明和阶段冻结总结。

阶段 1 车辆识别小闭环冻结总结：

```text
docs\STAGE1_VEHICLE_RECOGNITION_SUMMARY.md
```

阶段 1 冻结前最后修补文档：

```text
docs\PROJECT_DIRECTORY_STRATEGY.md
docs\INDEX.md
docs\MODEL_ARTIFACTS.md
docs\STAGE1_FINAL_FIX_NOTES.md
```

阶段 3 可视化基线冻结总结：

```text
docs\STAGE3_VISUAL_BASELINE_SUMMARY.md
```

阶段 3.3 客户展示页计划：

```text
docs\STAGE3_CUSTOMER_SHOWCASE_PLAN.md
```

阶段 3.4 客户演示材料计划：

```text
docs\STAGE3_CUSTOMER_MATERIALS_PLAN.md
```

阶段 4 运动约束与候选路径计划：

```text
docs\STAGE4_MOTION_CONSTRAINTS_PLAN.md
docs\STAGE4_MACHINE_FEASIBLE_PATH_PLAN.md
docs\STAGE4_COLLISION_AND_SAFETY_PLAN.md
docs\STAGE4_MULTI_ACTUATOR_CONSTRAINTS.md
docs\STAGE4_PATH_OPTIMIZATION_PLAN.md
docs\STAGE4_CYCLE_TIME_OPTIMIZATION.md
docs\STAGE4_MOTION_SAFETY_BASELINE_SUMMARY.md
docs\STAGE4_CONTINUOUS_SURFACE_PATH_PLAN.md
docs\STAGE4_SURFACE_MODEL_AND_SCAN_STRATEGY.md
```

## demos

`demos` 保存项目展示层内容。阶段 1.D 已创建：

```text
demos\stage1_visual_demo
```

该 Demo 用于给项目组、客户或合作方展示阶段1车辆识别成果：输入一张车辆图片，调用现有 `vehicle_type_lab --mode classify`，复制 JSON、检测分类可视化图和 crop，再读取 `aicar_sim\data\vehicles` 中的车辆模型，生成单文件 HTML 报告。

Demo 是展示壳，不属于阶段2，不修改 `vehicle_type_lab` / `aicar_sim` 核心逻辑。`demo_inputs` 和 `demo_outputs` 中的真实图片、生成报告和 JSON 默认不进入 Git。

阶段 2.D 已创建：

```text
demos\stage2_pipeline_demo
```

该 Demo 用于展示阶段2.1到阶段2.6完整链路：从 `vehicle_type_result.json` 出发，一键生成洗车策略、空间模型、喷嘴覆盖、流程状态机、抽象路径点和覆盖率报告，并生成单文件 HTML。它只是展示层，不做新算法、不做动画引擎、不做 PLC 或硬件控制。`demo_outputs` 中的 HTML 和 JSON 默认不进入 Git。

阶段 3.1 已创建：

```text
demos\stage3_2d_visual_demo
```

该 Demo 用于把阶段2 JSON 结果渲染为 2D HTML/SVG 报告，包括洗车房俯视图、车辆包络、安全包络、抽象喷嘴路径、覆盖率表和流程时间线。它不是 3D、不是动画引擎、不是真实路径规划，也不连接 PLC 或硬件。`demo_outputs` 中的 HTML 和 JSON 默认不进入 Git。

阶段 3.2 已创建：

```text
demos\stage3_timeline_animation_demo
```

该 Demo 用于把阶段2 JSON 结果按洗车流程时间轴播放展示，包括 Play/Pause/Reset、slider、当前状态面板、当前区域高亮和当前抽象路径高亮。它不是 3D、不是复杂动画引擎、不是真实运动控制，也不连接 PLC 或硬件。`demo_outputs` 中的 HTML 和 JSON 默认不进入 Git。

阶段 3.3 已创建：

```text
demos\stage3_customer_showcase_demo
```

该 Demo 用于把阶段1车辆识别、阶段2仿真链路和阶段3可视化结果包装成一页式客户展示页，面向项目组、客户、领导、合作方和申报材料沟通。它不是新算法、不是 3D、不是真实路径规划、不是 PLC 或硬件控制。`demo_outputs` 中的 HTML 和 JSON 默认不进入 Git。

阶段 4.1 / 4.2 已创建：

```text
demos\stage4_motion_constraint_demo
```

该 Demo 把阶段2抽象路径转换为满足通用三轴参考模型基础约束的机械可行候选轨迹，并检查工作空间、速度、加速度、连续性、时间戳和安全距离。它不代表真实设备轨迹，不生成 PLC 或伺服指令，也不控制硬件。

## aicar_sim

`aicar_sim` 是主仿真框架项目。它负责无人洗车纯仿真、路径规划占位、洗车状态机占位、VirtualPLC 占位、喷嘴控制占位、日志、输出和配置。

它通过 `vehicle_type_input.py` 读取 `vehicle_type_lab` 输出的 JSON，并解析到 `data\vehicles` 下的车辆模型文件。它不直接识别图片，也不训练模型。

阶段 1.9 中，`aicar_sim` 正式消费 `sedan` / `suv` / `mpv` 分类结果，加载 `data\vehicles\sedan.json`、`suv.json`、`mpv.json` 中的 mock 尺寸和 `wash_profile`。`scripts\check_vehicle_model_selection.py` 检查当前真实 JSON，`scripts\check_all_vehicle_model_selection.py` 使用 fixtures 检查三类和 unknown fallback。

阶段 2.1 中，`aicar_sim` 新增 `data\wash_profiles`、`wash_profile.py` 和 `wash_strategy.py`，根据车辆模型中的 `wash_profile` 生成 `outputs\wash_strategy\wash_strategy_plan.json`。该阶段只做策略层 JSON，不做路径规划、喷嘴轨迹、PLC 或硬件控制。

阶段 2.2 中，`aicar_sim` 新增 `data\wash_bays`、`vehicle_envelope.py`、`wash_bay.py` 和 `space_model.py`，根据车辆尺寸和 wash profile 生成车辆包络、洗车房静态空间模型和 `outputs\space_model\space_model_report.json`。该阶段仍不做路径规划、动画、PLC 或硬件控制。

阶段 2.3 中，`aicar_sim` 新增 `data\nozzles`、`nozzle_model.py` 和 `nozzle_coverage.py`，根据 `space_model_report.json` 的 surface zones 生成 `outputs\nozzle_plan\nozzle_coverage_plan.json`。该阶段只做喷嘴参数和区域覆盖计划，不生成真实喷嘴路径，不做动画、PLC 或硬件控制。

阶段 2.4 中，`aicar_sim` 新增 `data\wash_flows`、`wash_flow.py`、`wash_state_machine.py` 的真实状态机构建逻辑和 `outputs\wash_flow\wash_flow_run.json` 输出。该阶段只把洗车策略、空间模型和喷嘴覆盖计划串成状态级 timeline，不生成真实喷嘴路径，不做动画、PLC 或硬件控制。

阶段 2.5 中，`aicar_sim` 新增 `abstract_path.py`、`path_plan.py` 和 `outputs\path_plan\abstract_nozzle_path_plan.json` 输出。该阶段只生成车辆坐标系下的抽象喷嘴路径点，不生成真实硬件路径规划，不做动画、PLC 或硬件控制。

阶段 2.6 中，`aicar_sim` 新增 `coverage_report.py` 和 `outputs\coverage_report\coverage_report.json` 输出。该阶段只基于抽象路径点、喷嘴覆盖目标和空间 zone 做覆盖率估算报告，不做真实流体仿真、动画、PLC 或硬件控制。

阶段 2.F 中，阶段2已形成 simulation baseline。冻结总结文档位于：

```text
docs\STAGE2_SIMULATION_BASELINE_SUMMARY.md
```

阶段 3.1 中，`aicar_sim` 新增 `visualization_2d.py`、`generate_2d_visualization_report.py` 和 `outputs\visualization_2d\stage3_2d_visual_report.html` 输出。该阶段只做静态 2D 可视化，不做 3D、动画引擎、真实路径规划、PLC 或硬件控制。

阶段 3.2 中，`aicar_sim` 新增 `timeline_animation.py`、`generate_timeline_animation_report.py` 和 `outputs\timeline_animation\stage3_timeline_animation_report.html` 输出。该阶段只做轻量时间轴动画展示，不做 3D、复杂动画引擎、真实运动控制、PLC 或硬件控制。

阶段 3.3 中，`aicar_sim` 新增 `customer_showcase.py`、`generate_customer_showcase_report.py` 和 `outputs\customer_showcase\stage3_customer_showcase_report.html` 输出。该阶段只做客户展示页包装，不改变阶段1识别、阶段2仿真或阶段3可视化核心逻辑。

阶段 4.1 / 4.2 中，`aicar_sim` 新增通用三轴 motion model、线性插值、时间参数化、候选路径规划、运动验证和单文件 HTML 报告。运行输出位于 `outputs\machine_path` 和 `outputs\motion_validation`，默认不进入 Git。

阶段 3.F 中，阶段3已形成 visual baseline。冻结总结文档位于：

```text
docs\STAGE3_VISUAL_BASELINE_SUMMARY.md
```

后续它可以作为独立 git 仓库维护。当前阶段只做 scaffold，不做复杂仿真算法。

## vehicle_type_lab

`vehicle_type_lab` 是车辆识别小闭环项目。它的目标是后续完成 sedan / SUV / MPV 三分类识别，并输出标准 JSON 结果给 `aicar_sim` 使用。

当前已预留 `schemas`、`examples`、图片输入工具、YOLO 检测入口和 mock 输出入口，用于生成 `outputs\predictions\vehicle_type_result.json`。可选 history 输出保存在 `outputs\predictions\history`。

`data\datasets\vehicle_type_classification` 保存 sedan / suv / mpv 三分类数据规范，包括 incoming 原图归档、raw 标准化输出、train/val split、manifest 模板、类别定义和命名规则。真实训练图片默认不提交 git。

阶段 1.6 中，`split_vehicle_type_dataset.py` 会从 `raw` 复制图片到 `split\train` 和 `split\val`，并生成 `manifests\split_manifest.csv`。它不移动 raw，也不训练模型。

阶段 1.6.1 中，`make_vehicle_type_split_contact_sheets.py` 会读取 split/train 和 split/val，生成 `review` 下的 contact sheet 总览图，用于人工质检。

阶段 1.7 中，`train_vehicle_type_classifier.py` 使用 split/train 和 split/val 训练小分类模型，`eval_vehicle_type_classifier.py` 输出验证报告。训练产物保存在 `models\vehicle_type_classifier` 和 `outputs\training\vehicle_type_classifier`。

阶段 1.8 中，`main.py --mode classify` 会复用 YOLO 车辆检测 bbox，裁切车辆区域到 `outputs\predictions\crops`，再调用 `models\vehicle_type_classifier\best.pt` 进行 sedan / suv / mpv 推理，并输出兼容的 `vehicle_type_result.json`。相关说明见 `docs\VEHICLE_TYPE_CLASSIFY_PIPELINE.md`。

后续它可以作为独立 git 仓库维护。当前阶段只做 scaffold，不训练模型，不下载数据集，不实现复杂 AI。

## external_repos

`external_repos` 用于存放后续下载的 GitHub 开源参考项目，例如 Turntable_carwash、PythonRobotics、pymodbus、openplc-runtime 等。

这些项目只作为学习和参考，不要把源码直接复制进 `aicar_sim` 或 `vehicle_type_lab`，也不要把第三方仓库混入自己的 git。

## future planned directories

以下目录是后续预留共识，当前 `business_docs` 已用于阶段3.4客户演示材料，`experiments` 暂未创建：

```text
experiments    # 后续实验验证
business_docs  # 后续商业方案、汇报材料、客户材料
```

所有后续相关内容应放在 `F:\aicar` 下，不建议在 `F:\aicar` 外创建散落项目目录。

## business_docs

`business_docs` 保存面向客户、领导、合作方和项目申报的材料。阶段3.4新增：

```text
business_docs\stage3_customer_materials
```

该目录包含一页式项目介绍、客户演示话术、客户演示PPT大纲、常见问题、价值主张、技术边界说明和后续路线图。当前只整理 Markdown/文本材料，不生成 PPTX，不修改核心代码。

`PPT_GENERATION_PLAN.md` 记录正式 PPTX 生成前方案，包括12页结构、每页核心观点、推荐图示、讲解要点和素材来源。当前只记录方案，不生成 PPTX。

## datasets

`datasets` 是共享数据目录，用于统一管理 raw、processed、vehicle_type、annotations、samples 等数据。

数据集通常体积较大，不建议直接塞进 git。当前只预留目录，不下载大数据集。

## models

`models` 是共享模型目录，用于统一管理 pretrained、trained、exported 等模型文件。

模型文件通常体积较大，不建议直接塞进 git。当前只预留目录，不下载大模型。

## tools

`tools` 保存总工作区工具脚本，例如基础依赖安装脚本、工作区检查脚本、临时输出清理脚本。

## Current Boundary

阶段 1 已冻结为车辆识别小闭环：图片输入、YOLO 检测、车辆裁切、三分类推理、JSON 输出、`aicar_sim` 车辆模型选择链路已经跑通。后续阶段 2 再进入洗车策略与喷嘴路径仿真。

阶段4.3在 `aicar_sim\data\safety_models` 和 `data\actuator_systems` 保存参考安全布局与三执行机构配置，在 `src\aicar_sim` 保存碰撞、扫掠体、任务分配、互锁调度和安全停机模块。生成的 JSON/HTML 位于 `aicar_sim\outputs\collision_safety`、`outputs\multi_actuator_schedule` 和 `demos\stage4_collision_safety_demo\demo_outputs`，均不进入 Git；目录只保留 `.gitkeep`。

阶段4.4在 `aicar_sim\data\optimization_profiles` 保存安全优先优化参数，在 `src\aicar_sim` 保存路径指标、简化、transition、clearance-aware、任务顺序和调度优化模块。生成结果位于 `outputs\path_optimization`、`outputs\optimized_schedule` 和 `demos\stage4_path_optimization_demo\demo_outputs`，均由 `.gitignore` 排除。

阶段4.1至4.4的冻结范围、基线指标、已知限制和后续路线统一记录在 `docs\STAGE4_MOTION_SAFETY_BASELINE_SUMMARY.md`。冻结 tag 为 `stage4-motion-safety-baseline`；这不是可直接下发PLC或伺服的真实控制基线。

阶段4.5在 `aicar_sim\data\surface_models` 和 `data\continuous_path_profiles` 保存参考解析表面与扫描参数，在 `src\aicar_sim` 保存surface patch、scan、stitch、coverage、validation和report模块。生成JSON/HTML位于 `outputs\continuous_*` 与 `demos\stage4_continuous_surface_path_demo\demo_outputs`，均不进入Git；目录仅保留 `.gitkeep`。

阶段4.5-R在独立修复分支中新增 `state_scan_policy.py`、`patch_route_optimizer.py`、`surface_task_aggregator.py`、`surface_schedule_adapter.py` 和 `continuous_surface_*repair*.py` 适配层。修正版输出目录统一使用 `_r` 后缀，Demo 位于 `demos\stage4_continuous_surface_path_repair_demo`。生成JSON/HTML均被忽略，只提交源码、配置、schema、文档、检查脚本和 `.gitkeep`。首版状态为 `NO_MEANINGFUL_IMPROVEMENT`，修正版为当前实验；两者均未合并 `main`，Stage4冻结基线不变。
