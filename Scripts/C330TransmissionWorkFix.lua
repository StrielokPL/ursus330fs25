-- C-330/C-330M work-speed-aware automatic gearbox correction.
-- Loaded before C330TransmissionFix.lua, but installs on the first mission update
-- so it wraps the final validated controller instead of the raw GIANTS method.
-- The full prerelease diagnostic may then wrap this layer read-only.

C330TransmissionWorkFix = C330TransmissionWorkFix or {}

local LOW_RANGE = 1
local HIGH_RANGE = 2
local LOW_RANGE_RATIO = 0.24691358
local MAX_RPM = 2200
local WORK_MIN_RPM_AT_LIMIT = 1500
local WORK_RANGE_UP_RPM = 2050
local WORK_RANGE_UP_DWELL_MS = 2000
local WORK_RELEASE_HOLD_MS = 2500
local LUG_DOWNSHIFT_RPM = 1450
local LUG_DOWNSHIFT_LOAD = 0.75
local LUG_DOWNSHIFT_ACCEL = 0.85
local RANGE_CHANGE_COOLDOWN_MS = 800
local modDirectory = g_currentModDirectory

-- Nominal high-range speeds at 2200 rpm. Low range is the same three gears
-- through the factory 0.24691358 reducer.
local HIGH_RANGE_SPEEDS = {
    ["C-330"] = {7.389, 14.324, 22.878},
    ["C-330M"] = {8.491, 16.460, 26.290}
}

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
    return endsWith(vehicle.configFileName, "c330m.xml")
end

local function getMotorName(motor)
    if motor == nil or not isTargetVehicle(motor.vehicle) then
        return nil
    end
    if motor.c330WorkMotorName ~= nil then
        return motor.c330WorkMotorName
    end

    local vehicle = motor.vehicle
    local configurations = vehicle.configurations
    if configurations == nil or configurations.motor == nil or vehicle.xmlFile == nil then
        return nil
    end

    local key = ConfigurationUtil.getXMLConfigurationKey(
        vehicle.xmlFile,
        configurations.motor,
        "vehicle.motorized.motorConfigurations.motorConfiguration",
        "vehicle.motorized",
        "motor"
    )
    if key == nil then
        return nil
    end

    local name = vehicle.xmlFile:getValue(key .. "#name")
    if HIGH_RANGE_SPEEDS[name] ~= nil then
        motor.c330WorkMotorName = name
        return name
    end
    return nil
end

local function isAutomaticForward(motor)
    return getMotorName(motor) ~= nil
        and motor.gearGroups ~= nil
        and #motor.gearGroups == 2
        and motor.gearShiftMode == VehicleMotor.SHIFT_MODE_AUTOMATIC
        and (motor.currentDirection or 1) >= 0
end

local function getRpm(motor)
    if motor ~= nil and motor.getLastModulatedMotorRpm ~= nil then
        local value = tonumber(motor:getLastModulatedMotorRpm())
        if value ~= nil then
            return value
        end
    end
    return tonumber(motor ~= nil and motor.lastMotorRpm) or 0
end

local function getLoad(motor)
    local vehicle = motor ~= nil and motor.vehicle or nil
    local adsSpec = vehicle ~= nil and vehicle.spec_AdvancedDamageSystem or nil
    local adsLoad = adsSpec ~= nil and tonumber(adsSpec.dynamicMotorLoad) or nil
    if adsLoad ~= nil and adsLoad >= 0 and adsLoad <= 1.05 then
        return math.clamp(adsLoad, 0, 1.0), "ADS"
    end

    if motor ~= nil and motor.getSmoothLoadPercentage ~= nil then
        local nativeLoad = tonumber(motor:getSmoothLoadPercentage())
        if nativeLoad ~= nil then
            return math.clamp(nativeLoad, 0, 1.5), "GIANTS"
        end
    end
    return nil, "n/a"
end

local function getFiniteSpeedLimit(vehicle, withTools)
    if vehicle == nil or type(vehicle.getSpeedLimit) ~= "function" then
        return nil
    end
    -- Capture only the first return value. getSpeedLimit can also return a boolean.
    local ok, value = pcall(vehicle.getSpeedLimit, vehicle, withTools)
    if not ok then
        return nil
    end
    value = tonumber(value)
    if value == nil or value <= 0 or value == math.huge or value > 1000 then
        return nil
    end
    return value
end

local function getActiveWorkSpeedLimit(vehicle)
    local toolsLimit = getFiniteSpeedLimit(vehicle, true)
    if toolsLimit == nil then
        return nil
    end

    local vehicleLimit = getFiniteSpeedLimit(vehicle, false)
    if vehicleLimit ~= nil and toolsLimit >= vehicleLimit - 0.05 then
        return nil
    end
    return toolsLimit
end

local function getVirtualGear(range, gear)
    return ((range or LOW_RANGE) - 1) * 3 + math.max(1, math.min(gear or 1, 3))
end

local function virtualToRangeGear(virtualGear)
    virtualGear = math.max(1, math.min(virtualGear or 1, 6))
    if virtualGear <= 3 then
        return LOW_RANGE, virtualGear
    end
    return HIGH_RANGE, virtualGear - 3
end

local function getWorkTarget(motor, speedLimit)
    local motorName = getMotorName(motor)
    local high = motorName ~= nil and HIGH_RANGE_SPEEDS[motorName] or nil
    if high == nil or speedLimit == nil then
        return nil, nil, nil, nil
    end

    local speeds = {
        high[1] * LOW_RANGE_RATIO,
        high[2] * LOW_RANGE_RATIO,
        high[3] * LOW_RANGE_RATIO,
        high[1], high[2], high[3]
    }

    -- Choose the highest real gear that would still keep the engine at or above
    -- the useful 1500 rpm floor at the implement's active working speed.
    for virtualGear = 6, 1, -1 do
        local requiredRpm = MAX_RPM * speedLimit / speeds[virtualGear]
        if requiredRpm >= WORK_MIN_RPM_AT_LIMIT then
            local range, gear = virtualToRangeGear(virtualGear)
            return range, gear, virtualGear, requiredRpm
        end
    end

    local requiredRpm = MAX_RPM * speedLimit / speeds[1]
    return LOW_RANGE, 1, 1, requiredRpm
end

local function markDecision(motor, range, gear, reason, workLimit, workTargetVirtual)
    local now = g_time or 0
    motor.c330FixRequestedRange = range
    motor.c330FixRequestedGear = gear
    motor.c330FixRequestedRangeAt = now
    motor.c330FixRequestedRangeReason = reason
    motor.c330WorkSpeedLimit = workLimit
    motor.c330WorkTargetVirtual = workTargetVirtual
end

local function setUpshiftHold(motor, untilTime)
    local current = tonumber(motor.c330FixUpshiftHoldUntil) or 0
    motor.c330FixUpshiftHoldUntil = math.max(current, untilTime)
end

local function requestRange(motor, targetRange, targetGear, reason, workLimit, targetVirtual)
    local now = g_time or 0
    markDecision(motor, targetRange, targetGear, reason, workLimit, targetVirtual)
    if (motor.activeGearGroupIndex or LOW_RANGE) ~= targetRange then
        motor:setGearGroup(targetRange)
    end
    motor.c330FixRangeCooldownUntil = now + RANGE_CHANGE_COOLDOWN_MS
    motor.c330FixRangeRecoverySince = nil
    motor.autoGearChangeTimer = math.max(motor.autoGearChangeTime or 0, RANGE_CHANGE_COOLDOWN_MS)
    return targetGear
end

function C330TransmissionWorkFix:install()
    if self.installed or VehicleMotor == nil then
        return
    end

    local originalPrediction = VehicleMotor.findGearChangeTargetGearPrediction
    if type(originalPrediction) ~= "function" then
        return
    end

    self.installed = true

    VehicleMotor.findGearChangeTargetGearPrediction = function(motor, curGear, gears, gearSign, gearChangeTimer, acceleratorPedal, dt)
        local beforeRange = motor.activeGearGroupIndex or LOW_RANGE
        local result = originalPrediction(motor, curGear, gears, gearSign, gearChangeTimer, acceleratorPedal, dt)

        if not isAutomaticForward(motor)
            or curGear == nil
            or curGear <= 0
            or gears == nil
            or #gears < 1 then
            return result
        end

        -- If the validated base controller changed the mechanical range during
        -- this prediction, never second-guess that same transition in this frame.
        local range = motor.activeGearGroupIndex or LOW_RANGE
        if range ~= beforeRange then
            return result
        end

        local now = g_time or 0
        local rpm = getRpm(motor)
        local load, loadSource = getLoad(motor)
        local accel = math.abs(tonumber(acceleratorPedal) or 0)
        local workLimit = getActiveWorkSpeedLimit(motor.vehicle)
        local workRange, workGear, workVirtual = getWorkTarget(motor, workLimit)

        motor.c330WorkSpeedLimit = workLimit
        motor.c330WorkTargetVirtual = workVirtual
        motor.c330WorkLoadSource = loadSource

        if workLimit ~= nil then
            motor.c330WorkWasActive = true
            motor.c330WorkReleaseHoldUntil = nil
        elseif motor.c330WorkWasActive then
            motor.c330WorkWasActive = false
            motor.c330WorkReleaseHoldUntil = now + WORK_RELEASE_HOLD_MS
            setUpshiftHold(motor, motor.c330WorkReleaseHoldUntil)
            markDecision(motor, range, curGear, "WORK RELEASE HOLD", nil, nil)
        end

        if workVirtual ~= nil then
            local currentVirtual = getVirtualGear(range, curGear)

            -- If the tool becomes active while the tractor is already above the
            -- correct work gear, reduce one real step at a time until it is safe.
            if currentVirtual > workVirtual then
                local targetVirtual = currentVirtual - 1
                local targetRange, targetGear = virtualToRangeGear(targetVirtual)
                setUpshiftHold(motor, now + WORK_RELEASE_HOLD_MS)
                if targetRange ~= range then
                    return requestRange(motor, targetRange, targetGear, "WORK GEAR DOWN", workLimit, workVirtual)
                end
                markDecision(motor, targetRange, targetGear, "WORK GEAR DOWN", workLimit, workVirtual)
                motor.autoGearChangeTimer = math.max(motor.autoGearChangeTime or 0, RANGE_CHANGE_COOLDOWN_MS)
                return targetGear
            end

            -- The selected work gear is a ceiling while the implement speed limit
            -- is active. GIANTS may otherwise keep chasing a taller gear after the
            -- requested field speed has already been reached.
            if currentVirtual == workVirtual and result ~= nil and result > curGear then
                markDecision(motor, range, curGear, "WORK GEAR HOLD", workLimit, workVirtual)
                motor.autoGearChangeTimer = math.max(motor.autoGearChangeTime or 0, 250)
                return curGear
            end

            -- The original controller required load <= 0.55 for I/3 -> II/1.
            -- Under real field load that can trap the tractor in I/3 even when
            -- II/1 is the correct work gear. Permit only this boundary crossing
            -- once RPM and the existing 2 s dwell are both safe.
            if currentVirtual == 3
                and workVirtual >= 4
                and rpm >= WORK_RANGE_UP_RPM
                and now - (motor.c330FixSettledGearSince or now) >= WORK_RANGE_UP_DWELL_MS
                and (motor.c330FixUpshiftHoldUntil == nil or now >= motor.c330FixUpshiftHoldUntil) then
                return requestRange(motor, HIGH_RANGE, 1, "WORK RANGE UP", workLimit, workVirtual)
            end
        end

        -- Recovery failsafe independent of implements. If a tall gear has already
        -- pulled the engine into the lugging zone at high throttle/load, force one
        -- mechanical downshift and hold further upshifts for 2.5 s.
        if curGear > 1
            and accel >= LUG_DOWNSHIFT_ACCEL
            and load ~= nil
            and load >= LUG_DOWNSHIFT_LOAD
            and rpm <= LUG_DOWNSHIFT_RPM then
            local targetGear = curGear - 1
            setUpshiftHold(motor, now + WORK_RELEASE_HOLD_MS)
            markDecision(motor, range, targetGear, "LUG DOWNSHIFT", workLimit, workVirtual)
            motor.autoGearChangeTimer = math.max(motor.autoGearChangeTime or 0, RANGE_CHANGE_COOLDOWN_MS)
            return targetGear
        end

        -- The base controller already uses c330FixUpshiftHoldUntil for range
        -- recovery. Extend that same hold to ordinary within-range upshifts so a
        -- recovery reduction cannot bounce immediately back into the bad gear.
        if result ~= nil
            and result > curGear
            and motor.c330FixUpshiftHoldUntil ~= nil
            and now < motor.c330FixUpshiftHoldUntil then
            markDecision(motor, range, curGear, "BLOCK UPSHIFT HOLD", workLimit, workVirtual)
            motor.autoGearChangeTimer = math.max(motor.autoGearChangeTime or 0, 250)
            return curGear
        end

        return result
    end

    Logging.info("[C330WORKFIX] installed work-speed governor + lug recovery")
end

function C330TransmissionWorkFix:update(dt)
    if not self.installed
        and VehicleMotor ~= nil
        and C330TransmissionFix ~= nil
        and C330TransmissionFix.installed then
        self:install()
    end
end

if not C330TransmissionWorkFix.listenerAdded then
    C330TransmissionWorkFix.listenerAdded = true
    addModEventListener(C330TransmissionWorkFix)
end
