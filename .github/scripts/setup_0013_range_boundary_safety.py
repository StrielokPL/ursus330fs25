from pathlib import Path
import json
import xml.etree.ElementTree as ET

# 0.0.1.3: isolate the remaining automatic range-boundary edge cases seen in the
# 0.0.1.2 runtime log. Engine curve, top-gear guard, ratios and ADS contract stay unchanged.

p = Path('Scripts/C330TransmissionFix.lua')
s = p.read_text(encoding='utf-8')

s = s.replace(
    '-- 0.0.1.2 TEST: 6F/2R range control with 100 Nm engine compatibility guards; ADS-safe.',
    '-- 0.0.1.3 TEST: 6F/2R range-boundary safety with 100 Nm engine; ADS-safe.',
    1
)

needle = '''    local RANGE_DOWNSHIFT_RPM = 1500\n    local RANGE_DOWNSHIFT_LOAD = 0.75\n    local RANGE_DOWNSHIFT_ACCEL = 0.85\n    -- Full throttle alone must not force II/1 -> I/3 when the engine is lightly loaded.\n    -- 0.0.1.1 runtime trace showed an unnecessary reduction at ~1499 rpm, load 0.335.\n    local RANGE_DOWNSHIFT_ACCEL_MIN_LOAD = 0.55\n'''
replacement = '''    local RANGE_DOWNSHIFT_RPM = 1500\n    local RANGE_DOWNSHIFT_LOAD = 0.75\n    local RANGE_DOWNSHIFT_ACCEL = 0.85\n    -- Full throttle alone must not force II/1 -> I/3 when the engine is lightly loaded.\n    -- 0.0.1.1 runtime trace showed an unnecessary reduction at ~1499 rpm, load 0.335.\n    local RANGE_DOWNSHIFT_ACCEL_MIN_LOAD = 0.55\n    -- Factory I/3 is 5.649 km/h at 2200 rpm. Allow a small governor margin, but\n    -- never command the mechanical II/1 -> I/3 range change above 6.0 km/h.\n    -- 6.0 km/h corresponds to ~2337 rpm in I/3, still below the ~2450 rpm\n    -- no-load governor speed from the workshop documentation.\n    local FORWARD_RANGE_DOWNSHIFT_MAX_SPEED = 6.0\n    -- getBestStartGear is not guaranteed to be called during every near-stop.\n    -- Force range I deterministically once forward speed is essentially walking pace.\n    local FORWARD_LOW_SPEED_RANGE_RESET = 0.5\n'''
if needle not in s:
    raise SystemExit('range constants anchor not found')
s = s.replace(needle, replacement, 1)

needle = '''        local accel = math.abs(tonumber(acceleratorPedal) or 0)\n        local maxGear = math.min(#gears, 3)\n\n        -- Reverse has one mechanical reverse gear passing through the same I/II\n'''
insert = '''        local accel = math.abs(tonumber(acceleratorPedal) or 0)\n        local maxGear = math.min(#gears, 3)\n\n        -- 0.0.1.2 showed that a near-stop can occasionally continue in range II\n        -- without getBestStartGear resetting the box first. Do not allow the\n        -- automatic forward transmission to re-accelerate through II/2 or II/3\n        -- from walking pace: a real C-330 restarts in range I.\n        if isAutomaticForward(self)\n            and range == HIGH_RANGE\n            and speed <= FORWARD_LOW_SPEED_RANGE_RESET then\n            return setAutomaticRange(\n                self, LOW_RANGE, 1, "LOW SPEED RANGE RESET",\n                rpm, load, loadSource, false\n            )\n        end\n\n        -- Reverse has one mechanical reverse gear passing through the same I/II\n'''
if needle not in s:
    raise SystemExit('low speed insertion anchor not found')
s = s.replace(needle, insert, 1)

needle = '''        if range == HIGH_RANGE\n            and curGear == 1\n            and speed > 0.5\n            and rpm <= RANGE_DOWNSHIFT_RPM\n'''
replacement = '''        if range == HIGH_RANGE\n            and curGear == 1\n            and speed > 0.5\n            and speed <= FORWARD_RANGE_DOWNSHIFT_MAX_SPEED\n            and rpm <= RANGE_DOWNSHIFT_RPM\n'''
# only replace the forward block; the reverse block has speed > 0.3
if needle not in s:
    raise SystemExit('forward range down anchor not found')
s = s.replace(needle, replacement, 1)

s = s.replace(
    'Logging.info("[C330TRANS] 0.0.1.2 C-330 6F/2R controller installed (100Nm compatibility guards, ADS-safe)")',
    'Logging.info("[C330TRANS] 0.0.1.3 C-330 6F/2R controller installed (range-boundary safety, ADS-safe)")',
    1
)

p.write_text(s, encoding='utf-8')

# Version
p = Path('modDesc.xml')
s = p.read_text(encoding='utf-8')
if '<version>0.0.1.2</version>' not in s:
    raise SystemExit('Expected modDesc 0.0.1.2')
s = s.replace('<version>0.0.1.2</version>', '<version>0.0.1.3</version>', 1)
p.write_text(s, encoding='utf-8')
ET.parse(p)

# README
p = Path('README.md')
s = p.read_text(encoding='utf-8')
if '**0.0.1.2 – S-312C / gearbox compatibility test prerelease**' not in s:
    raise SystemExit('Expected README 0.0.1.2 line')
s = s.replace(
    '**0.0.1.2 – S-312C / gearbox compatibility test prerelease**',
    '**0.0.1.3 – C-330 range-boundary safety prerelease**',
    1
)
p.write_text(s, encoding='utf-8')

# CHANGELOG
p = Path('CHANGELOG.md')
s = p.read_text(encoding='utf-8')
if not s.startswith('# Changelog\n\n'):
    raise SystemExit('Unexpected changelog header')
entry = '''# Changelog\n\n## 0.0.1.3 - C-330 range-boundary safety\n\nSmall isolated follow-up to the 0.0.1.2 gearbox/100 Nm compatibility test. **Engine and top-gear calibration are unchanged.**\n\n### Runtime evidence from 0.0.1.2\n- The II/2 -> II/3 predicted-RPM guard works: repeated `BLOCK TOP UPSHIFT` events occurred under load and the eventual shifts happened at materially higher RPM.\n- A remaining II/1 -> I/3 request occurred at about **7.41 km/h / 1488 rpm / ADS load 0.559**. That speed is above the factory I/3 road speed (5.649 km/h at 2200 rpm), so commanding I/3 there is mechanically undesirable even if the throttle/load condition is otherwise true.\n- After a near-stop in range II, the runtime state machine could sometimes accelerate again through II/2 and II/3 before `getBestStartGear` performed a range-I reset.\n- The interrupted interval with engine RPM=0 and implausible vehicle-speed jumps was excluded from calibration decisions.\n\n### Change\n- Forward II/1 -> I/3 is now permitted only at <= **6.0 km/h**. This leaves a small governor margin above the 5.649 km/h rated I/3 speed while avoiding an over-speed range selection.\n- Automatic forward now performs a deterministic **LOW SPEED RANGE RESET** to range I at <= **0.5 km/h** if range II is still active.\n\n### Explicitly unchanged\n- S-312C 100 Nm torque curve from 0.0.1.1.\n- 0.0.1.2 II/2 -> II/3 predicted-RPM guard (1200 rpm target, load-aware).\n- Factory 6F/2R ratios, other range thresholds and reverse logic.\n- Fuel use, min/max RPM, chassis physics and C-330M.\n- ADS remains optional, filtered and read-only.\n\n'''
s = entry + s[len('# Changelog\n\n'):]
p.write_text(s, encoding='utf-8')

Path('.release/release.json').write_text(json.dumps({
    'version': '0.0.1.3',
    'tag': '0.0.1.3',
    'title': '0.0.1.3 - C-330 range-boundary safety test',
    'prerelease': True,
    'zipName': 'FS25_UrsusC330_330M_4x2.zip'
}, indent=2) + '\n', encoding='utf-8')

Path('.release/notes.md').write_text('''## Ursus C-330 / C-330M 0.0.1.3\n\nFinal small automatic-range boundary test before returning to the S-312C engine.\n\n### Changed\n- II/1 -> I/3 is blocked above 6.0 km/h, preventing the automatic controller from selecting I/3 above its mechanical road-speed range,\n- if the tractor nearly stops while range II remains active, automatic forward now resets deterministically to range I at <=0.5 km/h.\n\n### Unchanged\nThe 100 Nm S-312C curve, the 0.0.1.2 top-gear predicted-RPM guard, gearbox ratios, reverse logic, fuel use, ADS read-only handling, C-330M and chassis physics are unchanged.\n\n### Test focus\nRepeat loaded acceleration/deceleration with C-330 motor=1. Confirm that II/1 no longer changes to I/3 above 6.0 km/h and that a near-stop in range II produces `LOW SPEED RANGE RESET` before re-acceleration. The existing `BLOCK TOP UPSHIFT` behavior should remain unchanged. Send the complete `log.txt`.\n''', encoding='utf-8')

# Sanity checks
ET.parse('modDesc.xml')
code = Path('Scripts/C330TransmissionFix.lua').read_text(encoding='utf-8')
assert 'FORWARD_RANGE_DOWNSHIFT_MAX_SPEED = 6.0' in code
assert 'FORWARD_LOW_SPEED_RANGE_RESET = 0.5' in code
assert 'LOW SPEED RANGE RESET' in code
assert 'speed <= FORWARD_RANGE_DOWNSHIFT_MAX_SPEED' in code
assert 'TOP_GEAR_POSTSHIFT_MIN_RPM = 1200' in code
assert '0.0.1.3 C-330 6F/2R controller installed' in code
assert '<version>0.0.1.3</version>' in Path('modDesc.xml').read_text(encoding='utf-8')
# Engine must remain exactly on the 0.0.1.1 safe point.
vehicle = Path('c330m.xml').read_text(encoding='utf-8')
c0 = vehicle.find('<motorConfiguration name="C-330" hp="30" price="0">')
c1 = vehicle.find('</motorConfiguration>', c0)
cblock = vehicle[c0:c1]
assert 'torqueScale="0.100"' in cblock
assert 'normRpm="0.727273" torque="1.00"' in cblock
assert 'normRpm="0.818182" torque="1.00"' in cblock
assert 'normRpm="1.00" torque="0.972364"' in cblock
print('0.0.1.3 range-boundary safety test validated')
