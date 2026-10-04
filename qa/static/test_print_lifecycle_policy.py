from lib.paths import ROOT


CONFIG = ROOT / "pkgs" / "klipper-config" / "payload" / "config"
PRINT_MACROS = CONFIG / "ff-print-macros.cfg"


def _section(text, header):
    start = text.index(header)
    next_header = text.find("\n[gcode_macro ", start + len(header))
    if next_header == -1:
        return text[start:]
    return text[start:next_header]


def test_cancel_print_does_not_run_end_print_twice():
    text = PRINT_MACROS.read_text()
    cancel = _section(text, "[gcode_macro CANCEL_PRINT]")

    assert "BASE_CANCEL_PRINT" in cancel
    assert '{% if not printer["gcode_macro _FF_JOB"].ended %}' in cancel
    assert "END_PRINT" in cancel


def test_resume_rearms_motion_clog_sensor_explicitly():
    text = PRINT_MACROS.read_text()
    resume = _section(text, "[gcode_macro RESUME]")

    assert "FF_RUNOUT_ARM SWITCH=1 MOTION=1" in resume
    assert "BASE_RESUME" in resume
