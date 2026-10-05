from lib.paths import ROOT


INSTALLER = ROOT / "installer" / "runFirmwareExe.sh"


def test_dropbear_host_key_patch_is_idempotent_and_conditional():
    text = INSTALLER.read_text()

    assert "DROPBEAR_KEY_ARGS=\"\"" in text
    assert "dropbear_rsa_host_key" in text
    assert "dropbear_ecdsa_host_key" in text
    assert "printf 'DROPBEAR_ARGS=\"%s\"\\n' \"$DROPBEAR_KEY_ARGS\"" in text
    assert "cat > \"$_dropbear_init.anvil-new\" << INITEOF" in text
    assert "test -r /etc/default/dropbear && . /etc/default/dropbear" in text
    assert ": \\${DROPBEAR_ARGS:=\"$DROPBEAR_KEY_ARGS\"}" in text
    assert "--exec /usr/sbin/dropbear -- \\$DROPBEAR_ARGS" in text
    assert "auto-generation" in text


def test_toniforge_helpers_are_exposed_on_ssh_path():
    text = INSTALLER.read_text()

    assert "PATH=/usr/data/anvil/bin:/usr/prog/bin:\\$PATH" in text
    assert "export PATH" in text
