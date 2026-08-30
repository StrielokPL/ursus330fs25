## Ursus C-330 / C-330M 0.0.1.4

Isolated mass-aware automatic start-gear test.

### Changed
- automatic forward starts directly in **I/3** when total tractor+attached-equipment mass is below **3.175 t**,
- at 3.175 t or more, the previous native low-range start-gear choice remains,
- the emergency near-stop range-I reset follows the same mass rule,
- `[C330TRANS] START GEAR` now reports the measured total mass and selected mode.

### Unchanged
0.0.1.3 range-boundary safety, the 0.0.1.2 top-gear guard, the 100 Nm S-312C curve, gearbox ratios, reverse logic, fuel use, ADS read-only handling, C-330M and chassis physics are unchanged.

### Test focus
Test at least: (1) bare/light C-330 below 3.175 t, which should log `START GEAR I/3 ... mode=LIGHT_I3`; (2) a set clearly above 3.175 t, which should log `mode=NATIVE_LOW_RANGE` and must not be forced to I/3. Check standing starts, stop/restart, forward/reverse changes and one loaded acceleration/deceleration cycle. Send the complete `log.txt`.

<!-- release-trigger-0.0.1.4 -->
