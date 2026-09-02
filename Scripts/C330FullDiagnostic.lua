-- C-330/C-330M flight-recorder diagnostics for prerelease builds.
-- IMPORTANT: instrumentation must never change or interrupt drivetrain execution.
-- Critical VehicleMotor hooks only copy primitive values to RAM and return immediately.
-- Formatting, API probes and log writes happen later from the mod event listener.

C330FullDiagnostic = C330FullDiagnostic or {}

local PREFIX = "[C330FULLDIAG]"
local SNAPSHOT_INTERVAL_MS = 250
local IMPLEMENT_INTERVAL_MS = 1000
local modDirectory = g_currentModDirectory
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
    local vehicle = motor ~= nil and motor.vehicle or nil
    local adsSpec = vehicle ~= nil and vehicle.spec_AdvancedDamageSystem or nil
    local ads = adsSpec ~= nil and tonumber(adsSpec.dynamicMotorLoad) or nil
    local native = tonumber(safeFirst(motor, "getSmoothLoadPercentage"))
    local selected = nil
    local sourceName = "n/a"

    if ads ~= nil and ads >= 0 and ads <= 1.05 then
        selected = math.max(0, math.min(ads, 1.0))
        sourceName = "ADS"
    elseif native ~= nil then
        selected = math.max(0, math.min(native, 1.5))
        sourceName = "GIANTS"
    end

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

local function getRearWheelSummary(vehicle)
    local wheels = vehicle ~= nil
        and vehicle.spec_wheels ~= nil
        and vehicle.spec_wheels.wheels
        or nil
    if type(wheels) ~= "table" then
        return "n/a"
    end

    local parts = {}
    for _, index in ipairs({3, 4}) do
        local wheel = wheels[index]
        if wheel ~= nil then
            local physics = wheel.physics or {}
            parts[#parts + 1] = string.format(
                "W%d{tireLoad=%s,restLoad=%s,addMass=%s,radius=%s}",
                index,
                fmt(tonumber(wheel.tireLoad), 3),
                fmt(tonumber(physics.restLoad), 3),
                fmt(tonumber(wheel.additionalMass), 3),
                fmt(tonumber(wheel.radius) or tonumber(physics.radius), 4)
            )
        end
    end

    return #parts > 0 and table.concat(parts, " ") or "n/a"
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
        Logging.info("%s[REAR_WHEELS] %s", PREFIX, getRearWheelSummary(vehicle))
    end
end

function C330FullDiagnostic:install()
    if self.installed then
        return
    end
    self.installed = true

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
            local reason = selfMotor.c330FixRequestedRangeReason
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

    Logging.info("%s flight recorder installed; state=%dms implements=%dms; critical hooks are RAM-only", PREFIX, SNAPSHOT_INTERVAL_MS, IMPLEMENT_INTERVAL_MS)
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
