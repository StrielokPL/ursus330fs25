from pathlib import Path
import json
import xml.etree.ElementTree as ET

VERSION = "0.0.3.1"

# Keep diagnostics lightweight: do not recursively walk the whole wheel->vehicle graph.
p = Path("debug/TyreDebugKit.lua")
s = p.read_text(encoding="utf-8")
old = '''                local descend = containsAny(keyText, tokens)\n                    or containsAny(path, {"pressure", "tire", "tyre", "wheel", "mud"})'''
new = '''                local descend = containsAny(keyText, tokens)\n                    or containsAny(path, {"pressure", "tire", "tyre", "mud"})'''
if old not in s:
    raise SystemExit("Expected diagnostic recursion guard not found")
s = s.replace(old, new, 1)
p.write_text(s, encoding="utf-8")

# modDesc: prerelease version + read-only tyre diagnostic source before production transmission code.
p = Path("modDesc.xml")
s = p.read_text(encoding="utf-8")
if "<version>0.0.3.0</version>" not in s:
    raise SystemExit("Expected stable 0.0.3.0 version not found")
s = s.replace("<version>0.0.3.0</version>", f"<version>{VERSION}</version>", 1)
old_block = '''    <extraSourceFiles>\n        <sourceFile filename="Scripts/C330TransmissionFix.lua" />\n    </extraSourceFiles>'''
new_block = '''    <!-- Temporary read-only tyre/suspension diagnostics for 0.0.3.1 prerelease. -->\n    <extraSourceFiles>\n        <sourceFile filename="debug/TyreDebugKit.lua" />\n        <sourceFile filename="Scripts/C330TransmissionFix.lua" />\n    </extraSourceFiles>'''
if old_block not in s:
    raise SystemExit("Expected stable extraSourceFiles block not found")
s = s.replace(old_block, new_block, 1)
p.write_text(s, encoding="utf-8")
ET.parse(p)

# README development marker.
p = Path("README.md")
s = p.read_text(encoding="utf-8")
s = s.replace(
    "**0.0.3.0 – stable C-330 mass / balance milestone**",
    "**0.0.3.1 – C-330 tyre / pressure diagnostic prerelease**",
    1,
)
s = s.replace(
    "The temporary diagnostic kit was removed for stable **0.0.2.0**. It can be restored in a later development branch when another subsystem needs runtime instrumentation.",
    "The mass diagnostic kit was removed again for stable **0.0.3.0**. Version **0.0.3.1** temporarily adds a separate read-only `TyreDebugKit` to measure wheel load, spring/damper state, wheel movement and MudSystemPhysics pressure-related runtime fields without changing tyre physics.",
    1,
)
p.write_text(s, encoding="utf-8")

# CHANGELOG entry.
p = Path("CHANGELOG.md")
s = p.read_text(encoding="utf-8")
entry = '''## 0.0.3.1 - C-330 tyre / pressure diagnostic prerelease\n\nRead-only instrumentation build starting the tyre spring/deformation/damping stage after stable 0.0.3.0. **No tyre, suspension, mass, drivetrain or traction value is changed in this build.**\n\n### Diagnostic scope\n- Targets the C-330/C-330M `c330m.xml` vehicle only.\n- Records the selected wheel configuration and total mass.\n- Samples individual FL/FR/RL/RR tire loads and front/rear axle totals every **100 ms**.\n- Records wheel-node vertical position relative to the tractor root to expose physical wheel/suspension movement.\n- Every **500 ms** records runtime wheel/physics fields including mass, radius, width, `restLoad`, load ratio, `suspTravel`, compression/length candidates, spring, damper, initialCompression, forcePointRatio, longitudinal/lateral stiffness and friction.\n- Records visual `maxDeformation` separately so visual tire deformation is not confused with physical suspension compliance.\n- Every **250 ms** searches read-only runtime structures for pressure/inflation/PSI/bar fields in MudSystemPhysics/tire/wheel-related specializations and logs a breadcrumb whenever the pressure state changes.\n- On each settled wheel configuration it emits a one-time scalar discovery dump for pressure/suspension/deformation/stiffness fields, allowing unknown GIANTS/MS runtime field names to be identified from the log.\n\n### Intended test\nUse the basic standard C-330 without ballast or attachments. Test both available tyre sets/configurations. For each tyre set, change pressure through MudSystemPhysics across several clearly separated settings, let the tractor stand briefly at each setting, then drive the same short route / disturbance so load and wheel movement can be compared.\n\n### Explicitly unchanged\n- Stable 0.0.3.0 mass, COM and factory metal ballast values.\n- Tyre XML radius, width, mass, maxDeformation, frictionScale and stiffness values.\n- Wheel suspension spring/damper/travel values.\n- MudSystemPhysics itself; the bridge is diagnostic/read-only and nil-safe.\n- Engine, 6F/2R transmission controller, ADS integration, differential and C-330M drivetrain scope.\n\n'''
if not s.startswith("# Changelog\n\n"):
    raise SystemExit("Unexpected CHANGELOG header")
s = "# Changelog\n\n" + entry + s[len("# Changelog\n\n"):]
p.write_text(s, encoding="utf-8")

release = {
    "version": VERSION,
    "tag": VERSION,
    "title": "0.0.3.1 - C-330 tyre / pressure diagnostic test",
    "prerelease": True,
    "zipName": "FS25_UrsusC330_330M_4x2.zip",
}
Path(".release/release.json").write_text(json.dumps(release, indent=2) + "\n", encoding="utf-8")

notes = '''## Ursus C-330 / C-330M 0.0.3.1\n\n**Read-only tyre / MudSystemPhysics pressure diagnostic prerelease.** No physical values are changed from stable 0.0.3.0.\n\n### What this build records\n- wheel configuration and mass context,\n- FL/FR/RL/RR tire load plus front/rear totals at 100 ms resolution,\n- wheel vertical movement relative to the tractor,\n- runtime spring, damper, suspension travel/compression candidates, radius, stiffness and friction every 500 ms,\n- visual maxDeformation separately,\n- pressure-like runtime fields from MudSystemPhysics/tire/wheel specializations every 250 ms and whenever the detected state changes.\n\n### Test plan\nUse the unballasted standard C-330 with no attachment. Test both tyre sets. For each set:\n1. let the tractor settle at the first MS pressure;\n2. keep it stationary for a few seconds;\n3. drive the same short route / bump or rough patch;\n4. change to the next clearly different MS pressure and repeat.\n\nUse as many pressure steps as convenient; three or more (low / medium / high) will make the spring/damping trend much easier to identify. Send the complete `log.txt`.\n'''
Path(".release/notes.md").write_text(notes, encoding="utf-8")

# Assertions: diagnostic-only release and validated stable physical values preserved.
moddesc = Path("modDesc.xml").read_text(encoding="utf-8")
assert f"<version>{VERSION}</version>" in moddesc
assert 'debug/TyreDebugKit.lua' in moddesc
assert Path("debug/TyreDebugKit.lua").exists()
assert 'traceIntervalMs = 100' in Path("debug/TyreDebugKit.lua").read_text(encoding="utf-8")
assert 'detailIntervalMs = 500' in Path("debug/TyreDebugKit.lua").read_text(encoding="utf-8")
assert 'pressureIntervalMs = 250' in Path("debug/TyreDebugKit.lua").read_text(encoding="utf-8")
c = Path("c330m.xml").read_text(encoding="utf-8")
rb = Path("Wheels/LizardBack.xml").read_text(encoding="utf-8")
assert '<component centerOfMass="0 0.1 -0.125" solverIterationCount="20" mass="792"/>' in c
assert 'massActive="342"' in c
assert 'mass="0.072"' in rb and 'mass="0.052"' in rb
assert json.loads(Path(".release/release.json").read_text(encoding="utf-8"))["prerelease"] is True
print("0.0.3.1 tyre diagnostic setup validated")
