## Ursus C-330 / C-330M 0.0.5.0

**Prerelease calibration test focused on C-330M.** The stable C-330 0.0.4.3 baseline is intentionally preserved; C-330M now inherits the validated shared physics and drivetrain behavior wherever the real tractors use the same systems.

### C-330M inherited from the validated C-330 baseline

- Same S-312C calibration: **100 Nm target**, **600-2200 rpm**, approximately **22.4 kW / 30 hp** at rated speed.
- Same calibrated torque curve as C-330.
- Same base vehicle mass/COM and shared wheel physics.
- Same dry tyre setup: **spring 12 / damper 22 / suspTravel 0.07**.
- Same rear tyre water ballast: **+132 kg per rear wheel / +264 kg total**, approximately **spring 14 / damper 30** when filled.
- Same shop ordering: **Engine -> Wheels -> Water -> Front ballast -> Cabin -> Loader console**.
- Same automatic 6F/2R controller, including mass-aware starts, range logic, 2 s upshift dwell, RPM/load protections and optional read-only ADS load input.

### C-330M-specific gearing

The M variant keeps the same three gearbox-step proportions and the same low/high range ratio as the calibrated C-330, while the complete speed set is scaled to a working top-speed target of **26.290 km/h**.

High range / nominal max speed at 2200 rpm:

- **II/1: 8.491 km/h**
- **II/2: 16.460 km/h**
- **II/3: 26.290 km/h**
- **R-II: 7.133 km/h**

Low range uses the same **0.24691358** ratio:

- **I/1: ~2.097 km/h**
- **I/2: ~4.064 km/h**
- **I/3: ~6.491 km/h**
- **R-I: ~1.761 km/h**

### Important test status

- **C-330 remains the 0.0.4.3 stable calibration.** Its XML speed set and torque curve were not changed.
- **C-330M 0.0.5.0 is not yet validated in gameplay.** This prerelease needs the same staged road/load/hill checks previously used for C-330.
- Current rebuild multiplayer remains **not yet fully validated**.
- The shared shop-order and liquid-ballast helpers already target `c330m.xml`, so both motor variants use them without duplicate hooks.

Recommended first test: buy a fresh C-330M, verify 30 hp/100 Nm behavior, manual and automatic `I/1 -> I/2 -> I/3 -> II/1 -> II/2 -> II/3`, unloaded top speed around 26.3 km/h, reverse around 7.1 km/h, then repeat with a moderate implement/trailer and ADS/MudSystemPhysics enabled.
