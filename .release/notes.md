## Ursus C-330 / C-330M 0.0.0.5

Second **C-330 gearbox test**, focused on ADS safety and eliminating range hunting seen in the 0.0.0.4 runtime log.

### Changes
- keeps factory C-330 gearing and successful `II/1 -> I/3` heavy-load reduction,
- `I/3 -> II/1` now requires >=2050 rpm, <=0.55 load and 800 ms of sustained recovery,
- post-downshift recovery hold increased to 2.5 s,
- range cooldown increased to 0.8 s,
- ADS `dynamicMotorLoad` is strictly read-only and accepted only when approximately within 0..1,
- invalid/negative ADS shift samples fall back to native GIANTS smoothed load,
- Static Cabins / dirty-flag compatibility protection remains unchanged.

### Test
Use **C-330 (motor=1)**. Test unloaded acceleration, then the same heavy trailer. The key check is whether it now stays in range I while the load remains high instead of oscillating around `I/3 <-> II/1`. Send the complete `log.txt`.
