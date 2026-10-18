"""外部小量測入口；執行才會編譯／量測，準備階段只讀 AST，不 import。"""
import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import platform
import re
import resource
import shlex
import shutil
import signal
import statistics
import subprocess
import time

BASE_SHA = "e64aa6359d600f43313ec9d7ba1112c465b6a40c"
BASE_MANIFEST = "eb802fb4751e207621055fc7c9e3930a070651f577b56fd72a953e4efcf70dd4"
BASE_SOURCE = Path(__file__).resolve().parent.parent / "artifacts/sources/integration-e64aa635"
STAGES = ("create_and_9_bind", "noop_evaluate", "seal", "publish", "destroy",
          "lifecycle_including_harness_checks")


def require(value, message):
    if not value:
        raise RuntimeError(message)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def source_identity(source, sha, manifest_hash):
    manifest_path = source / "source-manifest.json"
    require(digest(manifest_path) == manifest_hash, "來源 manifest pin 不符")
    manifest = json.loads(manifest_path.read_text())
    require(manifest["sha"] == sha, "來源 commit pin 不符")
    for relative, expected in manifest["files"].items():
        path = source / relative
        require(not Path(relative).is_absolute() and ".." not in Path(relative).parts
                and Path(relative).parts[0] not in (".codex", "feedback"), "來源範圍不合法")
        require(path.is_file() and not path.is_symlink() and path.resolve().is_relative_to(source), "來源不是封存內的一般檔案")
        require(digest(path) == expected, "封存來源已改變: " + relative)
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=BASE_SOURCE)
    parser.add_argument("--source-sha", default=BASE_SHA)
    parser.add_argument("--source-manifest-sha256", default=BASE_MANIFEST)
    parser.add_argument("--output", type=Path, required=True, help="必須尚不存在")
    parser.add_argument("--cc", default="/usr/bin/gcc")
    parser.add_argument("--warmup", type=int, default=2)
    parser.add_argument("--sha-repeats", type=int, default=11)
    parser.add_argument("--candidate-repeats", type=int, default=9)
    parser.add_argument("--timeout", type=float, default=900)
    args = parser.parse_args()
    require(re.fullmatch("[0-9a-f]{40}", args.source_sha), "需完整來源 SHA")
    require(re.fullmatch("[0-9a-f]{64}", args.source_manifest_sha256), "需 manifest SHA256")
    require(all(0 < n <= 100000 for n in (args.warmup, args.sha_repeats, args.candidate_repeats)), "重複數超界")
    require(math.isfinite(args.timeout) and args.timeout > 0, "timeout 必須為正有限秒數")
    source, output = args.source.resolve(), args.output.resolve()
    require(not output.is_relative_to(source), "結果不可寫進固定來源")
    output.mkdir(parents=True, exist_ok=False)
    soft, hard = resource.getrlimit(resource.RLIMIT_STACK)
    required_stack = 16 * 1024 * 1024
    require(hard == resource.RLIM_INFINITY or hard >= required_stack, "stack hard limit 不足 16 MiB")
    resource.setrlimit(resource.RLIMIT_STACK, (max(soft, required_stack) if soft != resource.RLIM_INFINITY else soft, hard))
    harness = Path(__file__).with_name("bench.c").resolve()
    cc = Path(shutil.which(args.cc) or args.cc).resolve()
    receipt = {"status": "未完成", "source": str(source), "source_sha": args.source_sha,
               "source_manifest_sha256": args.source_manifest_sha256,
               "harness_sha256": digest(harness), "wrapper_sha256": digest(Path(__file__)),
               "compiler": str(cc), "compiler_sha256": digest(cc), "uname": list(platform.uname()),
               "python": platform.python_version(), "warmup": args.warmup,
               "sha_repeats": args.sha_repeats, "candidate_repeats": args.candidate_repeats,
               "clock_scope": "各 API 分段包含計時讀值開銷；完整 lifecycle 另含 harness 核對，不含輸出",
               "commands": []}
    cpuinfo = Path("/proc/cpuinfo").read_text()
    receipt["cpu_model"] = sorted(set(re.findall(r"^model name\s*:\s*(.*)$", cpuinfo, re.M)))
    receipt["cpu_affinity"] = sorted(os.sched_getaffinity(0))
    receipt["os_release"] = Path("/etc/os-release").read_text()
    env = {"PATH": "/usr/bin:/bin", "LANG": "C.UTF-8", "LC_ALL": "C.UTF-8", "TZ": "UTC"}

    def command(label, argv):
        start = time.monotonic()
        record = {"label": label, "argv": [str(a) for a in argv], "timeout_s": args.timeout}
        receipt["commands"].append(record)
        with (output / (label + ".stdout")).open("wb") as stdout, (output / (label + ".stderr")).open("wb") as stderr:
            child = subprocess.Popen(record["argv"], cwd=output, env=env, stdout=stdout, stderr=stderr, start_new_session=True)
            try:
                try:
                    # WNOWAIT 保留本次 leader，直到正常退出或異常清理完成才 reap。
                    while os.waitid(os.P_PID, child.pid, os.WEXITED | os.WNOHANG | os.WNOWAIT) is None:
                        if time.monotonic() - start >= args.timeout:
                            raise subprocess.TimeoutExpired(record["argv"], args.timeout)
                        time.sleep(0.02)
                except BaseException:
                    os.killpg(child.pid, signal.SIGKILL)
                    child.wait()
                    record["interrupted_or_timeout"] = True
                    raise
                record["exit"] = child.wait()
            finally:
                record["command_wall_s"] = time.monotonic() - start
                write(output / "receipt.json", receipt)
        require(record["exit"] == 0, label + " 失敗；原始 stdout/stderr 已保存")
        return (output / (label + ".stdout")).read_bytes()

    try:
        manifest = source_identity(source, args.source_sha, args.source_manifest_sha256)
        require("room_a.scene" in manifest["files"], "工作負載未受來源 manifest 封印")
        receipt["scene_sha256"] = manifest["files"]["room_a.scene"]
        shutil.copyfile(source / "source-manifest.json", output / "source-manifest.json")
        shutil.copyfile(harness, output / "bench.c")
        shutil.copyfile(Path(__file__), output / "measure.py")
        receipt["compiler_version"] = command("compiler-version", [cc, "--version"]).decode()
        binary = output / "bench"
        command("build", [cc, "-std=c11", "-O2", "-MMD", "-MF", output / "bench.d",
                          "-I", source, output / "bench.c", "-o", binary, "-lm"])
        dependencies = shlex.split((output / "bench.d").read_text().replace("\\\n", " ").split(":", 1)[1])
        closure = {}
        for item in dependencies:
            path = Path(item).resolve()
            if path == output / "bench.c":
                require(digest(path) == receipt["harness_sha256"], "harness 建置期間改變")
                continue
            require(path.is_relative_to(source), "compiler 使用封存以外的非系統 include")
            relative = str(path.relative_to(source))
            require(relative in manifest["files"] and digest(path) == manifest["files"][relative], "實際 include 未受 manifest 封印")
            closure[relative] = digest(path)
        require(all(p in closure for p in ("current_geometry.c", "geometry-core/kernel/codec.c", "geometry-core/kernel/candidate.c", "geometry-app/native/app_candidate.c", "geometry-app/native/world_candidate.inc")), "缺少真產品閉包")
        write(output / "actual-compiler-closure.json", closure)
        receipt["binary_sha256"] = digest(binary)
        sizes = json.loads(command("sizes", [binary, "sizes"]))
        require(sizes["kind"] == "sizes" and len(sizes["bindings"]) == 9, "真 sizeof/bind 清單不符")
        require(sizes["version_store_bytes"] == next(b["bytes"] for b in sizes["bindings"] if b["name"] == "core.version_store"), "K store 大小不符真 bind")
        write(output / "sizes.json", sizes)
        summary = {"source_sha": args.source_sha, "sha": {}, "candidate": {}}
        fixture_record = {}
        for kind, length in (("world", sizes["world_bytes"]), ("version_store", sizes["version_store_bytes"])):
            require(isinstance(length, int) and 0 < length < 64 * 1024 * 1024, "payload 大小異常")
            period = bytes((i * 131 + 17) % 256 for i in range(256))
            payload = (period * ((length + 255) // 256))[:length]
            expected = hashlib.sha256(payload).hexdigest()
            (output / (kind + ".bin")).write_bytes(payload)
            fixture_record[kind] = {"bytes": length, "sha256": expected, "formula": "byte[i] = (131*i + 17) % 256"}
            write(output / "independent-hashlib-fixtures.json", fixture_record)
            rows = [json.loads(line) for line in command("sha-" + kind, [binary, "sha", kind, expected, str(args.warmup), str(args.sha_repeats)]).splitlines()]
            require(len(rows) == args.sha_repeats and all(r["kind"] == "sha" and r["payload"] == kind and r["iteration"] == i and r["bytes"] == length and r["digest"] == expected for i, r in enumerate(rows)), "SHA 完成樣本或獨立 digest 不符")
            totals = {clock: sum(r["sha"][clock] for r in rows) for clock in ("wall_s", "process_cpu_s")}
            require(all(math.isfinite(v) and v > 0 for v in totals.values()), "SHA 計時無效")
            summary["sha"][kind] = {"bytes_per_call": length, "completed_calls": len(rows), "total_input_bytes": length * len(rows), **totals,
                "wall_MB_per_s": length * len(rows) / 1e6 / totals["wall_s"],
                "process_cpu_MB_per_s": length * len(rows) / 1e6 / totals["process_cpu_s"]}
        write(output / "independent-hashlib-fixtures.json", fixture_record)
        rows = [json.loads(line) for line in command("candidate", [binary, "candidate", source / "room_a.scene", str(args.warmup), str(args.candidate_repeats)]).splitlines()]
        require(len(rows) == args.candidate_repeats and all(r["kind"] == "candidate" and r["iteration"] == i and r["bindings"] == 9 and r["evaluation_generation"] == 1 and r["published"] is True for i, r in enumerate(rows)), "候選完成樣本或真判決不符")
        for stage in STAGES:
            summary["candidate"][stage] = {}
            for clock in ("wall_s", "process_cpu_s"):
                samples = [r[stage][clock] * 1000 for r in rows]
                require(all(math.isfinite(v) and v >= 0 for v in samples), "候選計時無效")
                summary["candidate"][stage][clock.replace("_s", "_ms_per_candidate")] = {"mean": statistics.mean(samples), "median": statistics.median(samples), "min": min(samples), "max": max(samples)}
        summary["candidate"]["completed_candidates"] = len(rows)
        require(digest(binary) == receipt["binary_sha256"] and digest(cc) == receipt["compiler_sha256"], "執行期間 compiler/binary 改變")
        require(digest(harness) == receipt["harness_sha256"] and digest(Path(__file__)) == receipt["wrapper_sha256"], "執行期間工具改變")
        source_identity(source, args.source_sha, args.source_manifest_sha256)
        receipt["status"] = "量測完成，待最後來源核對"
    except BaseException as exc:
        receipt["error"] = type(exc).__name__ + ": " + str(exc)
        raise
    finally:
        try:
            source_identity(source, args.source_sha, args.source_manifest_sha256)
            receipt["source_after"] = "固定封存 bytes 相同"
            if receipt["status"] == "量測完成，待最後來源核對":
                receipt["status"] = "完成"  # 非產品全驗收綠燈。
                write(output / "summary.json", summary)
        except BaseException as exc:
            receipt["source_after"] = "失敗: " + str(exc)
            receipt["status"] = "未完成"
            raise
        finally:
            write(output / "receipt.json", receipt)


if __name__ == "__main__":
    main()
