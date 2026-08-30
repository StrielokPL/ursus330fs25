# Changelog

## 0.0.0.7 - full C-330 6F/2R automatic gearbox test

Completes the automatic range controller after 0.0.0.6 proved that remaining external I/II changes were GIANTS reverse/start behavior. Factory ratios and established forward thresholds are unchanged.

### Reverse automatic control
- GIANTS automatic group selection is now disabled for C-330 automatic mode in both directions.
- Reverse is treated as the real two-step range gearbox: `R-I` (~1.53 km/h) and `R-II` (~6.21 km/h).
- `R-I -> R-II` requires the same ADS-safe sustained recovery used at the forward range boundary: >=2050 rpm, load <=0.55, held for 800 ms, and no active recovery hold.
- `R-II -> R-I` occurs under the established protection threshold: <=1500 rpm with load >=0.75 or strong accelerator demand.
- Automatic start/restart forces range I; manual transmission modes remain unchanged.

### ADS protection
- ADS remains optional and strictly read-only.
- Invalid/negative ADS shift samples are still rejected and replaced with native GIANTS smoothed load.
- Reverse range changes now use the same filtered load path as forward changes.
- Existing Static Cabins / dirty-flag protection remains unchanged.

### Diagnostics
- `[TRACTORDBG][RANGE_CHANGE]` now includes current direction.
- Controller-generated reverse changes use reasons `REVERSE RANGE UP` / `REVERSE RANGE DOWN`.
- Start/reset range changes are marked as `START RANGE RESET` for source attribution.

### Explicitly unchanged
- C-330 factory ratios and forward shift thresholds from 0.0.0.5.
- Engine torque/fuel model.
- C-330M drivetrain.
- Mass/COM, ballast, tyres and suspension.

## 0.0.0.6 - range-source diagnostic test

Diagnostic follow-up to the 0.0.0.5 runtime log. **No transmission ratios, thresholds, engine values or ADS-facing behavior are changed.**

### Findings from 0.0.0.5
- ADS-safe range-up hysteresis worked: observed `I/3 -> II/1` transitions occurred around 2180-2220 rpm at moderate ADS load.
- No C-330/ADS/AIASF Lua error was observed.
- `activeGearIndex=0` is a normal disengaged phase during shifts; the old debugger incorrectly flagged many such sequences as oscillations.
- Several low-speed range changes occurred without a matching `[C330TRANS] RANGE UP/DOWN` message and need source attribution before changing gearbox logic.

### Diagnostics
- `SHIFT_OSCILLATION` now ignores transitions involving gear index 0.
- Every shift log now includes raw active/target/current gear fields, current direction and auto gear timer.
- Every actual gear-group change gets a `[TRACTORDBG][RANGE_CHANGE]` line.
- Range changes are labelled `source=C330TRANS` when they match a recent controller request, otherwise `source=EXTERNAL/GIANTS`.
- `C330TransmissionFix` writes only an internal diagnostic breadcrumb for its own requested range; it still never writes to ADS state.

### ADS protection
- 0.0.0.5 load validation and fallback remain unchanged.
- ADS remains optional and read-only.
- Static Cabins / dirty-flag protection remains unchanged.

### Explicitly unchanged
- C-330 factory ratios and range thresholds.
- Engine torque/fuel model.
- C-330M drivetrain.
- Mass/COM, ballast, tyres and suspension.

## 0.0.0.5 - ADS-safe gearbox hysteresis test

Follow-up to the first real C-330 0.0.0.4 runtime test. Factory ratios are unchanged.

### Automatic range controller
- Kept the successful heavy-load `II/1 -> I/3` downshift behavior.
- Raised `I/3 -> II/1` recovery RPM from 1950 to **2050 rpm**.
- Reduced maximum load for range upshift from 0.72 to **0.55**.
- Added **800 ms sustained recovery** requirement before leaving range I.
- Increased range-change cooldown from 650 to **800 ms**.
- Increased post-downshift recovery hold from 1800 to **2500 ms**.
- Goal: prevent repeated `I/3 <-> II/1` hunting with a heavy trailer while still allowing a clean road-range transition when unloaded.

### ADS protection
- ADS remains optional and read-only; the tractor mod never writes to ADS state.
- `dynamicMotorLoad` is accepted only as a valid approximately 0..1 sample (0..1.05 tolerance, clamped to 1.0).
- Negative shift sentinels and out-of-range ADS values are ignored and the controller falls back to native GIANTS smoothed motor load.
- Reduced range hunting also reduces artificial rapid load/shift cycling presented to ADS.
- Existing Static Cabins / dirty-flag protection remains unchanged.

### Explicitly unchanged
- Factory C-330 ratios introduced in 0.0.0.4.
- Engine torque/fuel model.
- C-330M drivetrain.
- Mass/COM, ballast, tyres and suspension.

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
