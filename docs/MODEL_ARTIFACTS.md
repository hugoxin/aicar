# 模型产物说明

## 1. 阶段1核心模型产物

阶段1车辆识别小闭环的核心模型产物是：

```text
vehicle_type_lab\models\vehicle_type_classifier\best.pt
```

当前文件大小：

```text
3,188,866 bytes
```

## 2. 用途

`best.pt` 是 `sedan` / `suv` / `mpv` 三分类模型，用于：

```powershell
python vehicle_type_lab\src\vehicle_type_lab\main.py --mode classify --image vehicle_type_lab\data\input_images\test_car.jpg --save-history
```

在 `vehicle_type_lab --mode classify` 中，它接收 YOLO 检测框裁切出的车辆图片，并输出车辆大类：

- `sedan`
- `suv`
- `mpv`
- `unknown`

## 3. 当前状态

- `best.pt` 当前存在于本地。
- `best.pt` 是阶段1冻结核心产物。
- `best.pt` 不适合直接进入普通 Git 仓库。
- 当前 `.gitignore` 会忽略模型权重。

相关 `.gitignore` 规则：

```text
*.pt
vehicle_type_lab/models/vehicle_type_classifier/*.pt
```

因此，换机或重新 clone 时不会自动带上 `best.pt`。

## 4. 短期建议

- 手动备份 `best.pt` 到本地备份目录、移动硬盘或网盘。
- 推荐本地备份路径示例：`F:\aicar_backup\vehicle_type_classifier\best.pt`。
- 在交付或迁移时必须一起提供 `best.pt`。
- 不要仅依赖 Git 保存模型权重。
- Git 初始化和首次提交不会包含 `best.pt`。
- 后续换机或迁移项目时，必须同时恢复 `best.pt` 到 `F:\aicar\vehicle_type_lab\models\vehicle_type_classifier\best.pt`。
- 备份时建议同时记录文件大小、训练脚本、训练数据版本和 eval 结果。

## 5. 长期建议

后续可以使用以下方式管理模型文件：

- GitHub Release
- 网盘
- 对象存储
- 模型仓库
- 内部制品管理目录

代码仓库中建议只保存：

- 模型说明
- 模型路径
- 模型版本
- 训练来源
- 评估结果
- 校验信息
- 外部备份位置

## 6. 本次不执行

本文档只记录模型归档策略。

本次不执行：

- 不移动 `best.pt`。
- 不复制 `best.pt`。
- 不修改模型加载路径。
- 不取消 `.pt` 忽略规则。
- 不把 `best.pt` 强行加入 Git。

## 7. 阶段1.G-fix 记录

阶段1.G-fix 仅补充 Git 初始化前的忽略规则和模型归档说明。

- `best.pt` 当前不进入 Git。
- `best.pt` 仍需单独备份。
- 本次没有移动或复制 `best.pt`。
- 本次没有修改模型加载路径。

## 8. 本地备份状态

- `best.pt` 已备份到：`F:\aicar_backup\vehicle_type_classifier\best.pt`。
- 源文件大小：`3,188,866 bytes`。
- 备份文件大小：`3,188,866 bytes`。
- 备份用途：防止 Git 不保存模型权重导致换机或误删时无法恢复。
- 注意：Git 仓库仍不保存 `best.pt`，迁移项目时需要同步恢复该模型文件。
- 本次没有移动原始 `best.pt`。
- 本次没有修改模型加载路径。
