"""Real bridge unittest oracle. Assertion failures, infrastructure and skips stay distinct."""
import argparse
import json
import os
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


class ObservedResult(unittest.TextTestResult):
    def startTest(self, test):
        self.started.append(test.id())
        super().startTest(test)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.started = []


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
    payload = {
        "schema": "geometry-bridge-mutation-tests/1", "requested": args.methods,
        "started": result.started, "total": result.testsRun,
        "failures": [{"test": test.id(), "detail": detail[-3000:]} for test, detail in result.failures],
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
