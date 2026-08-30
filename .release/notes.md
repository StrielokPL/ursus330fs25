## Ursus C-330 / C-330M 0.0.0.4

Dedicated **C-330 gearbox test** based on the 0.0.0.3 runtime log. C-330M is intentionally unchanged.

### What changed
- factory C-330 3x2 speed ladder: ~1.825 / 3.537 / 5.649 / 7.389 / 14.324 / 22.878 km/h,
- factory range reduction 4.050,
- reverse targets ~1.533 / 6.207 km/h,
- custom forward automatic range controller,
- explicit heavy-load II/1 -> I/3 downshift,
- controlled I/3 -> II/1 upshift,
- one-mechanical-step limit inside a range,
- cooldown and load/RPM guards against range hunting,
- optional ADS load input with native GIANTS load fallback,
- `[C330TRANS]` logging added; `[TRACTORDBG]` remains enabled.

### Not changed
Engine torque, mass/COM, ballast, tyres, suspension and the C-330M drivetrain are unchanged.

### Test
Use the C-330 (`motor=1`). First drive unloaded through the full speed range, then repeat with the heavy trailer that previously stayed in road range. Send the complete `log.txt`; useful lines are `[TRACTORDBG][SHIFT]` and `[C330TRANS]`.
