## Ursus C-330 / C-330M 0.0.4.1

**First functional rear-tyre water ballast prototype.**

### New independent option
- **Water in rear tyres: No / Yes**
- Can be combined with existing metal rear wheel weights.

### Prototype physics
- **+132 kg per rear wheel** = **+264 kg total**.
- Dry rear tyre remains **spring 12 / damper 22**.
- Water-filled rear tyre is approximately **spring 14 / damper 26**.
- Suspension travel remains **0.07 m**.

The filled-tyre spring/damper values are a conservative first test point, not a final target. MudSystemPhysics pressure/radius/friction behavior is left intact.

### Suggested first test
Use basic Polowe tyres, no metal wheel weights or attachments. Compare Water **Off vs On** at settled **2.40 bar** and **1.00 bar** using the established 10 km/h obstacle route plus the single-board Vmax pass. With water On and no metal weights, static total mass should be about **1.939 t**. Send the complete `log.txt`.

Temporary `TyreDebugKit` is restored for this prerelease. Engine/transmission/ADS, base mass/COM and metal ballast are unchanged.

<!-- release-trigger-0.0.4.1-liquid-ballast -->
