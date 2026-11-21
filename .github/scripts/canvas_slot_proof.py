"""Capture source-bound two-slot browser proofs, without granting acceptance.

Six real full/shard runs and exact browser withdrawals are required. The raw
artifact is subsequently validated/imported by canvas_registry.js; this tool
does not change counts, costs, fragments, product sources or historical pins.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import signal
import subprocess
import sys
import zipfile

import canvas_evidence as evidence

ROOT = evidence.ROOT
MODES = ("full", "shard1", "shard2")
RAW_FILES = ("candidate.json", "plan.json", "stdout.log", "stderr.log", "runtime.stdout", "runtime.stderr")
IDENTITY_FIELDS = ("execution_sha", "head_sha", "tree", "run_id", "run_attempt")
PIN_FIELDS = ("id", "module", "moduleSha256", "protocolSha256", "legacySha256")
CONTROLS = (
    ("R386_CANVAS_SLOT_STORAGE_RESTORE", "omit-restore", "R386_SLOT_STORAGE_ROUNDTRIP"),
    ("R386_CANVAS_SLOT_STATE_GUARD", "omit-guard", "R386_SLOT_FAILED_RESTORE_MUST_REJECT"),
)
ANCHORS = {
    "omit-restore": ("await helpers.eval_(restoreStorageExpression(snapshot));", "/* R386 exact restore withdrawal */"),
    "omit-guard": ("requireThat(same(snapshot,actual),'R386_CANVAS_SLOT_STATE_RESTORE');", "/* R386 exact state guard withdrawal */"),
}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def read(path):
    path = Path(path)
    evidence.require(path.is_file() and not path.is_symlink(), "R386_SLOT_RAW_FILE: " + str(path))
    return path.read_bytes()


def node(expression, *args, env=None, payload=None):
    process = subprocess.run(["node", "-e", expression, *map(str, args)], cwd=ROOT, env=env,
                             input=None if payload is None else json.dumps(payload, ensure_ascii=False),
                             text=True, capture_output=True, check=False)
    evidence.require(process.returncode == 0, "R386_SLOT_NODE_REJECTED: " + process.stderr)
    return evidence.read_json(process.stdout)


def slot_identity(section):
    evidence.require(re.fullmatch(r"P[0-9]+[A-Z]?", section) is not None, "R386_SLOT_SECTION_ID")
    return node("const R=require('./geometry-web/canvas_registry.js');"
                "process.stdout.write(JSON.stringify(R.slotIdentity(process.cwd(),process.argv[1])));", section)


def scope_environment(mode):
    evidence.require(mode in MODES, "R386_SLOT_MODE")
    env = dict(os.environ)
    # A proof never silently removes a caller's partial/update scope.
    forbidden = [name for name in env if re.fullmatch(r"GEOMETRY_.*_(?:ONLY|CASE|CASES)", name)
                 or name in {"GEOMETRY_CDP_SHARD", "GEOMETRY_CDP_FROM_P31", "GEOMETRY_CDP_UPDATE_GOLDEN",
                             "GEOMETRY_CANVAS_MODULE", "GEOMETRY_CANVAS_PLACEMENT_CANDIDATE"}]
    evidence.require(not forbidden, "R386_SLOT_SCOPE_CONTAMINATED: " + ",".join(sorted(forbidden)))
    if mode != "full":
        env["GEOMETRY_CDP_SHARD"] = mode[-1] + "/2"
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    return env


def current_plan(env):
    raw = subprocess.check_output(["node", "tests/helpers/canvas_shards.js", "plan"], cwd=ROOT, env=env)
    return evidence.read_json(raw)


def verify_run(receipt, folder, env=None):
    evidence.require(receipt.get("schema") == "geometry-canvas-slot-capture/1"
                     and receipt.get("acceptance") is False, "R386_SLOT_CAPTURE_SCHEMA")
    evidence.require(set(receipt.get("files", {})) == set(RAW_FILES), "R386_SLOT_RAW_SET")
    for name in RAW_FILES:
        evidence.require(sha(read(folder / name)) == receipt["files"][name], "R386_SLOT_RAW_HASH: " + name)
    events, result = evidence.trace(read(folder / "stdout.log"))
    environment = receipt.get("environment", {})
    port = evidence.runtime_endpoint(environment.get("GEOMETRY_TEST_URL", ""))
    evidence.require(receipt.get("command") == ["node", "geometry-web/cdp_test.js"]
                     and receipt.get("runtime_command") == ["<python>", "-B", "geometry-web/runtime_version.py", "--probe", str(port)],
                     "R386_SLOT_COMMAND")
    expected_shard = None if receipt.get("mode") == "full" else str(receipt.get("mode", ""))[-1:] + "/2"
    evidence.require(environment.get("GEOMETRY_CDP_SHARD") == expected_shard, "R386_SLOT_SCOPE")
    runtime = evidence.read_json(read(folder / "runtime.stdout"))
    evidence.require(runtime.get("schema") == "geometry-runtime/1" and runtime.get("fresh") is True
                     and runtime.get("root") == receipt.get("execution_root")
                     and isinstance(runtime.get("root"), str)
                     and runtime.get("version") == receipt.get("runtime_version") == evidence.runtime_version(),
                     "R386_SLOT_RUNTIME_SOURCE")
    evidence.require(result.get("scope", {}).get("url") == environment.get("GEOMETRY_TEST_URL")
                     and result.get("scope", {}).get("feedbackDirectory") == environment.get("GEOMETRY_FEEDBACK_DIR")
                     and receipt.get("scope") == result.get("scope")
                     and receipt.get("sections") == result.get("sections")
                     and receipt.get("assertions") == result.get("passedAssertions"), "R386_SLOT_FAKE_SUMMARY")
    payload = {"receipt": receipt, "plan": evidence.read_json(read(folder / "plan.json")),
               "candidate": evidence.read_json(read(folder / "candidate.json")), "events": events, "result": result}
    return node("const fs=require('fs'),R=require('./geometry-web/canvas_registry.js');"
                "process.stdout.write(JSON.stringify(R.verifySlotRun(JSON.parse(fs.readFileSync(0,'utf8')))));",
                env=env, payload=payload)


def capture(section, unit, mode, output):
    evidence.require(unit in (1, 2), "R386_SLOT_UNIT")
    identity, run_identity, pins = evidence.source_identity(), evidence.run_id(), slot_identity(section)
    env = scope_environment(mode)
    output.mkdir(parents=True, exist_ok=False)
    subprocess.run(["node", "geometry-web/canvas_registry.js", "placement-candidate", "--root", str(ROOT),
                    "--id", section, "--unit", str(unit), "--out", str(output / "candidate.json")],
                   cwd=ROOT, check=True)
    env["GEOMETRY_CANVAS_PLACEMENT_CANDIDATE"] = str(output / "candidate.json")
    plan = current_plan(env)
    evidence.save(output / "plan.json", plan)
    port = evidence.runtime_endpoint(env["GEOMETRY_TEST_URL"])
    env["GEOMETRY_FEEDBACK_DIR"] = str(Path(env["GEOMETRY_FEEDBACK_DIR"]).resolve())
    runtime_command = [sys.executable, "-B", "geometry-web/runtime_version.py", "--probe", str(port)]
    runtime_exit = evidence.capture(runtime_command, output / "runtime.stdout", output / "runtime.stderr", env)
    evidence.require(runtime_exit == 0, "R386_SLOT_RUNTIME_PROCESS")
    runtime = evidence.read_json(read(output / "runtime.stdout"))
    evidence.require(runtime.get("fresh") is True and runtime.get("schema") == "geometry-runtime/1",
                     "R386_SLOT_RUNTIME_NOT_FRESH")
    command = ["node", "geometry-web/cdp_test.js"]
    status = evidence.capture(command, output / "stdout.log", output / "stderr.log", env)
    receipt = {"schema": "geometry-canvas-slot-capture/1", **identity, **run_identity, **pins,
               "unit": unit, "slot": unit, "mode": mode, "command": command, "process_exit": status,
               "runtime_command": ["<python>", *runtime_command[1:]], "runtime_exit": runtime_exit,
               "runtime_fresh": runtime["fresh"], "runtime_version": runtime["version"],
               "execution_root": str(ROOT), "candidate_sha256": sha(read(output / "candidate.json")),
               "plan_sha256": plan["sha256"], "capture_verified": False, "acceptance": False,
               "environment": {name: env.get(name) for name in ("GEOMETRY_TEST_URL", "GEOMETRY_FEEDBACK_DIR",
                   "GEOMETRY_CHROME", "GEOMETRY_CHROME_FLAGS", "GEOMETRY_CDP_PORT", "GEOMETRY_CDP_SHARD",
                   "GEOMETRY_CANVAS_PLACEMENT_CANDIDATE")},
               "files": {name: sha(read(output / name)) for name in RAW_FILES}}
    evidence.save(output / "manifest.json", receipt)
    evidence.require(status == 0, "R386_SLOT_PROCESS_FAILED: " + str(status))
    # No claimed success is written until the original per-run gates validate.
    events, result = evidence.trace(read(output / "stdout.log"))
    candidate_receipt = {**receipt, "capture_verified": True, "scope": result["scope"],
                         "sections": result["sections"], "assertions": result["passedAssertions"]}
    verified = verify_run(candidate_receipt, output, env)
    evidence.require(evidence.source_identity() == identity and current_plan(env) == plan
                     and slot_identity(section) == pins and evidence.runtime_version() == runtime["version"],
                     "R386_SLOT_SOURCE_CHANGED")
    receipt.update(candidate_receipt, verified=verified)
    evidence.save(output / "manifest.json", receipt)
    print(json.dumps({"capture_verified": True, "acceptance": False, "unit": unit, "mode": mode}, ensure_ascii=False))


def mutation_result(raw):
    lines = [line.removeprefix("CANVAS_SLOT_MUTATION_RESULT ") for line in raw.decode("utf-8").splitlines()
             if line.startswith("CANVAS_SLOT_MUTATION_RESULT ")]
    evidence.require(len(lines) == 1, "R386_SLOT_MUTATION_RESULT_COUNT")
    return evidence.read_json(lines[0])


def verify_phase(result, status, control, phase):
    expected_exit = 1 if phase == "withdrawn" else 0
    test_id, variant, oracle = control
    evidence.require(type(status) is int and status == expected_exit, "R386_SLOT_MUTATION_EXIT")
    evidence.require(result.get("schema") == "geometry-canvas-slot-probe/1" and result.get("completed") is True
                     and result.get("infrastructureError") is False and result.get("skipped") == [],
                     "R386_SLOT_MUTATION_INFRASTRUCTURE")
    evidence.require(result.get("mutation") == (variant if phase == "withdrawn" else "none"),
                     "R386_SLOT_MUTATION_VARIANT")
    tests = result.get("tests", [])
    evidence.require([row.get("id") for row in tests] == [row[0] for row in CONTROLS], "R386_SLOT_MUTATION_TEST_SET")
    failures = [row for row in tests if row.get("passed") is False]
    evidence.require(all(type(row.get("passed")) is bool for row in tests), "R386_SLOT_MUTATION_VERDICT")
    evidence.require(all(set(row) == {"id", "passed", "oracle"} and (not row["passed"] or row["oracle"] is None)
                         for row in tests), "R386_SLOT_MUTATION_VERDICT")
    if phase == "withdrawn":
        evidence.require(failures == [{"id": test_id, "passed": False, "oracle": oracle}],
                         "R386_SLOT_MUTATION_WRONG_ORACLE")
    else:
        evidence.require(not failures, "R386_SLOT_MUTATION_BASELINE_FAILED")
    evidence.require(type(result.get("passedAssertions")) is int and result["passedAssertions"] == 2 - expected_exit
                     and type(result.get("failedAssertions")) is int and result["failedAssertions"] == expected_exit
                     and isinstance(result.get("browserVersion"), str) and result["browserVersion"],
                     "R386_SLOT_MUTATION_COUNTS")
    return {"exit": status, "tests": 2, "passed": 2 - expected_exit, "failed": expected_exit,
            "skipped": 0, "infrastructureError": False,
            "failedTest": test_id if expected_exit else None, "oracle": oracle if expected_exit else None}


def variant_hashes(variant):
    raw = read(ROOT / "geometry-web/canvas_registry.js").replace(b"\r\n", b"\n")
    source = raw.decode("utf-8")
    if variant != "none":
        evidence.require(variant in ANCHORS, "R386_SLOT_MUTATION_VARIANT")
        before, after = ANCHORS[variant]
        evidence.require(source.count(before) == 1, "R386_SLOT_MUTATION_ANCHOR_NOT_UNIQUE")
        source = source.replace(before, after)
    return sha(raw), sha(source.encode("utf-8"))


def validate_mutations(receipt, reader):
    evidence.require(receipt.get("schema") == "geometry-canvas-slot-mutations/1"
                     and receipt.get("acceptance") is False
                     and [row.get("id") for row in receipt.get("rows", [])] == [row[0] for row in CONTROLS],
                     "R386_SLOT_MUTATION_SCHEMA")
    wanted = {"manifest.json"}
    for row, control in zip(receipt["rows"], CONTROLS):
        for phase in ("baseline", "withdrawn", "restored"):
            item = row[phase]
            prefix = control[0] + "/" + phase
            variant = control[1] if phase == "withdrawn" else "none"
            evidence.require(item.get("stdout") == prefix + ".stdout" and item.get("stderr") == prefix + ".stderr"
                             and item.get("command") == ["node", ".github/scripts/canvas_slot_probe.cjs", variant],
                             "R386_SLOT_MUTATION_RAW_PATH")
            stdout, stderr = reader(item["stdout"]), reader(item["stderr"])
            expected_files = {"mutations/" + item["stdout"]: sha(stdout), "mutations/" + item["stderr"]: sha(stderr)}
            evidence.require(item.get("files") == expected_files and sha(stdout) == item["stdoutSha256"]
                             and sha(stderr) == item["stderrSha256"], "R386_SLOT_MUTATION_RAW_HASH")
            result = mutation_result(stdout)
            checked = verify_phase(result, item["exit"], control, phase)
            evidence.require(all(item.get(key) == value for key, value in checked.items()),
                             "R386_SLOT_MUTATION_FAKE_SUMMARY")
            original_hash, mutation_hash = variant_hashes(variant)
            evidence.require(result.get("registrySourceSha256") == item.get("registrySourceSha256") == original_hash
                             and result.get("mutationSourceSha256") == item.get("mutationSourceSha256") == mutation_hash,
                             "R386_SLOT_MUTATION_SOURCE_HASH")
            wanted.update((item["stdout"], item["stderr"]))
    return wanted


def verify_mutation_archive(artifact, mutation_file):
    evidence.require(mutation_file == "mutations/manifest.json", "R386_SLOT_MUTATION_MANIFEST_PATH")
    with zipfile.ZipFile(artifact) as archive:
        entries = archive.infolist()
        names = [entry.filename for entry in entries if not entry.is_dir()]
        evidence.require(len(names) == len(set(names)), "R386_SLOT_ZIP_DUPLICATE")

        def raw(name):
            info = archive.getinfo(name)
            evidence.require(not info.is_dir() and info.file_size <= 16 * 1024 * 1024
                             and (info.external_attr >> 16) & 0o170000 != 0o120000, "R386_SLOT_ZIP_RAW")
            return archive.read(info)

        receipt = evidence.read_json(raw(mutation_file))
        wanted = validate_mutations(receipt, lambda name: raw("mutations/" + name))
        evidence.require({name for name in names if name.startswith("mutations/")}
                         == {"mutations/" + name for name in wanted}, "R386_SLOT_MUTATION_FILE_SET")
    return {"schema": "geometry-canvas-slot-mutation-verification/1", "rows": len(CONTROLS),
            "exitCodes": [[0, 1, 0] for _ in CONTROLS], "acceptance": False}


def run_probe(variant, stdout, stderr):
    command = ["node", ".github/scripts/canvas_slot_probe.cjs", variant]
    with stdout.open("wb") as out, stderr.open("wb") as err:
        process = subprocess.Popen(command, cwd=ROOT, stdout=out, stderr=err, start_new_session=True)
        try:
            return process.wait(timeout=60)
        except subprocess.TimeoutExpired:
            # Kill only this probe's fresh process group, including its Chrome.
            os.killpg(process.pid, signal.SIGKILL)
            process.wait()
            raise ValueError("R386_SLOT_MUTATION_CHILD_TIMEOUT_60_SECONDS")


def mutations(section, output):
    identity, run_identity, pins = evidence.source_identity(), evidence.run_id(), slot_identity(section)
    scope_environment("full")
    output.mkdir(parents=True, exist_ok=False)
    rows = []
    for control in CONTROLS:
        row = {"id": control[0]}
        for phase in ("baseline", "withdrawn", "restored"):
            variant = control[1] if phase == "withdrawn" else "none"
            prefix = control[0] + "/" + phase
            stdout, stderr = output / (prefix + ".stdout"), output / (prefix + ".stderr")
            stdout.parent.mkdir(parents=True, exist_ok=True)
            status = run_probe(variant, stdout, stderr)
            raw = read(stdout)
            print(raw.decode("utf-8"), end="", flush=True)
            result = mutation_result(raw)
            checked = verify_phase(result, status, control, phase)
            checked.update(stdout=prefix + ".stdout", stderr=prefix + ".stderr",
                           stdoutSha256=sha(raw), stderrSha256=sha(read(stderr)),
                           registrySourceSha256=result["registrySourceSha256"],
                           mutationSourceSha256=result["mutationSourceSha256"],
                           command=["node", ".github/scripts/canvas_slot_probe.cjs", variant],
                           files={"mutations/" + prefix + ".stdout": sha(raw),
                                  "mutations/" + prefix + ".stderr": sha(read(stderr))})
            row[phase] = checked
        rows.append(row)
    evidence.require(evidence.source_identity() == identity and slot_identity(section) == pins,
                     "R386_SLOT_SOURCE_CHANGED")
    receipt = {"schema": "geometry-canvas-slot-mutations/1", **identity, **run_identity, **pins,
               "acceptance": False, "rows": rows}
    validate_mutations(receipt, lambda name: read(output / name))
    evidence.save(output / "manifest.json", receipt)
    print(json.dumps({"mutations_verified": True, "acceptance": False, "exitCodes": [[0, 1, 0] for _ in rows]}))


def expected_artifact_names(section, attempt):
    prefix = "canvas-slot-" + section + "-" + str(attempt) + "-"
    return {prefix + "slot" + str(unit) + "-" + mode: "slot" + str(unit) + "/" + mode
            for unit in (1, 2) for mode in MODES} | {prefix + "mutations": "mutations"}


def check_identity(receipt, expected, pins):
    for key in IDENTITY_FIELDS:
        evidence.require(receipt.get(key) == expected[key], "R386_SLOT_IDENTITY: " + key)
    for key in PIN_FIELDS:
        evidence.require(receipt.get(key) == pins[key], "R386_SLOT_PIN: " + key)


def make_zip(folder, output):
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(folder.rglob("*")):
            evidence.require(not path.is_symlink(), "R386_SLOT_ARCHIVE_SYMLINK")
            if not path.is_file():
                continue
            info = zipfile.ZipInfo(path.relative_to(folder).as_posix(), (1980, 1, 1, 0, 0, 0))
            info.external_attr = 0o100644 << 16
            info.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(info, read(path))


def assemble(section, artifacts, output):
    expected = {**evidence.source_identity(), **evidence.run_id()}
    pins = slot_identity(section)
    names = expected_artifact_names(section, expected["run_attempt"])
    evidence.require(set(path.name for path in artifacts.iterdir()) == set(names), "R386_SLOT_ARTIFACT_SET")
    output.mkdir(parents=True, exist_ok=False)
    captures = []
    for name, destination in sorted(names.items()):
        folder = artifacts / name
        evidence.require(folder.is_dir() and not folder.is_symlink(), "R386_SLOT_ARTIFACT_DIRECTORY")
        receipt = evidence.read_json(read(folder / "manifest.json"))
        check_identity(receipt, expected, pins)
        if destination != "mutations":
            unit, mode = int(destination[4]), destination.split("/")[1]
            evidence.require(receipt.get("unit") == unit and receipt.get("mode") == mode
                             and receipt.get("capture_verified") is True, "R386_SLOT_CAPTURE_LOCATION")
            evidence.require(set(path.name for path in folder.iterdir()) == {*RAW_FILES, "manifest.json"},
                             "R386_SLOT_CAPTURE_FILE_SET")
            verify_run(receipt, folder)
            captures.append({"unit": unit, "mode": mode, "manifest": destination + "/manifest.json",
                             "sha256": sha(read(folder / "manifest.json"))})
        else:
            wanted = validate_mutations(receipt, lambda name: read(folder / name))
            actual = {path.relative_to(folder).as_posix() for path in folder.rglob("*") if path.is_file()}
            evidence.require(actual == wanted, "R386_SLOT_MUTATION_FILE_SET")
        for path in folder.rglob("*"):
            evidence.require(not path.is_symlink(), "R386_SLOT_RAW_SYMLINK")
        shutil.copytree(folder, output / destination)
    proof = {"schema": "geometry-canvas-slot-proof/1", **expected, **pins, "acceptance": False,
             "captures": captures, "mutationProof": {"file": "mutations/manifest.json",
                                                       "sha256": sha(read(output / "mutations/manifest.json"))}}
    evidence.save(output / "proof.json", proof)
    archive = output.with_suffix(".verify.zip")
    make_zip(output, archive)
    try:
        verified = node("const R=require('./geometry-web/canvas_registry.js');"
                        "process.stdout.write(JSON.stringify(R.verifySlotProof(process.cwd(),process.argv[1],process.argv[2])));",
                        section, archive)
    finally:
        archive.unlink(missing_ok=True)
    evidence.require({**evidence.source_identity(), **evidence.run_id()} == expected and slot_identity(section) == pins,
                     "R386_SLOT_SOURCE_CHANGED")
    print(json.dumps({"capture_verified": True, "acceptance": False, "proof": verified}, ensure_ascii=False))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("run", "mutations", "assemble", "verify-mutations"))
    parser.add_argument("--section")
    parser.add_argument("--unit", type=int, choices=(1, 2))
    parser.add_argument("--scope", choices=MODES)
    parser.add_argument("--artifacts", type=Path)
    parser.add_argument("--out", type=Path)
    parser.add_argument("--artifact", type=Path)
    parser.add_argument("--mutation-file", default="mutations/manifest.json")
    args = parser.parse_args()
    if args.mode == "verify-mutations":
        evidence.require(args.artifact is not None, "R386_SLOT_ARTIFACT_REQUIRED")
        print(json.dumps(verify_mutation_archive(args.artifact, args.mutation_file), ensure_ascii=False))
        raise SystemExit(0)
    evidence.require(args.section is not None and args.out is not None, "R386_SLOT_OUTPUT_AND_SECTION_REQUIRED")
    if args.mode == "run":
        capture(args.section, args.unit, args.scope, args.out.resolve())
    elif args.mode == "mutations":
        mutations(args.section, args.out.resolve())
    else:
        evidence.require(args.artifacts is not None, "R386_SLOT_ARTIFACTS_REQUIRED")
        assemble(args.section, args.artifacts.resolve(), args.out.resolve())
