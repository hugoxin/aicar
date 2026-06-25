# Input Images

This directory is reserved for images waiting to be classified by `vehicle_type_lab`.

Current phase:

- You may manually place a small test image here, such as `test_car.jpg` or `test_car.png`.
- Do not store large image collections in this project directory.
- Do not download images automatically.
- The current phase only reads image dimensions and does not perform real recognition.
- The current CLI still uses `--mock-type` to choose a mock `sedan` / `suv` / `mpv` / `unknown` result.

Example:

```powershell
python vehicle_type_lab\src\vehicle_type_lab\main.py --image vehicle_type_lab\data\input_images\test_car.jpg --mock-type suv --save-history
```

Check whether a local `test_car.jpg` exists and can be read:

```powershell
python vehicle_type_lab\scripts\check_image_input.py
```
