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
