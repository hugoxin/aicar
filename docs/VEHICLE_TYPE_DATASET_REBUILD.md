# Vehicle Type Dataset Rebuild

阶段 1.5.R 用于重新补齐和重建 sedan / suv / mpv 三分类 `raw` 数据。

当前仍不训练模型，不下载数据集，不做 train / val 切分。

## Workflow

1. 手动整理 incoming 下的原图：

```text
vehicle_type_lab\data\datasets\vehicle_type_classification\incoming\sedan
vehicle_type_lab\data\datasets\vehicle_type_classification\incoming\suv
vehicle_type_lab\data\datasets\vehicle_type_classification\incoming\mpv
```

2. 手动删除 incoming 中明显不能用的图片：

- 错类
- 车辆不完整
- 多车混乱
- 过度模糊
- 明显裁坏
- 不是 sedan / suv / mpv

3. 运行检查：

```powershell
python vehicle_type_lab\scripts\check_vehicle_type_dataset.py
```

4. dry-run：

```powershell
python vehicle_type_lab\scripts\prepare_vehicle_type_images.py --dry-run
```

5. 清空旧 raw 并重新生成：

```powershell
python vehicle_type_lab\scripts\prepare_vehicle_type_images.py --use-yolo-crop --clean-output
```

6. 再次检查：

```powershell
python vehicle_type_lab\scripts\check_vehicle_type_dataset.py
```

## Safety Rules

- `incoming` 是原始图片池，脚本不自动删除。
- `raw` 是标准化输出，可以清空后重建。
- `--clean-output` 只删除 `raw\sedan`、`raw\suv`、`raw\mpv` 下的图片文件和旧 `preprocess_report.csv`。
- `split\train` 和 `split\val` 当前不处理。
- `vehicle_type_lab\data\input_images\test_car.jpg` 不会被删除。
- `yolo11n.pt` 不会被删除。

训练前还要进行人工质检和 train / val 切分。

## After Rebuild

重建并人工质检 `raw` 后，阶段 1.6 使用复制方式生成 train / val：

```powershell
python vehicle_type_lab\scripts\split_vehicle_type_dataset.py --clean-split
```

这个步骤不训练模型。训练或分类 demo 放到后续阶段。
