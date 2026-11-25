"""固定兩個單例、兩種 CPU 配額。測試退出碼與資源讀值均原樣保留。"""
import hashlib
import json
import os
from pathlib import Path
import re
import resource
import subprocess
import sys
import time


TESTS = {
    "r363": "tests.test_r363_native_merge.R363NativeMerge.test_scenario_verification_accepts_complete_mixed_scene",
    "beam": "tests.test_bridge_integrity.IntegrityTests.test_beam_centers_survive_repeated_reload",
}
BRIDGE = Path("/tmp/geometry-tests/bridge")
CG = Path("/sys/fs/cgroup")
METRICS = ("cpu.max", "cpu.stat", "cpu.pressure", "cpuset.cpus.effective",
           "memory.max", "memory.high", "memory.swap.max", "memory.events")


def write(path, result):
    path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")


def sample():
    relative = next(row[3:] for row in Path("/proc/self/cgroup").read_text().splitlines()
                    if row.startswith("0::"))
    leaf = CG / relative.lstrip("/")
    ancestry = []
    for path in (leaf, *leaf.parents):
        if path != CG and CG not in path.parents:
            break
        props = {key: (path / key).read_text().strip() for key in METRICS if (path / key).is_file()}
        ancestry.append({"path": str(path), **props})
    return {"monotonic_ns": time.monotonic_ns(), "realtime_ns": time.time_ns(),
            "cpu_affinity": sorted(os.sched_getaffinity(0)), "cgroups": ancestry,
            "loadavg": Path("/proc/loadavg").read_text().strip()}


def bridge_traces(casedir):
    found = []
    for path in sorted(casedir.glob("exec.trace.*")):
        lines = path.read_text(errors="replace").splitlines()
        start = next((line for line in lines if f'execve("{BRIDGE}",' in line and line.rstrip().endswith("= 0")), None)
        if start is None:
            continue
        end = next((line for line in reversed(lines) if "+++ exited with" in line or "+++ killed by" in line), None)
        found.append({"pid": int(path.name.split(".")[-1]), "start": start, "end": end,
                      "wall_seconds": round(float(end.split()[0])-float(start.split()[0]), 6) if end else None})
    return sorted(found, key=lambda row: row["start"])


def main():
    arm, case, output = sys.argv[1:]
    casedir = Path(output)
    casedir.mkdir(parents=True, exist_ok=True)
    env = {**os.environ, "TMPDIR": str(casedir / "tmp"), "GEOMETRY_TEST_BRIDGE": str(BRIDGE),
           "PYTHONDONTWRITEBYTECODE": "1", "PYTHONHASHSEED": "0"}
    Path(env["TMPDIR"]).mkdir(exist_ok=False)
    program = ["/usr/bin/strace", "--seccomp-bpf", "-ff", "-ttt", "-e", "trace=execve,exit_group",
               "-o", str(casedir / "exec.trace"), sys.executable, "-B", "-m", "unittest", "-v", TESTS[case]]
    before = sample()
    cpu_max = before["cgroups"][0]["cpu.max"].split()
    if arm == "quota25":
        assert cpu_max == ["25000", "100000"], cpu_max
    else:
        assert cpu_max[0] == "max", cpu_max
    start = time.monotonic()
    with (casedir / "unittest.log").open("wb") as log:
        child = subprocess.run(program, stdout=log, stderr=subprocess.STDOUT, env=env)
    elapsed = time.monotonic() - start
    after = sample()
    raw = (casedir / "unittest.log").read_text(errors="replace")
    if not re.search(r"^Ran 1 test in ", raw, re.M) or re.search(r"\bskipped\b", raw, re.I):
        raise ValueError("未執行一個正常單例或出現略過，見 unittest.log")
    durations = bridge_traces(casedir)
    if not durations or any(row["end"] is None for row in durations):
        raise ValueError("缺少 bridge 啟動／結束事件，見原始 strace")
    results = {"arm": arm, "test": TESTS[case], "command": program, "exit": child.returncode,
               "test_wall_seconds": round(elapsed, 6), "before": before, "after": after,
               "bridge_runs": durations, "bridge_sha256": hashlib.sha256(BRIDGE.read_bytes()).hexdigest(),
               "stack_limits": resource.getrlimit(resource.RLIMIT_STACK),
               "uid": os.getuid(), "python": sys.version, "kernel": os.uname().release}
    write(casedir / "case.json", results)
    print(json.dumps({key: results[key] for key in ["arm", "test", "exit", "test_wall_seconds", "bridge_runs"]}))


if __name__ == "__main__":
    main()
