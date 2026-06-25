# Image Preprocessing Flow

阶段 1.5.1 / 1.5.2 / 1.5.3 建立 sedan / suv / mpv 三分类图片归档和标准化预处理流程。

当前不训练模型，不下载数据集，不删除原图。

## Phase 1.5.1: 原始图片归档

用户手动收集的原始图片放入：

```text
vehicle_type_lab\data\datasets\vehicle_type_classification\incoming\sedan
vehicle_type_lab\data\datasets\vehicle_type_classification\incoming\suv
vehicle_type_lab\data\datasets\vehicle_type_classification\incoming\mpv
```

`incoming` 中的图片可以尺寸不统一、命名不统一、后缀不统一。

支持输入格式：

- `jpg`
- `jpeg`
- `png`
- `webp`
- `bmp`

不要把未经处理的乱图直接放入 `raw`。

## Phase 1.5.2: 图片标准化预处理

运行：

```powershell
python vehicle_type_lab\scripts\prepare_vehicle_type_images.py
```

默认处理：

- 读取 EXIF 旋转并转为 RGB。
- 整图 letterbox/pad 到正方形，避免拉伸变形。
- resize 到 `640x640`。
- 输出 JPG，质量 92。
- 命名为 `类别_local_四位编号.jpg`。

可选 YOLO 辅助裁切：

```powershell
python vehicle_type_lab\scripts\prepare_vehicle_type_images.py --use-yolo-crop
```

YOLO crop 只用于根据 car / truck / bus bbox 尽量让车辆居中，不等于 sedan / suv / mpv 分类。

如果 YOLO 不可用或检测不到车辆，脚本会 fallback 到整图 letterbox，不崩溃。

## Phase 1.5.3: 标准化后检查

运行：

```powershell
python vehicle_type_lab\scripts\check_vehicle_type_dataset.py
```

检查 incoming、raw、split/train、split/val 中每个类别的图片数量。

标准化输出目录：

```text
vehicle_type_lab\data\datasets\vehicle_type_classification\raw
```

处理报告：

```text
vehicle_type_lab\data\datasets\vehicle_type_classification\manifests\preprocess_report.csv
```

报告默认可以提交，但真实图片默认不提交 git。

## Phase 1.5.R: 补齐后重建 raw

当用户补充或清理了 `incoming` 原图后，可以重建 `raw` 标准化输出。

先 dry-run：

```powershell
python vehicle_type_lab\scripts\prepare_vehicle_type_images.py --dry-run
```

清空旧 `raw` 图片并重新生成：

```powershell
python vehicle_type_lab\scripts\prepare_vehicle_type_images.py --use-yolo-crop --clean-output
```

`--clean-output` 只会删除：

- `raw\sedan` / `raw\suv` / `raw\mpv` 下的 `.jpg` / `.jpeg` / `.png`
- `manifests\preprocess_report.csv`

它不会删除 `incoming` 原图，不会删除 `input_images\test_car.jpg`，不会删除 `yolo11n.pt`，也不会处理 `split\train` 或 `split\val`。

完整重建流程见 `docs\VEHICLE_TYPE_DATASET_REBUILD.md`。

## Phase 1.6: train / val 自动切分

标准化并人工检查 `raw` 后，运行：

```powershell
python vehicle_type_lab\scripts\split_vehicle_type_dataset.py --clean-split
```

该脚本从 `raw` 复制图片到 `split\train` 和 `split\val`，默认比例为 80/20。它不移动 `raw`，不删除 `incoming`，不训练模型。

完整说明见 `docs\VEHICLE_TYPE_DATASET_SPLIT.md`。
