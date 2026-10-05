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

This is not upstream Reforge. It is our fork, for our machine. It exists
because the Reforge/Klipper4FlashForge developers did the hard base-port work:
FlashForge update packaging, Klipper/Moonraker/Mainsail/HelixScreen integration,
toolchanger support, installer safety, and the Creator 5 documentation base.
Thank you to the Reforge developers and the Creator 5 modding community.

```text
[ operator ] ToniMcQueen
[ machine  ] FlashForge Creator 5 Pro
[ branch   ] creator5pro-local-fullcolour-tuning
[ goal     ] reliable CMYW / ImageMap / toolchange workflow
[ rule     ] physical printer evidence beats screenshots
```

## What This Fork Adds

- Local Creator 5 Pro macros for print lifecycle, preflight, purge, resume, and cancel behavior.
- A standalone `REFORGE_PREFLIGHT` macro for purge/check workflows without silently starting a print.
- Safer `START_PRINT` mesh handling: it does not blindly clear/load meshes unless requested.
- Full-colour purge/preflight profile work for debugging CMYW tool reliability.
- Toolchange hardening around dock, grab, release, load, purge, and runout sensor windows.
- Runout and motion/clog sensor policy so sensors are disarmed only during risky tool handling paths.
- Snapshot timelapse plumbing for per-print photo evidence and later AI review.
- Timelapse package patching so raw frames can be zipped and cleaned instead of rendering costly video.
- Dual-camera support kept in the fork instead of dropping the second feed.
- Moonraker/camera/API hardening notes and config work for weaker printer-board resources.
- Chamber heater, chamber fan, aux cooling, and outside-air intake policy for PLA versus ABS/ASA/nylon.
- Fan-control planning for the Creator 5 Pro airflow problem where chamber heat and aux cooling fight each other.
- Dropbear/SSH installer handling so SSH access survives cleanly instead of losing host keys or breaking login paths.
- Boot-screen branding support for `ToniMcQueen's Forge`.
- Orca/ImageMap printer, process, and CMYW filament profiles.
- G-code arc fitting test plan for future slicer work.
- Static tests for the behavior we care about keeping fixed.
- Optional Tailscale userspace-networking package for remote access without
  requiring `/dev/net/tun`; disabled until the owner explicitly logs in.

## Changed Areas

```text
[ macros       ] START_PRINT, CANCEL_PRINT, RESUME, REFORGE_PREFLIGHT
[ toolchange   ] dock/release/grab paths, fast departure, parked tool state
[ sensors      ] filament switch + motion/clog sensor arming policy
[ timelapse    ] snapshot trigger, frame archive cleanup, no printer-side video render
[ cameras      ] preserve two camera feeds in the fork
[ airflow      ] chamber heater, recirculation, aux fan, outside-air cooling policy
[ ssh/dropbear ] installer-side SSH persistence and safer update handling
[ tailscale    ] optional userspace-networking client, no baked auth keys
[ boot         ] ToniMcQueen's Forge boot-screen branding
[ slicer       ] local Orca/ImageMap profiles, CMYW filament profiles, snapshot profiles
[ qa           ] static tests for lifecycle, timelapse, toolchange, webcam/fan, arcs, installer
```

This is a practical fork, not a clean-room rewrite. The point is to capture
the things we changed while tuning a real Creator 5 Pro, then make those
changes reproducible instead of leaving them as one-off live-printer edits.

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
| `docs/tailscale-remote-access.md` | Optional Tailscale/Headscale remote-access setup |
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

Special thanks to the Reforge developers for making the Creator 5/Creator 5 Pro
Klipper firmware path possible in the first place. This fork would not exist
without their installer, packaging, recovery, Klipper, Moonraker, Mainsail,
HelixScreen, toolchanger, and documentation work.

Thanks also to Klipper, Moonraker, Mainsail, HelixScreen, OpenCreator, and the
Creator 5 modding community for the ecosystem this local workshop branch builds
on. ToniMcQueen-forge is our experimental local branch and not an upstream
support channel.
