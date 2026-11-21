"""Measure one declared canvas module in real CI; never issue full acceptance.

The official artifact ZIP is subsequently imported by canvas_registry.js.
No estimated cost, golden, fragment or product source is written here.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys

import canvas_evidence as evidence

ROOT = evidence.ROOT


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def run(section, output):
    evidence.require(re.fullmatch(r"P[0-9]+[A-Z]?", section) is not None, "R386_CANVAS_SECTION_ID")
    identity, run_identity = evidence.source_identity(), evidence.run_id()
    query = ("const R=require('./geometry-web/canvas_registry.js');"
             "const r=R.load(process.cwd(),{allowCandidates:true});"
             "const row=r.extensions.find(x=>x.id===process.argv[1])||r.drivers.find(x=>x.id===process.argv[1]);"
             "R.requireThat(row,'R386_CANVAS_MODULE_UNKNOWN');"
             "process.stdout.write(JSON.stringify(row));")
    row = evidence.read_json(subprocess.check_output(["node", "-e", query, section], cwd=ROOT))
    if row["execution"]["kind"] == "driver":
        return run_driver(section, row, output, identity, run_identity)
    module = ROOT / row["execution"]["module"]
    source_query = ("const R=require('./geometry-web/canvas_registry.js');"
                    "process.stdout.write(R.moduleSourceHash(process.cwd(),process.argv[1]));")
    def module_source_hash():
        return subprocess.check_output(["node", "-e", source_query, row["execution"]["module"]], cwd=ROOT, text=True).strip()
    module_hash = module_source_hash()
    output.mkdir(parents=True, exist_ok=False)
    env = dict(os.environ)
    for key in tuple(env):
        if re.fullmatch(r"GEOMETRY_.*_(?:ONLY|CASE|CASES)", key) or key in (
                "GEOMETRY_CDP_SHARD", "GEOMETRY_CDP_FROM_P31", "GEOMETRY_CDP_UPDATE_GOLDEN",
                "GEOMETRY_CANVAS_PLACEMENT_CANDIDATE"):
            env.pop(key)
    env.update(GEOMETRY_CANVAS_MODULE_ONLY="1", GEOMETRY_CANVAS_MODULE=section,
               PYTHONDONTWRITEBYTECODE="1")
    port = evidence.runtime_endpoint(env["GEOMETRY_TEST_URL"])
    runtime_command = [sys.executable, "-B", "geometry-web/runtime_version.py", "--probe", str(port)]
    runtime_exit = evidence.capture(runtime_command, output / "runtime.stdout", output / "runtime.stderr", env)
    evidence.require(runtime_exit == 0, "R386_CANVAS_MEASURE_RUNTIME")
    runtime = evidence.read_json((output / "runtime.stdout").read_bytes())
    evidence.require(runtime.get("fresh") is True and runtime.get("schema") == "geometry-runtime/1",
                     "R386_CANVAS_MEASURE_RUNTIME")
    command = ["node", "geometry-web/cdp_test.js"]
    status = evidence.capture(command, output / "stdout.log", output / "stderr.log", env)
    receipt = {"schema": "geometry-canvas-section-measurement/1", **identity, **run_identity,
               "module": row["execution"]["module"], "module_sha256": module_hash,
               "command": command, "process_exit": status, "runtime_fresh": runtime["fresh"],
               "runtime_version": runtime["version"], "capture_verified": False, "acceptance": False,
               "files": {name: sha((output / name).read_bytes()) for name in
                         ("stdout.log", "stderr.log", "runtime.stdout", "runtime.stderr")}}
    evidence.save(output / "manifest.json", receipt)
    evidence.require(status == 0, "R386_CANVAS_MEASURE_PROCESS_FAILED")
    evidence.require(evidence.source_identity() == identity and evidence.runtime_version() == runtime["version"]
                     and module_source_hash() == module_hash,
                     "R386_CANVAS_MEASURE_SOURCE_CHANGED")
    _, result = evidence.trace((output / "stdout.log").read_bytes())
    # Counts are observations from this run, not a prefilled candidate number.
    row["assertions"] = result.get("sections", {}).get(section)
    candidate = {**receipt, "capture_verified": True}
    verifier = ("const fs=require('fs'),R=require('./geometry-web/canvas_registry.js');"
                "const p=JSON.parse(fs.readFileSync(0,'utf8'));"
                "const m=R.verifyMeasurement(p.receipt,fs.readFileSync(p.output+'/stdout.log'),"
                "fs.readFileSync(p.output+'/stderr.log'),p.row,p.moduleHash);"
                "process.stdout.write(JSON.stringify(m));")
    measured = subprocess.run(["node", "-e", verifier], cwd=ROOT, input=json.dumps({
        "receipt": candidate, "output": str(output), "row": row, "moduleHash": module_hash}),
        text=True, capture_output=True, check=False)
    evidence.require(measured.returncode == 0, "R386_CANVAS_MEASURE_REJECTED: " + measured.stderr)
    evidence.save(output / "manifest.json", candidate)
    print(json.dumps({"capture_verified": True, "acceptance": False,
                      "measured": evidence.read_json(measured.stdout)}, ensure_ascii=False))


def clean_env():
    env = dict(os.environ)
    for key in tuple(env):
        if re.fullmatch(r"GEOMETRY_.*_(?:ONLY|CASE|CASES)", key) or key in (
                "GEOMETRY_CDP_SHARD", "GEOMETRY_CDP_FROM_P31", "GEOMETRY_CDP_UPDATE_GOLDEN",
                "GEOMETRY_CANVAS_PLACEMENT_CANDIDATE", "GEOMETRY_CANVAS_MODULE", "GEOMETRY_FRAMING_JIG_ARTIFACT_DIR"):
            env.pop(key)
    return env


def run_driver(section, row, output, identity, run_identity):
    """R445: reviewed CDP driver. Same partial capture contract as a module,
    but the driver's own flag selects it and every file it writes is kept."""
    identity_query = ("const R=require('./geometry-web/canvas_registry.js');"
                      "process.stdout.write(JSON.stringify(R.driverIdentity(process.cwd(),process.argv[1])));")
    def driver_identity():
        return evidence.read_json(subprocess.check_output(["node", "-e", identity_query, section], cwd=ROOT))
    driver = driver_identity()
    evidence.require(driver["driver"] == row["execution"]["driver"] and driver["flag"] == row["execution"]["flag"],
                     "R386_CANVAS_DRIVER_UNREVIEWED")
    output.mkdir(parents=True, exist_ok=False)
    outputs = output / "driver-outputs"
    outputs.mkdir()
    env = clean_env()
    env.update({driver["flag"]: "1", "GEOMETRY_FRAMING_JIG_ARTIFACT_DIR": str(outputs), "PYTHONDONTWRITEBYTECODE": "1"})
    port = evidence.runtime_endpoint(env["GEOMETRY_TEST_URL"])
    runtime_command = [sys.executable, "-B", "geometry-web/runtime_version.py", "--probe", str(port)]
    runtime_exit = evidence.capture(runtime_command, output / "runtime.stdout", output / "runtime.stderr", env)
    evidence.require(runtime_exit == 0, "R386_CANVAS_MEASURE_RUNTIME")
    runtime = evidence.read_json((output / "runtime.stdout").read_bytes())
    evidence.require(runtime.get("fresh") is True and runtime.get("schema") == "geometry-runtime/1",
                     "R386_CANVAS_MEASURE_RUNTIME")
    command = ["node", "geometry-web/cdp_test.js"]
    status = evidence.capture(command, output / "stdout.log", output / "stderr.log", env)
    produced = {path.relative_to(output).as_posix(): sha(path.read_bytes())
                for path in sorted(outputs.rglob("*")) if path.is_file() and not path.is_symlink()}
    evidence.require(all(not path.is_symlink() for path in outputs.rglob("*")), "R386_CANVAS_DRIVER_OUTPUT_HASH")
    receipt = {"schema": "geometry-canvas-driver-measurement/1", **identity, **run_identity, "id": section,
               "driver": driver["driver"], "driver_sha256": driver["sha256"], "dispatch_sha256": driver["dispatchSha256"],
               "flag": driver["flag"], "command": command, "process_exit": status, "runtime_fresh": runtime["fresh"],
               "runtime_version": runtime["version"], "capture_verified": False, "acceptance": False,
               "files": {name: sha((output / name).read_bytes()) for name in
                         ("stdout.log", "stderr.log", "runtime.stdout", "runtime.stderr")},
               "outputs": produced}
    evidence.save(output / "manifest.json", receipt)
    evidence.require(status == 0, "R386_CANVAS_MEASURE_PROCESS_FAILED")
    evidence.require(evidence.source_identity() == identity and evidence.runtime_version() == runtime["version"]
                     and driver_identity() == driver, "R386_CANVAS_MEASURE_SOURCE_CHANGED")
    _, result = evidence.trace((output / "stdout.log").read_bytes())
    row["assertions"] = result.get("sections", {}).get(section)
    candidate = {**receipt, "capture_verified": True}
    evidence.save(output / "manifest.json", candidate)
    # The importer's own verifier, over exactly the files that will be uploaded.
    verifier = ("const fs=require('fs'),path=require('path'),R=require('./geometry-web/canvas_registry.js');"
                "const p=JSON.parse(fs.readFileSync(0,'utf8')),m={};"
                "const walk=d=>{for(const n of fs.readdirSync(d)){const f=path.join(d,n);"
                "if(fs.lstatSync(f).isDirectory())walk(f);else m[path.relative(p.output,f).split(path.sep).join('/')]=fs.readFileSync(f);}};"
                "walk(p.output);"
                "process.stdout.write(JSON.stringify(R.verifyDriverMeasurement(m,p.row,R.driverIdentity(process.cwd(),p.row.id))));")
    measured = subprocess.run(["node", "-e", verifier], cwd=ROOT, input=json.dumps({"output": str(output), "row": row}),
                              text=True, capture_output=True, check=False)
    evidence.require(measured.returncode == 0, "R386_CANVAS_MEASURE_REJECTED: " + measured.stderr)
    print(json.dumps({"capture_verified": True, "acceptance": False,
                      "measured": evidence.read_json(measured.stdout)}, ensure_ascii=False))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--section", required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    run(args.section, args.out.resolve())
