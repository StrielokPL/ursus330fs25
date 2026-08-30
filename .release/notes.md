## Ursus C-330 / C-330M 0.0.1.8

Transmission finalization test based on the complete 0.0.1.7 log.

### Changed
- automatic upshifts cannot occur earlier than **2.0 s after the current mechanical gear/range settles**,
- heavy sets (>=3.175 t) require **2.0 s continuous load <0.70** before II/3,
- light sets (<3.175 t) now start reverse directly in **R-II**, matching the forward light-start mass rule,
- heavy sets (>=3.175 t) still start reverse in **R-I**.

### Why
0.0.1.7 was free of shift oscillation and Lua errors, but the 600 ms heavy-set top-gear window still allowed one II/3 engagement to settle near 1180 rpm / 0.846 ADS load and another near 1225 rpm / 0.783. Both recovered, so the remaining change is a conservative timing safeguard rather than a ratio or torque retune.

### Unchanged
Factory ratios, 100 Nm S-312C curve, forward/downshift thresholds, fuel, chassis physics, ADS read-only protection and C-330M are unchanged.

### Test focus
Test four starts if practical: forward light, forward >=3.175 t, reverse light, reverse >=3.175 t. Confirm light reverse logs `START REVERSE R-II`, heavy reverse logs `START REVERSE R-I`, and automatic upshifts show at least 2 s settled-gear dwell. With the heavy trailer, verify II/3 only follows 2 s continuous load below 0.70 and does not create hunting. Send the complete `log.txt`.
