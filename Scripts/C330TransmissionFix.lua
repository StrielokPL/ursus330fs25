-- Ursus C-330 FS25 automatic range controller
-- 0.0.0.4 TEST: factory 3-speed main gearbox x 2 mechanical ranges.
--
-- The C-330 range box is NOT a powershift splitter. In automatic mode the
-- intended virtual order is:
--   I/1 -> I/2 -> I/3 -> II/1 -> II/2 -> II/3
-- and the reverse order while downshifting.
--
-- Manual modes are left to GIANTS unchanged. C-330M is intentionally excluded
-- from this test until its own gearing is calibrated.

C330TransmissionFix = C330TransmissionFix or {}

if not C330TransmissionFix.installed then
    C330TransmissionFix.installed = true

    local modDirectory = g_currentModDirectory

    local originalGetBestStartGear = VehicleMotor.getBestStartGear
    local originalFindGearChangeTargetGearPrediction = VehicleMotor.findGearChangeTargetGearPrediction
    local originalGetUseAutomaticGroupShifting = VehicleMotor.getUseAutomaticGroupShifting

    local LOW_RANGE = 1
    local HIGH_RANGE = 2

    -- First-pass thresholds for the diagnostic gearbox test. They are deliberately
    -- conservative and will be tuned from [TRACTORDBG] + [C330TRANS] logs.
    local RANGE_DOWNSHIFT_RPM = 1500
    local RANGE_DOWNSHIFT_LOAD = 0.75
    local RANGE_DOWNSHIFT_ACCEL = 0.85

    local RANGE_UPSHIFT_RPM = 1950
    local RANGE_UPSHIFT_MAX_LOAD = 0.72

    local NORMAL_UPSHIFT_GUARD_LOAD = 0.80
    local NORMAL_UPSHIFT_GUARD_RPM = 1750

    local RANGE_CHANGE_COOLDOWN_MS = 650
    local LOAD_RECOVERY_HOLD_MS = 1800
    local LOG_COOLDOWN_MS = 1200

    local function endsWith(value, suffix)
        return value ~= nil
            and suffix ~= nil
            and string.sub(value, -string.len(suffix)) == suffix
    end

    local function isTargetVehicle(vehicle)
        if vehicle == nil or vehicle.configFileName == nil then
            return false
        end

        if modDirectory ~= nil
            and string.sub(vehicle.configFileName, 1, string.len(modDirectory)) ~= modDirectory then
            return false
        end

        return endsWith(vehicle.configFileName, "c330m.xml")
    end

    local function getSelectedMotorConfigurationName(vehicle)
        if vehicle == nil or vehicle.configurations == nil or vehicle.configurations.motor == nil then
            return nil
        end

        local xmlFile = vehicle.xmlFile
        if xmlFile == nil then
            return nil
        end

        local key = ConfigurationUtil.getXMLConfigurationKey(
            xmlFile,
            vehicle.configurations.motor,
            "vehicle.motorized.motorConfigurations.motorConfiguration",
            "vehicle.motorized",
            "motor"
        )
        if key == nil then
            return nil
        end

        return xmlFile:getValue(key .. "#name")
    end

    local function isC330Motor(motor)
        if motor == nil or not isTargetVehicle(motor.vehicle) then
            return false
        end

        if motor.c330FixTargetCache == nil then
            motor.c330FixTargetCache = getSelectedMotorConfigurationName(motor.vehicle) == "C-330"
        end

        return motor.c330FixTargetCache == true
    end

    local function hasFactoryRanges(motor)
        return motor ~= nil
            and motor.gearGroups ~= nil
            and #motor.gearGroups == 2
            and motor.gearGroups[LOW_RANGE] ~= nil
            and motor.gearGroups[HIGH_RANGE] ~= nil
    end

    local function isAutomaticForward(motor)
        return isC330Motor(motor)
            and hasFactoryRanges(motor)
            and motor.gearShiftMode == VehicleMotor.SHIFT_MODE_AUTOMATIC
            and (motor.currentDirection or 1) >= 0
    end

    local function getRpm(motor)
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

    local function getSpeed(motor)
        local vehicle = motor ~= nil and motor.vehicle or nil
        if vehicle ~= nil and vehicle.getLastSpeed ~= nil then
            return tonumber(vehicle:getLastSpeed()) or 0
        end
        return 0
    end

    local function getLoad(motor)
        local vehicle = motor ~= nil and motor.vehicle or nil
        local adsSpec = vehicle ~= nil and vehicle.spec_AdvancedDamageSystem or nil
        local adsLoad = adsSpec ~= nil and tonumber(adsSpec.dynamicMotorLoad) or nil

        -- ADS briefly reports negative values around shifts. Treat those as an
        -- unavailable sample and fall back to the native GIANTS load instead.
        if adsLoad ~= nil and adsLoad >= 0 then
            return math.clamp(adsLoad, 0, 1.5), "ADS"
        end

        if motor ~= nil and motor.getSmoothLoadPercentage ~= nil then
            local nativeLoad = tonumber(motor:getSmoothLoadPercentage())
            if nativeLoad ~= nil then
                return math.clamp(nativeLoad, 0, 1.5), "GIANTS"
            end
        end

        return nil, "n/a"
    end

    local function logDecision(motor, action, fromGear, fromRange, toGear, toRange, rpm, load, loadSource)
        local now = g_time or 0
        if motor.c330FixLogUntil ~= nil and now < motor.c330FixLogUntil then
            return
        end
        motor.c330FixLogUntil = now + LOG_COOLDOWN_MS

        Logging.info(
            "[C330TRANS] %s %s/%d -> %s/%d rpm=%d load=%s source=%s speed=%.2f",
            action,
            fromRange == LOW_RANGE and "I" or "II",
            fromGear or 0,
            toRange == LOW_RANGE and "I" or "II",
            toGear or 0,
            math.floor((rpm or 0) + 0.5),
            load ~= nil and string.format("%.3f", load) or "n/a",
            tostring(loadSource),
            getSpeed(motor)
        )
    end

    local function setAutomaticRange(motor, targetRange, targetGear, reason, rpm, load, loadSource, recoveryHold)
        local currentRange = motor.activeGearGroupIndex or LOW_RANGE
        local currentGear = motor.targetGear or motor.gear or 0

        if targetRange ~= currentRange then
            motor:setGearGroup(targetRange)
        end

        local now = g_time or 0
        motor.c330FixRangeCooldownUntil = now + RANGE_CHANGE_COOLDOWN_MS
        if recoveryHold then
            motor.c330FixUpshiftHoldUntil = now + LOAD_RECOVERY_HOLD_MS
        end
        motor.autoGearChangeTimer = math.max(motor.autoGearChangeTime or 0, RANGE_CHANGE_COOLDOWN_MS)

        logDecision(motor, reason, currentGear, currentRange, targetGear, targetRange, rpm, load, loadSource)
        return targetGear
    end

    -- GIANTS automatic group selection treats the two C-330 ranges as unrelated
    -- optimization choices. Disable that only while driving forward in automatic
    -- mode; reverse and all manual modes keep the base-game behavior for now.
    function VehicleMotor:getUseAutomaticGroupShifting()
        if isAutomaticForward(self) then
            return false
        end

        return originalGetUseAutomaticGroupShifting(self)
    end

    function VehicleMotor:getBestStartGear(gears)
        local gear, group = originalGetBestStartGear(self, gears)

        if isAutomaticForward(self) then
            group = LOW_RANGE
            gear = math.max(1, math.min(gear or 1, math.min(#gears, 3)))

            if self.activeGearGroupIndex ~= LOW_RANGE then
                self:setGearGroup(LOW_RANGE)
            end
        end

        return gear, group
    end

    function VehicleMotor:findGearChangeTargetGearPrediction(curGear, gears, gearSign, gearChangeTimer, acceleratorPedal, dt)
        local vanillaTarget = originalFindGearChangeTargetGearPrediction(
            self, curGear, gears, gearSign, gearChangeTimer, acceleratorPedal, dt
        )

        if not isAutomaticForward(self)
            or vanillaTarget == nil
            or curGear == nil
            or curGear <= 0
            or gears == nil
            or #gears < 1 then
            return vanillaTarget
        end

        local now = g_time or 0
        if self.c330FixRangeCooldownUntil ~= nil and now < self.c330FixRangeCooldownUntil then
            return curGear
        end

        local range = self.activeGearGroupIndex or LOW_RANGE
        local rpm = getRpm(self)
        local load, loadSource = getLoad(self)
        local speed = getSpeed(self)
        local accel = math.abs(tonumber(acceleratorPedal) or 0)
        local maxGear = math.min(#gears, 3)

        -- The critical missing behavior in vanilla: II/1 must be allowed to fall
        -- back to I/3 BEFORE the tractor nearly stops. This is the real next lower
        -- ratio in the C-330 six-step sequence.
        if range == HIGH_RANGE
            and curGear == 1
            and speed > 0.5
            and rpm <= RANGE_DOWNSHIFT_RPM
            and ((load ~= nil and load >= RANGE_DOWNSHIFT_LOAD) or accel >= RANGE_DOWNSHIFT_ACCEL) then
            return setAutomaticRange(
                self, LOW_RANGE, maxGear, "RANGE DOWN",
                rpm, load, loadSource, true
            )
        end

        -- Crossing the other boundary is I/3 -> II/1. Do it only when the engine
        -- is genuinely ready; a load-recovery hold prevents an immediate undo of
        -- the protective downshift above.
        if range == LOW_RANGE
            and curGear == maxGear
            and rpm >= RANGE_UPSHIFT_RPM
            and (load == nil or load <= RANGE_UPSHIFT_MAX_LOAD)
            and (self.c330FixUpshiftHoldUntil == nil or now >= self.c330FixUpshiftHoldUntil) then
            return setAutomaticRange(
                self, HIGH_RANGE, 1, "RANGE UP",
                rpm, load, loadSource, false
            )
        end

        -- Keep vanilla's useful within-range prediction, but never let it skip
        -- multiple mechanical gears in a single decision.
        local targetGear = vanillaTarget
        if targetGear > curGear + 1 then
            targetGear = curGear + 1
        elseif targetGear < curGear - 1 then
            targetGear = curGear - 1
        end

        targetGear = math.max(1, math.min(targetGear, maxGear))

        -- Do not allow a normal upshift when the engine is already heavily loaded
        -- below the useful upper-RPM band. ADS is preferred when present; native
        -- GIANTS smooth load is used otherwise.
        if targetGear > curGear
            and load ~= nil
            and load >= NORMAL_UPSHIFT_GUARD_LOAD
            and rpm < NORMAL_UPSHIFT_GUARD_RPM then
            logDecision(self, "BLOCK UPSHIFT", curGear, range, curGear, range, rpm, load, loadSource)
            self.autoGearChangeTimer = math.max(self.autoGearChangeTime or 0, 250)
            return curGear
        end

        return targetGear
    end

    Logging.info("[C330TRANS] 0.0.0.4 C-330 3x2 range controller installed")
end
