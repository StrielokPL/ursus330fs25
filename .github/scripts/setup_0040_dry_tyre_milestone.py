from pathlib import Path
import json
import xml.etree.ElementTree as ET

VERSION = "0.0.4.0"

# Validate selected dry-tyre physics baseline from 0.0.3.5.
p = Path("c330m.xml")
s = p.read_text(encoding="utf-8")
if s.count('spring="12"') != 40:
    raise SystemExit(f"Expected 40 spring=12 entries, found {s.count('spring=\"12\"')}")
if s.count('damper="22"') != 40:
    raise SystemExit(f"Expected 40 damper=22 entries, found {s.count('damper=\"22\"')}")
ET.parse(p)

# Remove temporary tyre diagnostics from modDesc, preserve production transmission controller.
p = Path("modDesc.xml")
s = p.read_text(encoding="utf-8")
if "<version>0.0.3.5</version>" not in s:
    raise SystemExit("Expected 0.0.3.5 modDesc version not found")
s = s.replace("<version>0.0.3.5</version>", f"<version>{VERSION}</version>", 1)
s = s.replace('    <sourceFile filename="debug/TyreDebugKit.lua" />\n', '', 1)
if 'debug/TyreDebugKit.lua' in s:
    raise SystemExit("TyreDebugKit still referenced by modDesc")
if 'Scripts/C330TransmissionFix.lua' not in s:
    raise SystemExit("Production transmission controller reference missing")
p.write_text(s, encoding="utf-8")
ET.parse(p)

# README marker.
p = Path("README.md")
s = p.read_text(encoding="utf-8")
s = s.replace(
    "**0.0.3.5 – C-330 damper=22 tyre test prerelease**",
    "**0.0.4.0 – C-330 dry tyre physics milestone**",
    1,
)
p.write_text(s, encoding="utf-8")

# Changelog.
p = Path("CHANGELOG.md")
s = p.read_text(encoding="utf-8")
entry = '''## 0.0.4.0 - C-330 dry tyre physics milestone\n\nStable milestone closing the first dry-tyre spring/damper tuning phase.\n\n### Selected dry-tyre baseline\n- Common wheel spring: **12** (runtime ~120), selected after standardized A/B against the original spring 15.\n- Common wheel damper: **22**, selected after direct comparison against damper 25 on the spring=12 baseline.\n- `suspTravel=0.07` unchanged.\n\n### Runtime validation\n- Standardized route: board set + pallet truck + campfire at cruise control 10 km/h; single board at Vmax.\n- Tested at settled 2.40 bar and 1.00 bar using MudSystemPhysics.\n- Damper 22 reduced the maximum single-wheel load on the 10 km/h route at both pressures and reduced zero-contact samples compared with damper 25.\n- No C-330 errors, Lua call stacks or transmission oscillation markers were observed in the validation log.\n\n### Diagnostic cleanup\n- Temporary `debug/TyreDebugKit.lua` source reference removed from `modDesc.xml` for the stable package.\n- Production `Scripts/C330TransmissionFix.lua` retained.\n\n### Explicitly unchanged\n- Mass/COM and factory metal ballast.\n- Wheel geometry, tyre widths/radii, friction/stiffness values and MudSystemPhysics pressure behavior.\n- Engine, transmission logic, differential and ADS protection.\n\n### Next phase\nLiquid ballast in rear tyres will be developed separately, including both physical added mass and a distinct filled-tyre spring/damping response.\n\n'''
if not s.startswith("# Changelog\n\n"):
    raise SystemExit("Unexpected CHANGELOG header")
s = "# Changelog\n\n" + entry + s[len("# Changelog\n\n"):]
p.write_text(s, encoding="utf-8")

release = {
    "version": VERSION,
    "tag": VERSION,
    "title": "0.0.4.0 - C-330 dry tyre physics milestone",
    "prerelease": False,
    "zipName": "FS25_UrsusC330_330M_4x2.zip",
}
Path(".release/release.json").write_text(json.dumps(release, indent=2) + "\n", encoding="utf-8")

notes = '''## Ursus C-330 / C-330M 0.0.4.0\n\n**Stable dry-tyre physics milestone.**\n\n### Selected values\n- Wheel spring **12** (runtime ~120).\n- Wheel damper **22**.\n- Suspension travel remains **0.07 m**.\n\nThese values were selected from standardized obstacle tests at 10 km/h plus a single-board Vmax test at 2.40 and 1.00 bar with MudSystemPhysics. Compared with spring=12 / damper=25, damper=22 reduced the single-wheel peak on the repeatable 10 km/h route at both pressures and reduced zero-contact samples.\n\nTemporary tyre diagnostics are removed from the stable package. Mass/COM, metal ballast, wheel geometry/traction, engine, transmission, differential, MudSystemPhysics behavior and ADS protection are unchanged.\n\nNext development phase: rear tyre liquid ballast with physical mass plus a dedicated filled-tyre response.\n'''
Path(".release/notes.md").write_text(notes, encoding="utf-8")
print("Prepared 0.0.4.0 stable dry tyre milestone")
