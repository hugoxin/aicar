# vehicle_type_lab

`vehicle_type_lab` 是 AI 智能无人洗车项目的车辆识别小闭环。

后续目标是识别：

- sedan
- SUV
- MPV

当前阶段只搭框架，不训练模型，不下载数据集，不实现复杂 AI。后续它会输出标准 JSON，供 `aicar_sim` 读取。

当前已建立 `vehicle_type_lab` -> `aicar_sim` 的 JSON 接口：

- Schema: `schemas\vehicle_type_result.schema.json`
- Examples: `examples\result_sedan.json`、`examples\result_suv.json`、`examples\result_mpv.json`、`examples\result_unknown.json`
- Output: `outputs\predictions\vehicle_type_result.json`

当前只生成 mock 结果，不加载 YOLO，不下载模型。

图片输入流程已预留：CLI 可以接收 `--image`，读取图片尺寸，然后仍然用 `--mock-type` 生成结果。如果图片不存在，程序会输出 `unknown`，并在 `notes` 中说明原因。

阶段 1.4 增加了 YOLO 车辆检测模式：`--mode detect` 会检测图片中是否存在 car / truck / bus，但仍不做 sedan / SUV / MPV 分类训练。检测到车辆时，`vehicle_detected=true`，`vehicle_type` 仍为 `unknown`。

阶段 1.5 增加了三分类数据规范：

- Dataset root: `data\datasets\vehicle_type_classification`
- Classes: `sedan` / `suv` / `mpv`
- Documents: `CLASS_DEFINITION.md`、`NAMING_RULES.md`
- Manifest template: `manifests\dataset_manifest_template.csv`
- Check script: `scripts\check_vehicle_type_dataset.py`

当前只准备数据目录和规范，不训练模型，不下载数据集。

阶段 1.5.1-1.5.3 增加了原始图片归档和标准化预处理：

- Put original images into `data\datasets\vehicle_type_classification\incoming`
- Run `scripts\prepare_vehicle_type_images.py`
- Standardized `640x640` JPG output goes to `data\datasets\vehicle_type_classification\raw`
- Preprocess report goes to `manifests\preprocess_report.csv`

阶段 1.5.R 增加了 raw 重建流程：补齐或清理 incoming 后，可以用 `--clean-output` 清空旧 raw 图片和旧报告，再重新生成标准化图片。该参数不会删除 incoming 原图。

阶段 1.6 增加了 train / val 自动切分：

- Source: `data\datasets\vehicle_type_classification\raw`
- Output: `data\datasets\vehicle_type_classification\split\train` and `split\val`
- Manifest: `data\datasets\vehicle_type_classification\manifests\split_manifest.csv`
- Default ratio: 80/20
- Current scope: copy files only, no training

阶段 1.6.1 增加了 split 人工质检辅助：

- Review root: `data\datasets\vehicle_type_classification\review`
- Script: `scripts\make_vehicle_type_split_contact_sheets.py`
- Output: one contact sheet per split/class
- Current scope: review images only, no training

阶段 1.7 增加了三分类小模型训练：

- Train script: `scripts\train_vehicle_type_classifier.py`
- Eval script: `scripts\eval_vehicle_type_classifier.py`
- Model output: `models\vehicle_type_classifier\best.pt`
- Reports: `outputs\training\vehicle_type_classifier\reports`
- Current scope: train and validate only; no integration into `vehicle_type_result.json`

阶段 1.8 增加了 YOLO 检测框 + 三分类模型推理接入验证：

- Classify mode: `src\vehicle_type_lab\main.py --mode classify`
- Detector: `yolo11n.pt`
- Classifier: `models\vehicle_type_classifier\best.pt`
- Crop output: `outputs\predictions\crops`
- Visualization output: `outputs\predictions\visualized`
- Check script: `scripts\check_vehicle_type_classify.py`
- Current scope: inference validation only; no new training and no `aicar_sim` logic changes

运行 scaffold：

```powershell
python vehicle_type_lab\src\vehicle_type_lab\main.py
```

生成 mock 结果：

```powershell
python vehicle_type_lab\src\vehicle_type_lab\main.py --mock-type suv
```

显式 mock 模式：

```powershell
python vehicle_type_lab\src\vehicle_type_lab\main.py --mode mock --mock-type suv
```

带图片路径生成 mock 结果：

```powershell
python vehicle_type_lab\src\vehicle_type_lab\main.py --image vehicle_type_lab\data\input_images\test_car.jpg --mock-type suv --save-history
```

YOLO 检测模式：

```powershell
python vehicle_type_lab\src\vehicle_type_lab\main.py --mode detect --image vehicle_type_lab\data\input_images\test_car.jpg --save-history
```

检查接口：

```powershell
python vehicle_type_lab\scripts\check_interface.py
```

检查 YOLO 检测入口：

```powershell
python vehicle_type_lab\scripts\check_yolo_detect.py
```

检查三分类数据目录：

```powershell
python vehicle_type_lab\scripts\check_vehicle_type_dataset.py
```

标准化 incoming 原始图片：

```powershell
python vehicle_type_lab\scripts\prepare_vehicle_type_images.py --dry-run
python vehicle_type_lab\scripts\prepare_vehicle_type_images.py --use-yolo-crop
```

重建 raw 标准化图片：

```powershell
python vehicle_type_lab\scripts\prepare_vehicle_type_images.py --use-yolo-crop --clean-output
```

切分 train / val：

```powershell
python vehicle_type_lab\scripts\split_vehicle_type_dataset.py --dry-run
python vehicle_type_lab\scripts\split_vehicle_type_dataset.py --clean-split
```

生成 split contact sheet：

```powershell
python vehicle_type_lab\scripts\make_vehicle_type_split_contact_sheets.py
```

训练和验证三分类小模型：

```powershell
python vehicle_type_lab\scripts\train_vehicle_type_classifier.py --dry-run
python vehicle_type_lab\scripts\train_vehicle_type_classifier.py --copy-best
python vehicle_type_lab\scripts\eval_vehicle_type_classifier.py --save-report
```

检测 + 裁切 + 三分类推理：

```powershell
python vehicle_type_lab\src\vehicle_type_lab\main.py --mode classify --image vehicle_type_lab\data\input_images\test_car.jpg --save-history
python vehicle_type_lab\scripts\check_vehicle_type_classify.py
```
