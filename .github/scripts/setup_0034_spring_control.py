from pathlib import Path
import json
import xml.etree.ElementTree as ET

VERSION = "0.0.3.4"

# A/B control only: restore the original common wheel spring.
p = Path("c330m.xml")
s = p.read_text(encoding="utf-8")
count = s.count('spring="12"')
if count < 4:
    raise SystemExit(f"Expected spring=12 occurrences from 0.0.3.3, found {count}")
s = s.replace('spring="12"', 'spring="15"')
if 'spring="12"' in s:
    raise SystemExit("Not all spring=12 values were restored")
p.write_text(s, encoding="utf-8")
ET.parse(p)
print(f"Restored {count} wheel spring values: 12 -> 15")

# Keep the temporary read-only logger and only update its build marker.
p = Path("debug/TyreDebugKit.lua")
s = p.read_text(encoding="utf-8")
s = s.replace("0.0.3.3", VERSION)
s = s.replace("tyre-spring physical test prerelease", "spring-control A/B prerelease")
s = s.replace("spring-test trace", "spring-control trace")
p.write_text(s, encoding="utf-8")

# Mod version.
p = Path("modDesc.xml")
s = p.read_text(encoding="utf-8")
if "<version>0.0.3.3</version>" not in s:
    raise SystemExit("Expected 0.0.3.3 modDesc version not found")
s = s.replace("<version>0.0.3.3</version>", f"<version>{VERSION}</version>", 1)
p.write_text(s, encoding="utf-8")
ET.parse(p)

# README current version marker.
p = Path("README.md")
s = p.read_text(encoding="utf-8")
s = s.replace(
    "**0.0.3.3 – C-330 softer tyre-spring test prerelease**",
    "**0.0.3.4 – C-330 spring=15 A/B control prerelease**",
    1,
)
p.write_text(s, encoding="utf-8")

# Changelog entry.
p = Path("CHANGELOG.md")
s = p.read_text(encoding="utf-8")
entry = '''## 0.0.3.4 - C-330 spring=15 standardized A/B control\n\nControl build for the stabilized obstacle-test protocol introduced during the 0.0.3.3 runtime test. This intentionally restores the pre-0.0.3.3 common spring so the spring change can be compared under the same driving conditions.\n\n### New standardized test protocol\n- Basic C-330 / Polowe wheel configuration, no ballast or attachment changes.\n- Board set, pallet truck and campfire at cruise control **10 km/h**.\n- One single board at tractor **Vmax**.\n- Repeat the sequence at settled MudSystemPhysics **2.40 bar** and **1.00 bar**.\n- Keep obstacle order and line as consistent as practical.\n\n### 0.0.3.3 spring=12 reference\n- Runtime spring was confirmed at **120** with `suspTravel=0.07`.\n- The controlled 10 km/h portions averaged about **9.90 km/h at 2.40 bar** and **9.92 km/h at 1.00 bar**.\n- Peak single-wheel load in those standardized portions was **1.551 t at 2.40 bar** and **1.562 t at 1.00 bar**.\n- The Vmax board runs reached **23.05 km/h** and **22.97 km/h** respectively; observed single-wheel peaks were **1.650 t** and **1.987 t**. These peaks are treated as comparative runtime indicators because the logger samples at finite intervals.\n- The 0.0.3.3 run had **0 `Error:`**, **0 Lua stack errors** and **0 `SHIFT_OSCILLATION`**.\n\n### Isolated control change\n- Common wheel XML spring: **12 -> 15** on all entries changed by 0.0.3.3.\n- Expected GIANTS runtime spring: approximately **120 -> 150**.\n- This is an A/B control, not an assertion that 15 is the final value.\n\n### Explicitly unchanged\n- `damper=25`, `suspTravel=0.07`, initialCompression and forcePointRatio.\n- Wheel mass, dimensions, stiffness and traction fields.\n- MudSystemPhysics pressure/radius/friction behavior.\n- Stable mass/COM/factory ballast.\n- Engine, transmission controller, ADS read-only protection and differential.\n\n### Decision after test\nCompare 0.0.3.4 directly with the standardized 0.0.3.3 run. Only then choose whether the next spring should stay at 15, return to 12, or use an intermediate value.\n\n'''
if not s.startswith("# Changelog\n\n"):
    raise SystemExit("Unexpected CHANGELOG header")
s = "# Changelog\n\n" + entry + s[len("# Changelog\n\n"):]
p.write_text(s, encoding="utf-8")

release = {
    "version": VERSION,
    "tag": VERSION,
    "title": "0.0.3.4 - C-330 spring=15 standardized control",
    "prerelease": True,
    "zipName": "FS25_UrsusC330_330M_4x2.zip",
}
Path(".release/release.json").write_text(json.dumps(release, indent=2) + "\n", encoding="utf-8")

notes = '''## Ursus C-330 / C-330M 0.0.3.4\n\n**A/B control for the new stabilized obstacle-test protocol.**\n\n### Change\n- Common wheel spring **12 -> 15** (runtime expected about **120 -> 150**).\n- This deliberately restores the pre-0.0.3.3 spring for one controlled comparison. It is not yet a final tuning decision.\n\n### Why\nThe test method changed after spring had already been reduced in 0.0.3.3. The 0.0.3.3 log is therefore the first clean baseline for the new route, but there is no spring=15 run under exactly the same conditions. 0.0.3.4 supplies that missing control.\n\n### Repeat exactly\n1. Basic Polowe C-330, same configuration.\n2. Let **2.40 bar** settle.\n3. Board set + pallet truck + campfire on cruise control **10 km/h**.\n4. Single board at **Vmax**.\n5. Let **1.00 bar** settle and repeat the same two tests.\n6. Keep the same line/order as closely as practical and send the complete `log.txt`.\n\n`damper=25`, `suspTravel=0.07`, tyre dimensions/traction, MudSystemPhysics, mass/COM/ballast, engine/transmission/ADS and differential are unchanged.\n'''
Path(".release/notes.md").write_text(notes, encoding="utf-8")
