from pathlib import Path
import json
import xml.etree.ElementTree as ET

# C330TransmissionFix.lua: tighten range hysteresis and ADS input validation.
p = Path('Scripts/C330TransmissionFix.lua')
s = p.read_text(encoding='utf-8')
repls = {
    '-- 0.0.0.4 TEST: factory 3-speed main gearbox x 2 mechanical ranges.': '-- 0.0.0.5 TEST: factory 3-speed main gearbox x 2 mechanical ranges; ADS-safe hysteresis.',
    '    local RANGE_UPSHIFT_RPM = 1950\n    local RANGE_UPSHIFT_MAX_LOAD = 0.72': '    local RANGE_UPSHIFT_RPM = 2050\n    local RANGE_UPSHIFT_MAX_LOAD = 0.55\n    local RANGE_UPSHIFT_STABLE_MS = 800',
    '    local RANGE_CHANGE_COOLDOWN_MS = 650\n    local LOAD_RECOVERY_HOLD_MS = 1800': '    local RANGE_CHANGE_COOLDOWN_MS = 800\n    local LOAD_RECOVERY_HOLD_MS = 2500',
    '        if adsLoad ~= nil and adsLoad >= 0 then\n            return math.clamp(adsLoad, 0, 1.5), "ADS"\n        end': '        -- ADS dynamicMotorLoad is treated as a read-only 0..1 signal. Values\n        -- outside that range (including the negative shift sentinels visible in\n        -- runtime logs) are never used for a shift decision. A tiny numerical\n        -- tolerance above 1.0 is accepted and clamped.\n        if adsLoad ~= nil and adsLoad >= 0 and adsLoad <= 1.05 then\n            return math.clamp(adsLoad, 0, 1.0), "ADS"\n        end',
    '        motor.c330FixRangeCooldownUntil = now + RANGE_CHANGE_COOLDOWN_MS\n        if recoveryHold then': '        motor.c330FixRangeCooldownUntil = now + RANGE_CHANGE_COOLDOWN_MS\n        motor.c330FixRangeRecoverySince = nil\n        if recoveryHold then',
    '        -- Crossing the other boundary is I/3 -> II/1. Do it only when the engine\n        -- is genuinely ready; a load-recovery hold prevents an immediate undo of\n        -- the protective downshift above.\n        if range == LOW_RANGE\n            and curGear == maxGear\n            and rpm >= RANGE_UPSHIFT_RPM\n            and (load == nil or load <= RANGE_UPSHIFT_MAX_LOAD)\n            and (self.c330FixUpshiftHoldUntil == nil or now >= self.c330FixUpshiftHoldUntil) then\n            return setAutomaticRange(\n                self, HIGH_RANGE, 1, "RANGE UP",\n                rpm, load, loadSource, false\n            )\n        end': '        -- Crossing the other boundary is I/3 -> II/1. The 0.0.0.4 log showed\n        -- that a single recovered sample was not enough: under a heavy trailer the\n        -- tractor could upshift and request I/3 again roughly a second later.\n        -- Require sustained recovery before leaving range I. This also limits\n        -- artificial shift cycling seen by ADS.\n        local rangeRecoveryReady = range == LOW_RANGE\n            and curGear == maxGear\n            and rpm >= RANGE_UPSHIFT_RPM\n            and (load == nil or load <= RANGE_UPSHIFT_MAX_LOAD)\n            and (self.c330FixUpshiftHoldUntil == nil or now >= self.c330FixUpshiftHoldUntil)\n\n        if rangeRecoveryReady then\n            if self.c330FixRangeRecoverySince == nil then\n                self.c330FixRangeRecoverySince = now\n            elseif now - self.c330FixRangeRecoverySince >= RANGE_UPSHIFT_STABLE_MS then\n                return setAutomaticRange(\n                    self, HIGH_RANGE, 1, "RANGE UP",\n                    rpm, load, loadSource, false\n                )\n            end\n        else\n            self.c330FixRangeRecoverySince = nil\n        end',
    '    Logging.info("[C330TRANS] 0.0.0.4 C-330 3x2 range controller installed")': '    Logging.info("[C330TRANS] 0.0.0.5 C-330 3x2 range controller installed (ADS-safe hysteresis)")'
}
for old, new in repls.items():
    if old not in s:
        raise SystemExit(f'Missing expected transmission fragment: {old[:80]!r}')
    s = s.replace(old, new, 1)
p.write_text(s, encoding='utf-8')

# modDesc version only; source files remain unchanged.
p = Path('modDesc.xml')
s = p.read_text(encoding='utf-8')
if '<version>0.0.0.4</version>' not in s:
    raise SystemExit('Expected modDesc 0.0.0.4')
s = s.replace('<version>0.0.0.4</version>', '<version>0.0.0.5</version>', 1)
p.write_text(s, encoding='utf-8')
ET.parse(p)

# README version line.
p = Path('README.md')
s = p.read_text(encoding='utf-8')
s = s.replace('**0.0.0.4 – C-330 gearbox test prerelease**', '**0.0.0.5 – ADS-safe gearbox test prerelease**', 1)
p.write_text(s, encoding='utf-8')

# Changelog entry.
p = Path('CHANGELOG.md')
s = p.read_text(encoding='utf-8')
if not s.startswith('# Changelog\n\n'):
    raise SystemExit('Unexpected changelog header')
entry = '''# Changelog\n\n## 0.0.0.5 - ADS-safe gearbox hysteresis test\n\nFollow-up to the first real C-330 0.0.0.4 runtime test. Factory ratios are unchanged.\n\n### Automatic range controller\n- Kept the successful heavy-load `II/1 -> I/3` downshift behavior.\n- Raised `I/3 -> II/1` recovery RPM from 1950 to **2050 rpm**.\n- Reduced maximum load for range upshift from 0.72 to **0.55**.\n- Added **800 ms sustained recovery** requirement before leaving range I.\n- Increased range-change cooldown from 650 to **800 ms**.\n- Increased post-downshift recovery hold from 1800 to **2500 ms**.\n- Goal: prevent repeated `I/3 <-> II/1` hunting with a heavy trailer while still allowing a clean road-range transition when unloaded.\n\n### ADS protection\n- ADS remains optional and read-only; the tractor mod never writes to ADS state.\n- `dynamicMotorLoad` is accepted only as a valid approximately 0..1 sample (0..1.05 tolerance, clamped to 1.0).\n- Negative shift sentinels and out-of-range ADS values are ignored and the controller falls back to native GIANTS smoothed motor load.\n- Reduced range hunting also reduces artificial rapid load/shift cycling presented to ADS.\n- Existing Static Cabins / dirty-flag protection remains unchanged.\n\n### Explicitly unchanged\n- Factory C-330 ratios introduced in 0.0.0.4.\n- Engine torque/fuel model.\n- C-330M drivetrain.\n- Mass/COM, ballast, tyres and suspension.\n\n'''
s = entry + s[len('# Changelog\n\n'):]
p.write_text(s, encoding='utf-8')

# Release config/notes.
Path('.release/release.json').write_text(json.dumps({
    'version': '0.0.0.5',
    'tag': '0.0.0.5',
    'title': '0.0.0.5 - C-330 ADS-safe gearbox test',
    'prerelease': True,
    'zipName': 'FS25_UrsusC330_330M_4x2.zip'
}, indent=2) + '\n', encoding='utf-8')
Path('.release/notes.md').write_text('''## Ursus C-330 / C-330M 0.0.0.5\n\nSecond **C-330 gearbox test**, focused on ADS safety and eliminating range hunting seen in the 0.0.0.4 runtime log.\n\n### Changes\n- keeps factory C-330 gearing and successful `II/1 -> I/3` heavy-load reduction,\n- `I/3 -> II/1` now requires >=2050 rpm, <=0.55 load and 800 ms of sustained recovery,\n- post-downshift recovery hold increased to 2.5 s,\n- range cooldown increased to 0.8 s,\n- ADS `dynamicMotorLoad` is strictly read-only and accepted only when approximately within 0..1,\n- invalid/negative ADS shift samples fall back to native GIANTS smoothed load,\n- Static Cabins / dirty-flag compatibility protection remains unchanged.\n\n### Test\nUse **C-330 (motor=1)**. Test unloaded acceleration, then the same heavy trailer. The key check is whether it now stays in range I while the load remains high instead of oscillating around `I/3 <-> II/1`. Send the complete `log.txt`.\n''', encoding='utf-8')

# Sanity checks.
if 'RANGE_UPSHIFT_RPM = 2050' not in Path('Scripts/C330TransmissionFix.lua').read_text(encoding='utf-8'):
    raise SystemExit('Transmission thresholds were not updated')
if '<version>0.0.0.5</version>' not in Path('modDesc.xml').read_text(encoding='utf-8'):
    raise SystemExit('Version update failed')
print('0.0.0.5 ADS-safe gearbox setup validated')
