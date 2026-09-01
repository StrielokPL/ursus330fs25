## Ursus C-330 / C-330M 0.0.4.2

**Water-ballast damping A/B test.**

0.0.4.1 confirmed that the independent water option works correctly: **+132 kg per rear wheel**, **1.939 t** total on the basic tractor, front axle essentially unchanged and the added 264 kg carried by the rear axle. MudSystemPhysics pressure/radius behavior also remains active.

### Only physical change
- Water-filled rear tyres: **spring 14 / damper 30** (was 14 / 26).
- Dry tyres stay **12 / 22**.
- `suspTravel=0.07` and liquid mass stay unchanged.

### Test
Use the same basic Polowe tyres and standardized route. Compare water On at settled **1.00 bar** and **2.40 bar**: boards + pallet jack + firepit at cruise-control **10 km/h**, then the single board at Vmax. The key question is whether the stronger damping shortens the zero-load/rebound episodes without making impacts harsher. Send the complete `log.txt`.

Temporary TyreDebugKit remains enabled for this prerelease.
