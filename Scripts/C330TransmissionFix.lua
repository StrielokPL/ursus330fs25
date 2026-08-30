-- Ursus C-330 FS25 automatic range controller
-- 0.0.2.0 STABLE: validated 2 s upshift failsafe, mass-aware 6F/2R control and ADS-safe operation.
--
-- The C-330 range box is NOT a powershift splitter. In automatic mode the
-- intended virtual order is:
--   I/1 -> I/2 -> I/3 -> II/1 -> II/2 -> II/3
-- and the reverse order while downshifting.
--
-- Manual modes are left to GIANTS unchanged. Automatic forward and reverse use
-- explicit C-330 range logic. C-330M remains intentionally excluded.

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
    -- Full throttle alone must not force II/1 -> I/3 when the engine is lightly loaded.
    -- 0.0.1.1 runtime trace showed an unnecessary reduction at ~1499 rpm, load 0.335.
    local RANGE_DOWNSHIFT_ACCEL_MIN_LOAD = 0.55
    -- Factory I/3 is 5.649 km/h at 2200 rpm. Allow a small governor margin, but
    -- never command the mechanical II/1 -> I/3 range change above 6.0 km/h.
    -- 6.0 km/h corresponds to ~2337 rpm in I/3, still below the ~2450 rpm
    -- no-load governor speed from the workshop documentation.
    local FORWARD_RANGE_DOWNSHIFT_MAX_SPEED = 6.0
    -- getBestStartGear is not guaranteed to be called during every near-stop.
    -- Force range I deterministically once forward speed is essentially walking pace.
    local FORWARD_LOW_SPEED_RANGE_RESET = 0.5

    -- Mass-aware automatic start requested after the 0.0.1.3 test. The real C-330
    -- base mass is 1675 kg. A complete tractor+implement/trailer set below
    -- 1675 + 1500 = 3175 kg may start directly in I/3, avoiding two unnecessary
    -- low-range shifts when essentially unloaded. At or above the threshold,
    -- keep GIANTS' native start-gear choice, but always in range I.
    local FACTORY_BASE_MASS_T = 1.675
    local LIGHT_START_EXTRA_MASS_T = 1.500
    local LIGHT_START_MAX_TOTAL_MASS_T = FACTORY_BASE_MASS_T + LIGHT_START_EXTRA_MASS_T

    local RANGE_UPSHIFT_RPM = 2050
    local RANGE_UPSHIFT_MAX_LOAD = 0.55
    local RANGE_UPSHIFT_STABLE_MS = 800

    -- Final safety net requested after the 0.0.1.7 runtime test. Once a mechanical
    -- gear/range has settled, no automatic request for a numerically/historically
    -- higher ratio may be issued for the first 2 seconds. Downshifts remain free.
    local UPSHIFT_MIN_DWELL_MS = 2000

    local NORMAL_UPSHIFT_GUARD_LOAD = 0.80
    local NORMAL_UPSHIFT_GUARD_RPM = 1750

    -- II/2 -> II/3 is the largest within-range step. With the factory speed ladder,
    -- engine rpm after the shift is approximately currentRpm * (14.324 / 22.878).
    -- The 0.0.1.1 test allowed a shift at 1695 rpm / load 0.789 and the engine fell
    -- to ~960-980 rpm at ~0.9 load. Keep vanilla freedom at light load, but under
    -- meaningful load require a predicted post-shift speed of at least ~1200 rpm.
    local TOP_GEAR_POSTSHIFT_RPM_RATIO = 14.324 / 22.878
    local TOP_GEAR_POSTSHIFT_MIN_RPM = 1200
    local TOP_GEAR_PREDICTION_GUARD_MIN_LOAD = 0.55
    -- 0.0.1.7 proved that 600 ms is still too short for the large II/2 -> II/3
    -- step on a 3.469 t set. The guard correctly blocked the first requests, but
    -- II/3 could still settle near 1180-1225 rpm with ~0.78-0.85 load. Require
    -- 2 seconds of continuous load below 0.70 before a heavy set may use II/3.
    -- This is independent of, and may overlap with, the generic 2 s gear dwell.
    local TOP_GEAR_HIGH_LOAD = 0.70
    local TOP_GEAR_HIGH_LOAD_MIN_RPM = 2100
    local TOP_GEAR_HEAVY_SET_STABLE_MS = 2000

    local RANGE_CHANGE_COOLDOWN_MS = 800
    local LOAD_RECOVERY_HOLD_MS = 2500
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

    local function isAutomaticC330(motor)
        return isC330Motor(motor)
            and hasFactoryRanges(motor)
            and motor.gearShiftMode == VehicleMotor.SHIFT_MODE_AUTOMATIC
    end

    local function isAutomaticForward(motor)
        return isAutomaticC330(motor)
            and (motor.currentDirection or 1) >= 0
    end

    local function isAutomaticReverse(motor)
        return isAutomaticC330(motor)
            and (motor.currentDirection or 1) < 0
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

    local function getTotalMassTons(motor)
        local vehicle = motor ~= nil and motor.vehicle or nil
        if vehicle ~= nil and vehicle.getTotalMass ~= nil then
            local value = tonumber(vehicle:getTotalMass())
            if value ~= nil and value > 0 then
                return value
            end
        end
        return nil
    end

    local function getForwardStartGear(motor, gears, fallbackGear)
        local maxGear = math.min(#gears, 3)
        local gear = math.max(1, math.min(fallbackGear or 1, maxGear))
        local totalMass = getTotalMassTons(motor)

        if maxGear >= 3
            and totalMass ~= nil
            and totalMass < LIGHT_START_MAX_TOTAL_MASS_T then
            return 3, totalMass, "LIGHT_I3"
        end

        return gear, totalMass, "NATIVE_LOW_RANGE"
    end

    local function getReverseStartRange(motor)
        local totalMass = getTotalMassTons(motor)

        if totalMass ~= nil and totalMass < LIGHT_START_MAX_TOTAL_MASS_T then
            return HIGH_RANGE, totalMass, "LIGHT_RII"
        end

        return LOW_RANGE, totalMass, "NATIVE_RI"
    end

    local function logForwardStartGear(motor, gear, totalMass, mode)
        local now = g_time or 0
        if motor.c330FixStartGearLogUntil ~= nil and now < motor.c330FixStartGearLogUntil then
            return
        end
        motor.c330FixStartGearLogUntil = now + 500

        Logging.info(
            "[C330TRANS] START GEAR I/%d totalMass=%s threshold=%.3f mode=%s",
            gear or 0,
            totalMass ~= nil and string.format("%.3f", totalMass) or "n/a",
            LIGHT_START_MAX_TOTAL_MASS_T,
            tostring(mode)
        )
    end

    local function logReverseStartRange(motor, range, totalMass, mode)
        local now = g_time or 0
        if motor.c330FixReverseStartLogUntil ~= nil and now < motor.c330FixReverseStartLogUntil then
            return
        end
        motor.c330FixReverseStartLogUntil = now + 500

        Logging.info(
            "[C330TRANS] START REVERSE R-%s totalMass=%s threshold=%.3f mode=%s",
            range == HIGH_RANGE and "II" or "I",
            totalMass ~= nil and string.format("%.3f", totalMass) or "n/a",
            LIGHT_START_MAX_TOTAL_MASS_T,
            tostring(mode)
        )
    end

    local function getLoad(motor)
        local vehicle = motor ~= nil and motor.vehicle or nil
        local adsSpec = vehicle ~= nil and vehicle.spec_AdvancedDamageSystem or nil
        local adsLoad = adsSpec ~= nil and tonumber(adsSpec.dynamicMotorLoad) or nil

        -- ADS briefly reports negative values around shifts. Treat those as an
        -- unavailable sample and fall back to the native GIANTS load instead.
        -- ADS dynamicMotorLoad is treated as a read-only 0..1 signal. Values
        -- outside that range (including the negative shift sentinels visible in
        -- runtime logs) are never used for a shift decision. A tiny numerical
        -- tolerance above 1.0 is accepted and clamped.
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

    local function getUpshiftDwellState(motor, range, gear, now)
        local direction = (motor.currentDirection or 1) < 0 and -1 or 1
        local key = string.format("%d:%d:%d", direction, range or 0, gear or 0)

        if motor.c330FixSettledGearKey ~= key then
            motor.c330FixSettledGearKey = key
            motor.c330FixSettledGearSince = now
            return false, 0
        end

        local age = now - (motor.c330FixSettledGearSince or now)
        return age >= UPSHIFT_MIN_DWELL_MS, age
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
        local now = g_time or 0

        -- Diagnostic breadcrumb only. TractorDebugKit uses this to tell a range
        -- change explicitly requested here from one performed elsewhere by the
        -- GIANTS transmission state machine. No ADS state is written.
        motor.c330FixRequestedRange = targetRange
        motor.c330FixRequestedGear = targetGear
        motor.c330FixRequestedRangeAt = now
        motor.c330FixRequestedRangeReason = reason

        if targetRange ~= currentRange then
            motor:setGearGroup(targetRange)
        end

        motor.c330FixRangeCooldownUntil = now + RANGE_CHANGE_COOLDOWN_MS
        motor.c330FixRangeRecoverySince = nil
        if recoveryHold then
            motor.c330FixUpshiftHoldUntil = now + LOAD_RECOVERY_HOLD_MS
        end
        motor.autoGearChangeTimer = math.max(motor.autoGearChangeTime or 0, RANGE_CHANGE_COOLDOWN_MS)

        logDecision(motor, reason, currentGear, currentRange, targetGear, targetRange, rpm, load, loadSource)
        return targetGear
    end

    -- GIANTS automatic group selection treats the two mechanical C-330 ranges as
    -- unrelated optimization choices. Disable it for the complete automatic 6F/2R
    -- gearbox. Manual modes still keep base-game group handling.
    function VehicleMotor:getUseAutomaticGroupShifting()
        if isAutomaticC330(self) then
            return false
        end

        return originalGetUseAutomaticGroupShifting(self)
    end

    function VehicleMotor:getBestStartGear(gears)
        local gear, group = originalGetBestStartGear(self, gears)

        if isAutomaticC330(self) then
            local startRange = LOW_RANGE
            gear = math.max(1, math.min(gear or 1, math.min(#gears, 3)))

            -- Forward: light set starts directly in I/3. Reverse now mirrors the
            -- same mass rule: below 3.175 t start directly in R-II, while a heavy
            -- set starts in R-I and may later recover to R-II normally.
            if isAutomaticForward(self) and #gears >= 3 then
                local totalMass, startMode
                gear, totalMass, startMode = getForwardStartGear(self, gears, gear)
                logForwardStartGear(self, gear, totalMass, startMode)
            elseif isAutomaticReverse(self) then
                local totalMass, startMode
                gear = 1
                startRange, totalMass, startMode = getReverseStartRange(self)
                logReverseStartRange(self, startRange, totalMass, startMode)
            end

            group = startRange

            -- Mark every controller-forced start range so TractorDebugKit can
            -- distinguish it from GIANTS group selection.
            if self.activeGearGroupIndex ~= startRange then
                local now = g_time or 0
                self.c330FixRequestedRange = startRange
                self.c330FixRequestedGear = gear
                self.c330FixRequestedRangeAt = now
                if isAutomaticReverse(self) then
                    self.c330FixRequestedRangeReason = startRange == HIGH_RANGE
                        and "START REVERSE R-II" or "START REVERSE R-I"
                else
                    self.c330FixRequestedRangeReason = "START RANGE RESET"
                end
                self:setGearGroup(startRange)
            end

            self.c330FixRangeRecoverySince = nil
        end

        return gear, group
    end

    function VehicleMotor:findGearChangeTargetGearPrediction(curGear, gears, gearSign, gearChangeTimer, acceleratorPedal, dt)
        local vanillaTarget = originalFindGearChangeTargetGearPrediction(
            self, curGear, gears, gearSign, gearChangeTimer, acceleratorPedal, dt
        )

        if not isAutomaticC330(self)
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
        local totalMass = getTotalMassTons(self)
        local accel = math.abs(tonumber(acceleratorPedal) or 0)
        local maxGear = math.min(#gears, 3)
        local upshiftDwellReady, upshiftDwellAge = getUpshiftDwellState(self, range, curGear, now)

        -- 0.0.1.2 showed that a near-stop can occasionally continue in range II
        -- without getBestStartGear resetting the box first. Do not allow the
        -- automatic forward transmission to re-accelerate through II/2 or II/3
        -- from walking pace: a real C-330 restarts in range I.
        if isAutomaticForward(self)
            and range == HIGH_RANGE
            and speed <= FORWARD_LOW_SPEED_RANGE_RESET then
            local resetGear, totalMass, startMode = getForwardStartGear(self, gears, 1)
            logForwardStartGear(self, resetGear, totalMass, startMode)
            return setAutomaticRange(
                self, LOW_RANGE, resetGear, "LOW SPEED RANGE RESET",
                rpm, load, loadSource, false
            )
        end

        -- Reverse has one mechanical reverse gear passing through the same I/II
        -- range box: R-I ~= 1.53 km/h, R-II ~= 6.21 km/h. GIANTS previously
        -- selected range II around 1.5 km/h even at ~0.8 ADS load. Treat reverse
        -- as a two-step gearbox and only leave range I after sustained recovery.
        if isAutomaticReverse(self) then
            if range == HIGH_RANGE
                and curGear == 1
                and speed > 0.3
                and rpm <= RANGE_DOWNSHIFT_RPM
                and (
                    (load ~= nil and load >= RANGE_DOWNSHIFT_LOAD)
                    or (accel >= RANGE_DOWNSHIFT_ACCEL and load ~= nil and load >= RANGE_DOWNSHIFT_ACCEL_MIN_LOAD)
                ) then
                return setAutomaticRange(
                    self, LOW_RANGE, 1, "REVERSE RANGE DOWN",
                    rpm, load, loadSource, true
                )
            end

            local reverseRecoveryBaseReady = range == LOW_RANGE
                and curGear == 1
                and rpm >= RANGE_UPSHIFT_RPM
                and (load == nil or load <= RANGE_UPSHIFT_MAX_LOAD)
                and (self.c330FixUpshiftHoldUntil == nil or now >= self.c330FixUpshiftHoldUntil)

            if reverseRecoveryBaseReady and not upshiftDwellReady then
                logDecision(self, "BLOCK REVERSE UPSHIFT DWELL", curGear, range, curGear, range, rpm, load, loadSource)
            end

            local reverseRecoveryReady = reverseRecoveryBaseReady and upshiftDwellReady

            if reverseRecoveryReady then
                if self.c330FixRangeRecoverySince == nil then
                    self.c330FixRangeRecoverySince = now
                elseif now - self.c330FixRangeRecoverySince >= RANGE_UPSHIFT_STABLE_MS then
                    return setAutomaticRange(
                        self, HIGH_RANGE, 1, "REVERSE RANGE UP",
                        rpm, load, loadSource, false
                    )
                end
            else
                self.c330FixRangeRecoverySince = nil
            end

            -- There is only one backwardGear. Range selection above is therefore
            -- the complete reverse automatic logic; never hand group choice back
            -- to vanilla while reversing.
            return 1
        end

        -- The critical missing behavior in vanilla: II/1 must be allowed to fall
        -- back to I/3 BEFORE the tractor nearly stops. This is the real next lower
        -- ratio in the C-330 six-step sequence.
        if range == HIGH_RANGE
            and curGear == 1
            and speed > 0.5
            and speed <= FORWARD_RANGE_DOWNSHIFT_MAX_SPEED
            and rpm <= RANGE_DOWNSHIFT_RPM
            and (
                (load ~= nil and load >= RANGE_DOWNSHIFT_LOAD)
                or (accel >= RANGE_DOWNSHIFT_ACCEL and load ~= nil and load >= RANGE_DOWNSHIFT_ACCEL_MIN_LOAD)
            ) then
            return setAutomaticRange(
                self, LOW_RANGE, maxGear, "RANGE DOWN",
                rpm, load, loadSource, true
            )
        end

        -- Crossing the other boundary is I/3 -> II/1. The 0.0.0.4 log showed
        -- that a single recovered sample was not enough: under a heavy trailer the
        -- tractor could upshift and request I/3 again roughly a second later.
        -- Require sustained recovery before leaving range I. This also limits
        -- artificial shift cycling seen by ADS.
        local rangeRecoveryBaseReady = range == LOW_RANGE
            and curGear == maxGear
            and rpm >= RANGE_UPSHIFT_RPM
            and (load == nil or load <= RANGE_UPSHIFT_MAX_LOAD)
            and (self.c330FixUpshiftHoldUntil == nil or now >= self.c330FixUpshiftHoldUntil)

        if rangeRecoveryBaseReady and not upshiftDwellReady then
            logDecision(self, "BLOCK RANGE UPSHIFT DWELL", curGear, range, curGear, range, rpm, load, loadSource)
        end

        local rangeRecoveryReady = rangeRecoveryBaseReady and upshiftDwellReady

        if rangeRecoveryReady then
            if self.c330FixRangeRecoverySince == nil then
                self.c330FixRangeRecoverySince = now
            elseif now - self.c330FixRangeRecoverySince >= RANGE_UPSHIFT_STABLE_MS then
                return setAutomaticRange(
                    self, HIGH_RANGE, 1, "RANGE UP",
                    rpm, load, loadSource, false
                )
            end
        else
            self.c330FixRangeRecoverySince = nil
        end

        -- Keep vanilla's useful within-range prediction, but never let it skip
        -- multiple mechanical gears in a single decision.
        local targetGear = vanillaTarget or curGear
        if targetGear > curGear + 1 then
            targetGear = curGear + 1
        elseif targetGear < curGear - 1 then
            targetGear = curGear - 1
        end

        targetGear = math.max(1, math.min(targetGear, maxGear))

        -- Special protection for II/2 -> II/3 with the calibrated 100 Nm engine.
        -- Heavy sets use a short recovery hold so a transient ADS dip cannot open
        -- top gear while the tractor is still pulling hard. ADS remains read-only.
        if range == HIGH_RANGE
            and curGear == 2
            and targetGear == 3
            and load ~= nil then
            local heavySet = totalMass ~= nil and totalMass >= LIGHT_START_MAX_TOTAL_MASS_T

            if heavySet then
                if load >= TOP_GEAR_HIGH_LOAD then
                    self.c330FixTopGearLowLoadSince = nil
                    logDecision(self, "BLOCK TOP UPSHIFT HEAVY SET", curGear, range, curGear, range, rpm, load, loadSource)
                    self.autoGearChangeTimer = math.max(self.autoGearChangeTime or 0, 250)
                    return curGear
                end

                if self.c330FixTopGearLowLoadSince == nil then
                    self.c330FixTopGearLowLoadSince = now
                    logDecision(self, "BLOCK TOP UPSHIFT STABILIZE", curGear, range, curGear, range, rpm, load, loadSource)
                    self.autoGearChangeTimer = math.max(self.autoGearChangeTime or 0, 250)
                    return curGear
                elseif now - self.c330FixTopGearLowLoadSince < TOP_GEAR_HEAVY_SET_STABLE_MS then
                    logDecision(self, "BLOCK TOP UPSHIFT STABILIZE", curGear, range, curGear, range, rpm, load, loadSource)
                    self.autoGearChangeTimer = math.max(self.autoGearChangeTime or 0, 250)
                    return curGear
                end
            else
                self.c330FixTopGearLowLoadSince = nil

                -- Preserve the 0.0.1.6 light-set high-load safeguard.
                if load >= TOP_GEAR_HIGH_LOAD and rpm < TOP_GEAR_HIGH_LOAD_MIN_RPM then
                    logDecision(self, "BLOCK TOP UPSHIFT HIGH LOAD", curGear, range, curGear, range, rpm, load, loadSource)
                    self.autoGearChangeTimer = math.max(self.autoGearChangeTime or 0, 250)
                    return curGear
                end
            end

            if load >= TOP_GEAR_PREDICTION_GUARD_MIN_LOAD then
                local predictedRpm = rpm * TOP_GEAR_POSTSHIFT_RPM_RATIO
                if predictedRpm < TOP_GEAR_POSTSHIFT_MIN_RPM then
                    logDecision(self, "BLOCK TOP UPSHIFT", curGear, range, curGear, range, rpm, load, loadSource)
                    self.autoGearChangeTimer = math.max(self.autoGearChangeTime or 0, 250)
                    return curGear
                end
            end
        else
            self.c330FixTopGearLowLoadSince = nil
        end

        -- Generic 2-second failsafe. The top-gear load timer above may run in
        -- parallel, but no within-range automatic upshift can actually be issued
        -- until the current settled gear has existed for at least 2 seconds.
        if targetGear > curGear and not upshiftDwellReady then
            logDecision(self, "BLOCK UPSHIFT DWELL", curGear, range, curGear, range, rpm, load, loadSource)
            self.autoGearChangeTimer = math.max(self.autoGearChangeTime or 0, 250)
            return curGear
        end

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

    Logging.info("[C330TRANS] 0.0.2.0 C-330 6F/2R controller installed (stable, 2s upshift failsafe, mass-aware reverse start, ADS-safe)")
end
