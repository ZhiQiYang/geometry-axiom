#!/usr/bin/env python3
"""Eight physical R13 host withdrawals in an isolated checkout; never mutate the caller.

Run after T and P with a fresh model-base (GEOMETRY_MODEL_BASE may select it)
and --out outside the checkout. A kill requires one completed named assertion
failure between two green runs of the same exact selected tests. No browser or
CI claim is made.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile

import binaries

ROOT = Path(__file__).resolve().parents[1]
BASE = "b3c4b981bb96b118c1c05b7a1bd98062d710c8b2"
HOST_TEST = "tests/test_r13_reconstruction_store.js"
K1 = "![GRID_DRAFTS_FORMAT,CARD_FORMAT, ROOM_CANDIDATE_FORMAT, PROFILE_RUN_FORMAT, RECONSTRUCTION_FORMAT].includes(manifest.format)"
R06 = "if (hasRoomCandidate !== declaresRoomCandidate || hasRoomCandidate && ![ROOM_CANDIDATE_FORMAT, PROFILE_RUN_FORMAT, RECONSTRUCTION_FORMAT].includes(manifest.format))"
FAULTS = (
    ("R13_K1_STALE_FORMAT_DEFINITION", "tests/mutate_k1_frontend.py", K1,
     K1.replace(", RECONSTRUCTION_FORMAT", ""), "R13_H23", HOST_TEST, "R13_K1_FORMAT_WITHDRAWAL_ANCHOR"),
    ("R13_R06_STALE_FORMAT_DEFINITION", "tests/bay_repeat_mutations.json", R06,
     R06.replace(", RECONSTRUCTION_FORMAT", ""), "R13_H24", HOST_TEST, "R13_R06_FORMAT_WITHDRAWAL_ANCHOR"),
    ("K1_OLD_FORMAT_GUARD_WITHDRAWAL", "geometry-web/project-store.js", K1, "false", "T17b",
     "tests/test_cutting_project_store.js", "Missing expected rejection"),
    ("R06_REQUIRE_UNRELATED_ROOM_DRAFT", "geometry-web/project-store.js", R06,
     R06[:-1] + " || !hasRoomCandidate && manifest.format === ROOM_CANDIDATE_FORMAT)",
     "R06 integration shares format 19", "tests/test_assembly_main_integration.js", "KILLER[r06-main:repeat-only-format19]"),
    ("R13_UNDO_ZERO_DROP_HIGHWATER", "geometry-web/project-store.js",
     "const reconstruction=Features.Reconstruction.preserveHighwater(restoredReconstruction,reconstructionHighwater);",
     "const reconstruction=restoredReconstruction;", "R13_H20", HOST_TEST, "R13_UNDO_ZERO_FORMAT"),
    ("R13_RECOVERY_RAW_FLUSH_REMOVED", "geometry-web/reference-workspace.js",
     "if(!transactionOwner){window.AssemblyWorkspace?.flush();window.InfiniteGridWorkspace?.flush();window.ReconstructionWorkspace?.flush();}",
     "if(!transactionOwner){window.AssemblyWorkspace?.flush();window.InfiniteGridWorkspace?.flush();}",
     "R13_H21", HOST_TEST, "R13_RECOVERY_LATEST_RAW"),
    ("R13_LEGACY_GRID_OWNER_BOUND_REMOVED", "geometry-web/feature-attachments.js",
     "const MAX_BYTES = 128 * 1024,", "const MAX_BYTES = 1024 * 1024,", "R13_H22", HOST_TEST,
     "R13_RECONSTRUCTION_EXCEEDS_LEGACY_BOUND"),
    ("R13_OWNER_SCOPE_SELECTION_REMOVED", "geometry-web/reference-workspace.js",
     "const scopeMode=reconstructionScopeMode(R.plan(original,recordId),options);",
     "const scopeMode=R.plan(original,recordId).completeness;", "R13_H25", HOST_TEST, "R13_SCOPE_SELECTION_REQUIRED"),
)


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def identity(path: Path) -> dict:
    raw = path.read_bytes()
    return {"bytes": len(raw), "sha256": sha(raw)}


def copy_sources(work: Path) -> dict:
    """Include the actual JS/Python dependency tree plus frozen test inputs."""
    paths = set()
    for area in ("geometry-web", "geometry-core", "geometry-app", "geometry-templates", "tests"):
        for source in (ROOT / area).rglob("*"):
            if not source.is_file():
                continue
            relative = source.relative_to(ROOT)
            if area == "geometry-web":
                if source.parent != ROOT / area and relative.as_posix() != "geometry-web/vendor/fflate/umd/index.js":
                    continue
                if source.suffix not in (".js", ".cjs", ".mjs", ".py"):
                    continue
            elif area == "tests":
                if source.parent != ROOT / area and not relative.as_posix().startswith(("tests/fixtures/", "tests/oracles/")):
                    continue
                if source.suffix not in (".js", ".cjs", ".json", ".py", ".gcanvas"):
                    continue
            elif source.suffix not in (".js", ".py"):
                continue
            paths.add(source)
    paths.add(ROOT / "公理層.md")
    for source in sorted(paths):
        target = work / source.relative_to(ROOT)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
    return {source.relative_to(ROOT).as_posix(): identity(work / source.relative_to(ROOT)) for source in sorted(paths)}


def execute(work: Path, out: Path, name: str, phase: str, pattern: str, test: str, env: dict) -> tuple[dict, str]:
    command = ["node", "--test", "--test-reporter=tap", "--test-name-pattern=^" + pattern + " ", test]
    run = subprocess.run(command, cwd=work, env=env, capture_output=True, timeout=60)
    stem = out / (name + "-" + phase)
    stem.with_suffix(".stdout").write_bytes(run.stdout)
    stem.with_suffix(".stderr").write_bytes(run.stderr)
    text = (run.stdout + run.stderr).decode("utf-8")
    counts = {key: int(value) for key, value in re.findall(r"^# (tests|pass|fail|cancelled|skipped|todo) (\d+)$", text, re.M)}
    result = {"phase": phase, "command": command, "exit": run.returncode, "counts": counts,
              "stdoutBytes": len(run.stdout), "stdoutSha256": sha(run.stdout),
              "stderrBytes": len(run.stderr), "stderrSha256": sha(run.stderr)}
    stem.with_suffix(".json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return result, text


def completed(result: dict, fail: bool, total: int) -> bool:
    counts = result["counts"]
    return result["exit"] == int(fail) and counts.get("tests") == total and counts.get("fail") == int(fail) and counts.get("pass") == total - int(fail) and all(
        counts.get(key) == 0 for key in ("cancelled", "skipped", "todo"))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    out = args.out.resolve()
    if out == ROOT or ROOT in out.parents or out.exists() and (not out.is_dir() or any(out.iterdir())):
        parser.error("--out must be an empty directory outside the checkout")
    info = binaries.inspect_one(binaries.BY_NAME["model-base"], path=os.environ.get("GEOMETRY_MODEL_BASE"))
    if info.state != "fresh":
        parser.error("a fresh model-base is required: " + info.reason)
    out.mkdir(parents=True, exist_ok=True)
    env = {**os.environ, "GEOMETRY_MODEL_BASE": str(info.path), "NO_COLOR": "1"}
    summary = {"schema": "r13-storage-local-withdrawals/2", "sourceBase": BASE, "acceptance": False,
               "binary": {"path": str(info.path), **identity(info.path)}, "results": []}
    with tempfile.TemporaryDirectory(prefix="r13-storage-withdrawals-") as directory:
        work = Path(directory)
        sources = copy_sources(work)
        (out / "source-index.json").write_text(json.dumps(sources, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        summary["sourceIndexSha256"] = sha((out / "source-index.json").read_bytes())
        for name, file, before, after, pattern, test, assertion in FAULTS:
            total = 2 if name == "R06_REQUIRE_UNRELATED_ROOM_DRAFT" else 1
            target = work / file
            original = target.read_bytes()
            if original.count(before.encode("utf-8")) != 1:
                raise RuntimeError(name + ": mutation anchor is missing or not unique")
            baseline, _ = execute(work, out, name, "baseline", pattern, test, env)
            if not completed(baseline, False, total):
                raise RuntimeError(name + ": baseline did not complete the exact selected green tests")
            changed = original.replace(before.encode("utf-8"), after.encode("utf-8"), 1)
            try:
                target.write_bytes(changed)
                withdrawn, text = execute(work, out, name, "withdrawn", pattern, test, env)
            finally:
                target.write_bytes(original)
            restored, _ = execute(work, out, name, "restored", pattern, test, env)
            killed = completed(withdrawn, True, total) and assertion in text and "ERR_ASSERTION" in text and "AssertionError" in text and not any(
                marker in text for marker in ("MODULE_NOT_FOUND", "SyntaxError", "ReferenceError", "TypeError:", "ERR_MODULE_NOT_FOUND", "FATAL ERROR"))
            valid = killed and completed(restored, False, total) and target.read_bytes() == original
            summary["results"].append({"name": name, "file": file, "before": before, "after": after, "assertion": assertion,
                                       "sourceSha256": sha(original), "faultSha256": sha(changed),
                                       "selectedTests": total,
                                       "exitCodes": [baseline["exit"], withdrawn["exit"], restored["exit"]], "verified": valid,
                                       "runs": [baseline, withdrawn, restored]})
            (out / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            if not valid:
                raise RuntimeError(name + ": no named assertion kill plus exact-byte restoration")
            print(name + " 0/1/0", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
