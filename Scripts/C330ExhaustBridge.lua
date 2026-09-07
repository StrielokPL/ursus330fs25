-- Intentionally inert since 0.0.5.1P3.
-- P2 wrapped Vehicle.update and called vehicle:toggleEffects / setParticleIntensity.
-- That was not the Lights.lua:1469 cause. P2/P3 dropped VehicleMotor.updateGear's
-- second return (brakePedal). P4 restores that contract. Do not hook Vehicle.update.
C330ExhaustBridge = {}
