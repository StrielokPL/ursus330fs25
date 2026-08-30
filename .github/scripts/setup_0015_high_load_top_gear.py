from pathlib import Path
import json
import xml.etree.ElementTree as ET

# 0.0.1.5: isolated high-load II/2 -> II/3 protection.
# Preserve 0.0.1.4 mass-aware start, range logic, 100 Nm engine and ADS contract.

p = Path('Scripts/C330TransmissionFix.lua')
s = p.read_text(encoding='utf-8')

s = s.replace(
    '-- 0.0.1.4 TEST: mass-aware forward start gear with 6F/2R range safety; ADS-safe.',
    '-- 0.0.1.5 TEST: high-load top-gear guard with mass-aware 6F/2R control; ADS-safe.',
    1
)

anchor = '''    local TOP_GEAR_POSTSHIFT_RPM_RATIO = 14.324 / 22.878\n    local TOP_GEAR_POSTSHIFT_MIN_RPM = 1200\n    local TOP_GEAR_PREDICTION_GUARD_MIN_LOAD = 0.55\n'''
replacement = '''    local TOP_GEAR_POSTSHIFT_RPM_RATIO = 14.324 / 22.878\n    local TOP_GEAR_POSTSHIFT_MIN_RPM = 1200\n    local TOP_GEAR_PREDICTION_GUARD_MIN_LOAD = 0.55\n    -- 0.0.1.4 hill traces showed that the ratio-only prediction is too optimistic\n    -- while the tractor is pulling hard. Examples: 1928 rpm / 0.804 load -> ~1065 rpm,\n    -- 1976 / 0.878 -> ~974 rpm and 2081 / 0.840 -> ~1167 rpm after II/3 engaged.\n    -- A 2137 rpm / 0.822 shift recovered at ~1550 rpm, so keep II/2 below 2100 rpm\n    -- whenever the current load is already at or above 0.80.\n    local TOP_GEAR_HIGH_LOAD = 0.80\n    local TOP_GEAR_HIGH_LOAD_MIN_RPM = 2100\n'''
if anchor not in s:
    raise SystemExit('top gear constants anchor not found')
s = s.replace(anchor, replacement, 1)

anchor = '''        if range == HIGH_RANGE\n            and curGear == 2\n            and targetGear == 3\n            and load ~= nil\n            and load >= TOP_GEAR_PREDICTION_GUARD_MIN_LOAD then\n            local predictedRpm = rpm * TOP_GEAR_POSTSHIFT_RPM_RATIO\n            if predictedRpm < TOP_GEAR_POSTSHIFT_MIN_RPM then\n                logDecision(self, "BLOCK TOP UPSHIFT", curGear, range, curGear, range, rpm, load, loadSource)\n                self.autoGearChangeTimer = math.max(self.autoGearChangeTime or 0, 250)\n                return curGear\n            end\n        end\n'''
replacement = '''        if range == HIGH_RANGE\n            and curGear == 2\n            and targetGear == 3\n            and load ~= nil\n            and load >= TOP_GEAR_PREDICTION_GUARD_MIN_LOAD then\n            -- On a real climb the vehicle can lose appreciable road speed during\n            -- the 0.4 s gear change, so a static ratio prediction alone can still\n            -- allow II/3 to land below the useful engine band. Under heavy load,\n            -- require the engine to be essentially at the top of II/2 first.\n            if load >= TOP_GEAR_HIGH_LOAD and rpm < TOP_GEAR_HIGH_LOAD_MIN_RPM then\n                logDecision(self, "BLOCK TOP UPSHIFT HIGH LOAD", curGear, range, curGear, range, rpm, load, loadSource)\n                self.autoGearChangeTimer = math.max(self.autoGearChangeTime or 0, 250)\n                return curGear\n            end\n\n            local predictedRpm = rpm * TOP_GEAR_POSTSHIFT_RPM_RATIO\n            if predictedRpm < TOP_GEAR_POSTSHIFT_MIN_RPM then\n                logDecision(self, "BLOCK TOP UPSHIFT", curGear, range, curGear, range, rpm, load, loadSource)\n                self.autoGearChangeTimer = math.max(self.autoGearChangeTime or 0, 250)\n                return curGear\n            end\n        end\n'''
if anchor not in s:
    raise SystemExit('top gear guard anchor not found')
s = s.replace(anchor, replacement, 1)

s = s.replace(
    'Logging.info("[C330TRANS] 0.0.1.4 C-330 6F/2R controller installed (mass-aware start gear, range safety, ADS-safe)")',
    'Logging.info("[C330TRANS] 0.0.1.5 C-330 6F/2R controller installed (high-load top-gear guard, mass-aware start, ADS-safe)")',
    1
)

p.write_text(s, encoding='utf-8')

# Version
p = Path('modDesc.xml')
s = p.read_text(encoding='utf-8')
if '<version>0.0.1.4</version>' not in s:
    raise SystemExit('Expected modDesc 0.0.1.4')
s = s.replace('<version>0.0.1.4</version>', '<version>0.0.1.5</version>', 1)
p.write_text(s, encoding='utf-8')
ET.parse(p)

# README
p = Path('README.md')
s = p.read_text(encoding='utf-8')
if '**0.0.1.4 – C-330 mass-aware I/3 start prerelease**' not in s:
    raise SystemExit('Expected README 0.0.1.4 line')
s = s.replace(
    '**0.0.1.4 – C-330 mass-aware I/3 start prerelease**',
    '**0.0.1.5 – C-330 high-load II/3 guard prerelease**',
    1
)
p.write_text(s, encoding='utf-8')

# CHANGELOG
p = Path('CHANGELOG.md')
s = p.read_text(encoding='utf-8')
if not s.startswith('# Changelog\n\n'):
    raise SystemExit('Unexpected changelog header')
entry = '''# Changelog\n\n## 0.0.1.5 - C-330 high-load II/3 guard\n\nIsolated automatic transmission test based on the 0.0.1.4 flat + slope runtime trace. **Mass-aware starting, range logic, engine calibration and ADS handling are unchanged.**\n\n### Runtime evidence from 0.0.1.4\n- Mass-aware starting classified every observed set correctly: 1.683 t -> `LIGHT_I3`; 3.469 t, 6.885 t and 12.881 t -> `NATIVE_LOW_RANGE`.\n- All 39 observed range changes were attributed to `C330TRANS`; there were no `SHIFT_OSCILLATION` warnings and no Lua errors.\n- The existing II/2 -> II/3 predicted-RPM guard works at moderate load, but hill tests exposed a high-load corner case.\n- Observed high-load shifts: about 1928 rpm / 0.804 ADS -> ~1065 rpm / 0.905 after II/3; 1976 / 0.878 -> ~974 / 0.990; 2081 / 0.840 -> ~1167 / 0.857.\n- A later 2137 rpm / 0.822 shift recovered around 1550 rpm, providing a useful safe-side boundary for the next test.\n\n### Change\n- Added a high-load II/2 -> II/3 gate: when load is **>= 0.80**, II/3 is blocked below **2100 rpm**.\n- Existing moderate-load predicted post-shift guard (`>=0.55` load, predicted minimum 1200 rpm) remains in place.\n- New diagnostic reason: `BLOCK TOP UPSHIFT HIGH LOAD`.\n\n### Explicitly unchanged\n- 0.0.1.4 light-set start rule: total mass <3.175 t starts in I/3; heavier/unknown mass retains native low-range start selection.\n- Forward I/3 <-> II/1 and reverse range logic, including the 6.0 km/h forward range-down ceiling.\n- S-312C 100 Nm torque curve, factory gearbox ratios, fuel use and chassis physics.\n- C-330M remains excluded.\n- ADS remains optional, filtered and read-only; no ADS state is written.\n\n'''
s = entry + s[len('# Changelog\n\n'):]
p.write_text(s, encoding='utf-8')

Path('.release/release.json').write_text(json.dumps({
    'version': '0.0.1.5',
    'tag': '0.0.1.5',
    'title': '0.0.1.5 - C-330 high-load II/3 guard test',
    'prerelease': True,
    'zipName': 'FS25_UrsusC330_330M_4x2.zip'
}, indent=2) + '\n', encoding='utf-8')

Path('.release/notes.md').write_text('''## Ursus C-330 / C-330M 0.0.1.5\n\nIsolated high-load top-gear protection test.\n\n### Changed\n- II/2 -> II/3 is now blocked below **2100 rpm** whenever current engine load is **>=0.80**,\n- the existing predicted post-shift RPM protection remains active for moderate load,\n- a new `BLOCK TOP UPSHIFT HIGH LOAD` diagnostic identifies this specific guard.\n\n### Unchanged\nThe 0.0.1.4 mass-aware I/3 start rule, range-boundary logic, reverse controller, 100 Nm S-312C curve, gearbox ratios, fuel use, ADS read-only handling, C-330M and chassis physics are unchanged.\n\n### Why\nThe 0.0.1.4 hill test allowed II/3 at roughly 1976 rpm / 0.878 load and the engine landed near 974 rpm / 0.990 load. Similar high-load cases landed around 1065-1167 rpm. A 2137 rpm / 0.822 shift recovered around 1550 rpm, so 2100 rpm is the isolated test threshold.\n\n### Test focus\nRepeat a flat acceleration and, most importantly, the same uphill/downhill stop-and-restart sequence. On a climb, high-load II/2 should log `BLOCK TOP UPSHIFT HIGH LOAD` until about 2100 rpm instead of dropping the engine toward 1000 rpm in II/3. Send the complete `log.txt`.\n''', encoding='utf-8')

# Sanity checks
ET.parse('modDesc.xml')
code = Path('Scripts/C330TransmissionFix.lua').read_text(encoding='utf-8')
assert 'TOP_GEAR_HIGH_LOAD = 0.80' in code
assert 'TOP_GEAR_HIGH_LOAD_MIN_RPM = 2100' in code
assert 'BLOCK TOP UPSHIFT HIGH LOAD' in code
assert 'LIGHT_START_MAX_TOTAL_MASS_T = FACTORY_BASE_MASS_T + LIGHT_START_EXTRA_MASS_T' in code
assert 'FORWARD_RANGE_DOWNSHIFT_MAX_SPEED = 6.0' in code
assert 'TOP_GEAR_POSTSHIFT_MIN_RPM = 1200' in code
assert '0.0.1.5 C-330 6F/2R controller installed' in code
assert '<version>0.0.1.5</version>' in Path('modDesc.xml').read_text(encoding='utf-8')
vehicle = Path('c330m.xml').read_text(encoding='utf-8')
c0 = vehicle.find('<motorConfiguration name="C-330" hp="30" price="0">')
c1 = vehicle.find('</motorConfiguration>', c0)
cblock = vehicle[c0:c1]
assert 'torqueScale="0.100"' in cblock
assert 'normRpm="0.727273" torque="1.00"' in cblock
assert 'normRpm="0.818182" torque="1.00"' in cblock
assert 'normRpm="1.00" torque="0.972364"' in cblock
print('0.0.1.5 high-load top-gear guard validated')
