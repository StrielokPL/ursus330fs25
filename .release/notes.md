## Ursus C-330 / C-330M 0.0.5.0 P1

**Gameplay prerelease based on the clean D2 diagnostic log.** Full diagnostics remain integrated in this prerelease.

No engine curve, torque value, gearbox ratio, ballast mass or tyre calibration is changed. P1 only adds a second automatic-transmission safety layer after the validated C330TransmissionFix controller.

### What the D2 log proved

With C-330 + Brony 5 (15 km/h work limit), GIANTS allowed II/2 -> II/3 at about 2126 rpm and ~0.755 load. After the shift the engine fell toward 1100 rpm, load rose to ~0.9-1.0 and the tractor kept slowing until II/2 was selected manually.

With C-330M + U021/1 (8.4 km/h work limit), II/1 was the correct work gear at roughly 2000-2160 rpm, but GIANTS still attempted II/1 -> II/2 and pulled the engine down toward ~1050-1150 rpm.

The log also confirmed that `vehicle:getSpeedLimit(true)` correctly follows the active lowered implement and returns no finite work limit after the implement is lifted.

### P1 gearbox changes

- Adds `Scripts/C330TransmissionWorkFix.lua` as a permanent gameplay layer.
- Uses the active GIANTS implement speed limit, not implement names/types.
- Maps the active work speed to the highest of the six real C-330/C-330M gears that keeps at least **1500 rpm** at that speed.
- Example targets from the current calibration:
  - ~8.4 km/h -> II/1,
  - ~13-15 km/h -> II/2,
  - slower implements may correctly remain in range I.
- The selected work gear becomes an upshift ceiling while the implement work limit is active.
- If the tractor is already above the correct work gear when a tool is lowered, it reduces one mechanical step at a time.
- Allows I/3 -> II/1 under field load when II/1 is the calculated work gear, RPM is at least 2050 and the existing 2 s dwell has elapsed. This removes the old `load <= 0.55` trap for that specific work transition.
- Adds a general lugging recovery: at >=0.85 throttle, >=0.75 load and <=1450 rpm, a too-tall within-range gear is reduced by one step.
- After a lugging reduction, ordinary upshifts are held for 2.5 s to prevent II/3 -> II/2 -> II/3 hunting.
- Lifting an actively working implement also creates a 2.5 s headland/release hold before road upshifts resume.

### Diagnostics

D2 flight-recorder diagnostics remain enabled in this prerelease. The `[C330FULLDIAG]` log still records transmission state, final prediction, speed limits, load/RPM, range/gear events, implements and wheel data. P1 also leaves controller breadcrumbs such as `WORK GEAR HOLD`, `WORK GEAR DOWN`, `WORK RANGE UP`, `LUG DOWNSHIFT`, `WORK RELEASE HOLD` and `BLOCK UPSHIFT HOLD` for the diagnostic state line.

### Test order

1. C-330 without an implement: verify normal road sequence and that II/3 is still available when power permits.
2. C-330 + Brony 5: work at the 15 km/h limit; expected ceiling is II/2, with no self-inflicted II/3 lugging.
3. C-330M + U021/1: expected work gear is II/1; verify I/3 -> II/1 can occur under real plough load and II/1 -> II/2 is blocked while the plough is active.
4. Lift/lower the implement while moving and verify the 2.5 s release hold.
5. Test U-201 / another ~13 km/h implement; expected work gear is II/2.
6. Send the complete `log.txt`.

This remains a prerelease. The full-release workflow still removes `C330FullDiagnostic.lua`; the work-speed gearbox fix itself is permanent gameplay code and is not removed from full builds.
