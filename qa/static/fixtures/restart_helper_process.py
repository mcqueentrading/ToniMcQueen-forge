"""Local subprocess fixture only. No printer paths or network operations."""
import importlib.util
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time

mode = sys.argv[1]
if mode == "driver":
    spec = importlib.util.spec_from_file_location("restart_under_test", sys.argv[2])
    helper = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(helper)
    result = helper.run_wakeup("restart", command=(sys.executable, __file__, sys.argv[3], sys.argv[4]),
                               cwd=str(Path(__file__).parent), timeout=float(sys.argv[5]), grace=.15)
    print(json.dumps(result))
else:
    pidfile = Path(sys.argv[2])
    if mode == "child":
        signal.signal(signal.SIGTERM, signal.SIG_IGN)
        while True:
            time.sleep(.05)
    pidfile.write_text(str(os.getpid()))
    if mode == "fds":
        forbidden = sys.argv[3]
        for descriptor in Path("/proc/self/fd").iterdir():
            try:
                if str(descriptor.resolve()) == forbidden:
                    sys.exit(9)
            except FileNotFoundError:
                pass
        sys.exit(0)
    if mode == "fail":
        sys.exit(7)
    if mode == "success":
        sys.exit(0)
    if mode == "spawn":
        child = subprocess.Popen([sys.executable, __file__, "child", str(pidfile)])
        Path(str(pidfile)+".child").write_text(str(child.pid))
    signal.signal(signal.SIGTERM, signal.SIG_IGN)
    while True:
        time.sleep(.05)
