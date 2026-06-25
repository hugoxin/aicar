# Vehicle Type Classifier Training Summary

- Stage: 1.7
- Training time: 2026-06-25T10:50:15
- Data path: `F:\aicar\vehicle_type_lab\data\datasets\vehicle_type_classification\split`
- Classes: sedan, suv, mpv

## Counts

- train/sedan: 16
- train/suv: 16
- train/mpv: 16
- val/sedan: 4
- val/suv: 4
- val/mpv: 4

## Parameters

- Model: `yolo11n-cls.pt`
- Epochs: 20
- Image size: 224
- Batch: 8
- Device: `cpu`

## Outputs

- Training output directory: `F:\aicar\vehicle_type_lab\outputs\training\vehicle_type_classifier\runs\yolo11n_cls_sedan_suv_mpv`
- best.pt original path: `F:\aicar\vehicle_type_lab\outputs\training\vehicle_type_classifier\runs\yolo11n_cls_sedan_suv_mpv\weights\best.pt`
- last.pt original path: `F:\aicar\vehicle_type_lab\outputs\training\vehicle_type_classifier\runs\yolo11n_cls_sedan_suv_mpv\weights\last.pt`
- best.pt copied path: `F:\aicar\vehicle_type_lab\models\vehicle_type_classifier\best.pt`

## Notes

Current data has only 20 images per class. This result is for pipeline validation only and does not represent commercial accuracy.
