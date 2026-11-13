#!/usr/bin/env python3
"""GEO-261 隔離效能量測；不修改原始 checkout，不使用 worktree。

prepare 只建立兩份 pinned 原生來源 archive；build/measure/profile 必須明確執行。
所有 subprocess 直接使用 argv，所有測量為單程序依序執行。
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import math
import os
from pathlib import Path
import re
import resource
import selectors
import shlex
import shutil
import signal
import statistics
import subprocess
import sys
import tarfile
import time
from datetime import datetime, timedelta, timezone

PINS = {"main": "e980cb0dbf39beb40f6f3002a9ffbc43ee38c425",
        "integration": "e64aa6359d600f43313ec9d7ba1112c465b6a40c"}
NAMES = ("bridge", "model-base")
HERE = Path(__file__).resolve().parent
TZ = timezone(timedelta(hours=8))


def stamp():
    return datetime.now(TZ).isoformat(timespec="seconds")


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def run(argv, *, cwd=None, timeout=900, env=None):
    result = subprocess.run(list(map(str, argv)), cwd=cwd, env=env, capture_output=True, timeout=timeout)
    if result.returncode:
        raise RuntimeError(f"指令失敗 {result.returncode}: {shlex.join(list(map(str, argv)))}\n"
                           + result.stdout.decode(errors="replace") + result.stderr.decode(errors="replace"))
    return result


def execution_env():
    # 不記錄環境值；只移除會將 profile 寫往其他位置的覆寫。
    env = dict(os.environ)
    env.pop("GMON_OUT_PREFIX", None)
    env["LC_ALL"] = "C"
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    return env


def stack_limit():
    soft, hard = resource.getrlimit(resource.RLIMIT_STACK)
    minimum = 16 * 1024 * 1024
    if soft != resource.RLIM_INFINITY and soft < minimum:
        if hard != resource.RLIM_INFINITY and hard < minimum:
            raise RuntimeError("stack 硬上限低於 16 MiB")
        resource.setrlimit(resource.RLIMIT_STACK, (minimum, hard))


def source_dir(args, label):
    return args.output / "sources" / f"{label}-{PINS[label][:8]}"


def prepare(args):
    roots = {"geometry-core", "geometry-app", "geometry-templates", "geometry-web", "tests"}
    metadata = {"AGENTS.md", ".gitattributes", "current_geometry.c", "tests/binaries.py", "geometry-web/start_local.py",
                "geometry-app/native/build.py", "room_a.scene"}
    for label, pin in PINS.items():
        actual = run(["git", "rev-parse", pin + "^{commit}"], cwd=args.repo).stdout.decode().strip()
        if actual != pin:
            raise RuntimeError("來源 SHA 不符")
        dest = source_dir(args, label)
        if dest.exists():
            verify_sources(args, label)
            continue
        names = run(["git", "ls-tree", "-r", "--name-only", "-z", pin], cwd=args.repo).stdout.split(b"\0")
        selected = []
        for raw in names:
            if not raw:
                continue
            name = raw.decode("utf-8")
            path = Path(name)
            if any(part in {".codex", "feedback", "evidence", "release-evidence", "node_modules", "vendor"}
                   for part in path.parts):
                continue
            if name in metadata or (path.parts[0] in roots and path.suffix in {".c", ".h", ".inc"}):
                selected.append(name)
        # Git archive 保留每個 source byte；只取原生閉包需要的來源，不複製 evidence 或受保護資料夾。
        archive = run(["git", "archive", "--format=tar", pin, "--", *selected], cwd=args.repo).stdout
        dest.mkdir(parents=True)
        with tarfile.open(fileobj=io.BytesIO(archive)) as tar:
            for item in tar:
                target = dest / item.name
                if Path(item.name).is_absolute() or ".." in Path(item.name).parts:
                    raise RuntimeError("archive 有非相對路徑")
                if item.isdir():
                    target.mkdir(parents=True, exist_ok=True)
                elif item.isfile():
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.write_bytes(tar.extractfile(item).read())
                else:
                    raise RuntimeError(f"archive 含非一般檔案: {item.name}")
        manifest = {"sha": pin, "created": stamp(), "archive_sha256": hashlib.sha256(archive).hexdigest(),
                    "files": {name: sha(dest / name) for name in selected},
                    "native_build_py_exists": (dest / "geometry-app/native/build.py").exists(),
                    "source_note": "選取原始 .c/.h/.inc 與真實 registry；沒有改寫原始來源。"}
        save(dest / "source-manifest.json", manifest)
        print(f"已準備 {label} {pin}: {len(selected)} 個檔案", flush=True)
    fixture = args.output / "inputs" / "room_a.scene"
    left = (source_dir(args, "main") / "room_a.scene").read_bytes()
    right = (source_dir(args, "integration") / "room_a.scene").read_bytes()
    if left != right:
        raise RuntimeError("兩版本 room_a.scene 不同，必須先指定共同夾具")
    fixture.parent.mkdir(parents=True, exist_ok=True)
    if fixture.exists() and fixture.read_bytes() != left:
        raise RuntimeError("既有共同夾具已改變，拒絕覆寫")
    fixture.write_bytes(left)
    save(args.output / "inputs/manifest.json", {"scene_sha256": sha(fixture), "pins": PINS,
         "bridge_round": workload(fixture), "cold_commands": [["cold_start_dump", "dump"]]})


def verify_sources(args, label):
    root = source_dir(args, label)
    manifest = json.loads((root / "source-manifest.json").read_text())
    if manifest["sha"] != PINS[label]:
        raise RuntimeError("來源 manifest SHA 不符")
    for name, digest in manifest["files"].items():
        if sha(root / name) != digest:
            raise RuntimeError(f"來源被更動: {label}/{name}")


PROBE = r'''
import importlib.util,json,sys,types
from pathlib import Path
root=Path(sys.argv[1]); output=Path(sys.argv[2]); compiler=sys.argv[3]
spec=importlib.util.spec_from_file_location("performance_registry",root/"tests/binaries.py")
module=importlib.util.module_from_spec(spec); sys.modules[spec.name]=module; spec.loader.exec_module(module)
module.OUT_DIR=output; module.os.environ["CC"]=compiler
calls=[]
def capture(argv,**kwargs):
    calls.append({"argv":argv,"cwd":str(kwargs.get("cwd",root))})
    return types.SimpleNamespace(returncode=0,stdout="",stderr="")
module.subprocess.run=capture
plans={}
for name in ("bridge","model-base"):
    binary=module.BY_NAME[name]
    if binary.posix_flags != ["-std=c11","-O2"]:
        raise RuntimeError("Pinned registry flags changed: "+repr(binary.posix_flags))
    start=len(calls); module._compile(binary,root/binary.source)
    if len(calls)!=start+1: raise RuntimeError("Unexpected compile/link topology")
    plans[name]=calls[-1]
print(json.dumps(plans))
'''


def build(args):
    compiler = shutil.which(args.cc)
    if not compiler:
        raise RuntimeError("找不到 C 編譯器")
    for label in PINS:
        verify_sources(args, label)
        root = source_dir(args, label)
        if (root / "geometry-app/native/build.py").exists():
            raise RuntimeError("Pinned 版本出現另一 build.py；須先重新檢查實際 link topology")
        for mode in ("normal", "gprof"):
            directory = args.output / "build" / label / mode
            directory.mkdir(parents=True, exist_ok=True)
            plans = json.loads(run([sys.executable, "-B", "-c", PROBE, root, directory, compiler],
                                   env=execution_env()).stdout)
            for name, plan in plans.items():
                original = plan["argv"]
                if any(Path(arg).suffix in {".o", ".a"} for arg in original):
                    raise RuntimeError("發現 registry 外部 object/library；拒絕聲稱全部已加 -pg")
                dep = directory / f"{name}.d"
                mapfile = directory / f"{name}.link-map"
                additions = ["-MMD", "-MF", str(dep), f"-Wl,-Map={mapfile}"]
                if mode == "gprof":
                    additions += ["-g", "-pg", "-fno-omit-frame-pointer"]
                command = [original[0], *additions, *original[1:]]
                executable = directory / name
                manifest_path = directory / f"{name}.manifest.json"
                compiler_version = run([compiler, "--version"]).stdout.decode()
                if manifest_path.exists():
                    previous = json.loads(manifest_path.read_text())
                    if (previous["sha"] == PINS[label] and previous["command"] == command
                            and previous["compiler_version"] == compiler_version and executable.exists()
                            and previous["binary_sha256"] == sha(executable)):
                        print(f"沿用已驗證建置：{label}/{mode}/{name}", flush=True)
                        continue
                    raise RuntimeError("既有建置身份不符；請用新的 --output 保留先前證據")
                save(directory / f"{name}.command.json", {"registry_command": original, "actual_command": command,
                                                           "cwd": str(root), "mode": mode})
                print(shlex.join(command), flush=True)
                started = time.perf_counter()
                try:
                    result = subprocess.run(command, cwd=root, env=execution_env(), capture_output=True, timeout=900)
                except subprocess.TimeoutExpired as error:
                    (directory / f"{name}.build.stdout").write_bytes(error.stdout or b"")
                    (directory / f"{name}.build.stderr").write_bytes(error.stderr or b"")
                    save(directory / f"{name}.build-timeout.json", {"timeout_seconds":900,"command":command})
                    raise
                (directory / f"{name}.build.stdout").write_bytes(result.stdout)
                (directory / f"{name}.build.stderr").write_bytes(result.stderr)
                if result.returncode:
                    raise RuntimeError(f"{label}/{mode}/{name} 編譯失敗，見 build.stderr")
                # Compiler .d 是實際預處理後的 include 閉包；unity 內 .c 全受同一編譯 -pg 旗標控制。
                dependencies = shlex.split(dep.read_text().replace("\\\n", " ").split(":", 1)[1])
                native = sorted({str((root / p).resolve().relative_to(root)) for p in dependencies if p.endswith(".c")})
                if not native:
                    raise RuntimeError("編譯器沒有回報任何原生 .c dependency")
                symbols = run(["nm", "-u", executable]).stdout.decode()
                (directory / f"{name}.undefined-symbols.txt").write_text(symbols)
                if mode == "gprof" and not re.search(r"\b(?:mcount|__fentry__)\b", symbols):
                    raise RuntimeError("profile binary 缺少 mcount/fentry；不可宣稱已插樁")
                save(directory / f"{name}.manifest.json", {"sha": PINS[label], "binary_sha256": sha(executable),
                     "compiler": compiler, "compiler_version": compiler_version,
                     "build_seconds": time.perf_counter()-started, "registry": "tests/binaries.py::_compile",
                     "native_sources": [{"path": p, "sha256": sha(root/p), "pg": mode == "gprof"} for p in native],
                     "command": command, "link_map": str(mapfile), "timestamp": stamp()})
        verify_sources(args, label)


def workload(fixture):
    return [("reset", "reset"), ("load_scene", f"loadfile {fixture}"),
            ("read_dump", "dump"), ("canvas_position", "line canvas-pos boundary 1 60 60"),
            ("unused_spec_create", "line spec PERF_VALUE 100"),
            ("unused_spec_replace", "line spec PERF_VALUE 200"),
            ("preview_spec", "line preview spec 主支1中線 900"),
            ("cancel_preview", "line cancel-preview"), ("read_final_dump", "dump")]


def require_response(raw, command, label):
    try:
        value = json.loads(raw)
    except Exception as error:
        raise RuntimeError(f"{label} 回應不是有效 JSON: {command}: {raw[:500]!r}") from error
    if not isinstance(value, dict) or value.get("ok") is not True:
        raise RuntimeError(f"{label} 回應未成功: {command}: {raw[:1200]!r}")
    if "preview spec" in command and value.get("preview", {}).get("valid") is not True:
        raise RuntimeError(f"{label} preview 未通過驗證: {raw[:1200]!r}")
    if command == "dump" and not isinstance(value.get("text"), str):
        raise RuntimeError("dump 缺少 text")
    return value


def kill_owned(proc):
    if proc.poll() is None:
        os.killpg(proc.pid, signal.SIGKILL)
    proc.wait()


def bridge_session(executable, commands, directory, label, timeout):
    directory.mkdir(parents=True)
    rows = []
    with (directory / "stderr.log").open("wb") as err, (directory / "responses.jsonl").open("w", encoding="utf-8") as receipt, (directory / "stdout.raw").open("wb") as raw_log:
        started = time.perf_counter_ns()
        proc = subprocess.Popen([str(executable)], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=err,
                                cwd=directory, env=execution_env(), start_new_session=True, bufsize=0)
        selector = selectors.DefaultSelector()
        selector.register(proc.stdout, selectors.EVENT_READ)
        buffered = bytearray()
        try:
            for index, (phase, command) in enumerate(commands):
                sent = time.perf_counter_ns()
                proc.stdin.write((command + "\n").encode("utf-8"))
                proc.stdin.flush()
                deadline = time.monotonic() + timeout
                while b"\n" not in buffered:
                    remaining = deadline-time.monotonic()
                    if remaining <= 0 or not selector.select(remaining):
                        raise TimeoutError(f"{label}: {phase} 超過 {timeout} 秒")
                    chunk = os.read(proc.stdout.fileno(), 65536)
                    if not chunk:
                        raise RuntimeError(f"{label}: {phase} 回應前 bridge 結束")
                    buffered.extend(chunk)
                raw, _, rest = buffered.partition(b"\n")
                buffered[:] = rest
                finished = time.perf_counter_ns()
                raw_log.write(raw+b"\n"); raw_log.flush()
                raw_text = raw.decode("utf-8")
                row = {"phase": phase, "command": command, "seconds": (finished-sent)/1e9,
                       "process_to_response_seconds": (finished-started)/1e9 if index == 0 else None,
                       "raw_response": raw_text}
                receipt.write(json.dumps(row, ensure_ascii=False)+"\n"); receipt.flush()
                value = require_response(raw_text, command, label)
                if command == "section-profile-read":
                    row["native_bytes"] = value.get("nativeBytes")
                rows.append({k:v for k,v in row.items() if k != "raw_response"})
            proc.stdin.close()
            # 沒有尚待讀的回應才可等待 EOF；多餘輸出不可以當成成功。
            if buffered:
                raise RuntimeError("bridge 產生額外未匹配輸出")
            tail = bytearray()
            deadline = time.monotonic()+timeout
            while True:
                remaining = deadline-time.monotonic()
                if remaining <= 0 or not selector.select(remaining):
                    raise TimeoutError("bridge EOF 清理逾時")
                chunk = os.read(proc.stdout.fileno(), 65536)
                if not chunk:
                    break
                raw_log.write(chunk); raw_log.flush()
                tail.extend(chunk)
            if tail.strip() or proc.wait(timeout=timeout) != 0:
                raise RuntimeError("bridge EOF 後有額外輸出或非零結束碼")
        finally:
            if buffered:
                raw_log.write(buffered); raw_log.flush()
            selector.close()
            kill_owned(proc)
            if not proc.stdin.closed:
                proc.stdin.close()
            proc.stdout.close()
    return rows


def model_once(executable, fixture, neutral, directory, label, timeout):
    directory.mkdir(parents=True)
    argv = [str(executable), *( ["--neutral-sources"] if neutral else []), str(fixture)]
    started = time.perf_counter_ns()
    try:
        result = subprocess.run(argv, cwd=directory, env=execution_env(), capture_output=True, timeout=timeout)
    except subprocess.TimeoutExpired as error:
        (directory/"stdout.json").write_bytes(error.stdout or b"")
        (directory/"stderr.log").write_bytes(error.stderr or b"")
        save(directory/"timeout.json",{"command":argv,"timeout_seconds":timeout})
        raise
    elapsed = (time.perf_counter_ns()-started)/1e9
    (directory/"stdout.json").write_bytes(result.stdout)
    (directory/"stderr.log").write_bytes(result.stderr)
    value = require_response(result.stdout.decode("utf-8"), shlex.join(argv), label)
    if result.returncode:
        raise RuntimeError(f"model-base 非零結束碼: {result.returncode}")
    expected = "geometry-neutral-source-envelope/1" if neutral else "geometry-base-snapshot/1"
    if value.get("schema") != expected:
        raise RuntimeError(f"model-base schema 不符: {value.get('schema')}")
    snapshot = value.get("legacySnapshot") if neutral else value
    if not isinstance(snapshot, dict) or snapshot.get("ok") is not True or snapshot.get("unplaced_timbers") != []:
        raise RuntimeError("model-base snapshot 無效或有未放置角材")
    if neutral and (not isinstance(value.get("neutralSources"), dict)
                    or value["neutralSources"].get("schema") != "geometry-neutral-sources/1"):
        raise RuntimeError("neutralSources 缺失")
    return {"seconds": elapsed, "command": argv, "stdout_bytes": len(result.stdout)}


def executable(args, label, mode, name):
    path = args.output / "build" / label / mode / name
    manifest = json.loads(path.with_suffix(".manifest.json").read_text())
    if manifest["sha"] != PINS[label] or manifest["binary_sha256"] != sha(path):
        raise RuntimeError("binary SHA 或來源 pin 不符")
    return path


def statistics_table(rows):
    groups = {}
    for row in rows:
        groups.setdefault((row["label"], row["workload"], row["phase"]), []).append(row["seconds"])
    out = []
    for (label, work, phase), values in groups.items():
        ordered = sorted(values)
        out.append({"label": label, "workload": work, "phase": phase, "count": len(values),
                    "median_seconds": statistics.median(values), "p95_seconds": ordered[math.ceil(.95*len(values))-1],
                    "min_seconds": min(values), "max_seconds": max(values), "sum_seconds": sum(values)})
    baselines = {(r["workload"],r["phase"]):r["median_seconds"] for r in out if r["label"] == "main"}
    for row in out:
        baseline = baselines.get((row["workload"],row["phase"]))
        row["ratio_to_main"] = row["median_seconds"]/baseline if baseline else None
    return out


def write_csv(path, rows):
    if not rows:
        return
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader(); writer.writerows(rows)


def parse_callgraph(text):
    # gprof 主列：[index] %time self children calls[+recursive] name [index]
    pattern = re.compile(r"^\[\d+\]\s+[\d.]+\s+([\d.]+)\s+([\d.]+)\s+(.*?)\s+\[\d+\]\s*$")
    rows = []
    for line in text.splitlines():
        match = pattern.match(line)
        if not match:
            continue
        own, children, rest = match.groups()
        calls = re.match(r"(\d+)(?:\+(\d+))?\s+(.*)", rest)
        direct, recursive, name = (int(calls[1]), int(calls[2] or 0), calls[3]) if calls else (0,0,rest)
        rows.append({"function": name, "self_seconds": float(own), "children_seconds": float(children),
                     "inclusive_seconds": float(own)+float(children), "calls": direct+recursive,
                     "direct_calls": direct, "recursive_calls": recursive})
    return rows


def profile_report(exe, gmfiles, directory):
    if not gmfiles or any(not p.is_file() for p in gmfiles):
        raise RuntimeError("缺少 gmon.out，不能產生 profile 成功報告")
    text = run(["gprof", "-b", exe, *gmfiles], env=execution_env()).stdout.decode()
    (directory/"full-gprof.txt").write_text(text)
    flat = run(["gprof", "-b", "-p", exe, *gmfiles], env=execution_env()).stdout
    (directory/"flat-profile.txt").write_bytes(flat)
    graph = run(["gprof", "-b", "-q", exe, *gmfiles], env=execution_env()).stdout.decode()
    (directory/"callgraph.txt").write_text(graph)
    rows = parse_callgraph(graph)
    if not rows:
        raise RuntimeError("無法解析 gprof callgraph，原文已保留")
    save(directory/"functions.json", rows)
    cycles = [row for row in rows if re.fullmatch(r"<cycle \d+ as a whole>",row["function"])]
    functions = [row for row in rows if row not in cycles]
    save(directory/"cycles.json",cycles)
    if not functions:
        raise RuntimeError("gprof callgraph 只有 cycle 合計，沒有函式資料")
    for title, key in (("self", "self_seconds"), ("inclusive", "inclusive_seconds"), ("calls", "calls")):
        ranked = sorted(functions, key=lambda row: (-row[key], row["function"]))[:20]
        write_csv(directory/f"top20-{title}.csv", ranked)
    save(directory/"profile-inputs.json", {"binary":str(exe), "binary_sha256":sha(exe),
         "gmon_files":[{"path":str(p),"sha256":sha(p)} for p in gmfiles],
         "note":"累積欄為 self + children；不是 flat profile 從上往下相加的 cumulative seconds。"})


def measure(args, profiling=False):
    stack_limit()
    if profiling and not shutil.which("gprof"):
        raise RuntimeError("找不到 gprof")
    for label in PINS:
        verify_sources(args, label)
    fixture = args.output / "inputs/room_a.scene"
    inputs = json.loads((args.output/"inputs/manifest.json").read_text())
    if inputs["scene_sha256"] != sha(fixture):
        raise RuntimeError("共同夾具 SHA 不符")
    commands = workload(fixture)
    mode = "gprof" if profiling else "normal"
    root = args.output / "runs" / (datetime.now(TZ).strftime("%Y%m%dT%H%M%S%f") + "-" + mode)
    root.mkdir(parents=True)
    save(root/"environment.json", {"timestamp":stamp(), "pins":PINS,
         "platform":dict(zip(("sysname","nodename","release","version","machine"),os.uname())),
         "python":sys.version, "cpu_count":os.cpu_count(), "loadavg":os.getloadavg(),
         "stack_limit":resource.getrlimit(resource.RLIMIT_STACK), "profile":profiling,
         "cold_repeats":args.cold_repeats, "rounds":args.rounds, "model_repeats":args.model_repeats,
         "commands":commands, "script_sha256":sha(__file__)})
    samples = []
    try:
        for label in PINS:
            bridge = executable(args,label,mode,"bridge")
            base = executable(args,label,mode,"model-base")
            print(f"開始 {label} {mode}，輸出 {root}",flush=True)
            cold_dir = root/label/"bridge-cold"
            cold_gm = []
            for index in range(args.cold_repeats):
                directory = cold_dir/f"sample-{index:03d}"
                rows = bridge_session(bridge,[("cold_start_dump","dump")],directory,label,args.timeout)
                samples.append({"label":label,"workload":"bridge-cold","phase":"cold_start_dump", "iteration":index,
                                "seconds":rows[0]["process_to_response_seconds"]})
                cold_gm.append(directory/"gmon.out")
            resident_dir = root/label/"bridge-resident"
            full_commands = [("excluded_startup_dump","dump"),("world_size","section-profile-read")]
            for index in range(args.rounds):
                full_commands += [(f"{index}:{phase}",command) for phase,command in commands]
            rows = bridge_session(bridge,full_commands,resident_dir/"session",label,args.timeout)
            save(resident_dir/"timing.json",rows)
            for row in rows[2:]:
                iteration,phase = row["phase"].split(":",1)
                samples.append({"label":label,"workload":"bridge-resident","phase":phase,
                                "iteration":int(iteration),"seconds":row["seconds"]})
            if profiling:
                profile_report(bridge,cold_gm,cold_dir)
                profile_report(bridge,[resident_dir/"session/gmon.out"],resident_dir)
            for neutral in ([False,True] if label == "integration" else [False]):
                work = "model-neutral" if neutral else "model-legacy"
                directory = root/label/work
                gmfiles = []
                for index in range(args.model_repeats):
                    subdir = directory/f"sample-{index:03d}"
                    row = model_once(base,fixture,neutral,subdir,label,args.timeout)
                    save(subdir/"timing.json",row)
                    samples.append({"label":label,"workload":work,"phase":"process_total",
                                    "iteration":index,"seconds":row["seconds"]})
                    gmfiles.append(subdir/"gmon.out")
                if profiling:
                    profile_report(base,gmfiles,directory)
            save(root/"samples.json",samples)
        summary = statistics_table(samples)
        if profiling:
            for row in summary:
                row["ratio_to_main"] = None
        by_work = {r["workload"]:r for r in summary if r["label"]=="integration" and r["phase"]=="process_total"}
        delta = by_work["model-neutral"]["median_seconds"]-by_work["model-legacy"]["median_seconds"]
        save(root/"summary.json",{"complete":True,"profile_times_are_not_regression_ratios":profiling,
             "rows":summary,"integration_neutral_minus_legacy_median_seconds":delta,
             "main_neutral":"未量測；本腳本僅 integration 做同 binary neutral 差額對照"})
        write_csv(root/"summary.csv",summary)
        print(f"完成：{root}/summary.csv",flush=True)
    except BaseException as error:
        save(root/"samples.json",samples)
        save(root/"failure.json",{"complete":False,"error":repr(error),"timestamp":stamp()})
        raise
    finally:
        for label in PINS:
            verify_sources(args,label)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stage",choices=("prepare","build","measure","profile","all"))
    parser.add_argument("--repo",type=Path,default=Path("/workspace/geometry-axiom"))
    parser.add_argument("--output",type=Path,default=HERE/"artifacts")
    parser.add_argument("--main-sha",default=PINS["main"],
                        help="main 比較來源的完整40位提交SHA")
    parser.add_argument("--integration-sha",default=PINS["integration"],
                        help="整合分支或自有修正候選的完整40位提交SHA；不同組合須另用output")
    parser.add_argument("--cc",default="gcc")
    parser.add_argument("--cold-repeats",type=int,default=7)
    parser.add_argument("--rounds",type=int,default=15)
    parser.add_argument("--model-repeats",type=int,default=7)
    parser.add_argument("--timeout",type=float,default=120)
    args = parser.parse_args()
    if not all(re.fullmatch(r"[0-9a-f]{40}", pin) for pin in (args.main_sha, args.integration_sha)):
        parser.error("比較來源必須是完整40位小寫提交SHA，不接受浮動ref")
    PINS.update(main=args.main_sha,integration=args.integration_sha)
    args.repo=args.repo.resolve(); args.output=args.output.resolve()
    if args.output == args.repo or args.repo in args.output.parents:
        parser.error("輸出不可位於原始 repo 內")
    if min(args.cold_repeats,args.rounds,args.model_repeats,args.timeout)<=0:
        parser.error("重複次數與 timeout 必須大於零")
    args.output.mkdir(parents=True,exist_ok=True)
    import fcntl
    with (args.output/"performance.lock").open("a") as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        existing_inputs=args.output/"inputs/manifest.json"
        if existing_inputs.exists() and json.loads(existing_inputs.read_text())["pins"] != PINS:
            parser.error("output 已屬於另一組來源SHA；請另選新output，不能覆蓋或混用舊證據")
        if args.stage in {"prepare","all"}: prepare(args)
        if args.stage in {"build","all"}: build(args)
        if args.stage in {"measure","all"}: measure(args)
        if args.stage in {"profile","all"}: measure(args,profiling=True)


if __name__ == "__main__":
    main()
