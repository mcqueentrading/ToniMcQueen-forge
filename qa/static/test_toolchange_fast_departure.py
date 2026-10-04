"""Static safety checks for the Creator 5 toolchange departure speed.

The fork intentionally borrows only the safe part of the faster klipper-c5
toolchanger: controlled latch/pullback first, then faster travel after sensor
verification. This test protects that ordering from becoming a blind feed bump.
"""
import re

import pytest

from lib.paths import ROOT

pytestmark = pytest.mark.static

TOOLCHANGE = (
    ROOT / "pkgs" / "klipper" / "payload" / "klipper" / "klippy"
    / "extras" / "ff_toolchange.py")
CONFIG = ROOT / "pkgs" / "klipper-config" / "payload" / "config" / "ff-toolchange.cfg"


def test_fast_grab_departure_is_after_sensor_verification():
    source = TOOLCHANGE.read_text(encoding="utf-8")
    assert "self.grab_departure_feed" in source
    verify = source.index("pre_departure_ok = self._poll_until")
    departure = source.index("self.grab_departure_feed", verify)
    assert verify < departure


def test_shipped_config_opts_into_controlled_fast_departure():
    config = CONFIG.read_text(encoding="utf-8")
    assert re.search(r"^grab_retreat_feed:\s*1500\s*$", config, re.MULTILINE)
    assert re.search(r"^grab_departure_feed:\s*4800\s*$", config, re.MULTILINE)
