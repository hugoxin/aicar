# Vehicle Type Classify Pipeline

## Stage 1.8 Goal

Stage 1.8 verifies the local inference pipeline inside `vehicle_type_lab`:

```text
input image
  -> YOLO vehicle detection
  -> crop vehicle bbox with margin
  -> vehicle type classifier best.pt
  -> vehicle_type_result.json
  -> crop and visualization outputs
```

This stage only validates the inference connection. It does not train a new
model, download datasets, download images, connect hardware, or start any
simulation.

## Modes

`mock` mode creates mock `sedan` / `suv` / `mpv` / `unknown` JSON results.

`detect` mode only detects vehicle presence with YOLO. It keeps
`vehicle_type=unknown` because sedan / suv / mpv classification is not enabled
in that mode.

`classify` mode runs YOLO detection first, crops the detected vehicle bbox, and
then runs `vehicle_type_lab\models\vehicle_type_classifier\best.pt` to predict
`sedan`, `suv`, or `mpv`.

## Commands

```powershell
python vehicle_type_lab\src\vehicle_type_lab\main.py --mode classify --image vehicle_type_lab\data\input_images\test_car.jpg --save-history
```

```powershell
python vehicle_type_lab\scripts\check_vehicle_type_classify.py
```

## Outputs

Main JSON output:

```text
vehicle_type_lab\outputs\predictions\vehicle_type_result.json
```

Crop output:

```text
vehicle_type_lab\outputs\predictions\crops\test_car_crop.jpg
```

Classified visualization output:

```text
vehicle_type_lab\outputs\predictions\visualized\test_car_classified.jpg
```

## JSON Fields

The classify pipeline keeps the standard interface fields and adds optional
pipeline fields:

- `detection_confidence`
- `classification_confidence`
- `detector_model_name`
- `classifier_model_name`
- `classifier_model_path`
- `crop_path`
- `pipeline_mode`

The `confidence` field uses classification confidence when available. If
classification cannot run, it falls back to detection confidence or `0.0`.

## Accuracy Note

The current classifier is a small-sample demo model trained from 20 images per
class. MPV/SUV boundary cases may still be misclassified.

## Stage 1.9 Consumer

Stage 1.9 lets `aicar_sim` consume the classify JSON result. `aicar_sim` reads
`vehicle_type`, selects the corresponding file under `aicar_sim\data\vehicles`,
and loads mock dimensions plus `wash_profile`.

```powershell
python aicar_sim\src\aicar_sim\main.py --vehicle-type-result vehicle_type_lab\outputs\predictions\vehicle_type_result.json
```

If the result is `unknown` or no vehicle was detected, `aicar_sim` falls back to
`suv.json`.
