# Stage4.6 Demo Explanation

The demo generates small ASCII OBJ, STL, PLY, XYZ, and CSV fixtures from the analytic reference at runtime. Explicit labels preserve nine wash-surface semantics. The pipeline normalizes geometry to millimetres, applies a non-manufacturer-specific 4800 x 1880 x 1450 mm reference profile, estimates or validates outward normals, and creates candidate nozzle quaternions.

The frozen Stage4.5-R route semantics are retained. Geometry-aware points are returned to the existing motion, swept-AABB collision, shared-resource interlock, scheduling, and safe-stop chain.

This is an offline interface demonstration. It does not parse native STEP/IGES, use a real scan, solve robot inverse kinematics, calibrate sensors, or issue PLC/servo commands.
