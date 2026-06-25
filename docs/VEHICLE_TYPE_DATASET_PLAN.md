# Vehicle Type Dataset Plan

阶段 1.5 的目标是为 sedan / suv / mpv 三分类准备清晰的数据目录、类别标准、命名规则、manifest 格式和检查脚本。

阶段 1.5.1 / 1.5.2 / 1.5.3 增加原始图片归档和标准化预处理：

- `incoming`: 用户手动放入的未处理原图。
- `raw`: 预处理脚本输出的标准化训练准备图片。
- `split`: 后续 train / val 切分目录。

当前不训练模型，不下载数据集，不下载图片。

## Why Define Data Standards First

先定义数据规范，可以避免后续样本混乱、类别边界不清、文件命名不可维护、训练/验证拆分不可复现。

在没有清晰类别定义前直接训练模型，很容易得到不可解释、不可复用的结果。

## Why sedan / suv / mpv Matters

无人洗车策略需要知道车辆的大致尺寸和形态：

- `sedan`：车身较低，路径和喷嘴高度可以更贴近低矮车身。
- `suv`：车身更高更宽，需要更保守的安全距离和覆盖高度。
- `mpv`：车身更长、更高、车顶更平，需要更完整的侧面和顶部覆盖策略。

第一阶段的车型分类不是品牌型号识别，而是洗车策略所需的大类识别。

## First Sample Target

推荐第一批小样本：

- `sedan`: 20 张
- `suv`: 20 张
- `mpv`: 20 张

这些图片可以先来自本地手动收集的小样本。公开数据集只作为后续研究，当前阶段不下载。

## Preprocessing Standard

原始图片先放入：

```text
vehicle_type_lab\data\datasets\vehicle_type_classification\incoming\sedan
vehicle_type_lab\data\datasets\vehicle_type_classification\incoming\suv
vehicle_type_lab\data\datasets\vehicle_type_classification\incoming\mpv
```

不要直接把命名混乱、尺寸不统一、背景较多的原图放入 `raw`。

预处理脚本：

```powershell
python vehicle_type_lab\scripts\prepare_vehicle_type_images.py
```

输出标准：

- 输入支持 `jpg` / `jpeg` / `png` / `webp` / `bmp`。
- 输出统一为 `jpg`。
- 默认尺寸为 `640x640`。
- 输出命名为 `类别_local_四位编号.jpg`。
- 不删除、不移动、不覆盖 `incoming` 原图。
- 可选 `--use-yolo-crop` 用 YOLO bbox 辅助居中。
- YOLO crop 失败时 fallback 到整图 letterbox。
- 报告输出到 `manifests\preprocess_report.csv`。

## Rebuild Flow

阶段 1.5.R 用于用户补齐或清理 incoming 后重建 `raw`：

```powershell
python vehicle_type_lab\scripts\prepare_vehicle_type_images.py --dry-run
python vehicle_type_lab\scripts\prepare_vehicle_type_images.py --use-yolo-crop --clean-output
python vehicle_type_lab\scripts\check_vehicle_type_dataset.py
```

`--clean-output` 只清理旧的 `raw` 图片和 `preprocess_report.csv`，不会删除 `incoming` 原图。

完整说明见 `docs\VEHICLE_TYPE_DATASET_REBUILD.md`。

## Train / Val Split

阶段 1.6 用于把 `raw` 标准化样本复制到 `split\train` 和 `split\val`：

```powershell
python vehicle_type_lab\scripts\split_vehicle_type_dataset.py --dry-run
python vehicle_type_lab\scripts\split_vehicle_type_dataset.py --clean-split
python vehicle_type_lab\scripts\check_vehicle_type_dataset.py
```

默认采用 80/20。每类 20 张时，train 16 张，val 4 张。

脚本只复制图片，不移动 `raw`，也不训练模型。

完整说明见 `docs\VEHICLE_TYPE_DATASET_SPLIT.md`。

## Split Review

阶段 1.6.1 用于生成 split contact sheet，辅助训练前人工质检：

```powershell
python vehicle_type_lab\scripts\make_vehicle_type_split_contact_sheets.py
```

重点检查错类、裁切坏图、局部图、多车图、过度模糊图，以及 val 是否能代表该类别。

完整说明见 `docs\VEHICLE_TYPE_SPLIT_REVIEW.md`。

## Classifier Training

阶段 1.7 使用 `split\train` 和 `split\val` 训练 sedan / suv / mpv 三分类小模型：

```powershell
python vehicle_type_lab\scripts\train_vehicle_type_classifier.py --copy-best
python vehicle_type_lab\scripts\eval_vehicle_type_classifier.py --save-report
```

这是小样本 demo，不代表商业精度。完整说明见 `docs\VEHICLE_TYPE_CLASSIFIER_TRAINING.md`。

## Next Stage

阶段 1.8 才考虑把分类模型接入 `vehicle_type_result.json`。
