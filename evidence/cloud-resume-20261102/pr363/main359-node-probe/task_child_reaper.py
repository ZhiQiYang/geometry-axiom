"""Task-local orphan reaping, with no signals or changes to test verdicts.

The Popen-owned main child is never passed to waitpid here. Only other direct
children adopted by this Linux subreaper are polled with WNOHANG. Running
children are observed, never killed. This supplies init-style zombie reaping
when a container's PID 1 is a non-reaping tail process.

Caller contract: this wrapper owns exactly one Popen main child. It must not
start another Popen child concurrently with tick/wait_main/drain_naturally.
"""
import ctypes
import datetime
import json
import os
from pathlib import Path
import time

def utc():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()

class ChildReaper:
    def __init__(self, log, observe_live=False):
        self.log = Path(log)
        self.log.parent.mkdir(parents=True, exist_ok=True)
        self.pid = os.getpid()
        self.observe_live = observe_live
        if self.children():
            raise RuntimeError('ChildReaper requires a wrapper with no existing children before its sole Popen main child is started')
        libc = ctypes.CDLL(None, use_errno=True)
        if libc.prctl(36, 1, 0, 0, 0) != 0:
            raise OSError(ctypes.get_errno(), 'PR_SET_CHILD_SUBREAPER')
        current = ctypes.c_int(0)
        if libc.prctl(37, ctypes.byref(current), 0, 0, 0) != 0 or current.value != 1:
            raise RuntimeError('PR_GET_CHILD_SUBREAPER did not return 1')
        self.events = []
        self.seen_alive = set()
        self.record({'event': 'enabled', 'pid': self.pid, 'subreaper': current.value,
                     'policy': 'Never signal children; waitpid WNOHANG only on adopted direct children excluding the Popen main child.'})

    def record(self, event):
        event['utc'] = utc()
        self.events.append(event)
        with self.log.open('a') as stream:
            stream.write(json.dumps(event, ensure_ascii=False) + '\n')

    def children(self):
        direct = Path(f'/proc/self/task/{self.pid}/children')
        if direct.is_file():
            return [int(v) for v in direct.read_text().split()]
        # CONFIG_CHECKPOINT_RESTORE is absent in this kernel. PPID from stat
        # supplies the same direct-child scope without touching any process.
        found = []
        for entry in Path('/proc').iterdir():
            if not entry.name.isdigit():
                continue
            try:
                fields = (entry / 'stat').read_text().rsplit(')', 1)[1].split()
                if int(fields[1]) == self.pid:
                    found.append(int(entry.name))
            except (OSError, ValueError, IndexError):
                continue
        return sorted(found)

    def tick(self, main_pid):
        while True:
            try:
                # WNOWAIT only peeks. If the main child is first, leave its
                # status untouched for Popen.poll(), then revisit other exits.
                exited = os.waitid(os.P_ALL, 0, os.WEXITED | os.WNOHANG | os.WNOWAIT)
            except ChildProcessError:
                break
            if exited is None or exited.si_pid == main_pid:
                break
            child = exited.si_pid
            try:
                waited, status = os.waitpid(child, os.WNOHANG)
            except ChildProcessError:
                continue
            if waited:
                self.record({'event': 'reaped-adopted-child', 'pid': child,
                             'observedState': 'terminated-exit-peek', 'waitStatus': status,
                             'exitCode': os.waitstatus_to_exitcode(status)})
        living = []
        if self.observe_live:
            for child in self.children():
                if child == main_pid:
                    continue
                try:
                    state = Path(f'/proc/{child}/stat').read_text().rsplit(')', 1)[1].split()[0]
                except (OSError, IndexError):
                    continue
                living.append(child)
                if state != 'Z' and child not in self.seen_alive:
                    self.seen_alive.add(child)
                    self.record({'event': 'observed-live-adopted-child', 'pid': child,
                                 'observedState': state, 'action': 'none'})
        return living

    def wait_main(self, process, deadline):
        """Return the Popen exit code; return None at deadline without sending signals."""
        while True:
            self.tick(process.pid)
            code = process.poll()
            if code is not None:
                self.tick(process.pid)
                self.record({'event': 'main-exit-observed-by-Popen', 'pid': process.pid, 'exitCode': code})
                return code
            if time.monotonic() >= deadline:
                self.record({'event': 'deadline', 'pid': process.pid, 'action': 'none'})
                return None
            time.sleep(0.02)

    def drain_naturally(self, main_pid, deadline):
        """Observe surviving adopted children until natural exit; never kill them."""
        while True:
            self.tick(main_pid)
            # Reaping an adopted parent may expose newly adopted descendants.
            # A second /proc children read is required before claiming empty.
            pending = [pid for pid in self.children() if pid != main_pid]
            if not pending or time.monotonic() >= deadline:
                self.record({'event': 'drain-finished', 'remainingAdoptedChildren': pending, 'action': 'none'})
                return pending
            time.sleep(0.02)
