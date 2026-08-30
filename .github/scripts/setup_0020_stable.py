from pathlib import Path
import json
import xml.etree.ElementTree as ET

VERSION = "0.0.2.0"

# Stable milestone: no drivetrain/engine behavior changes from 0.0.1.8.
# Remove only the temporary TractorDebugKit and update release/documentation metadata.

# modDesc
p = Path("modDesc.xml")
s = p.read_text(encoding="utf-8")
s = s.replace("<version>0.0.1.8</version>", f"<version>{VERSION}</version>", 1)
s = s.replace(
    '    <!-- Temporary diagnostics remain enabled during physics/engine development. -->\n'
    '    <extraSourceFiles>\n'
    '        <sourceFile filename="debug/TractorDebugKit.lua" />\n'
    '        <sourceFile filename="Scripts/C330TransmissionFix.lua" />\n'
    '    </extraSourceFiles>',
    '    <extraSourceFiles>\n'
    '        <sourceFile filename="Scripts/C330TransmissionFix.lua" />\n'
    '    </extraSourceFiles>',
    1,
)
p.write_text(s, encoding="utf-8")
ET.parse(p)

# Transmission controller: version label only, behavior unchanged.
p = Path("Scripts/C330TransmissionFix.lua")
s = p.read_text(encoding="utf-8")
s = s.replace(
    "-- 0.0.1.8 TEST: 2 s upshift failsafe, heavy-set top-gear recovery and mass-aware reverse start; ADS-safe.",
    "-- 0.0.2.0 STABLE: validated 2 s upshift failsafe, mass-aware 6F/2R control and ADS-safe operation.",
    1,
)
s = s.replace(
    'Logging.info("[C330TRANS] 0.0.1.8 C-330 6F/2R controller installed (2s upshift failsafe, mass-aware reverse start, ADS-safe)")',
    'Logging.info("[C330TRANS] 0.0.2.0 C-330 6F/2R controller installed (stable, 2s upshift failsafe, mass-aware reverse start, ADS-safe)")',
    1,
)
p.write_text(s, encoding="utf-8")

# Remove temporary runtime diagnostic kit from stable source/package.
dbg = Path("debug/TractorDebugKit.lua")
if dbg.exists():
    dbg.unlink()

# README
p = Path("README.md")
s = p.read_text(encoding="utf-8")
s = s.replace(
    "**0.0.1.8 – C-330 2 s upshift failsafe + mass-aware R-II start prerelease**",
    "**0.0.2.0 – stable C-330 drivetrain milestone**",
    1,
)
s = s.replace(
    "### Runtime diagnostics in 0.0.0.3\nVersion `0.0.0.3` adds a temporary **read-only** `TractorDebugKit` adapted from `strojenieciagnikowfs25`. It does not tune or overwrite vehicle physics. It records the runtime mass/axle-load baseline, component COM, wheel masses and loads, active configurations, motor/gear-group state, differential graph, real shift transitions and optional ADS `dynamicMotorLoad` when ADS is present.\n\nThe diagnostic code is temporary and remains enabled for the engine/physics tuning phase; it must be removed before a stable release.\n",
    "### Runtime diagnostics\nDevelopment builds `0.0.0.3` through `0.0.1.8` used a temporary **read-only** `TractorDebugKit` adapted from `strojenieciagnikowfs25` to validate mass, drivetrain, shift behavior and optional ADS load. The kit did not tune or overwrite vehicle physics.\n\nThe temporary diagnostic kit was removed for stable **0.0.2.0**. It can be restored in a later development branch when another subsystem needs runtime instrumentation.\n",
    1,
)
p.write_text(s, encoding="utf-8")

# CHANGELOG: prepend stable milestone.
p = Path("CHANGELOG.md")
s = p.read_text(encoding="utf-8")
entry = '''## 0.0.2.0 - stable C-330 drivetrain milestone

First full stable release of the rebuilt standard C-330 drivetrain phase. **No engine or transmission behavior is changed from 0.0.1.8.**

### Final 0.0.1.8 validation
- Complete runtime log contained **0 Lua/game errors** and **0 `SHIFT_OSCILLATION` warnings**.
- The generic 2.0 s upshift dwell was observed blocking premature automatic upshifts.
- Light 1.683 t forward starts selected `LIGHT_I3`; light reverse starts selected `LIGHT_RII` / R-II.
- A light R-II start may still fall back to R-I immediately when actual low-rpm load crosses the existing reverse downshift protection; this is intentional safety behavior, not hunting.
- All warnings in the validation log were unrelated to this mod (other-mod l10n/texture warnings, savegame/render warnings).

### Stable drivetrain state
- Factory-style C-330 6F/2R speed ladder with explicit I/II automatic range sequencing.
- 2.0 s minimum automatic upshift dwell and heavy-set II/3 recovery protection.
- Mass-aware starts: <3.175 t -> I/3 forward and R-II reverse; >=3.175 t keeps conservative low-range starts.
- S-312C calibration: 100 Nm maximum at 1600-1800 rpm and ~22.4 kW at 2200 rpm.
- ADS compatibility remains optional, filtered and strictly read-only.
- Static Cabins dirty-flag compatibility fix remains in place.
- C-330M remains outside the custom C-330 drivetrain controller and is reserved for separate calibration.

### Release cleanup
- Removed temporary `debug/TractorDebugKit.lua` from the stable package and `modDesc.xml`.
- Kept `Scripts/C330TransmissionFix.lua` as the production transmission controller.

### Next development subsystem
- Base mass and center-of-mass / axle-load calibration against the 1675 kg and ~38/62 factory target, isolated from tyres, ballast and drivetrain tuning.

'''
if not s.startswith("# Changelog\n\n"):
    raise SystemExit("Unexpected CHANGELOG header")
s = "# Changelog\n\n" + entry + s[len("# Changelog\n\n"):]
p.write_text(s, encoding="utf-8")

# Release config: stable, not prerelease.
release = {
    "version": VERSION,
    "tag": VERSION,
    "title": "0.0.2.0 - C-330 stable drivetrain milestone",
    "prerelease": False,
    "zipName": "FS25_UrsusC330_330M_4x2.zip",
}
Path(".release/release.json").write_text(json.dumps(release, indent=2) + "\n", encoding="utf-8")

notes = '''## Ursus C-330 / C-330M 0.0.2.0

**Full stable release** closing the first standard C-330 drivetrain calibration phase.

### Final validation
The complete 0.0.1.8 runtime test finished with **0 errors** and **0 `SHIFT_OSCILLATION` warnings**. The 2-second upshift failsafe was active in runtime, light 1.683 t starts selected I/3 forward and R-II reverse, and ADS remained read-only. The remaining warnings in the game log were generated by other mods, the savegame or renderer.

### Included C-330 drivetrain
- factory-style 6F/2R speed ladder and explicit I/II automatic sequencing,
- 2.0 s minimum dwell before automatic upshifts,
- heavy-set II/3 load-recovery protection,
- mass-aware start threshold at 3.175 t: light -> I/3 / R-II, heavy -> conservative low-range start,
- S-312C: 100 Nm maximum at 1600-1800 rpm and ~22.4 kW at 2200 rpm,
- ADS-safe filtered read-only load integration,
- existing Static Cabins compatibility protection.

### Release cleanup
Temporary `TractorDebugKit` instrumentation has been removed from the stable package. The production `C330TransmissionFix` controller remains active. No drivetrain behavior was changed from 0.0.1.8.

### Next
The next isolated development step will be **base mass / COM / axle-load distribution**, targeting 1675 kg and approximately 38/62 front/rear without touching tyres, ballast or drivetrain in the same test.
'''
Path(".release/notes.md").write_text(notes, encoding="utf-8")

# Final checks
assert f"<version>{VERSION}</version>" in Path("modDesc.xml").read_text(encoding="utf-8")
assert "debug/TractorDebugKit.lua" not in Path("modDesc.xml").read_text(encoding="utf-8")
assert not Path("debug/TractorDebugKit.lua").exists()
assert json.loads(Path(".release/release.json").read_text(encoding="utf-8"))["prerelease"] is False
print("0.0.2.0 stable setup validated")
