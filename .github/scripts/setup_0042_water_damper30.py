from pathlib import Path
import json
import xml.etree.ElementTree as ET

VERSION = "0.0.4.2"

# Water runtime layer: keep mass and spring, isolate damping change 26 -> 30.
p = Path("Scripts/C330LiquidBallast.lua")
s = p.read_text(encoding="utf-8")
if "damperRatio = 26 / 22" not in s or "springRatio = 14 / 12" not in s:
    raise SystemExit("Expected 0.0.4.1 liquid ballast baseline not found")
s = s.replace("0.0.4.1 prerelease", "0.0.4.2 prerelease", 1)
s = s.replace("damperRatio = 26 / 22", "damperRatio = 30 / 22", 1)
s = s.replace("targetApprox=14/26", "targetApprox=14/30")
s = s.replace("0.0.4.1 liquid ballast layer installed", "0.0.4.2 liquid ballast layer installed")
s = s.replace("spring=14 damper=26", "spring=14 damper=30")
p.write_text(s, encoding="utf-8")

# modDesc version only; source list remains the same.
p = Path("modDesc.xml")
s = p.read_text(encoding="utf-8")
if "<version>0.0.4.1</version>" not in s:
    raise SystemExit("Expected modDesc 0.0.4.1")
s = s.replace("<version>0.0.4.1</version>", f"<version>{VERSION}</version>", 1)
p.write_text(s, encoding="utf-8")
ET.parse(p)

# Keep temporary logger, but make its build label accurate.
p = Path("debug/TyreDebugKit.lua")
s = p.read_text(encoding="utf-8")
s = s.replace("0.0.4.1 liquid-ballast physical test prerelease", "0.0.4.2 water-damper physical test prerelease")
s = s.replace("TyreDebugKit 0.0.3.5 installed", "TyreDebugKit 0.0.4.2 installed")
p.write_text(s, encoding="utf-8")

# README development label.
p = Path("README.md")
s = p.read_text(encoding="utf-8")
s = s.replace("**0.0.4.1 – C-330 rear tyre liquid ballast prototype**", "**0.0.4.2 – C-330 water-ballast damper=30 test**", 1)
p.write_text(s, encoding="utf-8")

# Changelog.
p = Path("CHANGELOG.md")
s = p.read_text(encoding="utf-8")
entry = '''## 0.0.4.2 - C-330 water-ballast damper=30 test\n\nSecond liquid-ballast prerelease. It isolates rear filled-tyre damping after 0.0.4.1 confirmed the shop option, +132 kg per rear wheel, axle distribution and MudSystemPhysics compatibility.\n\n### Changed\n- Water-filled rear tyre damping: **26 -> 30**.\n- Water-filled rear tyre spring remains **14**.\n- Liquid mass remains **+132 kg per rear wheel**.\n\n### Why\nThe standardized 10 km/h water test showed full rear-axle unloading followed roughly 0.13 s later by a strong reload around 1.14 t per rear wheel at low pressure. The added rear wheel mass is about 56.9% above dry wheel mass, while 0.0.4.1 damping increased only 18.2%. A simple mass/spring damping scaling places the next useful test point near 30.\n\n### Unchanged\n- Dry tyres remain **spring 12 / damper 22 / suspTravel 0.07**.\n- Filled rear spring remains **14** and suspension travel remains **0.07**.\n- Liquid mass, wheel geometry, base mass/COM, metal ballast, MudSystemPhysics pressure logic, engine, transmission and ADS protection are unchanged.\n\n'''
if not s.startswith("# Changelog\n\n"):
    raise SystemExit("Unexpected changelog header")
s = "# Changelog\n\n" + entry + s[len("# Changelog\n\n"):]
p.write_text(s, encoding="utf-8")

release = {
    "version": VERSION,
    "tag": VERSION,
    "title": "0.0.4.2 - C-330 water-ballast damper=30 test",
    "prerelease": True,
    "zipName": "FS25_UrsusC330_330M_4x2.zip"
}
Path(".release/release.json").write_text(json.dumps(release, indent=2) + "\n", encoding="utf-8")

notes = '''## Ursus C-330 / C-330M 0.0.4.2\n\n**Water-ballast damping A/B test.**\n\n0.0.4.1 confirmed that the independent water option works correctly: **+132 kg per rear wheel**, **1.939 t** total on the basic tractor, front axle essentially unchanged and the added 264 kg carried by the rear axle. MudSystemPhysics pressure/radius behavior also remains active.\n\n### Only physical change\n- Water-filled rear tyres: **spring 14 / damper 30** (was 14 / 26).\n- Dry tyres stay **12 / 22**.\n- `suspTravel=0.07` and liquid mass stay unchanged.\n\n### Test\nUse the same basic Polowe tyres and standardized route. Compare water On at settled **1.00 bar** and **2.40 bar**: boards + pallet jack + firepit at cruise-control **10 km/h**, then the single board at Vmax. The key question is whether the stronger damping shortens the zero-load/rebound episodes without making impacts harsher. Send the complete `log.txt`.\n\nTemporary TyreDebugKit remains enabled for this prerelease.\n'''
Path(".release/notes.md").write_text(notes, encoding="utf-8")

print("Prepared 0.0.4.2 water damper=30 test")
