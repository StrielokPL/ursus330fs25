-- TractorDebugKit.lua
-- Standardized read-only diagnostic toolkit for FS25 tractor tuning.
-- Temporary debug code: remove from stable release.
-- Adapted for Ursus C-330 / C-330M.
-- 0.0.2.2 MASS/COM TEST: validate calculated base component mass and longitudinal COM correction.
-- Log prefix: [TRACTORDBG]

TractorDebugKit = TractorDebugKit or {}

if not TractorDebugKit.installed then
    TractorDebugKit.installed = true

    local CFG = {
        enabled = true,
        targetFileSuffixes = {"c330m.xml"},
        requireSameModDirectory = true,
        frontWheelIndices = {1, 2},
        rearWheelIndices = {3, 4},
        triggerWheelIndex = 4,
        settleDelayMs = 3500,
        traceTransmissionChanges = false,
        oscillationWindowMs = 1800,
        periodicWheelTrace = false,
        periodicWheelTraceMs = 500,
        periodicEngineTrace = false,
        periodicEngineTraceMs = 750,
        readAdsDynamicLoad = false
    }

    local modDirectory = g_currentModDirectory
    local originalWheelUpdate = Wheel.update

    local function endsWith(value, suffix)
        return value ~= nil
            and suffix ~= nil
            and string.sub(value, -string.len(suffix)) == suffix
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

    local function getWheel(vehicle, index)
        if vehicle == nil or vehicle.getWheelFromWheelIndex == nil then
            return nil
        end
        return vehicle:getWheelFromWheelIndex(index)
    end

    local function sumLoads(vehicle, indices)
        local total = 0
        for _, index in ipairs(indices) do
            total = total + safeTireLoad(getWheel(vehicle, index))
        end
        return total
    end

    local function safeRuntimeMass(component)
        if component == nil or component.node == nil then
            return -1
        end
        if getMass ~= nil then
            return tonumber(getMass(component.node)) or -1
        end
        return tonumber(component.defaultMass) or -1
    end

    local function safeCOM(component)
        if component == nil or component.node == nil or getCenterOfMass == nil then
            return 0, 0, 0
        end
        local x, y, z = getCenterOfMass(component.node)
        return tonumber(x) or 0, tonumber(y) or 0, tonumber(z) or 0
    end

    local function getMotor(vehicle)
        local spec = vehicle ~= nil and vehicle.spec_motorized or nil
        return spec ~= nil and spec.motor or nil
    end

    local function getMotorRpm(motor)
        if motor == nil then
            return 0
        end
        if motor.getLastModulatedMotorRpm ~= nil then
            local value = tonumber(motor:getLastModulatedMotorRpm())
            if value ~= nil then
                return value
            end
        end
        return tonumber(motor.lastMotorRpm) or 0
    end

    local function getGear(motor)
        if motor == nil then
            return 0
        end
        return tonumber(motor.activeGearIndex)
            or tonumber(motor.currentGear)
            or tonumber(motor.gear)
            or 0
    end

    local function getGroup(motor)
        if motor == nil then
            return 0
        end
        return tonumber(motor.activeGearGroupIndex) or 0
    end

    local function getAdsLoad(vehicle)
        if not CFG.readAdsDynamicLoad or vehicle == nil then
            return nil
        end
        local spec = vehicle.spec_AdvancedDamageSystem
        if spec == nil or spec.dynamicMotorLoad == nil then
            return nil
        end
        return tonumber(spec.dynamicMotorLoad)
    end

    local function getSpeed(vehicle)
        if vehicle ~= nil and vehicle.getLastSpeed ~= nil then
            return tonumber(vehicle:getLastSpeed()) or 0
        end
        return 0
    end

    local function countAttached(vehicle)
        if vehicle == nil or vehicle.getAttachedImplements == nil then
            return 0
        end
        local implements = vehicle:getAttachedImplements()
        return implements ~= nil and #implements or 0
    end

    local function logConfigurations(vehicle)
        local configurations = vehicle ~= nil and vehicle.configurations or nil
        if configurations == nil then
            return
        end

        local keys = {}
        for key, value in pairs(configurations) do
            if type(key) == "string" and type(value) == "number" then
                table.insert(keys, key)
            end
        end
        table.sort(keys)

        for _, key in ipairs(keys) do
            Logging.info("[TRACTORDBG][CONFIG] %s=%s", key, tostring(configurations[key]))
        end
    end

    local function logComponents(vehicle)
        if vehicle.components == nil then
            return
        end

        for index, component in ipairs(vehicle.components) do
            local x, y, z = safeCOM(component)
            Logging.info(
                "[TRACTORDBG][COMP] index=%d runtimeMass=%.3ft defaultMass=%s COM=%.4f %.4f %.4f node=%s",
                index,
                safeRuntimeMass(component),
                tostring(component.defaultMass),
                x, y, z,
                tostring(component.node)
            )
        end
    end

    local function logWheel(vehicle, index, axleLabel)
        local wheel = getWheel(vehicle, index)
        local physics = wheel ~= nil and wheel.physics or nil
        if wheel == nil or physics == nil then
            Logging.info("[TRACTORDBG][WHEEL] axle=%s index=%d unavailable", axleLabel, index)
            return
        end

        local tireLoad = safeTireLoad(wheel)
        local restLoad = tonumber(physics.restLoad) or 0
        local ratio = restLoad > 0 and tireLoad / restLoad or 0

        Logging.info(
            "[TRACTORDBG][WHEEL] axle=%s index=%d tireLoad=%.3f restLoad=%.3f loadRatio=%.3f wheelMass=%.3f physicsMass=%s addMass=%s suspTravel=%s spring=%s damper=%s forcePointRatio=%s maxLong=%s maxLat=%s friction=%s",
            axleLabel,
            index,
            tireLoad,
            restLoad,
            ratio,
            safeWheelMass(wheel),
            tostring(physics.mass),
            tostring(wheel.additionalMass),
            tostring(physics.suspTravel),
            tostring(physics.spring),
            tostring(physics.damper),
            tostring(physics.forcePointRatio),
            tostring(physics.maxLongStiffness),
            tostring(physics.maxLatStiffness),
            tostring(physics.frictionScale)
        )
    end

    local function logWheels(vehicle)
        for _, index in ipairs(CFG.frontWheelIndices) do
            logWheel(vehicle, index, "front")
        end
        for _, index in ipairs(CFG.rearWheelIndices) do
            logWheel(vehicle, index, "rear")
        end
    end

    local function logMass(vehicle)
        local front = sumLoads(vehicle, CFG.frontWheelIndices)
        local rear = sumLoads(vehicle, CFG.rearWheelIndices)
        local tireTotal = front + rear
        local frontPct = tireTotal > 0 and front / tireTotal * 100 or 0
        local rearPct = tireTotal > 0 and rear / tireTotal * 100 or 0
        local totalMass = -1

        if vehicle.getTotalMass ~= nil then
            totalMass = tonumber(vehicle:getTotalMass()) or -1
        end

        local attached = countAttached(vehicle)

        Logging.info(
            "[TRACTORDBG][MASS] tireTotal=%.3f front=%.3f rear=%.3f split=%.2f/%.2f getTotalMass=%.3f attachedImplements=%d",
            tireTotal, front, rear, frontPct, rearPct, totalMass, attached
        )

        if attached > 0 then
            Logging.info("[TRACTORDBG][NOTE] getTotalMass may include attached equipment; use tireTotal/front/rear for tractor axle-distribution diagnosis")
        end
    end

    local function logMotor(vehicle)
        local motor = getMotor(vehicle)
        if motor == nil then
            Logging.info("[TRACTORDBG][MOTOR] unavailable")
            return
        end

        local groupCount = motor.gearGroups ~= nil and #motor.gearGroups or 0
        local gearCount = motor.gears ~= nil and #motor.gears or 0
        local load = getAdsLoad(vehicle)

        Logging.info(
            "[TRACTORDBG][MOTOR] gear=%d group=%d gears=%d groups=%d shiftMode=%s rpm=%.0f minRpm=%s maxRpm=%s torqueScale=%s speed=%.2f adsLoad=%s",
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
        )

        if motor.gearGroups ~= nil then
            for index, group in ipairs(motor.gearGroups) do
                Logging.info(
                    "[TRACTORDBG][MOTOR_GROUP] index=%d name=%s ratio=%s default=%s",
                    index,
                    tostring(group.name or group.dashboardName),
                    tostring(group.ratio),
                    tostring(group.isDefault)
                )
            end
        end
    end

    local function logDifferentials(vehicle)
        local spec = vehicle ~= nil and vehicle.spec_motorized or nil
        local diffs = spec ~= nil and spec.differentials or nil
        if diffs == nil then
            Logging.info("[TRACTORDBG][DIFF] unavailable")
            return
        end

        Logging.info("[TRACTORDBG][DIFF] count=%d server=%s", #diffs, tostring(vehicle.isServer))
        for index, diff in ipairs(diffs) do
            Logging.info(
                "[TRACTORDBG][DIFF] index=%d i1=%s wheel1=%s i2=%s wheel2=%s torqueRatio=%s maxSpeedRatio=%s",
                index,
                tostring(diff.diffIndex1),
                tostring(diff.diffIndex1IsWheel),
                tostring(diff.diffIndex2),
                tostring(diff.diffIndex2IsWheel),
                tostring(diff.torqueRatio),
                tostring(diff.maxSpeedRatio)
            )
        end
    end

    local function logSnapshot(vehicle)
        Logging.info("[TRACTORDBG][SNAPSHOT] BEGIN file=%s server=%s client=%s", tostring(vehicle.configFileName), tostring(vehicle.isServer), tostring(vehicle.isClient))
        logConfigurations(vehicle)
        logMass(vehicle)
        logComponents(vehicle)
        logWheels(vehicle)
        logMotor(vehicle)
        logDifferentials(vehicle)
        Logging.info("[TRACTORDBG][SNAPSHOT] END file=%s", tostring(vehicle.configFileName))
    end

    local function gearSignature(motor)
        return string.format("%d:%d", getGear(motor), getGroup(motor))
    end

    local function gearFromSignature(signature)
        local gear = string.match(signature or "", "^(-?%d+):")
        return tonumber(gear) or 0
    end

    local function groupFromSignature(signature)
        local group = string.match(signature or "", ":(-?%d+)$")
        return tonumber(group) or 0
    end

    local function traceTransmission(vehicle)
        if not CFG.traceTransmissionChanges then
            return
        end

        local motor = getMotor(vehicle)
        if motor == nil then
            return
        end

        local signature = gearSignature(motor)
        if vehicle.tractorDbgLastGearSignature == nil then
            vehicle.tractorDbgLastGearSignature = signature
            vehicle.tractorDbgLastGroup = getGroup(motor)
            return
        end

        if signature == vehicle.tractorDbgLastGearSignature then
            return
        end

        local now = g_time or 0
        local previous = vehicle.tractorDbgLastGearSignature
        local load = getAdsLoad(vehicle)

        Logging.info(
            "[TRACTORDBG][SHIFT] %s -> %s speed=%.2f rpm=%.0f adsLoad=%s dtSinceLast=%s rawActive=%s rawTarget=%s rawGear=%s rawCurrent=%s direction=%s autoTimer=%s",
            previous,
            signature,
            getSpeed(vehicle),
            getMotorRpm(motor),
            load ~= nil and string.format("%.3f", load) or "n/a",
            vehicle.tractorDbgLastShiftTime ~= nil and tostring(now - vehicle.tractorDbgLastShiftTime) or "n/a",
            tostring(motor.activeGearIndex),
            tostring(motor.targetGear),
            tostring(motor.gear),
            tostring(motor.currentGear),
            tostring(motor.currentDirection),
            tostring(motor.autoGearChangeTimer)
        )

        local previousGroup = groupFromSignature(previous)
        local currentGroup = getGroup(motor)
        if currentGroup ~= previousGroup then
            local requestAt = tonumber(motor.c330FixRequestedRangeAt)
            local requestRange = tonumber(motor.c330FixRequestedRange)
            local requestAge = requestAt ~= nil and (now - requestAt) or nil
            local requestedHere = requestRange == currentGroup
                and requestAge ~= nil
                and requestAge >= 0
                and requestAge <= 1500

            Logging.info(
                "[TRACTORDBG][RANGE_CHANGE] %d -> %d source=%s requestAge=%s requestGear=%s reason=%s direction=%s speed=%.2f rpm=%.0f adsLoad=%s",
                previousGroup,
                currentGroup,
                requestedHere and "C330TRANS" or "EXTERNAL/GIANTS",
                requestAge ~= nil and tostring(requestAge) or "n/a",
                tostring(motor.c330FixRequestedGear),
                tostring(motor.c330FixRequestedRangeReason),
                tostring(motor.currentDirection),
                getSpeed(vehicle),
                getMotorRpm(motor),
                load ~= nil and string.format("%.3f", load) or "n/a"
            )
        end

        -- activeGearIndex==0 is the normal disengaged phase between mechanical
        -- gears. Do not report 0->N->0 or N->0->N as a real oscillation.
        local currentGear = gearFromSignature(signature)
        local previousGear = gearFromSignature(previous)
        if currentGear > 0
            and previousGear > 0
            and vehicle.tractorDbgPreviousShiftFrom ~= nil
            and vehicle.tractorDbgPreviousShiftTo ~= nil
            and vehicle.tractorDbgPreviousShiftFrom == signature
            and vehicle.tractorDbgPreviousShiftTo == previous
            and vehicle.tractorDbgLastShiftTime ~= nil
            and now - vehicle.tractorDbgLastShiftTime <= CFG.oscillationWindowMs then
            Logging.warning(
                "[TRACTORDBG][SHIFT_OSCILLATION] candidate %s -> %s -> %s within %d ms",
                signature, previous, signature, now - vehicle.tractorDbgLastShiftTime
            )
        end

        vehicle.tractorDbgLastGroup = currentGroup
        vehicle.tractorDbgPreviousShiftFrom = previous
        vehicle.tractorDbgPreviousShiftTo = signature
        vehicle.tractorDbgLastShiftTime = now
        vehicle.tractorDbgLastGearSignature = signature
    end

    local function getNativeMotorLoad(motor)
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

    local function periodicWheelTrace(vehicle)
        if not CFG.periodicWheelTrace then
            return
        end

        local now = g_time or 0
        if vehicle.tractorDbgNextWheelTrace ~= nil and now < vehicle.tractorDbgNextWheelTrace then
            return
        end
        vehicle.tractorDbgNextWheelTrace = now + CFG.periodicWheelTraceMs

        local front = sumLoads(vehicle, CFG.frontWheelIndices)
        local rear = sumLoads(vehicle, CFG.rearWheelIndices)
        Logging.info(
            "[TRACTORDBG][WHEEL_TRACE] front=%.3f rear=%.3f total=%.3f speed=%.2f",
            front, rear, front + rear, getSpeed(vehicle)
        )
    end

    function Wheel:update(dt, currentUpdateIndex, groundWetness, force)
        originalWheelUpdate(self, dt, currentUpdateIndex, groundWetness, force)

        if (self.wheelIndex or 0) ~= CFG.triggerWheelIndex then
            return
        end

        local vehicle = self.vehicle
        if not isTargetVehicle(vehicle)
            or not vehicle.isAddedToPhysics then
            return
        end

        local now = g_time or 0
        if vehicle.tractorDbgFirstSeenTime == nil then
            vehicle.tractorDbgFirstSeenTime = now
        end

        if not vehicle.tractorDbgSnapshotDone
            and now - vehicle.tractorDbgFirstSeenTime >= CFG.settleDelayMs then
            vehicle.tractorDbgSnapshotDone = true
            logSnapshot(vehicle)
        end

        traceTransmission(vehicle)
        periodicEngineTrace(vehicle)
        periodicWheelTrace(vehicle)
    end

    Logging.info("[TRACTORDBG] TractorDebugKit installed; target=%s", table.concat(CFG.targetFileSuffixes, ","))
end
