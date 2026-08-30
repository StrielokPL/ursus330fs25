from pathlib import Path
import json
import xml.etree.ElementTree as ET

VERSION = "0.0.3.2"

# Refine the existing read-only tyre logger using fields proven by the 0.0.3.1 runtime log.
p = Path("debug/TyreDebugKit.lua")
s = p.read_text(encoding="utf-8")
s = s.replace("-- 0.0.3.1 diagnostic prerelease. Remove from the next stable release.",
              "-- 0.0.3.2 suspension-travel diagnostic prerelease. Remove from the next stable release.", 1)
s = s.replace("traceIntervalMs = 100,", "traceIntervalMs = 50,", 1)

anchor = '''    local function pressureSignature(fields)\n        if fields == nil or #fields == 0 then\n            return "<none>"\n        end\n        return table.concat(fields, "|")\n    end\n\n'''
insert = '''    local function pressureSignature(fields)\n        if fields == nil or #fields == 0 then\n            return "<none>"\n        end\n        return table.concat(fields, "|")\n    end\n\n    local function getMudSystemPressure(vehicle)\n        local system = rawget(_G, "TirePressureSystem")\n        if system ~= nil and system.getVehicleWheelPressureAverage ~= nil then\n            local ok, current, target, count = pcall(system.getVehicleWheelPressureAverage, system, vehicle)\n            if ok then\n                return tonumber(current), tonumber(target), tonumber(count)\n            end\n        end\n        return nil, nil, nil\n    end\n\n'''
if anchor not in s:
    raise SystemExit("pressureSignature anchor not found")
s = s.replace(anchor, insert, 1)

old = '''    local function logPressureState(vehicle, force)\n        local fields = collectPressureFields(vehicle)\n        local signature = pressureSignature(fields)\n\n        if not force and vehicle.tyreDbgPressureSignature == signature then\n            return\n        end\n        vehicle.tyreDbgPressureSignature = signature\n\n        if #fields == 0 then\n            Logging.info("[TYREDBG][PRESSURE] no pressure-like runtime fields discovered; MS HUD setting must be correlated with effective wheel physics below")\n            return\n        end\n\n        Logging.info("[TYREDBG][PRESSURE] %s", table.concat(fields, " ; "))\n    end\n'''
new = '''    local function logPressureState(vehicle, force)\n        local current, target, count = getMudSystemPressure(vehicle)\n        if current ~= nil and target ~= nil then\n            local signature = string.format("direct:%.2f:%.2f:%s", current, target, tostring(count or 0))\n            if not force and vehicle.tyreDbgPressureSignature == signature then\n                return\n            end\n            vehicle.tyreDbgPressureSignature = signature\n            Logging.info(\n                "[TYREDBG][PRESSURE] current=%.3f target=%.3f wheels=%s source=TirePressureSystem",\n                current, target, tostring(count or 0)\n            )\n            return\n        end\n\n        local fields = collectPressureFields(vehicle)\n        local signature = pressureSignature(fields)\n\n        if not force and vehicle.tyreDbgPressureSignature == signature then\n            return\n        end\n        vehicle.tyreDbgPressureSignature = signature\n\n        if #fields == 0 then\n            Logging.info("[TYREDBG][PRESSURE] no pressure-like runtime fields discovered; MS unavailable or not exposing pressure state")\n            return\n        end\n\n        Logging.info("[TYREDBG][PRESSURE] fallback %s", table.concat(fields, " ; "))\n    end\n'''
if old not in s:
    raise SystemExit("logPressureState block not found")
s = s.replace(old, new, 1)

old = '''        local suspensionLength = firstValue(\n            physics.suspensionLength,\n            physics.suspLength,\n            wheel.suspensionLength,\n            wheel.suspLength\n        )\n'''
new = '''        local suspensionLength = firstValue(\n            wheel.lastSuspensionLength,\n            physics.suspensionLength,\n            physics.suspLength,\n            wheel.suspensionLength,\n            wheel.suspLength\n        )\n'''
if old not in s:
    raise SystemExit("suspensionLength block not found")
s = s.replace(old, new, 1)

old = '''            "[TYREDBG][WHEEL] axle=%s index=%d cfg=%s xml=%s load=%s rest=%s ratio=%s wheelMass=%s addMass=%s physicsMass=%s radiusWheel=%s radiusPhysics=%s width=%s maxDef=%s suspTravel=%s compression=%s suspLength=%s spring=%s damper=%s initialCompression=%s forcePointRatio=%s maxLong=%s maxLat=%s maxLatLoad=%s friction=%s localXYZ=%s/%s/%s",\n'''
new = '''            "[TYREDBG][WHEEL] axle=%s index=%d cfg=%s xml=%s load=%s rest=%s ratio=%s wheelMass=%s addMass=%s physicsMass=%s radiusWheel=%s radiusPhysics=%s radiusOriginal=%s tpRadius=%s width=%s maxDef=%s suspTravel=%s compression=%s suspLength=%s spring=%s springMul=%s damperCompLS=%s damperCompHS=%s damperCompThr=%s damperRelaxLS=%s damperRelaxHS=%s damperRelaxThr=%s initialCompression=%s forcePointRatio=%s maxLong=%s maxLat=%s maxLatLoad=%s friction=%s localXYZ=%s/%s/%s",\n'''
if old not in s:
    raise SystemExit("WHEEL format string not found")
s = s.replace(old, new, 1)

old_args = '''            fmt(wheel.radius, 4),\n            fmt(physics.radius, 4),\n            fmt(firstValue(wheel.width, physics.width), 4),\n            fmt(getVisualMaxDeformation(wheel), 4),\n            fmt(physics.suspTravel, 4),\n            fmt(compression, 4),\n            fmt(suspensionLength, 4),\n            fmt(physics.spring, 3),\n            fmt(physics.damper, 3),\n            fmt(physics.initialCompression, 3),\n'''
new_args = '''            fmt(wheel.radius, 4),\n            fmt(physics.radius, 4),\n            fmt(physics.radiusOriginal, 4),\n            fmt(physics.__tpDesiredRadius, 4),\n            fmt(firstValue(wheel.width, physics.width), 4),\n            fmt(getVisualMaxDeformation(wheel), 4),\n            fmt(physics.suspTravel, 4),\n            fmt(compression, 4),\n            fmt(suspensionLength, 4),\n            fmt(physics.spring, 3),\n            fmt(physics.springMultiplier, 3),\n            fmt(physics.damperCompressionLowSpeed, 3),\n            fmt(physics.damperCompressionHighSpeed, 3),\n            fmt(physics.damperCompressionLowSpeedThreshold, 4),\n            fmt(physics.damperRelaxationLowSpeed, 3),\n            fmt(physics.damperRelaxationHighSpeed, 3),\n            fmt(physics.damperRelaxationLowSpeedThreshold, 4),\n            fmt(physics.initialCompression, 3),\n'''
if old_args not in s:
    raise SystemExit("WHEEL argument block not found")
s = s.replace(old_args, new_args, 1)

old_trace_preamble = '''        local fy1, fy2 = getWheelY(vehicle, 1), getWheelY(vehicle, 2)\n        local ry1, ry2 = getWheelY(vehicle, 3), getWheelY(vehicle, 4)\n        local frontY = fy1 ~= nil and fy2 ~= nil and (fy1 + fy2) * 0.5 or nil\n        local rearY = ry1 ~= nil and ry2 ~= nil and (ry1 + ry2) * 0.5 or nil\n\n        Logging.info(\n            "[TYREDBG][TRACE] t=%d wheelCfg=%s speed=%s FL=%s FR=%s RL=%s RR=%s front=%s rear=%s frontY=%s rearY=%s",\n'''
new_trace_preamble = '''        local fy1, fy2 = getWheelY(vehicle, 1), getWheelY(vehicle, 2)\n        local ry1, ry2 = getWheelY(vehicle, 3), getWheelY(vehicle, 4)\n        local frontY = fy1 ~= nil and fy2 ~= nil and (fy1 + fy2) * 0.5 or nil\n        local rearY = ry1 ~= nil and ry2 ~= nil and (ry1 + ry2) * 0.5 or nil\n        local w1, w2, w3, w4 = getWheel(vehicle, 1), getWheel(vehicle, 2), getWheel(vehicle, 3), getWheel(vehicle, 4)\n        local pCurrent, pTarget = getMudSystemPressure(vehicle)\n\n        Logging.info(\n            "[TYREDBG][TRACE] t=%d wheelCfg=%s speed=%s p=%s pTarget=%s FL=%s FR=%s RL=%s RR=%s front=%s rear=%s FLs=%s FRs=%s RLs=%s RRs=%s frontY=%s rearY=%s",\n'''
if old_trace_preamble not in s:
    raise SystemExit("TRACE preamble not found")
s = s.replace(old_trace_preamble, new_trace_preamble, 1)

old_trace_args = '''            tostring(getConfig(vehicle, "wheel")),\n            fmt(getSpeed(vehicle), 2),\n            fmt(fl, 3), fmt(fr, 3), fmt(rl, 3), fmt(rr, 3),\n            fmt(fl + fr, 3), fmt(rl + rr, 3),\n            fmt(frontY, 4), fmt(rearY, 4)\n'''
new_trace_args = '''            tostring(getConfig(vehicle, "wheel")),\n            fmt(getSpeed(vehicle), 2),\n            fmt(pCurrent, 3), fmt(pTarget, 3),\n            fmt(fl, 3), fmt(fr, 3), fmt(rl, 3), fmt(rr, 3),\n            fmt(fl + fr, 3), fmt(rl + rr, 3),\n            fmt(w1 ~= nil and w1.lastSuspensionLength or nil, 4),\n            fmt(w2 ~= nil and w2.lastSuspensionLength or nil, 4),\n            fmt(w3 ~= nil and w3.lastSuspensionLength or nil, 4),\n            fmt(w4 ~= nil and w4.lastSuspensionLength or nil, 4),\n            fmt(frontY, 4), fmt(rearY, 4)\n'''
if old_trace_args not in s:
    raise SystemExit("TRACE argument block not found")
s = s.replace(old_trace_args, new_trace_args, 1)

s = s.replace(
    'Logging.info("[TYREDBG] TyreDebugKit 0.0.3.1 installed; read-only; target=%s trace=%dms detail=%dms pressureScan=%dms",',
    'Logging.info("[TYREDBG] TyreDebugKit 0.0.3.2 installed; read-only suspension trace; target=%s trace=%dms detail=%dms pressureScan=%dms",',
    1,
)
p.write_text(s, encoding="utf-8")

# modDesc version only; logger remains temporary and read-only.
p = Path("modDesc.xml")
s = p.read_text(encoding="utf-8")
if "<version>0.0.3.1</version>" not in s:
    raise SystemExit("Expected 0.0.3.1 modDesc version not found")
s = s.replace("<version>0.0.3.1</version>", f"<version>{VERSION}</version>", 1)
p.write_text(s, encoding="utf-8")
ET.parse(p)

# README marker.
p = Path("README.md")
s = p.read_text(encoding="utf-8")
s = s.replace(
    "**0.0.3.1 – C-330 tyre / pressure diagnostic prerelease**",
    "**0.0.3.2 – C-330 suspension-travel diagnostic prerelease**",
    1,
)
p.write_text(s, encoding="utf-8")

# Changelog.
p = Path("CHANGELOG.md")
s = p.read_text(encoding="utf-8")
entry = '''## 0.0.3.2 - C-330 suspension-travel diagnostic prerelease\n\nSecond read-only instrumentation pass. **No physical value is changed from stable 0.0.3.0 / diagnostic 0.0.3.1.**\n\n### What 0.0.3.1 proved\n- MudSystemPhysics pressure switching is active and persisted: road **2.40 bar**, field **1.00 bar**.\n- At 2.40 bar the runtime physics radius settles at about **0.3892 m front / 0.6692 m rear**.\n- At 1.00 bar it settles at about **0.3760 m front / 0.6392 m rear**, i.e. the MS 6% minimum-radius clamp is reached.\n- Pressure changes radius progressively; the C-330 wheel `spring` remains **150 runtime** throughout.\n- Runtime discovery exposed `wheel.lastSuspensionLength` plus split compression/rebound damper fields that the first detail logger did not sample dynamically.\n- `wheel=1` (Polowe basic) and `wheel=6` (Szosowe basic) showed the same runtime physical values, so further suspension tests only need one basic tyre family.\n- Right-side obstacle hits produced large transient load transfer and occasional zero tire load on the opposite wheel, proving the current setup can enter a real unload/rebound phase.\n\n### Diagnostic refinement\n- High-rate trace interval **100 -> 50 ms**.\n- Trace now records direct MudSystemPhysics current/target pressure when the public system API is present.\n- Trace now records FL/FR/RL/RR `lastSuspensionLength` independently.\n- Detailed wheel lines now expose `radiusOriginal`, pressure-requested radius, `springMultiplier`, and GIANTS split compression/rebound damper values and thresholds.\n- Legacy pressure-field scanning remains as a nil-safe fallback if MudSystemPhysics is absent or changes its API.\n\n### Test focus\nUse one basic tyre family only. Compare **2.40 bar** and **1.00 bar** over the same board-stack / stone-fire / pallet-truck route. For the one-sided obstacles keep using the right wheels. Similar approach speed is more important than additional tyre configurations.\n\n### Explicitly unchanged\n- Base mass/COM and factory metal ballast.\n- Wheel XML `spring=15`, `damper=25`, `suspTravel=0.07`, initialCompression, radius/width/stiffness/friction.\n- MudSystemPhysics itself.\n- Engine, transmission controller, ADS protection and differential.\n\n'''
if not s.startswith("# Changelog\n\n"):
    raise SystemExit("Unexpected CHANGELOG header")
s = "# Changelog\n\n" + entry + s[len("# Changelog\n\n"):]
p.write_text(s, encoding="utf-8")

release = {
    "version": VERSION,
    "tag": VERSION,
    "title": "0.0.3.2 - C-330 suspension-travel diagnostic test",
    "prerelease": True,
    "zipName": "FS25_UrsusC330_330M_4x2.zip",
}
Path(".release/release.json").write_text(json.dumps(release, indent=2) + "\n", encoding="utf-8")

notes = '''## Ursus C-330 / C-330M 0.0.3.2\n\n**Read-only suspension-travel diagnostic prerelease. No physical values changed.**\n\n0.0.3.1 showed that MudSystemPhysics already handles the 2.40/1.00 bar radius/friction layer independently of the C-330 wheel spring. This build measures the missing physical suspension/tire-compliance motion directly.\n\n### Test\nOne basic tyre family is enough; 0.0.3.1 confirmed Polowe/Szosowe share the same runtime physics.\n\n1. Set **2.40 bar**, let it settle, drive the same three-prop route.\n2. Set **1.00 bar**, let the pressure finish changing, repeat at roughly similar speeds.\n3. Keep the stone-fire and pallet-truck hits on the **right side** as before.\n4. Send the complete `log.txt`.\n\nThe log now includes pressure current/target and FL/FR/RL/RR suspension length every 50 ms plus the full GIANTS compression/rebound damper split.\n'''
Path(".release/notes.md").write_text(notes, encoding="utf-8")

# Regression assertions: physical safe points unchanged.
logger = Path("debug/TyreDebugKit.lua").read_text(encoding="utf-8")
assert "traceIntervalMs = 50" in logger
assert "lastSuspensionLength" in logger
assert "getVehicleWheelPressureAverage" in logger
assert "damperCompressionHighSpeed" in logger and "damperRelaxationHighSpeed" in logger
assert f"<version>{VERSION}</version>" in Path("modDesc.xml").read_text(encoding="utf-8")
c = Path("c330m.xml").read_text(encoding="utf-8")
assert '<component centerOfMass="0 0.1 -0.125" solverIterationCount="20" mass="792"/>' in c
assert 'initialCompression="50" suspTravel="0.07" spring="15" damper="25"' in c
assert 'initialCompression="20" suspTravel="0.07" spring="15" damper="25"' in c
assert json.loads(Path(".release/release.json").read_text(encoding="utf-8"))["prerelease"] is True
print("0.0.3.2 suspension trace diagnostic setup validated")
