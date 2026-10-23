"""同機依序量測，禁止並行工作；記下完整命令、結束碼與 stdout 指紋。"""
import hashlib
import json
from pathlib import Path
import platform
import resource
import statistics
import subprocess
import sys
import time
from mini_gen import scene

base, fix, main, work = map(lambda p: Path(p).resolve(), sys.argv[1:])
work.mkdir(parents=True, exist_ok=True)
resource.setrlimit(resource.RLIMIT_STACK, (16*1024*1024, resource.getrlimit(resource.RLIMIT_STACK)[1]))
report = {"platform": platform.platform(), "compiler": subprocess.check_output(["gcc", "--version"], text=True).splitlines()[0],
          "stack": resource.getrlimit(resource.RLIMIT_STACK)[0], "builds": {}, "equivalence": [], "samples": [], "medians": {}}
def save():
    (work / "measurements.json").write_text(json.dumps(report, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
def loaded(run):
    if run.returncode: sys.exit(run.returncode)
    assert not run.stderr, run.stderr
    assert all(json.loads(line)["ok"] for line in run.stdout.splitlines()), run.stdout

for name, root in (("base", base), ("fix", fix), ("main", main)):
    command = ["gcc", "-std=c11", "-O2", "geometry-web/web_bridge.c", "-o", str(work / ("bridge-"+name)), "-lm"]
    run = subprocess.run(command, cwd=root, capture_output=True, text=True)
    report["builds"][name] = {"root": str(root), "head": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip(),
                               "command": command, "exit": run.returncode, "stdout": run.stdout, "stderr": run.stderr,
                               "source_sha256": hashlib.sha256((root/"geometry-core/kernel/source.c").read_bytes()).hexdigest() if name != "main" else None}
    save()
    if run.returncode: sys.exit(run.returncode)
    print("編譯", name, "結束碼", run.returncode, flush=True)

for n in (16, 32, 48, 64):
    path = work / f"s{n}.scene"
    path.write_text(scene(n), encoding="utf-8")
    outputs = []
    for name in ("base", "fix"):
        command = [str(work / ("bridge-"+name))]
        data = f"loadfile {path}\ndump\n".encode()
        run = subprocess.run(command, input=data, capture_output=True)
        (work / f"{name}-{n}.stdout").write_bytes(run.stdout)
        outputs.append(run.stdout)
        report["equivalence"].append({"n": n, "version": name, "command": command, "stdin": data.decode(), "exit": run.returncode,
                                      "stdout_bytes": len(run.stdout), "stdout_sha256": hashlib.sha256(run.stdout).hexdigest(),
                                      "stderr": run.stderr.decode()})
        save()
        loaded(run)
    if outputs[0] != outputs[1]: raise AssertionError(f"N={n} stdout 不同")
    print(f"等價 N={n}：逐位元組相同，{len(outputs[0])} bytes", flush=True)

for n in (16, 32, 48, 64):
    # 每回合輪換先後順序，三個版本各三次；只下 loadfile，不含 dump。
    for order in (("base", "fix", "main"), ("fix", "main", "base"), ("main", "base", "fix")):
        for name in order:
            command = [str(work / ("bridge-"+name))]
            data = f"loadfile {work / f's{n}.scene'}\n".encode()
            start = time.perf_counter()
            run = subprocess.run(command, input=data, capture_output=True)
            elapsed = time.perf_counter()-start
            report["samples"].append({"n": n, "version": name, "command": command, "stdin": data.decode(), "exit": run.returncode,
                                      "seconds": elapsed, "stdout": run.stdout.decode(), "stderr": run.stderr.decode()})
            save()
            print(f"N={n} {name} {elapsed:.6f}s 結束碼 {run.returncode}", flush=True)
            loaded(run)
    medians = {name: statistics.median(row["seconds"] for row in report["samples"] if row["n"] == n and row["version"] == name)
               for name in ("base", "fix", "main")}
    medians["fix/main"] = medians["fix"] / medians["main"]
    medians["base/fix"] = medians["base"] / medians["fix"]
    report["medians"][n] = medians
    save()
    print("中位數", n, medians, flush=True)
