#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""issue #300 微基準的分析:讀 bench.tsv,擬合冪次、估算載入時間、判讀「角材容量 512 可行與否」。

    python3 fit.py bench.tsv
    python3 fit.py bench.tsv --min-n 64 --f1-n 110 --house-n 300 --load-limit 30 --stack-margin-mib 2
    python3 fit.py bench.tsv --json fit.json -o fit.md
    python3 fit.py --selftest

只用標準函式庫。輸入可以是不完整的 TSV(預算用完分幾次跑);資料不足的項目會寫「資料不足」而不是丟例外。

判讀用的兩個數字(--load-limit 30 秒、--stack-margin-mib 2 MiB)只是「建議值」,由主迴圈定案。
"""
from __future__ import print_function

import argparse
import json
import math
import os
import sys

STACK_CONTRACT_KIB = 16384
LINE_KINDS = ("line-grid", "line-place", "line-delete", "line-timber")
KINDS = ("load",) + LINE_KINDS
EXPECT_CUBIC = ("line-place", "line-grid", "line-delete")


# ------------------------------------------------------------------------------------------ 讀檔

def read_rows(paths):
    rows = []
    for path in paths:
        with open(path, "r", encoding="utf-8") as fh:
            header = None
            for ln in fh:
                ln = ln.rstrip("\n")
                if not ln or ln.startswith("#"):
                    continue
                parts = ln.split("\t")
                if parts[0] == "N":
                    header = parts
                    continue
                if header is None:
                    continue
                parts += [""] * (len(header) - len(parts))
                d = dict(zip(header, parts))
                try:
                    d["N"] = int(d["N"])
                    d["cap"] = int(d["cap"])
                    d["seconds"] = float(d["seconds"]) if d["seconds"] != "" else 0.0
                    d["rc"] = int(d["rc"])
                    d["stack_kib"] = int(d["stack_kib"]) if d.get("stack_kib", "") != "" else 0
                except (KeyError, ValueError):
                    continue
                rows.append(d)
    return rows


def median(xs):
    s = sorted(xs)
    n = len(s)
    if not n:
        return None
    return s[n // 2] if n % 2 else 0.5 * (s[n // 2 - 1] + s[n // 2])


def series(rows, family, cap, kind):
    """{N: [seconds...]},只收 rc==0 的樣本。"""
    out = {}
    for r in rows:
        if r.get("family") == family and r["cap"] == cap and r["kind"] == kind and r["rc"] == 0 and r["seconds"] > 0:
            out.setdefault(r["N"], []).append(r["seconds"])
    return out


def points_of(ser):
    return sorted((n, median(v)) for n, v in ser.items())


# ------------------------------------------------------------------------------------------ 擬合

def ols(xs, ys):
    n = float(len(xs))
    mx, my = sum(xs) / n, sum(ys) / n
    sxx = sum((x - mx) ** 2 for x in xs)
    if sxx == 0:
        return None
    b = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / sxx
    a = my - b * mx
    ss_tot = sum((y - my) ** 2 for y in ys)
    ss_res = sum((y - (a + b * x)) ** 2 for x, y in zip(xs, ys))
    return b, a, (1 - ss_res / ss_tot) if ss_tot > 0 else 1.0


def loglog_slope(points):
    if len(points) < 2:
        return None
    r = ols([math.log(n) for n, _ in points], [math.log(t) for _, t in points])
    return r[0] if r else None


def local_slopes(points):
    out = []
    for (n0, t0), (n1, t1) in zip(points, points[1:]):
        if n1 > n0 and t0 > 0 and t1 > 0:
            out.append((n0, n1, math.log(t1 / t0) / math.log(float(n1) / n0)))
    return out


def best_poly(points, ks=(1, 2, 3, 4)):
    """t = a + b*N^k 的相對誤差加權最小平方法;回傳 [(k, rel_rms, a, b)] 依誤差排序。需要 >= 4 點。"""
    if len(points) < 4:
        return []
    res = []
    for k in ks:
        xs = [float(n) ** k for n, _ in points]
        ys = [t for _, t in points]
        ws = [1.0 / (y * y) for y in ys]
        sw = sum(ws)
        mx = sum(w * x for w, x in zip(ws, xs)) / sw
        my = sum(w * y for w, y in zip(ws, ys)) / sw
        sxx = sum(w * (x - mx) ** 2 for w, x in zip(ws, xs))
        if sxx == 0:
            continue
        b = sum(w * (x - mx) * (y - my) for w, x, y in zip(ws, xs, ys)) / sxx
        a = my - b * mx
        if b < 0:
            continue
        rel = math.sqrt(sum(((a + b * x) / y - 1.0) ** 2 for x, y in zip(xs, ys)) / len(xs))
        res.append((k, rel, a, b))
    return sorted(res, key=lambda t: t[1])


def describe_slope(s):
    if s is None:
        return "資料不足"
    if s < 0.5:
        return "近乎常數(固定成本主導)"
    if s < 1.5:
        return "約線性"
    if s < 2.5:
        return "約平方"
    if s < 2.6:
        return "介於平方與立方"
    if s <= 3.4:
        return "接近 3(立方)"
    if s < 3.5:
        return "介於立方與四次"
    if s < 4.5:
        return "約四次"
    return "超過四次"


def interp(points, n):
    """log-log 內插/外插。回傳 (值, 模式, 用到的斜率)。"""
    pts = [p for p in points if p[1] and p[1] > 0]
    if not pts:
        return None, "none", None
    for (n0, t0), (n1, t1) in zip(pts, pts[1:]):
        if n0 <= n <= n1:
            if n0 == n:
                return t0, "measured", None
            if n1 == n:
                return t1, "measured", None
            s = math.log(t1 / t0) / math.log(float(n1) / n0)
            return t0 * (float(n) / n0) ** s, "interpolated", s
    if len(pts) == 1:
        return None, "none", None
    if n < pts[0][0]:
        (n0, t0), (n1, t1) = pts[0], pts[1]
    else:
        (n0, t0), (n1, t1) = pts[-2], pts[-1]
    s = math.log(t1 / t0) / math.log(float(n1) / n0)
    ref_n, ref_t = (pts[0] if n < pts[0][0] else pts[-1])
    return ref_t * (float(n) / ref_n) ** s, "extrapolated", s


def estimate(points, n, min_n):
    """估算 N=n 的時間,給範圍:內插只有一個值;外插取「末兩點斜率」與「N>=min_n 全段 OLS 斜率」兩者的範圍。"""
    val, mode, s = interp(points, n)
    if val is None:
        return None
    lo = hi = val
    note = mode
    if mode == "extrapolated":
        big = [(a, b) for a, b in points if a >= min_n]
        s2 = loglog_slope(big) if len(big) >= 3 else None
        if s2 is not None:
            ref_n, ref_t = points[-1] if n > points[-1][0] else points[0]
            alt = ref_t * (float(n) / ref_n) ** s2
            lo, hi = min(val, alt), max(val, alt)
    return dict(value=val, lo=lo, hi=hi, mode=note, slope=s)


def fmt_s(x):
    if x is None:
        return "-"
    if x < 1:
        return "%.1f ms" % (x * 1000)
    if x < 120:
        return "%.2f s" % x
    return "%.1f min" % (x / 60.0)


# ------------------------------------------------------------------------------------------ 分析

def analyze(rows, a):
    L = []
    res = {"exponents": {}, "estimates": {}, "stack": {}, "verdict": {}}

    def out(s=""):
        L.append(s)

    out("# issue #300 微基準分析")
    out()
    out("輸入列數 %d;建議判準(由主迴圈定案):五房整套載入 <= %.0f s;16 MiB 堆疊下餘裕 >= %.1f MiB。" % (
        len(rows), a.load_limit, a.stack_margin_mib))
    out()

    # ---- 1 涵蓋範圍
    out("## 1. 涵蓋範圍(load 的成功樣本數)")
    out()
    fams = sorted(set(r["family"] for r in rows if r["kind"] == "load"))
    caps = sorted(set(r["cap"] for r in rows if r["kind"] == "load"))
    ns = sorted(set(r["N"] for r in rows if r["kind"] == "load"))
    out("| 家族 | 容量 | " + " | ".join("N=%d" % n for n in ns) + " |")
    out("|---|---|" + "---|" * len(ns))
    for f in fams:
        for c in caps:
            cells = []
            for n in ns:
                got = [r for r in rows if r["kind"] == "load" and r["family"] == f and r["cap"] == c and r["N"] == n]
                ok = [r for r in got if r["rc"] == 0]
                bad = sorted(set(r["rc"] for r in got if r["rc"] != 0))
                cells.append(("%d" % len(ok) if ok else "") + (" (rc=%s)" % ",".join(map(str, bad)) if bad else "") or "-")
            out("| %s | %d | " % (f, c) + " | ".join(cells) + " |")
    out()

    # ---- 2 冪次
    out("## 2. 冪次(log-log 斜率)")
    out()
    out("斜率會隨 N 變大而爬升(固定成本被稀釋),所以「最後三點」比「全段」可信;`a+b*N^k` 是把常數項分出來再比 k。")
    out("load = 一連串指令的總和:若每條指令是立方,load 應約四次方(load 斜率 - 1 = 等效每指令斜率)。")
    out()
    for f in fams or ["single"]:
        for c in caps:
            for kind in KINDS:
                ser = series(rows, f, c, kind)
                pts = points_of(ser)
                if not pts:
                    continue
                key = "%s/cap%d/%s" % (f, c, kind)
                last3 = loglog_slope(pts[-3:]) if len(pts) >= 3 else None
                big = [p for p in pts if p[0] >= a.min_n]
                s_big = loglog_slope(big) if len(big) >= 3 else None
                s_all = loglog_slope(pts) if len(pts) >= 3 else None
                poly = best_poly(pts)
                out("### %s  (家族 %s,容量 %d,%s)" % (kind, f, c, "整份載入" if kind == "load" else "單條 line 指令"))
                out()
                out("| N | " + " | ".join(str(n) for n, _ in pts) + " |")
                out("|---|" + "---|" * len(pts))
                out("| 中位數 | " + " | ".join(fmt_s(t) for _, t in pts) + " |")
                out("| 樣本數 | " + " | ".join(str(len(ser[n])) for n, _ in pts) + " |")
                loc = local_slopes(pts)
                if loc:
                    out("| 區段斜率 | " + " | ".join("%d->%d: %.2f" % l for l in loc) + " | |")
                out()
                lines = []
                lines.append("- 全段斜率:%s" % ("%.2f" % s_all if s_all is not None else "資料不足(需要 >= 3 個 N)"))
                lines.append("- N >= %d 的斜率:%s" % (a.min_n, "%.2f" % s_big if s_big is not None else "資料不足"))
                lines.append("- 最後三點斜率:%s => %s" % ("%.2f" % last3 if last3 is not None else "-", describe_slope(last3)))
                if kind == "load" and last3 is not None:
                    lines.append("- 等效每指令斜率(load 斜率 - 1):%.2f => %s" % (last3 - 1, describe_slope(last3 - 1)))
                if poly:
                    lines.append("- `a + b*N^k` 擬合(相對誤差 RMS):" + ",".join("k=%d: %.0f%%" % (k, rel * 100) for k, rel, _, _ in poly) +
                                 "  => 最佳 k=%d" % poly[0][0])
                out("\n".join(lines))
                out()
                res["exponents"][key] = dict(points=pts, last3=last3, n_ge_min=s_big, all=s_all,
                                             best_k=poly[0][0] if poly else None)

    # 立方假說
    out("## 3. 「每條指令約 O(N^3)」假說")
    out()
    verdict_lines = []
    support, against = 0, 0
    for kind in EXPECT_CUBIC:
        ex = res["exponents"].get("single/cap512/%s" % kind)
        if not ex or ex["last3"] is None:
            continue
        s = ex["last3"]
        near = 2.6 <= s <= 3.4
        support += 1 if near else 0
        against += 0 if near else 1
        verdict_lines.append("- single / 容量 512 / %s:最後三點斜率 %.2f(距 3:%+.2f)=> %s" % (kind, s, s - 3, describe_slope(s)))
    if verdict_lines:
        out("\n".join(verdict_lines))
        out()
        tops = [max(n for n, _ in res["exponents"]["single/cap512/%s" % k]["points"])
                for k in EXPECT_CUBIC if "single/cap512/%s" % k in res["exponents"]]
        top = max(tops) if tops else 0
        out("結論:%s(最大量測 N=%d;若最大 N < 256,斜率仍被固定成本壓低,不能據此否定立方)。" % (
            "支持立方假說" if support and not against else ("不支持立方假說" if against and not support else "證據分歧"), top))
        res["verdict"]["cubic"] = "support" if support and not against else ("against" if against and not support else "mixed")
    else:
        out("資料不足(single / 容量 512 至少要 3 個 N 的 line-place 或 line-grid 樣本)。")
        res["verdict"]["cubic"] = "insufficient"
    out()

    # ---- 4 容量 64 vs 512 同 N
    out("## 4. 同一個 N,容量 64 與容量 512 的差(純粹是容量放大的開銷;預期約 +10~30%,因為每個候選都整份複製 World)")
    out()
    rowsout = []
    for kind in KINDS:
        s64, s512 = series(rows, "single", 64, kind), series(rows, "single", 512, kind)
        for n in sorted(set(s64) & set(s512)):
            rowsout.append("| %s | %d | %s | %s | %.2fx |" % (kind, n, fmt_s(median(s64[n])), fmt_s(median(s512[n])),
                                                              median(s512[n]) / median(s64[n])))
    if rowsout:
        out("| 類型 | N | 容量 64 | 容量 512 | 比值 |")
        out("|---|---|---|---|---|")
        out("\n".join(rowsout))
    else:
        out("資料不足(容量 64 與 512 沒有共同的 N)。")
    out()

    # ---- 5 估算
    out("## 5. 估算(容量 512)")
    out()
    est_rows = []

    def est(label, fam, kind, n):
        pts = points_of(series(rows, fam, 512, kind))
        e = estimate(pts, n, a.min_n)
        res["estimates"]["%s/%s/N=%d" % (fam, kind, n)] = e
        if e is None:
            est_rows.append("| %s | %s | %d | 資料不足 | |" % (label, kind, n))
        else:
            rng = "" if e["lo"] == e["hi"] else "%s ~ %s" % (fmt_s(e["lo"]), fmt_s(e["hi"]))
            est_rows.append("| %s | %s | %d | %s | %s%s |" % (label, kind, n, fmt_s(e["value"]), e["mode"],
                                                              ("(範圍 " + rng + ")") if rng else ""))
        return e

    e_f1 = est("F1 客廳(單房,P=M=N)", "single", "load", a.f1_n)
    e_house = est("五房整套(house)", "house", "load", a.house_n)
    e_house_ub = est("五房整套的上界(用單房曲線)", "single", "load", a.house_n)
    e_512 = est("單房 512", "single", "load", 512)
    est("F1 客廳", "single", "line-place", a.f1_n)
    est("五房整套", "house", "line-place", a.house_n)
    est("單房 512", "single", "line-place", 512)
    est("F1 客廳", "single", "line-grid", a.f1_n)
    est("單房 512", "single", "line-grid", 512)
    out("| 情境 | 類型 | N | 估計 | 依據 |")
    out("|---|---|---|---|---|")
    out("\n".join(est_rows))
    out()
    out("說明:house 家族每房一個承載面,P(同面角材數)只有 N 的一部分、M(整個 World)仍是 N;single 是 P=M=N 的最壞情形,所以 single 的值是 house 的上界。")
    out("serve.py 的 BRIDGE_TIMEOUT = 30 s:單一 `loadfile` 超過就會逾時。")
    out()

    # ---- 6 堆疊
    out("## 6. 堆疊(ulimit -S -s 階梯)")
    out()
    srows = [r for r in rows if r["kind"].startswith("stack:") and r["stack_kib"]]
    world = {}
    for r in rows:
        if r["kind"] == "worldbytes" and r["rc"] == 0 and r.get("note", "").startswith("world="):
            try:
                world[r["cap"]] = int(r["note"].split("=", 1)[1])
            except ValueError:
                pass
    if world:
        out("sizeof(World):" + ",".join("容量 %d = %s B (%.3f MiB)" % (c, "{:,}".format(w), w / 1048576.0) for c, w in sorted(world.items())) +
            ";3 份 World = " + ",".join("容量 %d: %.2f MiB" % (c, 3 * w / 1048576.0) for c, w in sorted(world.items())))
        out()
    min_stack = {}
    if srows:
        out("| 容量 | 工作負載 | 16 MiB 通過? | 最小通過 KiB | 最大失敗 KiB | 備註 |")
        out("|---|---|---|---|---|---|")
        for c in sorted(set(r["cap"] for r in srows)):
            for wl in sorted(set(r["kind"] for r in srows if r["cap"] == c)):
                rr = [r for r in srows if r["cap"] == c and r["kind"] == wl]
                tested = {}
                for r in rr:
                    tested[r["stack_kib"]] = r["rc"]
                invalid = sorted(k for k in tested if tested[k] == 1)     # ok:false:工作負載本身不成立,不算堆疊結果
                for k in invalid:
                    del tested[k]
                if not tested:
                    out("| %d | %s | - | - | - | 工作負載無效(回 ok:false),已排除 |" % (c, wl[len("stack:"):]))
                    continue
                ks = sorted(tested, reverse=True)
                contiguous = None
                for k in ks:
                    if tested[k] == 0:
                        contiguous = k
                    else:
                        break
                fails = [k for k in ks if tested[k] != 0]
                top_ok = tested.get(STACK_CONTRACT_KIB) == 0
                nonmono = any(tested[k] == 0 for k in ks if fails and k < max(fails))
                max_fail = max(fails) if fails else None
                out("| %d | %s | %s | %s | %s | %s |" % (c, wl[len("stack:"):], "是" if top_ok else ("否" if STACK_CONTRACT_KIB in tested else "未測"),
                                                      contiguous if contiguous is not None else "-", max_fail if max_fail else "-",
                                                      "非單調(較小的堆疊反而通過)" if nonmono else ""))
                if contiguous is not None:
                    min_stack[c] = max(min_stack.get(c, 0), contiguous)
                if not top_ok and STACK_CONTRACT_KIB in tested:
                    min_stack[c] = 10 ** 9
        out()
        for c, k in sorted(min_stack.items()):
            if k >= 10 ** 9:
                out("- 容量 %d:在 16 MiB 就失敗。" % c)
                continue
            line = "- 容量 %d:所有工作負載都通過的最小堆疊 = %d KiB (%.2f MiB),16 MiB 下餘裕 %.2f MiB" % (
                c, k, k / 1024.0, (STACK_CONTRACT_KIB - k) / 1024.0)
            if c in world:
                line += ";= %.2f 份 World" % (k * 1024.0 / world[c])
            out(line)
        out()
        out("限制:階梯只涵蓋 #211 的三個場景 + 一個 N=64 的產生場景(含 reference_snap);沒走到的更深呼叫鏈不在內。堆疊用量和 N 無關(框架大小由容量決定),所以 N=64 就足以代表。")
    else:
        out("資料不足(沒有 stack 列)。")
    res["stack"] = {str(c): k for c, k in min_stack.items()}
    out()

    # ---- 7 判準
    out("## 7. 判準與結論(建議判準,由主迴圈定案)")
    out()

    def status(value_lo, value_hi, limit):
        if value_hi is None:
            return "資料不足"
        if value_hi <= limit:
            return "PASS"
        if value_lo is not None and value_lo > limit:
            return "FAIL"
        return "未定(範圍跨過門檻)"

    c1 = c1_basis = None
    for e, label in ((e_house, "house 家族"), (e_house_ub, "single 曲線上界")):
        if e is not None and (c1 is None):
            c1_basis = "%s,%s" % (label, e["mode"])
            if label == "single 曲線上界":
                # 上界通過 => 真值也通過;上界沒過 => 只能說未定
                c1 = "PASS" if e["hi"] <= a.load_limit else "未定(只有上界超過門檻,需要 house 家族的資料)"
            else:
                c1 = status(e["lo"], e["hi"], a.load_limit)
            c1_val = e
    if c1 is None:
        c1, c1_basis = "資料不足", "-"
    out("- 判準 1:五房整套(N=%d)載入 <= %.0f s:**%s**(%s%s)" % (
        a.house_n, a.load_limit, c1, c1_basis, (";估計 %s" % fmt_s(c1_val["value"])) if c1 != "資料不足" else ""))
    k512 = min_stack.get(512)
    if k512 is None:
        c2 = "資料不足"
    else:
        margin = (STACK_CONTRACT_KIB - k512) / 1024.0
        c2 = "PASS" if (k512 < 10 ** 9 and margin >= a.stack_margin_mib) else "FAIL"
        out("- 判準 2:16 MiB 堆疊下餘裕 >= %.1f MiB:**%s**(最小通過 %s,餘裕 %s)" % (
            a.stack_margin_mib, c2, ("%d KiB" % k512) if k512 < 10 ** 9 else "16 MiB 即失敗",
            ("%.2f MiB" % margin) if k512 < 10 ** 9 else "<0"))
    if c2 == "資料不足":
        out("- 判準 2:16 MiB 堆疊下餘裕 >= %.1f MiB:**資料不足**(沒有容量 512 的 stack 列)" % a.stack_margin_mib)
    out()
    if "FAIL" in (c1, c2):
        overall = "512 依建議判準不可行(至少一項 FAIL)"
    elif c1 == "PASS" and c2 == "PASS":
        overall = "512 依建議判準可行(兩項 PASS)"
    else:
        overall = "尚無定論(%s / %s)" % (c1, c2)
    out("**總結:%s**" % overall)
    out()
    res["verdict"].update(load_house=c1, stack=c2, overall=overall)
    return "\n".join(L) + "\n", res


# ------------------------------------------------------------------------------------------ selftest

def _synthetic():
    rows = []

    def add(n, cap, kind, t, fam="single", rc=0, rep=1, stack=0, note=""):
        rows.append(dict(N=n, cap=cap, kind=kind, seconds=t, rc=rc, family=fam, rep=rep, stack_kib=stack, note=note))

    for cap, mult in ((64, 1.0), (512, 1.2)):
        for n in (16, 32, 64, 128, 256, 512):
            if n > cap:
                continue
            for rep in (1, 2, 3):
                jitter = 1.0 + 0.02 * (rep - 2)
                place = (2e-4 + 1.0e-9 * n ** 3) * mult * jitter
                add(n, cap, "line-place", place, rep=rep)
                add(n, cap, "line-grid", place * 0.7, rep=rep)
                add(n, cap, "line-delete", place * 0.6, rep=rep)
                add(n, cap, "load", (1e-3 + 2.5e-10 * n ** 4) * mult * jitter, rep=rep)
    for n in (128, 256, 512):
        add(n, 512, "load", (1e-3 + 2.5e-10 * n ** 4) * 0.2, fam="house")
        add(n, 512, "line-place", (2e-4 + 1.0e-9 * n ** 3) * 0.3, fam="house")
    add(0, 64, "worldbytes", 0, note="world=4759448", fam="")
    add(0, 512, "worldbytes", 0, note="world=5605272", fam="")
    for cap, need in ((64, 5000), (512, 11000)):
        for wl in ("gen64", "ax_r13"):
            for k in (16384, 14336, 12288, 11264, 11008, 10752, 10240):
                add(64, cap, "stack:" + wl, 0.2, fam="stack", rc=0 if k >= need else 139, stack=k)
    return rows


def selftest():
    rows = _synthetic()
    args = argparse.Namespace(min_n=64, f1_n=110, house_n=300, load_limit=30.0, stack_margin_mib=2.0)
    text, res = analyze(rows, args)
    problems = []
    ex = res["exponents"].get("single/cap512/line-place")
    if not ex or ex["last3"] is None or not (2.7 <= ex["last3"] <= 3.1):
        problems.append("line-place last3 slope should be ~3, got %r" % (ex and ex["last3"]))
    exl = res["exponents"].get("single/cap512/load")
    if not exl or not (3.7 <= exl["last3"] <= 4.1):
        problems.append("load last3 slope should be ~4, got %r" % (exl and exl["last3"]))
    if ex and ex["best_k"] != 3:
        problems.append("best_k should be 3, got %r" % ex["best_k"])
    if res["verdict"].get("cubic") != "support":
        problems.append("cubic verdict should be support: %r" % res["verdict"].get("cubic"))
    house = res["estimates"].get("house/load/N=300")
    if not house or house["mode"] != "interpolated":
        problems.append("house N=300 should be interpolated: %r" % house)
    if res["stack"].get("512") not in (11008,):
        problems.append("stack min for 512 should be 11008, got %r" % res["stack"].get("512"))
    if res["verdict"]["stack"] != "PASS":
        problems.append("stack verdict should be PASS (margin 5.2 MiB): %r" % res["verdict"]["stack"])
    # 立方成本在 N=300 的 house 估計:2.5e-10*300^4*0.2 ~ 0.4 s => PASS
    if res["verdict"]["load_house"] != "PASS":
        problems.append("load verdict should be PASS: %r" % res["verdict"]["load_house"])
    # 反向案例:堆疊在 12288 才通過 => 餘裕 4 MiB PASS;在 15000 才通過 => 餘裕 < 2 FAIL
    bad = [dict(r) for r in rows]
    for r in bad:
        if r["kind"].startswith("stack:") and r["cap"] == 512:
            r["rc"] = 0 if r["stack_kib"] >= 15000 else 139
            if r["stack_kib"] < 15000 and r["rc"] == 0:
                r["rc"] = 139
    for k in (16384, 15360, 15000):
        bad.append(dict(N=64, cap=512, kind="stack:gen64", seconds=0.2, rc=0, family="stack", rep=0, stack_kib=k, note=""))
    _, res2 = analyze(bad, args)
    if res2["verdict"]["stack"] != "FAIL" or "不可行" not in res2["verdict"]["overall"]:
        problems.append("tight stack should FAIL: %r" % res2["verdict"])
    # 空資料不能丟例外
    _, res3 = analyze([], args)
    if "尚無定論" not in res3["verdict"]["overall"]:
        problems.append("empty input should be inconclusive: %r" % res3["verdict"])
    if problems:
        print("fit selftest FAILED:", file=sys.stderr)
        for p in problems:
            print("  - " + p, file=sys.stderr)
        return 1
    print("fit selftest OK")
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("tsv", nargs="*", help="bench.tsv (one or more)")
    ap.add_argument("--min-n", type=int, default=64, help="only N >= this joins the 'N>=min' slope (default 64)")
    ap.add_argument("--f1-n", type=int, default=110, help="N for the F1 living room estimate (default 110)")
    ap.add_argument("--house-n", type=int, default=300, help="N for the whole-house estimate (default 300)")
    ap.add_argument("--load-limit", type=float, default=30.0, help="suggested: whole-house load <= this many seconds")
    ap.add_argument("--stack-margin-mib", type=float, default=2.0, help="suggested: required headroom under 16 MiB")
    ap.add_argument("--json", help="also write the numbers as JSON")
    ap.add_argument("-o", "--out", help="also write the report here")
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--demo", action="store_true", help="print the report for built-in SYNTHETIC data (format preview only)")
    a = ap.parse_args(argv)
    if a.selftest:
        return selftest()
    if a.demo:
        print("(以下是合成資料,只用來預覽輸出格式,不是量測結果)")
        print()
        sys.stdout.write(analyze(_synthetic(), a)[0])
        return 0
    if not a.tsv:
        ap.error("need at least one TSV (or --selftest)")
    rows = read_rows(a.tsv)
    text, res = analyze(rows, a)
    sys.stdout.write(text)
    if a.out:
        with open(a.out, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(text)
    if a.json:
        with open(a.json, "w", encoding="utf-8", newline="\n") as fh:
            json.dump(res, fh, ensure_ascii=False, indent=1, default=str)
    return 0


if __name__ == "__main__":
    sys.exit(main())
