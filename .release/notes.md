## Ursus C-330 / C-330M 0.0.4.3

**Full career-stable release.** This promotes the validated 0.0.4.3 shop-cleanup build to a normal release without changing the calibrated physics or transmission behavior.

### Stable status

- **Singleplayer / career:** validated and considered stable.
- **Multiplayer for the current rebuild:** **not yet fully validated** with host + second client / dedicated server.
- Final validation log contained no C-330 Lua errors or call stacks.
- Temporary `TractorDebugKit` / `TyreDebugKit` tooling is not included in the release ZIP.
- Production diagnostic `Logging.info` spam from the transmission, liquid-ballast and shop-order helpers has been removed/silenced.

### Shop and configuration cleanup

Verified top sequence:

**Engine -> Wheels -> Water -> Front ballast -> Cabin -> Loader console**

The ordering hook is local to `c330m.xml` and does not alter global GIANTS configuration priorities for other vehicles.

Rear metal wheel weights remain inside **Wheels** because their meshes and physical mass are implemented as wheel sub-configurations; separating them would be a larger physics/save-format refactor.

### Final calibrated state

- Base C-330 mass: **1675 kg**, approximately **38/62 front/rear**.
- Factory front ballast: **42 kg**.
- Rear metal ballast variants: **40 / 144 / 184 kg**.
- Dry tyres: **spring 12 / damper 22 / suspTravel 0.07**.
- Rear tyre water ballast: **+132 kg per rear wheel / +264 kg total**.
- Water-filled rear tyres: approximately **spring 14 / damper 30**.
- Factory-style C-330 automatic sequence: `I/1 -> I/2 -> I/3 -> II/1 -> II/2 -> II/3` with the validated dwell/load/RPM protections.
- Advanced Damage System integration remains optional and read-only; invalid ADS load samples fall back to the native GIANTS load signal.

### Last validation environment

Farming Simulator 25 **1.21.1.0** with these active script/physics mods:

- Advanced Damage System **0.9.2.4**,
- MudSystemPhysics **1.3.1.0**,
- Mud Sprayer **1.0.0.0**,
- tireSound **1.0.0.0**,
- toggleSuperStrength **1.1.0.0**,
- Vehicle Years **1.0.0.6**.

The extreme hill test also included heavy trailer loading and severe rear-wheel slip. One unusual range transition seen there was traced to wheel slip and trailer geometry unloading/lifting the driven rear axle; no equivalent anomaly was observed in normal career use, so no transmission retune was made for that artificial case.

### Multiplayer / dirty-flag history

The source package imported for this rebuild already contained the earlier **Static Cabins** dirty-flag compatibility fix. The original C-330 consumed nearly the whole 32-bit dirty-flag budget and could collide with ADS/AIAutomaticSteering in multiplayer. The fix removed 18 unnecessary cabin `movingTool` definitions and related controls/animations while preserving cabin variants as static geometry.

That historical investigation led to AI Automatic Steering Fix (AIASF):
https://github.com/StrielokPL/Farming25fixnmix

The earlier Static Cabins fix was successfully tested in multiplayer with ADS 0.9.2.4 and AIASF debug. **That historical result does not replace a full multiplayer validation of the current 0.0.4.3 rebuild.**

Detailed current validation status is kept in `docs/VALIDATION_STATUS.md`.

<!-- release-final-tag-sync -->
