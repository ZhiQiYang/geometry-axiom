"""Real bridge unittest oracle. Assertion failures, bridge deaths, infrastructure and skips stay distinct.

Every entry of `failures` carries a structured `kind`: "assertion" (a test assertion failed) or "bridge_closed" (the
bridge process died under the test, with its exit status in `bridge_returncode`; see tests/_bridge.py::BridgeClosed).
tests/mutation_bridge.py::classify turns the first into `killed` and a death with no assertion failure into `crashed`."""
import argparse
import json
import os
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def failure_label(exc):
    """Structured kind of one assertion-class failure, read from the exception object (never from its text).

    tests/_bridge.py::BridgeClosed marks "the bridge process died under the test" (crash, abort, OOM kill) with a
    class-level `bridge_closed` flag and its exit status in `returncode`.  Everything else that unittest files under
    `failures` is an assertion about the bridge's answers."""
    if getattr(exc, "bridge_closed", False) is True:
        code = getattr(exc, "returncode", None)
        return {"kind": "bridge_closed", "bridge_returncode": code if type(code) is int else None}
    return {"kind": "assertion"}


class ObservedResult(unittest.TextTestResult):
    def startTest(self, test):
        self.started.append(test.id())
        super().startTest(test)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.started = []
        self.failure_labels = []     # parallel to self.failures, one failure_label() per entry

    def _label_new_failures(self, before, err):
        for _ in range(len(self.failures) - before):
            self.failure_labels.append(failure_label(err[1]))

    def addFailure(self, test, err):
        before = len(self.failures)
        super().addFailure(test, err)
        self._label_new_failures(before, err)

    def addSubTest(self, test, subtest, err):
        before = len(self.failures)
        super().addSubTest(test, subtest, err)
        if err is not None:
            self._label_new_failures(before, err)


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
    suite = unittest.defaultTestLoader.loadTestsFromNames(args.methods)
    result = unittest.TextTestRunner(stream=sys.stdout, verbosity=2, resultclass=ObservedResult).run(suite)
    if len(result.failure_labels) != len(result.failures):
        raise RuntimeError("every failure must carry a structured kind; the result would be ambiguous")
    payload = {
        "schema": "geometry-bridge-mutation-tests/1", "requested": args.methods,
        "started": result.started, "total": result.testsRun,
        "failures": [{"test": test.id(), "detail": detail[-3000:], **label}
                     for (test, detail), label in zip(result.failures, result.failure_labels)],
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
