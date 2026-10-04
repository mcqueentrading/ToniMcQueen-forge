from lib.paths import ROOT


CONFIG = ROOT / "pkgs" / "klipper-config" / "payload" / "config"
TIMELAPSE_BUILD = ROOT / "pkgs" / "timelapse" / "build.sh"


def test_snapshot_macro_file_is_included_and_shipped():
    base = (CONFIG / "printer.base.cfg").read_text()
    macro = CONFIG / "ff-timelapse-snapshot.cfg"

    assert macro.exists()
    assert "[include ff-timelapse-snapshot.cfg]" in base
    assert "REFORGE_SNAPSHOT_START" in macro.read_text()


def test_timelapse_patch_guards_imports_and_cleans_frames():
    text = TIMELAPSE_BUILD.read_text()

    assert "missing_imports = []" in text
    assert 'if "import os" not in text:' in text
    assert 'if "import logging" not in text:' in text
    assert 'text = "\\n".join(missing_imports) + "\\n" + text' in text
    assert "os.remove(frame)" in text
    assert "saveFramesZip body changed upstream" in text
