from pathlib import Path
import json
import xml.etree.ElementTree as ET

VERSION = "0.0.4.1"

# --- c330m.xml: add independent liquid ballast configuration ---
p = Path("c330m.xml")
s = p.read_text(encoding="utf-8")
if s.count('spring="12"') != 40 or s.count('damper="22"') != 40:
    raise SystemExit("Expected stable 0.0.4.0 dry tyre baseline spring=12 / damper=22 on 40 wheel entries")
if "<design24Configurations" in s:
    raise SystemExit("design24Configurations already exists")
marker = "<!-- Kolory Blach -->"
if marker not in s:
    raise SystemExit("Could not find insertion marker for design24Configurations")
liquid_cfg = '''<!-- Rear tyre liquid ballast (independent of metal wheel weights). -->\n\t<design24Configurations title="$l10n_LiquidBallast">\n\t\t<design24Configuration name="$l10n_ui_no" price="0"/>\n\t\t<design24Configuration name="$l10n_ui_yes" price="0"/>\n\t</design24Configurations>\n\n'''
s = s.replace(marker, liquid_cfg + marker, 1)
p.write_text(s, encoding="utf-8")
ET.parse(p)

# --- liquid ballast runtime layer ---
liquid_script = r'''-- C330LiquidBallast.lua
-- Ursus C-330/C-330M rear tyre liquid ballast prototype.
-- 0.0.4.1 prerelease: +132 kg per rear wheel and a conservative filled-tyre spring/damper step.
-- Dry tyre baseline stays spring=12 / damper=22.

C330LiquidBallast = C330LiquidBallast or {}

if not C330LiquidBallast.installed then
    C330LiquidBallast.installed = true

    local CFG = {
        targetFileSuffix = "c330m.xml",
        configurationName = "design24",
        enabledIndex = 2,
        rearWheelIndices = { [3] = true, [4] = true },
        waterMassPerWheel = 0.132, -- tonnes = 132 kg
        springRatio = 14 / 12,
        damperRatio = 26 / 22
    }

    local modDirectory = g_currentModDirectory
    local originalLoadFromXML = Wheel.loadFromXML

    local function endsWith(value, suffix)
        return value ~= nil and suffix ~= nil and string.sub(value, -string.len(suffix)) == suffix
    end

    local function isTargetVehicle(vehicle)
        if vehicle == nil or vehicle.configFileName == nil then
            return false
        end
        if modDirectory ~= nil and string.sub(vehicle.configFileName, 1, string.len(modDirectory)) ~= modDirectory then
            return false
        end
        return endsWith(vehicle.configFileName, CFG.targetFileSuffix)
    end

    local function getConfigIndex(vehicle)
        local configurations = vehicle ~= nil and vehicle.configurations or nil
        return configurations ~= nil and tonumber(configurations[CFG.configurationName]) or 1
    end

    local function scaleNumber(tbl, key, factor)
        if tbl ~= nil and type(tbl[key]) == "number" then
            tbl[key] = tbl[key] * factor
        end
    end

    Wheel.loadFromXML = function(wheel, ...)
        local ok = originalLoadFromXML(wheel, ...)
        if not ok then
            return ok
        end

        local vehicle = wheel.vehicle
        if not isTargetVehicle(vehicle)
            or getConfigIndex(vehicle) ~= CFG.enabledIndex
            or not CFG.rearWheelIndices[wheel.wheelIndex] then
            return ok
        end

        wheel.additionalMass = (tonumber(wheel.additionalMass) or 0) + CFG.waterMassPerWheel

        local physics = wheel.physics
        if physics ~= nil then
            scaleNumber(physics, "spring", CFG.springRatio)
            scaleNumber(physics, "damperCompressionLowSpeed", CFG.damperRatio)
            scaleNumber(physics, "damperCompressionHighSpeed", CFG.damperRatio)
            scaleNumber(physics, "damperRelaxationLowSpeed", CFG.damperRatio)
            scaleNumber(physics, "damperRelaxationHighSpeed", CFG.damperRatio)
        end

        Logging.info(
            "[C330WATER] applied rear wheel=%d addMass=%.3f spring=%s damperRelaxLS=%s dryBase=12/22 targetApprox=14/26",
            wheel.wheelIndex,
            CFG.waterMassPerWheel,
            physics ~= nil and tostring(physics.spring) or "n/a",
            physics ~= nil and tostring(physics.damperRelaxationLowSpeed) or "n/a"
        )

        return ok
    end

    Logging.info("[C330WATER] 0.0.4.1 liquid ballast layer installed (+132 kg/rear wheel; targetApprox spring=14 damper=26)")
end
'''
Path("Scripts/C330LiquidBallast.lua").write_text(liquid_script, encoding="utf-8")

# --- TyreDebugKit: restore for the prerelease and expose the liquid-ballast configuration ---
p = Path("debug/TyreDebugKit.lua")
s = p.read_text(encoding="utf-8")
s = s.replace("0.0.3.5 damper=22 physical test prerelease", "0.0.4.1 liquid-ballast physical test prerelease")
s = s.replace("read-only damper-test trace", "read-only liquid-ballast trace")
s = s.replace("damper-test trace", "liquid-ballast trace")
old = '"[TYREDBG][CONFIG] reason=%s wheel=%s motor=%s design3=%s vehicleType=%s totalMass=%s speed=%s",\n            tostring(reason),\n            tostring(getConfig(vehicle, "wheel")),\n            tostring(getConfig(vehicle, "motor")),\n            tostring(getConfig(vehicle, "design3")),\n            tostring(getConfig(vehicle, "vehicleType")),\n            vehicle.getTotalMass ~= nil and fmt(vehicle:getTotalMass(), 3) or "n/a",\n            fmt(getSpeed(vehicle), 2)'
new = '"[TYREDBG][CONFIG] reason=%s wheel=%s motor=%s design3=%s liquidBallast=%s vehicleType=%s totalMass=%s speed=%s",\n            tostring(reason),\n            tostring(getConfig(vehicle, "wheel")),\n            tostring(getConfig(vehicle, "motor")),\n            tostring(getConfig(vehicle, "design3")),\n            tostring(getConfig(vehicle, "design24")),\n            tostring(getConfig(vehicle, "vehicleType")),\n            vehicle.getTotalMass ~= nil and fmt(vehicle:getTotalMass(), 3) or "n/a",\n            fmt(getSpeed(vehicle), 2)'
if old not in s:
    raise SystemExit("Could not update TyreDebugKit CONFIG line")
s = s.replace(old, new, 1)
p.write_text(s, encoding="utf-8")

# --- modDesc.xml ---
p = Path("modDesc.xml")
s = p.read_text(encoding="utf-8")
if "<version>0.0.4.0</version>" not in s:
    raise SystemExit("Expected 0.0.4.0 modDesc version not found")
s = s.replace("<version>0.0.4.0</version>", f"<version>{VERSION}</version>", 1)

# Temporary diagnostics + production/runtime layers.
old_sources = '''    <!-- Temporary read-only tyre/suspension diagnostics for 0.0.3.1 prerelease. -->\n    <extraSourceFiles>\n            <sourceFile filename="Scripts/C330TransmissionFix.lua" />\n    </extraSourceFiles>'''
new_sources = '''    <!-- 0.0.4.1 liquid-ballast prototype + temporary read-only tyre diagnostics. -->\n    <extraSourceFiles>\n        <sourceFile filename="Scripts/C330LiquidBallast.lua" />\n        <sourceFile filename="debug/TyreDebugKit.lua" />\n        <sourceFile filename="Scripts/C330TransmissionFix.lua" />\n    </extraSourceFiles>'''
if old_sources not in s:
    raise SystemExit("Unexpected extraSourceFiles block")
s = s.replace(old_sources, new_sources, 1)

l10n_marker = "\t</l10n>"
if l10n_marker not in s:
    raise SystemExit("l10n closing tag not found")
liquid_l10n = '''\t\t<text name="LiquidBallast">\n\t\t\t<en>Water in rear tyres</en>\n\t\t\t<pl>Woda w tylnych oponach</pl>\n\t\t\t<de>Wasser in den Hinterreifen</de>\n\t\t\t<fr>Eau dans les pneus arrière</fr>\n\t\t</text>\n'''
s = s.replace(l10n_marker, liquid_l10n + l10n_marker, 1)
p.write_text(s, encoding="utf-8")
ET.parse(p)

# --- README ---
p = Path("README.md")
s = p.read_text(encoding="utf-8")
s = s.replace(
    "**0.0.4.0 – C-330 dry tyre physics milestone**",
    "**0.0.4.1 – C-330 rear tyre liquid ballast prototype**",
    1,
)
p.write_text(s, encoding="utf-8")

# --- CHANGELOG ---
p = Path("CHANGELOG.md")
s = p.read_text(encoding="utf-8")
entry = '''## 0.0.4.1 - C-330 rear tyre liquid ballast prototype\n\nFirst functional prerelease for water ballast in the rear tyres.\n\n### Independent shop configuration\n- Adds **Water in rear tyres: No / Yes** as `design24`, independent of the existing metal wheel-weight selection.\n- The water state therefore combines with the dry wheel, Small, Big and Both metal-weight variants instead of replacing them.\n\n### Physical mass\n- Adds **132 kg per rear wheel** when enabled, for **264 kg total liquid ballast**.\n- The mass is applied to the rear wheel object before wheel physics is finalized, so it adds to any existing metal wheel mass.\n- Expected unladen/no-metal total: about **1.939 t**, with the added 264 kg on the rear axle.\n\n### Preliminary filled-tyre response\n- Dry tyre baseline remains **spring=12 / damper=22**.\n- Filled rear tyres are scaled to approximately **spring=14 / damper=26**.\n- `suspTravel=0.07` remains unchanged.\n- This is an intentionally conservative first test point, not a final water-filled tyre model.\n\n### Diagnostics\n- Temporarily restores read-only `TyreDebugKit.lua`.\n- Adds `[C330WATER]` startup/application logging.\n- Diagnostics expose `design24`, wheel mass/additional mass, spring/damper and MudSystemPhysics pressure.\n\n### Explicitly unchanged\n- Front tyre physics stay on the dry 12/22 baseline.\n- Wheel geometry, nominal radii/widths, stiffness/friction values and MudSystemPhysics pressure logic are not overwritten.\n- Base tractor mass/COM and factory metal ballast remain unchanged.\n- Engine, transmission, differential and ADS protection remain unchanged.\n\n'''
if not s.startswith("# Changelog\n\n"):
    raise SystemExit("Unexpected CHANGELOG header")
s = "# Changelog\n\n" + entry + s[len("# Changelog\n\n"):]
p.write_text(s, encoding="utf-8")

# --- release metadata ---
release = {
    "version": VERSION,
    "tag": VERSION,
    "title": "0.0.4.1 - C-330 rear tyre liquid ballast prototype",
    "prerelease": True,
    "zipName": "FS25_UrsusC330_330M_4x2.zip",
}
Path(".release/release.json").write_text(json.dumps(release, indent=2) + "\n", encoding="utf-8")

notes = '''## Ursus C-330 / C-330M 0.0.4.1\n\n**First functional rear-tyre water ballast prototype.**\n\n### New independent option\n- **Water in rear tyres: No / Yes**\n- Can be combined with existing metal rear wheel weights.\n\n### Prototype physics\n- **+132 kg per rear wheel** = **+264 kg total**.\n- Dry rear tyre remains **spring 12 / damper 22**.\n- Water-filled rear tyre is approximately **spring 14 / damper 26**.\n- Suspension travel remains **0.07 m**.\n\nThe filled-tyre spring/damper values are a conservative first test point, not a final target. MudSystemPhysics pressure/radius/friction behavior is left intact.\n\n### Suggested first test\nUse basic Polowe tyres, no metal wheel weights or attachments. Compare Water **Off vs On** at settled **2.40 bar** and **1.00 bar** using the established 10 km/h obstacle route plus the single-board Vmax pass. With water On and no metal weights, static total mass should be about **1.939 t**. Send the complete `log.txt`.\n\nTemporary `TyreDebugKit` is restored for this prerelease. Engine/transmission/ADS, base mass/COM and metal ballast are unchanged.\n'''
Path(".release/notes.md").write_text(notes, encoding="utf-8")

print("Prepared 0.0.4.1 liquid ballast prototype")
