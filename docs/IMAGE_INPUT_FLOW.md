# Image Input Flow

当前阶段建立最小图片输入流程骨架，不使用真实 AI 模型，不下载 YOLO 权重，不训练模型。

```text
真实图片
  ↓
vehicle_type_lab 读取图片尺寸
  ↓
mock_classifier 生成 sedan / suv / mpv / unknown
  ↓
输出 vehicle_type_result.json
  ↓
aicar_sim 读取结果并选择车辆模型
```

## Current CLI

默认输出：

```text
vehicle_type_lab\outputs\predictions\vehicle_type_result.json
```

示例：

```powershell
python vehicle_type_lab\src\vehicle_type_lab\main.py --image vehicle_type_lab\data\input_images\test_car.jpg --mock-type suv --save-history
```

参数：

- `--image`：可选图片路径。如果图片存在，则读取真实图片尺寸。
- `--mock-type`：可选 mock 类型，允许 `sedan` / `suv` / `mpv` / `unknown`。
- `--output`：可选输出 JSON 路径。
- `--save-history`：可选参数，额外保存一份带时间戳的历史结果到 `vehicle_type_lab\outputs\predictions\history`。

## Missing Image Behavior

如果传入的图片不存在，程序不会崩溃，会输出 `unknown` 结果，并在 `notes` 中说明图片不存在。

## Boundary

`--mock-type` 只是为了测试“图片输入 -> JSON 输出 -> aicar_sim 读取”的流程。当前还没有真实 AI 模型，也不进行真实车辆分类。

## Phase 1.3: 真实本地图片尺寸读取验证

阶段 1.3 只验证本地图片路径和尺寸读取。

用户可以手动放入：

```text
vehicle_type_lab\data\input_images\test_car.jpg
```

然后运行：

```powershell
python vehicle_type_lab\scripts\check_image_input.py
```

如果图片存在，脚本会读取并打印真实 `image_width` 和 `image_height`。如果图片不存在，脚本只提示用户手动放入图片，不报错。

继续生成 mock JSON：

```powershell
python vehicle_type_lab\src\vehicle_type_lab\main.py --image vehicle_type_lab\data\input_images\test_car.jpg --mock-type suv --save-history
```

如果 `test_car.jpg` 存在，`vehicle_type_result.json` 中的 `image_width` / `image_height` 会使用真实图片尺寸。车辆类型仍然由 `--mock-type` 指定，不进行真实 AI 识别。

## Phase 1.4: 现成 YOLO 车辆检测

阶段 1.4 增加 `detect` 模式：

```powershell
python vehicle_type_lab\src\vehicle_type_lab\main.py --mode detect --image vehicle_type_lab\data\input_images\test_car.jpg --save-history
```

该模式使用现成 YOLO 模型检测 car / truck / bus 是否存在。如果检测到车辆，会输出 `vehicle_detected=true`，但 `vehicle_type` 仍然是 `unknown`，因为当前还没有启用 sedan / suv / mpv 分类。

完整说明见 `docs\YOLO_DETECTION_FLOW.md`。
