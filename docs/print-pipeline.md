# The print pipeline

What drives a print on stock firmware, what breaks when the application is not
there to drive it, and what this mod sends in its place. The owner-facing
version of this — why a stock-sliced file still prints, and the two knobs for
changing that — is [How a print runs](how-a-print-runs.md).

Addresses and the recovery work behind the stock side are in
[Print lifecycle](notes/50-print-lifecycle.md) and
[firmwareExe vs Klipper](notes/25-app-vs-klipper-ownership.md); this page is
the comparison rather than the source.

---

## Stock, step by step

The chain is `BuildPage::doPreparetion` → `prepareForEddy` →
`BuildPage::startPrint` → `CommMgr::serialPrint`, the last being a 37 KB
engine thread inside the application. Preparation, in order:

1. `G90`, `M82`, `M400`
2. `G28`, aborting on failure
3. `SET_GCODE_OFFSET X=0 Y=0 MOVE=1 MOVE_SPEED=600`
4. two probe touch checks, internal to the app
5. heat bed and chamber; dock whatever tool is held; presence-check the file's
   **first** tool — the app's E0165
6. `SET_IDLE_TIMEOUT TIMEOUT=1800000`; eddy probe at (265, 4.8); nozzle clean
   of every tool the file uses — purge at the chute, wipe at (266.5, 13.8),
   cool by 100 °C, release
7. bed and chamber soak, 5 minutes from the bed reaching target, then a
   `G28 Z` re-home
8. leveling toggle: on → `BED_MESH_CALIBRATE` at `ACCEL=2000` then
   `BED_MESH_PROFILE LOAD=default`; explicit `MESH=<profile>` loads that
   profile; otherwise the fork leaves the currently active mesh alone instead
   of blindly restoring `MESH_DATA`
9. heat and grab the first tool, `G1 Z10 F1200` for clearance

Then the absolute print Z offset — the ~3.2 mm eddy-to-nozzle gap, computed
once — and the preamble: `G1 X250 F2400` to clear the docks,
`SDCARD_SET_CHANNEL CHANNEL=<tool>`, `M21` → `M23 /<name>` → `M26 S0` →
`M24`, `SET_IDLE_TIMEOUT TIMEOUT=864000`. No heating is sent for a fresh
print: the temperatures came from preparation and from the file.

Pause is inline in that thread — the UI buttons send no G-code of their own.
It sends `M400` and `M25`, waits for the SD state to read paused, saves every
tool's target, `SAVE_GCODE_STATE NAME=PAUSE_state`, turns **all hotends off**
(bed and chamber stay), parks upward, and writes a power-loss record. Resume
reheats in two stages, e1+e2 then e3+e4, re-grabs the head if needed, and
restores. Cancel and normal completion share one exit block.

## Where a Mainsail print breaks on stock

This is the specific thing that makes the mod necessary rather than merely
nicer. FlashForge's Klipper fork intercepts toolchange lines in
`virtual_sdcard.py` before they reach the G-code engine:

```python
if line.startswith("T") and line in VALID_GCODE_T:
    self.print_channel = int(line[1:])
    if self.print_channel != self.load_channel:
        self.gcode.run_script("M400")
        self.change_filament = True        # exposed as 'refuelling'
        self.doingChangeEx = True
        while self.change_filament:        # busy-waits for the UI app
            self.reactor.pause(...)
```

The fork performs **no motion at all**. It raises a flag and waits for
firmwareExe to do the physical change and send `SDCARD_CLEAR_REFUELLING`. For
a print nobody is servicing, that loop never ends.

(`line` comes from `data.split('\n')` and is never stripped, so `T2 ; anything`
did not match and fell through to the G-code engine. Earlier releases of this
mod exploited exactly that with a `; ff-toolchange` marker in the slicer's
change-filament field. We ship upstream `virtual_sdcard` now, so bare `Tn`
reaches `ff_toolchange` directly and the marker is gone — but files still
carrying it print correctly, because the parser discards the comment.)

## Here, step by step

`[ff_print]` hooks `SDCARD_PRINT_FILE` and `M23`, and can call two macros
around the job: `FF_BEFORE_PRINT_START` before the file's first line and
`FF_AFTER_PRINT_END` once it leaves the printing state. `CANCEL_PRINT` is
overridden as well.

On this local full-colour branch, `FF_BEFORE_PRINT_START` still runs
`_FF_PREFLIGHT` as a zero-motion calibration/tool-presence gate, but its
`prepare` variable is `0`. That means it does not automatically run
`START_PRINT`. The slicer profile or operator owns explicit startup. This avoids
a manual preflight, a profile start block, and the wrapper all queuing
different prepare paths.

`START_PRINT` follows the app's order, with the app's own addresses noted in
the config beside each step: `_FF_PREFLIGHT` for every tool in `TOOLS=`, then
`G90`, `M82`, `G28`, `SET_GCODE_OFFSET X=0 Y=0 MOVE=1`,
`SET_IDLE_TIMEOUT TIMEOUT=864000`, `M140` so the bed heats **during** the
clean, `_FF_NOZZLE_CLEAN` for the used tools, `M190` and the optional soak,
`G28 Z`, the mesh (calibrate or load), `M104` and `T<n>` to grab the first
tool, and `TOOLCHANGE_SET_PRINT_OFFSET` for the thermal, bed and thin-layer
terms.

Mesh handling is deliberately stricter than the stock app path. `START_PRINT`
loads a mesh only when `LEVEL=1` or `MESH=<profile>` is explicit. If neither is
given, it leaves the currently active mesh alone. This prevents an old
`MESH_DATA` profile from replacing a freshly probed flipped-bed mesh behind the
operator's back.

`REFORGE_PREFLIGHT` is separate from `START_PRINT`. It is a standalone purge
and tool check for Fluidd/Mainsail buttons or manual operator use:

```gcode
REFORGE_PREFLIGHT BED=55 TOOL=0 NOZZLE=220 TOOLS=0:220,1:220,2:220,3:220 PURGE_LENGTH=150 PARK=1
```

It does not home, probe, clear/load mesh, or start the print.

The Z frame differs from the app's by design. The app applied one absolute
offset per print; here every `T<n>` grab applies that tool's own
`nozzle_z − station_z + z_adjust`, so Z=0 is the bed whenever a tool is
mounted, and `TOOLCHANGE_SET_PRINT_OFFSET` adds only the print-time terms.
