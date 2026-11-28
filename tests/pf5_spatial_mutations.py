"""Local PF5 native source withdrawals with exact named 0/1/0 evidence.

Copies the current candidate inputs to an isolated directory, never changes the
invoking repository, and uses the original binaries builder, flags, fingerprint,
smoke and sidecar checks. Only its output directory is isolated. Compilation is
bounded by 900 seconds and each selected native test by the existing 60 seconds.
This report is not the official mutation ledger or a browser acceptance receipt.
"""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import shutil
import signal
import subprocess
import sys
import tempfile
import time
import unittest

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))
import pf5_geometry_mutations as diagnostic

SOURCE = "geometry-web/panel_fill_spatial_bridge.inc"
TEST_FILE = "tests/test_pf5_spatial_native.py"
BUILD_TIMEOUT = 900
TEST_TIMEOUT = 60
MUTATIONS = [
    {"name": "PF5_NATIVE_WITHDRAW_PANEL_CLIP", "file": SOURCE,
     "before": "if(!pf_clip(w,d,tile))return false; /* PF5_NATIVE_PANEL_CLIP */",
     "after": "/* PF5_NATIVE_PANEL_CLIP withdrawn: the real envelope clip is not called. */",
     "test": "PF5SpatialNative.test_Q47_six_heights_keep_two_independent_layers",
     "assertion": "PF5_NATIVE_PANEL_AREA"},
    {"name": "PF5_NATIVE_WITHDRAW_STRUCTURAL_SIDE", "file": SOURCE,
     "before": "layer->frame.normal=(d->finish->side>0?d->frame.normal:geo_vector_negate(d->frame.normal)); /* PF5_NATIVE_PANEL_NORMAL */",
     "after": "layer->frame.normal=d->frame.normal; /* PF5_NATIVE_PANEL_NORMAL withdrawn: physical structural side ignored. */",
     "test": "PF5SpatialNative.test_all_signed_axis_frames_and_sides_have_exact_world_vertices",
     "assertion": "PF5_NATIVE_WORLD_VERTEX"},
    {"name": "PF5_NATIVE_WITHDRAW_SHARED_EDGE_INTERSECTION", "file": SOURCE,
     "before": "if(lo>=hi)continue; /* PF5_NATIVE_SHARED_EDGE_INTERSECTION */",
     "after": "continue; /* PF5_NATIVE_SHARED_EDGE_INTERSECTION withdrawn: no positive edge intersection is accumulated. */",
     "test": "PF5SpatialNative.test_explicit_step_junctions_and_missing_side_are_not_synthesized",
     "assertion": "PF5_NATIVE_SHARED_EDGES"},
]


def fingerprint(raw):
    return {"bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}


def bounded(command, cwd, log, timeout):
    """Capture complete raw output; kill the whole child process group on timeout."""
    start = time.monotonic()
    environment = dict(os.environ)
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    options = {"start_new_session": True} if os.name != "nt" else {"creationflags": subprocess.CREATE_NEW_PROCESS_GROUP}
    timed_out, process_status = False, None
    try:
        process = subprocess.Popen(command, cwd=cwd, env=environment, stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE, text=True, encoding="utf-8", errors="replace", **options)
        try:
            stdout, stderr = process.communicate(timeout=timeout)
            status = process.returncode
        except subprocess.TimeoutExpired:
            timed_out = True
            if os.name == "nt":
                try:
                    subprocess.run(["taskkill", "/PID", str(process.pid), "/T", "/F"],
                                   capture_output=True, timeout=10, check=False)
                finally:
                    process.kill()
            else:
                try:
                    os.killpg(process.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
            stdout, stderr = process.communicate(timeout=10)
            stderr += "\nPF5_NATIVE_WITHDRAWAL_TIMEOUT\n"
            status = 124
        process_status = process.returncode
    except OSError as error:
        stdout, stderr, status = "", "PF5_NATIVE_WITHDRAWAL_EXECUTION_ERROR: "+str(error)+"\n", 125
    elapsed = time.monotonic()-start
    raw = ("command="+json.dumps(command)+"\ncwd="+str(cwd)+"\ntimeout="+str(timeout)+
           "\nstdout:\n"+stdout+"\nstderr:\n"+stderr+"\nexit="+str(status)+
           "\nprocessExit="+str(process_status)+"\n")
    log.write_text(raw, encoding="utf-8")
    return {"exit": status, "processExit": process_status, "command": command, "cwd": str(cwd),
            "timeoutSeconds": timeout, "elapsedSeconds": elapsed, "timedOut": timed_out,
            "log": log.name, **fingerprint(log.read_bytes())}


def build_child(directory, output):
    sys.path.insert(0, str(Path(directory)/"tests"))
    import binaries
    binaries.OUT_DIR = Path(output)
    return binaries.main(["build", "bridge"])


def test_child(binary, selected, result_file):
    """Reuse the original bridge-death observer, preserving exact exception facts."""
    sys.path.insert(0, str(ROOT))
    from bridge_mutation_oracle import ChildWatch, failure_label
    os.environ["GEOMETRY_TEST_BRIDGE"] = binary
    os.environ.pop("GEOMETRY_ENGINEERING_BRIDGE", None)
    watch = ChildWatch(binary).install()

    class Result(diagnostic.EvidenceResult):
        def startTest(self, test):
            watch.mark()
            super().startTest(test)

        def record(self, test, error, kind, subtest=None):
            label = failure_label(error[1], watch.deaths()) if kind == "assertion-failure" else {"kind": "execution-error"}
            super().record(test, error, kind, subtest)
            self.events[-1]["bridgeObservation"] = label
            if label["kind"] != "assertion":
                self.events[-1]["kind"] = label["kind"]

    try:
        specification = importlib.util.spec_from_file_location("pf5_native_subject", ROOT/TEST_FILE)
        module = importlib.util.module_from_spec(specification)
        sys.modules[specification.name] = module
        specification.loader.exec_module(module)
        suite = unittest.TestLoader().loadTestsFromName(selected, module)
        result = unittest.TextTestRunner(verbosity=2, resultclass=Result).run(suite)
        report = {"events": result.events, "testsRun": result.testsRun, "failures": len(result.failures),
                  "errors": len(result.errors), "skipped": len(result.skipped),
                  "expectedFailures": len(result.expectedFailures),
                  "unexpectedSuccesses": len(result.unexpectedSuccesses), "success": result.wasSuccessful()}
        status = int(not result.wasSuccessful())
    except BaseException as error:
        import traceback
        traceback.print_exc()
        report = {"events": [{"kind": "execution-error", "test": selected,
                              "exception": type(error).__module__+"."+type(error).__name__,
                              "message": str(error), "subtest": None}],
                  "testsRun": 0, "failures": 0, "errors": 1, "skipped": 0,
                  "unexpectedSuccesses": 0, "success": False}
        status = 2
    Path(result_file).write_text(json.dumps(report, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    return status


def snapshot(target):
    # Tracked files preserve fixtures and builder inputs. The builder's own
    # source scan also includes newly added C/H/INC inputs ignored by git.
    command = ["git", "-C", str(ROOT), "ls-files", "-z", "--cached", "--others", "--exclude-standard"]
    result = subprocess.run(command, check=True, capture_output=True, timeout=10)
    paths = set(result.stdout.decode("utf-8").split("\0"))-{""}
    import binaries
    _, closure, _ = binaries.compute_fingerprint(binaries.BY_NAME["bridge"])
    paths.update(path for path in closure if (ROOT/path).is_file())
    paths.update((SOURCE, TEST_FILE, "tests/pf5_spatial_mutations.py", "tests/pf5_geometry_mutations.py",
                  "tests/pf5_geometry_oracle.py", "tests/pf5_geometry_check.py"))
    copied = {}
    for relative in sorted(paths):
        path = ROOT/relative
        if not path.is_file():
            continue
        destination = target/relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(path, destination)
        if relative in closure or relative in (TEST_FILE, "tests/pf5_spatial_mutations.py", "tests/pf5_geometry_mutations.py",
                                               "tests/pf5_geometry_oracle.py", "tests/pf5_geometry_check.py", "tests/_bridge.py",
                                               "tests/bridge_mutation_oracle.py", "tests/binaries.py"):
            copied[relative] = fingerprint(path.read_bytes())
    return copied


def phase(directory, binaries, out, name, selected):
    build = bounded([sys.executable, "-B", str(directory/"tests/pf5_spatial_mutations.py"), "--_build",
                     str(directory), str(binaries)], directory, out/(name+"-build.log"), BUILD_TIMEOUT)
    result = {"build": build}
    if build["exit"] != 0:
        result["test"] = {"exit": None, "timedOut": False, "unittest": None, "reason": "build did not pass"}
        return result
    binary = binaries/("bridge.exe" if os.name == "nt" else "bridge")
    result["binary"] = {"path": str(binary), **fingerprint(binary.read_bytes())}
    # Sidecar suffix belongs to the original builder; obtain it without guessing.
    import binaries as registry
    sidecar = binary.with_name(binary.name+registry.SIDECAR_SUFFIX)
    result["sidecar"] = fingerprint(sidecar.read_bytes())
    (out/(name+"-binary-sidecar.json")).write_bytes(sidecar.read_bytes())
    structured = out/(name+"-unittest.json")
    result["test"] = bounded([sys.executable, "-B", str(directory/"tests/pf5_spatial_mutations.py"), "--_child",
                              str(binary), selected, str(structured)], directory, out/(name+"-test.log"), TEST_TIMEOUT)
    result["test"]["unittest"] = None
    if structured.is_file():
        result["test"]["unittest"] = json.loads(structured.read_text(encoding="utf-8"))
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", required=True, help="actual full repository HEAD, not the historical design base")
    parser.add_argument("--out", type=Path, required=True, help="new evidence directory")
    args = parser.parse_args()
    head = subprocess.run(["git", "-C", str(ROOT), "rev-parse", "HEAD"], check=True,
                          capture_output=True, text=True, timeout=10).stdout.strip()
    if not re.fullmatch(r"[0-9a-f]{40}", args.base) or head != args.base:
        parser.error("--base must equal the actual full repository HEAD")
    out = args.out.resolve()
    out.mkdir(parents=True, exist_ok=False)
    report = {"schema": "pf5-native-source-withdrawals/1", "base": head,
              "scope": "local source withdrawals only; not official CI/mutation/browser evidence",
              "buildTimeoutSeconds": BUILD_TIMEOUT, "testTimeoutSeconds": TEST_TIMEOUT,
              "mutations": [], "ok": False}
    original = (ROOT/SOURCE).read_bytes()
    for item in MUTATIONS:
        if original.count(item["before"].encode("utf-8")) != 1:
            parser.error(item["name"]+": expected exactly one real calculation target")
    try:
        with tempfile.TemporaryDirectory(prefix="pf5-native-withdrawal-") as temporary:
            directory = Path(temporary)/"source"
            directory.mkdir()
            report["inputs"] = snapshot(directory)
            build_output = Path(temporary)/"binaries"
            for item in MUTATIONS:
                target = directory/item["file"]
                before = target.read_bytes()
                changed = before.replace(item["before"].encode("utf-8"), item["after"].encode("utf-8"))
                baseline = phase(directory, build_output, out, item["name"]+"-baseline", item["test"])
                try:
                    target.write_bytes(changed)
                    mutant = phase(directory, build_output, out, item["name"]+"-mutant", item["test"])
                finally:
                    target.write_bytes(before)
                restored_bytes = target.read_bytes() == before
                restored = phase(directory, build_output, out, item["name"]+"-restored", item["test"])
                codes = [step["test"]["exit"] for step in (baseline, mutant, restored)]
                killed = (codes == [0, 1, 0] and restored_bytes
                          and diagnostic.successful_run(baseline["test"]) and diagnostic.successful_run(restored["test"])
                          and diagnostic.expected_failure(mutant["test"], item["test"], item["assertion"]))
                report["mutations"].append({**item, "original": fingerprint(before), "mutated": fingerprint(changed),
                                            "baseline": baseline, "mutant": mutant, "restored": restored,
                                            "restoredBytesMatch": restored_bytes, "killed": killed})
                print(item["name"], *codes, "PASS" if killed else "FAIL", flush=True)
        report["invokingSourceUnchanged"] = (ROOT/SOURCE).read_bytes() == original
        report["ok"] = report["invokingSourceUnchanged"] and all(item["killed"] for item in report["mutations"])
    except BaseException as error:
        report["error"] = type(error).__name__+": "+str(error)
        raise
    finally:
        (out/"manifest.json").write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True)+"\n", encoding="utf-8")
    print("manifest:", out/"manifest.json", "ok="+str(report["ok"]))
    return int(not report["ok"])


if __name__ == "__main__":
    if len(sys.argv) == 4 and sys.argv[1] == "--_build":
        sys.exit(build_child(sys.argv[2], sys.argv[3]))
    if len(sys.argv) == 5 and sys.argv[1] == "--_child":
        sys.exit(test_child(sys.argv[2], sys.argv[3], sys.argv[4]))
    sys.exit(main())
