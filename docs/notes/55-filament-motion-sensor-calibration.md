# Creator 5 Pro Filament Motion Sensor Calibration

## Current finding

During ImageMap calibration printing on 2026-10-03, the printer repeatedly paused with `T0 clog` even though T0 physically purged filament.

The important distinction is:

- `filament_switch_sensor fd_ex*` checks whether filament is present.
- `filament_motion_sensor fm_ex*` tries to detect whether filament is moving while extrusion is commanded.

Live testing after reboot showed:

- T0 purged 150 mm successfully.
- T0 then purged another 150 mm with `fm_ex0` enabled.
- T0 switch sensor stayed true, but `fm_ex0` ended false.
- T1 purged 150 mm and looked healthy during that test.
- T2 purged 150 mm and looked healthy during that test.
- T3 purged 150 mm, switch sensor stayed true, but `fm_ex3` ended false.

That evidence does not support a real nozzle clog. It points to firmware/config behaviour around filament motion sensors.

## Live sensor config observed

All four motion sensors were configured similarly:

```ini
[filament_motion_sensor fm_ex0]
detection_length: 50
event_delay: 3.0
pause_on_runout: False
runout_gcode:
  _FF_RUNOUT TOOL=0 KIND=motion

[filament_motion_sensor fm_ex1]
detection_length: 50
event_delay: 3.0
pause_on_runout: False
runout_gcode:
  _FF_RUNOUT TOOL=1 KIND=motion

[filament_motion_sensor fm_ex2]
detection_length: 50
event_delay: 3.0
pause_on_runout: False
runout_gcode:
  _FF_RUNOUT TOOL=2 KIND=motion

[filament_motion_sensor fm_ex3]
detection_length: 50
event_delay: 3.0
pause_on_runout: False
runout_gcode:
  _FF_RUNOUT TOOL=3 KIND=motion
```

`pause_on_runout` is false, so Klipper itself is not directly pausing. Reforge pauses through `_FF_RUNOUT`, controlled by `_FF_RUNOUT_CFG`:

```text
switch_pause=1
clog_pause=1
```

## Diagnostic tool

Local diagnostic script:

```text
/home/unknown/Desktop/Documents/3dprints/reforge_sensor_tools/reforge_filament_motion_sensor_calibrate.py
```

The tool:

- Refuses to run during an active print.
- Enables the requested switch and motion sensors.
- Runs controlled `LOAD_FILAMENT TOOL=n TEMP=... LENGTH=... RETRACT=0`.
- Logs `toolhead.position[3]`, switch state, motion state, `filament_position`, and `runout_position`.
- Writes timestamped JSONL samples and a Markdown summary.

The useful output is whether `E` moved by the requested amount while `fm_exN.filament_detected` still ended false.

## Fork changes implemented

Implemented in this fork after the 2026-10-03 diagnostic:

- `ff_toolchange.py` arms only the hard switch sensor on tool grab/restart.
- `FF_RUNOUT_ARM` accepts `SWITCH=` and `MOTION=` and reports both states.
- `FF_RUNOUT_DISARM MOTION_ONLY=1` disables only soft motion/clog sensors.
- `ff-filament.cfg` disarms motion sensors before load/unload/purge/preflight extrusion and re-arms only the switch afterward.
- `START_PRINT` arms the selected tool's motion sensor only after preflight, final tool selection, heat, and print Z offset.
- Full-colour/WarmTools Orca/ImageMap profiles disable motion during toolchange heat/grab, then call `REFORGE_ARM_MOTION_SENSOR TOOL=[next_extruder]`.
- `_FF_RUNOUT` keeps hard switch runout as an immediate pause, but treats motion/clog as soft suspicion first and pauses only after `motion_pause_after` repeated events.
- `REFORGE_FILAMENT_SENSOR_TEST` exists as a printer-side manual lifecycle test.

The current default confirmation policy is:

```text
switch_pause=1
clog_pause=1
motion_pause_after=2
```

That means first motion fault is a warning, second confirmed motion fault pauses. Set `clog_pause=0` to make motion faults report-only while still keeping switch runout active.

## Design requirements

### 1. Add a real Reforge calibration macro

The fork now has a macro equivalent to:

```gcode
REFORGE_FILAMENT_SENSOR_TEST TOOL=0 LENGTH=150 TEMP=220
```

It should continue to:

- Refuse during an active print unless explicitly allowed.
- Enable only the selected tool's switch and motion sensors.
- Move to purge position.
- Heat selected tool.
- Extrude fixed lengths in chunks, for example 25 mm x 6.
- Report before/after `filament_detected`, `filament_position`, and `runout_position`.
- Never leave a tool at 250 C after the test.

### 2. Stop treating motion-sensor faults as immediate print-killers

Keep switch runout protection enabled but make motion/clog pause softer:

- Switch runout: pause immediately.
- Motion/clog runout: warn first, optionally retry/purge, then pause only after repeated failure.

This is especially important for ImageMap/top-surface calibration because slow dense textured moves can trip strict motion checks.

### 3. Do not arm motion sensors during toolchange/load/purge windows

Motion sensors should be ignored during:

- `LOAD_FILAMENT`
- `UNLOAD_FILAMENT`
- preflight purge
- nozzle wipe/prime
- toolchange recovery moves
- resume heat restoration

The sensor is re-armed only after the tool is selected, hot, primed, and the profile has reached the print path.

### 4. Reset stale runout state when arming

Before enabling `fm_exN`, reset or re-baseline its runout state so stale `runout_position` from a previous macro cannot immediately trigger `_FF_RUNOUT`.

Current behaviour suggests stale or badly-timed `runout_position` can survive across purge/resume paths.

### 5. Make detection length configurable by print mode

Current live value is `detection_length: 50`.

Recommended fork tunables:

- Normal print default: keep conservative after testing.
- Full-colour/ImageMap profile: larger detection length or warning-only motion faults.
- Preflight: motion sensors disabled or ignored.

Do not hardcode one value until the diagnostic tool has been run across all tools with the real filament path and typical print speeds.

## Operational policy

For calibration prints:

- Trust physical purge proof over one motion-sensor false state.
- Keep switch sensors active.
- Use the ImageMap full-colour profile that calls `REFORGE_ARM_MOTION_SENSOR` after start and toolchange.

For production prints:

- Re-enable motion detection only after it has passed the controlled diagnostic on all participating tools.
