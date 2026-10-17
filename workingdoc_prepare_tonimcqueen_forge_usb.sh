#!/usr/bin/env bash
set -euo pipefail

DEV="${DEV:-/dev/sda1}"
DISK="${DISK:-/dev/sda}"
MOUNT="${MOUNT:-/home/unknown/ff_usb}"
LABEL="${LABEL:-TONIFORGE}"
PKG="${PKG:-/home/unknown/Desktop/Documents/3dprints/reforge_firmware_repo/work/out/Creator5Pro-tonimcqueen-forge-20261017.tgz}"
PKG_NAME="$(basename "$PKG")"
EXPECTED_SHA256="${EXPECTED_SHA256:-276a2b1f2193166b465f6e8e004abd188552d330f75bac2ed41c963e014635f4}"

if [[ "$(id -u)" == "0" ]]; then
    AS_ROOT=1
    RUN_PRIV=()
    OWNER_USER="${SUDO_USER:-unknown}"
    OWNER_UID="$(id -u "$OWNER_USER" 2>/dev/null || stat -c %u /home/unknown)"
    OWNER_GID="$(id -g "$OWNER_USER" 2>/dev/null || stat -c %g /home/unknown)"
else
    AS_ROOT=0
    RUN_PRIV=(doas)
    OWNER_UID="$(id -u)"
    OWNER_GID="$(id -g)"
fi

run_priv() {
    if [[ "$AS_ROOT" == "1" ]]; then
        "$@"
    else
        "${RUN_PRIV[@]}" "$@"
    fi
}

echo "Preparing ToniMcQueen Forge USB installer"
echo "Device:  $DEV"
echo "Disk:    $DISK"
echo "Package: $PKG"
echo "SHA256:  $EXPECTED_SHA256"
echo "Owner:   uid=$OWNER_UID gid=$OWNER_GID"
echo
echo "WARNING: this will erase all files on $DEV"
echo

if [[ ! -b "$DEV" ]]; then
    echo "ERROR: $DEV does not exist." >&2
    lsblk -o NAME,TRAN,RM,RO,SIZE,FSTYPE,LABEL,MOUNTPOINTS,MODEL >&2 || true
    exit 1
fi

if [[ ! -b "$DISK" ]]; then
    echo "ERROR: $DISK does not exist." >&2
    exit 1
fi

if [[ ! -f "$PKG" ]]; then
    echo "ERROR: firmware package not found: $PKG" >&2
    exit 1
fi

echo "Verifying local package before touching USB"
printf '%s  %s\n' "$EXPECTED_SHA256" "$PKG" | sha256sum -c -
echo

echo "Current block devices:"
lsblk -o NAME,TRAN,RM,RO,SIZE,FSTYPE,LABEL,MOUNTPOINTS,MODEL
echo

disk_info="$(lsblk -dn -o NAME,TRAN,RM,RO,SIZE,MODEL "$DISK")"
echo "Disk check:"
echo "  $disk_info"

tran="$(lsblk -dn -o TRAN "$DISK" | tr -d '[:space:]')"
rmflag="$(lsblk -dn -o RM "$DISK" | tr -d '[:space:]')"
roflag="$(lsblk -dn -o RO "$DISK" | tr -d '[:space:]')"

if [[ "$tran" != "usb" || "$rmflag" != "1" ]]; then
    echo "ERROR: $DISK does not look like a removable USB disk. Refusing." >&2
    exit 1
fi

if [[ "$roflag" != "0" ]]; then
    echo "ERROR: $DISK is read-only. Check the USB adapter/lock switch." >&2
    exit 1
fi

echo
read -r -p "Type ERASE to format $DEV and copy $PKG_NAME: " confirm
if [[ "$confirm" != "ERASE" ]]; then
    echo "Aborted."
    exit 1
fi

if [[ "$AS_ROOT" == "0" ]]; then
    echo
    echo "Authenticating doas before making changes"
    run_priv true
fi

cleanup() {
    if findmnt -rn "$MOUNT" >/dev/null 2>&1; then
        sync || true
        run_priv umount "$MOUNT" || true
    fi
}
trap cleanup EXIT

echo
echo "Unmounting any current mounts for $DEV"
while read -r target; do
    [[ -n "$target" ]] || continue
    echo "  umount $target"
    run_priv umount "$target"
done < <(findmnt -rn -S "$DEV" -o TARGET | sort -r)

echo
echo "Formatting $DEV as FAT32 label $LABEL"
run_priv mkfs.vfat -F 32 -n "$LABEL" "$DEV"

echo
echo "Mounting $DEV at $MOUNT"
mkdir -p "$MOUNT"
run_priv mount -o "uid=$OWNER_UID,gid=$OWNER_GID,utf8" "$DEV" "$MOUNT"

echo
echo "Copying firmware package to USB root"
cp -f "$PKG" "$MOUNT/$PKG_NAME"
sync

echo
echo "Verifying copied package"
printf '%s  %s\n' "$EXPECTED_SHA256" "$MOUNT/$PKG_NAME" | sha256sum -c -

echo
echo "USB contents:"
find "$MOUNT" -maxdepth 1 -type f -printf '  %f  %s bytes\n' | sort

echo
echo "Unmounting USB"
cleanup
trap - EXIT

echo
echo "Done. USB is ready and unmounted."
echo "Use on Creator5Pro only:"
echo "  $PKG_NAME"
