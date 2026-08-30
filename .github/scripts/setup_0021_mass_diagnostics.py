from pathlib import Path
import json
import subprocess
import xml.etree.ElementTree as ET

VERSION = "0.0.2.1"

# Restore the last validated read-only diagnostic kit, but configure it for a
# static mass/axle-load study only. No physics or drivetrain values are changed.
raw = subprocess.check_output(
    ["git", "show", "0.0.1.8:debug/TractorDebugKit.lua"], text=True
)
raw = raw.replace("settleDelayMs = 2500", "settleDelayMs = 3500", 1)
raw = raw.replace("traceTransmissionChanges = true", "traceTransmissionChanges = false", 1)
raw = raw.replace("periodicEngineTrace = true", "periodicEngineTrace = false", 1)
raw = raw.replace("readAdsDynamicLoad = true", "readAdsDynamicLoad = false", 1)
raw = raw.replace(
    "-- Adapted for Ursus C-330 / C-330M.\n",
    "-- Adapted for Ursus C-330 / C-330M.\n-- 0.0.2.1 MASS TEST: static configuration/mass/COM/axle-load snapshot only.\n",
    1,
)
Path("debug").mkdir(exist_ok=True)
Path("debug/TractorDebugKit.lua").write_text(raw, encoding="utf-8")

# modDesc: prerelease version + temporary diagnostic source.
p = Path("modDesc.xml")
s = p.read_text(encoding="utf-8")
s = s.replace("<version>0.0.2.0</version>", f"<version>{VERSION}</version>", 1)
old = '''    <extraSourceFiles>\n        <sourceFile filename="Scripts/C330TransmissionFix.lua" />\n    </extraSourceFiles>'''
new = '''    <!-- Temporary read-only mass diagnostics for 0.0.2.1 prerelease. -->\n    <extraSourceFiles>\n        <sourceFile filename="debug/TractorDebugKit.lua" />\n        <sourceFile filename="Scripts/C330TransmissionFix.lua" />\n    </extraSourceFiles>'''
if old not in s:
    raise SystemExit("Expected stable extraSourceFiles block not found")
s = s.replace(old, new, 1)
p.write_text(s, encoding="utf-8")
ET.parse(p)

# README current version.
p = Path("README.md")
s = p.read_text(encoding="utf-8")
s = s.replace(
    "**0.0.2.0 – stable C-330 drivetrain milestone**",
    "**0.0.2.1 – base mass / COM / axle-load diagnostic prerelease**",
    1,
)
p.write_text(s, encoding="utf-8")

# Changelog.
p = Path("CHANGELOG.md")
s = p.read_text(encoding="utf-8")
entry = '''## 0.0.2.1 - base mass / COM / axle-load diagnostic\n\nFirst isolated mass-analysis prerelease after stable 0.0.2.0. **No physical values are changed in this build.**\n\n### Change\n- Temporarily restored the validated read-only `TractorDebugKit` for static mass measurements.\n- Diagnostics are restricted to configuration, total mass, component mass/COM, wheel mass and settled front/rear tire loads.\n- Transmission-change tracing, periodic engine tracing and ADS-load reading are disabled for this test.\n- Snapshot settle delay increased to 3.5 s to give the suspension more time to stabilize.\n\n### Test target\n- Use the basic wheel configuration as the common baseline.\n- Record the naked/base tractor first, then cabin variants and ballast variants/combinations.\n- The log records selected configuration indices, so each spawned/reconfigured tractor can be identified from the log.\n- Primary factory target for the unballasted ready-to-work C-330: about 1675 kg total, 635 kg front / 1040 kg rear, approximately 38/62 axle split.\n\n### Explicitly unchanged\n- 0.0.2.0 production transmission controller and all gearbox behavior.\n- S-312C torque curve and engine parameters.\n- Component masses, center of mass, ballast values, wheels, tyres, suspension and differential.\n- C-330M drivetrain.\n\n'''
if not s.startswith("# Changelog\n\n"):
    raise SystemExit("Unexpected changelog header")
s = "# Changelog\n\n" + entry + s[len("# Changelog\n\n"):]
p.write_text(s, encoding="utf-8")

# Prerelease metadata.
release = {
    "version": VERSION,
    "tag": VERSION,
    "title": "0.0.2.1 - C-330 mass / COM diagnostic test",
    "prerelease": True,
    "zipName": "FS25_UrsusC330_330M_4x2.zip",
}
Path(".release/release.json").write_text(json.dumps(release, indent=2) + "\n", encoding="utf-8")

notes = '''## Ursus C-330 / C-330M 0.0.2.1\n\n**Mass / COM diagnostic prerelease. No physics values are changed from stable 0.0.2.0.**\n\n### Purpose\nMeasure the standard C-330 on one common basic-wheel baseline and determine the real runtime effect of cabin and ballast configurations before moving any center of mass or changing ballast mass.\n\n### Diagnostics\nThe temporary read-only `TractorDebugKit` is restored for this prerelease and records:\n- active configuration indices,\n- total runtime mass,\n- front/rear tire loads and percentage split,\n- each component runtime mass and center of mass,\n- wheel masses and static wheel loads.\n\nEngine periodic trace, transmission-change trace and ADS load reading are disabled for this test. The production 0.0.2.0 transmission controller is untouched.\n\n### Suggested test matrix\nKeep **basic wheels** for every sample. Start with the plain/unballasted tractor, then test the cabin variants, front ballast, rear wheel ballast and useful cabin+ballast combinations. Let each configuration stand still on flat ground for several seconds so the 3.5 s settled snapshot is recorded.\n\n### Reference target\nUnballasted ready-to-work C-330: **1675 kg**, approximately **635 kg front / 1040 kg rear**, or about **38/62**.\n\nSend the complete `log.txt`; the configuration numbers in the log will let us reconstruct the tested combinations.\n'''
Path(".release/notes.md").write_text(notes, encoding="utf-8")

# Validation.
assert Path("debug/TractorDebugKit.lua").exists()
assert "traceTransmissionChanges = false" in Path("debug/TractorDebugKit.lua").read_text(encoding="utf-8")
assert "periodicEngineTrace = false" in Path("debug/TractorDebugKit.lua").read_text(encoding="utf-8")
assert "readAdsDynamicLoad = false" in Path("debug/TractorDebugKit.lua").read_text(encoding="utf-8")
assert f"<version>{VERSION}</version>" in Path("modDesc.xml").read_text(encoding="utf-8")
assert "debug/TractorDebugKit.lua" in Path("modDesc.xml").read_text(encoding="utf-8")
assert json.loads(Path(".release/release.json").read_text(encoding="utf-8"))["prerelease"] is True
print("0.0.2.1 mass diagnostic setup validated")
