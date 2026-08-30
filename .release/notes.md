## Ursus C-330 / C-330M 0.0.2.3

**Factory ballast mass prerelease.** The 0.0.2.2 base mass/COM result is accepted and remains unchanged.

### 0.0.2.2 confirmed safe point
- base mass: **1675 kg**,
- front/rear: **634 / 1041 kg (37.86 / 62.14%)**,
- factory target: **1675 kg, 635 / 1040 kg**.

### 0.0.2.3 ballast changes
- front ballast: **100 -> 42 kg** total,
- rear Small: stays **40 kg** total,
- rear Big: **80/120 -> 144 kg** total depending visual variant,
- rear Both: **120 -> 184 kg** total.

The visual configurations and ballast locations are unchanged; only their physical masses are corrected.

### Test matrix
Please use the standard C-330 (`motor=1`) and let each configuration settle stationary on level ground for at least 4-5 seconds:
1. base, `wheel=1`, no front ballast — should repeat about **1675 / 634 / 1041 kg**;
2. front ballast only (`design3=2`) — about **1717 / 676 / 1041 kg**;
3. rear Small — about **1715 / 634 / 1081 kg**;
4. rear Big variants — about **1819 / 634 / 1185 kg**;
5. rear Both — about **1859 / 634 / 1225 kg**;
6. front + rear Both — about **1901 / 676 / 1225 kg** (factory full-metal target 1901 / 677 / 1224 kg).

A full `log.txt` is preferred. Engine, transmission, ADS behavior, tyre geometry and accepted base COM are unchanged.

<!-- release-trigger-0.0.2.3-factory-ballast -->
