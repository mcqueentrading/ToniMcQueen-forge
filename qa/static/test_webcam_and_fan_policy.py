"""Protect local Creator 5 camera and fan policy.

These are easy to accidentally "simplify" away during upstream merges:
Mainsail needs explicit enabled webcam entries, and FlashForge-style M106 P
values need to resolve to the real fan_generic names this fork ships.
"""
import configparser

import pytest

from lib.paths import ROOT

pytestmark = pytest.mark.static

MOONRAKER = ROOT / "pkgs" / "moonraker" / "payload" / "config" / "moonraker.conf"
CHAMBER = ROOT / "pkgs" / "klipper-config" / "payload" / "config" / "ff-chamber.cfg"


def test_two_enabled_webcam_entries_are_shipped():
    cp = configparser.RawConfigParser(strict=False)
    cp.read(MOONRAKER, encoding="utf-8")
    for section in ("webcam anvil", "webcam m1"):
        assert cp.has_section(section)
        assert cp.getboolean(section, "enabled")
        assert cp.get(section, "stream_url") == "/webcam/?action=stream"
        assert cp.get(section, "snapshot_url") == "/webcam/?action=snapshot"


def test_m106_flashforge_p_map_is_source_owned():
    text = CHAMBER.read_text(encoding="utf-8")
    assert "[gcode_macro FF_CHAMBER_AIR_POLICY]" in text
    assert "[gcode_macro M106]" in text
    assert "[gcode_macro M107]" in text
    assert "variable_cold_air_while_heating: 0" in text
    assert "variable_exhaust_while_heating: 0" in text
    assert "SET_FAN_SPEED FAN=fanM106" in text
    assert "SET_FAN_SPEED FAN=chamber_loop_fan" in text
    assert "SET_FAN_SPEED FAN=chamber_cool_fan" in text
    assert "SET_FAN_SPEED FAN=chamber_fan" in text
    assert "chamber_target > 0" in text
    assert "COLD=1" in text
    assert "EXHAUST=1" in text
