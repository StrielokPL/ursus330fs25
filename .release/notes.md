## Ursus C-330 / C-330M 0.0.1.1

First isolated **S-312C engine torque-curve** test for the standard C-330.

### Changed
- peak torque corrected from the imported ~138 Nm to **100 Nm**,
- maximum torque placed at **1600-1800 rpm**,
- 2200-rpm torque set to **~97.24 Nm** for the factory **22.4 kW** rated power,
- conservative low-rpm interpolation added for testing,
- read-only engine trace added for RPM/load analysis.

### Not changed
Fuel use, idle/max RPM, gearbox, ADS behavior, C-330M and chassis physics are unchanged.

### Test
Use **C-330 (motor=1)**. Compare unloaded acceleration with the previous build, then use the same heavy trailer on level ground and, if possible, on an incline/high-resistance pull. Let the engine work below 1800 rpm instead of immediately lifting off. Send the complete `log.txt`; `[ENGINE_TRACE]` will show how the real 100 Nm curve interacts with ADS and the completed gearbox.
