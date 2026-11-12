"""R14 H1 named product reversals in a disposable source copy.

Run after the normal host regression is green:
  GEOMETRY_TEST_BRIDGE=/tmp/.../bridge python tests/mutation_r14_host.py --out /tmp/r14-host-mutations

The shared checkout, golden files and official mutation ledger are never edited.
Each fault must produce its named assertion, with zero skip/crash, between two
green executions of the same test. Native advertising is rebuilt from the fault.
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

ROOT = Path(__file__).resolve().parents[1]
BASE = "7a2b16d4f16d6e208461cf8b3dda09cdf89a0386"
PROJECT = "geometry-web/project-store.js"
FAULTS = (
    ("R14_H_FULL_CAPABILITY_REMOVED", "geometry-web/engineering_bridge.inc",
     r'\"grid-subdivision-rules/1\",\"grid-subdivision-rules/2\",',
     r'\"grid-subdivision-rules/1\",', "R14H01", "R14_HOST_FULL_CAPABILITY"),
    ("R14_H_REPLAY_PANEL_REQUIREMENT_FORGOTTEN", PROJECT,
     "if (owner.panel && owner.hasRules) usesPanelSubdivision = true;",
     "if (owner.panel && owner.hasRules) usesPanelSubdivision = false;", "R14H04", "R14_HOST_REPLAY_V2_REQUIRED"),
    ("R14_H_OLD_SERVICE_GUARD_BYPASSED", PROJECT,
     "required.some(capability => !available.includes(capability))",
     'required.some(capability => capability !== SUBDIVISION_V2_CAPABILITY && !available.includes(capability))',
     "R14H07", "R14_HOST_OLD_SERVICE_REJECTS"),
    ("R14_H_MODEL_V2_CLAIM_ACCEPTED", PROJECT,
     "if (m.capabilities.some(isSubdivisionCapability) || sceneCapabilities(p.definitions.base_scene).some(isSubdivisionCapability))",
     "if (m.capabilities.includes(SUBDIVISION_CAPABILITY) || sceneCapabilities(p.definitions.base_scene).some(isSubdivisionCapability))",
     "R14H12", "R14_HOST_MODEL_CLAIM_REFUSES_V2"),
    ("R14_H_SNAPSHOT_CAPABILITY_DROPPED", PROJECT,
     "if (manifest.scenarioCatalog?.scenarios.some(s => projectCapabilities(s.snapshot.projectManifest,s.snapshot.worldScene).includes(SUBDIVISION_V2_CAPABILITY))) required.add(SUBDIVISION_V2_CAPABILITY);",
     "// R14 fault: snapshot capability is not propagated.", "R14H13", "R14_HOST_NESTED_CAPABILITY"),
    ("R14_H_SCENARIO_VERIFIER_V2_REMOVED", "geometry-web/scenario_verify.py",
     '{"grid-subdivision-rules/1", "grid-subdivision-rules/2", "assembly-bay-repeat/1",',
     '{"grid-subdivision-rules/1", "assembly-bay-repeat/1",', "R14H15", "R14_HOST_SCENARIO_VERIFIER"),
    ("R14_H_PYTHON_V1_REQUIREMENT_INVENTED", "geometry-app/geometry_app/model_common.py",
     "result.add(GRID_SUBDIVISION_V2_CAPABILITY if GRID_SUBDIVISION_V2_CAPABILITY in declared else GRID_SUBDIVISION_CAPABILITY)",
     "result.add(GRID_SUBDIVISION_CAPABILITY)", "R14H15", "R14_HOST_SCENARIO_VERIFIER"),
)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def run(command, cwd, env, target, timeout=120):
    process = subprocess.run(command, cwd=cwd, env=env, capture_output=True, timeout=timeout)
    target.with_suffix(".stdout").write_bytes(process.stdout)
    target.with_suffix(".stderr").write_bytes(process.stderr)
    receipt = {"command": command, "exit": process.returncode,
               "stdout_bytes": len(process.stdout), "stdout_sha256": digest(process.stdout),
               "stderr_bytes": len(process.stderr), "stderr_sha256": digest(process.stderr)}
    target.with_suffix(".json").write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    return process, receipt


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--only", choices=[row[0] for row in FAULTS])
    args = parser.parse_args()
    out = args.out.resolve()
    out.mkdir(parents=True, exist_ok=True)
    bridge = os.environ.get("GEOMETRY_TEST_BRIDGE")
    if not bridge:
        raise SystemExit("GEOMETRY_TEST_BRIDGE must identify the fresh green bridge")
    bridge = str(Path(bridge).resolve())
    faults = [row for row in FAULTS if args.only is None or row[0] == args.only]
    receipts = []
    with tempfile.TemporaryDirectory(prefix="r14-host-reversals-") as directory:
        work = Path(directory)
        for name in ("geometry-web", "geometry-core", "geometry-app", "geometry-templates", "geometry-guide"):
            shutil.copytree(ROOT / name, work / name, ignore=shutil.ignore_patterns("__pycache__", "node_modules"))
        for name in ("current_geometry.c", "公理層.md"):
            shutil.copy2(ROOT / name, work / name)
        (work / "tests").mkdir()
        for name in ("__init__.py", "binaries.py", "_bridge.py", "test_r14_host.js"):
            shutil.copy2(ROOT / "tests" / name, work / "tests" / name)
        env = {**os.environ, "GEOMETRY_TEST_BRIDGE": bridge, "PYTHONDONTWRITEBYTECODE": "1", "NO_COLOR": "1"}
        env.pop("GEOMETRY_R14_EVIDENCE_DIR", None)
        for name, relative, old, new, case, assertion in faults:
            location = work / relative
            original = location.read_bytes()
            old_bytes, new_bytes = old.encode(), new.encode()
            if original.count(old_bytes) != 1:
                raise RuntimeError(f"{name}: expected exactly one product anchor")
            folder = out / name
            folder.mkdir(exist_ok=True)
            command = ["node", "--test", "--test-reporter=tap", "--test-name-pattern", case, "tests/test_r14_host.js"]
            baseline, baseline_receipt = run(command, work, env, folder / "baseline")
            if baseline.returncode or b"# tests 1\n" not in baseline.stdout or b"# skipped 0\n" not in baseline.stdout:
                raise RuntimeError(f"{name}: baseline is not one real green test")
            try:
                location.write_bytes(original.replace(old_bytes, new_bytes))
                fault_env = dict(env)
                if relative.endswith(".inc"):
                    binaries = work / "fault-binaries"
                    code = "from pathlib import Path; from tests import binaries; import sys; binaries.OUT_DIR=Path(sys.argv[1]); r=binaries.build_one(binaries.BY_NAME['bridge']); print(r); sys.exit(0 if r.ok else 1)"
                    compiled, _ = run([sys.executable, "-c", code, str(binaries)], work, env, folder / "compile", timeout=180)
                    if compiled.returncode:
                        raise RuntimeError(f"{name}: mutant compilation failed, not killed")
                    fault_env["GEOMETRY_TEST_BRIDGE"] = str(binaries / ("bridge.exe" if os.name == "nt" else "bridge"))
                fault, fault_receipt = run(command, work, fault_env, folder / "fault")
                killed = (fault.returncode == 1 and assertion.encode() in fault.stdout
                          and b"# tests 1\n" in fault.stdout and b"# fail 1\n" in fault.stdout
                          and b"# skipped 0\n" in fault.stdout and b"ERR_ASSERTION" in fault.stdout)
                if not killed:
                    raise RuntimeError(f"{name}: no matching assertion kill; inspect fault output")
            finally:
                location.write_bytes(original)
            restored, restored_receipt = run(command, work, env, folder / "restored")
            if restored.returncode or location.read_bytes() != original or b"# skipped 0\n" not in restored.stdout:
                raise RuntimeError(f"{name}: restored product is not byte-identical and green")
            receipt = {"name": name, "verdict": "killed", "source": relative,
                       "baseline_source_sha256": digest(original), "fault_source_sha256": digest(original.replace(old_bytes, new_bytes)),
                       "assertion": assertion, "test": case, "exits": [baseline.returncode, fault.returncode, restored.returncode],
                       "baseline": baseline_receipt, "fault": fault_receipt, "restored": restored_receipt}
            receipts.append(receipt)
            print(name + " 0 -> 1 -> 0", flush=True)
    summary = {"base": BASE, "test_sha256": digest((ROOT / "tests/test_r14_host.js").read_bytes()),
               "normal_bridge_sha256": digest(Path(bridge).read_bytes()), "killed": len(receipts), "results": receipts}
    (out / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
