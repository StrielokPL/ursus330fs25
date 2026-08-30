from pathlib import Path
import json
import xml.etree.ElementTree as ET

# 0.0.1.7: heavy-set II/3 stabilization based on 0.0.1.6 runtime evidence.
# Keep light-set behavior unchanged. For total mass >= 3.175 t require load < 0.70
# continuously for 600 ms before II/2 -> II/3 may proceed.

p = Path('Scripts/C330TransmissionFix.lua')
s = p.read_text(encoding='utf-8')

s = s.replace(
    '-- 0.0.1.6 TEST: refined high-load top-gear guard with mass-aware 6F/2R control; ADS-safe.',
    '-- 0.0.1.7 TEST: heavy-set top-gear stability guard with mass-aware 6F/2R control; ADS-safe.',
    1
)

old_constants = '''    -- Hill traces show that the ratio-only prediction is too optimistic while\n    -- the tractor is pulling hard. 0.0.1.5 proved that 0.80 is too high as an\n    -- instantaneous ADS threshold: a shift at 2088 rpm / 0.757 load was allowed\n    -- and the engine then landed near 1112 rpm / 0.908 load in II/3. Keep the\n    -- 2100 rpm boundary, but classify >=0.70 as high load to add enough margin\n    -- for the short ADS/load dip visible at the exact prediction sample.\n    local TOP_GEAR_HIGH_LOAD = 0.70\n    local TOP_GEAR_HIGH_LOAD_MIN_RPM = 2100\n'''
new_constants = '''    -- 0.0.1.6 proved that the instantaneous load threshold itself is not enough:\n    -- on a heavy set ADS can fall below 0.70 for a fraction of a second just before\n    -- GIANTS requests II/3, then rise back above ~0.85 after the shift. Runtime\n    -- evidence separated bad transient windows (~0.15-0.27 s) from acceptable\n    -- recovery windows (~0.75-0.82 s). For a set at or above the same 3.175 t\n    -- threshold used by mass-aware starting, require 600 ms of continuous load\n    -- below 0.70 before top gear is allowed. Light sets keep the current behavior.\n    local TOP_GEAR_HIGH_LOAD = 0.70\n    local TOP_GEAR_HIGH_LOAD_MIN_RPM = 2100\n    local TOP_GEAR_HEAVY_SET_STABLE_MS = 600\n'''
if old_constants not in s:
    raise SystemExit('Expected 0.0.1.6 top-gear constants block not found')
s = s.replace(old_constants, new_constants, 1)

old_local = '''        local speed = getSpeed(self)\n        local accel = math.abs(tonumber(acceleratorPedal) or 0)\n        local maxGear = math.min(#gears, 3)\n'''
new_local = '''        local speed = getSpeed(self)\n        local totalMass = getTotalMassTons(self)\n        local accel = math.abs(tonumber(acceleratorPedal) or 0)\n        local maxGear = math.min(#gears, 3)\n'''
if old_local not in s:
    raise SystemExit('Expected local state block not found')
s = s.replace(old_local, new_local, 1)

old_guard = '''        -- Special protection for II/2 -> II/3 with the calibrated 100 Nm engine.\n        -- Do not blindly follow vanilla if the factory ratio step would drop the\n        -- engine far below its useful band while it is already carrying real load.\n        if range == HIGH_RANGE\n            and curGear == 2\n            and targetGear == 3\n            and load ~= nil\n            and load >= TOP_GEAR_PREDICTION_GUARD_MIN_LOAD then\n            -- On a real climb the vehicle can lose appreciable road speed during\n            -- the 0.4 s gear change, so a static ratio prediction alone can still\n            -- allow II/3 to land below the useful engine band. Under heavy load,\n            -- require the engine to be essentially at the top of II/2 first.\n            if load >= TOP_GEAR_HIGH_LOAD and rpm < TOP_GEAR_HIGH_LOAD_MIN_RPM then\n                logDecision(self, "BLOCK TOP UPSHIFT HIGH LOAD", curGear, range, curGear, range, rpm, load, loadSource)\n                self.autoGearChangeTimer = math.max(self.autoGearChangeTime or 0, 250)\n                return curGear\n            end\n\n            local predictedRpm = rpm * TOP_GEAR_POSTSHIFT_RPM_RATIO\n            if predictedRpm < TOP_GEAR_POSTSHIFT_MIN_RPM then\n                logDecision(self, "BLOCK TOP UPSHIFT", curGear, range, curGear, range, rpm, load, loadSource)\n                self.autoGearChangeTimer = math.max(self.autoGearChangeTime or 0, 250)\n                return curGear\n            end\n        end\n'''
new_guard = '''        -- Special protection for II/2 -> II/3 with the calibrated 100 Nm engine.\n        -- Heavy sets use a short recovery hold so a transient ADS dip cannot open\n        -- top gear while the tractor is still pulling hard. ADS remains read-only.\n        if range == HIGH_RANGE\n            and curGear == 2\n            and targetGear == 3\n            and load ~= nil then\n            local heavySet = totalMass ~= nil and totalMass >= LIGHT_START_MAX_TOTAL_MASS_T\n\n            if heavySet then\n                if load >= TOP_GEAR_HIGH_LOAD then\n                    self.c330FixTopGearLowLoadSince = nil\n                    logDecision(self, "BLOCK TOP UPSHIFT HEAVY SET", curGear, range, curGear, range, rpm, load, loadSource)\n                    self.autoGearChangeTimer = math.max(self.autoGearChangeTime or 0, 250)\n                    return curGear\n                end\n\n                if self.c330FixTopGearLowLoadSince == nil then\n                    self.c330FixTopGearLowLoadSince = now\n                    logDecision(self, "BLOCK TOP UPSHIFT STABILIZE", curGear, range, curGear, range, rpm, load, loadSource)\n                    self.autoGearChangeTimer = math.max(self.autoGearChangeTime or 0, 250)\n                    return curGear\n                elseif now - self.c330FixTopGearLowLoadSince < TOP_GEAR_HEAVY_SET_STABLE_MS then\n                    logDecision(self, "BLOCK TOP UPSHIFT STABILIZE", curGear, range, curGear, range, rpm, load, loadSource)\n                    self.autoGearChangeTimer = math.max(self.autoGearChangeTime or 0, 250)\n                    return curGear\n                end\n            else\n                self.c330FixTopGearLowLoadSince = nil\n\n                -- Preserve the 0.0.1.6 light-set high-load safeguard.\n                if load >= TOP_GEAR_HIGH_LOAD and rpm < TOP_GEAR_HIGH_LOAD_MIN_RPM then\n                    logDecision(self, "BLOCK TOP UPSHIFT HIGH LOAD", curGear, range, curGear, range, rpm, load, loadSource)\n                    self.autoGearChangeTimer = math.max(self.autoGearChangeTime or 0, 250)\n                    return curGear\n                end\n            end\n\n            if load >= TOP_GEAR_PREDICTION_GUARD_MIN_LOAD then\n                local predictedRpm = rpm * TOP_GEAR_POSTSHIFT_RPM_RATIO\n                if predictedRpm < TOP_GEAR_POSTSHIFT_MIN_RPM then\n                    logDecision(self, "BLOCK TOP UPSHIFT", curGear, range, curGear, range, rpm, load, loadSource)\n                    self.autoGearChangeTimer = math.max(self.autoGearChangeTime or 0, 250)\n                    return curGear\n                end\n            end\n        else\n            self.c330FixTopGearLowLoadSince = nil\n        end\n'''
if old_guard not in s:
    raise SystemExit('Expected 0.0.1.6 top-gear guard block not found')
s = s.replace(old_guard, new_guard, 1)

s = s.replace(
    'Logging.info("[C330TRANS] 0.0.1.6 C-330 6F/2R controller installed (refined high-load top-gear guard, mass-aware start, ADS-safe)")',
    'Logging.info("[C330TRANS] 0.0.1.7 C-330 6F/2R controller installed (heavy-set top-gear stability guard, mass-aware start, ADS-safe)")',
    1
)

p.write_text(s, encoding='utf-8')

# Version
p = Path('modDesc.xml')
s = p.read_text(encoding='utf-8')
if '<version>0.0.1.6</version>' not in s:
    raise SystemExit('Expected modDesc 0.0.1.6')
s = s.replace('<version>0.0.1.6</version>', '<version>0.0.1.7</version>', 1)
p.write_text(s, encoding='utf-8')
ET.parse(p)

# README
p = Path('README.md')
s = p.read_text(encoding='utf-8')
old_line = '**0.0.1.6 – C-330 refined high-load II/3 guard prerelease**'
if old_line not in s:
    raise SystemExit('Expected README 0.0.1.6 line')
s = s.replace(old_line, '**0.0.1.7 – C-330 heavy-set II/3 stability guard prerelease**', 1)
p.write_text(s, encoding='utf-8')

# CHANGELOG
p = Path('CHANGELOG.md')
s = p.read_text(encoding='utf-8')
if not s.startswith('# Changelog\n\n'):
    raise SystemExit('Unexpected changelog header')
entry = '''# Changelog\n\n## 0.0.1.7 - C-330 heavy-set II/3 stability guard\n\nIsolated follow-up to the 0.0.1.6 trailer/no-trailer runtime test. **Only II/3 admission for heavy sets is refined.**\n\n### Runtime evidence from 0.0.1.6\n- The 0.70 threshold started working: `BLOCK TOP UPSHIFT HIGH LOAD` appeared twice with the 3.469 t trailer set.\n- No-trailer behavior remained clean at 1.683 t.\n- Two loaded shifts still slipped through after short ADS dips below 0.70: the low-load window before the decision was only about 0.15 s and 0.27 s, and post-shift load climbed back to roughly 0.77-0.88.\n- Two more acceptable loaded cases had load below 0.70 for about 0.75-0.82 s before II/3 and recovered without the same severe bog.\n- All 13 range changes were `source=C330TRANS`; no `SHIFT_OSCILLATION` or Lua error occurred.\n\n### Change\n- For total mass **>= 3.175 t**, II/2 -> II/3 now requires filtered load **< 0.70 continuously for 600 ms**.\n- If load returns to >=0.70, the 600 ms timer resets.\n- Light sets below 3.175 t keep the 0.0.1.6 behavior.\n- The existing predicted post-shift RPM guard remains active after stabilization.\n\n### Explicitly unchanged\n- Mass-aware start rule and 3.175 t threshold.\n- Forward I/3 <-> II/1 and reverse range logic.\n- 100 Nm S-312C engine curve, factory gearbox ratios, fuel use and chassis physics.\n- C-330M remains excluded.\n- ADS remains optional, filtered and strictly read-only.\n\n'''
s = entry + s[len('# Changelog\n\n'):]
p.write_text(s, encoding='utf-8')

Path('.release/release.json').write_text(json.dumps({
    'version': '0.0.1.7',
    'tag': '0.0.1.7',
    'title': '0.0.1.7 - C-330 heavy-set II/3 stability guard test',
    'prerelease': True,
    'zipName': 'FS25_UrsusC330_330M_4x2.zip'
}, indent=2) + '\n', encoding='utf-8')

Path('.release/notes.md').write_text('''## Ursus C-330 / C-330M 0.0.1.7\n\nHeavy-set II/3 stability test.\n\n### Changed\n- for tractor+equipment total mass **>= 3.175 t**, II/2 -> II/3 requires filtered load **< 0.70 continuously for 600 ms**,\n- any return to load >=0.70 resets that timer,\n- light sets below 3.175 t retain the previous behavior.\n\n### Why\n0.0.1.6 correctly started blocking high-load top-gear requests, but two trailer shifts still passed after very short ADS dips below 0.70 (~0.15 s and ~0.27 s). After the shifts the load rose back to roughly 0.77-0.88. Acceptable trailer cases showed a much longer low-load recovery (~0.75-0.82 s), so 600 ms separates the two groups without slowing the unloaded tractor.\n\n### Unchanged\nMass-aware starting, range-boundary logic, reverse controller, 100 Nm S-312C curve, gearbox ratios, fuel use, ADS read-only handling, C-330M and chassis physics are unchanged.\n\n### Test focus\nRepeat one pass without a trailer and one with the same trailer. With the trailer, expect `BLOCK TOP UPSHIFT HEAVY SET` and/or `BLOCK TOP UPSHIFT STABILIZE` until load has stayed below 0.70 for 600 ms. Check that II/3 no longer lands near 1100-1250 rpm under ~0.85-0.90 load. Send the complete `log.txt`.\n''', encoding='utf-8')

# Sanity checks
ET.parse('modDesc.xml')
code = Path('Scripts/C330TransmissionFix.lua').read_text(encoding='utf-8')
assert 'TOP_GEAR_HIGH_LOAD = 0.70' in code
assert 'TOP_GEAR_HEAVY_SET_STABLE_MS = 600' in code
assert 'c330FixTopGearLowLoadSince' in code
assert 'BLOCK TOP UPSHIFT HEAVY SET' in code
assert 'BLOCK TOP UPSHIFT STABILIZE' in code
assert 'totalMass >= LIGHT_START_MAX_TOTAL_MASS_T' in code
assert 'FORWARD_RANGE_DOWNSHIFT_MAX_SPEED = 6.0' in code
assert '0.0.1.7 C-330 6F/2R controller installed' in code
assert '<version>0.0.1.7</version>' in Path('modDesc.xml').read_text(encoding='utf-8')
vehicle = Path('c330m.xml').read_text(encoding='utf-8')
c0 = vehicle.find('<motorConfiguration name="C-330" hp="30" price="0">')
c1 = vehicle.find('</motorConfiguration>', c0)
cblock = vehicle[c0:c1]
assert 'torqueScale="0.100"' in cblock
assert 'normRpm="0.727273" torque="1.00"' in cblock
assert 'normRpm="0.818182" torque="1.00"' in cblock
assert 'normRpm="1.00" torque="0.972364"' in cblock
print('0.0.1.7 heavy-set top-gear stability guard validated')
