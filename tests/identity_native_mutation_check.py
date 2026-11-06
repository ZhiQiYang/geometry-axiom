#!/usr/bin/env python3
"""Directed native R09a mutation evidence, using the real mutation table/oracle.

The complete official ledger remains tests/mutate.py's responsibility. This
runner never reads or rewrites mutants_results.json. It copies current source,
uses binaries.py with explicitly recorded -O0 flags for quick local evidence,
and executes the actual named bridge tests before/mutated/restored. To produce
official O2 ledger entries after committing the patches, run tests/mutate.py
with the fourteen R09A_N* IDs printed by --list. The two private fault rows
are a separate, explicitly non-official table selected by --private-faults.
Their actual instrumented binary is hashed and passed to both the oracle's
ChildWatch and the fault tests; no official O2 binary stands in for it.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tests"))
import binaries
import mutate
import mutation_bridge

PRIVATE_FAULT_MUTANTS = [
    dict(id="R09A_N15_PENDING_NOT_COMMITTED", desc="P053：暫配未驗證就推進正式序號", binary="private-fault",
         file="geometry-app/native/identity_ledger.inc", old="uint64_t serial = g_identity_next_serial;",
         new="uint64_t serial = g_identity_next_serial; g_identity_next_serial += need;",
         tests=["tests.test_identity_ledger_faults.IdentityLedgerFaults.test_P053_failed_settlement_after_temporary_allocation_consumes_nothing"]),
    dict(id="R09A_N16_INCOMPLETE_DUMP", desc="I70/L20：放行不完整帳本的完整dump", binary="private-fault",
         file="geometry-web/web_bridge.c", old="if (!deidentified && !complete) {", new="if (false) {",
         tests=["tests.test_identity_ledger_faults.IdentityLedgerFaults.test_L20_incomplete_world_refuses_full_dump_but_can_export_and_undo"]),
]

BUILD = """import pathlib,sys
sys.path.insert(0,'tests')
import binaries
binaries.OUT_DIR=pathlib.Path(sys.argv[1])
if not binaries.IS_WIN: binaries.BY_NAME['bridge'].posix_flags=['-std=c11','-O0']
raise SystemExit(binaries.main(['build','bridge']))
"""
ORACLE = """import sys
sys.path.insert(0,'tests')
import binaries
if not binaries.IS_WIN: binaries.BY_NAME['bridge'].posix_flags=['-std=c11','-O0']
import bridge_mutation_oracle
raise SystemExit(bridge_mutation_oracle.main(sys.argv[1:]))
"""
FAULT_BUILD = """import sys
from tests._identity_fault_bridge import build
print(build(sys.argv[1]))
"""
FAULT_ORACLE = """import os,sys
sys.path.insert(0,'tests')
os.environ['GEOMETRY_IDENTITY_FAULT_BRIDGE']=sys.argv[1]
import bridge_mutation_oracle
raise SystemExit(bridge_mutation_oracle.main(sys.argv[1:]))
"""


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def run(work, argv, folder, label):
    folder.mkdir(parents=True, exist_ok=True)
    env = {key: value for key, value in os.environ.items() if not key.startswith(("GEOMETRY_", "MUTATE_"))}
    env.update(PYTHONDONTWRITEBYTECODE="1", PYTHONIOENCODING="utf-8")
    completed = subprocess.run(argv, cwd=work, env=env, capture_output=True, timeout=300)
    record = {"command": argv, "exit_code": completed.returncode}
    for stream in ("stdout", "stderr"):
        raw = getattr(completed, stream)
        path = folder / (label + "." + stream)
        path.write_bytes(raw)
        record[stream + "_file"] = str(path)
        record[stream + "_sha256"] = sha(raw)
    rows = [line[len("GEOMETRY_BRIDGE_MUTATION_RESULT "):] for line in completed.stdout.decode("utf-8", "replace").splitlines()
            if line.startswith("GEOMETRY_BRIDGE_MUTATION_RESULT ")]
    record["result"] = json.loads(rows[0]) if len(rows) == 1 else None
    return record


def build(work, native, folder, label):
    record = run(work, [sys.executable, "-B", "-c", BUILD, str(native)], folder, label)
    if record["exit_code"]:
        raise RuntimeError("build failed: " + record["stderr_file"])
    binary = native / ("bridge.exe" if os.name == "nt" else "bridge")
    record["binary"] = str(binary)
    record["binary_sha256"] = sha(binary.read_bytes())
    record["sidecar"] = json.loads(binary.with_name(binary.name + binaries.SIDECAR_SUFFIX).read_text())
    return binary, record


def build_fault(work, native, folder, label):
    record = run(work, [sys.executable, "-B", "-c", FAULT_BUILD, str(native)], folder, label)
    if record["exit_code"]:
        raise RuntimeError("private fault build failed: " + record["stderr_file"])
    binary = native / ("identity_fault_bridge.exe" if os.name == "nt" else "identity_fault_bridge")
    record.update(binary=str(binary), binary_sha256=sha(binary.read_bytes()),
                  native_closure_sha256=mutate.Sources(work).closure,
                  fault_helper_sha256=sha((work / "tests/_identity_fault_bridge.py").read_bytes()),
                  compiler_mode="private instrumented native: -std=c11 -O0",
                  oracle_binary=str(binary), fault_fixture_binary=str(binary),
                  generated_sources={p.name: sha(p.read_bytes()) for p in sorted(native.iterdir())
                                     if p.suffix in (".c", ".inc")})
    return binary, record


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--list", action="store_true")
    parser.add_argument("--private-faults", action="store_true",
                        help="run the separate instrumented native table; never the formal ledger")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--native-output", type=Path)
    parser.add_argument("ids", nargs="*")
    args = parser.parse_args(argv)
    pool = PRIVATE_FAULT_MUTANTS if args.private_faults else mutate.MUTANTS
    selected = [m for m in pool if m["id"].startswith("R09A_N") and (not args.ids or m["id"] in args.ids)]
    if args.ids and set(args.ids) != {m["id"] for m in selected}:
        parser.error("unknown R09a mutation ID")
    if args.list:
        for mutation in selected:
            print(mutation["id"], mutation["desc"])
        return 0
    if not args.output or not args.native_output:
        parser.error("--output and --native-output are required")
    output, native = args.output.resolve(), args.native_output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    native.mkdir(parents=True, exist_ok=True)
    src = mutate.Sources(ROOT)
    for mutation in selected:
        # The existing definition checker always checks native closure and a
        # unique anchor. Only formal binary="bridge" rows use RESTORED; the
        # private table proves its own exact method set in the baseline below.
        kind, reason = mutate.definition_kind(mutation, src)
        if kind != "run":
            raise RuntimeError(mutation["id"] + ": " + reason)
    methods = sorted({method for mutation in selected for method in mutation["tests"]})
    with tempfile.TemporaryDirectory(prefix="r09a-mutation-source-", dir=native) as temporary:
        work = Path(temporary)
        # Copy every byte used by the official fingerprint plus the actual
        # Python judges and native scene fixtures. Product sources stay intact.
        paths = set(binaries._scan_shared())
        paths.update((ROOT / "tests").glob("*.py"))
        paths.update((ROOT / "tests").glob("*.c"))
        paths.update(ROOT.glob("*.scene"))
        paths.update((ROOT / "tests/fixtures").rglob("*.scene"))
        for path in sorted(paths):
            if path.is_file():
                target = work / path.relative_to(ROOT)
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(path, target)
        if mutate.Sources(work).closure != src.closure:
            raise RuntimeError("copied native closure differs from reviewed product")
        judges = {m["id"]: mutation_bridge.oracle_hash(m, work) for m in selected}
        judge_files = {p.relative_to(work).as_posix(): sha(p.read_bytes())
                       for p in sorted((work / "tests").glob("*.py"))}
        builder = build_fault if args.private_faults else build
        oracle = FAULT_ORACLE if args.private_faults else ORACLE
        baseline_binary, baseline_build = builder(work, native / "baseline", output, "baseline-build")
        baseline = run(work, [sys.executable, "-B", "-c", oracle, str(baseline_binary), *methods], output, "baseline")
        if mutation_bridge.classify(baseline, methods) != "survived":
            raise RuntimeError("directed baseline did not pass all methods")
        report = {"schema": "r09a-private-fault-mutations/1" if args.private_faults else "r09a-directed-native-mutations/1",
                  "base_pr_head": "8bc9f3f0298fcf6b4120dd1ea99ab30abd7da743", "official_ledger": False,
                  "table": "PRIVATE_FAULT_MUTANTS" if args.private_faults else "tests/mutate.py MUTANTS",
                  "compiler_mode": "-std=c11 -O0 (private instrumented native)" if args.private_faults
                      else "official Windows flags" if os.name == "nt" else "-std=c11 -O0",
                  "closure_sha256": src.closure, "judge_file_sha256": judge_files,
                  "baseline_build": baseline_build, "baseline": baseline, "mutations": []}
        for mutation in selected:
            folder = output / mutation["id"]
            target = work / mutation["file"]
            fixed = target.read_bytes()
            ending = b"\r\n" if b"\r\n" in fixed else b"\n"
            old, new = (mutation[key].encode("utf-8").replace(b"\n", ending) for key in ("old", "new"))
            if fixed.count(old) != 1:
                raise RuntimeError("mutation anchor not unique: " + mutation["id"])
            try:
                target.write_bytes(fixed.replace(old, new, 1))
                mutant_binary, mutation_build = builder(work, native / mutation["id"], folder, "mutant-build")
                failed = run(work, [sys.executable, "-B", "-c", oracle, str(mutant_binary), *mutation["tests"]], folder, "mutant")
            finally:
                target.write_bytes(fixed)
            if mutate.Sources(work).closure != src.closure:
                raise RuntimeError("source restoration failed")
            if mutation_bridge.oracle_hash(mutation, work) != judges[mutation["id"]]:
                raise RuntimeError("oracle changed during mutation")
            if sha(baseline_binary.read_bytes()) != baseline_build["binary_sha256"]:
                raise RuntimeError("baseline executable changed before restoration")
            restored = run(work, [sys.executable, "-B", "-c", oracle, str(baseline_binary), *mutation["tests"]], folder, "restored")
            verdict = mutation_bridge.classify(failed, mutation["tests"])
            restored_verdict = mutation_bridge.classify(restored, mutation["tests"])
            definition = sha(json.dumps(mutation, sort_keys=True, ensure_ascii=False).encode("utf-8")) if args.private_faults else mutate.mutant_key(mutation)
            entry = {"id": mutation["id"], "definition_sha256": definition,
                     "oracle_sha256": judges[mutation["id"]],
                     "source_file": mutation["file"], "source_sha256": src.hashes[mutation["file"]],
                     "methods": mutation["tests"], "build": mutation_build, "mutant": failed,
                     "restored": restored, "verdict": verdict, "restored_verdict": restored_verdict}
            report["mutations"].append(entry)
            (output / "results.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
            print(mutation["id"], verdict, "restored=" + restored_verdict, flush=True)
            if verdict != "killed" or restored_verdict != "survived":
                return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
