# Ursus C-330 — technical baseline for FS25

This file is the reference baseline for rebuilding the **Ursus C-330** configuration in this mod. It intentionally separates confirmed real-world data from values that still need to be tuned in-game.

## 1. Real tractor — target data

### Engine S-312C
- 2-cylinder, 4-stroke naturally aspirated diesel, direct injection
- displacement: **1960 cm³**
- bore x stroke: **102 x 120 mm**
- compression ratio: **17:1**
- rated power: **22.4 kW / ~30.5 hp at 2200 rpm**
- maximum torque: **100 Nm at 1600-1800 rpm**
- idle speed: **~550 rpm**
- maximum no-load speed: **~2450 rpm**
- fuel tank: **35 l**
- factory specific fuel consumption: about **265 g/kWh** at rated load

### Mass and balance
Factory service documentation gives the ready-to-work tractor, without additional ballast, as:
- total: **1675 kg**
- front axle: **635 kg (37.9%)**
- rear axle: **1040 kg (62.1%)**

With all factory metal ballast:
- total: **1901 kg**
- front axle: **677 kg (35.6%)**
- rear axle: **1224 kg (64.4%)**

Factory ballast masses:
- front: **2 x 21 kg = 42 kg**
- rear inner: **2 x 20 kg = 40 kg**
- rear outer: **6 x 24 kg = 144 kg**
- total metal ballast: **226 kg**
- optional water in rear 12.4-28 tyres: up to **2 x 132 kg = 264 kg**

For a 1920 mm wheelbase, the unballasted longitudinal centre of mass implied by the axle loads is approximately:
- **1190 mm behind the front axle**
- **730 mm ahead of the rear axle**

This is a longitudinal target only. A reliable factory value for CoM height has not yet been confirmed.

### Transmission
Mechanical, unsynchronised gearbox: **6 forward + 2 reverse** (3-speed main gearbox x 2-range reduction gearbox).

Factory internal ratios:
- I: **3.096**
- II: **1.597**
- III: **1.000**
- reverse: **3.686**
- low range: **4.050**
- high range: **1.000**
- final drive: **4.444**
- portal/final reduction: **4.812**

Nominal road speeds at 2200 rpm on 12.4-28 tyres are approximately:
- F1: **1.83 km/h**
- F2: **3.54 km/h**
- F3: **5.65 km/h**
- F4: **7.39 km/h**
- F5: **14.32 km/h**
- F6: **22.88 km/h**
- R1: **1.53 km/h**
- R2: **6.21 km/h**

The target maximum road speed for the standard C-330 should therefore be about **23 km/h**, not 27 km/h.

### PTO / hydraulics / hitch
- PTO: **540 rpm**, independent and ground-speed/dependent mode
- rear three-point linkage: **Category II**
- lift capacity at lower-link ends: **700 kg**
- hydraulic pump: **PZ18AT**
- nominal hydraulic flow: **20 l/min**
- nominal pressure: **11 MPa**
- pump maximum pressure: **13.5 MPa**
- maximum external oil draw: **10 l**

### Dimensions / wheels
- length: **~3080 mm**
- wheelbase: **1920 mm** in the normal setting (1870 mm in the alternative high setting cited by factory documentation)
- front tyres: **6.00-16**
- rear tyres: **12.4-28** standard
- front track options: **1350 / 1500 / 1650 mm**
- rear track on 12.4-28: **1250 / 1350 / 1400 / 1500 / 1600 / 1700 / 1750 / 1850 mm**
- minimum turning radius: about **3.30 m**, or about **2.95 m** using the independent inner-wheel brake

### Drawbar / trailer
- maximum drawbar pull on concrete in heavily ballasted test configuration: **16.5 kN**
- rated braked two-axle trailer gross mass: up to **5500 kg**
- vertical load, lower transport hitch: **900 kg**
- vertical load, swinging agricultural drawbar: **400 kg**

## 2. Current mod — preliminary findings

Imported source package: `FS25_UrsusC330_330M_4x2.zip`, original mod version **1.1.2.0**.

### Current mass
`c330m.xml` currently defines base physics components of:
- 800 kg
- 300 kg
- 2 kg
- 2 kg

Total component mass before configuration/object changes: **1104 kg**.

This is far below the factory **1675 kg ready-to-work** target and must be reworked together with centre-of-mass placement, wheel masses and configuration-specific ballast. Do not simply add 571 kg to one component; the target axle split is part of the physics requirement.

### Current engine
Current C-330 definition uses:
- `torqueScale="0.138"`
- normalized torque peak `1.0`
- max rpm `2200`

In FS terms this means a peak around **138 Nm**, roughly **38% above** the real 100 Nm maximum. The curve only falls enough at 2200 rpm to produce approximately the correct rated power. This gives the tractor an unrealistically large torque reserve at lower rpm.

Target concept for later tuning:
- peak physical torque around **100 Nm** at 1600-1800 rpm
- torque around **97 Nm at 2200 rpm** to obtain 22.4 kW
- retain realistic low-rpm falloff and diesel governor behaviour rather than using the current exaggerated hump

### Current gearbox
The active transmission is represented as 3 forward gears with 2 groups and one reverse gear. With current `maxSpeed` values and group ratio it does not reproduce the real C-330 speed ladder.

Real target ladder:
`1.83 / 3.54 / 5.65 / 7.39 / 14.32 / 22.88 km/h`, reverse `1.53 / 6.21 km/h`.

The commented alternative six-gear block in `c330m.xml` is also not historically correct.

### Current speed / store data
The package advertises **27 km/h** globally. This is too high for the standard C-330. C-330 and C-330M should eventually have separate, historically appropriate driveline definitions instead of sharing effectively identical physics.

### Fuel
Fuel capacity in the current XML is already **35 l**, which matches the real C-330.

### Rear axle drive
The active differential drives only the two rear wheels, which is correct for the 4x2 C-330/C-330M concept.

### Wheels
Current wheel physics:
- front radius: **0.40 m**, width **0.190 m**
- rear radius: **0.68 m**, width **0.50 m**

These should later be checked against the actual loaded/dynamic radii of 6.00-16 and 12.4-28 tyres, because tyre radius directly affects the speed calibration.

### Ballast configuration
The model already contains configuration-specific mass changes, but the current values and the base mass do not yet correspond to the factory ballast set of **42 kg front + 40 kg inner rear + 144 kg outer rear**. These should be mapped deliberately rather than preserved by accident.

## 3. Recommended rebuild order

1. Preserve a clean imported-source baseline in Git history.
2. Separate **C-330** and **C-330M** physics where real specifications differ.
3. Rebuild base mass and longitudinal CoM to hit **1675 kg and 635/1040 kg axle loads** in the chosen standard configuration.
4. Rebuild ballast masses and verify axle-load changes after each option.
5. Replace the C-330 engine curve with a 100 Nm / 22.4 kW physically consistent curve.
6. Rebuild the 6F/2R gearbox around the factory speed ladder.
7. Calibrate tyre rolling radius and only then finalise gear speed limits.
8. Verify 35 l fuel, PTO 540, rear linkage behaviour and realistic 700 kg lift target.
9. Test braking, engine braking, steering radius, traction and drawbar behaviour in-game.
10. Only after physics is stable, optimise meshes/textures/scripts and clean log warnings.

## 4. Primary reference

Factory source used as the main technical reference:
- **Ursus C-330 / C-335 Instrukcja Napraw, 1986** (available via Internet Archive).

Secondary sources should be treated only as cross-checks where they conflict with the factory manual.
