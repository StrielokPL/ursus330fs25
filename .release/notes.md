## Ursus C-330 / C-330M 0.0.1.2

Small compatibility correction between the completed C-330 gearbox controller and the calibrated **100 Nm S-312C** test curve.

### Changed
- prevents full throttle alone from forcing II/1 -> I/3 while engine load is low,
- adds a load-aware predicted-RPM guard for II/2 -> II/3,
- under meaningful load, top gear is blocked if the factory ratio step predicts <1200 rpm after the shift.

### Unchanged
The 0.0.1.1 engine curve, fuel use, gearbox ratios, ADS read-only handling, C-330M and chassis physics are unchanged.

### Test focus
Use C-330 motor=1 with the same heavy trailer. Watch II/2 under load: the controller should log `BLOCK TOP UPSHIFT` instead of dropping II/3 to ~1000 rpm. Also reproduce sustained full throttle in II/1 with moderate/low load; it should no longer unnecessarily reduce to I/3. Send the complete `log.txt`.

<!-- release-trigger-0.0.1.2 -->
