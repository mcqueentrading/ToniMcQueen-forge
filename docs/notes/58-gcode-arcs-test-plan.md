# G2/G3 arc fitting test plan

Date: 2026-10-04

## Current fork state

Reforge/Klipper has arc support declared in:

- `pkgs/klipper-config/payload/config/printer.base.cfg`

The active config is:

```ini
[gcode_arcs]
resolution: 1.0
```

That means the printer can accept slicer-emitted `G2` and `G3` commands, but
Klipper still converts them into linear segments internally. The expected win
is smaller G-code and lower parser load, not magic smoother motor motion.

## Profile policy

Safe Reforge profiles keep arc fitting off.

An explicit experimental profile exists for comparison:

- `0.20mm Reforge Quality Snapshot ARC TEST @C5P`

Only use that profile for controlled tests. Do not use it for first attempts at
ImageMap, SML, full-colour, or long prints.

## Test object

Use a small object with both curves and straight edges:

- one 30-50 mm cylinder or ring
- one square/rectangular block
- one simple text or logo feature if needed

Slice the same model twice:

- safe profile: `0.20mm Reforge Quality Snapshot @C5P`
- arc profile: `0.20mm Reforge Quality Snapshot ARC TEST @C5P`

## Static checks before printing

Compare the exported G-code:

```sh
grep -nE '^[[:space:]]*G[23][[:space:]]' safe.gcode | head
grep -nE '^[[:space:]]*G[23][[:space:]]' arc-test.gcode | head
wc -c safe.gcode arc-test.gcode
```

Expected result:

- safe file: no or almost no `G2`/`G3`
- arc-test file: visible `G2`/`G3`
- arc-test file: usually smaller

## Live checks

Print only after the static check proves the file is actually different.

Watch for:

- Klipper rejecting `G2` or `G3`
- pauses or planner stalls on curved walls
- missing extrusion around arcs
- worse seam quality
- no measurable file-size or parsing benefit

If any of those appear, keep arc fitting off. If the arc file prints the same
or better and reduces file size materially, then we can consider enabling it in
future ImageMap/SML slicer-fork profiles.
