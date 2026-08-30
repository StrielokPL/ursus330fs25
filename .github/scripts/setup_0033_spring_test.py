from pathlib import Path
import json
import re
import xml.etree.ElementTree as ET

VERSION = "0.0.3.3"

# One physical variable only: wheel/tire vertical spring.
p = Path("c330m.xml")
s = p.read_text(encoding="utf-8")
count = s.count('spring="15"')
if count < 4:
    raise SystemExit(f"Expected wheel spring=15 occurrences, found {count}")
s = s.replace('spring="15"', 'spring="12"')
if s.count('spring="15"') != 0:
    raise SystemExit("Not all spring=15 values were replaced")
p.write_text(s, encoding="utf-8")
ET.parse(p)
print(f"Changed {count} wheel spring values: 15 -> 12")

# Keep the temporary read-only logger, only mark the tested build version.
p = Path("debug/TyreDebugKit.lua")
s = p.read_text(encoding="utf-8")
s = s.replace("-- 0.0.3.2 suspension-travel diagnostic prerelease. Remove from the next stable release.",
              "-- 0.0.3.3 tyre-spring physical test prerelease. Remove from the next stable release.", 1)
s = s.replace(
    '[TYREDBG] TyreDebugKit 0.0.3.2 installed; read-only suspension trace;',
    '[TYREDBG] TyreDebugKit 0.0.3.3 installed; read-only spring-test trace;',
    1,
)
p.write_text(s, encoding="utf-8")

# Mod version.
p = Path("modDesc.xml")
s = p.read_text(encoding="utf-8")
if "<version>0.0.3.2</version>" not in s:
    raise SystemExit("Expected 0.0.3.2 modDesc version not found")
s = s.replace("<version>0.0.3.2</version>", f"<version>{VERSION}</version>", 1)
p.write_text(s, encoding="utf-8")
ET.parse(p)

# README marker.
p = Path("README.md")
s = p.read_text(encoding="utf-8")
s = s.replace(
    "**0.0.3.2 – C-330 suspension-travel diagnostic prerelease**",
    "**0.0.3.3 – C-330 softer tyre-spring test prerelease**",
    1,
)
p.write_text(s, encoding="utf-8")

# Changelog.
p = Path("CHANGELOG.md")
s = p.read_text(encoding="utf-8")
entry = '''## 0.0.3.3 - C-330 softer tyre-spring physical test\n\nFirst physical change in the tyre compliance stage after the 0.0.3.1/0.0.3.2 read-only diagnostics.\n\n### Runtime evidence from 0.0.3.2\n- The added board obstacles of different height and ramp steepness produced a broad and repeatable vertical-load response, so they are suitable as a practical test track.\n- `lastSuspensionLength` stayed exactly **0.0400 m on all four wheels** throughout the run even during strong load impulses; it is therefore not a usable dynamic-travel signal on this vehicle.\n- The repeated first four obstacle responses gave mean single-wheel peak load of about **0.845 t at 1.00 bar** versus **1.003 t at 2.40 bar** (about **+18.7%** at road pressure). Speeds were not identical, so this is treated as directional evidence, not a calibrated stiffness measurement.\n- A later low-pressure impact reached about **1.541 t** on one rear wheel, confirming that the existing setup can still transmit a very sharp obstacle impulse even with the MudSystemPhysics low-pressure radius state.\n- No C-330/tyre Lua errors were produced.\n\n### Isolated physical change\n- Wheel XML spring: **15 -> 12** on every existing C-330/C-330M wheel physics entry that used the common value.\n- GIANTS runtime scaling therefore changes the observed spring from approximately **150 -> 120**.\n- This is a **20% reduction** intended to increase dry tyre compliance and reduce sharp wheel-load spikes without changing damping at the same time.\n\n### Explicitly unchanged\n- `damper=25` and the runtime compression/rebound split derived from it.\n- `suspTravel=0.07`, initialCompression, forcePointRatio, wheel mass, radius, width and stiffness/traction fields.\n- MudSystemPhysics and its pressure/radius/friction behavior.\n- Stable 0.0.3.0 base mass/COM and factory metal ballast.\n- Engine, transmission controller, ADS read-only protection and differential.\n\n### Test focus\nRepeat the same board sequence at **2.40 bar** and **1.00 bar**, preferably keeping the order and approximate speeds similar to the 0.0.3.2 baseline. Subjective notes about bottoming, excessive rocking, or a noticeably softer hit are useful together with the complete log.\n\n'''
if not s.startswith("# Changelog\n\n"):
    raise SystemExit("Unexpected CHANGELOG header")
s = "# Changelog\n\n" + entry + s[len("# Changelog\n\n"):]
p.write_text(s, encoding="utf-8")

release = {
    "version": VERSION,
    "tag": VERSION,
    "title": "0.0.3.3 - C-330 softer tyre-spring test",
    "prerelease": True,
    "zipName": "FS25_UrsusC330_330M_4x2.zip",
}
Path(".release/release.json").write_text(json.dumps(release, indent=2) + "\n", encoding="utf-8")

notes = '''## Ursus C-330 / C-330M 0.0.3.3\n\n**First physical tyre-compliance test after the read-only diagnostics.**\n\n### Change\n- Common wheel spring **15 -> 12** (**-20%**, runtime about **150 -> 120**).\n- `damper=25` and `suspTravel=0.07` stay unchanged so the spring effect can be judged in isolation.\n\n### Why\nThe 0.0.3.2 multi-height/multi-ramp board route produced repeatable load impulses and showed that the current setup can still deliver very sharp wheel-load peaks. The attempted `lastSuspensionLength` signal stayed fixed at 0.0400 m and is not used for the decision.\n\n### Test\n1. Use the same basic Polowe wheel configuration and board sequence.\n2. Run once at **2.40 bar** after pressure settles.\n3. Run once at **1.00 bar** after pressure settles.\n4. Similar obstacle order and speed are more important than an exact speed target.\n5. Note if any obstacle causes obvious bottoming, excessive rocking, or a much softer/cleaner hit.\n6. Send the complete `log.txt`.\n\nAll engine/transmission/ADS behavior, mass/COM/ballast, tire dimensions/traction and MudSystemPhysics are unchanged.\n'''
Path(".release/notes.md").write_text(notes, encoding="utf-8")
