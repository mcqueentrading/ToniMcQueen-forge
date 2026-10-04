# Reforge Orca/ImageMap Profile Draft - 2026-09-26

Created from the exported FlashForge Creator 5 Pro profile, but with Reforge/Anvil-safe start/end G-code.

Installed into:

- `/home/unknown/.local/share/orcaslicer-imagemap-data/user/default/machine/Reforge Creator 5 Pro 0.4 nozzle.json`
- `/home/unknown/.local/share/orcaslicer-imagemap-data/user/default/machine/base/Reforge Creator 5 Pro 0.4 nozzle.json`
- `/home/unknown/.local/share/orcaslicer-imagemap-data/user/default/process/0.20mm Reforge First Test @C5P.json`
- `/home/unknown/.local/share/orcaslicer-imagemap-data/user/default/filament/Elegoo PLA @Reforge C5P.json`

Backup of prior user profile directory:

- `/home/unknown/Desktop/Documents/3dprints/reforge_orca_imagemap_profile_2026-09-26/backup_user_default_before_reforge_profile`

## Important

Use `Reforge Creator 5 Pro 0.4 nozzle.json` for conservative single-tool or low-risk tests instead of the stock `Flashforge Creator 5 Pro 0.4 nozzle` profile.

Use `Reforge Creator 5 Pro 0.4 nozzle ImageMap FullColour Safe.json` for ImageMap CMYK/CMYW jobs where all four tools should be purged before model moves.

Use `Reforge Creator 5 Pro 0.4 nozzle WarmTools 120C.json` as the preserved
profile variant for experiments that keep participating docked tools warm
instead of allowing them to drop cold.

Conservative start G-code uses:

```gcode
START_PRINT BED=[bed_temperature_initial_layer_single] TOOL=[initial_extruder] NOZZLE=[nozzle_temperature_initial_layer] LAYER=[layer_height] LEVEL=0 TOOLS=[initial_extruder]:[nozzle_temperature_initial_layer] CLEAN=1 SOAK=0
M104 S[nozzle_temperature_initial_layer] T[initial_extruder]
M109 S[nozzle_temperature_initial_layer] T[initial_extruder]
G90
M83
```

End G-code uses:

```gcode
END_PRINT
```

This is deliberately conservative and intended for a single-tool low-risk test first.

## Full-Colour ImageMap Profile

The full-colour-safe profile uses this start pattern:

```gcode
SET_GCODE_VARIABLE MACRO=FF_BEFORE_PRINT_START VARIABLE=prepare VALUE=0
REFORGE_PREFLIGHT BED=[bed_temperature_initial_layer_single] TOOL=[initial_extruder] NOZZLE=[nozzle_temperature_initial_layer] TOOLS=0:[nozzle_temperature_initial_layer],1:[nozzle_temperature_initial_layer],2:[nozzle_temperature_initial_layer],3:[nozzle_temperature_initial_layer] PURGE_LENGTH=150 PARK=1
START_PRINT BED=[bed_temperature_initial_layer_single] TOOL=[initial_extruder] NOZZLE=[nozzle_temperature_initial_layer] LAYER=[layer_height] LEVEL=0 TOOLS=0:[nozzle_temperature_initial_layer],1:[nozzle_temperature_initial_layer],2:[nozzle_temperature_initial_layer],3:[nozzle_temperature_initial_layer] CLEAN=0 SOAK=0
```

`REFORGE_PREFLIGHT` is now only a standalone purge/check. It does not call
`START_PRINT`, home, probe, or load a mesh. The following `START_PRINT` owns
the actual print setup. Keep `CLEAN=0` there if the standalone preflight already
purged all participating tools.

Change `LEVEL=0` to `LEVEL=1` only when intentionally probing a fresh mesh. For
a known bed-side mesh, use `MESH=<profile>` in `START_PRINT`, for example
`MESH=flipped_bed_20261004`. If neither `LEVEL` nor `MESH` is given, the macro
leaves the active mesh alone.

The full-colour and WarmTools profile variants also own the soft clog sensor
policy. They call `REFORGE_DISARM_MOTION_SENSORS` during toolchange
dock/grab/heat, then `REFORGE_ARM_MOTION_SENSOR TOOL=[next_extruder]` after the
new tool is hot and selected. Do not remove those lines unless motion/clog
detection is intentionally disabled at the printer.

Manual Fluidd/Mainsail preflight button command:

```gcode
REFORGE_PREFLIGHT BED=55 TOOL=0 NOZZLE=220 TOOLS=0:220,1:220,2:220,3:220 PURGE_LENGTH=150 PARK=1
```

`PARK=1` makes standalone preflight safe: it docks the tool and turns heaters
off after preparation.

The fork currently sets `variable_purge_length: 150.0` in `ff-filament.cfg` for
heavy debugging purge. Reduce it after the full-colour path is reliable.

## OpenCreator Slicer Notes

The stored Reforge process profiles keep Orca arc fitting disabled. The
OpenCreator slicer notes recommend `Arc fitting = off` because the target path
is Klipper/Moonraker, not a firmware that consumes arc moves directly.

The local profile package already points at the current printer address:

```text
http://192.168.0.113:7125
http://192.168.0.113:81/
```

If Orca/ImageMap shows the old `192.168.0.112` Device page after importing a
profile, change it in the slicer UI under printer connection settings and save
the profile copy. The JSON field may still be named `host_type: octoprint` in
Orca-derived profile files even when the UI labels the connection as Moonraker,
so do not bulk-rewrite that field without validating the UI behaviour.

OpenCreator also suggests these as optional test candidates, not hard defaults:

- retraction speed: 75 mm/s on all extruders
- deretraction speed: 75 mm/s on all extruders
- Z-hop: 0.24 mm

Keep those as tuning experiments until a sliced preview and a physical print
prove they do not worsen toolchange, stringing, or Z stress on this machine.

## Arc Fitting Experiment

The default Reforge process profiles keep arc fitting off. Klipper arc support
is declared in the firmware config, but Klipper converts `G2`/`G3` arcs into
linear segments internally, so the expected benefit is smaller G-code and less
parser load rather than inherently better curved motion.

Use this profile only for controlled comparison prints:

- `0.20mm Reforge Quality Snapshot ARC TEST @C5P`

Before printing, export both safe and arc-test G-code and confirm the arc-test
file actually contains `G2`/`G3`:

```sh
grep -nE '^[[:space:]]*G[23][[:space:]]' arc-test.gcode | head
wc -c safe.gcode arc-test.gcode
```

Keep ImageMap/SML/full-colour profiles on the safe no-arc path until a small
test print proves the arc path behaves correctly on the live printer.

## Snapshot-Only Timelapse

The machine profiles call:

```gcode
REFORGE_SNAPSHOT_START
```

at print start, then:

```gcode
REFORGE_SNAPSHOT_EVERY_MINUTE INTERVAL=60
```

on layer changes. This uses Moonraker timelapse still-frame capture only. It
does not call `TIMELAPSE_RENDER`, because video rendering on the printer costs
too much CPU and storage during the full-colour workflow.

At one frame per minute, a 10 hour print creates about 600 JPEGs. At roughly
112 KB each that is about 67 MB; at 250 KB each it is about 150 MB. The actual
size depends on mjpg-streamer resolution, lighting, and scene complexity.
