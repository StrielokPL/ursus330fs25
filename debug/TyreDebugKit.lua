-- TyreDebugKit.lua
-- Temporary read-only tyre/suspension diagnostics for Ursus C-330 / C-330M.
-- 0.0.3.1 diagnostic prerelease. Remove from the next stable release.
-- Log prefix: [TYREDBG]

TyreDebugKit = TyreDebugKit or {}

if not TyreDebugKit.installed then
    TyreDebugKit.installed = true

    local CFG = {
        enabled = true,
        targetFileSuffixes = {"c330m.xml"},
        requireSameModDirectory = true,
        triggerWheelIndex = 4,
        frontWheelIndices = {1, 2},
        rearWheelIndices = {3, 4},
        settleDelayMs = 2500,
        traceIntervalMs = 100,
        detailIntervalMs = 500,
        pressureIntervalMs = 250
    }

    local modDirectory = g_currentModDirectory
    local originalWheelUpdate = Wheel.update

    local function endsWith(value, suffix)
        return value ~= nil and suffix ~= nil and string.sub(value, -string.len(suffix)) == suffix
    end

    local function isTargetVehicle(vehicle)
        if not CFG.enabled or vehicle == nil or vehicle.configFileName == nil then
            return false
        end

        if CFG.requireSameModDirectory
            and modDirectory ~= nil
            and string.sub(vehicle.configFileName, 1, string.len(modDirectory)) ~= modDirectory then
            return false
        end

        for _, suffix in ipairs(CFG.targetFileSuffixes) do
            if endsWith(vehicle.configFileName, suffix) then
                return true
            end
        end
        return false
    end

    local function getWheel(vehicle, index)
        if vehicle == nil or vehicle.getWheelFromWheelIndex == nil then
            return nil
        end
        return vehicle:getWheelFromWheelIndex(index)
    end

    local function safeTireLoad(wheel)
        local physics = wheel ~= nil and wheel.physics or nil
        if physics ~= nil and physics.getTireLoad ~= nil then
            return tonumber(physics:getTireLoad()) or 0
        end
        return 0
    end

    local function safeWheelMass(wheel)
        if wheel ~= nil and wheel.getMass ~= nil then
            return tonumber(wheel:getMass()) or 0
        end
        return 0
    end

    local function safeNumber(value)
        local n = tonumber(value)
        return n ~= nil and n or 0
    end

    local function fmt(value, digits)
        local n = tonumber(value)
        if n == nil then
            return "n/a"
        end
        return string.format("%." .. tostring(digits or 3) .. "f", n)
    end

    local function getSpeed(vehicle)
        if vehicle ~= nil and vehicle.getLastSpeed ~= nil then
            return tonumber(vehicle:getLastSpeed()) or 0
        end
        return 0
    end

    local function getConfig(vehicle, name)
        local configs = vehicle ~= nil and vehicle.configurations or nil
        return configs ~= nil and configs[name] or nil
    end

    local function getWheelLocalPosition(vehicle, wheel)
        local node = wheel ~= nil and (wheel.node or wheel.repr or wheel.driveNode) or nil
        local root = vehicle ~= nil and (vehicle.rootNode or (vehicle.components ~= nil and vehicle.components[1] ~= nil and vehicle.components[1].node)) or nil
        if node == nil or root == nil or localToLocal == nil then
            return nil, nil, nil
        end

        local ok, x, y, z = pcall(localToLocal, node, root, 0, 0, 0)
        if not ok then
            return nil, nil, nil
        end
        return tonumber(x), tonumber(y), tonumber(z)
    end

    local function firstValue(...)
        for i = 1, select("#", ...) do
            local value = select(i, ...)
            if value ~= nil then
                return value
            end
        end
        return nil
    end

    local function getVisualMaxDeformation(wheel)
        if wheel == nil then
            return nil
        end
        return firstValue(
            wheel.maxDeformation,
            wheel.tire ~= nil and wheel.tire.maxDeformation or nil,
            wheel.visualTire ~= nil and wheel.visualTire.maxDeformation or nil
        )
    end

    local function getWheelXmlName(wheel)
        if wheel == nil then
            return "n/a"
        end
        return tostring(firstValue(
            wheel.xmlFilename,
            wheel.xmlFileName,
            wheel.filename,
            wheel.fileName,
            wheel.tireFilename,
            wheel.tireFileName,
            "n/a"
        ))
    end

    local function isScalar(value)
        local t = type(value)
        return t == "number" or t == "string" or t == "boolean"
    end

    local function containsAny(text, tokens)
        local lower = string.lower(tostring(text or ""))
        for _, token in ipairs(tokens) do
            if string.find(lower, token, 1, true) ~= nil then
                return true
            end
        end
        return false
    end

    local PRESSURE_TOKENS = {"pressure", "inflation", "psi", "bar"}
    local DISCOVERY_TOKENS = {
        "pressure", "inflation", "psi", "bar",
        "spring", "damper", "susp", "compress", "deform",
        "radius", "load", "mass", "friction", "stiff"
    }

    local function scanRelevantScalars(tbl, path, tokens, depth, seen, out, maxEntries)
        if type(tbl) ~= "table" or depth < 0 or #out >= maxEntries then
            return
        end
        if seen[tbl] then
            return
        end
        seen[tbl] = true

        local keys = {}
        for key, _ in pairs(tbl) do
            if type(key) == "string" or type(key) == "number" then
                table.insert(keys, key)
            end
        end
        table.sort(keys, function(a, b) return tostring(a) < tostring(b) end)

        for _, key in ipairs(keys) do
            if #out >= maxEntries then
                break
            end
            local value = tbl[key]
            local keyText = tostring(key)
            local childPath = path .. "." .. keyText

            if isScalar(value) and containsAny(keyText, tokens) then
                table.insert(out, childPath .. "=" .. tostring(value))
            elseif type(value) == "table" and depth > 0 then
                local descend = containsAny(keyText, tokens)
                    or containsAny(path, {"pressure", "tire", "tyre", "wheel", "mud"})
                if descend then
                    scanRelevantScalars(value, childPath, tokens, depth - 1, seen, out, maxEntries)
                end
            end
        end
    end

    local function collectPressureFields(vehicle)
        local out = {}
        local seen = {}

        if vehicle ~= nil then
            local specKeys = {}
            for key, value in pairs(vehicle) do
                if type(key) == "string"
                    and type(value) == "table"
                    and string.sub(key, 1, 5) == "spec_"
                    and containsAny(key, {"pressure", "tire", "tyre", "wheel", "mud"}) then
                    table.insert(specKeys, key)
                end
            end
            table.sort(specKeys)
            for _, key in ipairs(specKeys) do
                scanRelevantScalars(vehicle[key], "vehicle." .. key, PRESSURE_TOKENS, 3, seen, out, 60)
            end
        end

        for index = 1, 4 do
            local wheel = getWheel(vehicle, index)
            if wheel ~= nil then
                scanRelevantScalars(wheel, "wheel" .. tostring(index), PRESSURE_TOKENS, 2, seen, out, 60)
                if wheel.physics ~= nil then
                    scanRelevantScalars(wheel.physics, "wheel" .. tostring(index) .. ".physics", PRESSURE_TOKENS, 2, seen, out, 60)
                end
            end
        end

        table.sort(out)
        return out
    end

    local function pressureSignature(fields)
        if fields == nil or #fields == 0 then
            return "<none>"
        end
        return table.concat(fields, "|")
    end

    local function logPressureState(vehicle, force)
        local fields = collectPressureFields(vehicle)
        local signature = pressureSignature(fields)

        if not force and vehicle.tyreDbgPressureSignature == signature then
            return
        end
        vehicle.tyreDbgPressureSignature = signature

        if #fields == 0 then
            Logging.info("[TYREDBG][PRESSURE] no pressure-like runtime fields discovered; MS HUD setting must be correlated with effective wheel physics below")
            return
        end

        Logging.info("[TYREDBG][PRESSURE] %s", table.concat(fields, " ; "))
    end

    local function scalarDiscoveryLine(wheel, index)
        if wheel == nil then
            return
        end

        local out = {}
        local seen = {}
        scanRelevantScalars(wheel, "wheel" .. tostring(index), DISCOVERY_TOKENS, 2, seen, out, 80)
        if wheel.physics ~= nil then
            scanRelevantScalars(wheel.physics, "wheel" .. tostring(index) .. ".physics", DISCOVERY_TOKENS, 2, seen, out, 80)
        end
        table.sort(out)

        if #out > 0 then
            Logging.info("[TYREDBG][DISCOVER] index=%d %s", index, table.concat(out, " ; "))
        else
            Logging.info("[TYREDBG][DISCOVER] index=%d no matching scalar fields", index)
        end
    end

    local function logWheelDetail(vehicle, index, axle)
        local wheel = getWheel(vehicle, index)
        local physics = wheel ~= nil and wheel.physics or nil
        if wheel == nil or physics == nil then
            Logging.info("[TYREDBG][WHEEL] axle=%s index=%d unavailable", axle, index)
            return
        end

        local x, y, z = getWheelLocalPosition(vehicle, wheel)
        local tireLoad = safeTireLoad(wheel)
        local restLoad = tonumber(physics.restLoad)
        local ratio = restLoad ~= nil and restLoad > 0 and tireLoad / restLoad or nil

        local compression = firstValue(
            physics.suspensionCompression,
            physics.compression,
            wheel.suspensionCompression,
            wheel.compression
        )
        local suspensionLength = firstValue(
            physics.suspensionLength,
            physics.suspLength,
            wheel.suspensionLength,
            wheel.suspLength
        )

        Logging.info(
            "[TYREDBG][WHEEL] axle=%s index=%d cfg=%s xml=%s load=%s rest=%s ratio=%s wheelMass=%s addMass=%s physicsMass=%s radiusWheel=%s radiusPhysics=%s width=%s maxDef=%s suspTravel=%s compression=%s suspLength=%s spring=%s damper=%s initialCompression=%s forcePointRatio=%s maxLong=%s maxLat=%s maxLatLoad=%s friction=%s localXYZ=%s/%s/%s",
            axle,
            index,
            tostring(getConfig(vehicle, "wheel")),
            getWheelXmlName(wheel),
            fmt(tireLoad, 3),
            fmt(restLoad, 3),
            fmt(ratio, 3),
            fmt(safeWheelMass(wheel), 3),
            fmt(wheel.additionalMass, 3),
            fmt(physics.mass, 3),
            fmt(wheel.radius, 4),
            fmt(physics.radius, 4),
            fmt(firstValue(wheel.width, physics.width), 4),
            fmt(getVisualMaxDeformation(wheel), 4),
            fmt(physics.suspTravel, 4),
            fmt(compression, 4),
            fmt(suspensionLength, 4),
            fmt(physics.spring, 3),
            fmt(physics.damper, 3),
            fmt(physics.initialCompression, 3),
            fmt(physics.forcePointRatio, 3),
            fmt(physics.maxLongStiffness, 3),
            fmt(physics.maxLatStiffness, 3),
            fmt(physics.maxLatStiffnessLoad, 3),
            fmt(physics.frictionScale, 3),
            fmt(x, 4), fmt(y, 4), fmt(z, 4)
        )
    end

    local function logAllWheelDetails(vehicle)
        logWheelDetail(vehicle, 1, "front")
        logWheelDetail(vehicle, 2, "front")
        logWheelDetail(vehicle, 3, "rear")
        logWheelDetail(vehicle, 4, "rear")
    end

    local function logConfiguration(vehicle, reason)
        Logging.info(
            "[TYREDBG][CONFIG] reason=%s wheel=%s motor=%s design3=%s vehicleType=%s totalMass=%s speed=%s",
            tostring(reason),
            tostring(getConfig(vehicle, "wheel")),
            tostring(getConfig(vehicle, "motor")),
            tostring(getConfig(vehicle, "design3")),
            tostring(getConfig(vehicle, "vehicleType")),
            vehicle.getTotalMass ~= nil and fmt(vehicle:getTotalMass(), 3) or "n/a",
            fmt(getSpeed(vehicle), 2)
        )
    end

    local function getWheelY(vehicle, index)
        local wheel = getWheel(vehicle, index)
        local _, y, _ = getWheelLocalPosition(vehicle, wheel)
        return y
    end

    local function logTrace(vehicle)
        local fl = safeTireLoad(getWheel(vehicle, 1))
        local fr = safeTireLoad(getWheel(vehicle, 2))
        local rl = safeTireLoad(getWheel(vehicle, 3))
        local rr = safeTireLoad(getWheel(vehicle, 4))
        local fy1, fy2 = getWheelY(vehicle, 1), getWheelY(vehicle, 2)
        local ry1, ry2 = getWheelY(vehicle, 3), getWheelY(vehicle, 4)
        local frontY = fy1 ~= nil and fy2 ~= nil and (fy1 + fy2) * 0.5 or nil
        local rearY = ry1 ~= nil and ry2 ~= nil and (ry1 + ry2) * 0.5 or nil

        Logging.info(
            "[TYREDBG][TRACE] t=%d wheelCfg=%s speed=%s FL=%s FR=%s RL=%s RR=%s front=%s rear=%s frontY=%s rearY=%s",
            g_time or 0,
            tostring(getConfig(vehicle, "wheel")),
            fmt(getSpeed(vehicle), 2),
            fmt(fl, 3), fmt(fr, 3), fmt(rl, 3), fmt(rr, 3),
            fmt(fl + fr, 3), fmt(rl + rr, 3),
            fmt(frontY, 4), fmt(rearY, 4)
        )
    end

    local function logSnapshot(vehicle, reason)
        Logging.info("[TYREDBG][SNAPSHOT] BEGIN reason=%s file=%s server=%s client=%s", tostring(reason), tostring(vehicle.configFileName), tostring(vehicle.isServer), tostring(vehicle.isClient))
        logConfiguration(vehicle, reason)
        logPressureState(vehicle, true)
        logAllWheelDetails(vehicle)
        for index = 1, 4 do
            scalarDiscoveryLine(getWheel(vehicle, index), index)
        end
        Logging.info("[TYREDBG][SNAPSHOT] END reason=%s", tostring(reason))
    end

    function Wheel:update(dt, currentUpdateIndex, groundWetness, force)
        originalWheelUpdate(self, dt, currentUpdateIndex, groundWetness, force)

        if (self.wheelIndex or 0) ~= CFG.triggerWheelIndex then
            return
        end

        local vehicle = self.vehicle
        if not isTargetVehicle(vehicle) or not vehicle.isAddedToPhysics then
            return
        end

        local now = g_time or 0
        if vehicle.tyreDbgFirstSeenTime == nil then
            vehicle.tyreDbgFirstSeenTime = now
        end

        local wheelCfg = getConfig(vehicle, "wheel")
        if vehicle.tyreDbgLastWheelConfig ~= wheelCfg then
            vehicle.tyreDbgLastWheelConfig = wheelCfg
            vehicle.tyreDbgSnapshotDone = false
            vehicle.tyreDbgFirstSeenTime = now
            vehicle.tyreDbgDiscoveryConfig = nil
            logConfiguration(vehicle, "wheel-config-change")
        end

        if not vehicle.tyreDbgSnapshotDone and now - vehicle.tyreDbgFirstSeenTime >= CFG.settleDelayMs then
            vehicle.tyreDbgSnapshotDone = true
            vehicle.tyreDbgDiscoveryConfig = wheelCfg
            logSnapshot(vehicle, "settled")
        end

        if vehicle.tyreDbgNextPressureCheck == nil or now >= vehicle.tyreDbgNextPressureCheck then
            vehicle.tyreDbgNextPressureCheck = now + CFG.pressureIntervalMs
            local before = vehicle.tyreDbgPressureSignature
            logPressureState(vehicle, false)
            if before ~= nil and vehicle.tyreDbgPressureSignature ~= before then
                logConfiguration(vehicle, "pressure-state-change")
                logAllWheelDetails(vehicle)
            end
        end

        if vehicle.tyreDbgNextTrace == nil or now >= vehicle.tyreDbgNextTrace then
            vehicle.tyreDbgNextTrace = now + CFG.traceIntervalMs
            logTrace(vehicle)
        end

        if vehicle.tyreDbgNextDetail == nil or now >= vehicle.tyreDbgNextDetail then
            vehicle.tyreDbgNextDetail = now + CFG.detailIntervalMs
            logAllWheelDetails(vehicle)
        end
    end

    Logging.info("[TYREDBG] TyreDebugKit 0.0.3.1 installed; read-only; target=%s trace=%dms detail=%dms pressureScan=%dms", table.concat(CFG.targetFileSuffixes, ","), CFG.traceIntervalMs, CFG.detailIntervalMs, CFG.pressureIntervalMs)
end
