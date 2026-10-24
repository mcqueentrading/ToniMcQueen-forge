"""Bound the vendor levelboard wake-up invoked after Klipper disconnects.

This retains the vendor operation, not a claim that a board reconnected.
Never called from the live motion reactor or a toolchange path.
"""
import logging
import math
import os
import signal
import subprocess
import threading

WAKEUP_COMMAND = ("/usr/prog/bin/wakeup_level",)
WAKEUP_CWD = "/usr/prog/bin"
WAKEUP_TIMEOUT = 10.0
TERMINATE_GRACE = 1.0


def _signal_group(pid, sig):
    try:
        os.killpg(pid, sig)
    except ProcessLookupError:
        pass


def _cleanup(process, grace):
    # Also remove descendants when the immediate child has already exited.
    _signal_group(process.pid, signal.SIGTERM)
    try:
        process.wait(timeout=grace)
    except subprocess.TimeoutExpired:
        pass
    _signal_group(process.pid, signal.SIGKILL)
    try:
        process.wait(timeout=grace)
    except subprocess.TimeoutExpired:
        logging.critical("Levelboard wake-up PID %d did not reap after SIGKILL",
                         process.pid)
        return False
    return True


def run_wakeup(reason, command=WAKEUP_COMMAND, cwd=WAKEUP_CWD,
               timeout=WAKEUP_TIMEOUT, grace=TERMINATE_GRACE):
    """Return diagnostics; do not swallow parent termination or claim ready.

    Own one child session, use no shell and inherit no Klipper serial FDs.
    SIGKILL of this parent cannot be handled: supervisor-side orphan recovery
    remains a separate requirement. Do not auto-kill unrelated processes.
    """
    if (not math.isfinite(timeout) or timeout <= 0 or
            not math.isfinite(grace) or grace <= 0):
        raise ValueError("wake-up timeout and grace must be finite and positive")
    if threading.current_thread() is not threading.main_thread():
        raise RuntimeError("post-disconnect wake-up must run on the main thread")
    previous = {sig: signal.getsignal(sig) for sig in (signal.SIGTERM, signal.SIGINT)}
    process = None
    result = {"status": "not_started", "returncode": None,
              "cleanup_complete": True, "reason": reason}

    def terminate_parent(sig, frame):
        # s6 terminates the service PID, not automatically its new child session.
        signal.signal(signal.SIGTERM, signal.SIG_IGN)
        signal.signal(signal.SIGINT, signal.SIG_IGN)
        if process is not None:
            _cleanup(process, grace)
        handler = previous[sig]
        signal.signal(sig, handler)
        if handler == signal.SIG_DFL:
            os.kill(os.getpid(), sig)
        elif callable(handler):
            handler(sig, frame)

    try:
        for sig in previous:
            signal.signal(sig, terminate_parent)
        try:
            process = subprocess.Popen(tuple(command), cwd=cwd,
                                       stdin=subprocess.DEVNULL,
                                       close_fds=True, start_new_session=True)
        except OSError as exc:
            result["status"] = "launch_failed"
            logging.error("Levelboard wake-up could not start after %s: %s",
                          reason, exc)
            return result
        logging.info("Levelboard wake-up PID %d after %s (timeout %.1fs)",
                     process.pid, reason, timeout)
        try:
            result["returncode"] = process.wait(timeout=timeout)
            result["status"] = "ok" if process.returncode == 0 else "failed"
        except subprocess.TimeoutExpired:
            result["status"] = "timeout"
            logging.error("Levelboard wake-up timed out after %.1fs (%s)",
                          timeout, reason)
        return result
    finally:
        if process is not None:
            result["cleanup_complete"] = _cleanup(process, grace)
            result["returncode"] = process.returncode
        for sig, handler in previous.items():
            signal.signal(sig, handler)
        logging.info("Levelboard wake-up result: %s", result)
