#!/usr/bin/env python3
"""Directed R363 merge regressions; never rewrites the official mutation ledger.

Run --check to verify unique product anchors.  Run --output DIR to copy the
native source closure and test inputs into a disposable directory, build actual
-O0 binaries with honest binaries.py sidecars, and require baseline green,
eight exact named assertion failures, and restored green.  Build failures,
missing anchors, crashes, timeouts, errors and skips never count as kills.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / "tests")]
import binaries
import mutate
import mutation_bridge

MODULE = "tests.test_r363_native_merge."
BOUND = MODULE + "R363CapabilityBounds.test_full_bridge_union_and_model_boundary"
NATIVE = MODULE + "R363NativeMerge."
ALL_METHODS = [BOUND] + [NATIVE + name for name in (
    "test_bay_candidate_settlement_keeps_existing_marks_and_serial",
    "test_bridge_and_candidate_advertise_both_capabilities",
    "test_dump_keeps_bay_and_identity_and_deidentified_keeps_bay",
    "test_mixed_scene_roundtrip_and_stripped_requirements_reject_atomically",
    "test_scenario_verification_accepts_complete_mixed_scene")]
SCENARIO = 'BRIDGE_CAPABILITIES = NATIVE_CAPABILITIES | {"grid-subdivision-rules/1", "assembly-bay-repeat/1", "definition-import/1", "identity-ledger/1"}'

CASES = [
    {"id": "R363_NM01_NO_BAY_DUMP", "file": "current_geometry.c",
     "old": '    if(world->wood.assembly.bay_required)fputs("requires assembly-bay-repeat/1\\n",out);\n', "new": "",
     "method": NATIVE + "test_dump_keeps_bay_and_identity_and_deidentified_keeps_bay",
     "assertion": "R363_N03_BAY_DUMP_REQUIREMENT"},
    {"id": "R363_NM02_NO_IDENTITY_DUMP", "file": "current_geometry.c",
     "old": "    identity_dump_requires(world,out);\n", "new": "",
     "method": NATIVE + "test_dump_keeps_bay_and_identity_and_deidentified_keeps_bay",
     "assertion": "R363_N03_IDENTITY_DUMP_REQUIREMENT"},
    {"id": "R363_NM03_NO_BAY_REQUIRES_PARSER", "file": "geometry-core/engineering_commands.inc",
     "old": '    if(!strcmp(tokens[1],ASM_BAY_CAPABILITY)){w->wood.assembly.bay_required=true;return true;}\n', "new": "",
     "method": NATIVE + "test_mixed_scene_roundtrip_and_stripped_requirements_reject_atomically",
     "assertion": "R363_N04_MIXED_REPLAY"},
    {"id": "R363_NM04_NO_IDENTITY_REQUIRES_PARSER", "file": "geometry-core/engineering_commands.inc",
     "old": '    if(!strcmp(tokens[1],"identity-ledger/1"))return identity_accept_requires(path,line_no,w);\n', "new": "",
     "method": NATIVE + "test_mixed_scene_roundtrip_and_stripped_requirements_reject_atomically",
     "assertion": "R363_N04_MIXED_REPLAY"},
    {"id": "R363_NM05_NO_BAY_BRIDGE_CAPABILITY", "file": "geometry-web/engineering_bridge.inc",
     "old": ',\\"assembly-bay-repeat/1\\"', "new": "",
     "method": NATIVE + "test_bridge_and_candidate_advertise_both_capabilities",
     "assertion": "R363_N02_BRIDGE_CAPABILITY_UNION"},
    {"id": "R363_NM06_NO_IDENTITY_BRIDGE_CAPABILITY", "file": "geometry-web/engineering_bridge.inc",
     "old": ',\\"identity-ledger/1\\"', "new": "",
     "method": NATIVE + "test_bridge_and_candidate_advertise_both_capabilities",
     "assertion": "R363_N02_BRIDGE_CAPABILITY_UNION"},
    {"id": "R363_NM07_NO_BAY_VERIFIER_CAPABILITY", "file": "geometry-web/scenario_verify.py",
     "old": SCENARIO, "new": SCENARIO.replace('"assembly-bay-repeat/1", ', ""),
     "method": BOUND, "assertion": "R363_N01_VERIFIER_CAPABILITY_UNION", "python_only": True},
    {"id": "R363_NM08_NO_IDENTITY_VERIFIER_CAPABILITY", "file": "geometry-web/scenario_verify.py",
     "old": SCENARIO, "new": SCENARIO.replace(', "identity-ledger/1"', ""),
     "method": BOUND, "assertion": "R363_N01_VERIFIER_CAPABILITY_UNION", "python_only": True},
]

BUILD = """import pathlib,sys
sys.path[:0]=['.', 'tests']
import binaries
binaries.OUT_DIR=pathlib.Path(sys.argv[1])
if not binaries.IS_WIN:binaries.BY_NAME['bridge'].posix_flags=['-std=c11','-O0']
raise SystemExit(binaries.main(['build','bridge']))
"""
ORACLE = """import sys
sys.path[:0]=['.', 'tests']
import binaries
from tests import binaries as qualified
for module in (binaries,qualified):
 if not module.IS_WIN:module.BY_NAME['bridge'].posix_flags=['-std=c11','-O0']
import bridge_mutation_oracle
raise SystemExit(bridge_mutation_oracle.main(sys.argv[1:]))
"""


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def check(root):
    problems = []
    test = (root / "tests/test_r363_native_merge.py").read_text(encoding="utf-8")
    for case in CASES:
        source = (root / case["file"]).read_text(encoding="utf-8")
        if source.count(case["old"]) != 1:
            problems.append(case["id"] + ": product anchor is not unique")
        if case["assertion"] not in test:
            problems.append(case["id"] + ": named assertion is missing")
    return problems


def run(work, command, folder, label):
    folder.mkdir(parents=True, exist_ok=True)
    env = {key: value for key, value in os.environ.items() if not key.startswith(("GEOMETRY_", "MUTATE_"))}
    env.update(PYTHONDONTWRITEBYTECODE="1", PYTHONIOENCODING="utf-8")
    try:
        p = subprocess.run(command, cwd=work, env=env, capture_output=True, timeout=300)
        raw = {"stdout": p.stdout, "stderr": p.stderr}
        record = {"command": command, "exit_code": p.returncode, "timed_out": False}
    except subprocess.TimeoutExpired as exc:
        raw = {"stdout": exc.stdout or b"", "stderr": exc.stderr or b""}
        record = {"command": command, "exit_code": None, "timed_out": True}
    for stream, content in raw.items():
        path = folder / (label + "." + stream)
        path.write_bytes(content)
        record[stream + "_file"] = str(path)
        record[stream + "_sha256"] = sha(content)
    prefix = "GEOMETRY_BRIDGE_MUTATION_RESULT "
    rows = [line[len(prefix):] for line in raw["stdout"].decode("utf-8", "replace").splitlines() if line.startswith(prefix)]
    try:
        record["result"] = json.loads(rows[0]) if len(rows) == 1 else None
    except ValueError:
        record["result"] = None
    return record


def build(work, folder):
    native = folder / "native"
    native.mkdir(parents=True, exist_ok=True)
    record = run(work, [sys.executable, "-B", "-c", BUILD, str(native)], folder, "build")
    binary = native / ("bridge.exe" if os.name == "nt" else "bridge")
    if record["exit_code"] != 0 or record["timed_out"] or not binary.is_file():
        raise RuntimeError("native build failed; this is not a mutation kill: " + str(folder))
    record.update(binary=str(binary), binary_sha256=sha(binary.read_bytes()),
                  sidecar=json.loads(binary.with_name(binary.name + binaries.SIDECAR_SUFFIX).read_text()))
    return binary, record


def observe(work, binary, methods, folder, label):
    return run(work, [sys.executable, "-B", "-c", ORACLE, str(binary), *methods], folder, label)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    problems = check(ROOT)
    if args.check:
        print(json.dumps(problems))
        return bool(problems)
    if problems:
        raise RuntimeError("; ".join(problems))
    if args.output is None:
        parser.error("--output is required")
    out = args.output.resolve()
    out.mkdir(parents=True, exist_ok=True)
    source = mutate.Sources(ROOT)
    report = {"schema": "r363-directed-native-merge-mutations/1", "official_ledger": False,
              "inputs": {"head": "fab44a9e2eaa3868a3485c72252947d6f7f49429",
                         "main": "ffd84ea67bc55136b64482833359b025a8c03826"},
              "compiler_mode": "official Windows flags" if os.name == "nt" else "-std=c11 -O0",
              "native_closure_sha256": source.closure, "cases": []}
    def save():
        (out / "results.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    with tempfile.TemporaryDirectory(prefix="r363-native-merge-") as temporary:
        work = Path(temporary)
        paths = set(binaries._scan_shared())
        for directory in (ROOT / "tests", ROOT / "geometry-app", ROOT / "geometry-core",
                          ROOT / "geometry-templates", ROOT / "geometry-web"):
            paths.update(directory.rglob("*.py"))
        paths.update(ROOT.glob("*.scene"))
        paths.update((ROOT / "tests/fixtures").rglob("*.scene"))
        paths.add(ROOT / "公理層.md")
        for path in paths:
            if path.is_file():
                target = work / path.relative_to(ROOT)
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(path, target)
        if mutate.Sources(work).closure != source.closure:
            raise RuntimeError("native source snapshot differs from the submitted source")
        oracle_files = {p.relative_to(work).as_posix(): sha(p.read_bytes())
                        for p in sorted((work / "tests").rglob("*.py"))}
        report["judge_file_sha256"] = oracle_files
        baseline_binary, report["baseline_build"] = build(work, out / "baseline")
        report["baseline"] = observe(work, baseline_binary, ALL_METHODS, out / "baseline", "oracle")
        save()
        if mutation_bridge.classify(report["baseline"], ALL_METHODS) != "survived":
            raise RuntimeError("baseline is not green; no mutants were accepted")
        for case in CASES:
            path = work / case["file"]
            fixed = path.read_bytes()
            ending = b"\r\n" if b"\r\n" in fixed else b"\n"
            old, new = [case[key].encode().replace(b"\n", ending) for key in ("old", "new")]
            if fixed.count(old) != 1:
                raise RuntimeError(case["id"] + ": anchor not unique in the actual snapshot")
            folder = out / case["id"]
            try:
                path.write_bytes(fixed.replace(old, new, 1))
                if case.get("python_only"):
                    binary, built = baseline_binary, {"reused_native_binary": str(baseline_binary),
                                                       "binary_sha256": sha(baseline_binary.read_bytes())}
                else:
                    binary, built = build(work, folder)
                changed = observe(work, binary, [case["method"]], folder, "mutant")
            finally:
                path.write_bytes(fixed)
            if mutate.Sources(work).closure != source.closure:
                raise RuntimeError("native source was not restored")
            if any(sha((work / name).read_bytes()) != digest for name, digest in oracle_files.items()):
                raise RuntimeError("an oracle source changed during mutation")
            restored = observe(work, baseline_binary, [case["method"]], folder, "restored")
            verdict = mutation_bridge.classify(changed, [case["method"]])
            failures = (changed.get("result") or {}).get("failures", [])
            exact = (verdict == "killed" and len(failures) == 1
                     and failures[0]["test"] == case["method"] and case["assertion"] in failures[0]["detail"])
            restored_green = mutation_bridge.classify(restored, [case["method"]]) == "survived"
            record = {"definition": case, "source_sha256": sha(fixed), "build": built,
                      "mutant": changed, "restored": restored,
                      "verdict": "killed/exact-assertion" if exact else "blocked-or-survived",
                      "restored_green": restored_green}
            report["cases"].append(record)
            save()
            print(case["id"], record["verdict"], "restored=" + str(restored_green), flush=True)
            if not exact or not restored_green:
                return 1
        report["restored_all"] = observe(work, baseline_binary, ALL_METHODS, out / "restored", "oracle")
        report["restored_all_green"] = mutation_bridge.classify(report["restored_all"], ALL_METHODS) == "survived"
        save()
        return 0 if report["restored_all_green"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
