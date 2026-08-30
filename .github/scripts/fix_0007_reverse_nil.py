from pathlib import Path

p = Path('Scripts/C330TransmissionFix.lua')
s = p.read_text(encoding='utf-8')
old = '''        if not isAutomaticC330(self)\n            or vanillaTarget == nil\n            or curGear == nil\n            or curGear <= 0\n            or gears == nil\n            or #gears < 1 then\n            return vanillaTarget\n        end\n'''
new = '''        if not isAutomaticC330(self)\n            or curGear == nil\n            or curGear <= 0\n            or gears == nil\n            or #gears < 1 then\n            return vanillaTarget\n        end\n'''
if old not in s:
    raise SystemExit('prediction guard pattern not found')
s = s.replace(old, new, 1)
old2 = '        local targetGear = vanillaTarget\n'
new2 = '        local targetGear = vanillaTarget or curGear\n'
if old2 not in s:
    raise SystemExit('targetGear pattern not found')
s = s.replace(old2, new2, 1)
p.write_text(s, encoding='utf-8')
assert 'or vanillaTarget == nil' not in s
assert 'local targetGear = vanillaTarget or curGear' in s
print('0.0.0.7 reverse nil-guard fix validated')
