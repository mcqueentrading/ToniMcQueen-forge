"""Guard the optional pullback feed without changing historical defaults."""
import ast
import configparser
import importlib.util
from contextlib import nullcontext
from types import SimpleNamespace
import pytest
from lib.paths import ROOT

pytestmark = pytest.mark.static
SOURCE = ROOT / "pkgs/klipper/payload/klipper/klippy/extras/ff_toolchange.py"


def test_pullback_configuration_keeps_historical_default_and_positive_bound():
    tree = ast.parse(SOURCE.read_text())
    calls = [n for n in ast.walk(tree) if isinstance(n, ast.Call)
             and isinstance(n.func, ast.Attribute) and n.func.attr == "getint"
             and n.args and isinstance(n.args[0], ast.Constant)
             and n.args[0].value == "grab_pullback_feed"]
    assert len(calls) == 1
    call = calls[0]
    assert isinstance(call.args[1], ast.Name)
    assert call.args[1].id == "PULLBACK_FEED"
    assert any(k.arg == "minval" and k.value.value == 1 for k in call.keywords)
    defaults = [n for n in tree.body if isinstance(n, ast.Assign)
                and any(isinstance(t, ast.Name) and t.id == "PULLBACK_FEED" for t in n.targets)]
    assert defaults[0].value.value == 4800


def test_feed_used_after_lock_and_before_departure_verification():
    source = SOURCE.read_text()
    grab = source.split("    def _grab(self, tool):", 1)[1].split("    def _release(self, tool):", 1)[0]
    assert grab.index("self._run(self.grab_macro)") < grab.index("self.grab_pullback_feed")
    assert grab.index("self.grab_pullback_feed") < grab.index("self._run(self.grab2_macro)")
    assert grab.index("self._run(self.grab2_macro)") < grab.index("pre_departure_ok =")
    assert grab.index("pre_departure_ok =") < grab.index("self.grab_departure_feed")


def test_status_exposes_effective_pullback_feed():
    assert 'lines.append("  grab_pullback_feed %d" % self.grab_pullback_feed)' in SOURCE.read_text()


def test_optional_fast_profile_matches_tested_values_without_global_enable():
    profile = ROOT / "pkgs/klipper-config/payload/config/examples/ff-toolchange-fast.cfg"
    config = configparser.RawConfigParser()
    config.read(profile)
    assert dict(config["ff_toolchange"]) == {
        "fast_feed":"36000", "slow_feed":"5400", "release_slow_feed":"5400",
        "grab_pullback_feed":"9600", "grab_departure_feed":"36000",
        "release_retreat_feed":"36000", "accel_move":"30000"}
    base = (ROOT / "pkgs/klipper-config/payload/config/printer.base.cfg").read_text()
    assert "ff-toolchange-fast" not in base


@pytest.fixture
def grab_harness():
    spec = importlib.util.spec_from_file_location("configurable_pullback_test", SOURCE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    events = []
    states = iter([True,True,False])
    tc = SimpleNamespace(
        _dock=lambda t:(297.,100.), _wait_moves=lambda:None,
        _snapshot_motion_state=nullcontext, _set_tool_frame=lambda t:None,
        _run=events.append, _poll_until=lambda fn,deadline:next(states),
        _in_location=lambda t:True, _grab_sensor=lambda:True,
        accel_move=30000, x_safe=250., x_approach=280., fast_feed=36000,
        slow_feed=5400, grab_macro="MOTOR_GRAB", grab2_macro="MOTOR_GRAB2",
        grab_pullback=20., grab_pullback_feed=9600, grab_departure_feed=36000)
    return module,tc,events


def test_failed_predeparture_sensor_never_reaches_fast_departure(grab_harness):
    module,tc,events = grab_harness
    with pytest.raises(module.FFToolchangeError,match="before departure"):
        module.FFToolchange._grab(tc,0)
    assert "G1 X277.000 F9600" in events
    assert "G1 X250.000 F36000" in events  # initial clear approach only
    assert events.count("G1 X250.000 F36000")==1
    assert not any(e.startswith("ACTIVATE_EXTRUDER") for e in events)


def test_missing_docked_tool_prevents_all_pickup_motion(grab_harness):
    module,tc,events = grab_harness
    tc._poll_until=lambda fn,deadline:False
    with pytest.raises(module.FFToolchangeError,match="not in its dock"):
        module.FFToolchange._grab(tc,0)
    assert events==[]
