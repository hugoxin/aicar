# Stage4.6 CAD And Point-Cloud Boundaries

## Supported

- ASCII OBJ: `v`, `vn`, `f`, `g`, `o`, positive/negative indices, and fan triangulation.
- ASCII STL: `solid`, `facet normal`, `vertex`, and `endfacet`.
- ASCII PLY: `x y z`, optional `nx ny nz`, and optional `patch_id`.
- XYZ and CSV with positions, optional normals, and optional labels.
- Finite-value, empty, count-limit, index, degenerate-triangle, and duplicate-point checks.

Binary STL fails with `UNSUPPORTED_BINARY_STL`. Mesh input is tessellated triangles, not native parametric CAD.

## Not Supported

- Native STEP/IGES or SolidWorks assembly semantics.
- Manufacturer CAD downloads or restricted third-party models.
- ICP, SLAM, multi-view registration, camera/LiDAR calibration, or complex denoising.
- Real vehicle semantic segmentation or measured-body accuracy claims.

Demo OBJ/STL/PLY/XYZ/CSV files are generated locally from the analytic reference, carry explicit patch labels, and set `not_real_scan=true`. They only validate offline interfaces.

## Future Real Input

An authorized source must provide units, right-handed axes, origin, ground plane, complete extent, quality metadata, normal availability, semantic review, measured dimensions, provenance, licence, and tolerance. Large mismatch, missing patches, invalid normals, or unresolved coordinates must reject input instead of silently using analytic geometry.
