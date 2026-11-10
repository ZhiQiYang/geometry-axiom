#!/usr/bin/env python3
"""Temporary, read-only-in-repo C CPU profiler for PR #348 H7.

Run from the exact b245a252 checkout root on a Linux Actions runner:
  python3 /tmp/r348_h7_cpu_profile.py --out /tmp/r348-h7-profile \
      --phases line-128,line-256,line-384,load-512

Optional additional slow-runner stress (profiling, NOT an acceptance test):
  --phases line-512

All source objects are compiled by the project's *original* NativeBuild at
its original -O0. An external CC wrapper adds -pg/-g/frame pointers to the
same objects and link. gprof/call-graph profiles, per-command JSONL, CPU
metadata and build receipts are written outside the repo. No product or test
source, timeout, golden, expected value or mutation ledger is modified.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import shutil
import signal
import subprocess
import sys
import tempfile
import threading
import time

BASE = "b245a252ea562f3c1d30186cbfa589e77e60ecb1"
TEST_BLOB = "882a0b8ea3fd18b57718e33e3f551a0f320207d9"
PHASES = {"line-128", "line-256", "line-384", "line-512", "load-512"}


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write_json(path, data):
    Path(path).write_text(json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def command(*args):
    p = subprocess.run(args, capture_output=True, text=True)
    if p.returncode:
        raise RuntimeError("command failed: %s: %s" % (args, p.stderr.strip()))
    return p.stdout.strip()


def cpu_metadata():
    info = {"python": sys.version, "platform": platform.platform(),
            "machine": platform.machine(), "cpu_count": os.cpu_count(),
            "compiler": command("cc", "--version").splitlines()[0]}
    for filename, key in (("/proc/cpuinfo", "cpuinfo"),
                          ("/sys/fs/cgroup/cpu.max", "cgroup_cpu_max"),
                          ("/proc/sys/kernel/perf_event_paranoid", "perf_event_paranoid")):
        try:
            content = Path(filename).read_text()
            if key == "cpuinfo":
                info["cpu_model"] = next((line.split(":", 1)[1].strip()
                                          for line in content.splitlines()
                                          if line.lower().startswith("model name")), "unknown")
                info["cpu_mhz"] = next((line.split(":", 1)[1].strip()
                                        for line in content.splitlines()
                                        if line.lower().startswith("cpu mhz")), "unknown")
            else:
                info[key] = content.strip()
        except OSError as exc:
            info[key + "_error"] = str(exc)
    return info


def prepare_cc_wrapper(out):
    compiler = shutil.which(os.environ.get("CC", "cc"))
    if not compiler:
        raise RuntimeError("C compiler not available")
    wrapper = out / "r348-profile-cc"
    wrapper.write_text('#!/bin/sh\nexec "$R348_REAL_CC" -pg -g -fno-omit-frame-pointer "$@"\n', encoding="ascii")
    wrapper.chmod(0o755)
    os.environ["R348_REAL_CC"] = compiler
    os.environ["CC"] = str(wrapper)
    return compiler, wrapper


def memory_peak(pid):
    try:
        for line in Path("/proc/%d/status" % pid).read_text().splitlines():
            if line.startswith("VmHWM:"):
                return int(line.split()[1])
    except (OSError, ValueError, IndexError):
        pass
    return None


def run_protocol(name, executable, statements, out, seconds=600):
    """Execute real line protocol; never convert an error into success."""
    out.mkdir(parents=True, exist_ok=True)
    prefix = out / (name + ".gmon")
    env = dict(os.environ, GMON_OUT_PREFIX=str(prefix))
    stderr_path = out / (name + ".stderr")
    jsonl_path = out / (name + ".commands.jsonl")
    expired = threading.Event()
    sent = 0
    error = None
    started = time.monotonic()
    with stderr_path.open("wb") as stderr_file, jsonl_path.open("w", encoding="utf-8") as timing:
        p = subprocess.Popen([str(executable)], stdin=subprocess.PIPE,
                             stdout=subprocess.PIPE, stderr=stderr_file,
                             env=env, start_new_session=True)
        def expire():
            if p.poll() is None:
                expired.set()
                try:
                    os.killpg(p.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
        watchdog = threading.Timer(seconds, expire)
        watchdog.daemon = True
        watchdog.start()
        try:
            for i, statement in enumerate(statements):
                t0 = time.monotonic()
                try:
                    p.stdin.write((statement + "\n").encode("utf-8"))
                    p.stdin.flush()
                    reply = p.stdout.readline()
                except (BrokenPipeError, OSError) as exc:
                    error = "child-io: " + repr(exc)
                    break
                elapsed = time.monotonic() - t0
                row = {"index": i, "command": statement[:96],
                       "verb": statement.split(" ", 2)[1] if statement.startswith("line ") else statement.split(" ", 1)[0],
                       "elapsed_seconds": round(elapsed, 6), "reply_bytes": len(reply),
                       "child_peak_kib": memory_peak(p.pid), "child_pid": p.pid}
                sent += 1
                if not reply:
                    error = "missing-reply"
                    row["error"] = error
                else:
                    row["reply_sha256"] = hashlib.sha256(reply).hexdigest()
                    try:
                        value = json.loads(reply)
                        if value.get("ok") is not True:
                            error = "rejected-command: " + statement[:96]
                            row["error"] = error
                            row["response_error"] = str(value.get("error", ""))[:300]
                    except (ValueError, AttributeError) as exc:
                        error = "invalid-json: " + repr(exc)
                        row["error"] = error
                timing.write(json.dumps(row, ensure_ascii=False) + "\n")
                timing.flush()
                if error:
                    break
        finally:
            try:
                p.stdin.close()
            except OSError:
                pass
            # Exit normally for gmon; otherwise the watchdog enforces the
            # original 600-s limit on this independent diagnostic case.
            try:
                p.wait(timeout=max(0, seconds - (time.monotonic() - started)))
            except subprocess.TimeoutExpired:
                expire()
                p.wait()
            watchdog.cancel()
            watchdog.join()
            p.stdout.close()
    if expired.is_set():
        error = "TIMEOUT (600-s independent profile ceiling)"
    if p.returncode != 0 and not error:
        error = "nonzero-child-exit: %d" % p.returncode
    receipt = {"name": name, "commands_expected": len(statements),
               "commands_replied": sent, "exit": p.returncode, "error": error,
               "elapsed_seconds": round(time.monotonic() - started, 3),
               "peak_kib": memory_peak(p.pid),
               "commands_sha256": sha256(jsonl_path),
               "stderr_sha256": sha256(stderr_path),
               "timeout_seconds": seconds}
    write_json(out / (name + ".receipt.json"), receipt)
    return receipt


def gprof_report(name, exe, out):
    profiles = sorted(out.glob(name + ".gmon.*"))
    if not profiles:
        return {"status": "no-gmon-normal-exit-required"}
    if shutil.which("gprof") is None:
        return {"status": "gprof-unavailable", "files": [p.name for p in profiles]}
    reports = []
    for data in profiles:
        p = subprocess.run(["gprof", "-b", str(exe), str(data)],
                           capture_output=True, text=True)
        target = out / (data.name + ".gprof.txt")
        target.write_text(p.stdout + "\nSTDERR:\n" + p.stderr, encoding="utf-8")
        reports.append({"gmon": data.name, "gmon_sha256": sha256(data),
                        "gprof_exit": p.returncode, "report": target.name,
                        "report_sha256": sha256(target)})
    return {"status": "collected", "reports": reports}


def source_and_phase(root, name, out):
    from tests import geo300_scene_generator
    count = int(name.split("-")[1])
    text, _ = geo300_scene_generator.build(count, "single")
    fixture = out / (name + ".scene")
    fixture.write_bytes(text.encode("utf-8"))
    if name.startswith("load-"):
        steps = ["reset", "loadfile " + str(fixture)]
    else:
        steps = ["reset"] + ["line " + line for line in text.splitlines()
                             if line.strip() and not line.lstrip().startswith("#")]
    return steps, {"scene": fixture.name, "scene_sha256": sha256(fixture),
                   "statements": len(steps)}


def self_test():
    with tempfile.TemporaryDirectory() as folder:
        out = Path(folder)
        fake = out / "fake-bridge"
        fake.write_text("#!/usr/bin/env python3\nimport sys,json\nfor s in sys.stdin:\n"
                        " if s.strip()=='die':sys.exit(3)\n"
                        " print(json.dumps({'ok':s.strip()!='bad'}),flush=True)\n", encoding="utf-8")
        fake.chmod(0o755)
        ok = run_protocol("control-valid", fake, ["reset", "line timber 1"], out)
        assert ok["error"] is None and ok["commands_replied"] == 2, ok
        bad = run_protocol("M_REJECTED_REPLY", fake, ["bad"], out)
        assert isinstance(bad["error"], str) and bad["error"].startswith("rejected-command"), bad
        dead = run_protocol("M_MISSING_REPLY", fake, ["die"], out)
        assert dead["error"] == "missing-reply", dead
        cc, wrapper = prepare_cc_wrapper(out)
        assert "-pg -g -fno-omit-frame-pointer" in wrapper.read_text()
        assert command(str(wrapper), "--version"), "M_DROP_PG_BUILD_WRAPPER"
        csrc = out / "profile-echo.c"
        csrc.write_text('#include <stdio.h>\nint main(void){char b[64];while(fgets(b,sizeof b,stdin)){puts("{\\"ok\\":true}");fflush(stdout);}return 0;}\n', encoding="ascii")
        binary = out / "profile-echo"
        subprocess.run([str(wrapper), "-O0", str(csrc), "-o", str(binary)],
                       check=True, capture_output=True)
        live = run_protocol("M_GMON_ACTUAL_PROGRAM", binary, ["reset", "line timber 1"], out)
        report = gprof_report("M_GMON_ACTUAL_PROGRAM", binary, out)
        assert live["error"] is None and report["status"] == "collected", (live, report)
        cpu = cpu_metadata()
        assert cpu["cpu_count"] and cpu.get("cpu_model"), "M_DROP_CPU_MODEL"
        print("control-valid PASS; M_REJECTED_REPLY detected; "
              "M_MISSING_REPLY detected; M_DROP_PG_BUILD_WRAPPER detected; "
              "M_GMON_ACTUAL_PROGRAM detected; M_DROP_CPU_MODEL detected")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", default="/tmp/r348-h7-cpu-profile")
    parser.add_argument("--phases", default="line-128,line-256,line-384,load-512")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return 0
    if os.name != "posix" or not Path("/proc/cpuinfo").exists():
        raise SystemExit("This profiler requires a Linux Actions runner")
    root = Path.cwd().resolve()
    if command("git", "rev-parse", "HEAD") != BASE:
        raise SystemExit("Refusing an unpinned checkout: expected " + BASE)
    if command("git", "rev-parse", "HEAD:tests/test_geo261_timber_capacity_host.py") != TEST_BLOB:
        raise SystemExit("H7 test blob is not the originally reviewed source")
    phases = args.phases.split(",")
    if not phases or any(phase not in PHASES for phase in phases):
        raise SystemExit("Allowed phases: " + ",".join(sorted(PHASES)))
    out = Path(args.out).resolve()
    out.mkdir(parents=True, exist_ok=True)
    compiler, wrapper = prepare_cc_wrapper(out)
    write_json(out / "environment.json", {"base": BASE, "H7_test_blob": TEST_BLOB,
               "compiler_path": compiler, "cc_wrapper": str(wrapper), **cpu_metadata()})
    sys.path.insert(0, str(root))
    from tests.test_geo261_native_kernel import native
    build = native()
    executable = build.bridge()
    # The ordinary NativeBuild remains in control of its object list, -O0,
    # closure defines and link. Only -pg/-g/frame pointers are added externally.
    write_json(out / "build-log.json", build.logs)
    results = []
    for phase in phases:
        steps, source = source_and_phase(root, phase, out)
        receipt = run_protocol(phase, executable, steps, out)
        result = {"fixture": source, "receipt": receipt,
                  "gprof": gprof_report(phase, executable, out)}
        results.append(result)
        write_json(out / "summary.json", {"base": BASE, "results": results})
    if any(r["receipt"]["error"] for r in results):
        print("Some profiling cases did not complete; consult summary.json; this is NOT H7 acceptance", file=sys.stderr)
        return 1
    print("Profiler complete. Profiling results are NOT a replacement for original H7 or 12/12 CI.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
