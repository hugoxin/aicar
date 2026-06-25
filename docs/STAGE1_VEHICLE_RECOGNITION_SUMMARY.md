# 阶段1：车辆识别小闭环总结

## 1. 阶段定位

阶段1的目标不是完成完整无人洗车系统，而是先完成“车辆识别小闭环”。

本阶段要解决的问题是：

1. 能从一张真实车辆图片中检测到车辆。
2. 能根据检测框裁切出车辆区域。
3. 能训练一个本地小样本车型三分类模型。
4. 能输出 `sedan` / `suv` / `mpv` / `unknown` 车型分类结果。
5. 能将分类结果通过 JSON 交给 `aicar_sim`。
6. `aicar_sim` 能根据车型选择对应车辆模型和 `wash_profile`。

阶段1完成后，项目从“能看见车”推进到“能识别车，并把识别结果交给仿真系统使用”。

## 2. 最终链路

当前阶段1已经打通完整链路：

```text
test_car.jpg
  -> YOLO 检测车辆 bbox
  -> crop 裁切车辆区域
  -> best.pt 三分类模型推理
  -> vehicle_type_result.json
  -> aicar_sim 读取 JSON
  -> 选择车辆模型
  -> 输出车辆尺寸与 wash_profile
```

当前主命令：

```powershell
python vehicle_type_lab\src\vehicle_type_lab\main.py --mode classify --image vehicle_type_lab\data\input_images\test_car.jpg --save-history
python aicar_sim\src\aicar_sim\main.py --vehicle-type-result vehicle_type_lab\outputs\predictions\vehicle_type_result.json
```

## 3. 分阶段过程

### 阶段1.1：JSON 接口

定义了 `vehicle_type_lab` 到 `aicar_sim` 的标准 JSON 接口。

标准输出文件：

```text
vehicle_type_lab\outputs\predictions\vehicle_type_result.json
```

核心字段包括：

- `vehicle_detected`
- `vehicle_type`
- `confidence`
- `bbox`
- `source_image`
- `image_width`
- `image_height`
- `model_name`
- `model_version`
- `timestamp`
- `notes`

阶段1.8 之后，`classify` 模式额外包含：

- `detection_confidence`
- `classification_confidence`
- `detector_model_name`
- `classifier_model_name`
- `classifier_model_path`
- `crop_path`
- `pipeline_mode`

### 阶段1.2：图片输入流程

建立了最小图片输入流程，`vehicle_type_lab` 可以接收本地图片路径。

测试图片路径：

```text
vehicle_type_lab\data\input_images\test_car.jpg
```

如果图片不存在，流程会优雅输出 `unknown`，不会崩溃。

### 阶段1.3：真实图片尺寸读取

验证了真实本地图片尺寸读取流程。

当前 `test_car.jpg` 尺寸：

```text
image_width: 449
image_height: 438
```

### 阶段1.4：YOLO 车辆检测

加入现成 YOLO 检测能力，只检测车辆存在，不做车型三分类。

检测模型：

```text
yolo11n.pt
```

当前检测结果：

```text
vehicle_detected: true
detection_confidence: 0.8791555762290955
bbox: [42, 142, 434, 365]
```

检测可视化输出：

```text
vehicle_type_lab\outputs\predictions\visualized\test_car_detected.jpg
```

此阶段完成后，系统能判断“车在哪里”，但 `vehicle_type` 仍为 `unknown`。

### 阶段1.5：三分类数据规范

建立 `sedan` / `suv` / `mpv` 三分类数据目录与标签规范。

核心目录：

```text
vehicle_type_lab\data\datasets\vehicle_type_classification
├─ incoming
├─ raw
├─ split
├─ review
└─ manifests
```

目录含义：

- `incoming`：人工放入的原始图片池。
- `raw`：标准化后的训练准备图片。
- `split`：训练集和验证集。
- `review`：人工质检 contact sheet。
- `manifests`：处理报告和数据清单。

同时定义了类别说明、命名规则、manifest 模板和数据集检查脚本。

### 阶段1.5.R：图片补齐与重建

用户多轮补齐和替换原始图片后，三类样本达到每类 20 张。

当前数据量：

```text
incoming/sedan: 20
incoming/suv: 20
incoming/mpv: 20

raw/sedan: 20
raw/suv: 20
raw/mpv: 20
```

预处理报告：

```text
preprocess_report.csv
ok: 60
skipped: 0
error: 0
method: yolo_crop 60
```

标准化输出为 `640x640` JPG，流程为：

```text
incoming 原图
  -> YOLO 辅助检测车辆框
  -> 裁切车辆区域
  -> letterbox / resize
  -> raw 标准化图片
```

### 阶段1.6：train / val 自动切分

将 `raw` 中每类 20 张图片按 80/20 自动切分。

当前结果：

```text
split/train/sedan: 16
split/train/suv: 16
split/train/mpv: 16

split/val/sedan: 4
split/val/suv: 4
split/val/mpv: 4
```

生成：

```text
vehicle_type_lab\data\datasets\vehicle_type_classification\manifests\split_manifest.csv
```

### 阶段1.6.1：split 人工质检

生成 `split/train` 和 `split/val` 的 contact sheet，辅助训练前人工检查。

输出：

```text
vehicle_type_lab\data\datasets\vehicle_type_classification\review\split_train_sedan.jpg
vehicle_type_lab\data\datasets\vehicle_type_classification\review\split_train_suv.jpg
vehicle_type_lab\data\datasets\vehicle_type_classification\review\split_train_mpv.jpg
vehicle_type_lab\data\datasets\vehicle_type_classification\review\split_val_sedan.jpg
vehicle_type_lab\data\datasets\vehicle_type_classification\review\split_val_suv.jpg
vehicle_type_lab\data\datasets\vehicle_type_classification\review\split_val_mpv.jpg
```

### 阶段1.7：三分类小模型训练

使用 Ultralytics classification 训练 `sedan` / `suv` / `mpv` 三分类小模型。

训练参数：

```text
model: yolo11n-cls.pt
epochs: 20
imgsz: 224
batch: 8
device: cpu
```

模型输出：

```text
vehicle_type_lab\models\vehicle_type_classifier\best.pt
```

当前训练验证结果：

```text
validation samples: 12
overall accuracy: 0.8333
sedan accuracy: 1.0000
suv accuracy: 1.0000
mpv accuracy: 0.5000
```

### 阶段1.7.R：坏样本替换后重训

发现 `mpv_local_0004.jpg` 裁切不好后，用户替换了 `incoming/mpv` 中对应原图。

重训流程：

```text
替换 incoming 原图
  -> 全量重建 raw
  -> 全量重建 split
  -> 重新生成 contact sheet
  -> 重新训练
  -> 重新 eval
```

重训后结果：

```text
overall accuracy: 0.8333
sedan accuracy: 1.0000
suv accuracy: 1.0000
mpv accuracy: 0.5000
```

新误判：

```text
mpv_local_0007.jpg: true=mpv, pred=suv
mpv_local_0011.jpg: true=mpv, pred=sedan
```

结论：坏裁切样本替换有效，但整体准确率未提升。当前主要瓶颈是 MPV/SUV 边界与小样本数据量。

### 阶段1.8：检测 + 裁切 + 分类推理

`vehicle_type_lab` 新增：

```text
--mode classify
```

推理流程：

```text
YOLO 检测车辆 bbox
  -> crop 裁切车辆区域
  -> best.pt 分类
  -> 输出 sedan / suv / mpv / unknown
```

当前 `test_car.jpg` classify 结果：

```text
vehicle_detected: true
vehicle_type: sedan
detection_confidence: 0.8791555762290955
classification_confidence: 0.666374683380127
bbox: [42, 142, 434, 365]
pipeline_mode: classify
```

输出文件：

```text
vehicle_type_lab\outputs\predictions\vehicle_type_result.json
vehicle_type_lab\outputs\predictions\crops\test_car_crop.jpg
vehicle_type_lab\outputs\predictions\visualized\test_car_classified.jpg
```

### 阶段1.9：aicar_sim 消费识别结果

`aicar_sim` 正式读取：

```text
vehicle_type_lab\outputs\predictions\vehicle_type_result.json
```

并根据 `vehicle_type` 选择车辆模型：

```text
sedan -> aicar_sim\data\vehicles\sedan.json
suv -> aicar_sim\data\vehicles\suv.json
mpv -> aicar_sim\data\vehicles\mpv.json
unknown -> aicar_sim\data\vehicles\suv.json fallback
```

当前 fixture 检查通过：

```text
PASS sedan -> sedan.json
PASS suv -> suv.json
PASS mpv -> mpv.json
PASS unknown -> suv.json fallback
```

## 4. 当前最终结果

当前 `test_car.jpg` 最终输出：

```text
vehicle_type: sedan
detection_confidence: 0.8791555762290955
classification_confidence: 0.666374683380127
bbox: [42, 142, 434, 365]
```

`aicar_sim` 解析结果：

```text
resolved model: aicar_sim\data\vehicles\sedan.json
sedan dimensions: 4700 x 1800 x 1450 mm
wash_profile: standard_sedan
```

## 5. 当前训练结果

当前三分类模型验证结果：

```text
overall accuracy: 0.8333
sedan accuracy: 1.0000
suv accuracy: 1.0000
mpv accuracy: 0.5000
```

模型路径：

```text
vehicle_type_lab\models\vehicle_type_classifier\best.pt
```

训练和评估报告：

```text
vehicle_type_lab\outputs\training\vehicle_type_classifier\reports\train_summary.md
vehicle_type_lab\outputs\training\vehicle_type_classifier\reports\eval_summary.md
vehicle_type_lab\outputs\training\vehicle_type_classifier\reports\val_predictions.csv
vehicle_type_lab\outputs\training\vehicle_type_classifier\reports\retrain_notes.md
```

## 6. 当前限制

阶段1只是车辆识别小闭环 demo，不是商业级车型识别系统。

当前限制：

- 每类只有 20 张样本，总计 60 张。
- MPV/SUV 仍然容易混淆。
- 当前模型只是 demo，不代表商业精度。
- 当前车辆尺寸是 mock 参数，不代表真实车辆精确尺寸。
- 当前 `wash_profile` 只是策略标签，还没有生成真实洗车路径。
- 当前尚未进入洗车路径规划。
- 当前没有接入视频流、摄像头、PLC 或真实硬件。
- 当前没有启动 pygame 仿真。

当前模型的价值是证明：

```text
图片输入 -> 车辆检测 -> 车辆裁切 -> 车型分类 -> JSON 输出 -> aicar_sim 车辆模型选择
```

这条链路已经跑通。

## 7. 阶段1冻结结论

阶段1可以冻结为稳定识别模块。

冻结状态：

```text
阶段1：车辆识别小闭环
状态：已完成，可冻结
项目路径：F:\aicar
```

阶段1最终能力：

1. 支持真实图片输入。
2. 支持 YOLO 车辆检测。
3. 支持车辆框裁切。
4. 支持 `sedan` / `suv` / `mpv` 三分类推理。
5. 支持输出标准 `vehicle_type_result.json`。
6. 支持 history 保存。
7. 支持检测/分类可视化输出。
8. 支持 `aicar_sim` 读取车型结果。
9. 支持 `sedan` / `suv` / `mpv` / `unknown` 车辆模型选择。
10. 支持 `unknown` fallback 到 `suv`。

阶段1冻结后，后续阶段2再进入：

```text
洗车策略与喷嘴路径仿真
```

当前不开始阶段2。
