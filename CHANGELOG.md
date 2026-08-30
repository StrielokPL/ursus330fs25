# Changelog

## 0.0.2.2 - C-330 base mass / COM correction test

First measured mass/COM correction based on the complete 0.0.2.1 static diagnostic matrix.

### Runtime evidence from 0.0.2.1
- Settled unballasted/basic-wheel C-330: **1.683 t**, about **0.605 t front / 1.078 t rear = 35.97/64.03**.
- Factory target: **1.675 t**, **0.635 t front / 1.040 t rear = 37.9/62.1**.
- `vehicleType=1..10` cabin variants did not alter runtime mass or axle loads; current cabin choices are physics-mass-neutral.
- Rear wheel options added regular rear-only mass: +40, +80 and +120 kg; the two heaviest variants were both +120 kg.
- `design3=2` added exactly +100 kg through component 2 and effectively placed it on the front axle.
- Combined configurations were additive and stable.

### Change
- Base component 1 nominal mass: **800 -> 792 kg**. With the observed +35 kg runtime fuel mass this is expected to reduce the settled tractor from 1.683 t to approximately **1.675 t**.
- Component 1 longitudinal COM: **Z -0.200 -> -0.125 m**, a 75 mm forward correction.
- Using the 1.920 m factory wheelbase and measured component/runtime masses, this is predicted to move roughly 30-33 kg of axle reaction from rear to front and land close to **635/1040 kg**.

### Explicitly unchanged
- Cabin configuration masses (still neutral pending separate evidence for individual cabin weights).
- Front and rear ballast configuration masses.
- Wheel/tyre dimensions and traction physics.
- Engine, gearbox, ADS integration and all 0.0.2.0 drivetrain behavior.
- C-330M drivetrain/controller scope.

## 0.0.2.1 - base mass / COM / axle-load diagnostic

First isolated mass-analysis prerelease after stable 0.0.2.0. **No physical values are changed in this build.**

### Change
- Temporarily restored the validated read-only `TractorDebugKit` for static mass measurements.
- Diagnostics are restricted to configuration, total mass, component mass/COM, wheel mass and settled front/rear tire loads.
- Transmission-change tracing, periodic engine tracing and ADS-load reading are disabled for this test.
- Snapshot settle delay increased to 3.5 s to give the suspension more time to stabilize.

### Test target
- Use the basic wheel configuration as the common baseline.
- Record the naked/base tractor first, then cabin variants and ballast variants/combinations.
- The log records selected configuration indices, so each spawned/reconfigured tractor can be identified from the log.
- Primary factory target for the unballasted ready-to-work C-330: about 1675 kg total, 635 kg front / 1040 kg rear, approximately 38/62 axle split.

### Explicitly unchanged
- 0.0.2.0 production transmission controller and all gearbox behavior.
- S-312C torque curve and engine parameters.
- Component masses, center of mass, ballast values, wheels, tyres, suspension and differential.
- C-330M drivetrain.

## 0.0.2.0 - stable C-330 drivetrain milestone

First full stable release of the rebuilt standard C-330 drivetrain phase. **No engine or transmission behavior is changed from 0.0.1.8.**

### Final 0.0.1.8 validation
- Complete runtime log contained **0 Lua/game errors** and **0 `SHIFT_OSCILLATION` warnings**.
- The generic 2.0 s upshift dwell was observed blocking premature automatic upshifts.
- Light 1.683 t forward starts selected `LIGHT_I3`; light reverse starts selected `LIGHT_RII` / R-II.
- A light R-II start may still fall back to R-I immediately when actual low-rpm load crosses the existing reverse downshift protection; this is intentional safety behavior, not hunting.
- All warnings in the validation log were unrelated to this mod (other-mod l10n/texture warnings, savegame/render warnings).

### Stable drivetrain state
- Factory-style C-330 6F/2R speed ladder with explicit I/II automatic range sequencing.
- 2.0 s minimum automatic upshift dwell and heavy-set II/3 recovery protection.
- Mass-aware starts: <3.175 t -> I/3 forward and R-II reverse; >=3.175 t keeps conservative low-range starts.
- S-312C calibration: 100 Nm maximum at 1600-1800 rpm and ~22.4 kW at 2200 rpm.
- ADS compatibility remains optional, filtered and strictly read-only.
- Static Cabins dirty-flag compatibility fix remains in place.
- C-330M remains outside the custom C-330 drivetrain controller and is reserved for separate calibration.

### Release cleanup
- Removed temporary `debug/TractorDebugKit.lua` from the stable package and `modDesc.xml`.
- Kept `Scripts/C330TransmissionFix.lua` as the production transmission controller.

### Next development subsystem
- Base mass and center-of-mass / axle-load calibration against the 1675 kg and ~38/62 factory target, isolated from tyres, ballast and drivetrain tuning.

## 0.0.1.8 - 2 s upshift failsafe and mass-aware R-II start

Transmission follow-up based on the complete 0.0.1.7 runtime log.

### 0.0.1.7 result
- Controller remained stable: no `SHIFT_OSCILLATION` and no Lua errors.
- All observed range changes were attributed to `C330TRANS`.
- The 3.469 t heavy-set II/3 guard worked, but 600 ms was not enough: one top-gear shift still settled near 1180 rpm / 0.846 ADS load and another near 1225 rpm / 0.783. Both recovered without hunting, but the diagnostic target was not fully met.

### Changes
- Every automatic upshift now has a hard **2000 ms minimum settled-gear dwell**. Downshifts are not delayed.
- Heavy sets (>=3.175 t) now require **2000 ms continuous load <0.70** before II/2 -> II/3, replacing the 600 ms window.
- Reverse starting now mirrors forward mass-aware starting: **<3.175 t starts directly in R-II**, while **>=3.175 t starts in R-I**.
- Added diagnostic breadcrumbs: `BLOCK UPSHIFT DWELL`, `BLOCK RANGE UPSHIFT DWELL`, `BLOCK REVERSE UPSHIFT DWELL`, and `START REVERSE R-II/R-I`.

### Explicitly unchanged
- Factory 6F/2R ratios and speed ladder.
- Forward I/3 <-> II/1 downshift/load thresholds except for the new generic minimum dwell on upshifts.
- 100 Nm S-312C engine curve, fuel use, mass/COM, tyres and chassis physics.
- ADS remains optional, filtered and strictly read-only.
- C-330M remains excluded.

## 0.0.1.7 - C-330 heavy-set II/3 stability guard

Isolated follow-up to the 0.0.1.6 trailer/no-trailer runtime test. **Only II/3 admission for heavy sets is refined.**

### Runtime evidence from 0.0.1.6
- The 0.70 threshold started working: `BLOCK TOP UPSHIFT HIGH LOAD` appeared twice with the 3.469 t trailer set.
- No-trailer behavior remained clean at 1.683 t.
- Two loaded shifts still slipped through after short ADS dips below 0.70: the low-load window before the decision was only about 0.15 s and 0.27 s, and post-shift load climbed back to roughly 0.77-0.88.
- Two more acceptable loaded cases had load below 0.70 for about 0.75-0.82 s before II/3 and recovered without the same severe bog.
- All 13 range changes were `source=C330TRANS`; no `SHIFT_OSCILLATION` or Lua error occurred.

### Change
- For total mass **>= 3.175 t**, II/2 -> II/3 now requires filtered load **< 0.70 continuously for 600 ms**.
- If load returns to >=0.70, the 600 ms timer resets.
- Light sets below 3.175 t keep the 0.0.1.6 behavior.
- The existing predicted post-shift RPM guard remains active after stabilization.

### Explicitly unchanged
- Mass-aware start rule and 3.175 t threshold.
- Forward I/3 <-> II/1 and reverse range logic.
- 100 Nm S-312C engine curve, factory gearbox ratios, fuel use and chassis physics.
- C-330M remains excluded.
- ADS remains optional, filtered and strictly read-only.

## 0.0.1.6 - C-330 refined high-load II/3 guard

Isolated follow-up to the 0.0.1.5 trailer/no-trailer runtime test. **Only the high-load classification threshold for II/2 -> II/3 changes.**

### Runtime evidence from 0.0.1.5
- Without the trailer, top-gear shifts were acceptable and the mass-aware 1.683 t start remained `LIGHT_I3`.
- With the trailer, total mass 3.469 t correctly selected `NATIVE_LOW_RANGE`.
- One loaded II/2 -> II/3 shift was still too aggressive: 2088 rpm / 0.757 ADS at the decision, followed by about 1112 rpm / 0.908 load in II/3.
- The new `>=0.80` high-load gate did not trigger because the instantaneous ADS sample dipped below 0.80 at the decision point.
- All 11 observed range changes were attributed to `C330TRANS`; no `SHIFT_OSCILLATION`, Lua error or C330TRANS warning was present.

### Change
- `TOP_GEAR_HIGH_LOAD` reduced from **0.80** to **0.70**.
- `TOP_GEAR_HIGH_LOAD_MIN_RPM` remains **2100 rpm**.
- Therefore II/2 -> II/3 is held until 2100 rpm whenever the current filtered load is >=0.70.

### Explicitly unchanged
- 0.0.1.4 mass-aware start rule and 3.175 t threshold.
- Forward I/3 <-> II/1 and reverse range logic.
- Moderate-load predicted post-shift RPM guard.
- S-312C 100 Nm engine curve, factory gearbox ratios, fuel use and chassis physics.
- C-330M remains excluded.
- ADS remains optional, filtered and read-only.

## 0.0.1.5 - C-330 high-load II/3 guard

Isolated automatic transmission test based on the 0.0.1.4 flat + slope runtime trace. **Mass-aware starting, range logic, engine calibration and ADS handling are unchanged.**

### Runtime evidence from 0.0.1.4
- Mass-aware starting classified every observed set correctly: 1.683 t -> `LIGHT_I3`; 3.469 t, 6.885 t and 12.881 t -> `NATIVE_LOW_RANGE`.
- All 39 observed range changes were attributed to `C330TRANS`; there were no `SHIFT_OSCILLATION` warnings and no Lua errors.
- The existing II/2 -> II/3 predicted-RPM guard works at moderate load, but hill tests exposed a high-load corner case.
- Observed high-load shifts: about 1928 rpm / 0.804 ADS -> ~1065 rpm / 0.905 after II/3; 1976 / 0.878 -> ~974 / 0.990; 2081 / 0.840 -> ~1167 / 0.857.
- A later 2137 rpm / 0.822 shift recovered around 1550 rpm, providing a useful safe-side boundary for the next test.

### Change
- Added a high-load II/2 -> II/3 gate: when load is **>= 0.80**, II/3 is blocked below **2100 rpm**.
- Existing moderate-load predicted post-shift guard (`>=0.55` load, predicted minimum 1200 rpm) remains in place.
- New diagnostic reason: `BLOCK TOP UPSHIFT HIGH LOAD`.

### Explicitly unchanged
- 0.0.1.4 light-set start rule: total mass <3.175 t starts in I/3; heavier/unknown mass retains native low-range start selection.
- Forward I/3 <-> II/1 and reverse range logic, including the 6.0 km/h forward range-down ceiling.
- S-312C 100 Nm torque curve, factory gearbox ratios, fuel use and chassis physics.
- C-330M remains excluded.
- ADS remains optional, filtered and read-only; no ADS state is written.

## 0.0.1.4 - C-330 mass-aware I/3 start

Isolated automatic start-gear test based on the clean 0.0.1.3 range-boundary result. **Range logic, engine calibration and ADS handling are unchanged.**

### Runtime evidence from 0.0.1.3
- No II/1 -> I/3 range-down occurred above the 6.0 km/h safety ceiling; observed range-down requests were about 1.20, 1.43, 3.21 and 4.11 km/h.
- Near-stop range-I restoration worked through the existing `START RANGE RESET`; the extra `LOW SPEED RANGE RESET` remains a fallback safety path.
- All observed range changes were attributed to `C330TRANS`, with no `SHIFT_OSCILLATION` and no Lua errors.
- A light forward start still walked I/1 -> I/2 -> I/3, costing roughly two unnecessary low-range shifts before reaching I/3.

### Change
- Factory base mass reference: **1.675 t**.
- Light-start threshold: **3.175 t total set mass** (= 1.675 t + 1.500 t).
- In automatic forward, if `vehicle:getTotalMass()` is strictly below 3.175 t, the start/restart gear is forced to **I/3**.
- At 3.175 t or above, or if total mass cannot be read, GIANTS' native start-gear choice is retained and clamped to range I as before.
- The <=0.5 km/h emergency range-I reset uses the same mass-aware start-gear choice.
- Added `[C330TRANS] START GEAR` diagnostic with total mass, threshold and selection mode.

### Explicitly unchanged
- 0.0.1.3 forward II/1 -> I/3 6.0 km/h ceiling and low-speed range reset.
- 0.0.1.2 II/2 -> II/3 predicted-RPM guard.
- S-312C 100 Nm torque curve, gearbox ratios, reverse logic, fuel use and chassis physics.
- C-330M remains excluded.
- ADS remains optional, filtered and read-only; no ADS state is written.

## 0.0.1.3 - C-330 range-boundary safety

Small isolated follow-up to the 0.0.1.2 gearbox/100 Nm compatibility test. **Engine and top-gear calibration are unchanged.**

### Runtime evidence from 0.0.1.2
- The II/2 -> II/3 predicted-RPM guard works: repeated `BLOCK TOP UPSHIFT` events occurred under load and the eventual shifts happened at materially higher RPM.
- A remaining II/1 -> I/3 request occurred at about **7.41 km/h / 1488 rpm / ADS load 0.559**. That speed is above the factory I/3 road speed (5.649 km/h at 2200 rpm), so commanding I/3 there is mechanically undesirable even if the throttle/load condition is otherwise true.
- After a near-stop in range II, the runtime state machine could sometimes accelerate again through II/2 and II/3 before `getBestStartGear` performed a range-I reset.
- The interrupted interval with engine RPM=0 and implausible vehicle-speed jumps was excluded from calibration decisions.

### Change
- Forward II/1 -> I/3 is now permitted only at <= **6.0 km/h**. This leaves a small governor margin above the 5.649 km/h rated I/3 speed while avoiding an over-speed range selection.
- Automatic forward now performs a deterministic **LOW SPEED RANGE RESET** to range I at <= **0.5 km/h** if range II is still active.

### Explicitly unchanged
- S-312C 100 Nm torque curve from 0.0.1.1.
- 0.0.1.2 II/2 -> II/3 predicted-RPM guard (1200 rpm target, load-aware).
- Factory 6F/2R ratios, other range thresholds and reverse logic.
- Fuel use, min/max RPM, chassis physics and C-330M.
- ADS remains optional, filtered and read-only.

## 0.0.1.2 - S-312C / gearbox compatibility fix

Small isolated transmission-controller correction based on the 0.0.1.1 100 Nm engine runtime trace. **The S-312C torque curve itself is unchanged.**

### Runtime evidence
- II/2 -> II/3 was allowed at about **1695 rpm / ADS load 0.789**; after engagement the engine fell to about **960-980 rpm at ~0.89-0.93 load** before recovering.
- II/1 -> I/3 could be requested at about **1499 rpm / load 0.335** only because the accelerator was near full; the engine was not actually overloaded.

### Change
- Full throttle is no longer enough by itself to force a range downshift. The accelerator path additionally requires load >= **0.55**; the original high-load path (>=0.75) remains unchanged.
- Added a dedicated II/2 -> II/3 prediction guard. At load >= **0.55**, the controller estimates post-shift RPM using the factory 14.324/22.878 speed ratio and blocks the shift if predicted RPM would be below **1200 rpm**.
- Light-load top-gear shifts remain available to vanilla prediction, so unloaded road acceleration is not artificially forced to wait for a fixed high RPM.

### Explicitly unchanged
- C-330 S-312C curve from 0.0.1.1: 100 Nm peak, 1600-1800 rpm plateau, ~97.24 Nm at 2200 rpm.
- Fuel use, min/max RPM and engine acceleration/braking parameters.
- Factory 6F/2R ratios and range thresholds.
- ADS remains optional, filtered and read-only.
- C-330M and chassis physics.

## 0.0.1.1 - S-312C torque-curve test

First isolated engine calibration for the standard **C-330**. Gearbox behavior from 0.0.1.0 is deliberately unchanged. C-330M keeps the old imported engine as a comparison/control configuration.

### Problem
- Imported `torqueScale=0.138` gives about 138 Nm peak torque.
- The old curve produces roughly 22.9 kW already near 1580 rpm and about 24.1 kW near 1890 rpm, creating an unrealistically large low/mid-RPM torque reserve.
- Factory target is 100 Nm maximum at 1600-1800 rpm and 22.4 kW at 2200 rpm.

### Change
- C-330 `torqueScale`: **0.138 -> 0.100**.
- Confirmed torque anchors: **100 Nm at 1600 and 1800 rpm**.
- Rated point: **~97.24 Nm at 2200 rpm**, corresponding to **22.4 kW**.
- Low-RPM test interpolation: 88 Nm @990, 92 Nm @1100, 96 Nm @1298. These values are not claimed as factory measurements and are subject to runtime tuning.

### Diagnostics
- Added read-only `[TRACTORDBG][ENGINE_TRACE]` every 750 ms while the tractor is actually moving/loaded.
- Trace records RPM, speed, gear/group, direction, raw ADS load and native GIANTS smoothed load.
- `[TRACTORDBG][MOTOR]` also reports runtime min/max RPM and torqueScale fields when exposed by `VehicleMotor`.

### Explicitly unchanged
- Fuel consumer remains **4.2 l/h** for this test.
- `minRpm=600`, `maxRpm=2200`, acceleration/braking parameters.
- Complete C-330 6F/2R gearbox/controller.
- ADS integration remains read-only and filtered.
- C-330M engine/drivetrain.
- Mass/COM, ballast, tyres and suspension.

## 0.0.1.0 - C-330 gearbox milestone

Milestone release closing the dedicated standard C-330 transmission phase. **No gearbox code, ratios or shift thresholds are changed from 0.0.0.7.**

### Runtime validation of 0.0.0.7
- C-330 automatic range control covered the complete 6F/2R layout.
- All recorded I/II range changes were attributed to `C330TRANS`; no remaining `EXTERNAL/GIANTS` group changes were observed in the test.
- Forward `I/3 -> II/1` transitions remained stable at high RPM and moderate/low load.
- Reverse `R-I -> R-II` occurred only after R-I reached roughly 1.53 km/h at about 2170-2200 rpm and low ADS load (~0.30), instead of the earlier GIANTS high-load upshift.
- No `SHIFT_OSCILLATION`, C-330 Lua error, ADS error or controller error was observed.
- Active `R-II -> R-I` load reduction was not forced in the final runtime trace, but start/reset handling reliably returned to range I and no reverse hunting was observed.

### ADS / compatibility status
- ADS remains optional and strictly read-only.
- Invalid/negative ADS samples are rejected and fall back to native GIANTS smoothed load.
- Static Cabins / dirty-flag protection remains unchanged.

### Next subsystem
- Begin isolated S-312C engine calibration.
- Imported peak torque (~138 Nm) and fuel-use model remain untouched in this milestone and are the next tuning target.

### Explicitly unchanged
- `Scripts/C330TransmissionFix.lua` behavior from 0.0.0.7.
- C-330M drivetrain.
- Mass/COM, ballast, tyres and suspension.

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
