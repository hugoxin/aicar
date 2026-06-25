# 阶段1车辆识别可视化 Demo 说明

## 当前已经完成什么

阶段1已经完成车辆识别小闭环：从一张本地车辆图片出发，先检测车辆位置，再裁切车辆区域，随后使用小样本三分类模型输出 `sedan` / `suv` / `mpv` / `unknown`，最后由 `aicar_sim` 读取结果并选择对应车辆模型和 `wash_profile`。

## 一张车辆图片经过哪些步骤

```text
车辆图片
  -> YOLO 车辆检测
  -> 车辆区域 crop
  -> best.pt 三分类推理
  -> vehicle_type_result.json
  -> aicar_sim 车辆模型
  -> wash_profile
  -> HTML Demo 报告
```

## 输出结果代表什么

- `vehicle_detected`：是否检测到车辆。
- `vehicle_type`：当前识别到的车辆大类，支持 `sedan` / `suv` / `mpv` / `unknown`。
- `bbox`：检测框坐标，格式为 `[x1, y1, x2, y2]`。
- `wash_profile`：当前车型对应的洗车策略占位配置。

## confidence 的含义

`detection_confidence` 表示 YOLO 对车辆检测框的置信度。它回答的是“图里这里是不是车辆”。

`classification_confidence` 表示三分类模型对 `sedan` / `suv` / `mpv` 类别判断的置信度。它回答的是“裁切出来的车辆更像哪一类”。

## sedan / suv / mpv 如何影响后续洗车策略

阶段1输出的车型大类会影响后续洗车策略选择。例如 sedan、suv、mpv 的车身长度、高度和默认 `wash_profile` 不同，阶段2可以在此基础上生成更贴合车身外形的喷嘴路径和流程仿真。

## 当前限制

- 当前模型是小样本模型。
- MPV/SUV 仍可能混淆。
- 当前结果不代表商业级精度。
- 当前车辆尺寸是 mock 参数。
- 当前还没有进入真实洗车路径规划。

## 后续阶段2会做什么

- 根据车辆尺寸生成洗车策略。
- 生成喷嘴路径。
- 做洗车流程仿真。

