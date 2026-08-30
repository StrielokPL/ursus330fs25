from pathlib import Path
import json
import xml.etree.ElementTree as ET

# 0.0.1.6: isolated refinement of the high-load II/2 -> II/3 guard.
# Runtime 0.0.1.5 showed the 0.80 threshold can miss a real heavy-load event
# because ADS was 0.757 at the exact shift decision, then ~0.908 after II/3.

p = Path('Scripts/C330TransmissionFix.lua')
s = p.read_text(encoding='utf-8')

s = s.replace(
    '-- 0.0.1.5 TEST: high-load top-gear guard with mass-aware 6F/2R control; ADS-safe.',
    '-- 0.0.1.6 TEST: refined high-load top-gear guard with mass-aware 6F/2R control; ADS-safe.',
    1
)

old = '''    -- 0.0.1.4 hill traces showed that the ratio-only prediction is too optimistic\n    -- while the tractor is pulling hard. Examples: 1928 rpm / 0.804 load -> ~1065 rpm,\n    -- 1976 / 0.878 -> ~974 rpm and 2081 / 0.840 -> ~1167 rpm after II/3 engaged.\n    -- A 2137 rpm / 0.822 shift recovered at ~1550 rpm, so keep II/2 below 2100 rpm\n    -- whenever the current load is already at or above 0.80.\n    local TOP_GEAR_HIGH_LOAD = 0.80\n    local TOP_GEAR_HIGH_LOAD_MIN_RPM = 2100\n'''
new = '''    -- Hill traces show that the ratio-only prediction is too optimistic while\n    -- the tractor is pulling hard. 0.0.1.5 proved that 0.80 is too high as an\n    -- instantaneous ADS threshold: a shift at 2088 rpm / 0.757 load was allowed\n    -- and the engine then landed near 1112 rpm / 0.908 load in II/3. Keep the\n    -- 2100 rpm boundary, but classify >=0.70 as high load to add enough margin\n    -- for the short ADS/load dip visible at the exact prediction sample.\n    local TOP_GEAR_HIGH_LOAD = 0.70\n    local TOP_GEAR_HIGH_LOAD_MIN_RPM = 2100\n'''
if old not in s:
    raise SystemExit('Expected 0.0.1.5 high-load constants block not found')
s = s.replace(old, new, 1)

s = s.replace(
    'Logging.info("[C330TRANS] 0.0.1.5 C-330 6F/2R controller installed (high-load top-gear guard, mass-aware start, ADS-safe)")',
    'Logging.info("[C330TRANS] 0.0.1.6 C-330 6F/2R controller installed (refined high-load top-gear guard, mass-aware start, ADS-safe)")',
    1
)

p.write_text(s, encoding='utf-8')

# Version
p = Path('modDesc.xml')
s = p.read_text(encoding='utf-8')
if '<version>0.0.1.5</version>' not in s:
    raise SystemExit('Expected modDesc 0.0.1.5')
s = s.replace('<version>0.0.1.5</version>', '<version>0.0.1.6</version>', 1)
p.write_text(s, encoding='utf-8')
ET.parse(p)

# README
p = Path('README.md')
s = p.read_text(encoding='utf-8')
old_line = '**0.0.1.5 – C-330 high-load II/3 guard prerelease**'
if old_line not in s:
    raise SystemExit('Expected README 0.0.1.5 line')
s = s.replace(old_line, '**0.0.1.6 – C-330 refined high-load II/3 guard prerelease**', 1)
p.write_text(s, encoding='utf-8')

# CHANGELOG
p = Path('CHANGELOG.md')
s = p.read_text(encoding='utf-8')
if not s.startswith('# Changelog\n\n'):
    raise SystemExit('Unexpected changelog header')
entry = '''# Changelog\n\n## 0.0.1.6 - C-330 refined high-load II/3 guard\n\nIsolated follow-up to the 0.0.1.5 trailer/no-trailer runtime test. **Only the high-load classification threshold for II/2 -> II/3 changes.**\n\n### Runtime evidence from 0.0.1.5\n- Without the trailer, top-gear shifts were acceptable and the mass-aware 1.683 t start remained `LIGHT_I3`.\n- With the trailer, total mass 3.469 t correctly selected `NATIVE_LOW_RANGE`.\n- One loaded II/2 -> II/3 shift was still too aggressive: 2088 rpm / 0.757 ADS at the decision, followed by about 1112 rpm / 0.908 load in II/3.\n- The new `>=0.80` high-load gate did not trigger because the instantaneous ADS sample dipped below 0.80 at the decision point.\n- All 11 observed range changes were attributed to `C330TRANS`; no `SHIFT_OSCILLATION`, Lua error or C330TRANS warning was present.\n\n### Change\n- `TOP_GEAR_HIGH_LOAD` reduced from **0.80** to **0.70**.\n- `TOP_GEAR_HIGH_LOAD_MIN_RPM` remains **2100 rpm**.\n- Therefore II/2 -> II/3 is held until 2100 rpm whenever the current filtered load is >=0.70.\n\n### Explicitly unchanged\n- 0.0.1.4 mass-aware start rule and 3.175 t threshold.\n- Forward I/3 <-> II/1 and reverse range logic.\n- Moderate-load predicted post-shift RPM guard.\n- S-312C 100 Nm engine curve, factory gearbox ratios, fuel use and chassis physics.\n- C-330M remains excluded.\n- ADS remains optional, filtered and read-only.\n\n'''
s = entry + s[len('# Changelog\n\n'):]
p.write_text(s, encoding='utf-8')

Path('.release/release.json').write_text(json.dumps({
    'version': '0.0.1.6',
    'tag': '0.0.1.6',
    'title': '0.0.1.6 - C-330 refined high-load II/3 guard test',
    'prerelease': True,
    'zipName': 'FS25_UrsusC330_330M_4x2.zip'
}, indent=2) + '\n', encoding='utf-8')

Path('.release/notes.md').write_text('''## Ursus C-330 / C-330M 0.0.1.6\n\nRefined high-load top-gear protection test.\n\n### Changed\n- II/2 -> II/3 now treats **load >=0.70** as high load instead of >=0.80,\n- the high-load minimum remains **2100 rpm**,\n- existing moderate-load predicted-RPM protection remains unchanged.\n\n### Why\nIn the 0.0.1.5 trailer test one shift occurred at 2088 rpm / 0.757 ADS and landed near 1112 rpm / 0.908 load in II/3. The 0.80 gate therefore missed a real loaded event because the instantaneous ADS sample had already dipped below 0.80.\n\n### Unchanged\nMass-aware starting, the 3.175 t threshold, range-boundary logic, reverse controller, 100 Nm S-312C curve, gearbox ratios, fuel use, ADS read-only handling, C-330M and chassis physics are unchanged.\n\n### Test focus\nRepeat one pass without a trailer and one with the same trailer. The loaded run should log `BLOCK TOP UPSHIFT HIGH LOAD` when II/2 requests II/3 below 2100 rpm at load >=0.70, and should no longer land close to 1100 rpm under ~0.9 load. Send the complete `log.txt`.\n''', encoding='utf-8')

# Sanity checks
ET.parse('modDesc.xml')
code = Path('Scripts/C330TransmissionFix.lua').read_text(encoding='utf-8')
assert 'TOP_GEAR_HIGH_LOAD = 0.70' in code
assert 'TOP_GEAR_HIGH_LOAD_MIN_RPM = 2100' in code
assert 'BLOCK TOP UPSHIFT HIGH LOAD' in code
assert 'LIGHT_START_MAX_TOTAL_MASS_T = FACTORY_BASE_MASS_T + LIGHT_START_EXTRA_MASS_T' in code
assert 'FORWARD_RANGE_DOWNSHIFT_MAX_SPEED = 6.0' in code
assert '0.0.1.6 C-330 6F/2R controller installed' in code
assert '<version>0.0.1.6</version>' in Path('modDesc.xml').read_text(encoding='utf-8')
vehicle = Path('c330m.xml').read_text(encoding='utf-8')
c0 = vehicle.find('<motorConfiguration name="C-330" hp="30" price="0">')
c1 = vehicle.find('</motorConfiguration>', c0)
cblock = vehicle[c0:c1]
assert 'torqueScale="0.100"' in cblock
assert 'normRpm="0.727273" torque="1.00"' in cblock
assert 'normRpm="0.818182" torque="1.00"' in cblock
assert 'normRpm="1.00" torque="0.972364"' in cblock
print('0.0.1.6 refined high-load threshold validated')
