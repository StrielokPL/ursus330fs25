# Ursus C-330 / C-330M for Farming Simulator 25

Working repository for analysis, correction and further development of the FS25 Ursus C-330 / C-330M 4x2 mod.

## Authors
**StrielokPL**, Speedy, Miziuu

## Current development version
**0.0.3.0 – stable C-330 mass / balance milestone**

The repository was imported from mod package version **1.1.2.0**, but the project versioning was reset for the rebuild. Version `0.0.0.2` is the first documented development baseline in this repository.

### Runtime diagnostics
Development builds `0.0.0.3` through `0.0.1.8` used a temporary **read-only** `TractorDebugKit` adapted from `strojenieciagnikowfs25` to validate mass, drivetrain, shift behavior and optional ADS load. The kit did not tune or overwrite vehicle physics.

The temporary diagnostic kit was removed for stable **0.0.2.0**. It can be restored in a later development branch when another subsystem needs runtime instrumentation.

### Changes already present in the imported package
The uploaded source package already contained the previously tested **Static Cabins** compatibility fix from `Farming25fixnmix`, so the patch was **not applied again**.

The fix:
- removes 18 cabin-related `movingTool` definitions,
- removes the corresponding Interactive Control entries,
- removes the cabin animations `leweDrzwi`, `praweDrzwi`, `dach` and `okno`,
- keeps all cabin configurations available as static geometry,
- leaves only the 3 technical tractor `movingTool` definitions,
- reduces dirty-flag pressure that previously collided with AIAutomaticSteering/ADS behaviour in multiplayer.

The original compatibility patch was tested with Advanced Damage System 0.9.2.4 and AIASF debug enabled without erroneous Automatic Steering updates.

## Technical baseline
Technical reference for the C-330 rebuild: [`docs/FS25_C330_TECHNICAL_BASELINE.md`](docs/FS25_C330_TECHNICAL_BASELINE.md).

## Current priority
Validated milestones now include the standard C-330 drivetrain and the base mass / balance / factory ballast stage.

Next isolated subsystem:
- tyre spring/deformation and damping calibration on the basic tyres,
- then liquid rear-tyre ballast as a separate tyre state, including both its mass and its changed tyre compliance/damping,
- followed by tyre traction/radius refinement and later PTO/hydraulics/fuel work.
