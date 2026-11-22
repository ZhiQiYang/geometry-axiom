#!/usr/bin/env python3
"""PF-6 directed native withdrawals from the official mutation definitions.

Run in disposable source copies. Each named case is genuinely executed as
baseline / withdrawn / restored against the same unittest method. Only the
original bridge oracle's semantic AssertionError classification is accepted;
compile failures, unknown commands, skips, crashes and timeouts are not kills.
This produces local evidence, never edits the official mutation ledger, and
keeps the original binaries.py compiler flags and build timeout.
"""
import argparse
import hashlib
import inspect
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tests"))
import binaries
import mutate
import mutation_bridge

BUILD = """import pathlib,sys
sys.path.insert(0,'tests')
import binaries
binaries.OUT_DIR=pathlib.Path(sys.argv[1])
raise SystemExit(binaries.main(['build','bridge']))
"""


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def write_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n",
                    encoding="utf-8", newline="\n")


def run(work, argv, folder, label, timeout):
    folder.mkdir(parents=True, exist_ok=True)
    env = {key: value for key, value in os.environ.items()
           if not key.startswith(("GEOMETRY_", "MUTATE_"))}
    env.update(PYTHONDONTWRITEBYTECODE="1", PYTHONIOENCODING="utf-8")
    began = time.monotonic()
    record = mutation_bridge._run(argv, work, env, folder, label,
                                  ROOT, work, folder, timeout=timeout)
    record.update(seconds=time.monotonic() - began, timeout_seconds=timeout)
    for stream in ("stdout", "stderr"):
        path = folder / (label + "." + stream)
        record[stream + "_file"] = str(path)
        record[stream + "_sha256"] = sha(path.read_bytes())
    write_json(folder / (label + ".execution.json"), record)
    return record


def build(work, output, folder, label):
    record = run(work, [sys.executable, "-B", "-c", BUILD, str(output)],
                 folder, label, 900)
    if record["exit_code"]:
        raise RuntimeError("native build failed: " + record["stderr_file"])
    executable = output / ("bridge.exe" if os.name == "nt" else "bridge")
    record.update(binary=str(executable), binary_sha256=sha(executable.read_bytes()),
                  sidecar=json.loads(executable.with_name(
                      executable.name + binaries.SIDECAR_SUFFIX).read_text(encoding="utf-8")))
    write_json(folder / (label + ".execution.json"), record)
    return executable, record


def judge(work, executable, methods, folder, label):
    timeout = inspect.signature(mutation_bridge._run).parameters["timeout"].default
    return run(work, [sys.executable, "-B", "tests/bridge_mutation_oracle.py",
                      str(executable), *methods], folder, label, timeout)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--list", action="store_true")
    parser.add_argument("--out", type=Path)
    parser.add_argument("ids", nargs="*")
    args = parser.parse_args(argv)
    selected = [m for m in mutate.MUTANTS if m["id"].startswith("PF6_")
                and (not args.ids or m["id"] in args.ids)]
    if not selected or (args.ids and set(args.ids) != {m["id"] for m in selected}):
        parser.error("expected existing PF6_ IDs from tests/mutate.py")
    if args.list:
        for mutation in selected:
            print(mutation["id"], mutation["desc"])
        return 0
    if not args.out:
        parser.error("--out is required")
    output = args.out.resolve()
    output.mkdir(parents=True, exist_ok=False)
    if os.name != "nt":
        import resource
        hard = resource.getrlimit(resource.RLIMIT_STACK)[1]
        resource.setrlimit(resource.RLIMIT_STACK, (16777216, hard))
    source = mutate.Sources(ROOT)
    for mutation in selected:
        kind, reason = mutate.definition_kind(mutation, source)
        if kind != "run":
            raise RuntimeError(mutation["id"] + ": " + reason)
    paths = set(binaries._scan_shared())
    paths.update((ROOT / "tests").glob("*.py"))
    paths.update((ROOT / "tests").glob("*.c"))
    paths.update(ROOT.glob("*.scene"))
    paths.update((ROOT / "tests/fixtures").rglob("*.scene"))
    original = {p.relative_to(ROOT).as_posix(): p.read_bytes()
                for p in sorted(paths) if p.is_file()}
    write_json(output / "sources.json", {p: {"bytes": len(raw), "sha256": sha(raw)}
                                          for p, raw in original.items()})
    head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT,
                          capture_output=True, text=True, check=True).stdout.strip()
    report = {"schema": "pf6-directed-native-mutations/1", "base_sha": head,
              "official_ledger": False, "table": "tests/mutate.py MUTANTS",
              "closure_sha256": source.closure, "mutations": []}
    with tempfile.TemporaryDirectory(prefix="pf6-mutation-source-") as temporary:
        work = Path(temporary)
        for relative, raw in original.items():
            target = work / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(raw)
        if mutate.Sources(work).closure != source.closure:
            raise RuntimeError("copied native closure differs from source")
        baseline_binary, baseline_build = build(work, output / "binaries/base", output, "base-build")
        report["baseline_build"] = baseline_build
        for mutation in selected:
            folder = output / mutation["id"]
            methods = mutation["tests"]
            expected_judge = mutation_bridge.oracle_hash(mutation, work)
            baseline = judge(work, baseline_binary, methods, folder, "baseline")
            if mutation_bridge.classify(baseline, methods) != "survived":
                raise RuntimeError(mutation["id"] + ": baseline did not pass the exact judges")
            target = work / mutation["file"]
            fixed = target.read_bytes()
            ending = b"\r\n" if b"\r\n" in fixed else b"\n"
            old, new = (mutation[key].encode("utf-8").replace(b"\n", ending)
                        for key in ("old", "new"))
            if fixed.count(old) != 1:
                raise RuntimeError(mutation["id"] + ": withdrawal anchor is not unique")
            try:
                target.write_bytes(fixed.replace(old, new, 1))
                mutant_binary, mutant_build = build(work, output / "binaries" / mutation["id"],
                                                    folder, "mutant-build")
                withdrawn = judge(work, mutant_binary, methods, folder, "withdrawn")
            finally:
                target.write_bytes(fixed)
            if mutate.Sources(work).closure != source.closure:
                raise RuntimeError("restored native source bytes differ")
            if mutation_bridge.oracle_hash(mutation, work) != expected_judge:
                raise RuntimeError("judge changed during withdrawal")
            if sha(baseline_binary.read_bytes()) != baseline_build["binary_sha256"]:
                raise RuntimeError("baseline executable changed before restoration")
            restored = judge(work, baseline_binary, methods, folder, "restored")
            verdict = mutation_bridge.classify(withdrawn, methods)
            restored_verdict = mutation_bridge.classify(restored, methods)
            named_assertion = bool(withdrawn["result"]) and any(
                mutation["id"] in failure.get("detail", "")
                for failure in withdrawn["result"].get("failures", []))
            entry = {"id": mutation["id"], "definition_sha256": mutate.mutant_key(mutation),
                     "oracle_sha256": expected_judge, "methods": methods,
                     "baseline": baseline, "build": mutant_build, "withdrawn": withdrawn,
                     "restored": restored, "verdict": verdict,
                     "named_assertion": named_assertion,
                     "restored_verdict": restored_verdict,
                     "exits": [baseline["exit_code"], withdrawn["exit_code"], restored["exit_code"]]}
            report["mutations"].append(entry)
            report["original_sources_unchanged"] = all((ROOT / p).read_bytes() == raw
                                                        for p, raw in original.items())
            write_json(output / "results.json", report)
            print(mutation["id"], verdict, entry["exits"], flush=True)
            if (verdict != "killed" or not named_assertion or restored_verdict != "survived"
                    or entry["exits"] != [0, 1, 0] or not report["original_sources_unchanged"]):
                return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
