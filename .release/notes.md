## Ursus C-330 / C-330M 0.0.3.5

**First isolated damper test on the selected spring=12 tyre baseline.**

### Changes
- Restore selected spring baseline: **15 -> 12** (runtime expected ~150 -> 120).
- New test variable only: common wheel damper **25 -> 22**.

The damper step is intentionally small. After reducing spring from 15 to 12, a simple constant-damping-ratio estimate gives 25 × sqrt(12/15) ≈ 22.36, so 22 is a useful first measured point rather than an arbitrary large change.

### Repeat the standardized route
1. Basic Polowe C-330, no ballast/attachment changes.
2. Settle at **2.40 bar**.
3. Board set + pallet truck + campfire at cruise control **10 km/h**.
4. Single board at **Vmax**.
5. Settle at **1.00 bar** and repeat.
6. Keep obstacle order and line as consistent as practical and send the complete `log.txt`.

`suspTravel=0.07`, wheel geometry/traction, MudSystemPhysics, mass/COM/ballast, engine/transmission/ADS and differential are unchanged.

<!-- release-trigger-0.0.3.5-damper22 -->
