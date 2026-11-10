#!/usr/bin/env python3
"""Read-only sidecar for GEO-300 H7 on a checked-out geometry-axiom tree.

Run from the checkout root: python3 /path/to/r348_h7_trace.py
It runs the *unchanged* original tests 7 and 8 with observational wrappers.
No timeouts, assertions, expected counts, or product files are modified.
"""
import importlib
import json
import os
import pathlib
import subprocess
import sys
import time
import unittest
from unittest import mock

TESTS = (
    "test_real_placed_512_sequential_replay_and_safe_513_history",
    "test_real_placed_64_and_512_load_dump_and_canonical_replay",
)


def emit(kind, **values):
    print(json.dumps({"at": time.time(), "kind": kind, **values}, ensure_ascii=False),
          file=sys.stderr, flush=True)


def peak_kib(pid):
    try:
        for line in pathlib.Path(f"/proc/{pid}/status").read_text().splitlines():
            if line.startswith("VmHWM:"):
                return int(line.split()[1])
    except (OSError, ValueError, IndexError):
        pass
    return None


class StreamTrace:
    def __init__(self, stream, proc, state):
        self._stream, self._proc, self._state = stream, proc, state

    def readline(self, *args, **kwargs):
        reply = self._stream.readline(*args, **kwargs)
        started = self._state.get("start")
        emit("command_reply", name=self._state.get("name"),
             elapsed_s=round(time.monotonic() - started, 6) if started else None,
             bytes=len(reply), empty=not bool(reply),
             child_pid=self._proc.pid, child_peak_kib=peak_kib(self._proc.pid))
        return reply

    def __getattr__(self, name):
        return getattr(self._stream, name)


class ProcessTrace:
    def __init__(self, proc, state):
        self._proc = proc
        self.stdout = StreamTrace(proc.stdout, proc, state)
        self.stdin = proc.stdin
        self.stderr = proc.stderr

    def __getattr__(self, name):
        return getattr(self._proc, name)


def main():
    root = pathlib.Path.cwd().resolve()
    if not (root / "tests/test_geo261_timber_capacity_host.py").is_file():
        raise SystemExit("Run this file with cwd at the geometry-axiom checkout root")
    sys.path.insert(0, str(root))
    suite_mod = importlib.import_module("tests.test_geo261_timber_capacity_host")
    cls = suite_mod.TimberCapacityHost
    original_dialogue = suite_mod.run_placed_dialogue
    original_popen = subprocess.Popen
    original_batch = cls.placed_batch
    original_history = cls.placed_history_batch

    def instrument_dialogue(commands, *, bridge, timeout=600):
        state = {}
        wrapped_commands = []
        for name, item in commands:
            def timed_item(rows, name=name, item=item):
                state["name"] = name
                state["start"] = time.monotonic()
                return item(rows) if callable(item) else item
            wrapped_commands.append((name, timed_item))

        def observed_popen(*args, **kwargs):
            p = original_popen(*args, **kwargs)
            emit("child_started", pid=p.pid)
            return ProcessTrace(p, state)

        started = time.monotonic()
        emit("dialogue_begin", commands=len(commands), timeout_s=timeout)
        try:
            with mock.patch.object(subprocess, "Popen", observed_popen):
                return original_dialogue(wrapped_commands, bridge=bridge, timeout=timeout)
        except BaseException as e:
            completed = getattr(e, "completed", None)
            emit("dialogue_error", type=type(e).__name__, detail=str(e)[:500],
                 returncode=getattr(completed, "returncode", None),
                 replies=getattr(completed, "reply_names", None),
                 stderr_tail=(getattr(completed, "stderr", b"") or b"")[-1000:].decode("utf-8", "replace"))
            raise
        finally:
            emit("dialogue_end", elapsed_s=round(time.monotonic() - started, 6))

    def instrument_batch(self, commands, label):
        started = time.monotonic()
        emit("batch_begin", label=label, commands=len(commands))
        try:
            return original_batch(self, commands, label)
        finally:
            emit("batch_end", label=label, elapsed_s=round(time.monotonic()-started, 6))

    def instrument_history(self, commands, label):
        started = time.monotonic()
        emit("history_begin", label=label, commands=len(commands))
        try:
            return original_history(self, commands, label)
        finally:
            emit("history_end", label=label, elapsed_s=round(time.monotonic()-started, 6))

    try:
        import subprocess as sp
        head = sp.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=True).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        head = "unknown"
    emit("source", head=head, root=str(root), tests=list(TESTS))
    test_suite = unittest.TestSuite([cls(name) for name in TESTS])
    with mock.patch.object(suite_mod, "run_placed_dialogue", instrument_dialogue), \
         mock.patch.object(cls, "placed_batch", instrument_batch), \
         mock.patch.object(cls, "placed_history_batch", instrument_history):
        result = unittest.TextTestRunner(verbosity=2).run(test_suite)
    emit("result", tests_run=result.testsRun, failures=len(result.failures), errors=len(result.errors),
         success=result.wasSuccessful())
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    sys.exit(main())
