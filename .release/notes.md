## Ursus C-330 / C-330M 0.0.0.7

Final dedicated C-330 gearbox test: automatic range control now covers the complete **6F/2R** transmission.

### Changes
- keeps the validated forward `I/1 -> I/2 -> I/3 -> II/1 -> II/2 -> II/3` logic unchanged,
- takes control of reverse range selection from GIANTS,
- treats reverse as `R-I` (~1.53 km/h) and `R-II` (~6.21 km/h),
- only permits `R-I -> R-II` after sustained high-rpm / low-load recovery,
- protects `R-II` by downshifting to `R-I` under low-rpm high-load demand,
- forces range I for automatic start/restart,
- keeps manual modes unchanged,
- keeps ADS optional, read-only and filtered; Static Cabins protection is unchanged.

### Test
Use **C-330 (motor=1)**. Test forward as before, then reverse both unloaded and with the heavy trailer. In particular verify that a loaded tractor does not jump to R-II around 1.5 km/h, while an unloaded/lightly loaded tractor can reach R-II after R-I tops out. Send the complete `log.txt`.

<!-- release-trigger-0.0.0.7 -->
