# Changelog

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
