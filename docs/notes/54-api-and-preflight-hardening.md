# API and preflight hardening notes

Captured on 2026-10-01 while preparing a fast Creator 5 Pro lid print from
OrcaSlicer-ImageMap. This is a work note for changes that should land in the
Reforge fork after the current print, not a record of a live printer fix.

## Current printer state checked

Moonraker and Klippy recovered to `ready` after a physical printer restart. The
printer was idle/standby before the preflight attempt.

Confirmed values:

- Printer IP: `192.168.0.113`
- Klippy/Moonraker: `ready`
- Print state: `standby`
- Input shaper still saved: `shaper_type_x=mzv`, `shaper_freq_x=61.6`,
  `shaper_type_y=mzv`, `shaper_freq_y=67.8`
- Final local test file:
  `/home/unknown/3dprints/theo_tin_lid_remake_2026-09-30/FIANLTHEOLIDPRINTCODE.gcode`
- At the time of the check, that file was not listed under Moonraker `gcodes`.
  The printer only listed `cadburylidtin.gcode`,
  `theobirthday_reforge_warmtools_120c_220c.gcode`, and
  `unzip/Metadata/plate_1.gcode`.

## Intended manual preflight at capture time

For the lid job, the existing live `START_PRINT` macro was preferred over adding
a new macro or installing the whole fork immediately. Installing the fork or a
new macro requires a Klipper restart, and this printer had just shown
`levelboard` MCU startup fragility.

Full four-tool purge/check command:

```gcode
START_PRINT BED=55 TOOL=1 NOZZLE=220 LAYER=0.2 LEVEL=1 TOOLS=0:220,1:220,2:220,3:220 CLEAN=1 SOAK=0
```

Only the tools used by the lid file:

```gcode
START_PRINT BED=55 TOOL=1 NOZZLE=220 LAYER=0.2 LEVEL=1 TOOLS=1:220,2:220,3:220 CLEAN=1 SOAK=0
```

The live macro flow should be:

1. `_FF_PREFLIGHT`
2. `G28`
3. heat bed during clean
4. `_FF_NOZZLE_CLEAN`
5. `M190`
6. optional `BED_MESH_CALIBRATE`
7. heat and grab the first tool
8. `TOOLCHANGE_SET_PRINT_OFFSET`

## Observed preflight issue

The all-tool `START_PRINT` command was submitted via Moonraker:

```bash
curl -sS --max-time 10 \
  -H 'Content-Type: application/json' \
  -d '{"script":"START_PRINT BED=55 TOOL=1 NOZZLE=220 LAYER=0.2 LEVEL=1 TOOLS=0:220,1:220,2:220,3:220 CLEAN=1 SOAK=0"}' \
  http://192.168.0.113:7125/printer/gcode/script
```

The HTTP request timed out after 10 seconds with no body, but the printer did
accept and execute part of the command.

Observed after polling:

- `toolhead.homed_axes` became `xyz`
- printer remained `ready`
- no heater errors were reported
- bed and all hotend targets were back at `0`
- the toolhead was around `X130 Y130`
- `idle_timeout.state` reported `Printing` briefly despite no virtual SD print
- log contained `samll_safe_z_002 No trigger on probe after full movement`

Conclusion: the preflight reached motion/homing but did not perform the expected
heat/nozzle-clean/purge phase. Before relying on this as a manual preflight,
debug the `START_PRINT`/`_FF_PREFLIGHT` path around the safe-Z/probe checks and
the point where `_FF_NOZZLE_CLEAN` should run.

## API faults observed

Moonraker itself was alive, but the printer showed intermittent API/camera
behavior. Logs suggest load/noise around the web stack rather than slicer
failure.

Observed in `/usr/data/logs/moonraker.log`:

- UI clients reconnecting over websocket after boot.
- frequent file-list scans for `gcodes` and `config`.
- `server.files.metadata` errors for `.3mf` files in `/usr/data/gcodes`.
- `server.files.metascan` errors because `.3mf` project files are not valid
  G-code files.
- repeated `403` reads for symlinked config files such as
  `ff-print-macros.cfg`, blocked by Moonraker reserved-path rules.
- SSL certificate verification errors while fetching Moonraker/Klipper
  announcement/update data from GitHub.
- camera port `8080` could be open while snapshot requests still failed.

Observed in `/usr/data/logs/printer.log`:

- `levelboard` can fail to identify after a restart and require a physical power
  cycle.
- after a good boot, `levelboard` config succeeds and printer reaches ready.

## Fork work plan

Implement these in the Reforge fork one change at a time, with tests or live
proof after each change.

1. Keep `.3mf` project files out of `/usr/data/gcodes`.
   Put only real `.gcode` files under Moonraker `gcodes`. Store `.3mf` projects
   under a separate directory such as `/usr/data/reforge-projects` so Moonraker
   does not try to metadata-scan them as print files.

2. Fix config exposure for Mainsail/Fluidd.
   Moonraker sees symlinked config files but then blocks file reads because the
   resolved paths are reserved. Either expose safe copied config snapshots or
   hide those entries from the UI so it stops generating repeated `403` errors.

3. Disable or repair Moonraker announcement/update checks.
   Either ship the correct CA certificates for outbound HTTPS or disable the
   announcement subscriptions on this appliance build. These errors are noisy
   and not useful during print operation.

4. Add a lightweight health watchdog.
   Poll local endpoints:

   ```text
   http://127.0.0.1:7125/server/info
   http://127.0.0.1:7125/printer/info
   http://127.0.0.1:8080/?action=snapshot
   ```

   If only the camera fails, restart the camera service. If only Moonraker
   fails, restart Moonraker. Do not reboot the whole printer unless Klipper is
   also dead.

5. Reduce camera load.
   Prefer snapshot-oriented timelapse and lower live stream cost. Consider
   reducing mjpg-streamer FPS/resolution or making live camera optional because
   this board is weak and the camera/web stack competes with Moonraker.

6. Update local Orca/ImageMap profiles to avoid stale IPs.
   Existing local profiles still contain `http://192.168.0.112:7125`; the
   printer was on `192.168.0.113`. Long term, use a static DHCP lease or stable
   hostname/VLAN and point slicer profiles at that stable address.

7. Revisit `REFORGE_PREFLIGHT`.
   Resolved in source on 2026-10-04: keep it as a standalone purge/check
   macro only. It must not call `START_PRINT`, home, probe, clear/load bed
   mesh, or queue a second prepare path.

## 2026-10-04 fork resolution

The later bed-scratch/preflight failure showed that two lifecycle paths could
fight each other:

- `[ff_print]` / `FF_BEFORE_PRINT_START` could auto-call `START_PRINT`.
- manual `REFORGE_PREFLIGHT` previously depended on `START_PRINT`-style
  behaviour.
- `START_PRINT` could clear the active mesh and reload stale `MESH_DATA`.

The fork now separates these jobs:

- `REFORGE_PREFLIGHT` is only a standalone purge/check macro. Use it from a
  Fluidd/Mainsail button before a print:

  ```gcode
  REFORGE_PREFLIGHT BED=55 TOOL=0 NOZZLE=220 TOOLS=0:220,1:220,2:220,3:220 PURGE_LENGTH=150 PARK=1
  ```

- `FF_BEFORE_PRINT_START` has `variable_prepare: 0` by default. Profiles or
  the operator must call `START_PRINT` explicitly.
- `START_PRINT` no longer clears the active mesh or blindly loads `MESH_DATA`.
  It loads a mesh only with `LEVEL=1` or explicit `MESH=<profile>`.
- For the flipped bed, call `START_PRINT` with the known safe mesh, for
  example `MESH=flipped_bed_20261004`, or leave that mesh active. Do not let
  old startup code silently restore `MESH_DATA`.

## Immediate print guidance

Do not install the whole fork or restart Klipper immediately before a print.
For the next print, use the proven live macro path only after verifying:

- `printer/info` is `ready`
- `print_stats.state` is `standby`
- bed is clear
- expected G-code is uploaded and listed under Moonraker `gcodes`
- preflight either completes visibly or logs a clean `_FF_NOZZLE_CLEAN` sequence

If `START_PRINT` does only homing again and skips purge, stop and debug before
starting the print.
