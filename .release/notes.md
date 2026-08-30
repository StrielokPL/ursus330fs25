## Ursus C-330 / C-330M 0.0.1.6

Refined high-load top-gear protection test.

### Changed
- II/2 -> II/3 now treats **load >=0.70** as high load instead of >=0.80,
- the high-load minimum remains **2100 rpm**,
- existing moderate-load predicted-RPM protection remains unchanged.

### Why
In the 0.0.1.5 trailer test one shift occurred at 2088 rpm / 0.757 ADS and landed near 1112 rpm / 0.908 load in II/3. The 0.80 gate therefore missed a real loaded event because the instantaneous ADS sample had already dipped below 0.80.

### Unchanged
Mass-aware starting, the 3.175 t threshold, range-boundary logic, reverse controller, 100 Nm S-312C curve, gearbox ratios, fuel use, ADS read-only handling, C-330M and chassis physics are unchanged.

### Test focus
Repeat one pass without a trailer and one with the same trailer. The loaded run should log `BLOCK TOP UPSHIFT HIGH LOAD` when II/2 requests II/3 below 2100 rpm at load >=0.70, and should no longer land close to 1100 rpm under ~0.9 load. Send the complete `log.txt`.
