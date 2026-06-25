# AICAR Sim Vehicle Model Selection

## Stage 1.9 Goal

Stage 1.9 lets `aicar_sim` formally consume the `sedan` / `suv` / `mpv`
classification result produced by `vehicle_type_lab`.

The pipeline is:

```text
vehicle_type_lab vehicle_type_result.json
  -> aicar_sim reads vehicle_type
  -> select aicar_sim\data\vehicles\<vehicle_type>.json
  -> load mock dimensions and wash_profile
```

This is only the vehicle model selection loop. It is not final wash path
planning, nozzle trajectory control, hardware control, or pygame simulation.
Those belong to later phase 2 work.

## Responsibilities

`vehicle_type_lab` is responsible for detecting and classifying the vehicle
image. In classify mode it may output:

- `sedan`
- `suv`
- `mpv`
- `unknown`

`aicar_sim` is responsible for reading that JSON and selecting the matching
vehicle model file from:

```text
aicar_sim\data\vehicles
```

## Vehicle Model Files

Current phase 1.9 model files are mock simulation parameters:

- `sedan.json`: standard sedan dimensions and `standard_sedan`
- `suv.json`: standard SUV dimensions and `standard_suv`
- `mpv.json`: standard MPV dimensions and `standard_mpv`

These dimensions are not precise real-world vehicle specifications.

## Fallback Rule

If `vehicle_detected=false`, or `vehicle_type=unknown`, `aicar_sim` falls back
to:

```text
aicar_sim\data\vehicles\suv.json
```

The fallback keeps the simulation-side chain moving while upstream confidence
and data quality improve.

## Commands

Read the current `vehicle_type_lab` output:

```powershell
python aicar_sim\src\aicar_sim\main.py --vehicle-type-result vehicle_type_lab\outputs\predictions\vehicle_type_result.json
```

Check the current live result:

```powershell
python aicar_sim\scripts\check_vehicle_model_selection.py
```

Check all fixture cases:

```powershell
python aicar_sim\scripts\check_all_vehicle_model_selection.py
```

## Next Boundary

Stage 1.9 does not start phase 2. Phase 2 can use the selected vehicle
dimensions and `wash_profile` as inputs for path planning and washing process
simulation.
