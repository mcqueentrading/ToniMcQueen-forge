#!/usr/bin/env bash
# Download the tagged Creator 5 Pro installer and prepare /dev/sda1.
# The delegated formatter performs the removable-disk and ERASE checks.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")" && pwd)"
TAG="${TAG:-v20261018c-creator5pro-local-fullcolour}"
ASSET="${ASSET:-Creator5Pro-anvil-20261018c.tgz}"
URL="https://github.com/mcqueentrading/ToniMcQueen-forge/releases/download/${TAG}/${ASSET}"
PKG_DIR="${PKG_DIR:-$REPO_ROOT/work/out}"
PKG="$PKG_DIR/$ASSET"

mkdir -p "$PKG_DIR"

echo "Preparing ToniMcQueen Forge USB installer"
echo "Release: $TAG"
echo "Asset:   $ASSET"
echo "Device:  ${DEV:-/dev/sda1}"
echo
echo "Downloading and verifying the release asset"
curl -fL --retry 3 --retry-delay 2 "$URL" -o "$PKG"

SHA256="$(sha256sum "$PKG" | awk '{print $1}')"
echo "SHA256:  $SHA256"
printf '%s  %s\n' "$SHA256" "$PKG" | sha256sum -c -

echo
echo "The GitHub release asset is ready. The next command can erase the USB."
echo
PKG="$PKG" EXPECTED_SHA256="$SHA256" \
    bash "$REPO_ROOT/workingdoc_rewrite_tonimcqueen_forge_usb.sh"
