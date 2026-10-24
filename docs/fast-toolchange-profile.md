# Sensor-checked faster toolchange profile

The faster profile is active on the owner's printer and was intentionally left
active after the owner approved its behaviour. It has not been rolled back.
The bounded restart fix remains installed separately.

## Saved profile

`pkgs/klipper-config/payload/config/examples/ff-toolchange-fast.cfg` ships with
the config package but is NOT automatically included on other machines.
After machine-specific review it can be included after the base config and
before SAVE_CONFIG using:

```ini
[include /usr/data/anvil/config/examples/ff-toolchange-fast.cfg]
```

The owner's live printer uses equivalent explicit overrides in printer.cfg;
that user-owned file survives installer updates. Do not enable the example
and contradictory direct overrides together. Historical module/config defaults
remain available for machines that have not been tested.

| Setting | Requested value |
| --- | --- |
| Clear travel | 600 mm/s |
| Swap acceleration | 30000 mm/s2 |
| Final dock/pickup contact | 90 mm/s |
| First 20 mm pickup pullback | 160 mm/s |
| Verified departure / release retreat | 600 mm/s |
| Saved XY return | unchanged, 150 mm/s |
| Minimum cruise ratio | unchanged, 0.5 |

These are commanded limits, not measured segment speeds. The profile keeps
existing paths, dock coordinates, motor macros, sensor polling, deadlines,
retry limits and calibration frames. It does not import OpenCreator's full
motion sequence or change colour recipes.

`grab_pullback_feed` is now independently configurable in mm/min and defaults
to historical F4800 (80 mm/s). The example selects F9600 (160 mm/s).
Reloading a changed Python module requires a Klipper SERVICE restart, not
only a G-code RESTART, which can retain the previous imported module.

## What was observed

25 actual cold swaps completed in the sequence T0->T1->T2->T3->T0, repeated,
ending at T1: seven 0->1, six each 1->2, 2->3 and 3->0. Each submission had
a precheck and two successful postchecks. No heat or extrusion was commanded.
The owner observed the behaviour and requested the faster settings remain active.

Complete HTTP Tn+M400 request time including XY return: mean 5.594 s,
median 5.552 s, range 5.312-5.975 s. The earlier original-profile T0->T1
request took 6.811 s. This single-baseline comparison is indicative, not a
controlled multi-run speed benchmark or a comparison to a 3-second mechanical
swap claim with different timing boundaries.

Final raw sensors agreed: extruder_pos1/3/4 PRESSED, pos2 RELEASED;
extruder_grab2 PRESSED and other grab inputs RELEASED. All four filament
switches detected filament; only the mounted T1 hard-runout switch was enabled.

## Sensor-first guards retained

- Reject absent/invalid dock geometry and unhomed/ambiguous tool state.
- Confirm the target is docked before pickup approach; confirm engagement before locking.
- Confirm dock-empty plus grab-active before fast pickup departure and again after departure.
- Confirm the old tool is seated before unlock; retreat only after successful release, then verify dock-full and grab-inactive.
- Keep existing internal retries; the external test harness never resubmitted failed or uncertain commands.

Existing sensors do not measure mechanical latch strength, belt position,
backing/colour correctness or substep loss. `toolhead.stalls` is not a
comprehensive skipped-step measurement. No claim of zero impact or positional
repeatability beyond observed sensor checks is made.

## Remaining validation

Only four of twelve directed tool pairs were exercised. Hot tools, thermal
expansion, print-time clearance, temperature waits, purge, unattended endurance,
measured dock repeatability and all-pair testing remain unverified. This is not
approval to apply aggressive motion to an untested machine or to skip physical
interlocks. No print or SurfaceMix product geometry was approved by this test.
