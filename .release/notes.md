## Ursus C-330 / C-330M 0.0.5.0 D2

**Diagnostic hotfix prerelease.** Gameplay calibration is unchanged from 0.0.5.0/D1: no engine curve, ratio, shift threshold or transmission-controller rule is changed here.

D2 fixes the diagnostic layer itself after D1 caused severe frame/update stalls and corrupted-looking automatic gearbox behaviour.

### Root cause fixed

D1 called `tonumber(safeCall(vehicle, "getSpeedLimit", ...))`. `getSpeedLimit()` can return a second boolean value. Lua expanded that second return value into `tonumber()` as its optional base argument, producing:

`C330FullDiagnostic.lua:124: invalid argument #2 to 'tonumber' (number expected, got boolean)`

That exception occurred inside the wrapper around `findGearChangeTargetGearPrediction()`. The real C330 controller had already made its decision, but the diagnostic exception could abort the surrounding vehicle update before the result was returned to GIANTS. This explains both the massive lag/UI lockups and impossible-looking gearbox states such as a range change occurring while the old gear target remained active.

D1 also wrote some diagnostic events every frame, including repeated start-gear and prediction lines, creating excessive synchronous `log.txt` I/O.

### D2 diagnostic architecture

- Critical transmission hooks are now **RAM-only**: they copy primitive state and immediately return the original GIANTS/C330 result.
- No `Logging`, `getSpeedLimit`, mass probe, implement scan or formatting runs inside the transmission prediction path.
- `getSpeedLimit()` results are captured explicitly as a single return value before conversion.
- State snapshots are flushed outside the drivetrain path every **250 ms**.
- Implement/rear-wheel summaries are flushed every **1000 ms**.
- Prediction/start information is logged only when its meaningful state changes, not every frame.
- Range and gear events are recorded only for actual requested changes.
- The whole deferred diagnostic flush is protected by `pcall`; if any future diagnostic probe fails, diagnostics disable themselves for that tractor after one warning instead of repeatedly breaking `VehicleMotor.update`.

Log prefix remains **`[C330FULLDIAG]`**.

### Important local cleanup

An old separate `FS25_ZZ_C330FullDiagnostic` package may still be present in the local mods directory from earlier testing. It is no longer required. D2 diagnostics are inside the Ursus ZIP. Delete the old separate diagnostic ZIP/folder to avoid confusion; it was visible in the D1 test log as an available mod but was not selected in the shown save load.

### Test

1. Replace D1 with D2 and remove the old separate `FS25_ZZ_C330FullDiagnostic` from the mods folder.
2. Test C-330 first: automatic start, `I/3 -> II/1 -> II/2 -> II/3`, braking/downshifts, menu open/close and camera following.
3. Test C-330M with the same small period plow as before: lowered work, uphill/downhill, then brief lift/lower while moving.
4. Send the complete `log.txt`.

Expected D2 behaviour: no recurring `Error: Running LUA method 'update'` from `C330FullDiagnostic.lua`, no diagnostic-induced camera/UI stalls, and gearbox behaviour should return to the underlying 0.0.5.0 controller behaviour so the original C-330M plow issue can be measured cleanly.
