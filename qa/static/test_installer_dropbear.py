from lib.paths import ROOT


INSTALLER = ROOT / "installer" / "runFirmwareExe.sh"


def test_dropbear_host_key_patch_is_idempotent_and_conditional():
    text = INSTALLER.read_text()

    assert "DROPBEAR_KEY_ARGS=\"\"" in text
    assert "dropbear_rsa_host_key" in text
    assert "dropbear_ecdsa_host_key" in text
    assert "printf 'DROPBEAR_ARGS=\"%s\"\\n' \"$DROPBEAR_KEY_ARGS\"" in text
    assert "-e \"s#[[:space:]]-r[[:space:]]$DROPBEAR_KEY_DIR/dropbear_rsa_host_key##g\"" in text
    assert "-e \"s#[[:space:]]-r[[:space:]]$DROPBEAR_KEY_DIR/dropbear_ecdsa_host_key##g\"" in text
