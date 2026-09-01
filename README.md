# Ursus C-330 / C-330M for Farming Simulator 25

Working repository for analysis, correction and further development of the FS25 Ursus C-330 / C-330M 4x2 mod.

## Authors
**StrielokPL**, Speedy, Miziuu

## Current release
**0.0.4.3 – career-stable full release**

The repository was imported from mod package version **1.1.2.0**, but the project versioning was reset for the rebuild. Version `0.0.0.2` is the first documented development baseline in this repository.

### Validation status

- **Singleplayer / career:** stable.
- **Current rebuild multiplayer:** **not yet fully validated** with host + second client / dedicated server.
- Last validation snapshot: Farming Simulator 25 **1.21.1.0**.
- Detailed status and test matrix: [`docs/VALIDATION_STATUS.md`](docs/VALIDATION_STATUS.md).

The last career validation session loaded the C-330 together with:

- Advanced Damage System **0.9.2.4**,
- MudSystemPhysics **1.3.1.0**,
- Mud Sprayer **1.0.0.0**,
- tireSound **1.0.0.0**,
- toggleSuperStrength **1.1.0.0**,
- Vehicle Years **1.0.0.6**.

No C-330 Lua error or call stack was observed in the final 0.0.4.3 validation log.

## Stable rebuild state

### Standard C-330 drivetrain

The C-330 uses a calibrated factory-style 6F/2R automatic sequence:

`I/1 -> I/2 -> I/3 -> II/1 -> II/2 -> II/3`

The controller includes mass-aware starts, load/RPM-aware range changes, a 2-second minimum automatic upshift dwell and dedicated protection for the large II/2 -> II/3 step. Advanced Damage System integration is optional and strictly read-only; invalid ADS load samples fall back to the native GIANTS load signal.

C-330M remains intentionally outside the custom C-330 transmission controller and is reserved for separate calibration.

### Mass and factory ballast

Validated standard C-330 targets:

- base ready-to-work mass: **1675 kg**,
- base axle split: approximately **38% front / 62% rear**,
- front factory ballast: **42 kg**,
- rear metal ballast variants: **40 / 144 / 184 kg**,
- full factory metal ballast: **226 kg**, approximately **1901 kg total**.

### Tyres and suspension

Dry tyre baseline selected through standardized A/B testing:

- spring **12**,
- damper **22**,
- `suspTravel=0.07`.

MudSystemPhysics remains responsible for its pressure/radius/friction layer and is not overwritten by the C-330 scripts.

### Liquid ballast

Optional rear-tyre water ballast:

- **+132 kg per rear wheel**,
- **+264 kg total**,
- filled-tyre spring approximately **14**,
- filled-tyre damper approximately **30**,
- independent of the existing rear metal wheel weights.

### Shop cleanup

The C-330-only shop-order helper places the main functional selectors first:

**Engine -> Wheels -> Water -> Front ballast -> Cabin -> Loader console**

It returns a locally reordered list only while `c330m.xml` is open in the shop and does not change global GIANTS configuration priorities for other vehicles.

## Runtime diagnostics history

Development builds used temporary read-only tooling to establish runtime facts before tuning:

- `TractorDebugKit` for mass, COM, configuration, drivetrain and transmission tracing,
- `TyreDebugKit` for high-rate wheel load, spring/damper, suspension and MudSystemPhysics pressure diagnostics.

The temporary debug kits are **not included in the full 0.0.4.3 release**. Production diagnostic `Logging.info` spam from the transmission, water-ballast and shop-order helpers is also disabled/removed for the stable package.

Reusable diagnostic versions are preserved in:
https://github.com/StrielokPL/strojenieciagnikowfs25

## Static Cabins / dirty-flag compatibility fix

The source package imported into this repository already contained the previously tested **Static Cabins** compatibility fix from `Farming25fixnmix`, so the patch was **not applied again** during this rebuild.

The original C-330 consumed almost the entire 32-bit dirty-flag budget. High bits became shared by multiple systems, including AIAutomaticSteering, AttacherJoints, MoveableMirrors, dirt state and Advanced Damage System. In multiplayer this could make an ADS dirty flag look like an Automatic Steering update and lead to a crash in `writeSegmentStatesToStream` while `steeringFieldCourse` was nil.

The Static Cabins fix:

- removes 18 cabin-related `movingTool` definitions,
- removes the corresponding Interactive Control entries,
- removes cabin door/window/roof animations,
- keeps all cabin configurations available as static geometry,
- leaves only the technical tractor `movingTool` definitions,
- recovers 18 dirty flags and substantially reduces the collision risk.

This investigation led to the creation of **AI Automatic Steering Fix (AIASF)**:
https://github.com/StrielokPL/Farming25fixnmix

The historical dirty-flag fix was successfully tested in multiplayer with Advanced Damage System 0.9.2.4 and AIASF debug. That historical result does **not** mean the current 0.0.4.3 rebuild has already completed its own multiplayer validation.

## Technical reference

Technical reference for the C-330 rebuild:
[`docs/FS25_C330_TECHNICAL_BASELINE.md`](docs/FS25_C330_TECHNICAL_BASELINE.md)

Current validation matrix:
[`docs/VALIDATION_STATUS.md`](docs/VALIDATION_STATUS.md)

## Next priority

The physics/configuration stage represented by 0.0.4.3 is accepted as stable for normal career play. The next validation priority is a complete **multiplayer host/client pass** of the current rebuild. Further feature work such as PTO, hydraulics, fuel behavior or separate C-330M calibration should remain isolated from that MP validation baseline.
