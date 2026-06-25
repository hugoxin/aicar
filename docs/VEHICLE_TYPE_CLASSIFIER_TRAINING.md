# Vehicle Type Classifier Training

阶段 1.7 的目标是完成 sedan / suv / mpv 三分类小模型训练闭环。

当前只训练和验证模型，不把分类模型接入 `vehicle_type_result.json`。接入放到阶段 1.8。

## Data

训练数据来自：

```text
vehicle_type_lab\data\datasets\vehicle_type_classification\split\train
vehicle_type_lab\data\datasets\vehicle_type_classification\split\val
```

当前数量：

- train/sedan: 16
- train/suv: 16
- train/mpv: 16
- val/sedan: 4
- val/suv: 4
- val/mpv: 4

这是小样本 demo，只用于验证训练闭环，不代表商业精度。

## Model

使用 Ultralytics classification：

```text
yolo11n-cls.pt
```

如果本地没有该小模型权重，首次训练时允许 Ultralytics 自动下载。

## Commands

Dry-run:

```powershell
python vehicle_type_lab\scripts\train_vehicle_type_classifier.py --dry-run
```

Train and copy best model:

```powershell
python vehicle_type_lab\scripts\train_vehicle_type_classifier.py --copy-best
```

Evaluate:

```powershell
python vehicle_type_lab\scripts\eval_vehicle_type_classifier.py --save-report
```

## Outputs

Training runs:

```text
vehicle_type_lab\outputs\training\vehicle_type_classifier\runs
```

Reports:

```text
vehicle_type_lab\outputs\training\vehicle_type_classifier\reports\train_summary.md
vehicle_type_lab\outputs\training\vehicle_type_classifier\reports\eval_summary.md
vehicle_type_lab\outputs\training\vehicle_type_classifier\reports\val_predictions.csv
```

Copied model:

```text
vehicle_type_lab\models\vehicle_type_classifier\best.pt
```

## Notes

If training quality is poor, do not blindly tune parameters first. Prefer:

- add more data
- fix wrong labels
- remove blurry or badly cropped images
- ensure validation images represent each class

阶段 1.8 已增加 `classify` 推理模式：先用 YOLO 检测车辆 bbox，再裁切车辆区域，并调用 `vehicle_type_lab\models\vehicle_type_classifier\best.pt` 输出 `sedan` / `suv` / `mpv`。该推理接入只验证流程，不重新训练模型，也不修改 `aicar_sim`。

```powershell
python vehicle_type_lab\src\vehicle_type_lab\main.py --mode classify --image vehicle_type_lab\data\input_images\test_car.jpg --save-history
python vehicle_type_lab\scripts\check_vehicle_type_classify.py
```
