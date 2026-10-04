# ToniMcQueen-forge

```text
01010100 01101111 01101110 01101001 01001101 01100011 01010001 01110101 01100101 01100101 01101110

> wake up, Creator 5 Pro
> the stock firmware has you
> follow the white filament
```

**ToniMcQueen-forge** is our local FlashForge Creator 5 Pro firmware fork.
It is built for our workshop workflow: full-colour ImageMap printing, safer
toolchange behavior, snapshot timelapse evidence, Orca profile control, and
repeatable calibration.

This is not upstream Reforge. It is our fork, for our machine, with Reforge
credited as the base firmware project.

```text
[ operator ] ToniMcQueen
[ machine  ] FlashForge Creator 5 Pro
[ branch   ] creator5pro-local-fullcolour-tuning
[ goal     ] reliable CMYW / ImageMap / toolchange workflow
[ rule     ] physical printer evidence beats screenshots
```

## What This Fork Adds

- Local Creator 5 Pro macros for print lifecycle, preflight, purge, resume, and cancel behavior.
- Toolchange hardening around dock/grab/runout sensor windows.
- Snapshot timelapse plumbing for per-print photo evidence and later AI review.
- Dual-camera support kept in the fork.
- Chamber and aux-fan policy notes for PLA versus ABS/ASA/nylon behavior.
- Boot-screen branding support for the modded firmware.
- Orca/ImageMap printer, process, and CMYW filament profiles.
- Static tests for the behavior we care about keeping fixed.

## Matrix Map

```text
printer evidence pipeline
  print-id -> snapshot frames -> zip archive -> catalog metadata -> review

full-colour pipeline
  ImageMap calibration -> CMYW profile -> purge tuning -> texture print -> compare photos

firmware pipeline
  macro change -> package build -> static QA -> USB install -> hardware validation
```

Useful paths:

| Path | Purpose |
|---|---|
| `docs/local-fullcolour-fork-change-inventory.md` | Inventory of local fork changes |
| `docs/creator5pro-local-fullcolour-roadmap.md` | Roadmap for full-colour, evidence, and slicer work |
| `docs/notes/54-api-and-preflight-hardening.md` | API, preflight, Moonraker, and resource notes |
| `docs/notes/55-filament-motion-sensor-calibration.md` | Runout and motion sensor diagnostic plan |
| `docs/notes/56-upstream-and-c5-modding-review.md` | Upstream and Creator 5 modding review |
| `docs/notes/57-chamber-airflow-policy.md` | Chamber heat versus aux fan policy |
| `docs/notes/58-gcode-arcs-test-plan.md` | G2/G3 arc fitting plan |
| `local/creator5pro-orca-imagemap-profiles/` | Local Orca/ImageMap profiles |

## Build

Fetch pinned source assets:

```bash
./bin/fetch-assets.sh --all
```

Build packages:

```bash
make packages
```

Run static QA:

```bash
make qa-static
```

Known-good local result:

```text
367 passed, 1 skipped
```

Useful host checks before committing:

```bash
python3 -m pyflakes qa/static
git diff --check
```

## Flashing Rules

```text
there is no spoon
there is a heater
there is a bed that can be scratched
there is no substitute for watching first layer
```

- Build for `Creator5Pro`, not plain `Creator5`.
- Keep stock FlashForge recovery firmware available.
- Do not trust old Z offset after firmware or macro changes.
- Rehome, relevel, check Z offset, purge all needed tools, and inspect first layer.
- Do not install live-printer experiments unless the same behavior exists in the fork installer.
- Do not leave the printer unattended during new macro/toolchange testing.

## Remote

```text
https://github.com/mcqueentrading/ToniMcQueen-forge
```

Current working branch:

```text
creator5pro-local-fullcolour-tuning
```

## Credits

This fork is based on the Reforge/Klipper4FlashForge Creator 5 firmware work:

```text
https://github.com/Klipper4FlashForge/firmware
```

Reforge, Klipper, Moonraker, Mainsail, HelixScreen, and the Creator 5 modding
community provide the base this local fork builds on. ToniMcQueen-forge is our
workshop branch and not an upstream support channel.
