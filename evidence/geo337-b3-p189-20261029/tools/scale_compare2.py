#!/usr/bin/env python3
"""Load-time vs timber count N, two SHAs, through web_bridge loadfile (same path as drafts/issue300/bench/drive.py).

usage: scale_compare2.py <workdir> <outdir> <label=srcdir> <label=srcdir> [--ns 16,32,48,64] [--reps 3] [--timeout 600]
Each srcdir must already contain a built `bridge` (web_bridge.c compiled with -std=c11 -O2 -lm).
Order alternates per round so neither side always runs first. Every loadfile response is checked for ok.
"""
import argparse, hashlib, json, os, statistics, subprocess, sys, time

ap = argparse.ArgumentParser()
ap.add_argument("work"); ap.add_argument("out"); ap.add_argument("sides", nargs="+")
ap.add_argument("--ns", default="16,32,48,64"); ap.add_argument("--reps", type=int, default=3)
ap.add_argument("--timeout", type=float, default=600.0)
ap.add_argument("--gen", default="/tmp/g261r3/tools/gen_scene.py")
a = ap.parse_args()
sides = [s.split("=", 1) for s in a.sides]
ns = [int(x) for x in a.ns.split(",")]
os.makedirs(a.out, exist_ok=True)
tsv = open(os.path.join(a.out, "samples.tsv"), "w", encoding="utf-8")
tsv.write("n\tround\tside\tstatus\tok\tseconds\tdetail\n")


LOADFILE_SAMPLE_RECORDS = []


def record_loadfile_sample(bridge, scene, sample, out, err, seconds, returncode, timeout_error=None):
    # 所有檔案寫入都在原 dt 計算之後，不納入載入時間。
    ended = time.time()
    index = len(LOADFILE_SAMPLE_RECORDS) + 1
    relative = os.path.join('loadfile-sample-raw', '%06d' % index)
    directory = os.path.join(a.out, relative)
    os.makedirs(directory, exist_ok=False)
    payload = ('loadfile ' + scene + '\n').encode()
    files = {}
    for name, data in [('stdin.bin', payload), ('stdout.bin', out), ('stderr.bin', err)]:
        with open(os.path.join(directory, name), 'wb') as stream:
            stream.write(data)
        files[name] = {'path': os.path.join(relative, name), 'bytes': len(data),
                       'sha256': hashlib.sha256(data).hexdigest()}
    timeout = None
    if timeout_error is not None:
        timeout = {'type': type(timeout_error).__name__, 'message': str(timeout_error)}
        for name, data in [('timeout-partial.stdout.bin', timeout_error.stdout),
                           ('timeout-partial.stderr.bin', timeout_error.stderr)]:
            data = data if data is not None else b''
            with open(os.path.join(directory, name), 'wb') as stream:
                stream.write(data)
            files[name] = {'path': os.path.join(relative, name), 'bytes': len(data),
                           'sha256': hashlib.sha256(data).hexdigest()}
    load_ok = None
    try:
        response = json.loads(out.splitlines()[0])
        if isinstance(response, dict):
            load_ok = response.get('ok')
    except (IndexError, ValueError):
        pass
    row = {'index': index, **sample,
           'command': ['bash', '-c', 'ulimit -c 0; ulimit -S -s 16384 || exit 126; exec "$@"', 'x', bridge],
           'cwd': os.getcwd(), 'scene': scene, 'actual_process_returncode': returncode,
           'timeout_expired': timeout_error is not None, 'timeout_exception': timeout,
           'started_epoch_utc_derived_from_duration': ended - seconds, 'ended_epoch_utc': ended,
           'seconds': seconds, 'load_ok': load_ok, 'files': files}
    with open(os.path.join(directory, 'receipt.json'), 'w', encoding='utf-8') as stream:
        json.dump(row, stream, ensure_ascii=False, indent=2)
        stream.write('\n')
    LOADFILE_SAMPLE_RECORDS.append(row)
    with open(os.path.join(a.out, 'loadfile-samples.json'), 'w', encoding='utf-8') as stream:
        json.dump(LOADFILE_SAMPLE_RECORDS, stream, ensure_ascii=False, indent=2)
        stream.write('\n')


def one_load(bridge, scene, sample):
    p = subprocess.Popen(['bash', '-c', 'ulimit -c 0; ulimit -S -s 16384 || exit 126; exec "$@"', 'x', bridge],
                         stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    t0 = time.perf_counter()
    try:
        out, err = p.communicate(("loadfile " + scene + "\n").encode(), timeout=a.timeout)
    except subprocess.TimeoutExpired as error:
        p.kill(); out, err = p.communicate()
        dt = time.perf_counter() - t0
        record_loadfile_sample(bridge, scene, sample, out, err, dt, p.returncode, error)
        return "timeout", None, dt, ""
    dt = time.perf_counter() - t0
    record_loadfile_sample(bridge, scene, sample, out, err, dt, p.returncode)
    # ok:true 後非零結束也不算成功；原裁判忽略了真實退出碼。
    if p.returncode != 0:
        return "exit rc=%s" % p.returncode, None, dt, err.decode("utf-8", "replace")[-200:]
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
            st, ok, dt, detail = one_load(os.path.join(src, "bridge"), scene, {"n": n, "round": r, "side": label})
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
