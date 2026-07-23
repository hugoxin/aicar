# Stage4.6 Surface Normal And Nozzle Pose

## Normals

Input normals are normalized and oriented away from the vehicle reference centre. Missing point-cloud normals use a readable patch-local demo estimator. Reports include input, estimated, fallback, flipped, invalid, neighbour-difference, and unresolved-flip counts. Zero or non-finite normals fail.

## Pose Frame

```text
nozzle_position = surface_point + outward_normal * preferred_standoff
```

Preferred standoff is 350 mm, hard minimum 250 mm, and maximum 650 mm. Nozzle local `-Z` points toward the surface, so local `+Z` aligns with the outward normal. A tangent basis completes a right-handed frame and is converted to a normalized quaternion.

Quaternion signs remain continuous. Non-boundary orientation steps must not exceed 12 degrees; explicit patch/state/reposition boundaries remain marked. Incidence must not exceed 15 degrees. Tangent or roll smoothing may not violate incidence.

## Stage4.5 Adaptation And Safety

Stage4.5-R scan semantics remain. Process points map to the target patch while route-switch and state-boundary waypoints keep frozen safety topology. Machine points are regenerated with the reference tool offset and lower workspace limit. The full motion, swept-AABB collision, forbidden-zone, shared-resource interlock, schedule, and safe-stop chain reruns against the 4800 x 1880 x 1450 mm envelope.

Poses are geometric candidates, not robot inverse kinematics. There are no wrist limits, hose torsion, calibrated dynamics, PLC output, servo command, or safety certification.
