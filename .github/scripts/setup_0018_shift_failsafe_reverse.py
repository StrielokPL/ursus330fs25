from pathlib import Path
import json
import xml.etree.ElementTree as ET

# 0.0.1.8: transmission finalization test.
# - 2 s minimum settled-gear dwell before every automatic upshift
# - heavy-set II/3 recovery window extended from 600 ms to 2000 ms
# - light reverse start directly in R-II using the same 3.175 t threshold as forward I/3
# ADS remains strictly read-only.

p = Path('Scripts/C330TransmissionFix.lua')
s = p.read_text(encoding='utf-8')

s = s.replace(
    '-- 0.0.1.7 TEST: heavy-set top-gear stability guard with mass-aware 6F/2R control; ADS-safe.',
    '-- 0.0.1.8 TEST: 2 s upshift failsafe, heavy-set top-gear recovery and mass-aware reverse start; ADS-safe.',
    1
)

old = '''    local RANGE_UPSHIFT_RPM = 2050\n    local RANGE_UPSHIFT_MAX_LOAD = 0.55\n    local RANGE_UPSHIFT_STABLE_MS = 800\n\n    local NORMAL_UPSHIFT_GUARD_LOAD = 0.80\n'''
new = '''    local RANGE_UPSHIFT_RPM = 2050\n    local RANGE_UPSHIFT_MAX_LOAD = 0.55\n    local RANGE_UPSHIFT_STABLE_MS = 800\n\n    -- Final safety net requested after the 0.0.1.7 runtime test. Once a mechanical\n    -- gear/range has settled, no automatic request for a numerically/historically\n    -- higher ratio may be issued for the first 2 seconds. Downshifts remain free.\n    local UPSHIFT_MIN_DWELL_MS = 2000\n\n    local NORMAL_UPSHIFT_GUARD_LOAD = 0.80\n'''
if old not in s:
    raise SystemExit('Expected upshift constants block not found')
s = s.replace(old, new, 1)

old = '''    -- 0.0.1.6 proved that the instantaneous load threshold itself is not enough:\n    -- on a heavy set ADS can fall below 0.70 for a fraction of a second just before\n    -- GIANTS requests II/3, then rise back above ~0.85 after the shift. Runtime\n    -- evidence separated bad transient windows (~0.15-0.27 s) from acceptable\n    -- recovery windows (~0.75-0.82 s). For a set at or above the same 3.175 t\n    -- threshold used by mass-aware starting, require 600 ms of continuous load\n    -- below 0.70 before top gear is allowed. Light sets keep the current behavior.\n    local TOP_GEAR_HIGH_LOAD = 0.70\n    local TOP_GEAR_HIGH_LOAD_MIN_RPM = 2100\n    local TOP_GEAR_HEAVY_SET_STABLE_MS = 600\n'''
new = '''    -- 0.0.1.7 proved that 600 ms is still too short for the large II/2 -> II/3\n    -- step on a 3.469 t set. The guard correctly blocked the first requests, but\n    -- II/3 could still settle near 1180-1225 rpm with ~0.78-0.85 load. Require\n    -- 2 seconds of continuous load below 0.70 before a heavy set may use II/3.\n    -- This is independent of, and may overlap with, the generic 2 s gear dwell.\n    local TOP_GEAR_HIGH_LOAD = 0.70\n    local TOP_GEAR_HIGH_LOAD_MIN_RPM = 2100\n    local TOP_GEAR_HEAVY_SET_STABLE_MS = 2000\n'''
if old not in s:
    raise SystemExit('Expected 0.0.1.7 top-gear stability block not found')
s = s.replace(old, new, 1)

old = '''    local function getForwardStartGear(motor, gears, fallbackGear)\n        local maxGear = math.min(#gears, 3)\n        local gear = math.max(1, math.min(fallbackGear or 1, maxGear))\n        local totalMass = getTotalMassTons(motor)\n\n        if maxGear >= 3\n            and totalMass ~= nil\n            and totalMass < LIGHT_START_MAX_TOTAL_MASS_T then\n            return 3, totalMass, "LIGHT_I3"\n        end\n\n        return gear, totalMass, "NATIVE_LOW_RANGE"\n    end\n\n    local function logForwardStartGear(motor, gear, totalMass, mode)\n'''
new = '''    local function getForwardStartGear(motor, gears, fallbackGear)\n        local maxGear = math.min(#gears, 3)\n        local gear = math.max(1, math.min(fallbackGear or 1, maxGear))\n        local totalMass = getTotalMassTons(motor)\n\n        if maxGear >= 3\n            and totalMass ~= nil\n            and totalMass < LIGHT_START_MAX_TOTAL_MASS_T then\n            return 3, totalMass, "LIGHT_I3"\n        end\n\n        return gear, totalMass, "NATIVE_LOW_RANGE"\n    end\n\n    local function getReverseStartRange(motor)\n        local totalMass = getTotalMassTons(motor)\n\n        if totalMass ~= nil and totalMass < LIGHT_START_MAX_TOTAL_MASS_T then\n            return HIGH_RANGE, totalMass, "LIGHT_RII"\n        end\n\n        return LOW_RANGE, totalMass, "NATIVE_RI"\n    end\n\n    local function logForwardStartGear(motor, gear, totalMass, mode)\n'''
if old not in s:
    raise SystemExit('Expected forward start helper block not found')
s = s.replace(old, new, 1)

old = '''    local function getLoad(motor)\n'''
new = '''    local function logReverseStartRange(motor, range, totalMass, mode)\n        local now = g_time or 0\n        if motor.c330FixReverseStartLogUntil ~= nil and now < motor.c330FixReverseStartLogUntil then\n            return\n        end\n        motor.c330FixReverseStartLogUntil = now + 500\n\n        Logging.info(\n            "[C330TRANS] START REVERSE R-%s totalMass=%s threshold=%.3f mode=%s",\n            range == HIGH_RANGE and "II" or "I",\n            totalMass ~= nil and string.format("%.3f", totalMass) or "n/a",\n            LIGHT_START_MAX_TOTAL_MASS_T,\n            tostring(mode)\n        )\n    end\n\n    local function getLoad(motor)\n'''
if old not in s:
    raise SystemExit('Expected getLoad marker not found')
s = s.replace(old, new, 1)

old = '''    local function logDecision(motor, action, fromGear, fromRange, toGear, toRange, rpm, load, loadSource)\n'''
new = '''    local function getUpshiftDwellState(motor, range, gear, now)\n        local direction = (motor.currentDirection or 1) < 0 and -1 or 1\n        local key = string.format("%d:%d:%d", direction, range or 0, gear or 0)\n\n        if motor.c330FixSettledGearKey ~= key then\n            motor.c330FixSettledGearKey = key\n            motor.c330FixSettledGearSince = now\n            return false, 0\n        end\n\n        local age = now - (motor.c330FixSettledGearSince or now)\n        return age >= UPSHIFT_MIN_DWELL_MS, age\n    end\n\n    local function logDecision(motor, action, fromGear, fromRange, toGear, toRange, rpm, load, loadSource)\n'''
if old not in s:
    raise SystemExit('Expected logDecision marker not found')
s = s.replace(old, new, 1)

old = '''    function VehicleMotor:getBestStartGear(gears)\n        local gear, group = originalGetBestStartGear(self, gears)\n\n        if isAutomaticC330(self) then\n            group = LOW_RANGE\n            gear = math.max(1, math.min(gear or 1, math.min(#gears, 3)))\n\n            -- Forward only: a light set starts directly in I/3. Reverse still has\n            -- its single mechanical reverse gear and is intentionally unaffected.\n            if isAutomaticForward(self) and #gears >= 3 then\n                local totalMass, startMode\n                gear, totalMass, startMode = getForwardStartGear(self, gears, gear)\n                logForwardStartGear(self, gear, totalMass, startMode)\n            end\n\n            -- A real C-330 starts/restarts from range I. Mark this request so the\n            -- diagnostic kit does not misattribute the reset to GIANTS.\n            if self.activeGearGroupIndex ~= LOW_RANGE then\n                local now = g_time or 0\n                self.c330FixRequestedRange = LOW_RANGE\n                self.c330FixRequestedGear = gear\n                self.c330FixRequestedRangeAt = now\n                self.c330FixRequestedRangeReason = "START RANGE RESET"\n                self:setGearGroup(LOW_RANGE)\n            end\n\n            self.c330FixRangeRecoverySince = nil\n        end\n\n        return gear, group\n    end\n'''
new = '''    function VehicleMotor:getBestStartGear(gears)\n        local gear, group = originalGetBestStartGear(self, gears)\n\n        if isAutomaticC330(self) then\n            local startRange = LOW_RANGE\n            gear = math.max(1, math.min(gear or 1, math.min(#gears, 3)))\n\n            -- Forward: light set starts directly in I/3. Reverse now mirrors the\n            -- same mass rule: below 3.175 t start directly in R-II, while a heavy\n            -- set starts in R-I and may later recover to R-II normally.\n            if isAutomaticForward(self) and #gears >= 3 then\n                local totalMass, startMode\n                gear, totalMass, startMode = getForwardStartGear(self, gears, gear)\n                logForwardStartGear(self, gear, totalMass, startMode)\n            elseif isAutomaticReverse(self) then\n                local totalMass, startMode\n                gear = 1\n                startRange, totalMass, startMode = getReverseStartRange(self)\n                logReverseStartRange(self, startRange, totalMass, startMode)\n            end\n\n            group = startRange\n\n            -- Mark every controller-forced start range so TractorDebugKit can\n            -- distinguish it from GIANTS group selection.\n            if self.activeGearGroupIndex ~= startRange then\n                local now = g_time or 0\n                self.c330FixRequestedRange = startRange\n                self.c330FixRequestedGear = gear\n                self.c330FixRequestedRangeAt = now\n                if isAutomaticReverse(self) then\n                    self.c330FixRequestedRangeReason = startRange == HIGH_RANGE\n                        and "START REVERSE R-II" or "START REVERSE R-I"\n                else\n                    self.c330FixRequestedRangeReason = "START RANGE RESET"\n                end\n                self:setGearGroup(startRange)\n            end\n\n            self.c330FixRangeRecoverySince = nil\n        end\n\n        return gear, group\n    end\n'''
if old not in s:
    raise SystemExit('Expected getBestStartGear block not found')
s = s.replace(old, new, 1)

old = '''        local totalMass = getTotalMassTons(self)\n        local accel = math.abs(tonumber(acceleratorPedal) or 0)\n        local maxGear = math.min(#gears, 3)\n\n        -- 0.0.1.2 showed that a near-stop can occasionally continue in range II\n'''
new = '''        local totalMass = getTotalMassTons(self)\n        local accel = math.abs(tonumber(acceleratorPedal) or 0)\n        local maxGear = math.min(#gears, 3)\n        local upshiftDwellReady, upshiftDwellAge = getUpshiftDwellState(self, range, curGear, now)\n\n        -- 0.0.1.2 showed that a near-stop can occasionally continue in range II\n'''
if old not in s:
    raise SystemExit('Expected local runtime state block not found')
s = s.replace(old, new, 1)

old = '''            local reverseRecoveryReady = range == LOW_RANGE\n                and curGear == 1\n                and rpm >= RANGE_UPSHIFT_RPM\n                and (load == nil or load <= RANGE_UPSHIFT_MAX_LOAD)\n                and (self.c330FixUpshiftHoldUntil == nil or now >= self.c330FixUpshiftHoldUntil)\n\n            if reverseRecoveryReady then\n'''
new = '''            local reverseRecoveryBaseReady = range == LOW_RANGE\n                and curGear == 1\n                and rpm >= RANGE_UPSHIFT_RPM\n                and (load == nil or load <= RANGE_UPSHIFT_MAX_LOAD)\n                and (self.c330FixUpshiftHoldUntil == nil or now >= self.c330FixUpshiftHoldUntil)\n\n            if reverseRecoveryBaseReady and not upshiftDwellReady then\n                logDecision(self, "BLOCK REVERSE UPSHIFT DWELL", curGear, range, curGear, range, rpm, load, loadSource)\n            end\n\n            local reverseRecoveryReady = reverseRecoveryBaseReady and upshiftDwellReady\n\n            if reverseRecoveryReady then\n'''
if old not in s:
    raise SystemExit('Expected reverse recovery block not found')
s = s.replace(old, new, 1)

old = '''        local rangeRecoveryReady = range == LOW_RANGE\n            and curGear == maxGear\n            and rpm >= RANGE_UPSHIFT_RPM\n            and (load == nil or load <= RANGE_UPSHIFT_MAX_LOAD)\n            and (self.c330FixUpshiftHoldUntil == nil or now >= self.c330FixUpshiftHoldUntil)\n\n        if rangeRecoveryReady then\n'''
new = '''        local rangeRecoveryBaseReady = range == LOW_RANGE\n            and curGear == maxGear\n            and rpm >= RANGE_UPSHIFT_RPM\n            and (load == nil or load <= RANGE_UPSHIFT_MAX_LOAD)\n            and (self.c330FixUpshiftHoldUntil == nil or now >= self.c330FixUpshiftHoldUntil)\n\n        if rangeRecoveryBaseReady and not upshiftDwellReady then\n            logDecision(self, "BLOCK RANGE UPSHIFT DWELL", curGear, range, curGear, range, rpm, load, loadSource)\n        end\n\n        local rangeRecoveryReady = rangeRecoveryBaseReady and upshiftDwellReady\n\n        if rangeRecoveryReady then\n'''
if old not in s:
    raise SystemExit('Expected forward range recovery block not found')
s = s.replace(old, new, 1)

old = '''        -- Do not allow a normal upshift when the engine is already heavily loaded\n        -- below the useful upper-RPM band. ADS is preferred when present; native\n        -- GIANTS smooth load is used otherwise.\n        if targetGear > curGear\n            and load ~= nil\n'''
new = '''        -- Generic 2-second failsafe. The top-gear load timer above may run in\n        -- parallel, but no within-range automatic upshift can actually be issued\n        -- until the current settled gear has existed for at least 2 seconds.\n        if targetGear > curGear and not upshiftDwellReady then\n            logDecision(self, "BLOCK UPSHIFT DWELL", curGear, range, curGear, range, rpm, load, loadSource)\n            self.autoGearChangeTimer = math.max(self.autoGearChangeTime or 0, 250)\n            return curGear\n        end\n\n        -- Do not allow a normal upshift when the engine is already heavily loaded\n        -- below the useful upper-RPM band. ADS is preferred when present; native\n        -- GIANTS smooth load is used otherwise.\n        if targetGear > curGear\n            and load ~= nil\n'''
if old not in s:
    raise SystemExit('Expected normal upshift guard marker not found')
s = s.replace(old, new, 1)

s = s.replace(
    'Logging.info("[C330TRANS] 0.0.1.7 C-330 6F/2R controller installed (heavy-set top-gear stability guard, mass-aware start, ADS-safe)")',
    'Logging.info("[C330TRANS] 0.0.1.8 C-330 6F/2R controller installed (2s upshift failsafe, mass-aware reverse start, ADS-safe)")',
    1
)

p.write_text(s, encoding='utf-8')

# Version
p = Path('modDesc.xml')
s = p.read_text(encoding='utf-8')
if '<version>0.0.1.7</version>' not in s:
    raise SystemExit('Expected modDesc 0.0.1.7')
s = s.replace('<version>0.0.1.7</version>', '<version>0.0.1.8</version>', 1)
p.write_text(s, encoding='utf-8')
ET.parse(p)

# README
p = Path('README.md')
s = p.read_text(encoding='utf-8')
old_line = '**0.0.1.7 – C-330 heavy-set II/3 stability guard prerelease**'
if old_line not in s:
    raise SystemExit('Expected README 0.0.1.7 line')
s = s.replace(old_line, '**0.0.1.8 – C-330 2 s upshift failsafe + mass-aware R-II start prerelease**', 1)
p.write_text(s, encoding='utf-8')

# CHANGELOG
p = Path('CHANGELOG.md')
s = p.read_text(encoding='utf-8')
if not s.startswith('# Changelog\n\n'):
    raise SystemExit('Unexpected changelog header')
entry = '''# Changelog\n\n## 0.0.1.8 - 2 s upshift failsafe and mass-aware R-II start\n\nTransmission follow-up based on the complete 0.0.1.7 runtime log.\n\n### 0.0.1.7 result\n- Controller remained stable: no `SHIFT_OSCILLATION` and no Lua errors.\n- All observed range changes were attributed to `C330TRANS`.\n- The 3.469 t heavy-set II/3 guard worked, but 600 ms was not enough: one top-gear shift still settled near 1180 rpm / 0.846 ADS load and another near 1225 rpm / 0.783. Both recovered without hunting, but the diagnostic target was not fully met.\n\n### Changes\n- Every automatic upshift now has a hard **2000 ms minimum settled-gear dwell**. Downshifts are not delayed.\n- Heavy sets (>=3.175 t) now require **2000 ms continuous load <0.70** before II/2 -> II/3, replacing the 600 ms window.\n- Reverse starting now mirrors forward mass-aware starting: **<3.175 t starts directly in R-II**, while **>=3.175 t starts in R-I**.\n- Added diagnostic breadcrumbs: `BLOCK UPSHIFT DWELL`, `BLOCK RANGE UPSHIFT DWELL`, `BLOCK REVERSE UPSHIFT DWELL`, and `START REVERSE R-II/R-I`.\n\n### Explicitly unchanged\n- Factory 6F/2R ratios and speed ladder.\n- Forward I/3 <-> II/1 downshift/load thresholds except for the new generic minimum dwell on upshifts.\n- 100 Nm S-312C engine curve, fuel use, mass/COM, tyres and chassis physics.\n- ADS remains optional, filtered and strictly read-only.\n- C-330M remains excluded.\n\n'''
s = entry + s[len('# Changelog\n\n'):]
p.write_text(s, encoding='utf-8')

Path('.release/release.json').write_text(json.dumps({
    'version': '0.0.1.8',
    'tag': '0.0.1.8',
    'title': '0.0.1.8 - C-330 2 s upshift failsafe and R-II start test',
    'prerelease': True,
    'zipName': 'FS25_UrsusC330_330M_4x2.zip'
}, indent=2) + '\n', encoding='utf-8')

Path('.release/notes.md').write_text('''## Ursus C-330 / C-330M 0.0.1.8\n\nTransmission finalization test based on the complete 0.0.1.7 log.\n\n### Changed\n- automatic upshifts cannot occur earlier than **2.0 s after the current mechanical gear/range settles**,\n- heavy sets (>=3.175 t) require **2.0 s continuous load <0.70** before II/3,\n- light sets (<3.175 t) now start reverse directly in **R-II**, matching the forward light-start mass rule,\n- heavy sets (>=3.175 t) still start reverse in **R-I**.\n\n### Why\n0.0.1.7 was free of shift oscillation and Lua errors, but the 600 ms heavy-set top-gear window still allowed one II/3 engagement to settle near 1180 rpm / 0.846 ADS load and another near 1225 rpm / 0.783. Both recovered, so the remaining change is a conservative timing safeguard rather than a ratio or torque retune.\n\n### Unchanged\nFactory ratios, 100 Nm S-312C curve, forward/downshift thresholds, fuel, chassis physics, ADS read-only protection and C-330M are unchanged.\n\n### Test focus\nTest four starts if practical: forward light, forward >=3.175 t, reverse light, reverse >=3.175 t. Confirm light reverse logs `START REVERSE R-II`, heavy reverse logs `START REVERSE R-I`, and automatic upshifts show at least 2 s settled-gear dwell. With the heavy trailer, verify II/3 only follows 2 s continuous load below 0.70 and does not create hunting. Send the complete `log.txt`.\n''', encoding='utf-8')

# Sanity checks
ET.parse('modDesc.xml')
code = Path('Scripts/C330TransmissionFix.lua').read_text(encoding='utf-8')
assert 'UPSHIFT_MIN_DWELL_MS = 2000' in code
assert 'TOP_GEAR_HEAVY_SET_STABLE_MS = 2000' in code
assert 'getReverseStartRange' in code
assert 'LIGHT_RII' in code
assert 'START REVERSE R-II' in code
assert 'BLOCK UPSHIFT DWELL' in code
assert 'BLOCK RANGE UPSHIFT DWELL' in code
assert 'BLOCK REVERSE UPSHIFT DWELL' in code
assert '0.0.1.8 C-330 6F/2R controller installed' in code
assert '<version>0.0.1.8</version>' in Path('modDesc.xml').read_text(encoding='utf-8')
vehicle = Path('c330m.xml').read_text(encoding='utf-8')
c0 = vehicle.find('<motorConfiguration name="C-330" hp="30" price="0">')
c1 = vehicle.find('</motorConfiguration>', c0)
cblock = vehicle[c0:c1]
assert 'torqueScale="0.100"' in cblock
assert 'normRpm="0.727273" torque="1.00"' in cblock
assert 'normRpm="0.818182" torque="1.00"' in cblock
assert 'normRpm="1.00" torque="0.972364"' in cblock
print('0.0.1.8 shift failsafe and reverse start validated')
