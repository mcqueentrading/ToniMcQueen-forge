#!/usr/bin/env bash
# tailscale -- upstream static mipsle binaries, no compile.
set -euo pipefail
. ./bin/common.sh
. pkgs/lib.sh

pkg_begin tailscale || exit 0
pkg_unpack "$TAILSCALE_TGZ"

_src="$PKG_WORK/src/tailscale_${TAILSCALE_VERSION}_mipsle"
[ -x "$_src/tailscale" ] || pkg_die "tailscale: no tailscale binary in $TAILSCALE_TGZ"
[ -x "$_src/tailscaled" ] || pkg_die "tailscale: no tailscaled binary in $TAILSCALE_TGZ"

pkg_stage "$_src/tailscale" "bin/tailscale"
pkg_stage "$_src/tailscaled" "bin/tailscaled"
chmod +x "$PKG_WORK/stage$MODDIR/bin/tailscale" "$PKG_WORK/stage$MODDIR/bin/tailscaled"

# Go's linux/mipsle port emits generic o32/mips32 ELF flags. The Creator 5
# userspace is mips32r2 + NAN2008; this kernel refuses the generic header and
# busybox sh reports it as "syntax error: unexpected (". The text segment is
# still valid for this CPU, so stamp the ABI flags the rest of the fork's MIPS
# binaries carry: noreorder, pic, cpic, nan2008, o32, mips32r2.
printf '\007\024\000\160' | dd \
    of="$PKG_WORK/stage$MODDIR/bin/tailscale" \
    bs=1 seek=36 conv=notrunc 2>/dev/null
printf '\007\024\000\160' | dd \
    of="$PKG_WORK/stage$MODDIR/bin/tailscaled" \
    bs=1 seek=36 conv=notrunc 2>/dev/null

pkg_ship "bin/tailscale" "bin/tailscaled"
pkg_end
