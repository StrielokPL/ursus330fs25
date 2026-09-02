-- C-330/C-330M full drivetrain diagnostics for prerelease builds.
-- Read-only instrumentation: this file must not intentionally change drivetrain decisions.
-- Loaded indirectly by C330ShopOrder.lua and installed on the first mission update,
-- after C330TransmissionFix.lua has finished wrapping VehicleMotor.

C330FullDiagnostic = C330FullDiagnostic or {}

local PREFIX = "[C330FULLDIAG]"
local SNAPSHOT_INTERVAL_MS = 200
local IMPLEMENT_INTERVAL_MS = 1000
local modDirectory = g_currentModDirectory

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

local function safeCall(object, methodName, ...)
    if object == nil then
        return nil
    end
    local fn = object[methodName]
    if type(fn) ~= "function" then
        return nil
    end
    local ok, a, b, c = pcall(fn, object, ...)
    if not ok then
        return nil
    end
    return a, b, c
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
    local rpm = tonumber(safeCall(motor, "getLastModulatedMotorRpm"))
    return rpm or tonumber(motor ~= nil and motor.lastMotorRpm) or 0
end

local function getSpeed(vehicle)
    return tonumber(safeCall(vehicle, "getLastSpeed")) or 0
end

local function getMass(vehicle)
    return tonumber(safeCall(vehicle, "getTotalMass"))
end

local function getLoads(motor)
    local vehicle = motor ~= nil and motor.vehicle or nil
    local adsSpec = vehicle ~= nil and vehicle.spec_AdvancedDamageSystem or nil
    local ads = adsSpec ~= nil and tonumber(adsSpec.dynamicMotorLoad) or nil
    local native = tonumber(safeCall(motor, "getSmoothLoadPercentage"))
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
    return tonumber(safeCall(vehicle, "getSpeedLimit", true)),
        tonumber(safeCall(vehicle, "getSpeedLimit", false))
end

local function getObjectName(object)
    if object == nil then
        return "nil"
    end
    local name = safeCall(object, "getName")
    if type(name) == "string" and name ~= "" then
        return name
    end
    if type(object.configFileName) == "string" then
        return object.configFileName
    end
    return tostring(object)
end

local function getImplementsSummary(vehicle)
    local attached = safeCall(vehicle, "getAttachedImplements")
    if type(attached) ~= "table" then
        return "none"
    end

    local parts = {}
    for index, implement in ipairs(attached) do
        local object = implement ~= nil and implement.object or nil
        if object ~= nil then
            local lowered = safeCall(object, "getIsLowered")
            local turnedOn = safeCall(object, "getIsTurnedOn")
            local limit = tonumber(safeCall(object, "getSpeedLimit"))
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

local function logSnapshot(motor, curGear, resultGear, acceleratorPedal, reason)
    if not isTargetMotor(motor) then
        return
    end

    local now = g_time or 0
    local last = motor.c330FullDiagLastSnapshot or -100000
    if reason == "periodic" and now - last < SNAPSHOT_INTERVAL_MS then
        return
    end
    motor.c330FullDiagLastSnapshot = now

    local vehicle = motor.vehicle
    local ads, native, selected, sourceName = getLoads(motor)
    local toolsLimit, vehicleLimit = getSpeedLimits(vehicle)

    Logging.info(
        "%s[STATE] model=%s dir=%s shiftMode=%s speed=%s rpm=%s gear=%s target=%s curArg=%s result=%s range=%s accel=%s massT=%s loadSel=%s loadSrc=%s adsRaw=%s nativeRaw=%s speedLimitTools=%s speedLimitVehicle=%s autoTimer=%s dwellAgeMs=%s holdRemainMs=%s cooldownRemainMs=%s rangeRecoveryAgeMs=%s topLowLoadAgeMs=%s reqRange=%s reqGear=%s reqReason=%s sample=%s",
        PREFIX,
        getMotorConfigName(vehicle),
        tostring(motor.currentDirection or "n/a"),
        tostring(motor.gearShiftMode or "n/a"),
        fmt(getSpeed(vehicle), 3),
        fmt(getRpm(motor), 1),
        tostring(motor.gear or "n/a"),
        tostring(motor.targetGear or "n/a"),
        tostring(curGear or "n/a"),
        tostring(resultGear or "n/a"),
        tostring(motor.activeGearGroupIndex or "n/a"),
        fmt(math.abs(tonumber(acceleratorPedal) or 0), 3),
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
        tostring(motor.c330FixRequestedRangeReason or "n/a"),
        tostring(reason or "n/a")
    )

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

            if isTargetMotor(selfMotor) then
                logSnapshot(selfMotor, curGear, result, acceleratorPedal, "periodic")
                if result ~= nil and curGear ~= nil and result ~= curGear then
                    Logging.info(
                        "%s[DECISION] cur=%s result=%s rangeBefore=%s rangeAfter=%s gearBefore=%s gearAfter=%s targetBefore=%s targetAfter=%s gearSign=%s changeTimer=%s rpm=%s speed=%s load=%s source=%s reqReason=%s",
                        PREFIX,
                        tostring(curGear),
                        tostring(result),
                        tostring(beforeRange or "n/a"),
                        tostring(selfMotor.activeGearGroupIndex or "n/a"),
                        tostring(beforeGear or "n/a"),
                        tostring(selfMotor.gear or "n/a"),
                        tostring(beforeTarget or "n/a"),
                        tostring(selfMotor.targetGear or "n/a"),
                        tostring(gearSign or "n/a"),
                        tostring(gearChangeTimer or "n/a"),
                        fmt(getRpm(selfMotor), 1),
                        fmt(getSpeed(selfMotor.vehicle), 3),
                        fmt(select(3, getLoads(selfMotor)), 3),
                        select(4, getLoads(selfMotor)),
                        tostring(selfMotor.c330FixRequestedRangeReason or "n/a")
                    )
                    logSnapshot(selfMotor, curGear, result, acceleratorPedal, "decision")
                end
            end
            return result
        end
    end

    local originalBestStartGear = VehicleMotor.getBestStartGear
    if type(originalBestStartGear) == "function" then
        VehicleMotor.getBestStartGear = function(selfMotor, gears)
            local gear, group = originalBestStartGear(selfMotor, gears)
            if isTargetMotor(selfMotor) then
                Logging.info(
                    "%s[START_GEAR] gear=%s range=%s massT=%s model=%s direction=%s",
                    PREFIX,
                    tostring(gear or "n/a"),
                    tostring(group or "n/a"),
                    fmt(getMass(selfMotor.vehicle), 3),
                    getMotorConfigName(selfMotor.vehicle),
                    tostring(selfMotor.currentDirection or "n/a")
                )
            end
            return gear, group
        end
    end

    local originalSetGearGroup = VehicleMotor.setGearGroup
    if type(originalSetGearGroup) == "function" then
        VehicleMotor.setGearGroup = function(selfMotor, groupIndex, ...)
            if isTargetMotor(selfMotor) then
                Logging.info(
                    "%s[RANGE_SET] before=%s requested=%s gear=%s target=%s rpm=%s speed=%s load=%s source=%s reqReason=%s",
                    PREFIX,
                    tostring(selfMotor.activeGearGroupIndex or "n/a"),
                    tostring(groupIndex or "n/a"),
                    tostring(selfMotor.gear or "n/a"),
                    tostring(selfMotor.targetGear or "n/a"),
                    fmt(getRpm(selfMotor), 1),
                    fmt(getSpeed(selfMotor.vehicle), 3),
                    fmt(select(3, getLoads(selfMotor)), 3),
                    select(4, getLoads(selfMotor)),
                    tostring(selfMotor.c330FixRequestedRangeReason or "n/a")
                )
            end
            local result = originalSetGearGroup(selfMotor, groupIndex, ...)
            if isTargetMotor(selfMotor) then
                Logging.info("%s[RANGE_DONE] active=%s", PREFIX, tostring(selfMotor.activeGearGroupIndex or "n/a"))
            end
            return result
        end
    end

    local originalSetGear = VehicleMotor.setGear
    if type(originalSetGear) == "function" then
        VehicleMotor.setGear = function(selfMotor, gearIndex, ...)
            if isTargetMotor(selfMotor) then
                Logging.info(
                    "%s[GEAR_SET] before=%s requested=%s range=%s rpm=%s speed=%s load=%s source=%s",
                    PREFIX,
                    tostring(selfMotor.gear or "n/a"),
                    tostring(gearIndex or "n/a"),
                    tostring(selfMotor.activeGearGroupIndex or "n/a"),
                    fmt(getRpm(selfMotor), 1),
                    fmt(getSpeed(selfMotor.vehicle), 3),
                    fmt(select(3, getLoads(selfMotor)), 3),
                    select(4, getLoads(selfMotor))
                )
            end
            return originalSetGear(selfMotor, gearIndex, ...)
        end
    end

    Logging.info("%s installed inside Ursus prerelease; snapshot=%dms implements=%dms", PREFIX, SNAPSHOT_INTERVAL_MS, IMPLEMENT_INTERVAL_MS)
end

function C330FullDiagnostic:update(dt)
    if not self.installed and VehicleMotor ~= nil then
        self:install()
    end
end

if not C330FullDiagnostic.listenerAdded then
    C330FullDiagnostic.listenerAdded = true
    addModEventListener(C330FullDiagnostic)
end
