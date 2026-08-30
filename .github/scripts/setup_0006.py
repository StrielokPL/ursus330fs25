from pathlib import Path
import json
import xml.etree.ElementTree as ET

# 0.0.0.6 is diagnostic-only: no gearbox thresholds or ratios are changed.

# Add a marker for range changes requested by C330TransmissionFix so the read-only
# debugger can distinguish them from group changes originating elsewhere.
p = Path('Scripts/C330TransmissionFix.lua')
s = p.read_text(encoding='utf-8')
old = '''    local function setAutomaticRange(motor, targetRange, targetGear, reason, rpm, load, loadSource, recoveryHold)\n        local currentRange = motor.activeGearGroupIndex or LOW_RANGE\n        local currentGear = motor.targetGear or motor.gear or 0\n\n        if targetRange ~= currentRange then\n            motor:setGearGroup(targetRange)\n        end\n\n        local now = g_time or 0\n        motor.c330FixRangeCooldownUntil = now + RANGE_CHANGE_COOLDOWN_MS\n'''
new = '''    local function setAutomaticRange(motor, targetRange, targetGear, reason, rpm, load, loadSource, recoveryHold)\n        local currentRange = motor.activeGearGroupIndex or LOW_RANGE\n        local currentGear = motor.targetGear or motor.gear or 0\n        local now = g_time or 0\n\n        -- Diagnostic breadcrumb only. TractorDebugKit uses this to tell a range\n        -- change explicitly requested here from one performed elsewhere by the\n        -- GIANTS transmission state machine. No ADS state is written.\n        motor.c330FixRequestedRange = targetRange\n        motor.c330FixRequestedGear = targetGear\n        motor.c330FixRequestedRangeAt = now\n        motor.c330FixRequestedRangeReason = reason\n\n        if targetRange ~= currentRange then\n            motor:setGearGroup(targetRange)\n        end\n\n        motor.c330FixRangeCooldownUntil = now + RANGE_CHANGE_COOLDOWN_MS\n'''
if old not in s:
    raise SystemExit('Expected setAutomaticRange block not found')
s = s.replace(old, new, 1)
s = s.replace('-- 0.0.0.5 TEST: factory 3-speed main gearbox x 2 mechanical ranges; ADS-safe hysteresis.',
              '-- 0.0.0.6 TEST: 0.0.0.5 gearbox logic unchanged; extended range-source diagnostics.', 1)
s = s.replace('Logging.info("[C330TRANS] 0.0.0.5 C-330 3x2 range controller installed (ADS-safe hysteresis)")',
              'Logging.info("[C330TRANS] 0.0.0.6 C-330 3x2 range controller installed (0.0.0.5 logic + range diagnostics)")', 1)
p.write_text(s, encoding='utf-8')

# Improve TractorDebugKit: gear=0 is a normal transient during a mechanical shift,
# so it must not be treated as a real A->B->A oscillation. Also label range changes.
p = Path('debug/TractorDebugKit.lua')
s = p.read_text(encoding='utf-8')
old = '''    local function gearSignature(motor)\n        return string.format("%d:%d", getGear(motor), getGroup(motor))\n    end\n\n    local function traceTransmission(vehicle)\n'''
new = '''    local function gearSignature(motor)\n        return string.format("%d:%d", getGear(motor), getGroup(motor))\n    end\n\n    local function gearFromSignature(signature)\n        local gear = string.match(signature or "", "^(-?%d+):")\n        return tonumber(gear) or 0\n    end\n\n    local function groupFromSignature(signature)\n        local group = string.match(signature or "", ":(-?%d+)$")\n        return tonumber(group) or 0\n    end\n\n    local function traceTransmission(vehicle)\n'''
if old not in s:
    raise SystemExit('Expected gearSignature block not found')
s = s.replace(old, new, 1)

old = '''        if vehicle.tractorDbgLastGearSignature == nil then\n            vehicle.tractorDbgLastGearSignature = signature\n            return\n        end\n'''
new = '''        if vehicle.tractorDbgLastGearSignature == nil then\n            vehicle.tractorDbgLastGearSignature = signature\n            vehicle.tractorDbgLastGroup = getGroup(motor)\n            return\n        end\n'''
if old not in s:
    raise SystemExit('Expected trace initialization block not found')
s = s.replace(old, new, 1)

old = '''        Logging.info(\n            "[TRACTORDBG][SHIFT] %s -> %s speed=%.2f rpm=%.0f adsLoad=%s dtSinceLast=%s",\n            previous,\n            signature,\n            getSpeed(vehicle),\n            getMotorRpm(motor),\n            load ~= nil and string.format("%.3f", load) or "n/a",\n            vehicle.tractorDbgLastShiftTime ~= nil and tostring(now - vehicle.tractorDbgLastShiftTime) or "n/a"\n        )\n\n        if vehicle.tractorDbgPreviousShiftFrom ~= nil\n            and vehicle.tractorDbgPreviousShiftTo ~= nil\n            and vehicle.tractorDbgPreviousShiftFrom == signature\n            and vehicle.tractorDbgPreviousShiftTo == previous\n            and vehicle.tractorDbgLastShiftTime ~= nil\n            and now - vehicle.tractorDbgLastShiftTime <= CFG.oscillationWindowMs then\n            Logging.warning(\n                "[TRACTORDBG][SHIFT_OSCILLATION] candidate %s -> %s -> %s within %d ms",\n                signature, previous, signature, now - vehicle.tractorDbgLastShiftTime\n            )\n        end\n\n        vehicle.tractorDbgPreviousShiftFrom = previous\n'''
new = '''        Logging.info(\n            "[TRACTORDBG][SHIFT] %s -> %s speed=%.2f rpm=%.0f adsLoad=%s dtSinceLast=%s rawActive=%s rawTarget=%s rawGear=%s rawCurrent=%s direction=%s autoTimer=%s",\n            previous,\n            signature,\n            getSpeed(vehicle),\n            getMotorRpm(motor),\n            load ~= nil and string.format("%.3f", load) or "n/a",\n            vehicle.tractorDbgLastShiftTime ~= nil and tostring(now - vehicle.tractorDbgLastShiftTime) or "n/a",\n            tostring(motor.activeGearIndex),\n            tostring(motor.targetGear),\n            tostring(motor.gear),\n            tostring(motor.currentGear),\n            tostring(motor.currentDirection),\n            tostring(motor.autoGearChangeTimer)\n        )\n\n        local previousGroup = groupFromSignature(previous)\n        local currentGroup = getGroup(motor)\n        if currentGroup ~= previousGroup then\n            local requestAt = tonumber(motor.c330FixRequestedRangeAt)\n            local requestRange = tonumber(motor.c330FixRequestedRange)\n            local requestAge = requestAt ~= nil and (now - requestAt) or nil\n            local requestedHere = requestRange == currentGroup\n                and requestAge ~= nil\n                and requestAge >= 0\n                and requestAge <= 1500\n\n            Logging.info(\n                "[TRACTORDBG][RANGE_CHANGE] %d -> %d source=%s requestAge=%s requestGear=%s reason=%s speed=%.2f rpm=%.0f adsLoad=%s",\n                previousGroup,\n                currentGroup,\n                requestedHere and "C330TRANS" or "EXTERNAL/GIANTS",\n                requestAge ~= nil and tostring(requestAge) or "n/a",\n                tostring(motor.c330FixRequestedGear),\n                tostring(motor.c330FixRequestedRangeReason),\n                getSpeed(vehicle),\n                getMotorRpm(motor),\n                load ~= nil and string.format("%.3f", load) or "n/a"\n            )\n        end\n\n        -- activeGearIndex==0 is the normal disengaged phase between mechanical\n        -- gears. Do not report 0->N->0 or N->0->N as a real oscillation.\n        local currentGear = gearFromSignature(signature)\n        local previousGear = gearFromSignature(previous)\n        if currentGear > 0\n            and previousGear > 0\n            and vehicle.tractorDbgPreviousShiftFrom ~= nil\n            and vehicle.tractorDbgPreviousShiftTo ~= nil\n            and vehicle.tractorDbgPreviousShiftFrom == signature\n            and vehicle.tractorDbgPreviousShiftTo == previous\n            and vehicle.tractorDbgLastShiftTime ~= nil\n            and now - vehicle.tractorDbgLastShiftTime <= CFG.oscillationWindowMs then\n            Logging.warning(\n                "[TRACTORDBG][SHIFT_OSCILLATION] candidate %s -> %s -> %s within %d ms",\n                signature, previous, signature, now - vehicle.tractorDbgLastShiftTime\n            )\n        end\n\n        vehicle.tractorDbgLastGroup = currentGroup\n        vehicle.tractorDbgPreviousShiftFrom = previous\n'''
if old not in s:
    raise SystemExit('Expected shift logging block not found')
s = s.replace(old, new, 1)
p.write_text(s, encoding='utf-8')

# Version bump only; no vehicle XML physics change.
p = Path('modDesc.xml')
s = p.read_text(encoding='utf-8')
if '<version>0.0.0.5</version>' not in s:
    raise SystemExit('Expected modDesc 0.0.0.5')
s = s.replace('<version>0.0.0.5</version>', '<version>0.0.0.6</version>', 1)
p.write_text(s, encoding='utf-8')
ET.parse(p)

# README version line.
p = Path('README.md')
s = p.read_text(encoding='utf-8')
if '**0.0.0.5 – ADS-safe gearbox test prerelease**' not in s:
    raise SystemExit('Expected README 0.0.0.5 line')
s = s.replace('**0.0.0.5 – ADS-safe gearbox test prerelease**',
              '**0.0.0.6 – range-source diagnostic prerelease**', 1)
p.write_text(s, encoding='utf-8')

# Changelog.
p = Path('CHANGELOG.md')
s = p.read_text(encoding='utf-8')
if not s.startswith('# Changelog\n\n'):
    raise SystemExit('Unexpected changelog header')
entry = '''# Changelog\n\n## 0.0.0.6 - range-source diagnostic test\n\nDiagnostic follow-up to the 0.0.0.5 runtime log. **No transmission ratios, thresholds, engine values or ADS-facing behavior are changed.**\n\n### Findings from 0.0.0.5\n- ADS-safe range-up hysteresis worked: observed `I/3 -> II/1` transitions occurred around 2180-2220 rpm at moderate ADS load.\n- No C-330/ADS/AIASF Lua error was observed.\n- `activeGearIndex=0` is a normal disengaged phase during shifts; the old debugger incorrectly flagged many such sequences as oscillations.\n- Several low-speed range changes occurred without a matching `[C330TRANS] RANGE UP/DOWN` message and need source attribution before changing gearbox logic.\n\n### Diagnostics\n- `SHIFT_OSCILLATION` now ignores transitions involving gear index 0.\n- Every shift log now includes raw active/target/current gear fields, current direction and auto gear timer.\n- Every actual gear-group change gets a `[TRACTORDBG][RANGE_CHANGE]` line.\n- Range changes are labelled `source=C330TRANS` when they match a recent controller request, otherwise `source=EXTERNAL/GIANTS`.\n- `C330TransmissionFix` writes only an internal diagnostic breadcrumb for its own requested range; it still never writes to ADS state.\n\n### ADS protection\n- 0.0.0.5 load validation and fallback remain unchanged.\n- ADS remains optional and read-only.\n- Static Cabins / dirty-flag protection remains unchanged.\n\n### Explicitly unchanged\n- C-330 factory ratios and range thresholds.\n- Engine torque/fuel model.\n- C-330M drivetrain.\n- Mass/COM, ballast, tyres and suspension.\n\n'''
s = entry + s[len('# Changelog\n\n'):]
p.write_text(s, encoding='utf-8')

# Release config and notes.
Path('.release/release.json').write_text(json.dumps({
    'version': '0.0.0.6',
    'tag': '0.0.0.6',
    'title': '0.0.0.6 - C-330 range-source diagnostic test',
    'prerelease': True,
    'zipName': 'FS25_UrsusC330_330M_4x2.zip'
}, indent=2) + '\n', encoding='utf-8')
Path('.release/notes.md').write_text('''## Ursus C-330 / C-330M 0.0.0.6\n\nDiagnostic-only follow-up to the 0.0.0.5 gearbox test. **Gear ratios and shift thresholds are unchanged.**\n\n### Changes\n- suppresses false `SHIFT_OSCILLATION` warnings caused by the normal `activeGearIndex=0` disengaged phase,\n- adds raw active/target/current gear and direction fields to shift traces,\n- adds `[TRACTORDBG][RANGE_CHANGE]` for every actual I/II group change,\n- labels a range change as `C330TRANS` when requested by our controller, otherwise `EXTERNAL/GIANTS`,\n- keeps ADS strictly read-only and retains the 0.0.0.5 invalid-load fallback,\n- keeps Static Cabins / dirty-flag protection unchanged.\n\n### Test\nUse **C-330 (motor=1)** with the same heavy trailer. Drive from standstill through both ranges, then deliberately slow it under load and accelerate again. Send the complete `log.txt`; the key lines are `[TRACTORDBG][RANGE_CHANGE]`, `[TRACTORDBG][SHIFT]` and `[C330TRANS]`.\n''', encoding='utf-8')

# Sanity checks.
ET.parse('modDesc.xml')
dbg = Path('debug/TractorDebugKit.lua').read_text(encoding='utf-8')
fix = Path('Scripts/C330TransmissionFix.lua').read_text(encoding='utf-8')
assert '[TRACTORDBG][RANGE_CHANGE]' in dbg
assert 'rawTarget=%s' in dbg
assert 'currentGear > 0' in dbg and 'previousGear > 0' in dbg
assert 'c330FixRequestedRangeAt' in fix
assert '<version>0.0.0.6</version>' in Path('modDesc.xml').read_text(encoding='utf-8')
print('0.0.0.6 diagnostic setup validated')
