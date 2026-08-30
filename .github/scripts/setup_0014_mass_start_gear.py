from pathlib import Path
import json
import xml.etree.ElementTree as ET

# 0.0.1.4: isolated mass-aware forward start gear test.
# Preserve 0.0.1.3 range-boundary safety, 0.0.1.2 top-gear guard, engine and ADS contract.

p = Path('Scripts/C330TransmissionFix.lua')
s = p.read_text(encoding='utf-8')

s = s.replace(
    '-- 0.0.1.3 TEST: 6F/2R range-boundary safety with 100 Nm engine; ADS-safe.',
    '-- 0.0.1.4 TEST: mass-aware forward start gear with 6F/2R range safety; ADS-safe.',
    1
)

anchor = '''    local FORWARD_LOW_SPEED_RANGE_RESET = 0.5\n\n    local RANGE_UPSHIFT_RPM = 2050\n'''
replacement = '''    local FORWARD_LOW_SPEED_RANGE_RESET = 0.5\n\n    -- Mass-aware automatic start requested after the 0.0.1.3 test. The real C-330\n    -- base mass is 1675 kg. A complete tractor+implement/trailer set below\n    -- 1675 + 1500 = 3175 kg may start directly in I/3, avoiding two unnecessary\n    -- low-range shifts when essentially unloaded. At or above the threshold,\n    -- keep GIANTS' native start-gear choice, but always in range I.\n    local FACTORY_BASE_MASS_T = 1.675\n    local LIGHT_START_EXTRA_MASS_T = 1.500\n    local LIGHT_START_MAX_TOTAL_MASS_T = FACTORY_BASE_MASS_T + LIGHT_START_EXTRA_MASS_T\n\n    local RANGE_UPSHIFT_RPM = 2050\n'''
if anchor not in s:
    raise SystemExit('mass constants anchor not found')
s = s.replace(anchor, replacement, 1)

anchor = '''    local function getSpeed(motor)\n        local vehicle = motor ~= nil and motor.vehicle or nil\n        if vehicle ~= nil and vehicle.getLastSpeed ~= nil then\n            return tonumber(vehicle:getLastSpeed()) or 0\n        end\n        return 0\n    end\n\n    local function getLoad(motor)\n'''
replacement = '''    local function getSpeed(motor)\n        local vehicle = motor ~= nil and motor.vehicle or nil\n        if vehicle ~= nil and vehicle.getLastSpeed ~= nil then\n            return tonumber(vehicle:getLastSpeed()) or 0\n        end\n        return 0\n    end\n\n    local function getTotalMassTons(motor)\n        local vehicle = motor ~= nil and motor.vehicle or nil\n        if vehicle ~= nil and vehicle.getTotalMass ~= nil then\n            local value = tonumber(vehicle:getTotalMass())\n            if value ~= nil and value > 0 then\n                return value\n            end\n        end\n        return nil\n    end\n\n    local function getForwardStartGear(motor, gears, fallbackGear)\n        local maxGear = math.min(#gears, 3)\n        local gear = math.max(1, math.min(fallbackGear or 1, maxGear))\n        local totalMass = getTotalMassTons(motor)\n\n        if maxGear >= 3\n            and totalMass ~= nil\n            and totalMass < LIGHT_START_MAX_TOTAL_MASS_T then\n            return 3, totalMass, "LIGHT_I3"\n        end\n\n        return gear, totalMass, "NATIVE_LOW_RANGE"\n    end\n\n    local function logForwardStartGear(motor, gear, totalMass, mode)\n        local now = g_time or 0\n        if motor.c330FixStartGearLogUntil ~= nil and now < motor.c330FixStartGearLogUntil then\n            return\n        end\n        motor.c330FixStartGearLogUntil = now + 500\n\n        Logging.info(\n            "[C330TRANS] START GEAR I/%d totalMass=%s threshold=%.3f mode=%s",\n            gear or 0,\n            totalMass ~= nil and string.format("%.3f", totalMass) or "n/a",\n            LIGHT_START_MAX_TOTAL_MASS_T,\n            tostring(mode)\n        )\n    end\n\n    local function getLoad(motor)\n'''
if anchor not in s:
    raise SystemExit('mass helper anchor not found')
s = s.replace(anchor, replacement, 1)

anchor = '''        if isAutomaticC330(self) then\n            group = LOW_RANGE\n            gear = math.max(1, math.min(gear or 1, math.min(#gears, 3)))\n\n            -- A real C-330 starts/restarts from range I. Mark this request so the\n'''
replacement = '''        if isAutomaticC330(self) then\n            group = LOW_RANGE\n            gear = math.max(1, math.min(gear or 1, math.min(#gears, 3)))\n\n            -- Forward only: a light set starts directly in I/3. Reverse still has\n            -- its single mechanical reverse gear and is intentionally unaffected.\n            if isAutomaticForward(self) and #gears >= 3 then\n                local totalMass, startMode\n                gear, totalMass, startMode = getForwardStartGear(self, gears, gear)\n                logForwardStartGear(self, gear, totalMass, startMode)\n            end\n\n            -- A real C-330 starts/restarts from range I. Mark this request so the\n'''
if anchor not in s:
    raise SystemExit('getBestStartGear anchor not found')
s = s.replace(anchor, replacement, 1)

anchor = '''        if isAutomaticForward(self)\n            and range == HIGH_RANGE\n            and speed <= FORWARD_LOW_SPEED_RANGE_RESET then\n            return setAutomaticRange(\n                self, LOW_RANGE, 1, "LOW SPEED RANGE RESET",\n                rpm, load, loadSource, false\n            )\n        end\n'''
replacement = '''        if isAutomaticForward(self)\n            and range == HIGH_RANGE\n            and speed <= FORWARD_LOW_SPEED_RANGE_RESET then\n            local resetGear, totalMass, startMode = getForwardStartGear(self, gears, 1)\n            logForwardStartGear(self, resetGear, totalMass, startMode)\n            return setAutomaticRange(\n                self, LOW_RANGE, resetGear, "LOW SPEED RANGE RESET",\n                rpm, load, loadSource, false\n            )\n        end\n'''
if anchor not in s:
    raise SystemExit('low-speed reset anchor not found')
s = s.replace(anchor, replacement, 1)

s = s.replace(
    'Logging.info("[C330TRANS] 0.0.1.3 C-330 6F/2R controller installed (range-boundary safety, ADS-safe)")',
    'Logging.info("[C330TRANS] 0.0.1.4 C-330 6F/2R controller installed (mass-aware start gear, range safety, ADS-safe)")',
    1
)

p.write_text(s, encoding='utf-8')

# Version
p = Path('modDesc.xml')
s = p.read_text(encoding='utf-8')
if '<version>0.0.1.3</version>' not in s:
    raise SystemExit('Expected modDesc 0.0.1.3')
s = s.replace('<version>0.0.1.3</version>', '<version>0.0.1.4</version>', 1)
p.write_text(s, encoding='utf-8')
ET.parse(p)

# README
p = Path('README.md')
s = p.read_text(encoding='utf-8')
if '**0.0.1.3 – C-330 range-boundary safety prerelease**' not in s:
    raise SystemExit('Expected README 0.0.1.3 line')
s = s.replace(
    '**0.0.1.3 – C-330 range-boundary safety prerelease**',
    '**0.0.1.4 – C-330 mass-aware I/3 start prerelease**',
    1
)
p.write_text(s, encoding='utf-8')

# CHANGELOG
p = Path('CHANGELOG.md')
s = p.read_text(encoding='utf-8')
if not s.startswith('# Changelog\n\n'):
    raise SystemExit('Unexpected changelog header')
entry = '''# Changelog\n\n## 0.0.1.4 - C-330 mass-aware I/3 start\n\nIsolated automatic start-gear test based on the clean 0.0.1.3 range-boundary result. **Range logic, engine calibration and ADS handling are unchanged.**\n\n### Runtime evidence from 0.0.1.3\n- No II/1 -> I/3 range-down occurred above the 6.0 km/h safety ceiling; observed range-down requests were about 1.20, 1.43, 3.21 and 4.11 km/h.\n- Near-stop range-I restoration worked through the existing `START RANGE RESET`; the extra `LOW SPEED RANGE RESET` remains a fallback safety path.\n- All observed range changes were attributed to `C330TRANS`, with no `SHIFT_OSCILLATION` and no Lua errors.\n- A light forward start still walked I/1 -> I/2 -> I/3, costing roughly two unnecessary low-range shifts before reaching I/3.\n\n### Change\n- Factory base mass reference: **1.675 t**.\n- Light-start threshold: **3.175 t total set mass** (= 1.675 t + 1.500 t).\n- In automatic forward, if `vehicle:getTotalMass()` is strictly below 3.175 t, the start/restart gear is forced to **I/3**.\n- At 3.175 t or above, or if total mass cannot be read, GIANTS' native start-gear choice is retained and clamped to range I as before.\n- The <=0.5 km/h emergency range-I reset uses the same mass-aware start-gear choice.\n- Added `[C330TRANS] START GEAR` diagnostic with total mass, threshold and selection mode.\n\n### Explicitly unchanged\n- 0.0.1.3 forward II/1 -> I/3 6.0 km/h ceiling and low-speed range reset.\n- 0.0.1.2 II/2 -> II/3 predicted-RPM guard.\n- S-312C 100 Nm torque curve, gearbox ratios, reverse logic, fuel use and chassis physics.\n- C-330M remains excluded.\n- ADS remains optional, filtered and read-only; no ADS state is written.\n\n'''
s = entry + s[len('# Changelog\n\n'):]
p.write_text(s, encoding='utf-8')

Path('.release/release.json').write_text(json.dumps({
    'version': '0.0.1.4',
    'tag': '0.0.1.4',
    'title': '0.0.1.4 - C-330 mass-aware I/3 start test',
    'prerelease': True,
    'zipName': 'FS25_UrsusC330_330M_4x2.zip'
}, indent=2) + '\n', encoding='utf-8')

Path('.release/notes.md').write_text('''## Ursus C-330 / C-330M 0.0.1.4\n\nIsolated mass-aware automatic start-gear test.\n\n### Changed\n- automatic forward starts directly in **I/3** when total tractor+attached-equipment mass is below **3.175 t**,\n- at 3.175 t or more, the previous native low-range start-gear choice remains,\n- the emergency near-stop range-I reset follows the same mass rule,\n- `[C330TRANS] START GEAR` now reports the measured total mass and selected mode.\n\n### Unchanged\n0.0.1.3 range-boundary safety, the 0.0.1.2 top-gear guard, the 100 Nm S-312C curve, gearbox ratios, reverse logic, fuel use, ADS read-only handling, C-330M and chassis physics are unchanged.\n\n### Test focus\nTest at least: (1) bare/light C-330 below 3.175 t, which should log `START GEAR I/3 ... mode=LIGHT_I3`; (2) a set clearly above 3.175 t, which should log `mode=NATIVE_LOW_RANGE` and must not be forced to I/3. Check standing starts, stop/restart, forward/reverse changes and one loaded acceleration/deceleration cycle. Send the complete `log.txt`.\n''', encoding='utf-8')

# Sanity checks
ET.parse('modDesc.xml')
code = Path('Scripts/C330TransmissionFix.lua').read_text(encoding='utf-8')
assert 'LIGHT_START_MAX_TOTAL_MASS_T = FACTORY_BASE_MASS_T + LIGHT_START_EXTRA_MASS_T' in code
assert 'totalMass < LIGHT_START_MAX_TOTAL_MASS_T' in code
assert 'return 3, totalMass, "LIGHT_I3"' in code
assert '[C330TRANS] START GEAR I/%d' in code
assert 'FORWARD_RANGE_DOWNSHIFT_MAX_SPEED = 6.0' in code
assert 'FORWARD_LOW_SPEED_RANGE_RESET = 0.5' in code
assert 'TOP_GEAR_POSTSHIFT_MIN_RPM = 1200' in code
assert '0.0.1.4 C-330 6F/2R controller installed' in code
assert '<version>0.0.1.4</version>' in Path('modDesc.xml').read_text(encoding='utf-8')
# Engine must remain on the existing 100 Nm safe point.
vehicle = Path('c330m.xml').read_text(encoding='utf-8')
c0 = vehicle.find('<motorConfiguration name="C-330" hp="30" price="0">')
c1 = vehicle.find('</motorConfiguration>', c0)
cblock = vehicle[c0:c1]
assert 'torqueScale="0.100"' in cblock
assert 'normRpm="0.727273" torque="1.00"' in cblock
assert 'normRpm="0.818182" torque="1.00"' in cblock
assert 'normRpm="1.00" torque="0.972364"' in cblock
print('0.0.1.4 mass-aware I/3 start test validated')
