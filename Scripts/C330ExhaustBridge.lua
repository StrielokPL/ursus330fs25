-- Visual-only, per-tractor ADS/GIANTS bridge. Runs after vehicle specialization
-- updates so ExhaustExtension cannot overwrite the selected load in this frame.
C330ExhaustBridge = {}
function C330ExhaustBridge.update(vehicle, dt)
    local spec = vehicle.spec_motorized
    if not vehicle.isClient or not spec or not spec.motor then return end
    local started = C330Runtime.first(vehicle, "getIsMotorStarted") == true
    local load, sourceName = C330Runtime.load(spec.motor)
    local smoke = vehicle.c330Smoke or {load=0}
    vehicle.c330Smoke = smoke
    smoke.source, smoke.rawLoad = sourceName, load
    local target = started and math.min(load or 0, 1) or 0
    local tau = target > smoke.load and 200 or 500
    smoke.load = smoke.load + (target - smoke.load) * (1 - math.exp(-math.max(dt or 0, 0) / tau))
    smoke.extension, smoke.intensity = false, nil
    if not started then smoke.load = 0; return end
    -- Keep the original start sequence; its smoke is not a steady load effect.
    if spec.motorStartTime and vehicle.time and vehicle.time < spec.motorStartTime then return end
    if C330Runtime.first(vehicle, "getIsActive") == false then return end
    for _, effect in ipairs(spec.exhaustEffects or {}) do
        if effect.effectNode and effect.minRpmColor and effect.maxRpmColor then
            local t, lo, hi = smoke.load, effect.minRpmColor, effect.maxRpmColor
            setShaderParameter(effect.effectNode, "exhaustColor",
                lo[1]+(hi[1]-lo[1])*t, lo[2]+(hi[2]-lo[2])*t,
                lo[3]+(hi[3]-lo[3])*t, lo[4]+(hi[4]-lo[4])*t, false)
            -- Preserve native exhaust direction/rotation. Only its size is load-driven.
            if effect.minRpmScale and effect.maxRpmScale and effect.xRot and effect.zRot then
                setShaderParameter(effect.effectNode, "param", effect.xRot, effect.zRot, 0,
                    effect.minRpmScale+(effect.maxRpmScale-effect.minRpmScale)*t, false)
            end
        end
    end
    local ext = vehicle.spec_exhaustExtension
    if ext and ext.initialized and ext.particleSystems and #ext.particleSystems > 0
        and ext.particleModifiers and type(vehicle.toggleEffects) == "function"
        and type(vehicle.setParticleIntensity) == "function"
        and (ext.timer or 0) <= 0 and (ext.timerOffset or -1) <= 0 then
        local m = ext.particleModifiers
        local excess = math.max(0, smoke.load - (m.engineLoadThreshold or 0.5))
        local damage = C330Runtime.number(C330Runtime.first(vehicle, "getDamageAmount")) or 0
        local intensity = math.min(excess * 0.3 * (m.intensityFactor or 1) * (m.engineLoadFactor or 1) * (1+damage), 0.8)
        ext.isActivatedLoad = intensity > 0
        vehicle:toggleEffects(intensity > 0)
        vehicle:setParticleIntensity(intensity)
        smoke.extension, smoke.intensity = true, intensity
    end
end
if Vehicle and type(Vehicle.update) == "function" then
    local original = Vehicle.update
    Vehicle.update = function(vehicle, dt, ...)
        local result = original(vehicle, dt, ...)
        if C330Runtime.isTarget(vehicle) and not vehicle.c330SmokeDisabled then
            local ok, err = pcall(C330ExhaustBridge.update, vehicle, dt)
            if not ok then
                vehicle.c330SmokeDisabled = true
                Logging.warning("[C330EXHAUST] disabled for one vehicle: %s", tostring(err))
            end
        end
        return result
    end
end
