# Stage4.5 Continuous Surface Path Demo Explanation

The demo replaces the Stage2 sparse abstract source path with scans generated from nine analytic surface patches. It preserves wash-state order and zone/nozzle semantics, then reuses Stage4 motion, AABB collision, shared interlock, scheduling, and safe-stop validation.

The current result is `NO_MEANINGFUL_IMPROVEMENT`: transition count is lower, but path length and cycle time are worse because every reference surface is densely scanned in each required wash state. This result is intentionally reported rather than hidden.

The geometry, normals, coverage, machine parameters, and safety layout remain reference approximations. Nothing is sent to a PLC, servo, SDK, or real machine.
