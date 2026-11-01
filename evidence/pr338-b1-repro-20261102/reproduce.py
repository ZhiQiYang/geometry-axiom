"""GitHub-only byte reproduction; never execute the resulting ELF or resample R8."""
import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import stat
import subprocess
import tarfile
import traceback

F8 = "75a1e93811a52b69385cbdaf6a09d773ed9052ad"
BASE = "b74f9a2ae7ade1555b9be45283adecc097fb76e3"
TRAIN = "evidence/geo337-train-20261024"
ARCHIVE = TRAIN + "/full-R8-five-stage-raw/ORIGINAL_R8_FIVE_STAGE_RAW.tar.gz"
ARCHIVE_SHA = "4503955cefc6fb1a6491ad2a146c259e59a2185401d0fbebc09908a47e3bf9d0"
RECEIPT_SHA = "979680e78a381d28a6d1c6825b7b1b8af850bebec381ec3cee3ef42e9e46ea15"
SOURCES = {
    "base": ("original/work/source-base/", Path("/tmp/g337323R8/work/source-base"),
             184, "b9db198f840001d1ea6a9545f1790a6df87031e60be882fd1a022732f9f9b03e"),
    "fixed": ("fixed-R-source/", Path("/tmp/geo323-final-r8-source-20261024"),
              185, "7a2114e457fbd7ddf385936a2b7d60e8915120ae2838b82531951791c291921c"),
    "trace": ("original/work/fix-trace/source/", Path("/tmp/g337323R8/work/fix-trace/source"),
              185, "a8d1a65d63787d348313aa834dd84b9d2f2e82e608454bc84e320e05b949a8aa"),
}
ROLE_SOURCE = {"base-pg": "base", "fix": "fixed", "fix-trace": "trace"}


def sha(data):
    return hashlib.sha256(data).hexdigest()


def dump(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def closure(root):
    pending = ["geometry-web/web_bridge.c"]
    rows = {}
    while pending:
        name = pending.pop()
        if name in rows:
            continue
        path = root / name
        data = path.read_bytes()
        rows[name] = [name, len(data), sha(data)]
        for include in re.findall(rb'^\s*#\s*include\s*"([^"\r\n]+)"', data, re.M):
            value = include.decode("utf-8")
            candidate = (path.parent / value).resolve()
            if not candidate.is_file():
                candidate = (root / value).resolve()
            if not candidate.is_file():
                candidate = (root / "geometry-core/kernel" / value).resolve()
            if not candidate.is_file() or not candidate.is_relative_to(root):
                raise RuntimeError("quoted include outside frozen closure: " + name + " -> " + value)
            pending.append(candidate.relative_to(root).as_posix())
    return [rows[name] for name in sorted(rows)]


def main():
    if os.environ.get("GITHUB_ACTIONS") != "true":
        raise SystemExit("Build is authorized only in GitHub Actions")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    root, out = args.root.resolve(), args.out.resolve()
    out.mkdir(parents=True, exist_ok=True)
    report = {"schema": "pr338-exact-r8-reproduction/1", "startedUtc": now(),
              "ciExecutionHead": os.environ["GITHUB_SHA"], "ciRunId": os.environ["GITHUB_RUN_ID"],
              "historicalF8Source": F8, "historicalBaseSource": BASE,
              "originalR8OuterExitRetained": 1, "originalPerformanceResampled": False,
              "executedBuiltElf": False, "formalWholeMemoExecuted": False,
              "formalWholeMemoExit": None, "b1Closed": False,
              "commands": [], "builds": [], "errors": []}

    def run(command, label, cwd=None, build=False):
        completed = subprocess.run(command, cwd=cwd, capture_output=True,
                                   preexec_fn=(lambda: os.umask(0o077)) if build else None,
                                   timeout=600 if build else 60)
        streams = {}
        for kind, data in [("stdout", completed.stdout), ("stderr", completed.stderr)]:
            name = label + "." + kind + ".bin"
            (out / name).write_bytes(data)
            streams[kind] = {"path": name, "bytes": len(data), "sha256": sha(data)}
        row = {"command": command, "cwd": str(cwd) if cwd else None,
               "actualProcessReturncode": completed.returncode, **streams}
        report["commands"].append(row)
        dump(out / "RESULT.json", report)
        return completed, row

    try:
        status = json.loads((root / (TRAIN + "/review-unblock-20261029/B1_STATUS.json")).read_bytes())
        pins = {x["name"]: x["expected"] for x in status["requiredFiles"]}
        if status["requiredExecutionSha"] != F8:
            raise RuntimeError("F8 identity pin changed")
        archive_bytes = (root / ARCHIVE).read_bytes()
        if sha(archive_bytes) != ARCHIVE_SHA:
            raise RuntimeError("original R8 archive hash mismatch")
        report["originalArchive"] = {"path": ARCHIVE, "bytes": len(archive_bytes), "sha256": ARCHIVE_SHA}
        recipes = {}
        with tarfile.open(root / ARCHIVE, "r:gz") as archive:
            receipt_bytes = archive.extractfile("original/receipt.json").read()
            if sha(receipt_bytes) != RECEIPT_SHA:
                raise RuntimeError("original R8 receipt hash mismatch")
            (out / "R8_receipt.original.json").write_bytes(receipt_bytes)
            receipt = json.loads(receipt_bytes)
            report["originalVersions"] = receipt.get("versions")
            report["originalPlatform"] = receipt.get("platform")
            for role in ROLE_SOURCE:
                data = archive.extractfile(f"original/work/{role}/build.json").read()
                (out / f"{role}.build.original.json").write_bytes(data)
                recipes[role] = json.loads(data)
            for _, (prefix, destination, _, _) in SOURCES.items():
                if destination.exists():
                    raise RuntimeError("fresh original absolute source path required: " + str(destination))
                destination.mkdir(parents=True)
                for member in archive.getmembers():
                    if not member.isfile() or not member.name.startswith(prefix):
                        continue
                    relative = PurePosixPath(member.name[len(prefix):])
                    if relative.is_absolute() or ".." in relative.parts:
                        raise RuntimeError("unsafe source member")
                    path = destination / relative
                    path.parent.mkdir(parents=True, exist_ok=True)
                    path.write_bytes(archive.extractfile(member).read())
            tool = archive.extractfile("original/tools-frozen/verify_linux.py").read()
            (out / "verify_linux.original.py.txt").write_bytes(tool)
            report["traceGeneratorSha256"] = sha(tool)

        report["sourceClosures"] = {}
        for source, (_, destination, expected_count, expected_sha) in SOURCES.items():
            rows = closure(destination)
            value = sha(json.dumps(rows, ensure_ascii=False, separators=(",", ":")).encode())
            dump(out / (source + ".source-closure.json"), rows)
            if len(rows) != expected_count or value != expected_sha:
                raise RuntimeError("frozen source closure changed: " + source + " " + value)
            report["sourceClosures"][source] = {"files": len(rows), "sha256": value,
                                                "absoluteRoot": str(destination)}
        for command, label in [(["gcc", "--version"], "gcc-version"),
                               (["gcc", "-v"], "gcc-configure"),
                               (["gcc", "-dumpspecs"], "gcc-specs"),
                               (["ld", "--version"], "ld-version"),
                               (["gprof", "--version"], "gprof-version"),
                               (["ldd", "--version"], "ldd-version"),
                               (["dpkg-query", "-W"], "dpkg-packages"),
                               (["apt-cache", "policy", "gcc", "gcc-14", "binutils", "libc6", "libc6-dev"], "apt-policy")]:
            result, _ = run(command, label)
            if label == "gcc-version":
                report["compilerVersionMatchesOriginal"] = result.stdout.decode().splitlines()[0] == "gcc (Debian 14.2.0-19) 14.2.0"
        toolchain_files = []
        for name in ["crt1.o", "gcrt1.o", "Scrt1.o", "crti.o", "crtn.o", "crtbegin.o", "crtbeginS.o", "crtend.o", "libgcc.a", "libc.so"]:
            result, _ = run(["gcc", "-print-file-name=" + name], "toolchain-" + name)
            file = Path(result.stdout.decode().strip())
            if file.is_file():
                data = file.read_bytes()
                toolchain_files.append({"name": name, "path": str(file), "bytes": len(data), "sha256": sha(data)})
        dump(out / "TOOLCHAIN_FILES.json", toolchain_files)

        for role, source in ROLE_SOURCE.items():
            recipe = recipes[role]
            output_path = Path(recipe["command"][recipe["command"].index("-o") + 1])
            if str(output_path) != pins[role]["source_path"]:
                raise RuntimeError("original build output pin mismatch")
            output_path.parent.mkdir(parents=True, exist_ok=True)
            result, command_record = run(recipe["command"], role + ".compile", Path(recipe["cwd"]), build=True)
            row = {"role": role, "source": source, "sourceSha": BASE if role == "base-pg" else F8,
                   "originalCommand": recipe["command"], "originalCwd": recipe["cwd"],
                   "actualProcessReturncode": result.returncode, "expected": pins[role], "commandRecord": command_record}
            if output_path.is_file():
                data = output_path.read_bytes()
                row["actual"] = {"bytes": len(data), "sha256": sha(data), "mode": output_path.stat().st_mode}
                row["exactOriginalBytes"] = row["actual"]["bytes"] == pins[role]["bytes"] and row["actual"]["sha256"] == pins[role]["sha256"]
                row["exactOriginalMode"] = row["actual"]["mode"] == pins[role]["mode"]
                run(["readelf", "--wide", "-h", "-l", "-S", "-n", "-d", str(output_path)], role + ".readelf")
                run(["file", str(output_path)], role + ".file")
            else:
                row.update(exactOriginalBytes=False, exactOriginalMode=False)
            report["builds"].append(row)
            print(json.dumps(row, ensure_ascii=False), flush=True)
            dump(out / "RESULT.json", report)
        with tarfile.open(out / "REPRODUCED_ELFS.tar", "w") as archive:
            for row in report["builds"]:
                path = Path(row["expected"]["source_path"])
                if path.is_file():
                    archive.add(path, arcname="original/work/" + row["role"] + "/bridge", recursive=False)
        all_exact = len(report["builds"]) == 3 and all(
            x["actualProcessReturncode"] == 0 and x["exactOriginalBytes"] and x["exactOriginalMode"] for x in report["builds"])
        report["allThreeExactOriginalBytesAndMode"] = all_exact
        report["processExit"] = 0 if all_exact else 1
        report["nextAction"] = ("All exact: eligible for unchanged whole-memo execution under latest user instruction, with F8 identity and original history retained."
                                if all_exact else "Hashes differ: publish original loss, exact recipe, actual toolchain and full hashes; ask ChatGPT/dot to judge an explicit alternative closeout, never label these as original bytes.")
    except BaseException:
        report["errors"].append(traceback.format_exc())
        report["processExit"] = 2
    report["endedUtc"] = now()
    dump(out / "RESULT.json", report)
    dump(out / "MANIFEST.json", [{"path": path.relative_to(out).as_posix(), "bytes": path.stat().st_size,
                                   "sha256": sha(path.read_bytes())} for path in sorted(out.rglob("*")) if path.is_file()])
    print(json.dumps({key: report.get(key) for key in ["allThreeExactOriginalBytesAndMode", "processExit", "formalWholeMemoExecuted", "errors"]}, ensure_ascii=False))
    return report["processExit"]


if __name__ == "__main__":
    raise SystemExit(main())
