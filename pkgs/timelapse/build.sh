#!/usr/bin/env bash
# moonraker-timelapse -- two files out of the pinned tarball. Nothing is
# compiled, and the encoder is anvil-ffmpeg's problem, not this recipe's.
#
# UPSTREAM'S scripts/install.sh IS NOT USED: it clones into a home directory,
# symlinks into a Moonraker checkout, appends to live config and registers an
# update_manager entry that re-clones over the network -- all of which this
# repo does differently. The tarball is just a source, and the two files it
# actually contributes are placed by hand.
#
# GitHub wraps the archive in moonraker-timelapse-<sha>/; the paths reach
# through that rather than hiding the archive's shape behind --strip-components.
set -euo pipefail
. ./bin/common.sh
. pkgs/lib.sh

pkg_begin timelapse || exit 0
pkg_unpack "$TIMELAPSE_TGZ"

_src="$PKG_WORK/src/moonraker-timelapse-$TIMELAPSE_VERSION"

# pkgs/moonraker's guard, for the same reason: a tarball whose shape changed
# would stage nothing, which is a clean build and a tab that never appears.
[ -f "$_src/component/timelapse.py" ] || pkg_die \
    "timelapse: no component/timelapse.py in $(basename "$TIMELAPSE_TGZ")"
[ -f "$_src/klipper_macro/timelapse.cfg" ] || pkg_die \
    "timelapse: no klipper_macro/timelapse.cfg in $(basename "$TIMELAPSE_TGZ")"

# Inside anvil-moonraker's directory, because Moonraker resolves a component
# with import_module(".components.<name>", "moonraker") and looks nowhere else.
# Two packages, different files, one directory -- apk is content, and
# anvil-moonraker's Depends orders the install.
#
# Reforge runs snapshot-only timelapse on a weak printer CPU. Patch upstream's
# frame zip path so successful archives do not leave hundreds of loose JPEGs in
# /usr/data/anvil-timelapse after every print.
_component="$PKG_WORK/timelapse.py"
cp "$_src/component/timelapse.py" "$_component"
python3 - "$_component" <<'PY'
from pathlib import Path
import sys

path = Path(sys.argv[1])
text = path.read_text()
missing_imports = []
if "import os" not in text:
    missing_imports.append("import os")
if "import logging" not in text:
    missing_imports.append("import logging")
if missing_imports:
    text = "\n".join(missing_imports) + "\n" + text
old = '''            zipObj = ZipFile(self.out_dir + outfileFull, "w")

            for frame in filelist:
                zipObj.write(frame, frame.split("/")[-1])
'''
new = '''            with ZipFile(self.out_dir + outfileFull, "w") as zipObj:
                for frame in filelist:
                    zipObj.write(frame, frame.split("/")[-1])

            for frame in filelist:
                try:
                    os.remove(frame)
                except OSError as err:
                    logging.info(f"timelapse: failed to remove archived frame {frame}: {err}")
'''
if old not in text:
    raise SystemExit("timelapse: saveFramesZip body changed upstream")
path.write_text(text.replace(old, new))
PY
pkg_stage "$_component" "moonraker/components/timelapse.py"

# $MODDIR/config is a staging directory: anvil-link-prog.sh symlinks every
# .cfg in it into /usr/data/anvil-data/config, the mod's own config directory,
# where printer.base.cfg's [include timelapse.cfg] resolves. A link rather
# than a copy, so an `apk upgrade` of this package changes what Klipper reads.
#
# Reforge's snapshot profiles call TIMELAPSE_TAKE_FRAME through a lightweight
# wrapper. Upstream moonraker-timelapse ships that macro disabled by default,
# which makes a missing/old wrapper silently produce no frames. Ship our fork
# with still-frame capture enabled by default as a safer printer-local default.
_macro="$PKG_WORK/timelapse.cfg"
cp "$_src/klipper_macro/timelapse.cfg" "$_macro"
sed -i 's/^variable_enable: False$/variable_enable: True/' "$_macro"
grep -qx 'variable_enable: True' "$_macro" || \
    pkg_die "timelapse: failed to enable TIMELAPSE_TAKE_FRAME by default"
pkg_stage "$_macro" "config/timelapse.cfg"

pkg_ship "moonraker/components/timelapse.py" "config/timelapse.cfg"
pkg_end
