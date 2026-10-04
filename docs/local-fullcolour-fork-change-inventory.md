# Local full-colour fork change inventory

Date: 2026-10-04

Scope: source tree for the Creator 5 Pro local full-colour/ImageMap fork. This
is a source inventory, not proof that the current live printer has every change
installed.

## Current source behaviour

### Boot branding

- Boot splash text is fork-branded as `ToniMcQueen's Forge`.
- Relevant files:
  - `pkgs/anvil-core/payload/config/boot-screen.conf`
  - `pkgs/anvil-core/payload/prog/firmwareExe`
  - `bin/preview-boot-screen.py`
  - `docs/boot-screen-branding.md`

### Print startup and preflight

- `FF_BEFORE_PRINT_START` now defaults `variable_prepare: 0`.
- Slicer profiles or the operator must call `START_PRINT` explicitly.
- `REFORGE_PREFLIGHT` is now a standalone purge/check macro only.
- `REFORGE_PREFLIGHT` does not call `START_PRINT`, home, probe, clear/load bed
  mesh, or start a print.
- Full-colour preflight purge uses `PURGE_LENGTH=150` while debugging.
- `START_PRINT` no longer blindly clears the active mesh or loads `MESH_DATA`.
  It loads a mesh only when `LEVEL=1` or `MESH=<profile>` is explicit;
  otherwise it leaves the active mesh alone.
- Relevant files:
  - `pkgs/klipper-config/payload/config/ff-print-macros.cfg`
  - `docs/print-pipeline.md`
  - `docs/how-a-print-runs.md`
  - `docs/how-calibration-works.md`
  - `docs/notes/54-api-and-preflight-hardening.md`

### Orca/ImageMap profiles

- Local profile JSON now matches the fork startup model:
  - snapshot start first
  - disable wrapper prepare
  - explicit `START_PRINT`
  - full-colour profiles run standalone `REFORGE_PREFLIGHT` before
    `START_PRINT`
- Profile comments no longer claim that `[ff_print]` loads `MESH_DATA`.
- Relevant folder:
  - `local/creator5pro-orca-imagemap-profiles/`

### Snapshot timelapse

- Source includes lightweight still-frame macros for snapshot-only timelapse.
- The intended model is frames during print, no video render on the printer.
- Relevant files:
  - `pkgs/klipper-config/payload/config/ff-timelapse-snapshot.cfg`
  - `pkgs/klipper-config/payload/config/printer.base.cfg`
  - `pkgs/timelapse/build.sh`
  - `pkgs/moonraker/payload/config/moonraker.conf`

### Filament/runout and toolchange safety

- Source contains runout/motion-sensor changes intended to prevent false motion
  sensor faults during tool grab/release/load/purge paths.
- The intended policy is hard switch runout remains meaningful, while soft
  motion/clog sensing is disarmed during tool handling and only re-armed for
  the mounted tool when appropriate.
- Relevant files:
  - `pkgs/klipper-config/payload/config/ff-runout.cfg`
  - `pkgs/klipper/payload/klipper/klippy/extras/ff_tool.py`
  - `pkgs/klipper/payload/klipper/klippy/extras/ff_toolchange.py`

### SSH, LED, API/resource hardening

- Installer/source changes exist for persistent SSH host-key handling.
- Chamber LED startup behaviour is patched in source.
- Moonraker/camera/timelapse config has local hardening work staged.
- Relevant files:
  - `installer/runFirmwareExe.sh`
  - `pkgs/klipper-config/payload/config/ff-chamber.cfg`
  - `pkgs/moonraker/payload/config/moonraker.conf`

## Not yet proven by this inventory

- This doc does not prove the fork builds.
- This doc does not prove the USB installer flashes successfully.
- This doc does not prove the live printer is running these exact source files.
- Live proof still needs a controlled install, boot check, API check, safe mesh
  check, standalone preflight check, and a short print with snapshot capture.
