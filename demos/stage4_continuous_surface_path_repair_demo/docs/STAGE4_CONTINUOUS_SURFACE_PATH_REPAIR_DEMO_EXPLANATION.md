# Stage4.5-R Demo Explanation

## Purpose

The demo compares the frozen Stage4 baseline, the Stage4.5 first experiment, and the Stage4.5-R repair. It shows state-aware scan spacing, surface-route task aggregation, safe connection choices, motion validation, collision checks, actual shared-resource lock intervals, and schedule outcomes.

## Output boundary

The path is an offline candidate generated on a reference analytic surface. Coverage is a two-dimensional geometric estimate. The demo does not contain CAD or point-cloud reconstruction, real cleaning-effect validation, a globally optimal solver, PLC code, servo integration, device SDK calls, or real hardware control.

## Reading the result

An `ACCEPTED` result means the repaired candidate satisfies the configured coverage and frozen Stage4 safety gates while improving the selected engineering metrics. It does not certify a production machine trajectory.
