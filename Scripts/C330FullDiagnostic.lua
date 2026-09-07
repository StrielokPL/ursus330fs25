-- C-330/C-330M flight-recorder diagnostics for prerelease builds.
-- IMPORTANT: instrumentation must never change or interrupt drivetrain execution.
-- Critical VehicleMotor hooks only copy primitive values to RAM and return immediately.
-- Formatting, API probes and log writes happen later from the mod event listener.

C330FullDiagnostic = C330FullDiagnostic or {}

local PREFIX = "[C330FULLDIAG]"
local SNAPSHOT_INTERVAL_MS = 250
local IMPLEMENT_INTERVAL_MS = 1000
local modDirectory = g_currentModDirectory
local nextVehicleId = 0
local trackedMotors = setmetatable({}, {__mode = "k"})

local function fmt(value, decimals)
    if value == nil then
        return "n/a"
    end
    if type(value) == "number" then
        return string.format("%." .. tostring(decimals or 3) .. "f", value)
    end
    return tostring(value)
end

local function bool(value)
    if value == nil then
        return "n/a"
    end
    return value and "true" or "false"
end

-- Explicitly return ONLY the first result. Some GIANTS methods (notably
-- getSpeedLimit) return a second boolean; forwarding all Lua return values into
-- tonumber() accidentally turns that boolean into tonumber's base argument.
local function safeFirst(object, methodName, ...)
    if object == nil then
        return nil
    end
    local fn = object[methodName]
    if type(fn) ~= "function" then
        return nil
    end
    local ok, first = pcall(fn, object, ...)
    if not ok then
        return nil
    end
    return first
end

local function endsWith(value, suffix)
    return type(value) == "string"
        and type(suffix) == "string"
        and string.sub(value, -string.len(suffix)) == suffix
end

local function isTargetVehicle(vehicle)
    if vehicle == nil or type(vehicle.configFileName) ~= "string" then
        return false
    end
    if modDirectory ~= nil
        and string.sub(vehicle.configFileName, 1, string.len(modDirectory)) ~= modDirectory then
        return false
    end
    return endsWith(string.lower(vehicle.configFileName), "c330m.xml")
end

local function isTargetMotor(motor)
    return motor ~= nil and isTargetVehicle(motor.vehicle)
end

local function trackMotor(motor)
    if isTargetMotor(motor) then
        if not trackedMotors[motor] then
            nextVehicleId = nextVehicleId + 1
            motor.c330FullDiagId = nextVehicleId
        end
        trackedMotors[motor] = true
        return true
    end
    return false
end

local function getMotorConfigName(vehicle)
    if vehicle == nil
        or vehicle.configurations == nil
        or vehicle.configurations.motor == nil
        or vehicle.xmlFile == nil
        or ConfigurationUtil == nil then
        return "n/a"
    end

    local ok, key = pcall(
        ConfigurationUtil.getXMLConfigurationKey,
        vehicle.xmlFile,
        vehicle.configurations.motor,
        "vehicle.motorized.motorConfigurations.motorConfiguration",
        "vehicle.motorized",
        "motor"
    )
    if not ok or key == nil then
        return "n/a"
    end

    local okName, name = pcall(vehicle.xmlFile.getValue, vehicle.xmlFile, key .. "#name")
    return okName and (name or "n/a") or "n/a"
end

local function getRpm(motor)
    local rpm = tonumber(safeFirst(motor, "getLastModulatedMotorRpm"))
    return rpm or tonumber(motor ~= nil and motor.lastMotorRpm) or 0
end

local function getSpeed(vehicle)
    return tonumber(safeFirst(vehicle, "getLastSpeed")) or 0
end

local function getMass(vehicle)
    return tonumber(safeFirst(vehicle, "getTotalMass"))
end

local function getLoads(motor)
    local selected, sourceName, ads, native = C330Runtime.load(motor)
    return ads, native, selected, sourceName
end

local function getSpeedLimits(vehicle)
    local tools = safeFirst(vehicle, "getSpeedLimit", true)
    local vehicleOnly = safeFirst(vehicle, "getSpeedLimit", false)
    return tonumber(tools), tonumber(vehicleOnly)
end

local function getObjectName(object)
    if object == nil then
        return "nil"
    end
    local name = safeFirst(object, "getName")
    if type(name) == "string" and name ~= "" then
        return name
    end
    if type(object.configFileName) == "string" then
        return object.configFileName
    end
    return tostring(object)
end

local function getImplementsSummary(vehicle)
    local attached = safeFirst(vehicle, "getAttachedImplements")
    if type(attached) ~= "table" then
        return "none"
    end

    local parts = {}
    for index, implement in ipairs(attached) do
        local object = implement ~= nil and implement.object or nil
        if object ~= nil then
            local lowered = safeFirst(object, "getIsLowered")
            local turnedOn = safeFirst(object, "getIsTurnedOn")
            local limit = tonumber(safeFirst(object, "getSpeedLimit"))
            parts[#parts + 1] = string.format(
                "%d:%s{lowered=%s,on=%s,limit=%s,plow=%s,workArea=%s}",
                index,
                getObjectName(object),
                bool(lowered),
                bool(turnedOn),
                fmt(limit, 2),
                bool(object.spec_plow ~= nil),
                bool(object.spec_workArea ~= nil)
            )
        end
    end

    return #parts > 0 and table.concat(parts, " | ") or "none"
end

local function getWheelSummary(vehicle)
    local wheels = vehicle.spec_wheels and vehicle.spec_wheels.wheels
    if type(wheels) ~= "table" then return "n/a" end
    local parts = {}
    for index, wheel in ipairs(wheels) do
        local physics = wheel.physics or {}
        local net = physics.netInfo or {}
        local load
        -- GIANTS getTireLoad returns a mass-equivalent in tonnes, not newtons.
        -- A client without a physical wheel shape has no local force measurement.
        if vehicle.isServer and physics.wheelShapeCreated then
            load = tonumber(safeFirst(physics, "getTireLoad"))
        end
        parts[#parts+1] = string.format(
            "W%d{tireLoadT=%s,forceSource=%s,contact=%s,ground=%s,slip=%s,angularRadS=%s,suspensionM=%s,radiusM=%s,friction=%s,restLoadT=%s,addMassT=%s}",
            index, fmt(load), load ~= nil and "physics.getTireLoad" or "unavailable",
            fmt(physics.contact, 0), bool(physics.hasGroundContact), fmt(net.slip),
            fmt(net.xDriveSpeed), fmt(net.suspensionLength), fmt(wheel.radius or physics.radius, 4),
            fmt(physics.tireGroundFrictionCoeff), fmt(physics.restLoad), fmt(wheel.additionalMass))
    end
    return table.concat(parts, " ")
end
-- Event queue is bounded and flushed off the drivetrain path. It preserves
-- multiple shifts between 250 ms snapshots and exposes any overflow explicitly.
local function queueTransition(motor, beforeGear, beforeTarget, beforeRange)
    if beforeGear == motor.gear and beforeTarget == motor.targetGear and beforeRange == motor.activeGearGroupIndex then return end
    local queue = motor.c330FullDiagTransitions or {}
    motor.c330FullDiagTransitions = queue
    if #queue >= 128 then
        motor.c330FullDiagDropped = (motor.c330FullDiagDropped or 0) + 1
        return
    end
    motor.c330FullDiagTransitionSeq = (motor.c330FullDiagTransitionSeq or 0) + 1
    local p2 = motor.c330P2 or {}
    queue[#queue+1] = {seq=motor.c330FullDiagTransitionSeq, time=g_time or 0,
        before=beforeGear, after=motor.gear, beforeTarget=beforeTarget, target=motor.targetGear,
        beforeRange=beforeRange, range=motor.activeGearGroupIndex,
        reason=p2.reason, decisionAt=p2.decisionAt,
        allowTimer=motor.allowGearChangeTimer, gearTimer=motor.gearChangeTimer,
        groupTimer=motor.groupChangeTimer}
end

local function ageSince(value, now)
    if value == nil then
        return nil
    end
    return math.max(0, now - value)
end

local function remainingUntil(value, now)
    if value == nil then
        return nil
    end
    return math.max(0, value - now)
end

function C330FullDiagnostic:flushMotor(motor, now)
    if motor == nil or motor.c330FullDiagDisabled or not isTargetMotor(motor) then
        return
    end

    local PREFIX = PREFIX .. "[v" .. tostring(motor.c330FullDiagId or "?") .. "]"
    local vehicle = motor.vehicle
    if motor.c330FullDiagModel == nil then
        motor.c330FullDiagModel = getMotorConfigName(vehicle)
    end

    local ads, native, selected, sourceName = getLoads(motor)
    local toolsLimit, vehicleLimit = getSpeedLimits(vehicle)
    local prediction = motor.c330FullDiagPrediction or {}

    Logging.info(
        "%s[STATE] model=%s dir=%s shiftMode=%s speed=%s rpm=%s gear=%s target=%s range=%s predCur=%s predResult=%s accel=%s massT=%s loadSel=%s loadSrc=%s adsRaw=%s nativeRaw=%s speedLimitTools=%s speedLimitVehicle=%s autoTimer=%s dwellAgeMs=%s holdRemainMs=%s cooldownRemainMs=%s rangeRecoveryAgeMs=%s topLowLoadAgeMs=%s reqRange=%s reqGear=%s reqReason=%s",
        PREFIX,
        motor.c330FullDiagModel,
        tostring(motor.currentDirection or "n/a"),
        tostring(motor.gearShiftMode or "n/a"),
        fmt(getSpeed(vehicle), 3),
        fmt(getRpm(motor), 1),
        tostring(motor.gear or "n/a"),
        tostring(motor.targetGear or "n/a"),
        tostring(motor.activeGearGroupIndex or "n/a"),
        tostring(prediction.curGear or "n/a"),
        tostring(prediction.resultGear or "n/a"),
        fmt(math.abs(tonumber(prediction.acceleratorPedal) or 0), 3),
        fmt(getMass(vehicle), 3),
        fmt(selected, 3),
        sourceName,
        fmt(ads, 3),
        fmt(native, 3),
        fmt(toolsLimit, 3),
        fmt(vehicleLimit, 3),
        fmt(tonumber(motor.autoGearChangeTimer), 0),
        fmt(ageSince(motor.c330FixSettledGearSince, now), 0),
        fmt(remainingUntil(motor.c330FixUpshiftHoldUntil, now), 0),
        fmt(remainingUntil(motor.c330FixRangeCooldownUntil, now), 0),
        fmt(ageSince(motor.c330FixRangeRecoverySince, now), 0),
        fmt(ageSince(motor.c330FixTopGearLowLoadSince, now), 0),
        tostring(motor.c330FixRequestedRange or "n/a"),
        tostring(motor.c330FixRequestedGear or "n/a"),
        tostring(motor.c330FixRequestedRangeReason or "n/a")
    )

    local p2, smoke = motor.c330P2 or {}, vehicle.c330Smoke or {}
    Logging.info("%s[CONTROL] server=%s predictionAgeMs=%s reqAgeMs=%s allowTimerMs=%s allowDirection=%s gearTimerMs=%s groupTimerMs=%s directionTimerMs=%s workLimit=%s ceiling=%s gate=%s decision=%s decisionAgeMs=%s candidate=%s candidateAgeMs=%s decisionRpm=%s predictedRpm=%s predictedLoad=%s decisionLoad=%s filteredLoad=%s decisionLoadSrc=%s speedTrendKmhS=%s rearSlip=%s failedGear=%s failedLoad=%s failedAgeMs=%s reductionAgeMs=%s reductionCompletedMs=%s vetoBeforeMs=%s vetoReleaseAgeMs=%s",
        PREFIX, bool(vehicle.isServer), fmt(ageSince(prediction.time, now),0),
        fmt(ageSince(motor.c330FixRequestedRangeAt, now),0), fmt(motor.allowGearChangeTimer,0),
        fmt(motor.allowGearChangeDirection,0), fmt(motor.gearChangeTimer,0), fmt(motor.groupChangeTimer,0),
        fmt(motor.directionChangeTimer,0), fmt(motor.c330WorkSpeedLimit), fmt(motor.c330WorkTargetVirtual,0),
        tostring(p2.gate or "n/a"), tostring(p2.reason or "n/a"), fmt(ageSince(p2.decisionAt,now),0),
        fmt(p2.candidateVirtual,0), fmt(ageSince(p2.candidateAt,now),0), fmt(p2.decisionRpm,1), fmt(p2.predictedRpm,1), fmt(p2.predictedLoad), fmt(p2.decisionLoad),
        fmt(p2.filteredLoad), tostring(p2.decisionSource or "n/a"), fmt(p2.speedTrend), fmt(p2.slip),
        fmt(p2.failure and p2.failure.to,0), fmt(p2.failure and p2.failure.load), fmt(ageSince(p2.failure and p2.failure.at,now),0),
        fmt(p2.reduction and ageSince(p2.reduction.at,now),0),
        fmt(p2.reductionCompletedAt and p2.reductionRequestedAt and (p2.reductionCompletedAt-p2.reductionRequestedAt),0),
        fmt(p2.vetoBefore,0), fmt(ageSince(p2.vetoReleasedAt,now),0))
    Logging.info("%s[WHEELS] %s", PREFIX, getWheelSummary(vehicle))
    Logging.info("%s[EXHAUST] source=%s rawLoad=%s filteredLoad=%s extension=%s intensity=%s disabled=%s",
        PREFIX, tostring(smoke.source or "n/a"), fmt(smoke.rawLoad), fmt(smoke.load), bool(smoke.extension), fmt(smoke.intensity), bool(vehicle.c330SmokeDisabled))
    for _, event in ipairs(motor.c330FullDiagTransitions or {}) do
        Logging.info("%s[SHIFT_ACTUAL] seq=%s eventTimeMs=%s ageMs=%s gear=%s->%s target=%s->%s range=%s->%s decision=%s decisionAgeMs=%s allowTimerMs=%s gearTimerMs=%s groupTimerMs=%s",
            PREFIX, fmt(event.seq,0), fmt(event.time,0), fmt(now-event.time,0), fmt(event.before,0), fmt(event.after,0),
            fmt(event.beforeTarget,0), fmt(event.target,0), fmt(event.beforeRange,0), fmt(event.range,0),
            tostring(event.reason or "external/base"), fmt(ageSince(event.decisionAt,event.time),0),
            fmt(event.allowTimer,0), fmt(event.gearTimer,0), fmt(event.groupTimer,0))
    end
    motor.c330FullDiagTransitions = nil
    if (motor.c330FullDiagDropped or 0) > 0 then
        Logging.warning("%s[EVENT_OVERFLOW] dropped=%d", PREFIX, motor.c330FullDiagDropped)
        motor.c330FullDiagDropped = 0
    end

    local predictionSig = table.concat({
        tostring(prediction.curGear or "n/a"),
        tostring(prediction.resultGear or "n/a"),
        tostring(prediction.rangeBefore or "n/a"),
        tostring(prediction.rangeAfter or "n/a"),
        tostring(prediction.gearSign or "n/a"),
        tostring(motor.c330FixRequestedRangeReason or "n/a")
    }, ":")
    if prediction.time ~= nil and predictionSig ~= motor.c330FullDiagLastPredictionSig then
        motor.c330FullDiagLastPredictionSig = predictionSig
        Logging.info(
            "%s[PREDICTION_CHANGE] cur=%s result=%s rangeBefore=%s rangeAfter=%s gearBefore=%s gearAfter=%s targetBefore=%s targetAfter=%s gearSign=%s changeTimer=%s ageMs=%s",
            PREFIX,
            tostring(prediction.curGear or "n/a"),
            tostring(prediction.resultGear or "n/a"),
            tostring(prediction.rangeBefore or "n/a"),
            tostring(prediction.rangeAfter or "n/a"),
            tostring(prediction.gearBefore or "n/a"),
            tostring(prediction.gearAfter or "n/a"),
            tostring(prediction.targetBefore or "n/a"),
            tostring(prediction.targetAfter or "n/a"),
            tostring(prediction.gearSign or "n/a"),
            tostring(prediction.gearChangeTimer or "n/a"),
            tostring(math.max(0, now - prediction.time))
        )
    end

    local start = motor.c330FullDiagStart
    if start ~= nil then
        local startSig = table.concat({
            tostring(start.gear or "n/a"),
            tostring(start.group or "n/a"),
            tostring(motor.currentDirection or "n/a")
        }, ":")
        if startSig ~= motor.c330FullDiagLastStartSig then
            motor.c330FullDiagLastStartSig = startSig
            Logging.info(
                "%s[START_CHANGE] gear=%s range=%s model=%s direction=%s",
                PREFIX,
                tostring(start.gear or "n/a"),
                tostring(start.group or "n/a"),
                motor.c330FullDiagModel,
                tostring(motor.currentDirection or "n/a")
            )
        end
    end

    local rangeEvent = motor.c330FullDiagRangeEvent
    if rangeEvent ~= nil and rangeEvent.seq ~= motor.c330FullDiagLastRangeSeq then
        motor.c330FullDiagLastRangeSeq = rangeEvent.seq
        Logging.info(
            "%s[RANGE_EVENT] before=%s requested=%s after=%s gear=%s target=%s reqReason=%s ageMs=%s",
            PREFIX,
            tostring(rangeEvent.before or "n/a"),
            tostring(rangeEvent.requested or "n/a"),
            tostring(rangeEvent.after or "n/a"),
            tostring(rangeEvent.gear or "n/a"),
            tostring(rangeEvent.target or "n/a"),
            tostring(rangeEvent.reason or "n/a"),
            tostring(math.max(0, now - (rangeEvent.time or now)))
        )
    end

    local gearEvent = motor.c330FullDiagGearEvent
    if gearEvent ~= nil and gearEvent.seq ~= motor.c330FullDiagLastGearSeq then
        motor.c330FullDiagLastGearSeq = gearEvent.seq
        Logging.info(
            "%s[GEAR_EVENT] before=%s requested=%s after=%s range=%s ageMs=%s",
            PREFIX,
            tostring(gearEvent.before or "n/a"),
            tostring(gearEvent.requested or "n/a"),
            tostring(gearEvent.after or "n/a"),
            tostring(gearEvent.range or "n/a"),
            tostring(math.max(0, now - (gearEvent.time or now)))
        )
    end

    local lastImpl = motor.c330FullDiagLastImplement or -100000
    if now - lastImpl >= IMPLEMENT_INTERVAL_MS then
        motor.c330FullDiagLastImplement = now
        Logging.info("%s[IMPLEMENTS] %s", PREFIX, getImplementsSummary(vehicle))
    end
end

function C330FullDiagnostic:install()
    if self.installed then
        return
    end
    self.installed = true

    local originalUpdateGear = VehicleMotor.updateGear
    if type(originalUpdateGear) == "function" then
        VehicleMotor.updateGear = function(motor, ...)
            local beforeGear, beforeTarget, beforeRange = motor.gear, motor.targetGear, motor.activeGearGroupIndex
            local result = originalUpdateGear(motor, ...)
            if trackMotor(motor) then queueTransition(motor, beforeGear, beforeTarget, beforeRange) end
            return result
        end
    end
    local originalPrediction = VehicleMotor.findGearChangeTargetGearPrediction
    if type(originalPrediction) == "function" then
        VehicleMotor.findGearChangeTargetGearPrediction = function(selfMotor, curGear, gears, gearSign, gearChangeTimer, acceleratorPedal, dt)
            local beforeRange = selfMotor.activeGearGroupIndex
            local beforeGear = selfMotor.gear
            local beforeTarget = selfMotor.targetGear
            local result = originalPrediction(selfMotor, curGear, gears, gearSign, gearChangeTimer, acceleratorPedal, dt)

            -- Critical path: assignments only. Never call Logging, pcall probes,
            -- getSpeedLimit, getTotalMass or any other potentially expensive API here.
            if trackMotor(selfMotor) then
                selfMotor.c330FullDiagPrediction = {
                    time = g_time or 0,
                    curGear = curGear,
                    resultGear = result,
                    rangeBefore = beforeRange,
                    rangeAfter = selfMotor.activeGearGroupIndex,
                    gearBefore = beforeGear,
                    gearAfter = selfMotor.gear,
                    targetBefore = beforeTarget,
                    targetAfter = selfMotor.targetGear,
                    gearSign = gearSign,
                    gearChangeTimer = gearChangeTimer,
                    acceleratorPedal = acceleratorPedal
                }
            end
            return result
        end
    end

    local originalBestStartGear = VehicleMotor.getBestStartGear
    if type(originalBestStartGear) == "function" then
        VehicleMotor.getBestStartGear = function(selfMotor, gears)
            local gear, group = originalBestStartGear(selfMotor, gears)
            if trackMotor(selfMotor) then
                selfMotor.c330FullDiagStart = {
                    time = g_time or 0,
                    gear = gear,
                    group = group
                }
            end
            return gear, group
        end
    end

    local originalSetGearGroup = VehicleMotor.setGearGroup
    if type(originalSetGearGroup) == "function" then
        VehicleMotor.setGearGroup = function(selfMotor, groupIndex, ...)
            local target = trackMotor(selfMotor)
            local before = selfMotor.activeGearGroupIndex
            local beforeGear = selfMotor.gear
            local beforeTarget = selfMotor.targetGear
            local reason = selfMotor.c330FixRequestedRangeAt == (g_time or 0)
                and selfMotor.c330FixRequestedRangeReason or "external/base"
            local result = originalSetGearGroup(selfMotor, groupIndex, ...)
            if target and groupIndex ~= before then
                selfMotor.c330FullDiagRangeSeq = (selfMotor.c330FullDiagRangeSeq or 0) + 1
                selfMotor.c330FullDiagRangeEvent = {
                    seq = selfMotor.c330FullDiagRangeSeq,
                    time = g_time or 0,
                    before = before,
                    requested = groupIndex,
                    after = selfMotor.activeGearGroupIndex,
                    gear = beforeGear,
                    target = beforeTarget,
                    reason = reason
                }
            end
            return result
        end
    end

    local originalSetGear = VehicleMotor.setGear
    if type(originalSetGear) == "function" then
        VehicleMotor.setGear = function(selfMotor, gearIndex, ...)
            local target = trackMotor(selfMotor)
            local before = selfMotor.gear
            local range = selfMotor.activeGearGroupIndex
            local result = originalSetGear(selfMotor, gearIndex, ...)
            if target and gearIndex ~= before then
                selfMotor.c330FullDiagGearSeq = (selfMotor.c330FullDiagGearSeq or 0) + 1
                selfMotor.c330FullDiagGearEvent = {
                    seq = selfMotor.c330FullDiagGearSeq,
                    time = g_time or 0,
                    before = before,
                    requested = gearIndex,
                    after = selfMotor.gear,
                    range = range
                }
            end
            return result
        end
    end

    Logging.info("%s 0.0.5.1P2 flight recorder installed; state=%dms implements=%dms; critical hooks are RAM-only", PREFIX, SNAPSHOT_INTERVAL_MS, IMPLEMENT_INTERVAL_MS)
end

function C330FullDiagnostic:update(dt)
    if not self.installed and VehicleMotor ~= nil then
        self:install()
    end
    if not self.installed then
        return
    end

    local now = g_time or 0
    if self.nextFlushAt ~= nil and now < self.nextFlushAt then
        return
    end
    self.nextFlushAt = now + SNAPSHOT_INTERVAL_MS

    for motor, _ in pairs(trackedMotors) do
        if motor ~= nil and not motor.c330FullDiagDisabled then
            local ok, err = pcall(C330FullDiagnostic.flushMotor, self, motor, now)
            if not ok then
                -- Fail closed: one diagnostic bug may cost one warning, but it must
                -- never keep breaking VehicleMotor.update or spam an exception each frame.
                motor.c330FullDiagDisabled = true
                Logging.warning("%s disabled for one tractor after diagnostic error: %s", PREFIX, tostring(err))
            end
        end
    end
end

if not C330FullDiagnostic.listenerAdded then
    C330FullDiagnostic.listenerAdded = true
    addModEventListener(C330FullDiagnostic)
end
