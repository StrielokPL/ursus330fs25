## Ursus C-330 / C-330M 0.0.2.2

**Base mass / COM correction prerelease.** This is the first physics change after the 0.0.2.1 measurement pass.

### Measured 0.0.2.1 baseline
- basic wheels, no ballast: 1683 kg,
- front/rear: about 605 / 1078 kg (35.97 / 64.03%),
- factory target: 1675 kg and 635 / 1040 kg (37.9 / 62.1%).

All tested cabin `vehicleType` variants were mass-neutral. Rear wheel options added +40/+80/+120 kg at the rear, and the current front ballast added +100 kg at the front.

### 0.0.2.2 change
Only base component 1 changes:
- nominal mass **800 -> 792 kg**,
- longitudinal COM **Z -0.200 -> -0.125 m**.

The calculated target with a full tank is approximately **1675 kg and 635/1040 kg**. Temporary static mass diagnostics remain enabled to verify the result in runtime.

### Test
Use basic wheels, no ballast and preferably the simplest/no-cabin configuration first. Leave the tractor stationary on level ground for at least 4-5 seconds. One clean base snapshot is enough to judge the correction; additional cabin/ballast snapshots are welcome but not required for this iteration.

Transmission, engine, ADS behavior, tyres and ballast masses are unchanged.

<!-- release-trigger-0.0.2.2-mass-com -->
