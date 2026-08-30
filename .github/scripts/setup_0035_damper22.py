from pathlib import Path
import json
import xml.etree.ElementTree as ET

VERSION = "0.0.3.5"

# Restore the selected spring baseline from the A/B control and change only damper as the new test variable.
p = Path("c330m.xml")
s = p.read_text(encoding="utf-8")
spring_count = s.count('spring="15"')
damper_count = s.count('damper="25"')
if spring_count != 40:
    raise SystemExit(f"Expected 40 spring=15 entries in 0.0.3.4 control, found {spring_count}")
if damper_count != 40:
    raise SystemExit(f"Expected 40 damper=25 entries, found {damper_count}")
s = s.replace('spring="15"', 'spring="12"')
s = s.replace('damper="25"', 'damper="22"')
if 'spring="15"' in s or 'damper="25"' in s:
    raise SystemExit("Not all wheel spring/damper values were updated")
p.write_text(s, encoding="utf-8")
ET.parse(p)
print(f"Restored spring baseline on {spring_count} entries: 15 -> 12")
print(f"Changed damper on {damper_count} entries: 25 -> 22")

# Keep read-only tyre logger, only update its build marker.
p = Path("debug/TyreDebugKit.lua")
s = p.read_text(encoding="utf-8")
s = s.replace("0.0.3.4", VERSION)
s = s.replace("spring-control A/B prerelease", "damper=22 physical test prerelease")
s = s.replace("spring-control trace", "damper-test trace")
p.write_text(s, encoding="utf-8")

# Mod version.
p = Path("modDesc.xml")
s = p.read_text(encoding="utf-8")
if "<version>0.0.3.4</version>" not in s:
    raise SystemExit("Expected 0.0.3.4 modDesc version not found")
s = s.replace("<version>0.0.3.4</version>", f"<version>{VERSION}</version>", 1)
p.write_text(s, encoding="utf-8")
ET.parse(p)

# README marker.
p = Path("README.md")
s = p.read_text(encoding="utf-8")
s = s.replace(
    "**0.0.3.4 – C-330 spring=15 A/B control prerelease**",
    "**0.0.3.5 – C-330 damper=22 tyre test prerelease**",
    1,
)
p.write_text(s, encoding="utf-8")

# Changelog.
p = Path("CHANGELOG.md")
s = p.read_text(encoding="utf-8")
entry = '''## 0.0.3.5 - C-330 damper=22 tyre test\n\nFirst isolated damping test after the standardized spring A/B comparison selected **spring=12** as the new tyre-spring baseline.\n\n### Baseline restoration\n- Common wheel spring **15 -> 12** on all 40 wheel physics entries.\n- This is not a new spring experiment; it restores the selected 0.0.3.3 baseline after the 0.0.3.4 control run.\n\n### Isolated damping change\n- Common wheel damper **25 -> 22** on all 40 wheel physics entries.\n- The value is intentionally conservative. With spring reduced from 15 to 12, maintaining approximately the same classical damping ratio would scale damping by sqrt(12/15), giving about 22.36 from the previous 25.\n- Expected runtime damper components should decrease proportionally from the 0.0.3.3 baseline.\n\n### Explicitly unchanged\n- `suspTravel=0.07`, initialCompression, forcePointRatio and wheel geometry.\n- MudSystemPhysics pressure/radius/friction behavior.\n- Wheel masses, factory ballast, tractor mass/COM.\n- Engine, transmission controller, ADS protection and differential.\n\n### Test protocol\nUse the established standardized route: board set + pallet truck + campfire at cruise control **10 km/h**, then the single board at **Vmax**, at settled **2.40 bar** and **1.00 bar**. Compare directly against the 0.0.3.3 spring=12 / damper=25 log.\n\n### Decision target\nPrefer damper=22 only if it preserves or improves peak wheel loads/contact time while avoiding additional secondary bounce after obstacles. Otherwise return to 25 or test an intermediate value.\n\n'''
if not s.startswith("# Changelog\n\n"):
    raise SystemExit("Unexpected CHANGELOG header")
s = "# Changelog\n\n" + entry + s[len("# Changelog\n\n"):]
p.write_text(s, encoding="utf-8")

release = {
    "version": VERSION,
    "tag": VERSION,
    "title": "0.0.3.5 - C-330 damper=22 tyre test",
    "prerelease": True,
    "zipName": "FS25_UrsusC330_330M_4x2.zip",
}
Path(".release/release.json").write_text(json.dumps(release, indent=2) + "\n", encoding="utf-8")

notes = '''## Ursus C-330 / C-330M 0.0.3.5\n\n**First isolated damper test on the selected spring=12 tyre baseline.**\n\n### Changes\n- Restore selected spring baseline: **15 -> 12** (runtime expected ~150 -> 120).\n- New test variable only: common wheel damper **25 -> 22**.\n\nThe damper step is intentionally small. After reducing spring from 15 to 12, a simple constant-damping-ratio estimate gives 25 × sqrt(12/15) ≈ 22.36, so 22 is a useful first measured point rather than an arbitrary large change.\n\n### Repeat the standardized route\n1. Basic Polowe C-330, no ballast/attachment changes.\n2. Settle at **2.40 bar**.\n3. Board set + pallet truck + campfire at cruise control **10 km/h**.\n4. Single board at **Vmax**.\n5. Settle at **1.00 bar** and repeat.\n6. Keep obstacle order and line as consistent as practical and send the complete `log.txt`.\n\n`suspTravel=0.07`, wheel geometry/traction, MudSystemPhysics, mass/COM/ballast, engine/transmission/ADS and differential are unchanged.\n'''
Path(".release/notes.md").write_text(notes, encoding="utf-8")
