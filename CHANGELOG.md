# Changelog

## 0.0.0.4 - C-330 gearbox test prerelease

First dedicated transmission correction for the standard **C-330**. C-330M is deliberately unchanged in this test.

### C-330 factory gearing
- Range reduction changed from the imported `0.36` speed factor to `0.24691358`, corresponding to the factory 4.050 reduction.
- High-range forward speeds set to **7.389 / 14.324 / 22.878 km/h**.
- Low range therefore targets approximately **1.825 / 3.537 / 5.649 km/h**.
- High-range reverse set to **6.207 km/h**; low reverse follows the 4.050 reduction (~1.533 km/h).
- C-330 motor speed caps set to 22.878 km/h forward and 6.207 km/h reverse.

### Automatic range controller
- Added `Scripts/C330TransmissionFix.lua`, active only for the C-330 motor configuration in forward automatic mode.
- GIANTS automatic group optimization is disabled for C-330 forward automatic driving.
- Intended sequence is `I/1 -> I/2 -> I/3 -> II/1 -> II/2 -> II/3`, and the reverse order when downshifting.
- Vanilla still decides normal shifts inside each range, but multi-gear jumps are clamped to one mechanical gear at a time.
- Added explicit `II/1 -> I/3` load downshift before the tractor nearly stalls.
- Added explicit `I/3 -> II/1` range upshift only after RPM recovers and load is moderate.
- Added hysteresis/cooldowns to prevent immediate range hunting.
- ADS `dynamicMotorLoad` is used when valid; otherwise the native GIANTS smoothed motor load is used. ADS remains optional.
- Manual modes are unchanged. Reverse remains under GIANTS control in this first test.

### Diagnostics
- `TractorDebugKit` remains enabled.
- New controller messages use prefix `[C330TRANS]`.

### Explicitly unchanged
- C-330 engine torque curve and fuel use.
- C-330M drivetrain.
- Mass/COM, ballast, tyres and suspension.

### Test goal
Verify that a heavily loaded C-330 uses range I before losing almost all road speed, and that unloaded/light-load acceleration follows the real six-step order without rapid I/II oscillation.

## 0.0.0.3 - diagnostic prerelease

Cleanup and read-only runtime diagnostic build. **No drivetrain, mass, tyre or engine tuning is included in this version.**

### Source cleanup
- Fixed four I3D texture references that pointed to missing PNG files while the corresponding DDS assets were present.
- Corrected `$l10n_Yelow` references to the existing `$l10n_Yellow` key.
- Replaced the development `TEST` title on connection-hose configurations with a proper localized title.
- Corrected generator/dynamo translations and the Polish `Prądnica` label.
- Corrected swapped store labels for field and road tyre brands.
- Removed the obsolete fully commented alternative motor/transmission block.
- Compacted dead placeholder comments left by the Static Cabins patch while preserving the compatibility fix itself.
- Corrected the technical documentation so component mass is not mistaken for total runtime vehicle mass.

### Diagnostics
- Added temporary `debug/TractorDebugKit.lua`, scoped only to `c330m.xml`.
- Logs actual front/rear tyre loads and axle split after physics settles.
- Logs runtime component mass/defaultMass and component center of mass.
- Logs wheel mass, tire load/restLoad and key suspension/traction parameters.
- Logs active vehicle configurations, motor/gear/group state and differential graph.
- Traces real gear/group changes and flags quick A→B→A shift oscillation candidates.
- Reads ADS `dynamicMotorLoad` only when Advanced Damage System is present; there is no hard dependency.

### Explicitly unchanged
- Component mass values and center-of-mass values.
- Wheel radius, width, mass, friction and stiffness values.
- Engine torque curve, RPM limits and fuel usage.
- Gear ratios, groups and speed limits.
- Differential topology.
- Front/rear ballast masses.
- Static Cabins ADS/AIASF compatibility behavior.

### Test goal
Establish the real FS25 runtime baseline before changing mass distribution, ballast, engine, gearbox, tyres or suspension. Search the game log for `[TRACTORDBG]`.

## 0.0.0.2 - prerelease

Development baseline for the Ursus C-330 / C-330M FS25 rebuild.

### Imported state
- Reset project development version from the original package version `1.1.2.0` to `0.0.0.2`.
- Confirmed `StrielokPL` as the first listed author in `modDesc.xml`.
- Confirmed that the uploaded source package already contains the previously tested **Static Cabins** compatibility fix from `Farming25fixnmix`; the patch was not applied a second time.

### Static Cabins compatibility fix already present
- 18 cabin-related `movingTool` definitions removed.
- Corresponding Interactive Control entries removed.
- Cabin animations `leweDrzwi`, `praweDrzwi`, `dach` and `okno` removed.
- Cabin configurations retained as static geometry.
- Only 3 technical tractor `movingTool` definitions remain.
- Dirty-flag usage reduced to avoid the multiplayer collision previously observed between the original tractor setup, Advanced Damage System and AIAutomaticSteering.
- Original compatibility test: Advanced Damage System 0.9.2.4 enabled, AIASF debug enabled, no erroneous Automatic Steering updates observed.

### Documentation
- Added technical C-330 baseline for later physics correction.
- Documented planned targets for mass, axle load distribution, engine torque, gearbox, ballast, PTO and rear linkage.

### Not yet changed in 0.0.0.2
- Engine torque curve and rated power.
- Gear ratios and top speed.
- Base mass and axle load distribution.
- Factory ballast masses.
- Tyre/traction calibration.

This version is intended as a clean compatibility and documentation baseline before the physics rebuild begins.
