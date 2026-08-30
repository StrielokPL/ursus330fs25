## Ursus C-330 / C-330M 0.0.3.0

**Stable mass / balance milestone.** No physics values changed from validated 0.0.2.3; this release promotes the tested state and removes temporary mass diagnostics.

### Validated C-330 mass state
- base ready-to-work mass: **1675 kg**;
- base axle loads: **634 / 1041 kg (37.86 / 62.14%)**;
- factory front metal ballast: **42 kg**;
- rear metal ballast: **40 kg Small / 144 kg Big / 184 kg Both**;
- full factory metal ballast: **226 kg**, giving **1901 kg** total.

The 0.0.2.3 test matrix reproduced each configured mass exactly and confirmed additive front/rear behavior. The complete runtime log had no C-330 Lua/game errors or oscillation warnings.

### Stable cleanup
Temporary `TractorDebugKit` mass diagnostics are removed. The production 0.0.2.0 drivetrain controller remains unchanged.

### Next development stage
Tyre spring/deformation/damping calibration. Liquid ballast will be modeled afterward as a separate rear-tyre state with both added liquid mass and altered tyre compliance/damping, rather than as mass alone.
