from pathlib import Path
import xml.etree.ElementTree as ET

# Enable diagnostic source and bump development version.
p = Path('modDesc.xml')
s = p.read_text(encoding='utf-8')
old_version = '<version>0.0.0.2</version>'
if old_version not in s:
    raise SystemExit('Expected 0.0.0.2 version not found')
s = s.replace(old_version, '<version>0.0.0.3</version>', 1)

marker = '''    <multiplayer supported="true" />

    <storeItems>'''
replacement = '''    <multiplayer supported="true" />

    <!-- Temporary read-only runtime diagnostics for 0.0.0.3. Remove before stable release. -->
    <extraSourceFiles>
        <sourceFile filename="debug/TractorDebugKit.lua" />
    </extraSourceFiles>

    <storeItems>'''
if marker not in s:
    raise SystemExit('modDesc diagnostic insertion point not found')
s = s.replace(marker, replacement, 1)
p.write_text(s, encoding='utf-8')
ET.parse(p)

# README: mark current diagnostic version and explain scope.
p = Path('README.md')
s = p.read_text(encoding='utf-8')
s = s.replace('**0.0.0.2 – prerelease baseline**', '**0.0.0.3 – diagnostic prerelease**', 1)
needle = '''The repository was imported from mod package version **1.1.2.0**, but the project versioning was reset for the rebuild. Version `0.0.0.2` is the first documented development baseline in this repository.
'''
insert = needle + '''
### Runtime diagnostics in 0.0.0.3
Version `0.0.0.3` adds a temporary **read-only** `TractorDebugKit` adapted from `strojenieciagnikowfs25`. It does not tune or overwrite vehicle physics. It records the runtime mass/axle-load baseline, component COM, wheel masses and loads, active configurations, motor/gear-group state, differential graph, real shift transitions and optional ADS `dynamicMotorLoad` when ADS is present.

The diagnostic code is temporary and must be removed before a stable release.
'''
if needle not in s:
    raise SystemExit('README insertion point not found')
s = s.replace(needle, insert, 1)
p.write_text(s, encoding='utf-8')

# Changelog: prepend the diagnostic/cleanup stage while preserving 0.0.0.2 history.
p = Path('CHANGELOG.md')
s = p.read_text(encoding='utf-8')
if not s.startswith('# Changelog\n'):
    raise SystemExit('Unexpected changelog header')
entry = '''# Changelog

## 0.0.0.3 - diagnostic prerelease

Cleanup and read-only runtime diagnostic build. **No drivetrain, mass, tyre or engine tuning is included in this version.**

### Source cleanup
- Fixed four I3D texture references that pointed to missing PNG files while the corresponding DDS assets were present.
- Corrected `$l10n_Yelow` references to the existing `$l10n_Yellow` key.
- Replaced the development `TEST` title on connection-hose configurations with a proper localized title.
- Corrected generator/dynamo translations and the Polish `Prądnica` label.
- Corrected swapped store labels for field and road tyre brands.
- Removed the obsolete fully commented alternative motor/transmission block.
- Compacted dead placeholder comments left by the Static Cabins patch while preserving the compatibility fix itself.
- Corrected the technical documentation so component mass is not mistaken for total runtime vehicle mass.

### Diagnostics
- Added temporary `debug/TractorDebugKit.lua`, scoped only to `c330m.xml`.
- Logs actual front/rear tyre loads and axle split after physics settles.
- Logs runtime component mass/defaultMass and component center of mass.
- Logs wheel mass, tire load/restLoad and key suspension/traction parameters.
- Logs active vehicle configurations, motor/gear/group state and differential graph.
- Traces real gear/group changes and flags quick A→B→A shift oscillation candidates.
- Reads ADS `dynamicMotorLoad` only when Advanced Damage System is present; there is no hard dependency.

### Explicitly unchanged
- Component mass values and center-of-mass values.
- Wheel radius, width, mass, friction and stiffness values.
- Engine torque curve, RPM limits and fuel usage.
- Gear ratios, groups and speed limits.
- Differential topology.
- Front/rear ballast masses.
- Static Cabins ADS/AIASF compatibility behavior.

### Test goal
Establish the real FS25 runtime baseline before changing mass distribution, ballast, engine, gearbox, tyres or suspension. Search the game log for `[TRACTORDBG]`.

'''
s = entry + s[len('# Changelog\n\n'):]
p.write_text(s, encoding='utf-8')

print('Diagnostic 0.0.0.3 setup validated')
