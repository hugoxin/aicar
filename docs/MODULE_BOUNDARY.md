# Module Boundary

## aicar_sim

`aicar_sim` 是主仿真框架，不直接训练模型，不下载数据集，不管理真实 AI 训练流程，也不直接识别图片。

它负责读取车辆识别结果，选择 sedan / SUV / MPV 的车辆模型和路径策略，并运行洗车流程仿真。当前通过 `src\aicar_sim\vehicle_type_input.py` 解析 `vehicle_type_lab` 输出的 JSON。

## vehicle_type_lab

`vehicle_type_lab` 是车辆识别小闭环，不直接控制洗车流程，不连接 PLC，不控制喷嘴、水泵或阀门。

它负责输出标准 JSON 识别结果。当前阶段只生成 mock 结果，不加载 YOLO，不下载模型，不训练模型。

## JSON Connection

未来两个子项目通过 JSON 结果连接。例如：

```text
vehicle_type_lab\outputs\predictions\vehicle_type_result.json
```

标准内容：

```json
{
  "vehicle_detected": true,
  "vehicle_type": "suv",
  "confidence": 0.9,
  "bbox": [120, 80, 1180, 700],
  "source_image": "mock_image.jpg",
  "image_width": 1280,
  "image_height": 720,
  "model_name": "mock_vehicle_type_classifier",
  "model_version": "0.1.0-mock",
  "timestamp": "2026-06-24T10:00:00+08:00",
  "notes": "Mock result for interface testing only."
}
```

`aicar_sim` 读取这个 JSON，选择 sedan / SUV / MPV 的车辆模型和路径策略。如果 `vehicle_detected` 为 `false` 或 `vehicle_type` 为 `unknown`，当前默认回退到 `suv.json`。

完整接口说明见 `docs\VEHICLE_TYPE_INTERFACE.md`。
