from lib.paths import ROOT


INSTALLER = ROOT / "installer" / "runFirmwareExe.sh"
LINK_PROG = ROOT / "pkgs" / "anvil-core" / "payload" / "bin" / "anvil-link-prog.sh"


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
    assert "cat > /usr/prog/etc/init.d/S51dropbear-reforge-once << 'ONCEEOF'" in text
    assert "sleep 20" in text
    assert "/etc/init.d/S50dropbear restart >/tmp/dropbear-reforge-once.log 2>&1" in text
    assert "rm -f /etc/init.d/S51dropbear-reforge-once /usr/prog/etc/init.d/S51dropbear-reforge-once" in text
    assert "/etc/init.d/S51dropbear-reforge-once >/tmp/dropbear-reforge-once-launch.log 2>&1" in text
    assert "test -r /etc/default/dropbear && . /etc/default/dropbear" in text
    assert ": \\${DROPBEAR_ARGS:=\"$DROPBEAR_KEY_ARGS\"}" in text
    assert "--exec /usr/sbin/dropbear -- \\$DROPBEAR_ARGS" in text
    assert "auto-generation" in text


def test_toniforge_helpers_are_exposed_on_ssh_path():
    installer = INSTALLER.read_text()
    link_prog = LINK_PROG.read_text()

    assert "PATH=/usr/data/anvil/bin:/usr/prog/bin:\\$PATH" in installer
    assert "export PATH" in installer
    assert 'dst="/usr/prog/bin/$name"' in link_prog
    assert "link_helper toniforge-tailscale" in link_prog
    assert "link_helper toniforge-tailscale-enable" in link_prog
    assert "link_helper toniforge-tailscale-disable" in link_prog
