# Vehicle Type Split Review

阶段 1.6.1 是训练前人工质检辅助。

当前不训练模型，不移动图片，不删除图片。

## Review Goal

生成 split/train 和 split/val 的 contact sheet 总览图，帮助人工检查：

- train / val 中是否错类。
- 是否有裁切坏图。
- 是否有只拍车头、车尾、局部的图。
- 是否有多辆车混乱。
- 是否有过度模糊图。
- val 中图片是否能代表该类别。

## Command

```powershell
python vehicle_type_lab\scripts\make_vehicle_type_split_contact_sheets.py
```

输出目录：

```text
vehicle_type_lab\data\datasets\vehicle_type_classification\review
```

生成文件：

```text
split_train_sedan.jpg
split_train_suv.jpg
split_train_mpv.jpg
split_val_sedan.jpg
split_val_suv.jpg
split_val_mpv.jpg
```

## If Problems Are Found

如果发现错类、裁切坏图、局部图、多车图或严重模糊图，不要直接在 split 里手动修修补补。

正确流程：

1. 回到 `incoming` 中替换或删除原图。
2. 重新标准化：

```powershell
python vehicle_type_lab\scripts\prepare_vehicle_type_images.py --use-yolo-crop --clean-output
```

3. 重新切分：

```powershell
python vehicle_type_lab\scripts\split_vehicle_type_dataset.py --clean-split
```

4. 重新生成 contact sheet：

```powershell
python vehicle_type_lab\scripts\make_vehicle_type_split_contact_sheets.py
```

人工确认 contact sheet 可用后，阶段 1.7 才进入小模型训练：

```powershell
python vehicle_type_lab\scripts\train_vehicle_type_classifier.py --copy-best
```
