# Purge-tower transition stringing

Date: 2026-10-18

## Observation

Photos from the ImageMap calibration print show loose strands near the purge
or prime strip. The calibration squares themselves do not show the same
strands.

The earlier Theo print shows the same type of thin lines crossing empty travel
space between separated model regions, as well as strands around its purge
strip. This is corroborating evidence, not proof of the exact motion that
created each line. The source archive is:

`Desktop/Documents/3dprints/theo_child_character/diagnostics/2026-10-16-printing-problems/Printing problems.zip`

## Diagnosis

The G-code's first `CP TOOLCHANGE WIPE` line contains both the purge-tower
start coordinates and positive E. That is correct only if `T<n>` has already
returned to those coordinates. Our ImageMap Creator 5 profile has an empty
`change_filament_gcode`, while the firmware shipped with `restore_axis` unset,
so the toolchange ended at the dock and the first purge move could extrude
while travelling back to the tower.

This matches the loose strands seen in both calibration and Theo photos. The
camera angle alone was not sufficient; the slicer output and firmware contract
identify the mismatch.

## Fix

`[ff_toolchange]` now ships:

```ini
restore_axis: xy
restore_feed: 9000
```

The toolchanger restores the saved purge-tower XY after a successful grab,
through the newly applied tool frame. Z is not restored. The first positive E
move therefore starts at the tower rather than during dock departure.

## Validation

Re-slice a small monitored multi-tool job and inspect one transition. The
first `CP TOOLCHANGE WIPE` extrusion should begin at the purge-tower start
coordinate, with the toolhead already there. Stop the print if a strand still
appears; that would indicate nozzle ooze or a separate slicer travel issue.
