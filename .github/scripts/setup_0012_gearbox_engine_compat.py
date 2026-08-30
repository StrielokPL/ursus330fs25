from pathlib import Path
import json
import xml.etree.ElementTree as ET

# 0.0.1.2: small gearbox compatibility correction revealed by the 100 Nm S-312C test.
# Engine curve, ratios, ADS read-only contract and all chassis physics stay unchanged.

p = Path('Scripts/C330TransmissionFix.lua')
s = p.read_text(encoding='utf-8')

s = s.replace(
    '-- 0.0.0.7 TEST: complete automatic 6F/2R range control; ADS-safe forward and reverse.',
    '-- 0.0.1.2 TEST: 6F/2R range control with 100 Nm engine compatibility guards; ADS-safe.',
    1
)

needle = '''    local RANGE_DOWNSHIFT_RPM = 1500\n    local RANGE_DOWNSHIFT_LOAD = 0.75\n    local RANGE_DOWNSHIFT_ACCEL = 0.85\n'''
replacement = '''    local RANGE_DOWNSHIFT_RPM = 1500\n    local RANGE_DOWNSHIFT_LOAD = 0.75\n    local RANGE_DOWNSHIFT_ACCEL = 0.85\n    -- Full throttle alone must not force II/1 -> I/3 when the engine is lightly loaded.\n    -- 0.0.1.1 runtime trace showed an unnecessary reduction at ~1499 rpm, load 0.335.\n    local RANGE_DOWNSHIFT_ACCEL_MIN_LOAD = 0.55\n'''
if needle not in s:
    raise SystemExit('Downshift constants anchor not found')
s = s.replace(needle, replacement, 1)

needle = '''    local NORMAL_UPSHIFT_GUARD_LOAD = 0.80\n    local NORMAL_UPSHIFT_GUARD_RPM = 1750\n'''
replacement = '''    local NORMAL_UPSHIFT_GUARD_LOAD = 0.80\n    local NORMAL_UPSHIFT_GUARD_RPM = 1750\n\n    -- II/2 -> II/3 is the largest within-range step. With the factory speed ladder,\n    -- engine rpm after the shift is approximately currentRpm * (14.324 / 22.878).\n    -- The 0.0.1.1 test allowed a shift at 1695 rpm / load 0.789 and the engine fell\n    -- to ~960-980 rpm at ~0.9 load. Keep vanilla freedom at light load, but under\n    -- meaningful load require a predicted post-shift speed of at least ~1200 rpm.\n    local TOP_GEAR_POSTSHIFT_RPM_RATIO = 14.324 / 22.878\n    local TOP_GEAR_POSTSHIFT_MIN_RPM = 1200\n    local TOP_GEAR_PREDICTION_GUARD_MIN_LOAD = 0.55\n'''
if needle not in s:
    raise SystemExit('Upshift constants anchor not found')
s = s.replace(needle, replacement, 1)

old_reverse = '''            if range == HIGH_RANGE\n                and curGear == 1\n                and speed > 0.3\n                and rpm <= RANGE_DOWNSHIFT_RPM\n                and ((load ~= nil and load >= RANGE_DOWNSHIFT_LOAD) or accel >= RANGE_DOWNSHIFT_ACCEL) then\n'''
new_reverse = '''            if range == HIGH_RANGE\n                and curGear == 1\n                and speed > 0.3\n                and rpm <= RANGE_DOWNSHIFT_RPM\n                and (\n                    (load ~= nil and load >= RANGE_DOWNSHIFT_LOAD)\n                    or (accel >= RANGE_DOWNSHIFT_ACCEL and load ~= nil and load >= RANGE_DOWNSHIFT_ACCEL_MIN_LOAD)\n                ) then\n'''
if old_reverse not in s:
    raise SystemExit('Reverse downshift block not found')
s = s.replace(old_reverse, new_reverse, 1)

old_forward = '''        if range == HIGH_RANGE\n            and curGear == 1\n            and speed > 0.5\n            and rpm <= RANGE_DOWNSHIFT_RPM\n            and ((load ~= nil and load >= RANGE_DOWNSHIFT_LOAD) or accel >= RANGE_DOWNSHIFT_ACCEL) then\n'''
new_forward = '''        if range == HIGH_RANGE\n            and curGear == 1\n            and speed > 0.5\n            and rpm <= RANGE_DOWNSHIFT_RPM\n            and (\n                (load ~= nil and load >= RANGE_DOWNSHIFT_LOAD)\n                or (accel >= RANGE_DOWNSHIFT_ACCEL and load ~= nil and load >= RANGE_DOWNSHIFT_ACCEL_MIN_LOAD)\n            ) then\n'''
if old_forward not in s:
    raise SystemExit('Forward range down block not found')
s = s.replace(old_forward, new_forward, 1)

needle = '''        targetGear = math.max(1, math.min(targetGear, maxGear))\n\n        -- Do not allow a normal upshift when the engine is already heavily loaded\n'''
insert = '''        targetGear = math.max(1, math.min(targetGear, maxGear))\n\n        -- Special protection for II/2 -> II/3 with the calibrated 100 Nm engine.\n        -- Do not blindly follow vanilla if the factory ratio step would drop the\n        -- engine far below its useful band while it is already carrying real load.\n        if range == HIGH_RANGE\n            and curGear == 2\n            and targetGear == 3\n            and load ~= nil\n            and load >= TOP_GEAR_PREDICTION_GUARD_MIN_LOAD then\n            local predictedRpm = rpm * TOP_GEAR_POSTSHIFT_RPM_RATIO\n            if predictedRpm < TOP_GEAR_POSTSHIFT_MIN_RPM then\n                logDecision(self, "BLOCK TOP UPSHIFT", curGear, range, curGear, range, rpm, load, loadSource)\n                self.autoGearChangeTimer = math.max(self.autoGearChangeTime or 0, 250)\n                return curGear\n            end\n        end\n\n        -- Do not allow a normal upshift when the engine is already heavily loaded\n'''
if needle not in s:
    raise SystemExit('Top gear guard insertion anchor not found')
s = s.replace(needle, insert, 1)

s = s.replace(
    'Logging.info("[C330TRANS] 0.0.0.7 C-330 full 6F/2R automatic range controller installed (ADS-safe)")',
    'Logging.info("[C330TRANS] 0.0.1.2 C-330 6F/2R controller installed (100Nm compatibility guards, ADS-safe)")',
    1
)
p.write_text(s, encoding='utf-8')

# Version
p = Path('modDesc.xml')
s = p.read_text(encoding='utf-8')
if '<version>0.0.1.1</version>' not in s:
    raise SystemExit('Expected modDesc 0.0.1.1')
s = s.replace('<version>0.0.1.1</version>', '<version>0.0.1.2</version>', 1)
p.write_text(s, encoding='utf-8')
ET.parse(p)

# README
p = Path('README.md')
s = p.read_text(encoding='utf-8')
if '**0.0.1.1 – S-312C torque-curve test prerelease**' not in s:
    raise SystemExit('Expected README 0.0.1.1 line')
s = s.replace(
    '**0.0.1.1 – S-312C torque-curve test prerelease**',
    '**0.0.1.2 – S-312C / gearbox compatibility test prerelease**',
    1
)
p.write_text(s, encoding='utf-8')

# Changelog
p = Path('CHANGELOG.md')
s = p.read_text(encoding='utf-8')
if not s.startswith('# Changelog\n\n'):
    raise SystemExit('Unexpected changelog header')
entry = '''# Changelog\n\n## 0.0.1.2 - S-312C / gearbox compatibility fix\n\nSmall isolated transmission-controller correction based on the 0.0.1.1 100 Nm engine runtime trace. **The S-312C torque curve itself is unchanged.**\n\n### Runtime evidence\n- II/2 -> II/3 was allowed at about **1695 rpm / ADS load 0.789**; after engagement the engine fell to about **960-980 rpm at ~0.89-0.93 load** before recovering.\n- II/1 -> I/3 could be requested at about **1499 rpm / load 0.335** only because the accelerator was near full; the engine was not actually overloaded.\n\n### Change\n- Full throttle is no longer enough by itself to force a range downshift. The accelerator path additionally requires load >= **0.55**; the original high-load path (>=0.75) remains unchanged.\n- Added a dedicated II/2 -> II/3 prediction guard. At load >= **0.55**, the controller estimates post-shift RPM using the factory 14.324/22.878 speed ratio and blocks the shift if predicted RPM would be below **1200 rpm**.\n- Light-load top-gear shifts remain available to vanilla prediction, so unloaded road acceleration is not artificially forced to wait for a fixed high RPM.\n\n### Explicitly unchanged\n- C-330 S-312C curve from 0.0.1.1: 100 Nm peak, 1600-1800 rpm plateau, ~97.24 Nm at 2200 rpm.\n- Fuel use, min/max RPM and engine acceleration/braking parameters.\n- Factory 6F/2R ratios and range thresholds.\n- ADS remains optional, filtered and read-only.\n- C-330M and chassis physics.\n\n'''
s = entry + s[len('# Changelog\n\n'):]
p.write_text(s, encoding='utf-8')

Path('.release/release.json').write_text(json.dumps({
    'version': '0.0.1.2',
    'tag': '0.0.1.2',
    'title': '0.0.1.2 - S-312C gearbox compatibility test',
    'prerelease': True,
    'zipName': 'FS25_UrsusC330_330M_4x2.zip'
}, indent=2) + '\n', encoding='utf-8')

Path('.release/notes.md').write_text('''## Ursus C-330 / C-330M 0.0.1.2\n\nSmall compatibility correction between the completed C-330 gearbox controller and the calibrated **100 Nm S-312C** test curve.\n\n### Changed\n- prevents full throttle alone from forcing II/1 -> I/3 while engine load is low,\n- adds a load-aware predicted-RPM guard for II/2 -> II/3,\n- under meaningful load, top gear is blocked if the factory ratio step predicts <1200 rpm after the shift.\n\n### Unchanged\nThe 0.0.1.1 engine curve, fuel use, gearbox ratios, ADS read-only handling, C-330M and chassis physics are unchanged.\n\n### Test focus\nUse C-330 motor=1 with the same heavy trailer. Watch II/2 under load: the controller should log `BLOCK TOP UPSHIFT` instead of dropping II/3 to ~1000 rpm. Also reproduce sustained full throttle in II/1 with moderate/low load; it should no longer unnecessarily reduce to I/3. Send the complete `log.txt`.\n''', encoding='utf-8')

# Sanity checks
ET.parse('modDesc.xml')
code = Path('Scripts/C330TransmissionFix.lua').read_text(encoding='utf-8')
assert 'RANGE_DOWNSHIFT_ACCEL_MIN_LOAD = 0.55' in code
assert 'TOP_GEAR_POSTSHIFT_MIN_RPM = 1200' in code
assert 'BLOCK TOP UPSHIFT' in code
assert '0.0.1.2 C-330 6F/2R controller installed' in code
assert '<version>0.0.1.2</version>' in Path('modDesc.xml').read_text(encoding='utf-8')
# Prove engine curve remains untouched from 0.0.1.1.
vehicle = Path('c330m.xml').read_text(encoding='utf-8')
c0 = vehicle.find('<motorConfiguration name="C-330" hp="30" price="0">')
c1 = vehicle.find('</motorConfiguration>', c0)
cblock = vehicle[c0:c1]
assert 'torqueScale="0.100"' in cblock
assert 'normRpm="0.727273" torque="1.00"' in cblock
assert 'normRpm="0.818182" torque="1.00"' in cblock
assert 'normRpm="1.00" torque="0.972364"' in cblock
print('0.0.1.2 gearbox/100Nm compatibility test validated')
