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

## demos

`demos` 保存项目展示层内容。阶段 1.D 已创建：

```text
demos\stage1_visual_demo
```

该 Demo 用于给项目组、客户或合作方展示阶段1车辆识别成果：输入一张车辆图片，调用现有 `vehicle_type_lab --mode classify`，复制 JSON、检测分类可视化图和 crop，再读取 `aicar_sim\data\vehicles` 中的车辆模型，生成单文件 HTML 报告。

Demo 是展示壳，不属于阶段2，不修改 `vehicle_type_lab` / `aicar_sim` 核心逻辑。`demo_inputs` 和 `demo_outputs` 中的真实图片、生成报告和 JSON 默认不进入 Git。

## aicar_sim

`aicar_sim` 是主仿真框架项目。它负责无人洗车纯仿真、路径规划占位、洗车状态机占位、VirtualPLC 占位、喷嘴控制占位、日志、输出和配置。

它通过 `vehicle_type_input.py` 读取 `vehicle_type_lab` 输出的 JSON，并解析到 `data\vehicles` 下的车辆模型文件。它不直接识别图片，也不训练模型。

阶段 1.9 中，`aicar_sim` 正式消费 `sedan` / `suv` / `mpv` 分类结果，加载 `data\vehicles\sedan.json`、`suv.json`、`mpv.json` 中的 mock 尺寸和 `wash_profile`。`scripts\check_vehicle_model_selection.py` 检查当前真实 JSON，`scripts\check_all_vehicle_model_selection.py` 使用 fixtures 检查三类和 unknown fallback。

阶段 2.1 中，`aicar_sim` 新增 `data\wash_profiles`、`wash_profile.py` 和 `wash_strategy.py`，根据车辆模型中的 `wash_profile` 生成 `outputs\wash_strategy\wash_strategy_plan.json`。该阶段只做策略层 JSON，不做路径规划、喷嘴轨迹、PLC 或硬件控制。

阶段 2.2 中，`aicar_sim` 新增 `data\wash_bays`、`vehicle_envelope.py`、`wash_bay.py` 和 `space_model.py`，根据车辆尺寸和 wash profile 生成车辆包络、洗车房静态空间模型和 `outputs\space_model\space_model_report.json`。该阶段仍不做路径规划、动画、PLC 或硬件控制。

阶段 2.3 中，`aicar_sim` 新增 `data\nozzles`、`nozzle_model.py` 和 `nozzle_coverage.py`，根据 `space_model_report.json` 的 surface zones 生成 `outputs\nozzle_plan\nozzle_coverage_plan.json`。该阶段只做喷嘴参数和区域覆盖计划，不生成真实喷嘴路径，不做动画、PLC 或硬件控制。

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

以下目录是后续预留共识，当前暂未创建，不属于阶段1冻结缺陷：

```text
experiments    # 后续实验验证
business_docs  # 后续商业方案、汇报材料、客户材料
```

所有后续相关内容应放在 `F:\aicar` 下，不建议在 `F:\aicar` 外创建散落项目目录。

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
