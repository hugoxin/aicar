# Vehicle Type Classifier Retrain Notes

- Stage: 1.7.R
- Retrain time: 2026-06-25T10:50:30
- Reason: `mpv_local_0004.jpg` had a bad crop in the previous round. The user replaced the source image in `incoming/mpv`.
- Kept difficult sample: `mpv_local_0007.jpg` remains a real MPV sample and is kept as a hard MPV/SUV boundary case.
- Scope: rebuild `raw`, rebuild `split/train` and `split/val`, regenerate split contact sheets, retrain the classifier, and rerun eval.
- Main flow note: the classifier is not connected to `vehicle_type_result.json` yet, and `aicar_sim` was not changed.

## Raw Rebuild

- incoming/sedan: 20
- incoming/suv: 20
- incoming/mpv: 20
- raw/sedan: 20
- raw/suv: 20
- raw/mpv: 20
- preprocess status: ok=60, skipped=0, error=0
- preprocess method: yolo_crop=60
- preprocess report: `F:\aicar\vehicle_type_lab\data\datasets\vehicle_type_classification\manifests\preprocess_report.csv`

## Split Rebuild

- train/sedan: 16
- val/sedan: 4
- train/suv: 16
- val/suv: 4
- train/mpv: 16
- val/mpv: 4
- split manifest: `F:\aicar\vehicle_type_lab\data\datasets\vehicle_type_classification\manifests\split_manifest.csv`

## Training Result

- Training output directory: `F:\aicar\vehicle_type_lab\outputs\training\vehicle_type_classifier\runs\yolo11n_cls_sedan_suv_mpv`
- best.pt original path: `F:\aicar\vehicle_type_lab\outputs\training\vehicle_type_classifier\runs\yolo11n_cls_sedan_suv_mpv\weights\best.pt`
- best.pt copied path: `F:\aicar\vehicle_type_lab\models\vehicle_type_classifier\best.pt`
- best.pt size: 3,188,866 bytes
- training report: `F:\aicar\vehicle_type_lab\outputs\training\vehicle_type_classifier\reports\train_summary.md`

## Eval Result

- Validation samples: 12
- Overall accuracy: 0.8333
- sedan accuracy: 1.0000
- suv accuracy: 1.0000
- mpv accuracy: 0.5000
- eval report: `F:\aicar\vehicle_type_lab\outputs\training\vehicle_type_classifier\reports\eval_summary.md`
- prediction report: `F:\aicar\vehicle_type_lab\outputs\training\vehicle_type_classifier\reports\val_predictions.csv`

## Misclassifications

- `mpv_local_0007.jpg`: true=mpv, pred=suv, confidence=0.847209
- `mpv_local_0011.jpg`: true=mpv, pred=sedan, confidence=0.612926

## Comparison With Previous Round

- Previous overall accuracy: 0.8333
- New overall accuracy: 0.8333
- Overall accuracy improved: no
- Previous mpv accuracy: 0.5000
- New mpv accuracy: 0.5000
- mpv accuracy improved: no
- `mpv_local_0004.jpg` is still misclassified: no
- `mpv_local_0007.jpg` is still misclassified: yes

## Recommendation

The pipeline is healthy enough to proceed to phase 1.8 if this small-sample demo result is acceptable, but the model is still based on only 20 images per class and does not represent commercial accuracy. Before relying on it in production, expand and review more MPV samples, especially MPV/SUV boundary cases.
