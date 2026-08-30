from pathlib import Path
import json
import re
import xml.etree.ElementTree as ET

# 0.0.1.1: first isolated S-312C engine test for standard C-330 only.
# Confirmed anchors: 100 Nm at 1600-1800 rpm, 22.4 kW at 2200 rpm.
# Low-rpm points are a conservative interpolation and are explicitly test values.
# Fuel usage, min/max RPM, gearbox, C-330M and all other physics stay unchanged.

# --- C-330 engine curve only -------------------------------------------------
p = Path('c330m.xml')
s = p.read_text(encoding='utf-8')
start = s.find('<motorConfiguration name="C-330" hp="30" price="0">')
if start < 0:
    raise SystemExit('C-330 motorConfiguration not found')
end = s.find('</motorConfiguration>', start)
if end < 0:
    raise SystemExit('C-330 motorConfiguration end not found')
end += len('</motorConfiguration>')
block = s[start:end]

old_motor = '''<motor torqueScale="0.138" minRpm="600" maxRpm="2200" accelerationLimit="1.0" maxForwardSpeed="22.878" maxBackwardSpeed="6.207" brakeForce="1.3" lowBrakeForceScale="0.1" dampingRateScale="0.1">
                    <torque normRpm="0.45" torque="0.9"/>
                    <torque normRpm="0.50" torque="0.97"/>
                    <torque normRpm="0.59" torque="1"/>
                    <torque normRpm="0.72" torque="1"/>
                    <torque normRpm="0.86" torque="0.88"/>
                    <torque normRpm="1.00" torque="0.72"/>
                </motor>'''

new_motor = '''<motor torqueScale="0.100" minRpm="600" maxRpm="2200" accelerationLimit="1.0" maxForwardSpeed="22.878" maxBackwardSpeed="6.207" brakeForce="1.3" lowBrakeForceScale="0.1" dampingRateScale="0.1">
                    <!-- S-312C test curve. Confirmed anchors: 100 Nm @1600-1800 rpm,
                         22.4 kW @2200 rpm => ~97.24 Nm. Low-rpm points are
                         conservative interpolation pending runtime validation. -->
                    <torque normRpm="0.45" torque="0.88"/>      <!-- 990 rpm: 88 Nm (test interpolation) -->
                    <torque normRpm="0.50" torque="0.92"/>      <!-- 1100 rpm: 92 Nm (test interpolation) -->
                    <torque normRpm="0.59" torque="0.96"/>      <!-- 1298 rpm: 96 Nm (test interpolation) -->
                    <torque normRpm="0.727273" torque="1.00"/>  <!-- 1600 rpm: 100 Nm -->
                    <torque normRpm="0.818182" torque="1.00"/>  <!-- 1800 rpm: 100 Nm -->
                    <torque normRpm="1.00" torque="0.972364"/>  <!-- 2200 rpm: 97.24 Nm ~= 22.4 kW -->
                </motor>'''

if old_motor not in block:
    raise SystemExit('Expected imported C-330 engine block not found')
block = block.replace(old_motor, new_motor, 1)
s = s[:start] + block + s[end:]
p.write_text(s, encoding='utf-8')
ET.parse(p)

# Prove C-330M is still the imported control engine.
all_text = p.read_text(encoding='utf-8')
m_start = all_text.find('<motorConfiguration name="C-330M" hp="31" price="0">')
m_end = all_text.find('</motorConfiguration>', m_start)
if m_start < 0 or m_end < 0:
    raise SystemExit('C-330M motorConfiguration not found')
m_block = all_text[m_start:m_end]
assert 'torqueScale="0.138"' in m_block
assert '<torque normRpm="0.59" torque="1"/>' in m_block

# --- Read-only engine trace --------------------------------------------------
p = Path('debug/TractorDebugKit.lua')
s = p.read_text(encoding='utf-8')
s = s.replace(
    '        periodicWheelTrace = false,\n        periodicWheelTraceMs = 500,\n        readAdsDynamicLoad = true',
    '        periodicWheelTrace = false,\n        periodicWheelTraceMs = 500,\n        periodicEngineTrace = true,\n        periodicEngineTraceMs = 750,\n        readAdsDynamicLoad = true',
    1
)

old_motor_log = '''            "[TRACTORDBG][MOTOR] gear=%d group=%d gears=%d groups=%d shiftMode=%s rpm=%.0f maxRpm=%s speed=%.2f adsLoad=%s",
            getGear(motor),
            getGroup(motor),
            gearCount,
            groupCount,
            tostring(motor.gearShiftMode),
            getMotorRpm(motor),
            tostring(motor.maxRpm),
            getSpeed(vehicle),
            load ~= nil and string.format("%.3f", load) or "n/a"
        )'''
new_motor_log = '''            "[TRACTORDBG][MOTOR] gear=%d group=%d gears=%d groups=%d shiftMode=%s rpm=%.0f minRpm=%s maxRpm=%s torqueScale=%s speed=%.2f adsLoad=%s",
            getGear(motor),
            getGroup(motor),
            gearCount,
            groupCount,
            tostring(motor.gearShiftMode),
            getMotorRpm(motor),
            tostring(motor.minRpm),
            tostring(motor.maxRpm),
            tostring(motor.torqueScale),
            getSpeed(vehicle),
            load ~= nil and string.format("%.3f", load) or "n/a"
        )'''
if old_motor_log not in s:
    raise SystemExit('Expected MOTOR log block not found')
s = s.replace(old_motor_log, new_motor_log, 1)

needle = '''    local function periodicWheelTrace(vehicle)
        if not CFG.periodicWheelTrace then
            return
        end
'''
engine_func = '''    local function getNativeMotorLoad(motor)
        if motor ~= nil and motor.getSmoothLoadPercentage ~= nil then
            local value = tonumber(motor:getSmoothLoadPercentage())
            if value ~= nil then
                return value
            end
        end
        return nil
    end

    local function periodicEngineTrace(vehicle)
        if not CFG.periodicEngineTrace then
            return
        end

        local motor = getMotor(vehicle)
        if motor == nil then
            return
        end

        local now = g_time or 0
        if vehicle.tractorDbgNextEngineTrace ~= nil and now < vehicle.tractorDbgNextEngineTrace then
            return
        end
        vehicle.tractorDbgNextEngineTrace = now + CFG.periodicEngineTraceMs

        local speed = getSpeed(vehicle)
        local adsLoad = getAdsLoad(vehicle)
        local nativeLoad = getNativeMotorLoad(motor)

        -- Avoid filling the log while the tractor simply idles parked. The trace
        -- is read-only and is intended to capture real pull/acceleration states.
        if speed < 0.20
            and (adsLoad == nil or adsLoad < 0.10)
            and (nativeLoad == nil or nativeLoad < 0.10) then
            return
        end

        Logging.info(
            "[TRACTORDBG][ENGINE_TRACE] speed=%.2f rpm=%.0f gear=%d group=%d direction=%s adsLoad=%s giantsLoad=%s",
            speed,
            getMotorRpm(motor),
            getGear(motor),
            getGroup(motor),
            tostring(motor.currentDirection),
            adsLoad ~= nil and string.format("%.3f", adsLoad) or "n/a",
            nativeLoad ~= nil and string.format("%.3f", nativeLoad) or "n/a"
        )
    end

'''
if needle not in s:
    raise SystemExit('periodicWheelTrace insertion point not found')
s = s.replace(needle, engine_func + needle, 1)

old_call = '''        traceTransmission(vehicle)
        periodicWheelTrace(vehicle)
    end'''
new_call = '''        traceTransmission(vehicle)
        periodicEngineTrace(vehicle)
        periodicWheelTrace(vehicle)
    end'''
if old_call not in s:
    raise SystemExit('diagnostic update call site not found')
s = s.replace(old_call, new_call, 1)
p.write_text(s, encoding='utf-8')

# --- Version/docs/release ----------------------------------------------------
p = Path('modDesc.xml')
s = p.read_text(encoding='utf-8')
if '<version>0.0.1.0</version>' not in s:
    raise SystemExit('Expected modDesc 0.0.1.0')
s = s.replace('<version>0.0.1.0</version>', '<version>0.0.1.1</version>', 1)
p.write_text(s, encoding='utf-8')
ET.parse(p)

p = Path('README.md')
s = p.read_text(encoding='utf-8')
if '**0.0.1.0 – C-330 gearbox milestone prerelease**' not in s:
    raise SystemExit('Expected README 0.0.1.0 version line')
s = s.replace(
    '**0.0.1.0 – C-330 gearbox milestone prerelease**',
    '**0.0.1.1 – S-312C torque-curve test prerelease**',
    1
)
p.write_text(s, encoding='utf-8')

p = Path('CHANGELOG.md')
s = p.read_text(encoding='utf-8')
if not s.startswith('# Changelog\n\n'):
    raise SystemExit('Unexpected changelog header')
entry = '''# Changelog\n\n## 0.0.1.1 - S-312C torque-curve test\n\nFirst isolated engine calibration for the standard **C-330**. Gearbox behavior from 0.0.1.0 is deliberately unchanged. C-330M keeps the old imported engine as a comparison/control configuration.\n\n### Problem\n- Imported `torqueScale=0.138` gives about 138 Nm peak torque.\n- The old curve produces roughly 22.9 kW already near 1580 rpm and about 24.1 kW near 1890 rpm, creating an unrealistically large low/mid-RPM torque reserve.\n- Factory target is 100 Nm maximum at 1600-1800 rpm and 22.4 kW at 2200 rpm.\n\n### Change\n- C-330 `torqueScale`: **0.138 -> 0.100**.\n- Confirmed torque anchors: **100 Nm at 1600 and 1800 rpm**.\n- Rated point: **~97.24 Nm at 2200 rpm**, corresponding to **22.4 kW**.\n- Low-RPM test interpolation: 88 Nm @990, 92 Nm @1100, 96 Nm @1298. These values are not claimed as factory measurements and are subject to runtime tuning.\n\n### Diagnostics\n- Added read-only `[TRACTORDBG][ENGINE_TRACE]` every 750 ms while the tractor is actually moving/loaded.\n- Trace records RPM, speed, gear/group, direction, raw ADS load and native GIANTS smoothed load.\n- `[TRACTORDBG][MOTOR]` also reports runtime min/max RPM and torqueScale fields when exposed by `VehicleMotor`.\n\n### Explicitly unchanged\n- Fuel consumer remains **4.2 l/h** for this test.\n- `minRpm=600`, `maxRpm=2200`, acceleration/braking parameters.\n- Complete C-330 6F/2R gearbox/controller.\n- ADS integration remains read-only and filtered.\n- C-330M engine/drivetrain.\n- Mass/COM, ballast, tyres and suspension.\n\n'''
s = entry + s[len('# Changelog\n\n'):]
p.write_text(s, encoding='utf-8')

Path('.release/release.json').write_text(json.dumps({
    'version': '0.0.1.1',
    'tag': '0.0.1.1',
    'title': '0.0.1.1 - S-312C torque curve test',
    'prerelease': True,
    'zipName': 'FS25_UrsusC330_330M_4x2.zip'
}, indent=2) + '\n', encoding='utf-8')

Path('.release/notes.md').write_text('''## Ursus C-330 / C-330M 0.0.1.1\n\nFirst isolated **S-312C engine torque-curve** test for the standard C-330.\n\n### Changed\n- peak torque corrected from the imported ~138 Nm to **100 Nm**,\n- maximum torque placed at **1600-1800 rpm**,\n- 2200-rpm torque set to **~97.24 Nm** for the factory **22.4 kW** rated power,\n- conservative low-rpm interpolation added for testing,\n- read-only engine trace added for RPM/load analysis.\n\n### Not changed\nFuel use, idle/max RPM, gearbox, ADS behavior, C-330M and chassis physics are unchanged.\n\n### Test\nUse **C-330 (motor=1)**. Compare unloaded acceleration with the previous build, then use the same heavy trailer on level ground and, if possible, on an incline/high-resistance pull. Let the engine work below 1800 rpm instead of immediately lifting off. Send the complete `log.txt`; `[ENGINE_TRACE]` will show how the real 100 Nm curve interacts with ADS and the completed gearbox.\n''', encoding='utf-8')

# Final sanity checks
ET.parse('c330m.xml')
ET.parse('modDesc.xml')
text = Path('c330m.xml').read_text(encoding='utf-8')
c_start = text.find('<motorConfiguration name="C-330" hp="30" price="0">')
c_end = text.find('</motorConfiguration>', c_start)
c_block = text[c_start:c_end]
assert 'torqueScale="0.100"' in c_block
assert 'normRpm="0.727273" torque="1.00"' in c_block
assert 'normRpm="0.818182" torque="1.00"' in c_block
assert 'normRpm="1.00" torque="0.972364"' in c_block
m_start = text.find('<motorConfiguration name="C-330M" hp="31" price="0">')
m_end = text.find('</motorConfiguration>', m_start)
assert 'torqueScale="0.138"' in text[m_start:m_end]
assert '[TRACTORDBG][ENGINE_TRACE]' in Path('debug/TractorDebugKit.lua').read_text(encoding='utf-8')
assert '<version>0.0.1.1</version>' in Path('modDesc.xml').read_text(encoding='utf-8')
print('0.0.1.1 S-312C torque test validated')
