#!/usr/bin/env bash
set -euo pipefail

DEV="${DEV:-/dev/sda1}"
MOUNT="${MOUNT:-/home/unknown/ff_usb_check}"
PKG_NAME="Creator5Pro-tonimcqueen-forge-20261016.tgz"
EXPECTED_SHA256="85f85dce44ab43935545479e94e3670cca68d46bca7c63b2890677526de9bf71"

echo "Verifying ToniMcQueen Forge USB installer"
echo "Device: $DEV"
echo

if [[ ! -b "$DEV" ]]; then
    echo "ERROR: $DEV does not exist." >&2
    lsblk -o NAME,TRAN,RM,RO,SIZE,FSTYPE,LABEL,MOUNTPOINTS,MODEL >&2 || true
    exit 1
fi

echo "Block devices:"
lsblk -o NAME,TRAN,RM,RO,SIZE,FSTYPE,LABEL,MOUNTPOINTS,MODEL
echo

mkdir -p "$MOUNT"

cleanup() {
    if findmnt -rn "$MOUNT" >/dev/null 2>&1; then
        doas umount "$MOUNT"
    fi
}
trap cleanup EXIT

if ! findmnt -rn "$MOUNT" >/dev/null 2>&1; then
    doas mount -o "ro,uid=$(id -u),gid=$(id -g),utf8" "$DEV" "$MOUNT"
fi

echo "USB contents:"
find "$MOUNT" -maxdepth 1 -type f -printf '  %f  %s bytes\n' | sort
echo

copied="$MOUNT/$PKG_NAME"
if [[ ! -f "$copied" ]]; then
    echo "ERROR: expected installer not found: $PKG_NAME" >&2
    exit 1
fi

echo "Verifying SHA256:"
printf '%s  %s\n' "$EXPECTED_SHA256" "$copied" | sha256sum -c -

echo
echo "OK. USB contains the latest Tailscale-enabled Creator5Pro installer."
