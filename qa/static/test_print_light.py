"""Static checks for print lighting and snapshot capture."""

import configparser

import pytest

from lib.paths import ROOT


pytestmark = pytest.mark.static
CONFIG = ROOT / "pkgs" / "klipper-config" / "payload" / "config"


def test_print_light_macro_turns_on_chamber_led():
    config = configparser.RawConfigParser(
        strict=False, inline_comment_prefixes=(";", "#"))
    config.read(CONFIG / "ff-chamber.cfg")
    gcode = config.get("gcode_macro REFORGE_PRINT_LIGHT_ON", "gcode")

    assert "SET_LED LED=chamber_led WHITE=1.0 TRANSMIT=1" in gcode


def test_snapshot_start_enables_print_light():
    config = configparser.RawConfigParser(
        strict=False, inline_comment_prefixes=(";", "#"))
    config.read(CONFIG / "ff-timelapse-snapshot.cfg")
    gcode = config.get("gcode_macro REFORGE_SNAPSHOT_START", "gcode")

    assert "REFORGE_PRINT_LIGHT_ON" in gcode
