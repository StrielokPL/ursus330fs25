from pathlib import Path
import json
import xml.etree.ElementTree as ET

# c330m.xml: C-330 only. C-330M is intentionally untouched.
p = Path('c330m.xml')
s = p.read_text(encoding='utf-8')

old_motor = '<motor torqueScale="0.138" minRpm="600" maxRpm="2200" accelerationLimit="1.0" maxForwardSpeed="27" maxBackwardSpeed="8" brakeForce="1.3" lowBrakeForceScale="0.1" dampingRateScale="0.1">'
new_motor = '<motor torqueScale="0.138" minRpm="600" maxRpm="2200" accelerationLimit="1.0" maxForwardSpeed="22.878" maxBackwardSpeed="6.207" brakeForce="1.3" lowBrakeForceScale="0.1" dampingRateScale="0.1">'
if s.count(old_motor) != 2:
    raise SystemExit('Expected exactly two original motor headers')
s = s.replace(old_motor, new_motor, 1)

old_groups = '''                    <groups type="DEFAULT" changeTime="0.5">
                        <group ratio="0.36" name="I"/>
                        <group ratio="1" name="II"/>
                    </groups>

                    <forwardGear maxSpeed="13.2"/>
                    <forwardGear maxSpeed="17.2"/>
                    <forwardGear maxSpeed="27.0"/>

                    <backwardGear maxSpeed="8.4"/>'''
new_groups = '''                    <groups type="DEFAULT" changeTime="0.5">
                        <group ratio="0.24691358" name="I"/>
                        <group ratio="1" name="II"/>
                    </groups>

                    <!-- Factory C-330 nominal speeds at 2200 rpm on 12.4-28 tyres. -->
                    <forwardGear maxSpeed="7.389"/>
                    <forwardGear maxSpeed="14.324"/>
                    <forwardGear maxSpeed="22.878"/>

                    <backwardGear maxSpeed="6.207"/>'''
if s.count(old_groups) != 2:
    raise SystemExit('Expected exactly two original transmission blocks')
s = s.replace(old_groups, new_groups, 1)
p.write_text(s, encoding='utf-8')
ET.parse(p)

# modDesc.xml: version + load transmission controller next to diagnostics.
p = Path('modDesc.xml')
s = p.read_text(encoding='utf-8')
if '<version>0.0.0.3</version>' not in s:
    raise SystemExit('Expected version 0.0.0.3')
s = s.replace('<version>0.0.0.3</version>', '<version>0.0.0.4</version>', 1)
old_sources = '''    <!-- Temporary read-only runtime diagnostics for 0.0.0.3. Remove before stable release. -->
    <extraSourceFiles>
        <sourceFile filename="debug/TractorDebugKit.lua" />
    </extraSourceFiles>'''
new_sources = '''    <!-- Temporary diagnostics remain enabled during gearbox development. -->
    <extraSourceFiles>
        <sourceFile filename="debug/TractorDebugKit.lua" />
        <sourceFile filename="Scripts/C330TransmissionFix.lua" />
    </extraSourceFiles>'''
if old_sources not in s:
    raise SystemExit('Expected 0.0.0.3 source block')
s = s.replace(old_sources, new_sources, 1)
p.write_text(s, encoding='utf-8')
ET.parse(p)

# README current version.
p = Path('README.md')
s = p.read_text(encoding='utf-8')
s = s.replace('**0.0.0.3 – diagnostic prerelease**', '**0.0.0.4 – C-330 gearbox test prerelease**', 1)
p.write_text(s, encoding='utf-8')

# Changelog entry.
p = Path('CHANGELOG.md')
s = p.read_text(encoding='utf-8')
entry = '''# Changelog\n\n## 0.0.0.4 - C-330 gearbox test prerelease\n\nFirst dedicated transmission correction for the standard **C-330**. C-330M is deliberately unchanged in this test.\n\n### C-330 factory gearing\n- Range reduction changed from the imported `0.36` speed factor to `0.24691358`, corresponding to the factory 4.050 reduction.\n- High-range forward speeds set to **7.389 / 14.324 / 22.878 km/h**.\n- Low range therefore targets approximately **1.825 / 3.537 / 5.649 km/h**.\n- High-range reverse set to **6.207 km/h**; low reverse follows the 4.050 reduction (~1.533 km/h).\n- C-330 motor speed caps set to 22.878 km/h forward and 6.207 km/h reverse.\n\n### Automatic range controller\n- Added `Scripts/C330TransmissionFix.lua`, active only for the C-330 motor configuration in forward automatic mode.\n- GIANTS automatic group optimization is disabled for C-330 forward automatic driving.\n- Intended sequence is `I/1 -> I/2 -> I/3 -> II/1 -> II/2 -> II/3`, and the reverse order when downshifting.\n- Vanilla still decides normal shifts inside each range, but multi-gear jumps are clamped to one mechanical gear at a time.\n- Added explicit `II/1 -> I/3` load downshift before the tractor nearly stalls.\n- Added explicit `I/3 -> II/1` range upshift only after RPM recovers and load is moderate.\n- Added hysteresis/cooldowns to prevent immediate range hunting.\n- ADS `dynamicMotorLoad` is used when valid; otherwise the native GIANTS smoothed motor load is used. ADS remains optional.\n- Manual modes are unchanged. Reverse remains under GIANTS control in this first test.\n\n### Diagnostics\n- `TractorDebugKit` remains enabled.\n- New controller messages use prefix `[C330TRANS]`.\n\n### Explicitly unchanged\n- C-330 engine torque curve and fuel use.\n- C-330M drivetrain.\n- Mass/COM, ballast, tyres and suspension.\n\n### Test goal\nVerify that a heavily loaded C-330 uses range I before losing almost all road speed, and that unloaded/light-load acceleration follows the real six-step order without rapid I/II oscillation.\n\n'''
if not s.startswith('# Changelog\n\n'):
    raise SystemExit('Unexpected changelog header')
s = entry + s[len('# Changelog\n\n'):]
p.write_text(s, encoding='utf-8')

# Release configuration and notes.
Path('.release/release.json').write_text(json.dumps({
    'version': '0.0.0.4',
    'tag': '0.0.0.4',
    'title': '0.0.0.4 - C-330 factory gearbox test',
    'prerelease': True,
    'zipName': 'FS25_UrsusC330_330M_4x2.zip'
}, indent=2) + '\n', encoding='utf-8')

Path('.release/notes.md').write_text('''## Ursus C-330 / C-330M 0.0.0.4\n\nDedicated **C-330 gearbox test** based on the 0.0.0.3 runtime log. C-330M is intentionally unchanged.\n\n### What changed\n- factory C-330 3x2 speed ladder: ~1.825 / 3.537 / 5.649 / 7.389 / 14.324 / 22.878 km/h,\n- factory range reduction 4.050,\n- reverse targets ~1.533 / 6.207 km/h,\n- custom forward automatic range controller,\n- explicit heavy-load II/1 -> I/3 downshift,\n- controlled I/3 -> II/1 upshift,\n- one-mechanical-step limit inside a range,\n- cooldown and load/RPM guards against range hunting,\n- optional ADS load input with native GIANTS load fallback,\n- `[C330TRANS]` logging added; `[TRACTORDBG]` remains enabled.\n\n### Not changed\nEngine torque, mass/COM, ballast, tyres, suspension and the C-330M drivetrain are unchanged.\n\n### Test\nUse the C-330 (`motor=1`). First drive unloaded through the full speed range, then repeat with the heavy trailer that previously stayed in road range. Send the complete `log.txt`; useful lines are `[TRACTORDBG][SHIFT]` and `[C330TRANS]`.\n''', encoding='utf-8')

# Sanity checks.
if not Path('Scripts/C330TransmissionFix.lua').is_file():
    raise SystemExit('Transmission script missing')
if '<version>0.0.0.4</version>' not in Path('modDesc.xml').read_text(encoding='utf-8'):
    raise SystemExit('Version update failed')
print('0.0.0.4 gearbox setup validated')
