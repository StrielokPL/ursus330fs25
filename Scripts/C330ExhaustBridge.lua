-- Intentionally inert in 0.0.5.1P3.
-- P2 wrapped Vehicle.update and called vehicle:toggleEffects / setParticleIntensity.
-- That produced Lights.lua:1469 math.abs(nil) every frame and froze the tractor.
-- Keep the filename so extraSourceFiles stays valid; do not hook Vehicle.update.
C330ExhaustBridge = {}
