from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
PROFILES = ROOT / "local" / "creator5pro-orca-imagemap-profiles"
CONFIG = ROOT / "pkgs" / "klipper-config" / "payload" / "config" / "printer.base.cfg"


def test_klipper_arc_support_is_declared():
    text = CONFIG.read_text()
    assert "[gcode_arcs]" in text
    assert "resolution: 1.0" in text


def test_safe_process_profiles_keep_arc_fitting_off():
    for name in (
        "0.08mm Reforge ImageMap FullColour @C5P.json",
        "0.20mm Reforge Quality Snapshot @C5P.json",
    ):
        text = (PROFILES / name).read_text()
        assert '"enable_arc_fitting": "0"' in text


def test_arc_test_profile_is_explicitly_named_and_enabled():
    text = (PROFILES / "0.20mm Reforge Quality Snapshot ARC TEST @C5P.json").read_text()
    assert "ARC TEST" in text
    assert '"inherits": "0.20mm Reforge Quality Snapshot @C5P"' in text
    assert '"enable_arc_fitting": "1"' in text
