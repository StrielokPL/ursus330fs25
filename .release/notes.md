## Ursus C-330 / C-330M 0.0.1.0

Milestone release closing the dedicated **C-330 6F/2R gearbox** phase.

### Validated gearbox state
- factory C-330 range reduction and nominal 6F/2R speeds retained,
- complete automatic forward sequence `I/1 -> I/2 -> I/3 -> II/1 -> II/2 -> II/3`,
- reverse automatic handled as `R-I -> R-II`,
- GIANTS automatic I/II group selection is suppressed for the C-330 automatic mode,
- ADS-aware load protection remains optional, filtered and read-only,
- manual transmission modes and C-330M remain untouched.

The final 0.0.0.7 runtime test showed no external/GIANTS range changes, no shift-oscillation warnings and no C-330/ADS/controller Lua errors.

### Next phase
Temporary diagnostics remain enabled. The next isolated subsystem is the **S-312C engine torque/power/fuel calibration**.

<!-- release-trigger-0.0.1.0 -->
