## Ursus C-330 / C-330M 0.0.0.6

Diagnostic-only follow-up to the 0.0.0.5 gearbox test. **Gear ratios and shift thresholds are unchanged.**

### Changes
- suppresses false `SHIFT_OSCILLATION` warnings caused by the normal `activeGearIndex=0` disengaged phase,
- adds raw active/target/current gear and direction fields to shift traces,
- adds `[TRACTORDBG][RANGE_CHANGE]` for every actual I/II group change,
- labels a range change as `C330TRANS` when requested by our controller, otherwise `EXTERNAL/GIANTS`,
- keeps ADS strictly read-only and retains the 0.0.0.5 invalid-load fallback,
- keeps Static Cabins / dirty-flag protection unchanged.

### Test
Use **C-330 (motor=1)** with the same heavy trailer. Drive from standstill through both ranges, then deliberately slow it under load and accelerate again. Send the complete `log.txt`; the key lines are `[TRACTORDBG][RANGE_CHANGE]`, `[TRACTORDBG][SHIFT]` and `[C330TRANS]`.
