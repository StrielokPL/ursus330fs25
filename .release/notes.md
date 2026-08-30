## Ursus C-330 / C-330M 0.0.1.7

Heavy-set II/3 stability test.

### Changed
- for tractor+equipment total mass **>= 3.175 t**, II/2 -> II/3 requires filtered load **< 0.70 continuously for 600 ms**,
- any return to load >=0.70 resets that timer,
- light sets below 3.175 t retain the previous behavior.

### Why
0.0.1.6 correctly started blocking high-load top-gear requests, but two trailer shifts still passed after very short ADS dips below 0.70 (~0.15 s and ~0.27 s). After the shifts the load rose back to roughly 0.77-0.88. Acceptable trailer cases showed a much longer low-load recovery (~0.75-0.82 s), so 600 ms separates the two groups without slowing the unloaded tractor.

### Unchanged
Mass-aware starting, range-boundary logic, reverse controller, 100 Nm S-312C curve, gearbox ratios, fuel use, ADS read-only handling, C-330M and chassis physics are unchanged.

### Test focus
Repeat one pass without a trailer and one with the same trailer. With the trailer, expect `BLOCK TOP UPSHIFT HEAVY SET` and/or `BLOCK TOP UPSHIFT STABILIZE` until load has stayed below 0.70 for 600 ms. Check that II/3 no longer lands near 1100-1250 rpm under ~0.85-0.90 load. Send the complete `log.txt`.
