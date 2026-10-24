# Bounded levelboard wake-up after host disconnect

Deployed to one Creator 5 Pro on 24 October 2026 with a rollback backup.
Limited cold/no-motion hardware evidence is recorded below; this is not a
general firmware/print validation or a fix for all browser disconnects.

The pinned Klipper fork runs `os.system("cd /usr/prog/bin && ./wakeup_level")`
after `klippy:disconnect`. A hung helper keeps `Printer.run()` from returning,
so the normal restart loop never completes. Service termination can leave the
helper orphaned with `/dev/ttyS7` open, interfering with the next connection.

`pkgs/klipper/build.sh` now applies a narrow source patch before building and
stages `ff_restart_helper.py` alongside klippy. Patch/helper live in payload/
so package input hashing invalidates cached output. Generated work/ trees and
the upstream source pin are not edited by hand.

The helper retains the existing vendor wake-up, called after MCU disconnect.
It uses an absolute executable and no shell, closes inherited descriptors,
starts an owned session and bounds normal execution to 10 seconds. Cleanup
sends TERM then KILL to that session and waits for the direct child, with
one-second grace bounds. It logs nonzero exit, launch error and timeout.
An unreapable immediate child changes the host run result to error_exit rather
than continuing a normal restart. Descendants are signalled as a group; only
the direct child can be reaped by this parent without subreaper facilities.

SIGTERM/SIGINT received while the helper is owned trigger cleanup and preserve
the prior signal disposition. This is not a complete supervisor recovery
solution: uncatchable SIGKILL, uninterruptible kernel I/O, the spawn/ownership
handoff window and pre-existing unmanaged/orphan port users remain limitations.
Do not claim no-orphan guarantees for all possible parent-death timings.

No new firmware flashing, movement, temperature changes, toolchange code,
calibration offsets, startup handover or Moonraker/proxy settings are introduced
by this patch. The earlier browser-only disconnects remain a separate issue.
No claim is made that terminating a vendor helper necessarily leaves the
levelboard able to reconnect; that is a hardware gate.

## Verification boundary

Local tests cover helper success/failure/missing executable, invalid bounds,
timeouts, uncooperative child/descendant termination, service-style SIGTERM,
descriptor isolation, main-thread restriction and unreapable-child status.
They apply the patch to the actual pinned source archive and exercise restart,
firmware_restart, exit and error_exit event ordering, including cleanup failure.
These do not open serial ports or call the real vendor helper.

Before deployment, review process ownership and the retained wake-up requirement.
Back up the exact installed host file and record its hash: the printer copy has
an unrelated asynchronous-shutdown compatibility change that must be preserved.
Do not replace it with a whole upstream file merely to apply this patch.

Separate supervised cold/no-motion hardware approval is required. First verify
one restart reconnects all boards without lingering helpers, then verify repeated
restarts and configuration-save paths. Do not restore fast toolchange tuning or
start prints as part of restart verification. Keep a rollback and clean power
restart procedure available. Full cross-package build and hardware checks remain
pending even when source/process tests pass.

## Initial deployment evidence

The deployed host file preserves its unrelated invoke_async_shutdown compatibility
change; only the exit-time helper call was replaced. Original toolchange module,
printer configuration and speed settings were unchanged.

62 selected offline tests passed, including 24 restart-helper regressions and
toolchange/package-layout checks. The patch applies without fuzz to the pinned
source archive and the saved installed file. No full cross-package or replica
installer build is claimed by these tests.

One normal RESTART completed a full no-motion check in approximately 32 seconds:
disconnect/startup/ready observed, heater targets zero, unhomed position and T1
mount identity unchanged. The vendor helper timed out at 10 seconds, was cleaned
up and left no lingering ttyS7 helper; only Klipper held that port afterward.

A second RESTART also reconnected to ready in approximately 24 seconds, but
the immediate post-ready mount identity assertion failed. The next scheduled
restart was NOT sent. Subsequent read-only status and ten additional samples
showed valid T1 identity and unchanged unhomed position. This remains a failed
full cycle check, not a silently accepted pass or proven sensor-settling cause;
the instantaneous discrepant identity was not captured in that failed snapshot.
Further repeat/startup-settling verification remains pending. No motion/heating
or faster toolchange was part of deployment checks.

Live FIRMWARE_RESTART, SAVE_CONFIG, SIGKILL/orphan recovery, concurrent owners,
printing and older browser/WebSocket failures remain unverified. Source update
does not retroactively change previously published installer downloads.
