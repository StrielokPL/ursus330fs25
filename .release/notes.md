## Ursus C-330 / C-330M 0.0.0.3

Cleanup and **read-only runtime diagnostic** prerelease. This build intentionally does **not** tune the engine, gearbox, mass, tyres, suspension or ballast yet.

### Cleanup included
- fixed four I3D texture references that pointed to missing PNG files while matching DDS assets are present,
- corrected the `$l10n_Yelow` typo,
- replaced the development `TEST` connection-hose title with a localized label,
- corrected generator/dynamo translations including Polish `Prądnica`,
- corrected swapped field/road tyre store labels,
- removed the obsolete fully commented alternative drivetrain block,
- compacted dead comments left by the Static Cabins compatibility patch without changing its behaviour,
- corrected the mass documentation: component mass alone is not total runtime vehicle mass.

### Runtime diagnostics
Temporary `debug/TractorDebugKit.lua` is enabled only for `c330m.xml`. It is read-only and records lines prefixed with `[TRACTORDBG]`:
- front/rear tyre loads and axle split,
- runtime component mass/defaultMass and COM,
- wheel mass, tire load/restLoad and selected suspension/traction parameters,
- active configurations,
- motor, gear and group state,
- differential graph,
- actual gear/group transitions and quick A→B→A oscillation candidates,
- ADS `dynamicMotorLoad` when Advanced Damage System is installed; ADS is optional.

### Suggested first test
1. Start with no attached implement.
2. Use the basic C-330 configuration and wait at least 3 seconds after the tractor is created/loaded.
3. Check configurations with and without front ballast and the available rear wheel-weight variants.
4. Check C-330M as well.
5. Drive through the gearbox in manual and automatic modes if available.
6. Send `log.txt`; the useful lines can be found by searching for `TRACTORDBG`.

The diagnostic code will be removed before a stable release.
