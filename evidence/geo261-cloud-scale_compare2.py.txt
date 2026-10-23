#!/usr/bin/env python3
"""Load-time vs timber count N, two SHAs, through web_bridge loadfile (same path as drafts/issue300/bench/drive.py).

usage: scale_compare2.py <workdir> <outdir> <label=srcdir> <label=srcdir> [--ns 16,32,48,64] [--reps 3] [--timeout 600]
Each srcdir must already contain a built `bridge` (web_bridge.c compiled with -std=c11 -O2 -lm).
Order alternates per round so neither side always runs first. Every loadfile response is checked for ok.
"""
import argparse, json, os, statistics, subprocess, sys, time

ap = argparse.ArgumentParser()
ap.add_argument("work"); ap.add_argument("out"); ap.add_argument("sides", nargs="+")
ap.add_argument("--ns", default="16,32,48,64"); ap.add_argument("--reps", type=int, default=3)
ap.add_argument("--timeout", type=float, default=600.0)
ap.add_argument("--gen", default="/mnt/d/geometry-axiom-work/drafts/issue300/bench/gen_scene.py")
a = ap.parse_args()
sides = [s.split("=", 1) for s in a.sides]
ns = [int(x) for x in a.ns.split(",")]
os.makedirs(a.out, exist_ok=True)
tsv = open(os.path.join(a.out, "samples.tsv"), "w", encoding="utf-8")
tsv.write("n\tround\tside\tstatus\tok\tseconds\tdetail\n")


def one_load(bridge, scene):
    p = subprocess.Popen(["bash", "-c", 'ulimit -c 0; ulimit -S -s 16384 || exit 126; exec "$@"', "x", bridge],
                         stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    t0 = time.perf_counter()
    try:
        out, err = p.communicate(("loadfile " + scene + "\n").encode(), timeout=a.timeout)
    except subprocess.TimeoutExpired:
        p.kill(); p.communicate()
        return "timeout", None, time.perf_counter() - t0, ""
    dt = time.perf_counter() - t0
    line = out.decode("utf-8", "replace").splitlines()[:1]
    if not line:
        return "eof rc=%s" % p.returncode, None, dt, err.decode("utf-8", "replace")[-200:]
    try:
        resp = json.loads(line[0])
    except ValueError:
        return "badjson", None, dt, line[0][:200]
    ok = resp.get("ok")
    return "ok", ok, dt, "" if ok else json.dumps(resp, ensure_ascii=False)[:300]


summary = {}
for n in ns:
    scene = os.path.join(a.work, "s%d.scene" % n)
    with open(scene, "wb") as fh:
        subprocess.check_call([sys.executable, a.gen, str(n), "--family", "single"], stdout=fh)
    for r in range(a.reps):
        order = sides if r % 2 == 0 else sides[::-1]
        for label, src in order:
            st, ok, dt, detail = one_load(os.path.join(src, "bridge"), scene)
            tsv.write("%d\t%d\t%s\t%s\t%s\t%.4f\t%s\n" % (n, r, label, st, ok, dt, detail.replace("\t", " ").replace("\n", " ")))
            tsv.flush()
            print("n=%d round=%d %s %s ok=%s %.3fs %s" % (n, r, label, st, ok, dt, detail[:120]), flush=True)
            if st == "ok" and ok:
                summary.setdefault((n, label), []).append(dt)
            if st == "timeout":
                break
lines = []
for n in ns:
    row = ["N=%d" % n]
    for label, _ in sides:
        v = summary.get((n, label))
        row.append("%s median %s (%s)" % (label, "%.3f" % statistics.median(v) if v else "-", ",".join("%.3f" % x for x in v or [])))
    va = summary.get((n, sides[0][0]))
    for label, _ in sides[1:]:
        vb = summary.get((n, label))
        if va and vb:
            row.append("ratio %s/%s %.3f" % (label, sides[0][0], statistics.median(vb) / statistics.median(va)))
    lines.append("  ".join(row))
open(os.path.join(a.out, "summary.txt"), "w", encoding="utf-8").write("\n".join(lines) + "\n")
print("\n".join(lines))
