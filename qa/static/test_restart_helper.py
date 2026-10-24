"""Offline process-lifecycle regression tests; never touch the printer."""
import ast
import importlib.util
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import tarfile
import time
import threading
from types import SimpleNamespace

import pytest
from lib.paths import ROOT

pytestmark = pytest.mark.static
MODULE = ROOT / "pkgs/klipper/payload/klipper/klippy/ff_restart_helper.py"
PATCH = ROOT / "pkgs/klipper/payload/patches/bounded-levelboard-wakeup.patch"
FIXTURE = ROOT / "qa/static/fixtures/restart_helper_process.py"


@pytest.fixture
def helper():
    spec = importlib.util.spec_from_file_location("ff_restart_helper_test",MODULE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def alive(pid):
    try:
        # A terminated descendant may briefly await init reaping; it no longer owns FDs.
        text = Path("/proc/%d/stat" % pid).read_text()
        return text.rsplit(")",1)[1].split()[0] != "Z"
    except FileNotFoundError:
        return False


def wait_file(path, process):
    deadline = time.monotonic()+3
    while time.monotonic() < deadline:
        if path.exists():
            return int(path.read_text())
        assert process.poll() is None
        time.sleep(.01)
    raise AssertionError("fixture did not start")


@pytest.mark.parametrize("mode,expected,code",[("success","ok",0),("fail","failed",7)])
def test_exit_status_reported_and_signals_restored(helper,tmp_path,mode,expected,code):
    previous = {sig:signal.getsignal(sig) for sig in (signal.SIGTERM,signal.SIGINT)}
    result = helper.run_wakeup("restart",command=(sys.executable,str(FIXTURE),mode,str(tmp_path/"pid")),
                               cwd=str(tmp_path),timeout=2,grace=.15)
    assert result["status"] == expected and result["returncode"] == code
    assert result["cleanup_complete"] is True
    assert previous == {sig:signal.getsignal(sig) for sig in previous}


def test_missing_program_is_explicit(helper,tmp_path):
    result = helper.run_wakeup("restart",command=(str(tmp_path/"absent"),),cwd=str(tmp_path),timeout=.1,grace=.1)
    assert result["status"] == "launch_failed" and result["cleanup_complete"] is True


def test_does_not_inherit_parent_file_descriptors(helper,tmp_path):
    path = tmp_path/"pretend_serial_device"
    with path.open("w") as parent_fd:
        os.set_inheritable(parent_fd.fileno(),True)
        result = helper.run_wakeup("restart",command=(sys.executable,str(FIXTURE),"fds",str(tmp_path/"pid"),str(path)),
                                   cwd=str(tmp_path),timeout=2,grace=.15)
    assert result["status"]=="ok"


def test_background_thread_rejected_before_launch(helper):
    failures = []
    def run():
        try:
            helper.run_wakeup("restart")
        except RuntimeError as exc:
            failures.append(str(exc))
    worker = threading.Thread(target=run)
    worker.start()
    worker.join(1)
    assert not worker.is_alive()
    assert failures==["post-disconnect wake-up must run on the main thread"]


def test_unreapable_process_is_not_reported_as_clean(helper,monkeypatch):
    class FakeProcess:
        pid = 999999
        returncode = None
        def wait(self,timeout):
            raise subprocess.TimeoutExpired("fake",timeout)
    monkeypatch.setattr(helper.subprocess,"Popen",lambda *a,**k:FakeProcess())
    monkeypatch.setattr(helper,"_signal_group",lambda *a:None)
    result = helper.run_wakeup("restart",timeout=.1,grace=.1)
    assert result["status"]=="timeout" and result["cleanup_complete"] is False


@pytest.mark.parametrize("timeout,grace",[(0,1),(-1,1),(float("inf"),1),(float("nan"),1),(1,0),(1,-1)])
def test_invalid_bounds_rejected_without_launch(helper,timeout,grace):
    with pytest.raises(ValueError):
        helper.run_wakeup("restart",timeout=timeout,grace=grace)


@pytest.mark.parametrize("mode",["hang","spawn"])
def test_timeout_kills_and_reaps_owned_session(tmp_path,mode):
    pidfile = tmp_path/"pid"
    driver = subprocess.Popen([sys.executable,str(FIXTURE),"driver",str(MODULE),mode,str(pidfile),".7"],
                              stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    child = None
    try:
        pid = wait_file(pidfile,driver)
        if mode == "spawn":
            child = wait_file(Path(str(pidfile)+".child"),driver)
        output,error = driver.communicate(timeout=5)
        assert driver.returncode == 0,error
        result = json.loads(output)
        assert result["status"] == "timeout" and result["cleanup_complete"] is True
        assert not alive(pid)
        if child is not None:
            assert not alive(child)
    finally:
        if driver.poll() is None:
            driver.kill()
            driver.wait(timeout=2)
        if child is not None and alive(child):
            os.kill(child,signal.SIGKILL)


def test_parent_sigterm_cleans_owned_helper_before_exiting(tmp_path):
    pidfile = tmp_path/"pid"
    driver = subprocess.Popen([sys.executable,str(FIXTURE),"driver",str(MODULE),"spawn",str(pidfile),"20"],
                              stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    child = None
    try:
        pid = wait_file(pidfile,driver)
        child = wait_file(Path(str(pidfile)+".child"),driver)
        driver.terminate()
        driver.communicate(timeout=5)
        assert driver.returncode == -signal.SIGTERM
        assert not alive(pid) and not alive(child)
    finally:
        if driver.poll() is None:
            driver.kill()
            driver.wait(timeout=2)
        if child is not None and alive(child):
            os.kill(child,signal.SIGKILL)


def patched_source(tmp_path):
    version = "f51aab7a843a3852c808e28d694be8b59bbbc130"
    with tarfile.open(ROOT/"vendor"/("klipper-"+version+".tar.gz")) as archive:
        data = archive.extractfile("klipper-"+version+"/klippy/klippy.py").read()
    folder = tmp_path/"klippy"
    folder.mkdir()
    source = folder/"klippy.py"
    source.write_bytes(data)
    result = subprocess.run(["patch","--batch","--fuzz=0","-p1","-d",str(tmp_path),"-i",str(PATCH)],
                            capture_output=True,timeout=5)
    assert result.returncode == 0,result.stdout+result.stderr
    return source.read_text()


@pytest.mark.parametrize("reason",["restart","firmware_restart","error_exit","exit"])
@pytest.mark.parametrize("clean",[True,False])
def test_pinned_source_patch_preserves_lifecycle_events(tmp_path,monkeypatch,reason,clean):
    source = patched_source(tmp_path)
    assert 'os.system("cd /usr/prog/bin && ./wakeup_level")' not in source
    cls = next(n for n in ast.parse(source).body if isinstance(n,ast.ClassDef) and n.name=="Printer")
    method = next(n for n in cls.body if isinstance(n,ast.FunctionDef) and n.name=="run")
    events = []
    monkeypatch.setitem(sys.modules,"ff_restart_helper",SimpleNamespace(run_wakeup=lambda why: events.append(("helper",why)) or {"cleanup_complete":clean}))
    namespace = {"time":time,"logging":SimpleNamespace(info=lambda *a:None,exception=lambda *a:None)}
    exec(compile(ast.fix_missing_locations(ast.Module(body=[method],type_ignores=[])),"patched-run","exec"),namespace)
    printer = SimpleNamespace(run_result=reason,send_event=events.append,
                              reactor=SimpleNamespace(run=lambda:None,monotonic=lambda:0))
    assert namespace["run"](printer)==(reason if clean else "error_exit")
    assert events[-2:]==["klippy:disconnect",("helper",reason)]
    assert events.count("klippy:firmware_restart")==int(reason=="firmware_restart")


def test_build_recipe_stages_module_and_patches_before_compile():
    build = (ROOT/"pkgs/klipper/build.sh").read_text()
    assert build.index("bounded-levelboard-wakeup.patch") < build.index('pkg_build "$_top"')
    assert '"klipper/klippy/ff_restart_helper.py"' in build
    assert PATCH.is_relative_to(ROOT/"pkgs/klipper/payload")
