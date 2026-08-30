from pathlib import Path
import json
import xml.etree.ElementTree as ET

VERSION = "0.0.3.0"

# 0.0.3.0 closes the C-330 base mass / COM / factory ballast stage.
# No vehicle physics values are changed from validated 0.0.2.3.

# modDesc: version + remove temporary mass diagnostics, keep production transmission controller.
p = Path("modDesc.xml")
s = p.read_text(encoding="utf-8")
if "<version>0.0.2.3</version>" not in s:
    raise SystemExit("Expected 0.0.2.3 modDesc version not found")
s = s.replace("<version>0.0.2.3</version>", f"<version>{VERSION}</version>", 1)
old = '''    <!-- Temporary read-only mass diagnostics for 0.0.2.3 ballast prerelease. -->\n    <extraSourceFiles>\n        <sourceFile filename="debug/TractorDebugKit.lua" />\n        <sourceFile filename="Scripts/C330TransmissionFix.lua" />\n    </extraSourceFiles>'''
new = '''    <extraSourceFiles>\n        <sourceFile filename="Scripts/C330TransmissionFix.lua" />\n    </extraSourceFiles>'''
if old not in s:
    raise SystemExit("Expected temporary diagnostic extraSourceFiles block not found")
s = s.replace(old, new, 1)
p.write_text(s, encoding="utf-8")
ET.parse(p)

# Remove temporary diagnostic source from stable package.
dbg = Path("debug/TractorDebugKit.lua")
if dbg.exists():
    dbg.unlink()

# README milestone / next subsystem.
p = Path("README.md")
s = p.read_text(encoding="utf-8")
for old in (
    "**0.0.2.3 – C-330 factory ballast mass test**",
    "**0.0.2.2 – C-330 base mass / COM correction test**",
):
    if old in s:
        s = s.replace(old, "**0.0.3.0 – stable C-330 mass / balance milestone**", 1)
        break
# Update current priority wording if the known block is present.
old_priority = '''## Current priority\nThe initial physics rebuild will focus on:\n- correct 1675 kg base working mass and 38/62 axle load split,\n- real 100 Nm S-312C torque characteristic and 22.4 kW rated power,\n- historically correct 6F/2R gearing and ~23 km/h C-330 top speed,\n- correct factory ballast masses,\n- tyre-radius and traction calibration,\n- 35 l fuel tank, 540 rpm PTO and 700 kg rear linkage target.'''
new_priority = '''## Current priority\nValidated milestones now include the standard C-330 drivetrain and the base mass / balance / factory ballast stage.\n\nNext isolated subsystem:\n- tyre spring/deformation and damping calibration on the basic tyres,\n- then liquid rear-tyre ballast as a separate tyre state, including both its mass and its changed tyre compliance/damping,\n- followed by tyre traction/radius refinement and later PTO/hydraulics/fuel work.'''
if old_priority in s:
    s = s.replace(old_priority, new_priority, 1)
p.write_text(s, encoding="utf-8")

# CHANGELOG stable milestone entry.
p = Path("CHANGELOG.md")
s = p.read_text(encoding="utf-8")
entry = '''## 0.0.3.0 - stable C-330 mass / balance milestone\n\nFull release closing the isolated base-mass, longitudinal COM and factory metal-ballast calibration stage. **No physical values are changed from 0.0.2.3.**\n\n### Final 0.0.2.3 runtime validation\n- Base/basic-wheel C-330 repeated at **1.675 t**, **0.634 t front / 1.041 t rear = 37.86/62.14**.\n- Rear `Small` (`wheel=2`) measured **1.715 t**, exactly **+40 kg**, all on the rear axle.\n- Rear `Big` (`wheel=3`) measured **1.819 t**, exactly **+144 kg**, all on the rear axle.\n- Rear `Both` (`wheel=4`) measured **1.859 t**, exactly **+184 kg**, all on the rear axle.\n- Alternate rear `Big` (`wheel=5`) also measured **1.819 t**, exactly **+144 kg**.\n- Front ballast (`design3=2`) measured **1.717 t**, exactly **+42 kg**, effectively all on the front axle: **0.676 / 1.041 t**.\n- Front + alternate `Big` measured **1.861 t**, **0.676 / 1.185 t**, confirming additive behavior.\n- The validated full factory-metal combination is therefore **1.901 t** with approximately **0.676 / 1.225 t** axle load; factory reference is about **0.677 / 1.224 t**.\n- Complete test log contained **0 `Error:`**, **0 Lua stack errors**, **0 `SHIFT_OSCILLATION`** and no C330/TRACTORDBG warnings. Generic warnings were unrelated mods/map/rendering.\n\n### Accepted safe points\n- Base ready-to-work mass: **1675 kg**.\n- Component 1 nominal mass: **792 kg**; longitudinal COM **Z=-0.125 m**.\n- Unballasted axle split: approximately **38/62**.\n- Front factory metal ballast: **42 kg total**.\n- Rear factory metal ballast: **40 kg small / 144 kg big / 184 kg both**.\n- Full factory metal ballast: **226 kg**, giving **1901 kg** tractor mass.\n\n### Release cleanup\n- Removed temporary `debug/TractorDebugKit.lua` from the stable package and `modDesc.xml`.\n- Production `Scripts/C330TransmissionFix.lua` remains unchanged.\n\n### Next subsystem\n- Tyre spring/deformation and damping calibration on the basic tyres.\n- Liquid rear-tyre ballast will follow as a distinct tyre configuration/state, because adding liquid changes not only rear unsprung/rotating mass but also effective tyre compliance and damping.\n\n### Explicitly unchanged\n- Engine and factory-style 6F/2R transmission behavior.\n- ADS integration (optional, filtered, read-only).\n- Cabin mass neutrality.\n- Tyre radius, tyre stiffness/traction parameters, suspension and differential.\n- C-330M drivetrain/controller scope.\n\n'''
if not s.startswith("# Changelog\n\n"):
    raise SystemExit("Unexpected CHANGELOG header")
s = "# Changelog\n\n" + entry + s[len("# Changelog\n\n"):]
p.write_text(s, encoding="utf-8")

# Stable release metadata.
release = {
    "version": VERSION,
    "tag": VERSION,
    "title": "0.0.3.0 - stable C-330 mass / balance milestone",
    "prerelease": False,
    "zipName": "FS25_UrsusC330_330M_4x2.zip",
}
Path(".release/release.json").write_text(json.dumps(release, indent=2) + "\n", encoding="utf-8")

notes = '''## Ursus C-330 / C-330M 0.0.3.0\n\n**Stable mass / balance milestone.** No physics values changed from validated 0.0.2.3; this release promotes the tested state and removes temporary mass diagnostics.\n\n### Validated C-330 mass state\n- base ready-to-work mass: **1675 kg**;\n- base axle loads: **634 / 1041 kg (37.86 / 62.14%)**;\n- factory front metal ballast: **42 kg**;\n- rear metal ballast: **40 kg Small / 144 kg Big / 184 kg Both**;\n- full factory metal ballast: **226 kg**, giving **1901 kg** total.\n\nThe 0.0.2.3 test matrix reproduced each configured mass exactly and confirmed additive front/rear behavior. The complete runtime log had no C-330 Lua/game errors or oscillation warnings.\n\n### Stable cleanup\nTemporary `TractorDebugKit` mass diagnostics are removed. The production 0.0.2.0 drivetrain controller remains unchanged.\n\n### Next development stage\nTyre spring/deformation/damping calibration. Liquid ballast will be modeled afterward as a separate rear-tyre state with both added liquid mass and altered tyre compliance/damping, rather than as mass alone.\n'''
Path(".release/notes.md").write_text(notes, encoding="utf-8")

# Final checks: validated 0.0.2.3 physical values must remain.
c = Path("c330m.xml").read_text(encoding="utf-8")
rb = Path("Wheels/LizardBack.xml").read_text(encoding="utf-8")
assert '<component centerOfMass="0 0.1 -0.125" solverIterationCount="20" mass="792"/>' in c
assert 'massActive="342"' in c
assert 'mass="0.072"' in rb
assert 'mass="0.052"' in rb
assert f"<version>{VERSION}</version>" in Path("modDesc.xml").read_text(encoding="utf-8")
assert "TractorDebugKit.lua" not in Path("modDesc.xml").read_text(encoding="utf-8")
assert not Path("debug/TractorDebugKit.lua").exists()
assert json.loads(Path(".release/release.json").read_text(encoding="utf-8"))["prerelease"] is False
print("0.0.3.0 mass/balance stable setup validated")
