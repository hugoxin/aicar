# Stage4.6 Geometry and Nozzle Pose Interface Plan

## Purpose

Stage4.6 places a unified `GeometrySource` boundary in front of the frozen Stage4.5-R route. Downstream path code consumes normalized points, triangles, normals, semantic patches, and bounding boxes rather than branching into separate OBJ, STL, PLY, or analytic planners.

Supported sources are `ANALYTIC_REFERENCE`, tessellated ASCII OBJ/STL `CAD_MESH`, and ASCII PLY/XYZ/CSV `POINT_CLOUD`. Native STEP/IGES and SolidWorks parsing are deferred; authorized production CAD must first be converted by an offline tessellation process. Runtime fixtures come from the analytic reference and are not real CAD or scans.

## Coordinate And Units

Output uses millimetres and a right-handed vehicle frame: origin `vehicle_center_floor`, +X toward vehicle right, +Y toward vehicle front, and +Z upward. Normalization handles unit conversion, XY centring, ground alignment, bounding boxes, and dimension cross-checking.

## Dimension Authority

`demo_reference_real_size_sedan_dimensions.json` replaces the Stage4.5 demo 4700 x 1800 x 1450 mm dimensions with a reference 4800 x 1880 x 1450 mm profile and updates wheelbase, tracks, wheel radius, wheel width, and ground clearance. This is not manufacturer, homologation, or production data.

`PROFILE_WITH_GEOMETRY_CROSS_CHECK` allows non-uniform scaling only for the analytic source. Mesh and point-cloud sources permit uniform scaling and reject large silent mismatches.

## Pipeline

```text
geometry source -> normalization and dimensions -> semantic mapping
-> outward normals -> nozzle pose and quaternion -> Stage4.5-R mapping
-> machine timing -> collision/interlock/schedule/safe-stop -> report
```

Nine semantic patches and four wheel patches are mandatory. Explicit labels are preferred. `DIMENSION_HEURISTIC` emits `HEURISTIC_SEMANTIC_SEGMENTATION` and is not AI segmentation.

Mapped routes retain state, zone, patch, nozzle, scan-pass, segment, and task semantics. CAD/cloud inputs use nearest samples in the matching patch; mapping distance is reported and no analytic fallback is hidden.

## Acceptance Boundary

Hard acceptance keeps seven states, six zones, nine patches, four wheel patches, monotonic timestamps, terminal zero speed, zero workspace/velocity/acceleration/collision/forbidden/unassigned/conflict/deadlock violations, at least three safe stops, and clearance at or above 250 mm.

Warnings remain because fixtures, reference dimensions, normals, actuator models, and swept AABBs are approximations. No PLC, servo, robot, SDK, camera, LiDAR, or hardware is connected.
