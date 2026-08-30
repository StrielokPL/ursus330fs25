## Ursus C-330 / C-330M 0.0.3.4

**A/B control for the new stabilized obstacle-test protocol.**

### Change
- Common wheel spring **12 -> 15** (runtime expected about **120 -> 150**).
- This deliberately restores the pre-0.0.3.3 spring for one controlled comparison. It is not yet a final tuning decision.

### Why
The test method changed after spring had already been reduced in 0.0.3.3. The 0.0.3.3 log is therefore the first clean baseline for the new route, but there is no spring=15 run under exactly the same conditions. 0.0.3.4 supplies that missing control.

### Repeat exactly
1. Basic Polowe C-330, same configuration.
2. Let **2.40 bar** settle.
3. Board set + pallet truck + campfire on cruise control **10 km/h**.
4. Single board at **Vmax**.
5. Let **1.00 bar** settle and repeat the same two tests.
6. Keep the same line/order as closely as practical and send the complete `log.txt`.

`damper=25`, `suspTravel=0.07`, tyre dimensions/traction, MudSystemPhysics, mass/COM/ballast, engine/transmission/ADS and differential are unchanged.
