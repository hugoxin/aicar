# 阶段1冻结前最后一次修补记录

## 1. 修补原因

阶段1功能链路已经完成，两次只读审查确认阶段1可以冻结。

正式冻结前仍需要补充：

- 目录策略
- 文档索引
- 模型产物说明
- Git 状态和模型备份风险说明

本次是阶段1冻结前最后一次低风险工程修补，不是功能开发。

## 2. 本次边界

本次不做 Demo。

本次不进入阶段2。

本次不修改核心推理代码。

本次不训练模型。

本次不移动或复制 `best.pt`。

本次不执行任何 Git 初始化、提交或打标签操作。

## 3. 两份审查结论摘要

### 项目结构审查

- 阶段1“车辆识别小闭环”功能上已经完成，可以冻结。
- `vehicle_type_lab` 负责图片输入、YOLO 检测、车辆裁切、`sedan/suv/mpv` 分类和 `vehicle_type_result.json` 输出。
- `aicar_sim` 负责读取 `vehicle_type_result.json`，并根据 `sedan/suv/mpv/unknown` 选择车辆模型和 `wash_profile`。
- docs 文档较完整，但缺少总索引。
- 缺少 `PROJECT_DIRECTORY_STRATEGY`。
- `demos`、`experiments`、`business_docs` 当前 missing 不属于错误。
- `main.py` 偏重，但当前不重构。
- `detect_vehicle.py` / `classify_vehicle_type.py` 是旧占位，当前不删。

### P0 复核

- `F:\aicar` 当前不是有效 Git 仓库。
- `.git` 目录为空。
- `best.pt` 存在：`F:\aicar\vehicle_type_lab\models\vehicle_type_classifier\best.pt`。
- `best.pt` 大小：`3,188,866 bytes`。
- `best.pt` 被 `.gitignore` 忽略。
- `best.pt` 是阶段1核心产物，有备份风险。

## 4. 本次修补范围

新增文档：

- `docs\PROJECT_DIRECTORY_STRATEGY.md`
- `docs\INDEX.md`
- `docs\MODEL_ARTIFACTS.md`
- `docs\STAGE1_FINAL_FIX_NOTES.md`

更新文件：

- `README.md`
- `PROJECT_STRUCTURE.md`
- `tools\check_workspace.py`

## 5. 本次不做项

- 不创建 demo。
- 不创建 `demos\stage1_visual_demo`。
- 不进入阶段2。
- 不执行 `git init`。
- 不执行 `git add`。
- 不执行 `git commit`。
- 不执行 `git tag`。
- 不移动模型。
- 不复制模型。
- 不重构代码。
- 不删除旧脚本。
- 不下载数据。
- 不训练模型。

## 6. 冻结前状态

阶段1保持当前稳定基线：

```text
test_car.jpg
  -> YOLO 检测
  -> crop
  -> best.pt 分类
  -> vehicle_type_result.json
  -> aicar_sim
  -> 车辆模型
  -> wash_profile
```

后续可单独规划：

- `demos\stage1_visual_demo`
- 正式 Git 初始化和首次提交
- `best.pt` 外部备份
- 阶段2洗车策略与喷嘴路径仿真

## 7. 阶段1.G-fix：Git 初始化前小修补

阶段1.G-plan 只读检查发现首次提交前还有两个低风险忽略规则缺口：

- `incoming` 中存在 `.jfif` 原图。
- `split` 中存在 `train.cache` 和 `val.cache`。

本次修补记录：

- 补充 `.jfif` 图片忽略规则。
- 补充 split cache 忽略规则。
- 确认 `best.pt` 仍不进入 Git。
- 确认 `best.pt` 仍在原路径：`F:\aicar\vehicle_type_lab\models\vehicle_type_classifier\best.pt`。
- 确认 `best.pt` 大小仍为 `3,188,866 bytes`。
- 本次未执行 `git init` / `git add` / `git commit` / `git tag`。
- 本次未创建 Demo。
- 本次未进入阶段2。
- 本次未移动或复制 `best.pt`。
- 本次未修改核心推理代码或仿真消费代码。

## 8. 阶段1.G-backup：best.pt 本地备份

本次在正式 Git 初始化前完成 `best.pt` 外部备份。

- 已将 `best.pt` 备份到：`F:\aicar_backup\vehicle_type_classifier\best.pt`。
- 源文件路径：`F:\aicar\vehicle_type_lab\models\vehicle_type_classifier\best.pt`。
- 源文件大小：`3,188,866 bytes`。
- 备份文件大小：`3,188,866 bytes`。
- 源文件和备份文件大小一致。
- 本次未执行 `git init` / `git add` / `git commit` / `git tag`。
- 本次未创建 Demo。
- 本次未进入阶段2。
- 本次未修改核心推理代码。
- 本次未修改模型加载路径。
- 本次未移动原始 `best.pt`。

## 9. 阶段1.G-init-fix：首次提交前暂存区修复

阶段1.G-init 执行 `git add .` 后，暂存区发现不应进入 Git 的内容：

- `vehicle_type_lab\outputs\training\vehicle_type_classifier\runs\yolo11n_cls_sedan_suv_mpv\args.yaml`
- `vehicle_type_lab\outputs\training\vehicle_type_classifier\runs\yolo11n_cls_sedan_suv_mpv\results.csv`
- `aicar_stage1_review_pack_20260625_120735.zip`

本次修复记录：

- 补充 review zip 忽略规则：`aicar_stage1_review_pack_*.zip`。
- 补充 training runs 子内容忽略规则：`vehicle_type_lab/outputs/training/vehicle_type_classifier/runs/**`。
- `runs\.gitkeep` 属于 training runs 目录下的占位文件，不进入 Git；本次仅从暂存区移除，没有删除本地文件。
- 只从 Git 暂存区移除污染文件，不删除工作区文件本体。
- 本次未连接 GitHub。
- 本次未 push。
- 本次未创建 Demo。
- 本次未进入阶段2。
- 本次未移动或复制 `best.pt`。
- 本次未修改核心推理代码或仿真消费代码。
