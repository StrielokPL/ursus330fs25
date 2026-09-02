## Ursus C-330 / C-330M 0.0.5.0 D1

**Diagnostic prerelease rebuild of the existing 0.0.5.0 calibration.** Drivetrain ratios, engine calibration and controller thresholds are intentionally unchanged in D1. This build exists only to capture enough runtime data to diagnose the C-330M automatic gearbox while working with period-correct implements.

### Integrated full diagnostics

The diagnostic is now part of the Ursus prerelease ZIP itself. No second mod needs to appear in the mod selector.

Log prefix: **`[C330FULLDIAG]`**

The build records:

- full transmission state every **200 ms** while the gearbox prediction is active,
- final `findGearChangeTargetGearPrediction()` result after `C330TransmissionFix`,
- current/target gear and mechanical range I/II,
- RPM, real speed and accelerator input,
- total tractor + implement/trailer mass,
- ADS `dynamicMotorLoad`, native GIANTS smooth load, selected load and source,
- `getSpeedLimit(true)` with the active working implement and the vehicle-only limit,
- internal C330 controller dwell, cooldown, upshift hold and recovery timers,
- last requested range/gear and the C330 controller reason breadcrumb,
- explicit `setGearGroup()` / `setGear()` calls,
- start-gear/start-range decisions,
- attached implements every ~1 s with lowered/on state, implement speed limit and plow/work-area presence,
- a compact rear-wheel snapshot (`tireLoad`, `restLoad`, `additionalMass`, radius).

### Recommended C-330M test

1. Fresh C-330M, automatic gearbox, no implement: accelerate normally through the ranges.
2. Attach the small period plow used in the previous test.
3. Lower it and plow at full working load on level ground.
4. Repeat uphill and downhill.
5. While moving, lift the plow briefly and lower it again without changing throttle.
6. Note whether the sequence reaches `I/3 -> II/1`, and whether a temporary lift causes `II/1 -> II/2 -> II/3`.
7. Repeat with period-correct harrow/cultivator/seeder when available.
8. Send the complete `log.txt`; filtering is not required.

### Release policy from now on

- **Prerelease builds intentionally contain `Scripts/C330FullDiagnostic.lua`.**
- **Full releases automatically remove this file from the final Farming Simulator ZIP.**
- CI fails if a full release still contains `[C330FULLDIAG]` or the diagnostic Lua file.
- Standard temporary kits such as `TractorDebugKit` / `TyreDebugKit` remain forbidden in published release ZIPs.

The in-game mod version remains **0.0.5.0** because D1 does not change calibration or gameplay logic; the GitHub prerelease tag `0.0.5.0D1` uniquely identifies this diagnostic build. The next actual transmission fix can advance the mod version normally.
