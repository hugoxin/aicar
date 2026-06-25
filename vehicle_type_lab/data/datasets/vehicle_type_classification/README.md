# Vehicle Type Classification Dataset

This directory is reserved for sedan / suv / mpv classification data.

## Directory Roles

- `incoming`: user-collected original images that may have inconsistent size, naming, crop, and extension.
- `raw`: standardized training-ready JPG images produced by `prepare_vehicle_type_images.py`.
- `split/train`: training split prepared from standardized raw images.
- `split/val`: validation split prepared from standardized raw images.
- `manifests`: CSV templates and future dataset index files.

## Current Scope

Current phase:

- Do not download datasets.
- Do not train models.
- Do not commit real training images to git.
- Do not put messy original images directly into `raw`.
- Standardized output is JPG, default `640x640`.
- Supported incoming formats: `jpg`, `jpeg`, `png`, `webp`, `bmp`.
- Unreadable or unsupported images should be skipped and recorded in the preprocess report.
- Define class, naming, manifest, and preprocessing standards first.

Future data can be organized from:

- local manually collected images
- small public dataset samples after license review
- self-collected car wash scene images

`vehicle_type_lab\data\input_images` is only for single-image detection tests. It is not the training dataset.

## Standardization Flow

1. Put original images into `incoming\sedan`, `incoming\suv`, or `incoming\mpv`.
2. Run:

```powershell
python vehicle_type_lab\scripts\prepare_vehicle_type_images.py
```

3. Standardized JPG images are written into `raw\sedan`, `raw\suv`, or `raw\mpv`.
4. A report is written to `manifests\preprocess_report.csv`.

Optional YOLO-assisted crop:

```powershell
python vehicle_type_lab\scripts\prepare_vehicle_type_images.py --use-yolo-crop
```

YOLO crop only helps center the vehicle. It is not sedan / suv / mpv classification.

## Rebuild Raw After Adding More Incoming Images

After adding or cleaning images in `incoming`, rebuild `raw`:

```powershell
python vehicle_type_lab\scripts\prepare_vehicle_type_images.py --dry-run
python vehicle_type_lab\scripts\prepare_vehicle_type_images.py --use-yolo-crop --clean-output
python vehicle_type_lab\scripts\check_vehicle_type_dataset.py
```

`--clean-output` removes only old standardized images in `raw` and the old `manifests\preprocess_report.csv`.

It does not delete `incoming` originals, `input_images\test_car.jpg`, `yolo11n.pt`, or anything under `split`.
