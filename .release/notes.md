## Ursus C-330 / C-330M 0.0.1.5

Isolated high-load top-gear protection test.

### Changed
- II/2 -> II/3 is now blocked below **2100 rpm** whenever current engine load is **>=0.80**,
- the existing predicted post-shift RPM protection remains active for moderate load,
- a new `BLOCK TOP UPSHIFT HIGH LOAD` diagnostic identifies this specific guard.

### Unchanged
The 0.0.1.4 mass-aware I/3 start rule, range-boundary logic, reverse controller, 100 Nm S-312C curve, gearbox ratios, fuel use, ADS read-only handling, C-330M and chassis physics are unchanged.

### Why
The 0.0.1.4 hill test allowed II/3 at roughly 1976 rpm / 0.878 load and the engine landed near 974 rpm / 0.990 load. Similar high-load cases landed around 1065-1167 rpm. A 2137 rpm / 0.822 shift recovered around 1550 rpm, so 2100 rpm is the isolated test threshold.

### Test focus
Repeat a flat acceleration and, most importantly, the same uphill/downhill stop-and-restart sequence. On a climb, high-load II/2 should log `BLOCK TOP UPSHIFT HIGH LOAD` until about 2100 rpm instead of dropping the engine toward 1000 rpm in II/3. Send the complete `log.txt`.
