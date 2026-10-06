from lib.paths import ROOT


INSTALLER = ROOT / "installer" / "runFirmwareExe.sh"
LINK_PROG = ROOT / "pkgs" / "anvil-core" / "payload" / "bin" / "anvil-link-prog.sh"
DROPBEAR_FIX = ROOT / "pkgs" / "anvil-core" / "payload" / "etc" / "s6-rc" / "source" / "dropbear-fix"
OK_ALL_DROPBEAR_FIX = ROOT / "pkgs" / "anvil-core" / "payload" / "etc" / "s6-rc" / "source" / "ok-all" / "contents.d" / "dropbear-fix"


def test_dropbear_host_key_patch_is_idempotent_and_conditional():
    text = INSTALLER.read_text()

    assert "DROPBEAR_KEY_ARGS=\"\"" in text
    assert "dropbear_rsa_host_key" in text
    assert "dropbear_ecdsa_host_key" in text
    assert "printf 'DROPBEAR_ARGS=\"%s\"\\n' \"$DROPBEAR_KEY_ARGS\"" in text
    assert "[ -f \"$_dropbear_init\" ] || continue" not in text
    assert "for _dropbear_old in \\" in text
    assert "rm -f \"$_dropbear_old\"" in text
    assert "cat > /usr/prog/etc/init.d/S50dropbear << INITEOF" in text
    assert "cp -f /usr/prog/etc/init.d/S50dropbear /etc/init.d/S50dropbear" in text
    assert "/usr/data/zmod/zmod/.shell/eabi/dropbear" in text
    assert "cat > /usr/prog/etc/init.d/S98zmod-dropbear-clean-once << 'ZMODEOF'" in text
    assert "rm -f /usr/data/zmod/zmod/.shell/S60dropbear /usr/data/zmod/zmod/.shell/eabi/dropbear" in text
    assert "rm -f /etc/init.d/S98zmod-dropbear-clean-once /usr/prog/etc/init.d/S98zmod-dropbear-clean-once" in text
    assert "/etc/init.d/S98zmod-dropbear-clean-once >/tmp/zmod-dropbear-clean-once-launch.log 2>&1" in text
    assert "S99dropbear-reforge-once" in text
    assert "test -r /etc/default/dropbear && . /etc/default/dropbear" in text
    assert ": \\${DROPBEAR_ARGS:=\"$DROPBEAR_KEY_ARGS\"}" in text
    assert "--exec /usr/sbin/dropbear -- \\$DROPBEAR_ARGS" in text
    assert "auto-generation" in text


def test_dropbear_fix_is_in_the_boot_graph():
    up = (DROPBEAR_FIX / "up").read_text()

    assert (DROPBEAR_FIX / "type").read_text().strip() == "oneshot"
    assert (DROPBEAR_FIX / "timeout-up").read_text().strip() == "60000"
    assert (DROPBEAR_FIX / "dependencies.d" / "wifi").is_file()
    assert OK_ALL_DROPBEAR_FIX.is_file()
    assert "sleep 20" in up
    assert "grep '[d]ropbear' | grep -q -- ' -R'" in up
    assert "/etc/init.d/S50dropbear restart" in up
    assert "/etc/init.d/S50dropbear start" in up
    assert "dropbear-fix: OK no -R daemon present" in up


def test_toniforge_helpers_are_exposed_on_ssh_path():
    installer = INSTALLER.read_text()
    link_prog = LINK_PROG.read_text()

    assert "PATH=/usr/data/anvil/bin:/usr/prog/bin:\\$PATH" in installer
    assert "export PATH" in installer
    assert 'dst="/usr/prog/bin/$name"' in link_prog
    assert "link_helper toniforge-tailscale" in link_prog
    assert "link_helper toniforge-tailscale-enable" in link_prog
    assert "link_helper toniforge-tailscale-disable" in link_prog
