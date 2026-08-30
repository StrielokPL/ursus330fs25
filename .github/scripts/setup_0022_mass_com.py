from pathlib import Path
import json
import xml.etree.ElementTree as ET

VERSION = "0.0.2.2"

# Isolated base mass / COM correction test.
# Transmission, engine, wheels and configuration-specific ballast are unchanged.

# c330m.xml: base component only.
p = Path("c330m.xml")
s = p.read_text(encoding="utf-8")
old = '<component centerOfMass="0 0.1 -0.2" solverIterationCount="20" mass="800"/>'
new = '<component centerOfMass="0 0.1 -0.125" solverIterationCount="20" mass="792"/>'
if old not in s:
    raise SystemExit("Expected base component definition not found")
s = s.replace(old, new, 1)
p.write_text(s, encoding="utf-8")
ET.parse(p)

# modDesc version only; diagnostics stay enabled for this prerelease.
p = Path("modDesc.xml")
s = p.read_text(encoding="utf-8")
if "<version>0.0.2.1</version>" not in s:
    raise SystemExit("Expected 0.0.2.1 modDesc version not found")
s = s.replace("<version>0.0.2.1</version>", f"<version>{VERSION}</version>", 1)
p.write_text(s, encoding="utf-8")
ET.parse(p)

# Debug label only; diagnostic behavior unchanged.
p = Path("debug/TractorDebugKit.lua")
s = p.read_text(encoding="utf-8")
s = s.replace(
    "-- 0.0.2.1 MASS TEST: static configuration/mass/COM/axle-load snapshot only.",
    "-- 0.0.2.2 MASS/COM TEST: validate calculated base component mass and longitudinal COM correction.",
    1,
)
p.write_text(s, encoding="utf-8")

# README current development version.
p = Path("README.md")
s = p.read_text(encoding="utf-8")
old_readme = "**0.0.2.1 – C-330 mass / COM diagnostic prerelease**"
if old_readme in s:
    s = s.replace(old_readme, "**0.0.2.2 – C-330 base mass / COM correction test**", 1)
elif "**0.0.2.0 – stable C-330 drivetrain milestone**" in s:
    s = s.replace("**0.0.2.0 – stable C-330 drivetrain milestone**", "**0.0.2.2 – C-330 base mass / COM correction test**", 1)
p.write_text(s, encoding="utf-8")

# CHANGELOG prepend.
p = Path("CHANGELOG.md")
s = p.read_text(encoding="utf-8")
entry = '''## 0.0.2.2 - C-330 base mass / COM correction test

First measured mass/COM correction based on the complete 0.0.2.1 static diagnostic matrix.

### Runtime evidence from 0.0.2.1
- Settled unballasted/basic-wheel C-330: **1.683 t**, about **0.605 t front / 1.078 t rear = 35.97/64.03**.
- Factory target: **1.675 t**, **0.635 t front / 1.040 t rear = 37.9/62.1**.
- `vehicleType=1..10` cabin variants did not alter runtime mass or axle loads; current cabin choices are physics-mass-neutral.
- Rear wheel options added regular rear-only mass: +40, +80 and +120 kg; the two heaviest variants were both +120 kg.
- `design3=2` added exactly +100 kg through component 2 and effectively placed it on the front axle.
- Combined configurations were additive and stable.

### Change
- Base component 1 nominal mass: **800 -> 792 kg**. With the observed +35 kg runtime fuel mass this is expected to reduce the settled tractor from 1.683 t to approximately **1.675 t**.
- Component 1 longitudinal COM: **Z -0.200 -> -0.125 m**, a 75 mm forward correction.
- Using the 1.920 m factory wheelbase and measured component/runtime masses, this is predicted to move roughly 30-33 kg of axle reaction from rear to front and land close to **635/1040 kg**.

### Explicitly unchanged
- Cabin configuration masses (still neutral pending separate evidence for individual cabin weights).
- Front and rear ballast configuration masses.
- Wheel/tyre dimensions and traction physics.
- Engine, gearbox, ADS integration and all 0.0.2.0 drivetrain behavior.
- C-330M drivetrain/controller scope.

'''
if not s.startswith("# Changelog\n\n"):
    raise SystemExit("Unexpected CHANGELOG header")
s = "# Changelog\n\n" + entry + s[len("# Changelog\n\n"):]
p.write_text(s, encoding="utf-8")

# Release metadata.
release = {
    "version": VERSION,
    "tag": VERSION,
    "title": "0.0.2.2 - C-330 base mass / COM correction test",
    "prerelease": True,
    "zipName": "FS25_UrsusC330_330M_4x2.zip",
}
Path(".release/release.json").write_text(json.dumps(release, indent=2) + "\n", encoding="utf-8")

notes = '''## Ursus C-330 / C-330M 0.0.2.2

**Base mass / COM correction prerelease.** This is the first physics change after the 0.0.2.1 measurement pass.

### Measured 0.0.2.1 baseline
- basic wheels, no ballast: 1683 kg,
- front/rear: about 605 / 1078 kg (35.97 / 64.03%),
- factory target: 1675 kg and 635 / 1040 kg (37.9 / 62.1%).

All tested cabin `vehicleType` variants were mass-neutral. Rear wheel options added +40/+80/+120 kg at the rear, and the current front ballast added +100 kg at the front.

### 0.0.2.2 change
Only base component 1 changes:
- nominal mass **800 -> 792 kg**,
- longitudinal COM **Z -0.200 -> -0.125 m**.

The calculated target with a full tank is approximately **1675 kg and 635/1040 kg**. Temporary static mass diagnostics remain enabled to verify the result in runtime.

### Test
Use basic wheels, no ballast and preferably the simplest/no-cabin configuration first. Leave the tractor stationary on level ground for at least 4-5 seconds. One clean base snapshot is enough to judge the correction; additional cabin/ballast snapshots are welcome but not required for this iteration.

Transmission, engine, ADS behavior, tyres and ballast masses are unchanged.
'''
Path(".release/notes.md").write_text(notes, encoding="utf-8")

# Final checks.
assert 'centerOfMass="0 0.1 -0.125"' in Path("c330m.xml").read_text(encoding="utf-8")
assert 'mass="792"' in Path("c330m.xml").read_text(encoding="utf-8")
assert f"<version>{VERSION}</version>" in Path("modDesc.xml").read_text(encoding="utf-8")
assert json.loads(Path(".release/release.json").read_text(encoding="utf-8"))["prerelease"] is True
print("0.0.2.2 mass/COM setup validated")
