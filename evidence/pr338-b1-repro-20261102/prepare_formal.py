"""Restore pinned original inputs, then run the unchanged F8 whole-memo driver in CI."""
import argparse
import hashlib
import io
import json
import os
from pathlib import Path, PurePosixPath
import shutil
import subprocess
import sys
import tarfile
import traceback
import zipfile

F8 = "75a1e93811a52b69385cbdaf6a09d773ed9052ad"
TARGET = "9230a3dc04233e50c0bf97141a7fbe692828b2ca"
TRAIN = "evidence/geo337-train-20261024"
ARCHIVE = TRAIN + "/full-R8-five-stage-raw/ORIGINAL_R8_FIVE_STAGE_RAW.tar.gz"
ARCHIVE_SHA = "4503955cefc6fb1a6491ad2a146c259e59a2185401d0fbebc09908a47e3bf9d0"
ORIGINAL_RECEIPT_SHA = "979680e78a381d28a6d1c6825b7b1b8af850bebec381ec3cee3ef42e9e46ea15"
MEMO_TOOLS = TRAIN + "/prepared-during-F8/memo-copy-v2/tools"
V4_SOURCE = TRAIN + "/current-R5-status/recorder-v5-originals/original-v4"
V3 = Path("/tmp/geo323-merge-20261023/acceptance-tools-v3")
V4 = Path("/tmp/geo323-train337-lineage-20261024/acceptance-tools-v4-scene-binding")
CAPTURE = Path("/workspace/geo288-main-merge-20261023/native-final-tools/capture.py")
MEMO = Path("/tmp/geo337-F8-memo-counterfactual-tools-v2-20261025")
PINS = {
    "capture.py": "c387835c03fce36be0861b7fa5228ae494ad2be94bfa9cd62d4f36b9782dc762",
    "v3/geo323_record.py": "8aa05afded8738078cb319606422270345abc0317257d63e8879009acaaabb9b",
    "v3/profile_linux.py": "0dda20c3d4de8c4472ed7f936fcf7bbc48c4adacfdc779bc2bda6e300a0c853c",
    "v3/verify_linux.py": "ccbce3a5d32bee81f22be31a31c1f771ca05c54f53f21e4d94b11b4a08b4534d",
    "v4/run.py": "d4a38b7b60ac698eba4a274c5d26c83684cd1c665b8399f5e47546befae1f70e",
    "v4/verify_linux.py": "c3db1834c49365a08ef5720d38156253a355e9f5d5db0239486013871d0e2cac",
}


def sha(data):
    return hashlib.sha256(data).hexdigest()


def dump(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main():
    if os.environ.get("GITHUB_ACTIONS") != "true":
        raise SystemExit("Formal build/test is authorized only in GitHub Actions")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    root, out = args.root.resolve(), args.out.resolve()
    repo = Path("/tmp/geo337-whole-memo-clean-F8")
    formal_r8 = Path("/tmp/g337323R8")
    result = {"schema": "pr338-original-whole-memo-ci/1", "ciExecutionHead": os.environ["GITHUB_SHA"],
              "ciRunId": os.environ["GITHUB_RUN_ID"], "actualProductExecutionSha": F8,
              "currentPrProductHead": TARGET, "originalR8OuterExitRetained": 1,
              "originalR8PerformanceResampled": False, "originalJudgesModified": False,
              "formalExecuted": False, "formalActualProcessExit": None, "b1Closed": False,
              "commands": [], "errors": []}

    def run(command, label, cwd=None, timeout=300):
        completed = subprocess.run(command, cwd=cwd, capture_output=True, timeout=timeout)
        streams = {}
        for kind, data in [("stdout", completed.stdout), ("stderr", completed.stderr)]:
            relative = label + "." + kind + ".bin"
            (out / relative).write_bytes(data)
            streams[kind] = {"path": relative, "bytes": len(data), "sha256": sha(data)}
        row = {"command": command, "cwd": str(cwd) if cwd else None,
               "actualProcessReturncode": completed.returncode, **streams}
        result["commands"].append(row)
        dump(out / "CI_RESULT.json", result)
        return completed

    try:
        source_status = json.loads((root / (TRAIN + "/review-unblock-20261029/B1_STATUS.json")).read_bytes())
        pins = {x["name"]: x["expected"] for x in source_status["requiredFiles"]}
        zipped = (out / "repro-input.zip").read_bytes()
        if sha(zipped) != os.environ["REPRO_ZIP_SHA"].removeprefix("sha256:"):
            raise RuntimeError("predecessor artifact digest mismatch")
        with zipfile.ZipFile(io.BytesIO(zipped)) as archive:
            reproduced = json.loads(archive.read("RESULT.json"))
            if not reproduced["allThreeExactOriginalBytesAndMode"] or reproduced["processExit"] != 0:
                raise RuntimeError("all three exact bytes/full modes required")
            elf_tar = archive.read("REPRODUCED_ELFS.tar")
            (out / "REPRODUCED_ELFS.input.tar").write_bytes(elf_tar)
            result["exactBytePredecessor"] = {"ciExecutionHead": reproduced["ciExecutionHead"],
                                               "zipSha256": sha(zipped), "elfTarSha256": sha(elf_tar)}
        archived_bytes = (root / ARCHIVE).read_bytes()
        if sha(archived_bytes) != ARCHIVE_SHA:
            raise RuntimeError("original R8 archive changed")
        (out / "ORIGINAL_R8_FIVE_STAGE_RAW.input.tar.gz").write_bytes(archived_bytes)
        formal_r8.mkdir()
        with tarfile.open(fileobj=io.BytesIO(archived_bytes), mode="r:gz") as archive:
            for member in archive:
                if not member.isfile() or not member.name.startswith("original/"):
                    continue
                relative = PurePosixPath(member.name[len("original/"):])
                if relative.is_absolute() or ".." in relative.parts:
                    raise RuntimeError("unsafe original R8 member")
                file = formal_r8 / relative
                file.parent.mkdir(parents=True, exist_ok=True)
                file.write_bytes(archive.extractfile(member).read())
                file.chmod(member.mode)
        if sha((formal_r8 / "receipt.json").read_bytes()) != ORIGINAL_RECEIPT_SHA:
            raise RuntimeError("original formal receipt bytes changed")
        recovered = []
        with tarfile.open(fileobj=io.BytesIO(elf_tar), mode="r:") as archive:
            for role, pin in pins.items():
                member = archive.getmember("original/work/" + role + "/bridge")
                data = archive.extractfile(member).read()
                if not member.isfile() or len(data) != pin["bytes"] or sha(data) != pin["sha256"] or member.mode != 0o700:
                    raise RuntimeError("exact ELF tar bytes/mode changed: " + role)
                file = formal_r8 / "work" / role / "bridge"
                file.parent.mkdir(parents=True, exist_ok=True)
                if file.exists():
                    raise RuntimeError("unexpected preexisting original ELF body")
                file.write_bytes(data)
                file.chmod(member.mode)
                if file.stat().st_mode != pin["mode"]:
                    raise RuntimeError("full restored ELF mode changed")
                recovered.append({"role": role, "bytes": len(data), "sha256": sha(data), "mode": file.stat().st_mode,
                                  "origin": "GitHub reproducible build; full SHA equals historical original; permitted by 2026-11-02 user instruction"})
        result["exactOriginalElfInputs"] = recovered
        V3.mkdir(parents=True)
        V4.mkdir(parents=True)
        for file in (root / V4_SOURCE).iterdir():
            if file.is_file():
                shutil.copyfile(file, V3 / file.name)
                shutil.copyfile(file, V4 / file.name)
        shutil.copyfile(root / "evidence/pr338-b1-repro-20261102/frozen-tools/verify_linux.v3.py", V3 / "verify_linux.py")
        CAPTURE.parent.mkdir(parents=True)
        shutil.copyfile(root / "evidence/geo323-provider-hint-1449d430/TOOLS/capture.py", CAPTURE)
        shutil.copytree(root / MEMO_TOOLS, MEMO)
        tool_paths = {"capture.py": CAPTURE, "v3/geo323_record.py": V3 / "geo323_record.py",
                      "v3/profile_linux.py": V3 / "profile_linux.py", "v3/verify_linux.py": V3 / "verify_linux.py",
                      "v4/run.py": V4 / "run.py", "v4/verify_linux.py": V4 / "verify_linux.py"}
        result["originalHardPinnedTools"] = []
        for key, file in tool_paths.items():
            value = sha(file.read_bytes())
            if value != PINS[key]:
                raise RuntimeError("original hard tool pin mismatch: " + key)
            result["originalHardPinnedTools"].append({"name": key, "path": str(file), "sha256": value})
        shutil.copytree(MEMO, out / "pinned-original-memo-tools")
        shutil.copytree(V3, out / "pinned-original-v3-tools")
        shutil.copytree(V4, out / "pinned-original-v4-tools")
        shutil.copyfile(CAPTURE, out / "capture.original.py.txt")

        repo.mkdir()
        for command, label in [(["git", "init", "--quiet", str(repo)], "git-init"),
                               (["git", "remote", "add", "origin", "https://github.com/ZhiQiYang/geometry-axiom.git"], "git-remote"),
                               (["git", "config", "remote.origin.promisor", "true"], "git-promisor"),
                               (["git", "config", "remote.origin.partialclonefilter", "blob:none"], "git-partial-filter"),
                               (["git", "config", "core.autocrlf", "false"], "git-line-endings"),
                               (["git", "config", "core.sparseCheckout", "true"], "git-sparse"),
                               (["git", "fetch", "--no-tags", "--filter=blob:none", "--depth=1", "origin", F8, TARGET], "git-fetch-fixed-sources")]:
            if run(command, label, repo).returncode:
                raise RuntimeError("clean fixed source checkout failed: " + label)
        original_fixed = json.loads((root / "evidence/pr338-b1-repro-20261102/FIXED_SOURCE_CLOSURE.json").read_bytes())
        sparse = "/*\n!/*/\n/tests/fixtures/\n" + "".join("/" + row[0] + "\n" for row in original_fixed)
        (repo / ".git/info/sparse-checkout").write_text(sparse)
        if run(["git", "checkout", "--detach", F8], "git-checkout-F8", repo, timeout=600).returncode:
            raise RuntimeError("F8 checkout failed")
        state = run(["git", "status", "--porcelain=v1", "--untracked-files=all"], "F8-clean-state", repo)
        if state.returncode or state.stdout:
            raise RuntimeError("independent F8 source is not clean")
        closure = []
        for name, size, expected in original_fixed:
            data = (repo / name).read_bytes()
            target = run(["git", "show", TARGET + ":" + name], "current-input-" + str(len(closure)), repo)
            if len(data) != size or sha(data) != expected or target.returncode or target.stdout != data:
                raise RuntimeError("F8/current product compiled input differs: " + name)
            closure.append([name, size, expected])
        inventory = json.loads((formal_r8 / "evidence/scene-inventory.json").read_bytes())
        scenes = []
        for row in inventory["scenes"]:
            if "generated_n" in row:
                data = (formal_r8 / "evidence/scenes" / row["name"]).read_bytes()
            else:
                data = (repo / row["name"]).read_bytes()
                target = run(["git", "show", TARGET + ":" + row["name"]], "current-scene-" + str(len(scenes)), repo)
                if target.returncode or target.stdout != data:
                    raise RuntimeError("current original scene differs: " + row["name"])
            if len(data) != row["bytes"] or sha(data) != row["sha256"]:
                raise RuntimeError("original scene pin changed")
            scenes.append({"name": row["name"], "bytes": len(data), "sha256": sha(data)})
        differences = run(["git", "diff", "--name-only", F8, TARGET, "--", ".", ":(exclude)evidence"], "non-evidence-changes", repo)
        result["currentProductInputClosure"] = {"actualF8": F8, "currentPrHead": TARGET,
                                                "compiledFilesEqual": closure, "scenes": scenes,
                                                "allCompiledInputsAndOriginalScenesEqual": True,
                                                "nonEvidenceChangedPaths": differences.stdout.decode().splitlines(),
                                                "originalToolHashesEqual": True,
                                                "note": "Changed test ledger, geo314 test, decisions, architecture receipts, workflow and ignore files are not read by this pinned whole-memo build/profile/ABC input set."}
        dump(out / "CURRENT_PRODUCT_INPUT_CLOSURE.json", result["currentProductInputClosure"])
        for command, label in [(["gcc", "--version"], "formal-gcc-version"), (["gprof", "--version"], "formal-gprof-version"),
                               (["python3", "--version"], "formal-python-version"), (["git", "--version"], "formal-git-version"),
                               (["ldd", "--version"], "formal-libc-version"), (["dpkg-query", "-W"], "formal-dpkg-packages")]:
            run(command, label)
        command = [sys.executable, "-B", str(MEMO / "run.py"), "--repo", str(repo), "--sha", F8,
                   "--formal-out", str(formal_r8), "--out", str(out / "formal"),
                   "--heavy-lock", "/tmp/geo337-whole-memo.lock", "--phase", "all"]
        result["formalExecuted"] = True
        completed = run(command, "whole-memo-original-driver", repo, timeout=1200)
        result["formalActualProcessExit"] = completed.returncode
        if (out / "formal/receipt.json").is_file():
            formal = json.loads((out / "formal/receipt.json").read_bytes())
            result["originalDriverResult"] = {"passed": formal.get("passed"), "exit": formal.get("exit"),
                                               "sha": formal.get("sha"), "source_before": formal.get("source_before"),
                                               "source_after": formal.get("source_after"),
                                               "phases": [{"phase": x["phase"], "actual_exit": x["actual_exit"],
                                                           "execution_complete": x.get("result", {}).get("execution_complete"),
                                                           "actual": x.get("result", {}).get("actual"),
                                                           "ABC_result": x.get("result", {}).get("ABC_result")}
                                                          for x in formal.get("phases", [])]}
        result["processExit"] = completed.returncode
    except BaseException:
        result["errors"].append(traceback.format_exc())
        result["processExit"] = 2
    dump(out / "CI_RESULT.json", result)
    dump(out / "CI_MANIFEST.json", [{"path": file.relative_to(out).as_posix(), "bytes": file.stat().st_size,
                                      "sha256": sha(file.read_bytes())} for file in sorted(out.rglob("*")) if file.is_file()])
    print(json.dumps({key: result.get(key) for key in ["formalExecuted", "formalActualProcessExit", "originalDriverResult", "processExit", "errors"]}, ensure_ascii=False))
    return result["processExit"]


if __name__ == "__main__":
    raise SystemExit(main())
