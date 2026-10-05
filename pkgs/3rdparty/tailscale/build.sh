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

pkg_ship "bin/tailscale" "bin/tailscaled"
pkg_end
