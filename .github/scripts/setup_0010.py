from pathlib import Path
import json
import xml.etree.ElementTree as ET

# 0.0.1.0 closes the dedicated C-330 gearbox phase without changing gearbox code.
# Runtime diagnostics stay enabled because the next isolated subsystem is the S-312C engine.

# modDesc version + diagnostics comment
p = Path('modDesc.xml')
s = p.read_text(encoding='utf-8')
if '<version>0.0.0.7</version>' not in s:
    raise SystemExit('Expected modDesc 0.0.0.7')
s = s.replace('<version>0.0.0.7</version>', '<version>0.0.1.0</version>', 1)
s = s.replace(
    '<!-- Temporary diagnostics remain enabled during gearbox development. -->',
    '<!-- Temporary diagnostics remain enabled during physics/engine development. -->',
    1
)
p.write_text(s, encoding='utf-8')
ET.parse(p)

# README milestone and next priority
p = Path('README.md')
s = p.read_text(encoding='utf-8')
if '**0.0.0.7 – full 6F/2R gearbox prerelease**' not in s:
    raise SystemExit('Expected README 0.0.0.7 version line')
s = s.replace(
    '**0.0.0.7 – full 6F/2R gearbox prerelease**',
    '**0.0.1.0 – C-330 gearbox milestone prerelease**',
    1
)
s = s.replace(
    'The diagnostic code is temporary and must be removed before a stable release.',
    'The diagnostic code is temporary and remains enabled for the engine/physics tuning phase; it must be removed before a stable release.',
    1
)
p.write_text(s, encoding='utf-8')

# Changelog milestone
p = Path('CHANGELOG.md')
s = p.read_text(encoding='utf-8')
if not s.startswith('# Changelog\n\n'):
    raise SystemExit('Unexpected changelog header')
entry = '''# Changelog\n\n## 0.0.1.0 - C-330 gearbox milestone\n\nMilestone release closing the dedicated standard C-330 transmission phase. **No gearbox code, ratios or shift thresholds are changed from 0.0.0.7.**\n\n### Runtime validation of 0.0.0.7\n- C-330 automatic range control covered the complete 6F/2R layout.\n- All recorded I/II range changes were attributed to `C330TRANS`; no remaining `EXTERNAL/GIANTS` group changes were observed in the test.\n- Forward `I/3 -> II/1` transitions remained stable at high RPM and moderate/low load.\n- Reverse `R-I -> R-II` occurred only after R-I reached roughly 1.53 km/h at about 2170-2200 rpm and low ADS load (~0.30), instead of the earlier GIANTS high-load upshift.\n- No `SHIFT_OSCILLATION`, C-330 Lua error, ADS error or controller error was observed.\n- Active `R-II -> R-I` load reduction was not forced in the final runtime trace, but start/reset handling reliably returned to range I and no reverse hunting was observed.\n\n### ADS / compatibility status\n- ADS remains optional and strictly read-only.\n- Invalid/negative ADS samples are rejected and fall back to native GIANTS smoothed load.\n- Static Cabins / dirty-flag protection remains unchanged.\n\n### Next subsystem\n- Begin isolated S-312C engine calibration.\n- Imported peak torque (~138 Nm) and fuel-use model remain untouched in this milestone and are the next tuning target.\n\n### Explicitly unchanged\n- `Scripts/C330TransmissionFix.lua` behavior from 0.0.0.7.\n- C-330M drivetrain.\n- Mass/COM, ballast, tyres and suspension.\n\n'''
s = entry + s[len('# Changelog\n\n'):]
p.write_text(s, encoding='utf-8')

# Release metadata: project continues tuning, so this is a GitHub prerelease milestone.
Path('.release/release.json').write_text(json.dumps({
    'version': '0.0.1.0',
    'tag': '0.0.1.0',
    'title': '0.0.1.0 - C-330 gearbox milestone',
    'prerelease': True,
    'zipName': 'FS25_UrsusC330_330M_4x2.zip'
}, indent=2) + '\n', encoding='utf-8')

Path('.release/notes.md').write_text('''## Ursus C-330 / C-330M 0.0.1.0\n\nMilestone release closing the dedicated **C-330 6F/2R gearbox** phase.\n\n### Validated gearbox state\n- factory C-330 range reduction and nominal 6F/2R speeds retained,\n- complete automatic forward sequence `I/1 -> I/2 -> I/3 -> II/1 -> II/2 -> II/3`,\n- reverse automatic handled as `R-I -> R-II`,\n- GIANTS automatic I/II group selection is suppressed for the C-330 automatic mode,\n- ADS-aware load protection remains optional, filtered and read-only,\n- manual transmission modes and C-330M remain untouched.\n\nThe final 0.0.0.7 runtime test showed no external/GIANTS range changes, no shift-oscillation warnings and no C-330/ADS/controller Lua errors.\n\n### Next phase\nTemporary diagnostics remain enabled. The next isolated subsystem is the **S-312C engine torque/power/fuel calibration**.\n''', encoding='utf-8')

# Sanity checks
ET.parse('modDesc.xml')
assert '<version>0.0.1.0</version>' in Path('modDesc.xml').read_text(encoding='utf-8')
assert '**0.0.1.0 – C-330 gearbox milestone prerelease**' in Path('README.md').read_text(encoding='utf-8')
assert '0.0.1.0 - C-330 gearbox milestone' in Path('CHANGELOG.md').read_text(encoding='utf-8')
print('0.0.1.0 gearbox milestone setup validated')
