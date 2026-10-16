#!/usr/bin/env bash
set -euo pipefail

DISK="${DISK:-/dev/sda}"
DEV="${DEV:-/dev/sda1}"
MOUNT="${MOUNT:-/home/unknown/ff_usb}"
LABEL="${LABEL:-TONIFORGE}"
PKG="${PKG:-/home/unknown/Desktop/Documents/3dprints/reforge_firmware_repo/work/out/Creator5Pro-tonimcqueen-forge-20261016.tgz}"
PKG_NAME="$(basename "$PKG")"
EXPECTED_SHA256="${EXPECTED_SHA256:-85f85dce44ab43935545479e94e3670cca68d46bca7c63b2890677526de9bf71}"

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

cleanup_mount() {
    if findmnt -rn "$MOUNT" >/dev/null 2>&1; then
        sync || true
        run_priv umount "$MOUNT" || true
    fi
}
trap cleanup_mount EXIT

echo "Rewriting ToniMcQueen Forge USB installer"
echo "Disk:    $DISK"
echo "Device:  $DEV"
echo "Package: $PKG"
echo "SHA256:  $EXPECTED_SHA256"
echo "Owner:   uid=$OWNER_UID gid=$OWNER_GID"
echo
echo "WARNING: this will erase and repartition the whole USB disk: $DISK"
echo

if [[ ! -b "$DISK" ]]; then
    echo "ERROR: $DISK does not exist." >&2
    lsblk -o NAME,TRAN,RM,RO,SIZE,FSTYPE,LABEL,MOUNTPOINTS,MODEL >&2 || true
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
read -r -p "Type ERASE to wipe $DISK and copy $PKG_NAME: " confirm
if [[ "$confirm" != "ERASE" ]]; then
    echo "Aborted."
    exit 1
fi

if [[ "$AS_ROOT" == "0" ]]; then
    echo
    echo "Authenticating doas before making changes"
    run_priv true
fi

echo
echo "Unmounting anything currently mounted from $DISK"
while read -r node; do
    [[ -n "$node" ]] || continue
    while read -r target; do
        [[ -n "$target" ]] || continue
        echo "  umount $target"
        run_priv umount "$target"
    done < <(findmnt -rn -S "$node" -o TARGET | sort -r)
done < <(lsblk -lnpo NAME "$DISK")

echo
echo "Wiping old filesystem and partition signatures"
while read -r node; do
    [[ -n "$node" ]] || continue
    run_priv wipefs -a "$node" >/dev/null 2>&1 || true
done < <(lsblk -lnpo NAME "$DISK" | sort -r)

echo
echo "Creating one FAT32 partition"
if [[ "$AS_ROOT" == "1" ]]; then
    sfdisk "$DISK" <<EOF
label: dos
unit: sectors

$DEV : start=2048, type=c
EOF
else
    printf 'label: dos\nunit: sectors\n\n%s : start=2048, type=c\n' "$DEV" | doas sfdisk "$DISK"
fi

run_priv partprobe "$DISK" || true
run_priv udevadm settle || true
sleep 2

if [[ ! -b "$DEV" ]]; then
    echo "ERROR: expected partition did not appear: $DEV" >&2
    lsblk -o NAME,TRAN,RM,RO,SIZE,FSTYPE,LABEL,MOUNTPOINTS,MODEL >&2 || true
    exit 1
fi

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
cleanup_mount
trap - EXIT

echo
echo "Done. USB is ready and unmounted."
echo "Use on Creator5Pro only:"
echo "  $PKG_NAME"
