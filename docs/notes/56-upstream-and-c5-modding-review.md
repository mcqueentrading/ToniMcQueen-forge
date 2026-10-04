# Upstream Reforge and Creator 5 modding review

Date: 2026-10-04

Repos checked:

- `https://github.com/mcqueentrading/cr5customfirmware`
- `https://github.com/FlashForge-C5-Modding-Group/Creator-5-Mods`
- `https://github.com/FlashForge-C5-Modding-Group/Creator-5-Scripts`
- `https://github.com/FlashForge-C5-Modding-Group/OpenCreator`
- `https://github.com/FlashForge-C5-Modding-Group/creator-5-update-creator`

Local clone area:

- `/home/unknown/Desktop/Documents/3dprints/reforge_external_research/`

## Reforge upstream gap

Local branch `creator5pro-local-fullcolour-tuning` was based on upstream
`96c0565`. Current fetched upstream/master and `mcqueentrading/master` both
point to `3d9f193`.

New upstream commits:

- `01892ff` - Fix toolchanger status while parking (#31)
- `3d9f193` - Clear active bed mesh before parking with Z unhomed (#32)

## Recommended upstream merges

### 1. Toolchanger park status ownership

Target-applied locally.

Reason: a standalone park and a park nested inside a toolchange should both
report `changing` while the dock/release sequence is moving. This keeps
transient dock/grab overlap from looking like a hard toolchanger error during a
normal park.

Source area:

- `pkgs/klipper/payload/klipper/klippy/extras/ff_toolchange.py`
- upstream test: `qa/static/test_toolchange_park.py`

Adaptation needed: our local `ff_toolchange.py` has runout and Z-offset changes,
so apply this as a targeted patch around `cmd_TOOLCHANGE_PARK`, not a blind
merge.

Local action:

- `cmd_TOOLCHANGE_PARK` now marks `self.changing` true for the whole park and
  restores the caller's previous state in `finally`.
- `qa/static/test_toolchange_park.py` covers standalone and nested parks,
  including exception paths.

### 2. Clear active bed mesh before parking with unhomed Z

Target-applied locally, high priority.

Reason: an active non-flat mesh can turn dock XY travel into physical Z motion.
If Z is not homed, Klipper may reject the move or move unsafely. This directly
matches the mesh/Z safety problems seen during preflight and bed-side changes.

Source area:

- `pkgs/klipper/payload/klipper/klippy/extras/ff_toolchange.py`
- upstream test: `qa/static/test_ff_toolchange_mesh.py`

Adaptation needed: upstream test currently expects old `START_PRINT` behaviour
with `BED_MESH_CLEAR` before `G28` and `BED_MESH_PROFILE LOAD=MESH_DATA`.
That conflicts with this fork's explicit mesh policy. Keep the Python
toolchanger guard, but change the static test expectations so `START_PRINT`
loads/probes only with `LEVEL=1` or `MESH=<profile>`.

Local action:

- `cmd_TOOLCHANGE_PARK` clears an active bed mesh before release/parking when Z
  is unhomed, so dock XY moves cannot become mesh-driven Z moves.
- The guard intentionally does not restore that mesh after a failed park,
  because restoring it before Z is homed would make the next park attempt unsafe.
- `qa/static/test_ff_toolchange_mesh.py` covers the clear/no-clear cases and
  this fork's explicit `START_PRINT` mesh policy.

## External modding repo ideas

### Camera 720p watchdog

Found in:

- `Creator-5-Mods/Basic/Unlock camera to 720p/start-webcam.sh`

Useful part:

- wait for `/dev/video0`
- run `mjpg_streamer` with explicit resolution/FPS
- log to `/usr/data/logs/mjpg.log`
- restart the stream if it exits

Recommendation: adapt as a Reforge camera service option, but do not default to
720p30 on this printer. For our timelapse/snapshot workflow, expose a lower-load
profile first, then make 720p30 an opt-in setting.

### Chamber fan / heater-aware M106

Found in:

- `Creator-5-Mods/Basic/Allow for Heating Without Cooling/README.md`

Useful part:

- decouple chamber recirculation from chamber exhaust/cooling when chamber
  heater is active.

Recommendation: adapt the policy into our `ff-chamber.cfg` or fan macros only
after checking Reforge's existing fan names. This is more relevant for ABS/ASA
than PLA/ImageMap.

### SSH host-key persistence

Found in:

- `Creator-5-Mods/Basic/SSH Persist/README.md`
- `Creator-5-Mods/Basic/Make SSH host key persist/README.md`

Useful part:

- confirms the underlying cause: `/etc/dropbear` points into volatile storage
  too early during boot.

Recommendation: keep our source-level installer/startup fix instead of copying
the manual root hack. The external docs are useful corroboration.

### Tailscale userspace networking

Found in:

- `Creator-5-Mods/Intermediate/Tailscale Remote Access/README.md`

Useful part:

- Tailscale needs `--tun=userspace-networking` because `/dev/net/tun` is not
  present.
- warns that Moonraker/root access over a tailnet is still sensitive.

Recommendation: do not ship Tailscale in the firmware. Document it as an
optional operator install, or prefer routing through a stronger external box
such as the NVIDIA PC.

### Nginx worker reduction

Found in:

- `Creator-5-Scripts/tweaks-c5.sh`

Useful part:

- force `worker_processes 1`
- validate config before replacing
- reload with HUP

Recommendation: compare with our packaged nginx config. If Reforge still ships
more than one worker, setting one worker is a sensible resource reduction.

### Loop script / Entware / Legacy NaN

Found in:

- `Creator-5-Scripts/tweaks-c5.sh`

Recommendation: do not import into Reforge directly. Reforge already has a
proper package/service model; loop-script hacks and Entware are useful for stock
firmware modding but should not become part of this firmware fork unless a
specific package cannot be staged cleanly.

### OpenCreator / SBC architecture notes

Found in:

- `OpenCreator/docs/rpi-klipper.md`
- `OpenCreator/docs/architecture.md`
- `OpenCreator/docs/printer-features.md`
- `klipper-c5/klippy/extras/creator5_toolchanger.py`
- `klipper-c5/test/test_creator5_toolchanger.py`

Useful ideas:

- stock X2600 host is resource constrained.
- external SBC path is better for AI, extra cameras, and heavy monitoring.
- toolchanger, AFC, filament mapping, and pressure-advance research are active
  areas.
- the faster toolchanger work is not a small gcode macro in the modding repos;
  it is a Klippy Python module in `klipper-c5`.
- `klipper-c5` separates safe fast travel from slow latch/dock movements. It
  keeps controlled dock/latch feeds, verifies sensors, then allows faster
  retreat/departure.

Relevant `klipper-c5` speed knobs:

- `clear_travel_speed`
- `dock_approach_speed`
- `pickup_predock_speed`
- `pickup_latch_speed`
- `pullback_speed`
- `pullback_slow_distance`
- `departure_speed`
- `pickup_departure_speed`
- `pickup_accel`

Current Reforge comparison:

- our `ff_toolchange.py` already has fast dock travel via `fast_feed`
  defaulting to `30000` mm/min, or 500 mm/s.
- our latch/approach path is already conservative enough to preserve the
  stock sensor-driven sequence.
- our likely avoidable delay is post-grab retreat: local
  `ff-toolchange.cfg` sets `grab_retreat_feed: 1500`, or 25 mm/s.
- release retreat is already `4800` mm/min, or 80 mm/s, which is close to the
  `klipper-c5` default departure speed.

Recommendation: use these as roadmap references, not immediate wholesale code.
For this fork, keep the printer lightweight and offload AI/photo analysis to
the NVIDIA PC or another SBC. For toolchange speed, do a targeted port:

1. merge the upstream Reforge park-status and unhomed-Z mesh guards first.
2. add an experimental fast-toolchange config/profile that raises only
   `grab_retreat_feed` from `1500` to `4800` or `5400`.
3. if more speed is needed, port the `klipper-c5` segmented post-grab idea:
   slow/controlled pullback until latch clearance, then fast departure after
   sensor verification.
4. add static tests based on `klipper-c5/test/test_creator5_toolchanger.py`
   proving fast travel is used only after the latch/grab state is safe.

Do not replace `ff_toolchange.py` wholesale. Our fork has Reforge-specific
toolchanger status, runout safety, Z-offset, and print-start integration that
would be easy to regress.

Implemented local source patch:

- added `grab_departure_feed` to `ff_toolchange.py`.
- left legacy `grab_retreat_feed` accepted for old `printer.cfg` overrides.
- added a pre-departure sensor check before using the faster feed.
- shipped `grab_departure_feed: 4800` in `ff-toolchange.cfg`, matching the
  already-used controlled pullback/release speed.

This is intentionally narrower than the full `klipper-c5` module: the latch
approach, retries, polling, and Reforge-specific status/runout/Z-offset logic
stay owned by Reforge.

### OpenCreator slicer profile notes

Found in:

- `OpenCreator/docs/slicer-config.md`

Useful parts:

- turn Orca `Arc fitting` off because this target is Klipper/Moonraker.
- use Moonraker as the printer agent and keep 3MF upload disabled.
- optional tuning candidates: 75 mm/s retract/deretract, 0.24 mm Z-hop.

Local action:

- disabled `enable_arc_fitting` in the stored Reforge process presets.
- added a separate `ARC TEST` process preset for controlled `G2`/`G3`
  comparison without changing the safe default profiles.
- left `host_type: octoprint` untouched in the JSON because Orca-derived
  profiles can use that internal string even when the UI presents a Moonraker
  connection. Validate in the slicer UI before changing it.
- kept retraction and Z-hop values as future tuning, not defaults. They need a
  sliced preview plus physical print evidence before becoming fork policy.

### OpenCreator pressure-advance notes

Found in:

- `OpenCreator/docs/printer-features.md`
- `klipper-c5/test/test_c5_eboard_pa.py`

Useful parts:

- the stock "Flow Calibration" path is pressure advance, not generic flow.
- candidate values and eboard commands are documented around `PA_ACTION` and
  `PA_GET`.

Local action: no code change in this pass. This fork already has local
pressure-advance research and Reforge-specific PA config; the OpenCreator notes
are corroboration and test-reference material.

### OpenCreator feature list

Found in:

- `OpenCreator/docs/cfwfeatures.md`

Potential roadmap items:

- ZMax on print end.
- near-zero purge modes.
- single-tool calibration.
- AFC/infinite-spool style filament handling.
- faster camera path.
- power-loss recovery.

Local action: document only. These are larger feature tracks and should not be
mixed into the current toolchange/chamber/timelapse work without isolated tests.

### OpenCreator chamber safety note

Found in:

- `OpenCreator/docs/architecture.md`

Useful part:

- community notes warn that chamber-area plastic can deform above about 70 C.

Local action: documented as an operator warning. Do not treat the configured
Klipper `max_temp` as a normal chamber target.

### creator-5-update-creator

Found in:

- `creator-5-update-creator/scripts/build_update.py`

Useful ideas:

- clean staged update-package builder
- explicit source/stage separation
- tests around packaging

Recommendation: compare later against Reforge's existing installer only if our
USB build path becomes unreliable. Not needed before the next Reforge build.

## Suggested order

1. Keep the target-applied upstream `TOOLCHANGE_PARK` fixes covered by tests
   until this branch can be cleanly rebased or cherry-picked.
2. Consider camera watchdog/service hardening.
3. Consider nginx worker/process hardening.
4. Leave Tailscale, Entware, loop scripts, and SBC migration as documented
   optional/external paths.
5. Use OpenCreator slicer notes to keep arc fitting off in Reforge presets.
6. Keep pressure advance, AFC, power-loss recovery, and SBC offload as
   separate roadmap items with tests, not opportunistic imports.
