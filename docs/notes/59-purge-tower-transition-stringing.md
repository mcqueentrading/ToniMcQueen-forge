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

## Hypothesis

After a tool change, the next extrusion may begin before the toolhead reaches
the purge tower. If the travel from the swap location to the tower happens
with extrusion enabled, the filament can be laid across the bed or left as a
string on the way to the tower.

This is a working hypothesis, not yet a confirmed cause. The camera angle and
the purge strip also make the exact start point difficult to identify.

## Controlled test

For the next monitored multi-tool print:

1. Check the G-code around one tool change and the following purge-tower move.
2. Confirm the travel move has no positive E amount before the tower entry.
3. Confirm the first positive E move occurs inside the tower path.
4. If a strand still appears, capture the toolhead during the transition and
   compare it with the G-code sequence.

Do not patch the live macro based on the photos alone. The safe fix, if
confirmed, is to keep extrusion at zero during the travel and perform the
initial purge/reprime only after the toolhead reaches the tower.
