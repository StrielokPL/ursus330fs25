## Ursus C-330 / C-330M 0.0.3.1

**Read-only tyre / MudSystemPhysics pressure diagnostic prerelease.** No physical values are changed from stable 0.0.3.0.

### What this build records
- wheel configuration and mass context,
- FL/FR/RL/RR tire load plus front/rear totals at 100 ms resolution,
- wheel vertical movement relative to the tractor,
- runtime spring, damper, suspension travel/compression candidates, radius, stiffness and friction every 500 ms,
- visual maxDeformation separately,
- pressure-like runtime fields from MudSystemPhysics/tire/wheel specializations every 250 ms and whenever the detected state changes.

### Test plan
Use the unballasted standard C-330 with no attachment. Test both tyre sets. For each set:
1. let the tractor settle at the first MS pressure;
2. keep it stationary for a few seconds;
3. drive the same short route / bump or rough patch;
4. change to the next clearly different MS pressure and repeat.

Use as many pressure steps as convenient; three or more (low / medium / high) will make the spring/damping trend much easier to identify. Send the complete `log.txt`.
