## Ursus C-330 / C-330M 0.0.1.3

Final small automatic-range boundary test before returning to the S-312C engine.

### Changed
- II/1 -> I/3 is blocked above 6.0 km/h, preventing the automatic controller from selecting I/3 above its mechanical road-speed range,
- if the tractor nearly stops while range II remains active, automatic forward now resets deterministically to range I at <=0.5 km/h.

### Unchanged
The 100 Nm S-312C curve, the 0.0.1.2 top-gear predicted-RPM guard, gearbox ratios, reverse logic, fuel use, ADS read-only handling, C-330M and chassis physics are unchanged.

### Test focus
Repeat loaded acceleration/deceleration with C-330 motor=1. Confirm that II/1 no longer changes to I/3 above 6.0 km/h and that a near-stop in range II produces `LOW SPEED RANGE RESET` before re-acceleration. The existing `BLOCK TOP UPSHIFT` behavior should remain unchanged. Send the complete `log.txt`.

<!-- release-trigger-0.0.1.3 -->
