## Ursus C-330 / C-330M 0.0.2.1

**Mass / COM diagnostic prerelease. No physics values are changed from stable 0.0.2.0.**

### Purpose
Measure the standard C-330 on one common basic-wheel baseline and determine the real runtime effect of cabin and ballast configurations before moving any center of mass or changing ballast mass.

### Diagnostics
The temporary read-only `TractorDebugKit` is restored for this prerelease and records:
- active configuration indices,
- total runtime mass,
- front/rear tire loads and percentage split,
- each component runtime mass and center of mass,
- wheel masses and static wheel loads.

Engine periodic trace, transmission-change trace and ADS load reading are disabled for this test. The production 0.0.2.0 transmission controller is untouched.

### Suggested test matrix
Keep **basic wheels** for every sample. Start with the plain/unballasted tractor, then test the cabin variants, front ballast, rear wheel ballast and useful cabin+ballast combinations. Let each configuration stand still on flat ground for several seconds so the 3.5 s settled snapshot is recorded.

### Reference target
Unballasted ready-to-work C-330: **1675 kg**, approximately **635 kg front / 1040 kg rear**, or about **38/62**.

Send the complete `log.txt`; the configuration numbers in the log will let us reconstruct the tested combinations.
