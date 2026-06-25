# Vehicle Type Interface

本文档定义 `vehicle_type_lab` 与 `aicar_sim` 之间的车辆识别结果接口。

当前阶段已包含接口、图片输入骨架、mock 输出、YOLO 车辆存在检测和读取占位。本阶段不训练模型，不下载数据集，不连接真实硬件。

## vehicle_type_lab 职责

`vehicle_type_lab` 是车辆识别小闭环项目。

它负责：

- 输入车辆图片。
- 读取图片尺寸。
- 输出车辆大类识别结果。
- 当前目标只支持 `sedan` / `suv` / `mpv` / `unknown`。
- `mock` 模式先用 mock 结果，不使用真实 AI 模型。
- `detect` 模式使用现成 YOLO 只检测车辆是否存在，不做 sedan / suv / mpv 分类。
- `classify` 模式先使用 YOLO 检测车辆 bbox，再裁切车辆区域，并调用本地三分类模型输出 `sedan` / `suv` / `mpv`。

第一阶段的 `vehicle_type` 不是具体品牌型号，而是洗车策略所需的大类。

阶段 1.4 中，即使 YOLO 检测到车辆，`vehicle_type` 仍然输出 `unknown`。这是因为当前只验证车辆存在检测，车型大类分类尚未启用。

阶段 1.8 中，`classify` 模式会输出真实三分类推理结果。当前分类模型仍是小样本 demo，MPV/SUV 边界可能误判。

## aicar_sim 职责

`aicar_sim` 是主仿真框架。

它负责：

- 不训练模型。
- 不直接识别图片。
- 只读取 `vehicle_type_lab` 输出的 JSON。
- 根据 `vehicle_type` 选择 `data\vehicles` 下对应的 `sedan.json` / `suv.json` / `mpv.json`。

如果未检测到车辆，或 `vehicle_type` 为 `unknown`，当前默认回退到 `suv.json`，方便后续仿真流程继续推进。

阶段 1.9 中，`aicar_sim` 会加载解析到的车辆模型 JSON，并读取 `length_mm`、`width_mm`、`height_mm` 和 `wash_profile`，用于后续仿真链路占位。当前这些车辆模型参数是 mock 仿真参数，不代表真实车辆精确尺寸。

## 标准输出文件路径

```text
vehicle_type_lab\outputs\predictions\vehicle_type_result.json
```

## 标准字段

| Field | Type | Description |
| --- | --- | --- |
| `vehicle_detected` | bool | 是否检测到车辆。 |
| `vehicle_type` | string | 允许值：`sedan` / `suv` / `mpv` / `unknown`。 |
| `confidence` | float | 置信度，范围 `0.0` 到 `1.0`。 |
| `bbox` | array | 图片坐标 `[x1, y1, x2, y2]`，允许为空数组。 |
| `source_image` | string | 输入图片路径或名称。 |
| `image_width` | int | 图片宽度。mock 阶段可使用占位值。 |
| `image_height` | int | 图片高度。mock 阶段可使用占位值。 |
| `model_name` | string | 模型名称。mock 阶段使用 `mock_vehicle_type_classifier`。 |
| `model_version` | string | 模型版本。mock 阶段使用 `0.1.0-mock`。 |
| `timestamp` | string | ISO 格式时间戳。 |
| `notes` | string | 备注。 |

## Classify 模式可选字段

阶段 1.8 的 `classify` 模式会额外输出以下字段。`aicar_sim` 当前仍只依赖标准字段中的 `vehicle_type`，这些字段用于调试和追踪推理流程。

| Field | Type | Description |
| --- | --- | --- |
| `detection_confidence` | float | YOLO 车辆检测框置信度。 |
| `classification_confidence` | float | 三分类模型 top-1 置信度。 |
| `detector_model_name` | string | 检测模型名称，例如 `yolo11n.pt`。 |
| `classifier_model_name` | string | 分类模型文件名，例如 `best.pt`。 |
| `classifier_model_path` | string | 分类模型路径。 |
| `crop_path` | string | 检测框裁切图路径。 |
| `pipeline_mode` | string | 当前为 `classify`。 |

## Example

```json
{
  "vehicle_detected": true,
  "vehicle_type": "suv",
  "confidence": 0.9,
  "bbox": [120, 80, 1180, 760],
  "source_image": "mock_image.jpg",
  "image_width": 1280,
  "image_height": 720,
  "model_name": "mock_vehicle_type_classifier",
  "model_version": "0.1.0-mock",
  "timestamp": "2026-06-24T10:00:00+08:00",
  "notes": "Mock result for interface testing only."
}
```
