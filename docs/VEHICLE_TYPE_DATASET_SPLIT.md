# Vehicle Type Dataset Split

阶段 1.6 的目标是把标准化后的 sedan / suv / mpv 图片自动切分为 train / val。

当前不训练模型。训练放到阶段 1.7。

## Directory Roles

- `raw`: 标准化后的完整样本池。
- `split\train`: 后续训练集。
- `split\val`: 后续验证集。

当前采用 80/20 切分。每类 20 张时：

- `train`: 16 张
- `val`: 4 张

## Safety Rules

- 脚本使用复制，不移动 `raw`。
- `--clean-split` 只清理 `split\train` 和 `split\val` 下的图片。
- `--clean-split` 不清理 `raw`。
- `--clean-split` 不清理 `incoming`。
- 当前阶段不训练模型。

## Commands

Dry-run:

```powershell
python vehicle_type_lab\scripts\split_vehicle_type_dataset.py --dry-run
```

Clean and rebuild split:

```powershell
python vehicle_type_lab\scripts\split_vehicle_type_dataset.py --clean-split
```

Check dataset:

```powershell
python vehicle_type_lab\scripts\check_vehicle_type_dataset.py
```

## Manifest

The split script writes:

```text
vehicle_type_lab\data\datasets\vehicle_type_classification\manifests\split_manifest.csv
```

Fields:

```text
class_name,split,image_path,source_raw_path
```

## Manual Review

阶段 1.6.1 使用 contact sheet 做训练前人工质检：

```powershell
python vehicle_type_lab\scripts\make_vehicle_type_split_contact_sheets.py
```

如果发现问题，不要直接修改 split，回到 incoming/raw 阶段替换原图并重新预处理、重新切分。

完整说明见 `docs\VEHICLE_TYPE_SPLIT_REVIEW.md`。

## Training

人工质检通过后，阶段 1.7 可运行三分类小模型训练：

```powershell
python vehicle_type_lab\scripts\train_vehicle_type_classifier.py --copy-best
```

训练详情见 `docs\VEHICLE_TYPE_CLASSIFIER_TRAINING.md`。
