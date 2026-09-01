from pathlib import Path
import json
import re
import xml.etree.ElementTree as ET

VERSION = "0.0.4.3"

# --- c330m.xml: normalize only clearly material shop costs. No physics edits. ---
p = Path("c330m.xml")
s = p.read_text(encoding="utf-8")

# Rear metal ballast is currently embedded in wheelConfiguration variants.
wheel_prices = {
    "LIZARD_DEFAULT": 0,
    "LIZARD_WIDE": 100,          # +40 kg axle
    "LIZARD_WEIGHTS": 300,       # +144 kg axle
    "LIZARD_WIDEWEIGHT": 400,    # +184 kg axle
    "LIZARD_WIDEWEIGHTS": 300,   # +144 kg axle, alternate visual
    "LIZARD2_DEFAULT": 0,
    "LIZARD2_WIDE": 100,
    "LIZARD2_WEIGHTS": 300,
    "LIZARD2_WIDEWEIGHT": 400,
    "LIZARD2_WIDEWEIGHTS": 300,
}
for save_id, price in wheel_prices.items():
    pattern = re.compile(r'(<wheelConfiguration\b[^>]*?\bprice=")([0-9.]+)("[^>]*?\bsaveId="' + re.escape(save_id) + r'"[^>]*>)')
    s, n = pattern.subn(r'\g<1>' + str(price) + r'\g<3>', s, count=1)
    if n != 1:
        raise SystemExit(f"Unable to update wheel price for {save_id}: {n}")

# Loader console: substantial mounting hardware. Keep both supported Yes variants equal.
front_start = s.index("<frontloaderConfigurations>")
front_end = s.index("</frontloaderConfigurations>", front_start) + len("</frontloaderConfigurations>")
front = s[front_start:front_end]
front, n = re.subn(r'(<frontloaderConfiguration\s+name="\$l10n_ui_yes"\s+price=")300("[^>]*>)', r'\g<1>600\g<2>', front)
if n != 2:
    raise SystemExit(f"Expected two frontloader Yes variants at 300, found {n}")
s = s[:front_start] + front + s[front_end:]

# Cabin set: no-cabin stays free, nine actual cabin variants get one moderate hardware price.
vt_start = s.index("<vehicleTypeConfigurations>")
vt_end = s.index("</vehicleTypeConfigurations>", vt_start) + len("</vehicleTypeConfigurations>")
vt = s[vt_start:vt_end]
# All numbered cabin variants are currently price=0; do not change first $l10n_ui_no variant.
vt, n = re.subn(r'(<vehicleTypeConfiguration\s+name="[1-9]"\s+price=")0("\s+vehicleType="ursus">)', r'\g<1>500\g<2>', vt)
if n != 9:
    raise SystemExit(f"Expected nine numbered cabin variants, found {n}")
s = s[:vt_start] + vt + s[vt_end:]

p.write_text(s, encoding="utf-8")
ET.parse(p)

# --- modDesc: version, remove tyre diagnostics, add local shop-order helper. ---
p = Path("modDesc.xml")
s = p.read_text(encoding="utf-8")
if "<version>0.0.4.2</version>" not in s:
    raise SystemExit("Expected modDesc 0.0.4.2")
s = s.replace("<version>0.0.4.2</version>", f"<version>{VERSION}</version>", 1)
s = s.replace("    <!-- 0.0.4.1 liquid-ballast prototype + temporary read-only tyre diagnostics. -->\n", "    <!-- Stable drivetrain + final liquid ballast + local C-330 shop ordering. -->\n", 1)
s = s.replace('        <sourceFile filename="debug/TyreDebugKit.lua" />\n', "")
if 'Scripts/C330ShopOrder.lua' not in s:
    s = s.replace('        <sourceFile filename="Scripts/C330LiquidBallast.lua" />\n', '        <sourceFile filename="Scripts/C330LiquidBallast.lua" />\n        <sourceFile filename="Scripts/C330ShopOrder.lua" />\n', 1)
p.write_text(s, encoding="utf-8")
ET.parse(p)

# Tyre diagnostics are finished; do not ship the temporary logger anymore.
dbg = Path("debug/TyreDebugKit.lua")
if dbg.exists():
    dbg.unlink()

# Mark water script as finalized for this cleanup build; do not change physical ratios/mass.
p = Path("Scripts/C330LiquidBallast.lua")
s = p.read_text(encoding="utf-8")
s = s.replace("0.0.4.2 prerelease", "0.0.4.3 shop-cleanup build", 1)
s = s.replace("[C330WATER] 0.0.4.2 liquid ballast layer installed", "[C330WATER] final liquid ballast layer installed")
p.write_text(s, encoding="utf-8")

# README development marker.
p = Path("README.md")
s = p.read_text(encoding="utf-8")
for old in [
    "**0.0.4.2 – C-330 water-ballast damper=30 test**",
    "**0.0.4.1 – C-330 rear tyre liquid ballast prototype**",
    "**0.0.4.0 – C-330 dry tyre physics milestone**",
]:
    if old in s:
        s = s.replace(old, "**0.0.4.3 – C-330 shop cleanup test**", 1)
        break
p.write_text(s, encoding="utf-8")

# Changelog.
p = Path("CHANGELOG.md")
s = p.read_text(encoding="utf-8")
entry = '''## 0.0.4.3 - C-330 shop cleanup test\n\nShop/configuration cleanup prerelease after the mass, dry-tyre and liquid-ballast physics milestones.\n\n### Shop order\n- Adds a **C-330-only** shop ordering hook. It does not alter global GIANTS configuration priorities or other mods.\n- Intended top order: **Engine -> Wheels -> Water -> Front ballast -> Cabin -> Loader console**, then remaining equipment roughly from the front of the tractor to the rear.\n- Rear metal wheel weights remain embedded in the wheel selector in this cleanup because their geometry/mass is implemented inside `LizardBack.xml`; separating them would be a physics/save-format refactor, not a safe cleanup.\n\n### Prices\n- Water in rear tyres: **0** (free, unchanged).\n- Rear metal ballast variants per tyre family: **0 / 100 / 300 / 400 / 300** for none / +40 / +144 / +184 / alternate +144 kg.\n- Front 42 kg ballast: **100** (unchanged).\n- Cabin variants: **500**; no cabin remains 0.\n- Loader console: **600**; no console remains 0.\n- Existing small-accessory prices are retained where already plausible.\n\n### Cleaning\n- Removes the temporary `TyreDebugKit` now that tyre and water tuning is complete.\n- Final liquid-ballast physics remains **+132 kg/rear wheel, spring 14, damper 30**.\n- Dry tyres remain **spring 12 / damper 22 / suspTravel 0.07**.\n- No drivetrain, mass/COM, ADS, tyre or ballast physics changes.\n\n'''
if not s.startswith("# Changelog\n\n"):
    raise SystemExit("Unexpected changelog header")
s = "# Changelog\n\n" + entry + s[len("# Changelog\n\n"):]
p.write_text(s, encoding="utf-8")

release = {
    "version": VERSION,
    "tag": VERSION,
    "title": "0.0.4.3 - C-330 shop cleanup test",
    "prerelease": True,
    "zipName": "FS25_UrsusC330_330M_4x2.zip"
}
Path(".release/release.json").write_text(json.dumps(release, indent=2) + "\n", encoding="utf-8")

notes = '''## Ursus C-330 / C-330M 0.0.4.3\n\n**Shop cleanup / ordering test.** Physics from 0.0.4.2 is unchanged.\n\n### Please verify in the shop\nExpected top sequence: **Engine -> Wheels -> Water -> Front ballast -> Cabin -> Loader console**. After that, remaining selectors should be much closer to a front-to-rear customization flow.\n\nKnown structural limitation: rear metal wheel weights are still selectable inside **Wheels**, because their meshes and physical mass are wheel sub-configurations. They were not rewritten during this safe cleaning pass.\n\n### Price cleanup\n- Water: **free (0)**.\n- Rear wheel ballast: **100 / 300 / 400 / 300** for +40 / +144 / +184 / alternate +144 kg.\n- Front 42 kg ballast: **100**.\n- Cabins: **500**.\n- Loader console: **600**.\n\n### Runtime cleanup\nThe temporary tyre diagnostic logger has been removed. Liquid ballast stays **+132 kg per rear wheel, spring 14 / damper 30**; dry tyres stay **12 / 22**.\n\nPlease send either a screenshot/list of the visible selector order plus a normal `log.txt`. The important log marker is `[C330SHOP] local C-330 shop order active`; if it is absent, the ordering hook did not identify the active ShopConfigScreen and we will adjust only that helper.\n'''
Path(".release/notes.md").write_text(notes, encoding="utf-8")

print("Prepared 0.0.4.3 shop cleanup test")
