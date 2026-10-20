#!/usr/bin/env python3
"""P-189 Linux 複測；保留交接腳本的編譯旗標、程序計時與正反交錯順序。"""
import argparse
import copy
import datetime
import hashlib
import io
import json
import os
from pathlib import Path
import platform
import statistics
import subprocess
import sys
import tarfile
import time

NS = (16, 32, 48, 64)
LABELS = ("main", "base", "final")
REFS = ("adbaebf9", "3e600772", "7dae5f21")


def sha(data):
    return hashlib.sha256(data).hexdigest()


def write_json(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def validate_timing(samples, reps=3):
    errors, summary = [], []
    for n in NS:
        medians = {}
        for label in LABELS:
            rows = [s for s in samples if s["n"] == n and s["side"] == label]
            if len(rows) != reps or {s["round"] for s in rows} != set(range(reps)):
                errors.append(f"N={n} {label} 樣本輪次不完整：{len(rows)}/{reps}")
            bad = [s for s in rows if s["status"] != "ok" or s["ok"] is not True or s["returncode"] != 0]
            if bad:
                errors.append(f"N={n} {label} 載入失敗：{len(bad)} 筆")
            if len(rows) == reps and not bad:
                medians[label] = statistics.median(s["seconds"] for s in rows)
        row = {"n": n, "median_seconds": medians}
        if "main" in medians and "final" in medians:
            ratio = medians["final"] / medians["main"]
            row["final_main_ratio"] = ratio
            row["threshold_pass"] = ratio <= 2.0
            if ratio > 2.0:
                errors.append(f"P-189 N={n} final/main={ratio:.6f} > 2.0")
        summary.append(row)
    return {"pass": not errors, "errors": errors, "summary": summary}


def validator_selftest():
    good = [{"n": n, "round": r, "side": label, "status": "ok", "ok": True,
             "returncode": 0, "seconds": 1.0} for n in NS for r in range(3) for label in LABELS]
    cases = []
    cases.append(("正常對照", good, True, None))
    slow = copy.deepcopy(good)
    for s in slow:
        if s["n"] == 64 and s["side"] == "final":
            s["seconds"] = 2.01
    cases.append(("超過門檻", slow, False, "P-189 N=64"))
    cases.append(("缺樣本", good[:-1], False, "樣本輪次不完整"))
    refused = copy.deepcopy(good)
    refused[0]["ok"] = False
    cases.append(("載入遭拒", refused, False, "載入失敗"))
    crashed = copy.deepcopy(good)
    crashed[0]["returncode"] = -11
    cases.append(("程序崩潰", crashed, False, "載入失敗"))
    result = []
    for name, sample, expected, diagnostic in cases:
        actual = validate_timing(sample)
        assert actual["pass"] == expected, (name, actual)
        assert diagnostic is None or any(diagnostic in e for e in actual["errors"]), (name, actual)
        result.append({"case": name, "expected_pass": expected, "actual": actual})
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("phase", choices=("build", "equivalence", "timing", "check", "selftest", "all"))
    parser.add_argument("--repo", default="/workspace/geometry-axiom")
    parser.add_argument("--work", default="/workspace/geo261-perf-src")
    parser.add_argument("--out", default="/workspace/geo261-evidence/p189")
    parser.add_argument("--gen", default="/workspace/geo261-handoff/handoff/drafts/issue300/bench/gen_scene.py")
    parser.add_argument("--final", default=REFS[2])
    parser.add_argument("--timeout", type=float, default=900)
    args = parser.parse_args()
    repo, work, out = Path(args.repo), Path(args.work), Path(args.out)
    work.mkdir(parents=True, exist_ok=True)
    out.mkdir(parents=True, exist_ok=True)
    refs = dict(zip(LABELS, (*REFS[:2], args.final)))
    commits = {label: subprocess.check_output(["git", "rev-parse", f"{rev}^{{commit}}"], cwd=repo).decode().strip()
               for label, rev in refs.items()}
    source = {label: work / commits[label][:8] for label in LABELS}
    phases = {"build", "equivalence", "timing", "check", "selftest"} if args.phase == "all" else {args.phase}
    if "selftest" in phases:
        write_json(out / "validator-selftest.json", validator_selftest())
        print("收據判定器自證通過：正常、超標、缺樣本、載入遭拒、程序崩潰", flush=True)
    if "build" in phases:
        environment = {"started_utc": now(), "commits": commits, "platform": platform.platform(),
                       "gcc": subprocess.check_output(["gcc", "--version"]).decode().splitlines()[0],
                       "python": sys.version, "generator_sha256": sha(Path(args.gen).read_bytes()),
                       "runner_sha256": sha(Path(__file__).read_bytes()), "loadavg": os.getloadavg(),
                       "compile_flags": ["-std=c11", "-O2", "-lm"], "stack_kib": 16384,
                       "method": "每 N 三輪；偶數輪 main/base/final、奇數輪 final/base/main；獨立程序的 loadfile wall time，與交接腳本相同；不扣啟動成本"}
        write_json(out / "environment.json", environment)
        builds = []
        for label in LABELS:
            source[label].mkdir(parents=True, exist_ok=True)
            paths = ["current_geometry.c", "geometry-core", "geometry-app", "geometry-templates", "geometry-web"]
            paths = [p for p in paths if subprocess.run(["git", "cat-file", "-e", f"{commits[label]}:{p}"], cwd=repo, stderr=subprocess.DEVNULL).returncode == 0]
            excludes = [":(exclude)" + p for p in ("geometry-core/domain-decoupling", "geometry-web/docs", "geometry-web/prototypes", "geometry-web/vendor", "geometry-web/node_modules")]
            archive = subprocess.check_output(["git", "archive", "--format=tar", commits[label], "--", *paths, *excludes], cwd=repo)
            with tarfile.open(fileobj=io.BytesIO(archive), mode="r:") as tf:
                tf.extractall(source[label], filter="data")
            command = ["gcc", "-std=c11", "-O2", "geometry-web/web_bridge.c", "-o", "bridge", "-lm"]
            t0 = time.perf_counter()
            with (out / f"build-{label}.log").open("wb") as log:
                result = subprocess.run(command, cwd=source[label], stdout=log, stderr=subprocess.STDOUT)
            record = {"label": label, "sha": commits[label], "command": command, "cwd": str(source[label]),
                      "returncode": result.returncode, "seconds": time.perf_counter() - t0}
            if result.returncode == 0:
                record["binary_sha256"] = sha((source[label] / "bridge").read_bytes())
            builds.append(record)
            write_json(out / "build-receipt.json", builds)
            print(f"建置 {label} rc={result.returncode} {record['seconds']:.3f}s", flush=True)
            if result.returncode:
                return 2
    scenes = work / "scenes"
    scenes.mkdir(exist_ok=True)
    if phases & {"equivalence", "timing"}:
        for n in NS:
            with (scenes / f"s{n}.scene").open("wb") as fh:
                subprocess.run([sys.executable, args.gen, str(n), "--family", "single"], stdout=fh, check=True)

    def run_bridge(label, scene, dump, logstem):
        command = ["bash", "-c", 'ulimit -c 0; ulimit -S -s 16384 || exit 126; exec "$@"', "x", str(source[label] / "bridge")]
        p = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        t0 = time.perf_counter()
        timed_out = False
        try:
            stdout, stderr = p.communicate((f"loadfile {scene}\n" + ("dump\n" if dump else "")).encode(), timeout=args.timeout)
        except subprocess.TimeoutExpired:
            timed_out = True
            p.kill()
            stdout, stderr = p.communicate()
        elapsed = time.perf_counter() - t0
        (out / f"{logstem}.stdout").write_bytes(stdout)
        (out / f"{logstem}.stderr").write_bytes(stderr)
        try:
            responses = [json.loads(line) for line in stdout.splitlines()]
            valid = len(responses) == (2 if dump else 1) and all(isinstance(r, dict) for r in responses)
        except (ValueError, TypeError):
            responses, valid = [], False
        return {"status": "timeout" if timed_out else "ok" if p.returncode == 0 and valid else "bad-response",
                "ok": responses[0].get("ok") if responses else None, "returncode": p.returncode,
                "seconds": elapsed, "stdout_sha256": sha(stdout), "stdout_bytes": len(stdout),
                "responses": responses, "stdout_file": f"{logstem}.stdout", "stderr_file": f"{logstem}.stderr"}

    if "equivalence" in phases:
        dumpdir = out / "dump"
        dumpdir.mkdir(exist_ok=True)
        names = subprocess.check_output(["git", "ls-tree", "--name-only", commits["base"]], cwd=repo).decode().splitlines()
        scene_paths = [(f"s{n}.scene", scenes / f"s{n}.scene", True) for n in NS]
        for name in names:
            if name.endswith(".scene"):
                path = scenes / ("repo-" + name)
                path.write_bytes(subprocess.check_output(["git", "show", f"{commits['base']}:{name}"], cwd=repo))
                scene_paths.append((name, path, False))
        rows = []
        for name, path, generated in scene_paths:
            sides = {label: run_bridge(label, path, True, f"dump/{name}-{label}") for label in LABELS}
            identical = sides["base"]["stdout_sha256"] == sides["final"]["stdout_sha256"]
            all_three_identical = len({r["stdout_sha256"] for r in sides.values()}) == 1
            valid = all(r["status"] == "ok" and (not generated or all(x.get("ok") is True for x in r["responses"]))
                        for label, r in sides.items() if generated or label in ("base", "final"))
            row = {"scene": name, "scene_sha256": sha(path.read_bytes()), "generated": generated,
                   "identical": identical, "all_three_identical": all_three_identical,
                   "valid_execution": valid, "sides": sides}
            rows.append(row)
            write_json(out / "dump-equivalence.json", {"commits": commits, "pass": all(r["identical"] and r["valid_execution"] for r in rows), "complete": len(rows) == len(scene_paths), "scenes": rows})
            print(f"dump {name}: base/final {'逐位元組相同' if identical else '不同'}，三方相同={all_three_identical}，執行有效={valid}", flush=True)
    if "timing" in phases:
        (out / "timing").mkdir(exist_ok=True)
        samples = []
        tsv = (out / "samples.tsv").open("w", encoding="utf-8")
        tsv.write("n\tround\tside\tstatus\tok\treturncode\tseconds\n")
        for n in NS:
            for round_number in range(3):
                for label in LABELS if round_number % 2 == 0 else LABELS[::-1]:
                    row = run_bridge(label, scenes / f"s{n}.scene", False, f"timing/n{n}-r{round_number}-{label}")
                    row.update(n=n, round=round_number, side=label, sha=commits[label], loadavg=os.getloadavg())
                    samples.append(row)
                    write_json(out / "samples.json", samples)
                    tsv.write(f"{n}\t{round_number}\t{label}\t{row['status']}\t{row['ok']}\t{row['returncode']}\t{row['seconds']:.9f}\n")
                    tsv.flush()
                    print(f"N={n} round={round_number} {label} {row['status']} ok={row['ok']} rc={row['returncode']} {row['seconds']:.6f}s", flush=True)
        tsv.close()
        write_json(out / "timing-receipt.json", {"commits": commits, "finished_utc": now(), **validate_timing(samples)})
    if "check" in phases:
        samples = json.loads((out / "samples.json").read_text())
        timing = validate_timing(samples)
        equivalence = json.loads((out / "dump-equivalence.json").read_text())
        receipt = {"checked_utc": now(), "commits": commits, "timing": timing,
                   "dump_pass": equivalence["pass"] and equivalence["complete"], "scene_count": len(equivalence["scenes"])}
        receipt["pass"] = timing["pass"] and receipt["dump_pass"]
        receipt["exit_code"] = 0 if receipt["pass"] else 1
        write_json(out / "receipt.json", receipt)
        print(json.dumps(receipt, ensure_ascii=False, indent=2), flush=True)
        return receipt["exit_code"]
    return 0


if __name__ == "__main__":
    sys.exit(main())
