from pathlib import Path
import json
import xml.etree.ElementTree as ET

VERSION = "0.0.2.3"

# Isolated factory ballast-mass correction.
# Base mass/COM from 0.0.2.2 is preserved unchanged.
# Engine, transmission, ADS integration, tyre dimensions and chassis geometry are unchanged.

# Front ballast: factory 2 x 21 kg = 42 kg total.
p = Path("c330m.xml")
s = p.read_text(encoding="utf-8")
old_front = '''\t\t<design3Configuration name="$l10n_configuration_valueYes" price="100">\n\t\t\t<objectChange node="0&gt;6|1|0" visibilityActive="true"/>\n\t\t\t<objectChange node="1&gt;" massActive="400"/>\n        </design3Configuration>'''
new_front = '''\t\t<design3Configuration name="$l10n_configuration_valueYes" price="100">\n\t\t\t<objectChange node="0&gt;6|1|0" visibilityActive="true"/>\n\t\t\t<objectChange node="1&gt;" massActive="342"/>\n        </design3Configuration>'''
if old_front not in s:
    raise SystemExit("Expected front ballast configuration not found")
s = s.replace(old_front, new_front, 1)
p.write_text(s, encoding="utf-8")
ET.parse(p)

# Rear wheel ballast mapping based on visual shop labels:
# Small = inner pair = 2 x 20 kg = 40 kg total (already correct: 0.020 t/side).
# Big = outer set = 6 x 24 kg = 144 kg total = 0.072 t/side.
# Both = inner + outer = 184 kg total = 0.092 t/side.
# wideWeight2 is also labelled Big; because its visual geometry is composed of the
# 0.020 t innerRim plus an alternate additional object, the latter becomes 0.052 t
# so the total remains 0.072 t/side (144 kg total).
p = Path("Wheels/LizardBack.xml")
s = p.read_text(encoding="utf-8")

old_weight = '''        <configuration id="weight" >\n            <additional filename="Wheels/Wheels.i3d" nodeLeft="2|2" nodeRight="2|3" offset="0.01" scale="1 1 1" mass="0.04" />\n        </configuration>'''
new_weight = '''        <configuration id="weight" >\n            <additional filename="Wheels/Wheels.i3d" nodeLeft="2|2" nodeRight="2|3" offset="0.01" scale="1 1 1" mass="0.072" />\n        </configuration>'''
if old_weight not in s:
    raise SystemExit("Expected rear 'weight' configuration not found")
s = s.replace(old_weight, new_weight, 1)

old_wide_weight = '''        <configuration id="wideWeight" >\n            <innerRim   filename="Wheels/Wheels.i3d" nodeLeft="2|0" nodeRight="2|1" offset="0.01" scale="1 1 1" mass="0.02" />\n            <additional filename="Wheels/Wheels.i3d" nodeLeft="2|2" nodeRight="2|3" offset="0.01" scale="1 1 1" mass="0.04" />\n        </configuration>'''
new_wide_weight = '''        <configuration id="wideWeight" >\n            <innerRim   filename="Wheels/Wheels.i3d" nodeLeft="2|0" nodeRight="2|1" offset="0.01" scale="1 1 1" mass="0.02" />\n            <additional filename="Wheels/Wheels.i3d" nodeLeft="2|2" nodeRight="2|3" offset="0.01" scale="1 1 1" mass="0.072" />\n        </configuration>'''
if old_wide_weight not in s:
    raise SystemExit("Expected rear 'wideWeight' configuration not found")
s = s.replace(old_wide_weight, new_wide_weight, 1)

old_wide_weight2 = '''        <configuration id="wideWeight2" >\n            <innerRim   filename="Wheels/Wheels.i3d" nodeLeft="2|0" nodeRight="2|1" offset="0.01" scale="1 1 1" mass="0.02" />\n            <additional filename="Wheels/Wheels.i3d" nodeLeft="2|4" nodeRight="2|5" offset="0.01" scale="1 1 1" mass="0.04" />\n        </configuration>'''
new_wide_weight2 = '''        <configuration id="wideWeight2" >\n            <innerRim   filename="Wheels/Wheels.i3d" nodeLeft="2|0" nodeRight="2|1" offset="0.01" scale="1 1 1" mass="0.02" />\n            <additional filename="Wheels/Wheels.i3d" nodeLeft="2|4" nodeRight="2|5" offset="0.01" scale="1 1 1" mass="0.052" />\n        </configuration>'''
if old_wide_weight2 not in s:
    raise SystemExit("Expected rear 'wideWeight2' configuration not found")
s = s.replace(old_wide_weight2, new_wide_weight2, 1)
p.write_text(s, encoding="utf-8")
ET.parse(p)

# Version metadata.
p = Path("modDesc.xml")
s = p.read_text(encoding="utf-8")
if "<version>0.0.2.2</version>" not in s:
    raise SystemExit("Expected 0.0.2.2 modDesc version not found")
s = s.replace("<version>0.0.2.2</version>", f"<version>{VERSION}</version>", 1)
s = s.replace(
    "<!-- Temporary read-only mass diagnostics for 0.0.2.1 prerelease. -->",
    "<!-- Temporary read-only mass diagnostics for 0.0.2.3 ballast prerelease. -->",
    1,
)
p.write_text(s, encoding="utf-8")
ET.parse(p)

# README current development version (also fixes the stale 0.0.2.1 line).
p = Path("README.md")
s = p.read_text(encoding="utf-8")
for old in (
    "**0.0.2.1 – base mass / COM / axle-load diagnostic prerelease**",
    "**0.0.2.2 – C-330 base mass / COM correction test**",
):
    if old in s:
        s = s.replace(old, "**0.0.2.3 – C-330 factory ballast mass test**", 1)
        break
p.write_text(s, encoding="utf-8")

# CHANGELOG prepend.
p = Path("CHANGELOG.md")
s = p.read_text(encoding="utf-8")
entry = '''## 0.0.2.3 - C-330 factory ballast mass test

Isolated ballast-mass correction after 0.0.2.2 closed the base mass/COM calibration.

### Runtime evidence from 0.0.2.2
- Settled basic C-330: **1.675 t**, **0.634 t front / 1.041 t rear = 37.86/62.14**.
- Factory target: **1.675 t**, **0.635 / 1.040 t = 37.9/62.1**; residual error is about 1 kg per axle.
- Component 1 runtime mass is **0.827 t** from nominal 0.792 t, confirming the same +35 kg fuel/runtime contribution observed before.
- Base mass and longitudinal COM are therefore accepted as a safe point: component 1 stays at **792 kg, Z=-0.125 m**.

### Factory ballast mapping
- Front metal ballast: **2 x 21 kg = 42 kg total**.
- Rear small/inner set: **2 x 20 kg = 40 kg total**.
- Rear big/outer set: **6 x 24 kg = 144 kg total**.
- Rear both: **184 kg total**.
- Full factory metal ballast: **226 kg**, giving **1901 kg** total tractor mass.

### Change
- Front `design3=2`: component 2 active mass **400 -> 342 kg**, changing front ballast from +100 kg to **+42 kg**.
- Rear `Small` remains **+40 kg** because it already matches the factory inner pair.
- Rear `Big` (`weight`): **+80 -> +144 kg** total.
- Rear `Both` (`wideWeight`): **+120 -> +184 kg** total.
- Alternate rear `Big` (`wideWeight2`): **+120 -> +144 kg** total while preserving its composed visual geometry.

### Expected runtime targets
Starting from the measured 0.0.2.2 base (1675 / 634 / 1041 kg):
- front ballast only: about **1717 kg**, **676 / 1041 kg**;
- rear Small only: about **1715 kg**, **634 / 1081 kg**;
- rear Big only: about **1819 kg**, **634 / 1185 kg**;
- rear Both only: about **1859 kg**, **634 / 1225 kg**;
- full factory metal ballast (front + rear Both): about **1901 kg**, **676 / 1225 kg**.
Factory documentation for full metal ballast gives **1901 kg, 677 / 1224 kg**, so the predicted residual is again only about 1 kg per axle.

### Explicitly unchanged
- Accepted 0.0.2.2 base mass and COM.
- Cabin masses (still neutral).
- Wheel/tyre dimensions, suspension and traction physics.
- Engine, gearbox and ADS integration.
- C-330M drivetrain/controller scope.

'''
if not s.startswith("# Changelog\n\n"):
    raise SystemExit("Unexpected CHANGELOG header")
s = "# Changelog\n\n" + entry + s[len("# Changelog\n\n"):]
p.write_text(s, encoding="utf-8")

# Release metadata and test notes.
release = {
    "version": VERSION,
    "tag": VERSION,
    "title": "0.0.2.3 - C-330 factory ballast mass test",
    "prerelease": True,
    "zipName": "FS25_UrsusC330_330M_4x2.zip",
}
Path(".release/release.json").write_text(json.dumps(release, indent=2) + "\n", encoding="utf-8")

notes = '''## Ursus C-330 / C-330M 0.0.2.3

**Factory ballast mass prerelease.** The 0.0.2.2 base mass/COM result is accepted and remains unchanged.

### 0.0.2.2 confirmed safe point
- base mass: **1675 kg**,
- front/rear: **634 / 1041 kg (37.86 / 62.14%)**,
- factory target: **1675 kg, 635 / 1040 kg**.

### 0.0.2.3 ballast changes
- front ballast: **100 -> 42 kg** total,
- rear Small: stays **40 kg** total,
- rear Big: **80/120 -> 144 kg** total depending visual variant,
- rear Both: **120 -> 184 kg** total.

The visual configurations and ballast locations are unchanged; only their physical masses are corrected.

### Test matrix
Please use the standard C-330 (`motor=1`) and let each configuration settle stationary on level ground for at least 4-5 seconds:
1. base, `wheel=1`, no front ballast — should repeat about **1675 / 634 / 1041 kg**;
2. front ballast only (`design3=2`) — about **1717 / 676 / 1041 kg**;
3. rear Small — about **1715 / 634 / 1081 kg**;
4. rear Big variants — about **1819 / 634 / 1185 kg**;
5. rear Both — about **1859 / 634 / 1225 kg**;
6. front + rear Both — about **1901 / 676 / 1225 kg** (factory full-metal target 1901 / 677 / 1224 kg).

A full `log.txt` is preferred. Engine, transmission, ADS behavior, tyre geometry and accepted base COM are unchanged.
'''
Path(".release/notes.md").write_text(notes, encoding="utf-8")

# Final checks.
assert 'centerOfMass="0 0.1 -0.125"' in Path("c330m.xml").read_text(encoding="utf-8")
assert '<component centerOfMass="0 0.1 -0.125" solverIterationCount="20" mass="792"/>' in Path("c330m.xml").read_text(encoding="utf-8")
assert 'massActive="342"' in Path("c330m.xml").read_text(encoding="utf-8")
rb = Path("Wheels/LizardBack.xml").read_text(encoding="utf-8")
assert 'nodeLeft="2|2" nodeRight="2|3" offset="0.01" scale="1 1 1" mass="0.072"' in rb
assert 'nodeLeft="2|4" nodeRight="2|5" offset="0.01" scale="1 1 1" mass="0.052"' in rb
assert f"<version>{VERSION}</version>" in Path("modDesc.xml").read_text(encoding="utf-8")
assert json.loads(Path(".release/release.json").read_text(encoding="utf-8"))["prerelease"] is True
print("0.0.2.3 factory ballast setup validated")
