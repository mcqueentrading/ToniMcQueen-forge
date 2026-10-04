# Creator 5 Pro Local Full-Colour Fork Roadmap

Date: 2026-09-30

Branch: `creator5pro-local-fullcolour-tuning`

Base repo: `Klipper4FlashForge/firmware`

Printer target: FlashForge Creator 5 Pro running Reforge with OrcaSlicer ImageMap full-colour CMYK/CMYW workflows.

## Why This Fork Exists

The live printer is no longer being used like a stock Reforge install. We need
repeatable behaviour for full-colour prints, ImageMap texture workflows, camera
monitoring, and long multi-tool jobs. These changes should be tracked in source
instead of applied as one-off printer edits.

## Current Local Requirements

- Preserve Reforge's open Klipper/Moonraker/Fluidd control stack.
- Keep Creator 5 Pro toolchanger support.
- Support ImageMap-generated G-code cleanly.
- Avoid participating tools cooling to `0 C` during active multi-tool prints.
- Keep recently used docked tools warm enough to reduce long reheat delays.
- Prime/purge tools reliably before model moves, especially after idle periods.
- Keep timelapse paths aligned between Moonraker, Mainsail/Fluidd, Helix, and filesystem directories.
- Keep SSH host keys persistent so normal reboot does not trigger host-key warnings.
- Reduce boot/startup resource waste where practical.
- Keep update/restore path documented so the printer can return to stock if needed.

## Patch Areas

### 1. Timelapse Path Fix

Shipped Reforge defaults currently indicate:

```ini
[timelapse]
output_path: /usr/data/timelapse/
frame_path: /usr/data/anvil-timelapse/
snapshoturl: http://127.0.0.1:8080/?action=snapshot
```

The printer display appears to have a timelapse setting pointed at the wrong
directory. Before changing source, inspect the live printer with:

```sh
bash /home/unknown/Desktop/Documents/3dprints/workingdoc_inspect_reforge_timelapse_paths.sh
```

Fork goal:

- Ensure the display/UI and Moonraker agree on the timelapse output directory.
- Use snapshot-only capture for print monitoring. The local profile/macro path
  captures at most one JPEG per minute and deliberately does not render video on
  the printer.
- Ensure raw frames and rendered videos are saved under persistent `/usr/data`, not `/tmp`.
- Keep Mainsail/Fluidd able to list rendered videos.
- Avoid path changes that increase RAM pressure.

### 2. Warm Docked Tool Temperatures

Observed need:

- FlashForge stock kept participating tools around a warm idle temperature rather than shutting them fully off.
- Reforge/ImageMap G-code allowed participating tools to cool too aggressively, causing long waits and possible purge/clog symptoms.

Local target policy:

```text
Selected tool: heat to print temperature, usually 220 C for Elegoo PLA.
Participating docked tool used soon: keep around 120 C.
Participating docked tool used much later: optionally allow lower idle.
Participating active print tools: do not set to 0 C.
Non-participating tools: can stay off.
```

Fork goal:

- Move this out of one-off G-code patch scripts and into slicer profile plus Reforge-compatible macros where possible.
- Keep the behaviour explicit and measurable in generated G-code.

### 3. Preflight Multi-Tool Purge

Observed need:

- Early ImageMap full-colour prints produced tool "clog" symptoms even when tools purged successfully afterward.
- Stock FlashForge did a heavier initial purge for the tools used in the print.

Current local source change:

- Purge each participating tool at the rear before printing.
- Temporarily use a heavier purge, `150 mm`, for debugging in `ff-filament.cfg`.
- Add an explicit ImageMap full-colour Orca profile that owns print startup instead of relying on the legacy `[ff_print]` auto-prepare path.
- Confirm visible purge waste before starting the model.

Fork goal:

- Keep `REFORGE_PREFLIGHT` as a standalone tool purge/check macro. It deliberately does not call `START_PRINT`, does not home, and does not load a mesh.
- Keep actual print setup in `START_PRINT`, called explicitly by the slicer profile or by the operator.
- Keep purge location rear-safe and avoid dumping filament into the front fan.
- Use the wipe path where useful, but avoid long blocking cool-down waits unless required.
- Do not blindly load old `MESH_DATA`. `START_PRINT` loads a mesh only when `LEVEL=1` or `MESH=<profile>` is explicit; otherwise it leaves the current active mesh alone.

### 4. Toolchange Speed Tuning

Measured local baseline:

```text
Current Reforge mechanical toolchange: about 5.2 s
Stock FlashForge estimate: about 6.0 s
Community target: about 3.5 s
```

Possible tuning knobs:

```ini
[ff_toolchange]
fast_feed: 30000
slow_feed: 5400
release_slow_feed: 5400
grab_retreat_feed: 1500
release_retreat_feed: 4800
accel_move: 8000
```

Possible geared-stepper speed test:

```text
STEPPER_LOCK SPEED:    0.25 -> 0.3125
STEPPER_UNLOCK SPEED:  0.50 -> 0.625
MOTOR_GRAB2 SPEED:     0.02 -> 0.025
```

Fork goal:

- Keep baseline behaviour as a safe profile.
- Add an experimental faster profile behind a clearly named option.
- Test staged changes separately: travel acceleration first, lock/unlock speed second, path sequencing third.

### 5. Startup LED Default

Preference:

- Printer should boot with chamber LED off unless explicitly turned on.

Known command:

```gcode
SET_LED LED=chamber_led WHITE=0
```

Fork goal:

- Find the real stock/Reforge startup source of the LED-on behaviour.
- Patch source instead of adding a delayed override macro, unless no clean source exists.

### 6. SSH Host-Key Persistence

Problem:

- Reforge/Dropbear can regenerate host keys if configured only with volatile runtime storage.

Known working persistence target:

```text
/usr/data/dropbear/dropbear_rsa_host_key
/usr/data/dropbear/dropbear_ecdsa_host_key
```

The local installer also strips the stock Dropbear `-R` host-key autogeneration
flag from the live init script. The goal is stable SSH host identity after
normal reboot/update work, not a new host key every time the firmware stack is
touched.

Fork goal:

- Make persistent host-key generation/use part of Reforge install/startup.
- Avoid normal reboot changing SSH host identity.

### 7. Camera and Resource Use

Constraints:

- Printer hardware is limited.
- Camera/Mainsail/Moonraker can consume meaningful CPU.
- External monitoring through the NVIDIA PC or another SBC is preferred for AI spaghetti detection.

Fork goal:

- Keep printer-side camera service functional.
- Avoid expensive local AI or heavy processing on the printer.
- Make camera URLs and timelapse output stable for external tooling.

## Development Rules

- Do not patch live printer files first when a source-level fix is possible.
- Do not edit mod-owned config on the printer during a print.
- Preserve current upstream branch for clean pulls.
- Keep local changes on `creator5pro-local-fullcolour-tuning`.
- Each firmware behaviour change gets one commit and one test note.
- Build and flash only after source diff is reviewed.

## First Implementation Order

1. Inspect live timelapse mismatch and write the exact finding into this repo.
2. Patch timelapse defaults if the mismatch is source-level.
3. Add persistent SSH host-key behaviour to install/startup scripts. Source patch added in `installer/runFirmwareExe.sh`.
4. Find and patch LED startup source. Source patch added in `pkgs/klipper-config/payload/config/ff-chamber.cfg`.
5. Convert warm parked-tool/preflight purge behaviour into Reforge-aware macro/profile source.
   Current source now disables automatic `FF_BEFORE_PRINT_START` prepare by default, keeps `REFORGE_PREFLIGHT` standalone, and makes `START_PRINT` mesh loading explicit.
6. Only after reliable prints, start toolchange speed tuning.

## Related Local Files Outside Repo

```text
/home/unknown/Desktop/Documents/3dprints/reforge_toolchange_and_temperature_tuning_notes_2026-09-26.md
/home/unknown/Desktop/Documents/3dprints/reforge_stock_led_edit_plan_2026-09-28.md
/home/unknown/Desktop/Documents/3dprints/reforge_ssh_hostkey_persistence_2026-09-26.md
/home/unknown/Desktop/Documents/3dprints/workingdoc_inspect_reforge_timelapse_paths.sh
/home/unknown/Desktop/Documents/3dprints/workingdoc_fix_reforge_hostkey_and_pull_timelapse.sh
```
