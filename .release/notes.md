## Ursus C-330 / C-330M 0.0.4.0

**Stable dry-tyre physics milestone.**

### Selected values
- Wheel spring **12** (runtime ~120).
- Wheel damper **22**.
- Suspension travel remains **0.07 m**.

These values were selected from standardized obstacle tests at 10 km/h plus a single-board Vmax test at 2.40 and 1.00 bar with MudSystemPhysics. Compared with spring=12 / damper=25, damper=22 reduced the single-wheel peak on the repeatable 10 km/h route at both pressures and reduced zero-contact samples.

Temporary tyre diagnostics are removed from the stable package. Mass/COM, metal ballast, wheel geometry/traction, engine, transmission, differential, MudSystemPhysics behavior and ADS protection are unchanged.

Next development phase: rear tyre liquid ballast with physical mass plus a dedicated filled-tyre response.
