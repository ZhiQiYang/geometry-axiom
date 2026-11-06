"""Read-only recovery inventory. Success means inventory complete, never B1 acceptance.

This program does not compile, import historical tools, execute any ELF, or run a
product test. The separately reported static identity classification is 2 when
the three pinned historical payloads have not been recovered; that computed
classification is not a process exit code.
"""
import argparse
import datetime
import hashlib
import io
import json
import os
from pathlib import Path
import shutil
import stat
import subprocess
import tarfile
import traceback
import zipfile


REPO = "ZhiQiYang/geometry-axiom"
F8 = "75a1e93811a52b69385cbdaf6a09d773ed9052ad"
GREEN_HEAD = "ad64b7d7a53e0bec5ed94197a2a5c14712e32da3"
F8_RUN = 40170221039
GREEN_RUN = 41203002092
TRAIN = "evidence/geo337-train-20261024"
STATUS = TRAIN + "/review-unblock-20261029/B1_STATUS.json"
ORIGINAL = TRAIN + "/full-R8-five-stage-raw/ORIGINAL_R8_FIVE_STAGE_RAW.tar.gz"
EXCLUDED = TRAIN + "/full-R8-five-stage-raw/EXCLUDED_ELF_PAYLOADS.json"
TOOLS = TRAIN + "/prepared-during-F8/memo-copy-v2/tools"


def digest(data):
    return hashlib.sha256(data).hexdigest()


def dump(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[2]
    out = args.out.resolve()
    if out.exists():
        parser.error("fresh output directory required")
    if out == root or out.is_relative_to(root) or root.is_relative_to(out):
        parser.error("output must be outside repository")
    out.mkdir(parents=True)
    report = {
        "schema": "pr338-b1-original-payload-recovery-audit/1",
        "startedUtc": now(),
        "auditExecutionHead": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=root, text=True).strip(),
        "historicalRequiredExecutionSha": F8,
        "originalR8OuterExitRetained": 1,
        "originalPerformanceResampled": False,
        "compiledAnything": False,
        "executedAnyElf": False,
        "formalWholeMemoExecuted": False,
        "formalWholeMemoExit": None,
        "baselineWithdrawalRestoration": "UNRUN; no formal 0/1/0 claim",
        "b1Closed": False,
        "authority": "Only the reviewing party can determine final B1 closure.",
        "errors": [],
        "commands": [],
    }
    matches = []
    try:
        status_bytes = (root / STATUS).read_bytes()
        status = json.loads(status_bytes)
        wanted = {x["name"]: x["expected"] for x in status["requiredFiles"]}
        if status["requiredExecutionSha"] != F8 or status["formalExecuted"] is not False:
            raise RuntimeError("unexpected historical identity or formal status")
        report["requiredOriginals"] = wanted
        report["pinnedStatus"] = {"path": STATUS, "bytes": len(status_bytes), "sha256": digest(status_bytes)}
        (out / "B1_STATUS.original.json").write_bytes(status_bytes)

        def gh(endpoint, name, binary=False, allow_error=False):
            command = ["gh", "api", "-H", "Accept: application/vnd.github+json", endpoint]
            completed = subprocess.run(command, capture_output=True, cwd=root, timeout=180)
            prefix = out / "github" / name
            prefix.parent.mkdir(parents=True, exist_ok=True)
            stdout_file = str(prefix) + (".zip" if binary else ".json")
            stderr_file = str(prefix) + ".stderr.txt"
            Path(stdout_file).write_bytes(completed.stdout)
            Path(stderr_file).write_bytes(completed.stderr)
            row = {
                "command": command, "actualProcessReturncode": completed.returncode,
                "stdout": str(Path(stdout_file).relative_to(out)),
                "stdoutBytes": len(completed.stdout), "stdoutSha256": digest(completed.stdout),
                "stderr": str(Path(stderr_file).relative_to(out)),
                "stderrSha256": digest(completed.stderr),
            }
            report["commands"].append(row)
            dump(out / "AUDIT.json", report)
            if completed.returncode and not allow_error:
                raise RuntimeError("GitHub read failed: " + endpoint + "; " + completed.stderr.decode(errors="replace"))
            return completed.stdout if binary or completed.returncode else json.loads(completed.stdout)

        artifacts = []
        page = 1
        total_count = None
        while True:
            result = gh(f"repos/{REPO}/actions/artifacts?per_page=100&page={page}", f"artifact-list-{page}")
            if total_count is None:
                total_count = result["total_count"]
            artifacts.extend(result["artifacts"])
            if len(result["artifacts"]) < 100:
                break
            page += 1
        ids = [x["id"] for x in artifacts]
        if len(ids) != len(set(ids)) or len(artifacts) != total_count:
            raise RuntimeError("artifact pagination changed during snapshot; rerun with a new snapshot")
        report["artifactSnapshot"] = {
            "count": len(artifacts), "pages": page,
            "totalZipBytes": sum(x["size_in_bytes"] for x in artifacts),
            "downloaded": 0, "expired": [], "members": [],
        }

        def inspect_member(data, origin, mode):
            if data[:4] != b"\x7fELF" and len(data) not in {x["bytes"] for x in wanted.values()}:
                return
            entry = {"origin": origin, "bytes": len(data), "sha256": digest(data),
                     "mode": mode, "elfMagic": data[:4] == b"\x7fELF"}
            entry["byteMatchingRoles"] = [role for role, pin in wanted.items()
                                          if len(data) == pin["bytes"] and entry["sha256"] == pin["sha256"]
                                          and entry["elfMagic"]]
            entry["matchingRoles"] = [role for role in entry["byteMatchingRoles"]
                                      if mode == wanted[role]["mode"]]
            matches.append(entry)

        for artifact in artifacts:
            if artifact["expired"]:
                report["artifactSnapshot"]["expired"].append(artifact["id"])
                continue
            payload = gh(f"repos/{REPO}/actions/artifacts/{artifact['id']}/zip",
                         "artifacts/" + str(artifact["id"]), binary=True)
            actual = "sha256:" + digest(payload)
            if artifact.get("digest") and actual != artifact["digest"]:
                raise RuntimeError(f"artifact ZIP digest mismatch: {artifact['id']}")
            entries = []
            with zipfile.ZipFile(io.BytesIO(payload)) as archive:
                for member in archive.infolist():
                    if member.is_dir():
                        continue
                    data = archive.read(member)
                    mode = member.external_attr >> 16
                    entries.append({"name": member.filename, "bytes": len(data),
                                    "sha256": digest(data), "mode": mode})
                    inspect_member(data, f"artifact:{artifact['id']}:{member.filename}", mode)
            report["artifactSnapshot"]["members"].append({
                "artifactId": artifact["id"], "name": artifact["name"],
                "workflowRun": artifact["workflow_run"], "zipSha256": digest(payload), "members": entries})
            report["artifactSnapshot"]["downloaded"] += 1
            print(f"read artifact {artifact['id']} {artifact['name']}: {len(entries)} members", flush=True)

        historical_run = gh(f"repos/{REPO}/actions/runs/{F8_RUN}", "F8-run")
        historical_jobs = gh(f"repos/{REPO}/actions/runs/{F8_RUN}/jobs?filter=all&per_page=100", "F8-jobs")
        historical_artifacts = gh(f"repos/{REPO}/actions/runs/{F8_RUN}/artifacts?per_page=100", "F8-artifacts")
        gh(f"repos/{REPO}/actions/runs/{F8_RUN}/logs", "F8-logs", binary=True, allow_error=True)
        if historical_run["head_sha"] != F8:
            raise RuntimeError("historical F8 run SHA changed")
        report["historicalF8Actions"] = {
            "runId": F8_RUN, "sha": historical_run["head_sha"],
            "artifactCount": historical_artifacts["total_count"],
            "jobs": [{"id": x["id"], "name": x["name"], "conclusion": x["conclusion"],
                      "runnerId": x["runner_id"], "stepCount": len(x["steps"])} for x in historical_jobs["jobs"]],
        }
        green_run = gh(f"repos/{REPO}/actions/runs/{GREEN_RUN}", "seven-green-run")
        green_jobs = gh(f"repos/{REPO}/actions/runs/{GREEN_RUN}/jobs?filter=all&per_page=100", "seven-green-jobs")
        attempt_logs = []
        for attempt in range(1, green_run["run_attempt"] + 1):
            raw = gh(f"repos/{REPO}/actions/runs/{GREEN_RUN}/attempts/{attempt}/logs",
                     f"seven-green-attempt-{attempt}-rawlogs", binary=True)
            with zipfile.ZipFile(io.BytesIO(raw)) as logs:
                members = [{"name": item.filename, "bytes": item.file_size,
                            "sha256": digest(logs.read(item))}
                           for item in logs.infolist() if not item.is_dir()]
            attempt_logs.append({"attempt": attempt, "zipSha256": digest(raw), "members": members})
        if green_run["head_sha"] != GREEN_HEAD:
            raise RuntimeError("known seven-green run SHA changed")
        report["knownSevenGreenActions"] = {
            "runId": GREEN_RUN, "sha": green_run["head_sha"], "conclusion": green_run["conclusion"],
            "attempt": green_run["run_attempt"],
            "attemptRawLogs": attempt_logs,
            "jobs": [{"id": x["id"], "name": x["name"], "conclusion": x["conclusion"],
                      "attempt": x["run_attempt"], "startedAt": x["started_at"],
                      "completedAt": x["completed_at"]} for x in green_jobs["jobs"]],
            "scope": "Historical seven integration jobs only; attempt 1 contains the six browser runs and cancelled native, attempt 2 contains the completed native rerun. These do not run the missing whole-memo formal counterfactual.",
        }

        original_path = root / ORIGINAL
        original_bytes = original_path.read_bytes()
        preserved = out / "originals"
        preserved.mkdir()
        shutil.copyfile(original_path, preserved / original_path.name)
        shutil.copyfile(root / EXCLUDED, preserved / "EXCLUDED_ELF_PAYLOADS.json")
        inventory = []
        with tarfile.open(fileobj=io.BytesIO(original_bytes), mode="r:gz") as archive:
            for member in archive:
                row = {"name": member.name, "bytes": member.size, "mode": member.mode,
                       "kind": member.type.decode("ascii", errors="replace"), "linkname": member.linkname}
                if member.isfile():
                    data = archive.extractfile(member).read()
                    row["sha256"] = digest(data)
                    inspect_member(data, "original-R8-tar:" + member.name, stat.S_IFREG | member.mode)
                inventory.append(row)
        dump(out / "originals" / "R8_TAR_MEMBERS.json", inventory)
        report["originalR8Archive"] = {
            "path": ORIGINAL, "bytes": len(original_bytes), "sha256": digest(original_bytes),
            "memberCount": len(inventory),
            "requiredPayloadEntries": {role: [x for x in inventory if x["name"].lstrip("./") == pin["name"]]
                                       for role, pin in wanted.items()},
            "policy": json.loads((root / EXCLUDED).read_bytes()),
        }
        source_manifest = []
        for source_dir in [root / TOOLS, root / "evidence/pr338-b2-closure-20261029"]:
            for file in sorted(source_dir.rglob("*")):
                if not file.is_file():
                    continue
                data = file.read_bytes()
                relative = file.relative_to(root)
                target = out / "pinned-tools-and-closure" / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(data)
                source_manifest.append({"path": relative.as_posix(), "bytes": len(data), "sha256": digest(data)})
        dump(out / "PINNED_TOOLS_AND_CLOSURE.json", source_manifest)
        report["elfCandidates"] = matches
        recovered_roles = {role for match in matches for role in match["matchingRoles"]}
        report["originalPayloadIdentityGate"] = {
            "classificationCode": 0 if recovered_roles == set(wanted) else 2,
            "meaning": "Computed static exact bytes/full-mode classification, not a process exit or formal whole-memo execution.",
            "matchedRoles": sorted(recovered_roles), "missingRoles": sorted(set(wanted) - recovered_roles),
            "requiredModeOctal": "0100700", "requiredSource": F8,
        }
        report["nextAction"] = (
            "Retrieve the missing original payload bytes from the preserving owner/environment, verify full mode and hashes, "
            "then execute the unchanged original whole-memo driver in GitHub CI at actual F8 with raw streams/exits and a separate current-head input closure. "
            "No replacement build, performance resample, or synthetic metadata run can close B1.")
        report["auditComplete"] = True
        report["auditActualExit"] = 0
    except BaseException:
        report["errors"].append(traceback.format_exc())
        report["auditComplete"] = False
        report["auditActualExit"] = 1
    report["endedUtc"] = now()
    dump(out / "AUDIT.json", report)
    manifests = []
    for path in sorted(out.rglob("*")):
        if path.is_file():
            data = path.read_bytes()
            manifests.append({"path": path.relative_to(out).as_posix(), "bytes": len(data), "sha256": digest(data)})
    dump(out / "MANIFEST.json", manifests)
    print(json.dumps({key: report.get(key) for key in ["auditComplete", "auditActualExit", "originalPayloadIdentityGate", "formalWholeMemoExecuted", "b1Closed", "errors"]}, ensure_ascii=False))
    return report["auditActualExit"]


if __name__ == "__main__":
    raise SystemExit(main())
