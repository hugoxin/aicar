# YOLO Detection Flow

阶段 1.4 的目标是在 `vehicle_type_lab` 中加入现成 YOLO 车辆检测能力。

当前只检测车辆是否存在，不做 sedan / suv / mpv 三分类训练。

## Boundary

- 可以使用 `ultralytics`。
- 首次真实 detect 运行时允许下载小型 YOLO 权重，例如 `yolo11n.pt`。
- 不下载数据集。
- 不训练模型。
- 不 clone GitHub。
- 不连接真实硬件。
- 不做 pygame 仿真。

## Detect Command

```powershell
python vehicle_type_lab\src\vehicle_type_lab\main.py --mode detect --image vehicle_type_lab\data\input_images\test_car.jpg --save-history
```

默认输出：

```text
vehicle_type_lab\outputs\predictions\vehicle_type_result.json
```

如果检测到车辆，会额外保存带检测框的图片到：

```text
vehicle_type_lab\outputs\predictions\visualized
```

## Result Fields

输出 JSON 仍然符合 `vehicle_type_result.schema.json`：

- `vehicle_detected`：是否检测到 car / truck / bus。
- `vehicle_type`：当前仍然是 `unknown`。
- `confidence`：置信度最高的车辆框置信度。
- `bbox`：置信度最高的车辆框 `[x1, y1, x2, y2]`。
- `source_image`：输入图片路径。
- `image_width` / `image_height`：真实图片尺寸。
- `model_name`：实际 YOLO 模型名，例如 `yolo11n.pt`。
- `model_version`：`ultralytics-yolo-detect`。
- `notes`：说明当前只检测车辆存在，不做车型分类。

## Why vehicle_type Is Still unknown

YOLO 现成 COCO 类别可以检测 `car`、`truck`、`bus` 等车辆存在，但它不会直接给出洗车策略需要的 sedan / suv / mpv 大类。

所以阶段 1.4 中：

- 检测到车辆：`vehicle_detected=true`
- 车型大类：`vehicle_type=unknown`

阶段 1.5 先定义 sedan / suv / mpv 三分类数据目录、类别标准、命名规则和 manifest 格式。后续阶段才考虑车型大类分类 demo。

## Stage 1.8 Classify Mode

阶段 1.8 新增了 `classify` 模式，但 `detect` 模式的语义保持不变。

- `detect`：只检测 car / truck / bus，`vehicle_type` 仍为 `unknown`。
- `classify`：先使用 YOLO 选出最高置信车辆 bbox，再裁切车辆区域，并调用 `vehicle_type_lab\models\vehicle_type_classifier\best.pt` 输出 `sedan` / `suv` / `mpv`。

命令：

```powershell
python vehicle_type_lab\src\vehicle_type_lab\main.py --mode classify --image vehicle_type_lab\data\input_images\test_car.jpg --save-history
```

分类可视化图会保存到：

```text
vehicle_type_lab\outputs\predictions\visualized\test_car_classified.jpg
```

裁切图会保存到：

```text
vehicle_type_lab\outputs\predictions\crops\test_car_crop.jpg
```
