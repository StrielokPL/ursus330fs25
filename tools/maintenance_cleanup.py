from pathlib import Path
import re
import xml.etree.ElementTree as ET

# c330m.i3d: replace missing PNG references with existing DDS assets.
p = Path("c330m.i3d")
s = p.read_text(encoding="iso-8859-1")
for old, new in {
    "Textures/airConnector_normal.png": "Textures/airConnector_normal.dds",
    "Textures/airConnector_vmask.png": "Textures/airConnector_vmask.dds",
    "Textures/ske50Cabin_normal.png": "Textures/ske50Cabin_normal.dds",
    "Textures/ske50Cabin_vmask.png": "Textures/ske50Cabin_vmask.dds",
}.items():
    if old not in s:
        raise SystemExit(f"Missing expected I3D reference: {old}")
    s = s.replace(old, new)
p.write_text(s, encoding="iso-8859-1")

# c330m.xml: safe cleanup only; no physics tuning.
p = Path("c330m.xml")
s = p.read_text(encoding="utf-8")
if s.count("$l10n_Yelow") != 4:
    raise SystemExit("Unexpected $l10n_Yelow reference count")
s = s.replace("$l10n_Yelow", "$l10n_Yellow")

old = '<connectionHoseConfigurations title="TEST">'
if old not in s:
    raise SystemExit("Expected TEST connection-hose title not found")
s = s.replace(old, '<connectionHoseConfigurations title="$l10n_connectionHoses">', 1)

# Remove obsolete, fully commented-out alternative drivetrain block.
pattern = r"\n<!--\n\s*<motorConfigurations>.*?</motorConfigurations>\n-->\n"
s, count = re.subn(pattern, "\n", s, count=1, flags=re.S)
if count != 1:
    raise SystemExit("Obsolete commented motorConfiguration block not found exactly once")

old_controls = '''                    <!-- AIASF compatibility test: cabin door/window/roof Interactive Controls removed --><outdoorTrigger node="0&gt;10|7"/>
                    <!-- dach -->
                    <!-- lewe drzwi -->
                    <!-- prawe drzwi -->
                    <!-- lewe drzwi -->
                    <!-- prawe drzwi -->
                    <!-- tylnia szyba -->
                    <!-- dach -->
                    <!-- lewe drzwi -->
                    <!-- dach -->
                    <!-- lewe drzwi -->
                    <!-- dach -->
                    <!-- lewe drzwi -->
                    <!-- dach -->
                    <!-- lewe drzwi -->
                    <!-- prawe drzwi -->
                    <!-- tylnia szyba -->'''
new_controls = '''                    <!-- Static Cabins / AIASF compatibility: cabin door/window/roof controls removed. -->
                    <outdoorTrigger node="0&gt;10|7"/>'''
if old_controls not in s:
    raise SystemExit("Static Cabins IC placeholder block not found")
s = s.replace(old_controls, new_controls, 1)

old_tools = '''\t\t\t<!-- 1 -->
            <!-- 2 -->
            <!-- 3 -->\t
            <!-- 4 -->
            <!-- 5 -->
            <!-- 6 -->
            <!-- AIASF compatibility test: 18 cabin movingTools removed; cabin geometry stays static --></movingTools>'''
new_tools = '''            <!-- Static Cabins / AIASF compatibility: 18 cabin movingTools removed; cabin geometry stays static. -->
        </movingTools>'''
if old_tools not in s:
    raise SystemExit("Static Cabins movingTool placeholder block not found")
s = s.replace(old_tools, new_tools, 1)
p.write_text(s, encoding="utf-8")

# modDesc.xml: fix unambiguous localization/label errors.
p = Path("modDesc.xml")
s = p.read_text(encoding="utf-8")
for old, new in (
    ("<en>Sprinkler</en>", "<en>Generator</en>"),
    ("<de>Sprinkleranlage</de>", "<de>Gleichstromgenerator</de>"),
    ("<pl>Prądownica</pl>", "<pl>Prądnica</pl>"),
    ("<fr>Arrosage</fr>", "<fr>Dynamo</fr>"),
):
    if old not in s:
        raise SystemExit(f"Expected generator translation not found: {old}")
    s = s.replace(old, new, 1)

marker = '''        <text name="kable">   
\t\t    <en>Cables</en>    
\t\t    <de>Kabel</de>   
\t\t    <pl>Kable</pl>  
            <fr>Câbles</fr>
\t\t</text>\t\t'''
addition = marker + '''
        <text name="connectionHoses">
            <en>Connection Hoses</en>
            <de>Anschlussschläuche</de>
            <pl>Przewody przyłączeniowe</pl>
            <fr>Flexibles de raccordement</fr>
        </text>
'''
if marker not in s:
    raise SystemExit("L10N insertion point not found")
s = s.replace(marker, addition, 1)

old1 = '<brand name="Polowe" title="Opony Szosowe" image="brand_tire2.dds"/>'
old2 = '<brand name="Szosowe" title="Opony Polowe" image="brand_tire.dds"/>'
if old1 not in s or old2 not in s:
    raise SystemExit("Expected swapped tire labels not found")
s = s.replace(old1, '<brand name="Polowe" title="Opony Polowe" image="brand_tire2.dds"/>', 1)
s = s.replace(old2, '<brand name="Szosowe" title="Opony Szosowe" image="brand_tire.dds"/>', 1)
p.write_text(s, encoding="utf-8")

# Correct preliminary documentation: component mass alone is not total runtime mass.
p = Path("docs/FS25_C330_TECHNICAL_BASELINE.md")
s = p.read_text(encoding="utf-8")
old_mass = '''### Current mass
`c330m.xml` currently defines base physics components of:
- 800 kg
- 300 kg
- 2 kg
- 2 kg

Total component mass before configuration/object changes: **1104 kg**.

This is far below the factory **1675 kg ready-to-work** target and must be reworked together with centre-of-mass placement, wheel masses and configuration-specific ballast. Do not simply add 571 kg to one component; the target axle split is part of the physics requirement.
'''
new_mass = '''### Current mass
`c330m.xml` currently defines base physics components of:
- 800 kg
- 300 kg
- 2 kg
- 2 kg

Total component mass before configuration/object changes: **1104 kg**.

This value must **not** be treated as the complete tractor mass. The standard wheel definitions add approximately:
- front wheels: 2 x 40 kg = **80 kg**
- rear wheels: 2 x 232 kg = **464 kg**

That gives about **1648 kg before fuel**, already very close to the factory **1675 kg ready-to-work** figure. A full 35 l diesel tank can account for roughly another 29 kg depending on the density/model used by FS25.

Therefore the next mass step is **runtime measurement, not a blind component-mass increase**. The target remains **1675 kg and 635/1040 kg axle loads**, but component mass and centre of mass should only be changed after measuring `Wheel:getMass()` and actual FL/FR/RL/RR tire loads in game.
'''
if old_mass not in s:
    raise SystemExit("Old mass-baseline paragraph not found")
s = s.replace(old_mass, new_mass, 1)
old_step = "3. Rebuild base mass and longitudinal CoM to hit **1675 kg and 635/1040 kg axle loads** in the chosen standard configuration."
new_step = "3. Measure runtime mass, wheel masses and FL/FR/RL/RR loads; only then adjust base CoM/mass as needed to hit **1675 kg and 635/1040 kg axle loads**."
if old_step not in s:
    raise SystemExit("Old rebuild-order mass step not found")
s = s.replace(old_step, new_step, 1)
p.write_text(s, encoding="utf-8")

# Validation.
for xml in ("c330m.i3d", "c330m.xml", "modDesc.xml"):
    ET.parse(xml)
for asset in (
    "Textures/airConnector_normal.dds",
    "Textures/airConnector_vmask.dds",
    "Textures/ske50Cabin_normal.dds",
    "Textures/ske50Cabin_vmask.dds",
):
    if not Path(asset).is_file():
        raise SystemExit(f"Replacement asset missing: {asset}")
if "$l10n_Yelow" in Path("c330m.xml").read_text(encoding="utf-8"):
    raise SystemExit("Typoed l10n key still present")
print("Cleanup validation passed")
