## Ursus C-330 / C-330M 0.0.3.2

**Read-only suspension-travel diagnostic prerelease. No physical values changed.**

0.0.3.1 showed that MudSystemPhysics already handles the 2.40/1.00 bar radius/friction layer independently of the C-330 wheel spring. This build measures the missing physical suspension/tire-compliance motion directly.

### Test
One basic tyre family is enough; 0.0.3.1 confirmed Polowe/Szosowe share the same runtime physics.

1. Set **2.40 bar**, let it settle, drive the same three-prop route.
2. Set **1.00 bar**, let the pressure finish changing, repeat at roughly similar speeds.
3. Keep the stone-fire and pallet-truck hits on the **right side** as before.
4. Send the complete `log.txt`.

The log now includes pressure current/target and FL/FR/RL/RR suspension length every 50 ms plus the full GIANTS compression/rebound damper split.

<!-- release-trigger-0.0.3.2-suspension-trace -->
