"""R374 named withdrawals against the real reader's focused test helpers.

Usage: python3 -B tests/diagnostics/r374_reader_mutations.py --out /tmp/r374-proof
Only disposable copies are changed. Receipts must be outside the repository;
errors, skips, missing anchors and timeouts never count as assertion kills.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile


SYNC = "geometry-guide/sync_axiom_reader.py"
HTML = "geometry-guide/公理層-閱讀器.html"
TEST = "tests/test_axiom_reader.py"
COPIES = (SYNC, HTML, TEST)
INPUTS = (*COPIES, "公理層.md", "geometry-guide/公理層-白話.md",
          "geometry-guide/axiom_matrix.py", "current_geometry.c", "tests/mutate.py")
METHODS = ("check_offline_source_serialization", "check_offline_source_inline",
           "check_offline_source_template_migration")
CASES = (
    ("R374_M01_DROP_PY_JSON_ESCAPE", SYNC, r'.replace("://", r":\/\/")',
     METHODS[0], "R374_PY_JSON_OFFLINE", [{"serializer": "PY_JSON"}]),
    ("R374_M02_DROP_INLINE_URL_BREAK", HTML, r".replace(/(https?):\/\//gi,'$1:<wbr>//')",
     METHODS[1], "R374_INLINE_OFFLINE",
     [{"inline": name} for name in ("markdown", "case", "code", "bold", "escaped HTML")]),
    ("R374_M03_DROP_JS_JSON_ESCAPE", HTML, r".replace(/:\/\//g,':\\/\\/')",
     METHODS[0], "R374_JS_JSON_OFFLINE", [{"serializer": "JS_JSON"}]),
    ("R374_M04_DROP_TEMPLATE_MIGRATION", SYNC,
     "    template = apply_offline_source_urls(template)\n",
     METHODS[2], "R374_TEMPLATE_MIGRATION", [None]),
)

# A real unittest result records exception objects, not matches in traceback
# source lines. Explicitly selected helpers do not change normal discovery.
CHILD = r'''
import importlib.util, json, pathlib, sys, unittest
root = pathlib.Path(sys.argv[1])
methods = sys.argv[2:]
spec = importlib.util.spec_from_file_location("r374_reader_test", root / "tests/test_axiom_reader.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
case = module.CanonicalReader
class Result(unittest.TextTestResult):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.events = []
    def record(self, test, error, kind, params=None):
        self.events.append({"test": test.id(), "kind": kind,
            "exceptionType": error[0].__name__, "exceptionModule": error[0].__module__,
            "message": str(error[1]), "params": params})
    def addFailure(self, test, error):
        self.record(test, error, "failure")
        super().addFailure(test, error)
    def addError(self, test, error):
        self.record(test, error, "error")
        super().addError(test, error)
    def addSubTest(self, test, subtest, error):
        if error is not None:
            self.record(test, error, "failure" if issubclass(error[0], test.failureException) else "error",
                        dict(subtest.params))
        super().addSubTest(test, subtest, error)
result = unittest.TextTestRunner(stream=sys.stderr, verbosity=2, resultclass=Result).run(
    unittest.TestSuite(case(method) for method in methods))
print(json.dumps({"selected": methods, "testsRun": result.testsRun,
    "formalDiscovery": unittest.defaultTestLoader.loadTestsFromTestCase(case).countTestCases(),
    "failures": len(result.failures), "errors": len(result.errors),
    "skips": len(result.skipped), "expectedFailures": len(result.expectedFailures),
    "unexpectedSuccesses": len(result.unexpectedSuccesses), "events": result.events}, ensure_ascii=False))
sys.exit(0 if result.wasSuccessful() else 1)
'''


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def input_names(root):
    # Full rebuild reads these trace/witness inputs through axiom_matrix.
    discovered = [*root.glob("*.scene"), *(root / "geometry-guide/witness").rglob("*")]
    return tuple(sorted({*INPUTS, *(path.relative_to(root).as_posix()
                                   for path in discovered if path.is_file())}))


def probe(root, methods, out, label):
    command = [sys.executable, "-B", "-c", CHILD, str(root), *methods]
    row = {"command": command, "timeoutSeconds": 30, "exit": None}
    try:
        process = subprocess.run(command, cwd=root, capture_output=True, timeout=30,
                                 env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"})
        stdout, stderr = process.stdout, process.stderr
        row["exit"] = process.returncode
    except subprocess.TimeoutExpired as error:
        stdout, stderr = error.stdout or b"", error.stderr or b""
        row["blocked"] = "timeout"
    except OSError as error:
        stdout, stderr = b"", str(error).encode("utf-8")
        row["blocked"] = "process-start"
    for stream, raw in (("stdout", stdout), ("stderr", stderr)):
        path = out / (label + "." + stream)
        path.write_bytes(raw)
        row[stream] = {"file": path.name, "bytes": len(raw), "sha256": sha(raw)}
    try:
        row["result"] = json.loads(stdout)
    except (ValueError, UnicodeDecodeError):
        row["blocked"] = row.get("blocked", "missing-or-malformed-unittest-result")
    return row


def complete(row, methods):
    result = row.get("result", {})
    return (not row.get("blocked") and result.get("selected") == list(methods)
            and result.get("testsRun") == len(methods) and result.get("formalDiscovery") == 51
            and all(result.get(key) == 0 for key in (
                "errors", "skips", "expectedFailures", "unexpectedSuccesses")))


def green(row):
    return (complete(row, METHODS) and row["exit"] == 0
            and row["result"]["failures"] == 0 and row["result"]["events"] == [])


def killed(row, method, marker, params):
    result = row.get("result", {})
    events = result.get("events", [])
    return (complete(row, (method,)) and row["exit"] == 1
            and result.get("failures") == len(params) and len(events) == len(params)
            and [event.get("params") for event in events] == params
            and all(event.get("test") == "r374_reader_test.CanonicalReader." + method
                    and event.get("kind") == "failure"
                    and event.get("exceptionType") == "AssertionError"
                    and event.get("exceptionModule") == "builtins"
                    and event.get("message", "").endswith(marker) for event in events))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    root, out = args.root.resolve(), args.out.resolve()
    if out == root or root in out.parents:
        parser.error("--out must be outside the source repository")
    out.mkdir(parents=True, exist_ok=False)
    original = {name: (root / name).read_bytes() for name in input_names(root)}
    runner = Path(__file__).resolve()
    runner_bytes = runner.read_bytes()
    receipt = {
        "schema": "r374-reader-mutations/1", "status": "blocked", "sourceRoot": str(root),
        "sourceHead": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip(),
        "runner": {"path": str(runner), "bytes": len(runner_bytes), "sha256": sha(runner_bytes)},
        "inputs": {name: {"bytes": len(raw), "sha256": sha(raw)} for name, raw in original.items()},
        "cases": [],
    }
    try:
        for name, path, anchor, *_ in CASES:
            if original[path].count(anchor.encode("utf-8")) != 1:
                raise RuntimeError(name + ": mutation anchor must occur exactly once")
        with tempfile.TemporaryDirectory(prefix="r374-reader-") as folder:
            target = Path(folder)
            for name, raw in original.items():
                destination = target / name
                destination.parent.mkdir(parents=True, exist_ok=True)
                if name in COPIES:
                    destination.write_bytes(raw)
                else:
                    # Helpers only read these dependencies; -B prevents bytecode writes.
                    destination.symlink_to(root / name)
            receipt["baseline"] = probe(target, METHODS, out, "baseline")
            if not green(receipt["baseline"]):
                raise RuntimeError("baseline did not pass all helpers without errors/skips")
            for name, path, anchor, method, marker, params in CASES:
                mutated = original[path].replace(anchor.encode("utf-8"), b"", 1)
                row = {"id": name, "path": path, "removed": anchor,
                       "mutantSha256": sha(mutated), "requiredAssertion": marker,
                       "requiredSubtests": params, "status": "blocked"}
                receipt["cases"].append(row)
                try:
                    (target / path).write_bytes(mutated)
                    row["mutant"] = probe(target, (method,), out, name)
                finally:
                    (target / path).write_bytes(original[path])
                row["restored"] = probe(target, METHODS, out, name + "-restored")
                row["status"] = ("killed/exact-assertion" if killed(row["mutant"], method, marker, params)
                                 and green(row["restored"]) else "not-killed")
            receipt["copiesRestored"] = all((target / name).read_bytes() == original[name] for name in COPIES)
        receipt["temporaryRemoved"] = not target.exists()
        receipt["status"] = "passed" if (receipt["copiesRestored"] and receipt["temporaryRemoved"]
            and len(receipt["cases"]) == len(CASES)
            and all(row["status"] == "killed/exact-assertion" for row in receipt["cases"])) else "failed"
    except Exception as error:
        receipt["error"] = type(error).__name__ + ": " + str(error)
    finally:
        receipt["sourceUnchanged"] = (input_names(root) == tuple(original)
                                      and all((root / name).read_bytes() == raw for name, raw in original.items())
                                      and runner.read_bytes() == runner_bytes)
        if not receipt["sourceUnchanged"]:
            receipt["status"] = "failed"
        (out / "receipt.json").write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": receipt["status"], "sourceUnchanged": receipt["sourceUnchanged"],
                      "killed": sum(row["status"] == "killed/exact-assertion" for row in receipt["cases"]),
                      "receipt": str(out / "receipt.json")}, ensure_ascii=False))
    return 0 if receipt["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
