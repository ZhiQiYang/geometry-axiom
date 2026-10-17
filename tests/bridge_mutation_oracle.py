"""Real bridge unittest oracle. Assertion failures, bridge deaths, infrastructure and skips stay distinct.

Every entry of `failures` carries a structured `kind`: "assertion" (a test assertion failed) or "bridge_closed" (the
bridge process died under the test, with its exit status in `bridge_returncode` when one was observed; see
tests/_bridge.py::BridgeClosed and ChildWatch below).  tests/mutation_bridge.py::classify turns a run whose
failures are all assertions into `killed`; a death is never `killed`: one run with a death is `blocked`, and only
mutation_bridge.judge_trials() makes `crashed` out of RUN_RETRIES consecutive access-violation deaths in the same
tests."""
import argparse
import functools
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

# Text of tests/_bridge.py's BridgeClosed and of the hand-written copies of its line protocol
# (e.g. tests/integration/assembly_ownership_probe.py).  Text can only make a failure LESS trusted: a failure whose
# message says the bridge closed is never an assertion, but without an exit status it is not a proven death either.
BRIDGE_CLOSED_TEXT = "bridge closed:"


def exception_chain(exc):
    """`exc` and every exception it was raised from or while handling (__cause__ and __context__, even when the
    context is suppressed with `raise ... from None`), each once, outermost first."""
    seen, out, todo = set(), [], [exc]
    while todo:
        item = todo.pop(0)
        if item is None or id(item) in seen:
            continue
        seen.add(id(item))
        out.append(item)
        todo += [getattr(item, "__cause__", None), getattr(item, "__context__", None)]
    return out


def failure_label(exc, child_deaths=()):
    """Structured kind of one assertion-class failure.

    A failure is a death of the bridge ("bridge_closed") when any of these holds:
      - tests/_bridge.py::BridgeClosed (class-level `bridge_closed` flag, exit status in `returncode`) is anywhere in
        the exception chain: a test that catches it and calls self.fail(...) still failed because the bridge died;
      - a child process of the test died (`child_deaths`: exit statuses from ChildWatch, i.e. from the OS), which
        covers tests that run the bridge without tests/_bridge.py;
      - some message in the chain says the bridge closed (BRIDGE_CLOSED_TEXT).  That text alone carries no exit
        status, so `bridge_returncode` stays None and the failure can never count as a detection.
    `bridge_returncode` is the one exit status all the evidence agrees on; None when there is none or they disagree.
    Only a failure with no sign of a dead bridge is an "assertion" about the bridge's answers."""
    chain = exception_chain(exc)
    closed = [e for e in chain if getattr(e, "bridge_closed", False) is True]
    deaths = [code for code in child_deaths if type(code) is int]
    says_closed = any(BRIDGE_CLOSED_TEXT in str(e) for e in chain)
    if not (closed or deaths or says_closed):
        return {"kind": "assertion"}
    codes = [e.returncode for e in closed if type(getattr(e, "returncode", None)) is int] + deaths
    seen_by = (["BridgeClosed"] if closed else []) + (["child exit status"] if deaths else []) + (
        ["message text"] if says_closed and not closed else [])
    return {"kind": "bridge_closed", "bridge_returncode": codes[0] if len(set(codes)) == 1 else None,
            "death_seen_by": seen_by}


def _program(argv):
    """Normalised path of the program a Popen argument list starts, or None."""
    prog = argv[0] if isinstance(argv, (list, tuple)) and argv else argv
    try:
        return os.path.normcase(os.path.realpath(os.fspath(prog)))
    except (TypeError, ValueError, OSError):
        return None


def is_crash_status(code):
    """An exit status no orderly exit produces: killed by a signal (POSIX, negative) or a Windows NTSTATUS error
    such as 0xC0000005 (either signedness)."""
    return type(code) is int and (code < 0 or (code & 0xFFFFFFFF) >= 0xC0000000)


class ChildWatch:
    """Every child process this oracle process starts (subprocess.Popen, and so subprocess.run), so a failing test can
    be checked against what the OS says happened to its children, whatever helper the test used to talk to the bridge.

    A child counts as dead under a test when it was still alive (or not yet reaped) when the test started and, by the
    time the failure is reported, it ended with
      - any status other than 0 if it runs the oracle's bridge binary (web_bridge.c's only orderly end is 0), or
      - a crash status (is_crash_status) whatever program it runs.
    A child still running when a failure is reported gets up to GRACE seconds (shared by the children, once per test,
    so many failing subtests do not wait again) to finish dying: its stdout can close before the OS reports how it
    ended.  Children of children (e.g. a bridge started by a server the test started) are not seen."""
    GRACE = 1.0

    def __init__(self, bridge=None):
        self.bridge = _program([bridge]) if bridge is not None else None
        self.children = []
        self.settled = set()
        self.graced = set()          # children of the current test that already had their GRACE

    def install(self):
        watch = self

        class WatchedPopen(subprocess.Popen):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                watch.children.append(self)
        subprocess.Popen = WatchedPopen
        return self

    def mark(self):
        """At the start of a test: children that already ended belong to earlier tests."""
        self.settled = {id(child) for child in self.children if child.poll() is not None}
        self.graced = set()

    def is_death(self, child, code):
        if self.bridge is not None and _program(child.args) == self.bridge and code != 0:
            return True
        return is_crash_status(code)

    def deaths(self):
        """Exit statuses of the children that died since mark()."""
        deadline, codes = time.monotonic() + self.GRACE, []
        for child in self.children:
            if id(child) in self.settled:
                continue
            code = child.poll()
            if code is None:
                if id(child) in self.graced:
                    continue
                try:
                    code = child.wait(timeout=max(0.0, deadline - time.monotonic()))
                except subprocess.TimeoutExpired:
                    self.graced.add(id(child))
                    continue
            if self.is_death(child, code):
                codes.append(code)
        return codes


class ObservedResult(unittest.TextTestResult):
    def startTest(self, test):
        self.started.append(test.id())
        if self.watch is not None:
            self.watch.mark()
        super().startTest(test)

    def __init__(self, *args, watch=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.started = []
        self.failure_labels = []     # parallel to self.failures, one failure_label() per entry
        self.watch = watch           # ChildWatch of this oracle process, or None (no child processes observed)

    def _label_new_failures(self, before, err):
        deaths = self.watch.deaths() if self.watch is not None and len(self.failures) > before else []
        for _ in range(len(self.failures) - before):
            self.failure_labels.append(failure_label(err[1], deaths))

    def addFailure(self, test, err):
        before = len(self.failures)
        super().addFailure(test, err)
        self._label_new_failures(before, err)

    def addSubTest(self, test, subtest, err):
        before = len(self.failures)
        super().addSubTest(test, subtest, err)
        if err is not None:
            self._label_new_failures(before, err)


def failure_rows(result):
    """The payload's `failures`: every unittest failure with its structured kind.

    Refuses (RuntimeError, so no result line is printed and the run is blocked) when a failure has no label: zipping a
    shorter label list would silently drop failures from the report."""
    if len(result.failure_labels) != len(result.failures):
        raise RuntimeError("every failure must carry a structured kind; the result would be ambiguous")
    return [{"test": test.id(), "detail": detail[-3000:], **label}
            for (test, detail), label in zip(result.failures, result.failure_labels)]


def main(argv=None):
    if sys.flags.optimize:
        raise RuntimeError("optimized Python is not an assertion oracle")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("binary")
    parser.add_argument("methods", nargs="+")
    args = parser.parse_args(argv)
    if not Path(args.binary).is_file() or len(set(args.methods)) != len(args.methods):
        parser.error("one existing binary and distinct explicit test methods are required")
    os.environ["GEOMETRY_TEST_BRIDGE"] = args.binary
    os.environ["GEOMETRY_ENGINEERING_BRIDGE"] = args.binary
    watch = ChildWatch(args.binary).install()       # before the tests are imported, so they all see it
    suite = unittest.defaultTestLoader.loadTestsFromNames(args.methods)
    result = unittest.TextTestRunner(stream=sys.stdout, verbosity=2,
                                     resultclass=functools.partial(ObservedResult, watch=watch)).run(suite)
    payload = {
        "schema": "geometry-bridge-mutation-tests/1", "requested": args.methods,
        "started": result.started, "total": result.testsRun,
        "failures": failure_rows(result),
        "errors": [{"test": test.id(), "detail": detail[-3000:]} for test, detail in result.errors],
        "skipped": [{"test": test.id(), "reason": reason} for test, reason in result.skipped],
        "expected_failures": len(result.expectedFailures),
        "unexpected_successes": len(result.unexpectedSuccesses),
    }
    complete = result.started == args.methods and result.testsRun == len(args.methods)
    code = (2 if not complete or result.errors or result.skipped or result.expectedFailures or result.unexpectedSuccesses
            else 1 if result.failures else 0)
    print("GEOMETRY_BRIDGE_MUTATION_RESULT " + json.dumps(payload, ensure_ascii=False), flush=True)
    return code


if __name__ == "__main__":
    raise SystemExit(main())
