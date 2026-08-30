## Ursus C-330 / C-330M 0.0.3.3

**First physical tyre-compliance test after the read-only diagnostics.**

### Change
- Common wheel spring **15 -> 12** (**-20%**, runtime about **150 -> 120**).
- `damper=25` and `suspTravel=0.07` stay unchanged so the spring effect can be judged in isolation.

### Why
The 0.0.3.2 multi-height/multi-ramp board route produced repeatable load impulses and showed that the current setup can still deliver very sharp wheel-load peaks. The attempted `lastSuspensionLength` signal stayed fixed at 0.0400 m and is not used for the decision.

### Test
1. Use the same basic Polowe wheel configuration and board sequence.
2. Run once at **2.40 bar** after pressure settles.
3. Run once at **1.00 bar** after pressure settles.
4. Similar obstacle order and speed are more important than an exact speed target.
5. Note if any obstacle causes obvious bottoming, excessive rocking, or a much softer/cleaner hit.
6. Send the complete `log.txt`.

All engine/transmission/ADS behavior, mass/COM/ballast, tire dimensions/traction and MudSystemPhysics are unchanged.

<!-- release-trigger-0.0.3.3-spring-test -->
