"""Parking preserves status ownership during standalone and nested parks."""

import importlib.util
from types import SimpleNamespace

import pytest

from lib.paths import ROOT


pytestmark = pytest.mark.static
MODULE = (ROOT / "pkgs" / "klipper" / "payload" / "klipper" /
          "klippy" / "extras" / "ff_toolchange.py")


class CommandError(Exception):
    pass


@pytest.fixture
def parking(monkeypatch):
    spec = importlib.util.spec_from_file_location("anvil_ff_toolchange", MODULE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    tc = module.FFToolchange.__new__(module.FFToolchange)
    tc.changing = False
    tc.restore_axis = ""
    tc.release_macro = "MOTOR_RELEASE"
    tc.dock_sensors = ["dock%d" % i for i in range(module.EXTRUDER_COUNT)]
    tc.grab_sensors = ["grab%d" % i for i in range(module.EXTRUDER_COUNT)]
    tc.printer = SimpleNamespace(lookup_object=lambda name, default=None: None)
    sensors = {name: i != 0 for i, name in enumerate(tc.dock_sensors)}
    sensors.update({name: i == 0 for i, name in enumerate(tc.grab_sensors)})
    monkeypatch.setattr(tc, "_sensor", lambda name, eventtime=None: sensors[name])
    monkeypatch.setattr(tc, "_wait_moves", lambda: None)
    monkeypatch.setattr(tc, "_station_z", lambda: None)
    tc.tools = []
    tc.armed_tool = -1
    tc.armed_switch = False
    tc.armed_motion = False
    tc.job_z = 0.0
    tc.gcode_transform = SimpleNamespace(tool=0)
    view = module._ToolchangerView(tc)
    gcmd = SimpleNamespace(get=lambda name, default=None: default,
                           respond_info=lambda message: None,
                           error=CommandError)
    return module, tc, view, sensors, gcmd


@pytest.mark.parametrize("incoming", [False, True], ids=["standalone", "nested"])
def test_park_reports_changing_and_preserves_callers_state(parking, monkeypatch,
                                                          incoming):
    _module, tc, view, sensors, gcmd = parking
    tc.changing = incoming
    stages = []

    def ensure_homed(axes):
        assert axes == "xy"
        assert tc.changing is True
        assert view.get_status(0)["status"] == "changing"
        stages.append("home")

    def release(tool):
        assert tool == 0
        assert tc.changing is True
        sensors["dock0"] = True
        raw = tc.get_status(0)
        compat = view.get_status(0)
        assert raw["state_ok"] is False
        assert "sensor state is impossible" in raw["state_reason"]
        assert compat["status"] == "changing"
        sensors["grab0"] = False
        stages.append("release")

    monkeypatch.setattr(tc, "_ensure_homed", ensure_homed)
    monkeypatch.setattr(tc, "_release", release)
    tc.cmd_TOOLCHANGE_PARK(gcmd)

    assert stages == ["home", "release"]
    assert tc.changing is incoming
    assert view.get_status(0)["status"] == ("changing" if incoming else "ready")


@pytest.mark.parametrize("incoming", [False, True], ids=["standalone", "nested"])
def test_park_restores_callers_state_on_exception(parking, monkeypatch, incoming):
    module, tc, view, sensors, gcmd = parking
    tc.changing = incoming

    def ensure_homed(axes):
        assert tc.changing is True

    def release(tool):
        sensors["dock0"] = True
        raise module.FFToolchangeError("injected parking failure")

    monkeypatch.setattr(tc, "_ensure_homed", ensure_homed)
    monkeypatch.setattr(tc, "_release", release)
    with pytest.raises(CommandError, match="injected parking failure"):
        tc.cmd_TOOLCHANGE_PARK(gcmd)

    assert tc.changing is incoming
    assert view.get_status(0)["status"] == ("changing" if incoming else "error")
