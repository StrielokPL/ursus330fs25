from pathlib import Path
import json
import xml.etree.ElementTree as ET

# 0.0.0.7 completes automatic control of the C-330 6F/2R range gearbox.
# Forward thresholds/ratios from 0.0.0.5 remain unchanged; reverse now uses
# the same ADS-safe range logic instead of GIANTS automatic group selection.

p = Path('Scripts/C330TransmissionFix.lua')
s = p.read_text(encoding='utf-8')
s = s.replace(
    '-- 0.0.0.6 TEST: 0.0.0.5 gearbox logic unchanged; extended range-source diagnostics.',
    '-- 0.0.0.7 TEST: complete automatic 6F/2R range control; ADS-safe forward and reverse.',
    1
)
s = s.replace(
    '-- Manual modes are left to GIANTS unchanged. C-330M is intentionally excluded\n-- from this test until its own gearing is calibrated.',
    '-- Manual modes are left to GIANTS unchanged. Automatic forward and reverse use\n-- explicit C-330 range logic. C-330M remains intentionally excluded.',
    1
)

old = '''    local function isAutomaticForward(motor)\n        return isC330Motor(motor)\n            and hasFactoryRanges(motor)\n            and motor.gearShiftMode == VehicleMotor.SHIFT_MODE_AUTOMATIC\n            and (motor.currentDirection or 1) >= 0\n    end\n'''
new = '''    local function isAutomaticC330(motor)\n        return isC330Motor(motor)\n            and hasFactoryRanges(motor)\n            and motor.gearShiftMode == VehicleMotor.SHIFT_MODE_AUTOMATIC\n    end\n\n    local function isAutomaticForward(motor)\n        return isAutomaticC330(motor)\n            and (motor.currentDirection or 1) >= 0\n    end\n\n    local function isAutomaticReverse(motor)\n        return isAutomaticC330(motor)\n            and (motor.currentDirection or 1) < 0\n    end\n'''
if old not in s:
    raise SystemExit('Expected isAutomaticForward block not found')
s = s.replace(old, new, 1)

old = '''    -- GIANTS automatic group selection treats the two C-330 ranges as unrelated\n    -- optimization choices. Disable that only while driving forward in automatic\n    -- mode; reverse and all manual modes keep the base-game behavior for now.\n    function VehicleMotor:getUseAutomaticGroupShifting()\n        if isAutomaticForward(self) then\n            return false\n        end\n\n        return originalGetUseAutomaticGroupShifting(self)\n    end\n'''
new = '''    -- GIANTS automatic group selection treats the two mechanical C-330 ranges as\n    -- unrelated optimization choices. Disable it for the complete automatic 6F/2R\n    -- gearbox. Manual modes still keep base-game group handling.\n    function VehicleMotor:getUseAutomaticGroupShifting()\n        if isAutomaticC330(self) then\n            return false\n        end\n\n        return originalGetUseAutomaticGroupShifting(self)\n    end\n'''
if old not in s:
    raise SystemExit('Expected getUseAutomaticGroupShifting block not found')
s = s.replace(old, new, 1)

old = '''    function VehicleMotor:getBestStartGear(gears)\n        local gear, group = originalGetBestStartGear(self, gears)\n\n        if isAutomaticForward(self) then\n            group = LOW_RANGE\n            gear = math.max(1, math.min(gear or 1, math.min(#gears, 3)))\n\n            if self.activeGearGroupIndex ~= LOW_RANGE then\n                self:setGearGroup(LOW_RANGE)\n            end\n        end\n\n        return gear, group\n    end\n'''
new = '''    function VehicleMotor:getBestStartGear(gears)\n        local gear, group = originalGetBestStartGear(self, gears)\n\n        if isAutomaticC330(self) then\n            group = LOW_RANGE\n            gear = math.max(1, math.min(gear or 1, math.min(#gears, 3)))\n\n            -- A real C-330 starts/restarts from range I. Mark this request so the\n            -- diagnostic kit does not misattribute the reset to GIANTS.\n            if self.activeGearGroupIndex ~= LOW_RANGE then\n                local now = g_time or 0\n                self.c330FixRequestedRange = LOW_RANGE\n                self.c330FixRequestedGear = gear\n                self.c330FixRequestedRangeAt = now\n                self.c330FixRequestedRangeReason = "START RANGE RESET"\n                self:setGearGroup(LOW_RANGE)\n            end\n\n            self.c330FixRangeRecoverySince = nil\n        end\n\n        return gear, group\n    end\n'''
if old not in s:
    raise SystemExit('Expected getBestStartGear block not found')
s = s.replace(old, new, 1)

old = '''        if not isAutomaticForward(self)\n            or vanillaTarget == nil\n            or curGear == nil\n            or curGear <= 0\n            or gears == nil\n            or #gears < 1 then\n            return vanillaTarget\n        end\n'''
new = '''        if not isAutomaticC330(self)\n            or vanillaTarget == nil\n            or curGear == nil\n            or curGear <= 0\n            or gears == nil\n            or #gears < 1 then\n            return vanillaTarget\n        end\n'''
if old not in s:
    raise SystemExit('Expected prediction guard not found')
s = s.replace(old, new, 1)

needle = '''        local accel = math.abs(tonumber(acceleratorPedal) or 0)\n        local maxGear = math.min(#gears, 3)\n\n        -- The critical missing behavior in vanilla: II/1 must be allowed to fall\n'''
insert = '''        local accel = math.abs(tonumber(acceleratorPedal) or 0)\n        local maxGear = math.min(#gears, 3)\n\n        -- Reverse has one mechanical reverse gear passing through the same I/II\n        -- range box: R-I ~= 1.53 km/h, R-II ~= 6.21 km/h. GIANTS previously\n        -- selected range II around 1.5 km/h even at ~0.8 ADS load. Treat reverse\n        -- as a two-step gearbox and only leave range I after sustained recovery.\n        if isAutomaticReverse(self) then\n            if range == HIGH_RANGE\n                and curGear == 1\n                and speed > 0.3\n                and rpm <= RANGE_DOWNSHIFT_RPM\n                and ((load ~= nil and load >= RANGE_DOWNSHIFT_LOAD) or accel >= RANGE_DOWNSHIFT_ACCEL) then\n                return setAutomaticRange(\n                    self, LOW_RANGE, 1, "REVERSE RANGE DOWN",\n                    rpm, load, loadSource, true\n                )\n            end\n\n            local reverseRecoveryReady = range == LOW_RANGE\n                and curGear == 1\n                and rpm >= RANGE_UPSHIFT_RPM\n                and (load == nil or load <= RANGE_UPSHIFT_MAX_LOAD)\n                and (self.c330FixUpshiftHoldUntil == nil or now >= self.c330FixUpshiftHoldUntil)\n\n            if reverseRecoveryReady then\n                if self.c330FixRangeRecoverySince == nil then\n                    self.c330FixRangeRecoverySince = now\n                elseif now - self.c330FixRangeRecoverySince >= RANGE_UPSHIFT_STABLE_MS then\n                    return setAutomaticRange(\n                        self, HIGH_RANGE, 1, "REVERSE RANGE UP",\n                        rpm, load, loadSource, false\n                    )\n                end\n            else\n                self.c330FixRangeRecoverySince = nil\n            end\n\n            -- There is only one backwardGear. Range selection above is therefore\n            -- the complete reverse automatic logic; never hand group choice back\n            -- to vanilla while reversing.\n            return 1\n        end\n\n        -- The critical missing behavior in vanilla: II/1 must be allowed to fall\n'''
if needle not in s:
    raise SystemExit('Expected insertion point after maxGear not found')
s = s.replace(needle, insert, 1)

s = s.replace(
    'Logging.info("[C330TRANS] 0.0.0.6 C-330 3x2 range controller installed (0.0.0.5 logic + range diagnostics)")',
    'Logging.info("[C330TRANS] 0.0.0.7 C-330 full 6F/2R automatic range controller installed (ADS-safe)")',
    1
)
p.write_text(s, encoding='utf-8')

# Make range attribution explicit about direction for the final gearbox test.
p = Path('debug/TractorDebugKit.lua')
s = p.read_text(encoding='utf-8')
old = '''                "[TRACTORDBG][RANGE_CHANGE] %d -> %d source=%s requestAge=%s requestGear=%s reason=%s speed=%.2f rpm=%.0f adsLoad=%s",\n                previousGroup,\n                currentGroup,\n                requestedHere and "C330TRANS" or "EXTERNAL/GIANTS",\n                requestAge ~= nil and tostring(requestAge) or "n/a",\n                tostring(motor.c330FixRequestedGear),\n                tostring(motor.c330FixRequestedRangeReason),\n                getSpeed(vehicle),\n                getMotorRpm(motor),\n                load ~= nil and string.format("%.3f", load) or "n/a"\n            )\n'''
new = '''                "[TRACTORDBG][RANGE_CHANGE] %d -> %d source=%s requestAge=%s requestGear=%s reason=%s direction=%s speed=%.2f rpm=%.0f adsLoad=%s",\n                previousGroup,\n                currentGroup,\n                requestedHere and "C330TRANS" or "EXTERNAL/GIANTS",\n                requestAge ~= nil and tostring(requestAge) or "n/a",\n                tostring(motor.c330FixRequestedGear),\n                tostring(motor.c330FixRequestedRangeReason),\n                tostring(motor.currentDirection),\n                getSpeed(vehicle),\n                getMotorRpm(motor),\n                load ~= nil and string.format("%.3f", load) or "n/a"\n            )\n'''
if old not in s:
    raise SystemExit('Expected RANGE_CHANGE logging block not found')
s = s.replace(old, new, 1)
p.write_text(s, encoding='utf-8')

# Version bump.
p = Path('modDesc.xml')
s = p.read_text(encoding='utf-8')
if '<version>0.0.0.6</version>' not in s:
    raise SystemExit('Expected modDesc 0.0.0.6')
s = s.replace('<version>0.0.0.6</version>', '<version>0.0.0.7</version>', 1)
p.write_text(s, encoding='utf-8')
ET.parse(p)

# README current version.
p = Path('README.md')
s = p.read_text(encoding='utf-8')
if '**0.0.0.6 – range-source diagnostic prerelease**' not in s:
    raise SystemExit('Expected README 0.0.0.6 line')
s = s.replace(
    '**0.0.0.6 – range-source diagnostic prerelease**',
    '**0.0.0.7 – full 6F/2R gearbox prerelease**',
    1
)
p.write_text(s, encoding='utf-8')

# Changelog.
p = Path('CHANGELOG.md')
s = p.read_text(encoding='utf-8')
if not s.startswith('# Changelog\n\n'):
    raise SystemExit('Unexpected changelog header')
entry = '''# Changelog\n\n## 0.0.0.7 - full C-330 6F/2R automatic gearbox test\n\nCompletes the automatic range controller after 0.0.0.6 proved that remaining external I/II changes were GIANTS reverse/start behavior. Factory ratios and established forward thresholds are unchanged.\n\n### Reverse automatic control\n- GIANTS automatic group selection is now disabled for C-330 automatic mode in both directions.\n- Reverse is treated as the real two-step range gearbox: `R-I` (~1.53 km/h) and `R-II` (~6.21 km/h).\n- `R-I -> R-II` requires the same ADS-safe sustained recovery used at the forward range boundary: >=2050 rpm, load <=0.55, held for 800 ms, and no active recovery hold.\n- `R-II -> R-I` occurs under the established protection threshold: <=1500 rpm with load >=0.75 or strong accelerator demand.\n- Automatic start/restart forces range I; manual transmission modes remain unchanged.\n\n### ADS protection\n- ADS remains optional and strictly read-only.\n- Invalid/negative ADS shift samples are still rejected and replaced with native GIANTS smoothed load.\n- Reverse range changes now use the same filtered load path as forward changes.\n- Existing Static Cabins / dirty-flag protection remains unchanged.\n\n### Diagnostics\n- `[TRACTORDBG][RANGE_CHANGE]` now includes current direction.\n- Controller-generated reverse changes use reasons `REVERSE RANGE UP` / `REVERSE RANGE DOWN`.\n- Start/reset range changes are marked as `START RANGE RESET` for source attribution.\n\n### Explicitly unchanged\n- C-330 factory ratios and forward shift thresholds from 0.0.0.5.\n- Engine torque/fuel model.\n- C-330M drivetrain.\n- Mass/COM, ballast, tyres and suspension.\n\n'''
s = entry + s[len('# Changelog\n\n'):]
p.write_text(s, encoding='utf-8')

# Release metadata. This commit is produced by github-actions, so release.yml will
# not recursively trigger; a small manual notes marker will trigger it afterwards.
Path('.release/release.json').write_text(json.dumps({
    'version': '0.0.0.7',
    'tag': '0.0.0.7',
    'title': '0.0.0.7 - C-330 full 6F/2R gearbox test',
    'prerelease': True,
    'zipName': 'FS25_UrsusC330_330M_4x2.zip'
}, indent=2) + '\n', encoding='utf-8')
Path('.release/notes.md').write_text('''## Ursus C-330 / C-330M 0.0.0.7\n\nFinal dedicated C-330 gearbox test: automatic range control now covers the complete **6F/2R** transmission.\n\n### Changes\n- keeps the validated forward `I/1 -> I/2 -> I/3 -> II/1 -> II/2 -> II/3` logic unchanged,\n- takes control of reverse range selection from GIANTS,\n- treats reverse as `R-I` (~1.53 km/h) and `R-II` (~6.21 km/h),\n- only permits `R-I -> R-II` after sustained high-rpm / low-load recovery,\n- protects `R-II` by downshifting to `R-I` under low-rpm high-load demand,\n- forces range I for automatic start/restart,\n- keeps manual modes unchanged,\n- keeps ADS optional, read-only and filtered; Static Cabins protection is unchanged.\n\n### Test\nUse **C-330 (motor=1)**. Test forward as before, then reverse both unloaded and with the heavy trailer. In particular verify that a loaded tractor does not jump to R-II around 1.5 km/h, while an unloaded/lightly loaded tractor can reach R-II after R-I tops out. Send the complete `log.txt`.\n''', encoding='utf-8')

# Sanity checks.
ET.parse('modDesc.xml')
fix = Path('Scripts/C330TransmissionFix.lua').read_text(encoding='utf-8')
dbg = Path('debug/TractorDebugKit.lua').read_text(encoding='utf-8')
assert 'isAutomaticC330' in fix
assert 'REVERSE RANGE UP' in fix and 'REVERSE RANGE DOWN' in fix
assert 'if isAutomaticReverse(self) then' in fix
assert 'if isAutomaticC330(self) then\n            return false' in fix
assert 'START RANGE RESET' in fix
assert 'direction=%s speed=' in dbg
assert '<version>0.0.0.7</version>' in Path('modDesc.xml').read_text(encoding='utf-8')
print('0.0.0.7 full 6F/2R gearbox setup validated')
