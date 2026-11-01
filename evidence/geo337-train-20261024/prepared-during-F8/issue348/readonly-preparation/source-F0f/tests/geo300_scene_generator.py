#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""issue #300 微基準:產生「N 支角材」的代表性場景(純文字,不呼叫核心)。

    python3 gen_scene.py 64                       # 場景文字印到 stdout,摘要印到 stderr
    python3 gen_scene.py 512 -o s512.scene --meta s512.json
    python3 gen_scene.py 300 --family house -o h300.scene --meta h300.json
    python3 gen_scene.py --table                  # 各 N 的房間尺寸/密度一覽
    python3 gen_scene.py --selftest               # 與已知可被核心接受的 calib/f3-00.scene 逐句比對

兩種家族(family):
  single  一個矩形房間、一個承載面,N 支角材全在同一個 placement。這是「P = M = N」的最壞情形,
          也是 contact_order 線性掃描假說(每條指令約 O(N^3))直接針對的情形。
  house   五個房間,每房一個承載面(F1..F5 的支數比例取自探針 golden 各房最大排法 111:57:48:28:43),
          總數 N。每房的 P 只有 N 的一部分,但 M(整個 World 的角材數)仍是 N。N >= 100。

每個房間完全仿照探針(core-probe)已被核心實跑接受的 F2~F5 / ex3700 房間句型:
  2 支邊界材(沿 +u,貼 e0 / e2,between 左右牆)
  m 支主支(primary,at-line grid u i,between 下/上邊界,沿 +v)
  2 支沿牆主支(primary,at-face e3 / e1,between 下/上邊界,沿 ±v)
  (m+1) 個 bay x r 排副支(secondary,at-line grid v j,between 左右相鄰擋面,沿 +u)
格線間距沿用 oracle 的 u 間距 ~918、v 間距 367(= 1830/5 + 1,「記號上界模數」);截面 27x33、承載面 z=2500。
因此密度與 F1 客廳同量級:F1 約 95~111 支 / 20.8 m^2,本產生器約 3 支 / m^2(副支)+ 主支。

誠實聲明:本檔寫成時 *沒有* 對核心實跑過任何產生出來的場景(寫作當下禁止建置/執行)。--selftest 只證明
「產生器在 f3-00 的參數下逐句重現一個已被核心接受的房間」;其他尺寸是否被核心接受,要靠 bench.sh 的 sanity 階段實測。
"""
from __future__ import print_function

import argparse
import hashlib
import json
import math
import os
import re
import sys

A, B = 27, 33                 # 截面(與探針一致)
Z = 2500                      # 承載面 z
HALF_LO, HALF_HI = A // 2, A - A // 2   # 中線 u 的矩形 = [u-13, u+14)
U0, PITCH_U = 916, 918        # 第一條主支中線、主支間距(oracle 為 917~918)
V0, PITCH_V = 363, 367        # 第一排副支中線、排距
TAIL = 891                    # 最後一支主支到右牆的空隙(= PITCH_U - A,與其他 bay 同寬)
TOP_GAP = 295                 # 最後一排副支到上邊界的空隙(ex3700-gap3 為 295)
WALL = A                      # 沿牆主支/邊界材的寬
MAX_LINES = 64                # GRID_MAX_LINES
ASPECT = 1.04                 # F1 外接框 5000 x 4800
HOUSE_WEIGHTS = (111, 57, 48, 28, 43)
HOUSE_NAMES = ("F1", "F2", "F3", "F4", "F5")
ROOM_GAP = 1000
MIN_ROOM = 12                 # house 每房至少這麼多支(再少就退化成沒有主支的怪房間)
MIN_HOUSE = 100


# --------------------------------------------------------------------------------------- 幾何小工具

def _overlap_positive(a, b):
    return a[0] < b[2] and b[0] < a[2] and a[1] < b[3] and b[1] < a[3]


def plan_room(count):
    """為一個房間挑 (m 支主支, r 排副支),使 total = 4 + m + (m+1)*r >= count 且外接框接近 F1 的長寬比。

    回傳 (m, r, total)。total 超出 count 的部分之後由最後一個 bay 的最上面幾排副支裁掉(副支是葉節點,裁掉不影響其他角材)。
    """
    if count < MIN_ROOM and count < 7:
        raise ValueError("a room needs at least 7 timbers, got %d" % count)
    best = None
    for m in range(1, MAX_LINES - 3):
        if m > count - 5:           # 至少要留 1 支副支
            break
        r = max(1, -(-(count - 4 - m) // (m + 1)))
        if r > MAX_LINES - 4:
            continue
        total = 4 + m + (m + 1) * r
        width = U0 + PITCH_U * (m - 1) + HALF_HI + TAIL + WALL
        height = V0 + PITCH_V * (r - 1) + HALF_HI + TOP_GAP + WALL
        score = abs(math.log(float(width) / height / ASPECT)) + 0.01 * (total - count) / float(count)
        if best is None or score < best[0] - 1e-12:
            best = (score, m, r, total, width, height)
    if best is None:
        raise ValueError("cannot plan a room for %d timbers within %d grid lines" % (count, MAX_LINES))
    return best[1], best[2], best[3]


def room_spec(count, surface, grid, x0=0, y0=0):
    m, r, total = plan_room(count)
    u_lines = [x0 + U0 + PITCH_U * i for i in range(m)]
    v_lines = [y0 + V0 + PITCH_V * j for j in range(r)]
    width = U0 + PITCH_U * (m - 1) + HALF_HI + TAIL + WALL
    height = V0 + PITCH_V * (r - 1) + HALF_HI + TOP_GAP + WALL
    return dict(surface=surface, grid=grid, x0=x0, y0=y0, width=width, height=height,
                u_lines=u_lines, v_lines=v_lines, count=count, total=total)


def build_room(spec, id0, keep_secondaries=None):
    """依 spec 產生一個房間。keep_secondaries=None 表全留;否則只留前 keep_secondaries 支副支(bay 優先、排次之)。

    回傳 dict:head(surface/grid 兩行)、blocks(依放置順序,每個含 id/role/kind/timber/place/rect)、leaf(最後一支副支)。
    """
    s, g = spec["surface"], spec["grid"]
    x0, y0, w, h = spec["x0"], spec["y0"], spec["width"], spec["height"]
    us, vs = spec["u_lines"], spec["v_lines"]
    m, r = len(us), len(vs)
    if not (1 <= m <= MAX_LINES and 1 <= r <= MAX_LINES):
        raise ValueError("grid axis needs 1..%d lines (u=%d v=%d)" % (MAX_LINES, m, r))
    if any(b <= a for a, b in zip(us, us[1:])) or any(b <= a for a, b in zip(vs, vs[1:])):
        raise ValueError("grid lines must be strictly increasing")
    head = [
        "surface %d origin 0 0 %d u +x v +y outline %d,%d %d,%d %d,%d %d,%d" % (
            s, Z, x0, y0, x0 + w, y0, x0 + w, y0 + h, x0, y0 + h),
        "grid %d on %d u %s v %s" % (g, s, " ".join(str(u) for u in us), " ".join(str(v) for v in vs)),
    ]
    bottom, top = id0, id0 + 1
    mains = [id0 + 2 + i for i in range(m)]
    wl, wr = id0 + 2 + m, id0 + 3 + m
    first_sec = id0 + 4 + m
    y_lo, y_hi = y0 + WALL, y0 + h - WALL        # 主支/沿牆主支的 v 範圍(夾在兩條邊界材之間)
    blocks = []

    def add(role, kind, tid, place, rect):
        blocks.append(dict(id=tid, role=role, kind=kind, rect=rect,
                           timber="timber %d %d %d role %s" % (tid, A, B, role), place=place))

    add("boundary", "boundary", bottom, "place %d on %d at-face e0 between e3 e1 +u +n" % (bottom, s),
        (x0, y0, x0 + w, y0 + WALL))
    add("boundary", "boundary", top, "place %d on %d at-face e2 between e3 e1 -u +n" % (top, s),
        (x0, y0 + h - WALL, x0 + w, y0 + h))
    for i, tid in enumerate(mains):
        add("primary", "main", tid, "place %d on %d at-line grid %d u %d between t%d t%d +v +n" % (tid, s, g, i, bottom, top),
            (us[i] - HALF_LO, y_lo, us[i] + HALF_HI, y_hi))
    add("primary", "wall", wl, "place %d on %d at-face e3 between t%d t%d -v +n" % (wl, s, bottom, top),
        (x0, y_lo, x0 + WALL, y_hi))
    add("primary", "wall", wr, "place %d on %d at-face e1 between t%d t%d +v +n" % (wr, s, bottom, top),
        (x0 + w - WALL, y_lo, x0 + w, y_hi))
    sec_total = (m + 1) * r
    keep = sec_total if keep_secondaries is None else keep_secondaries
    if not (1 <= keep <= sec_total):
        raise ValueError("room keeps %d secondaries but has %d" % (keep, sec_total))
    leaf = None
    tid = first_sec
    for bay in range(m + 1):
        if tid - first_sec >= keep:
            break
        left_id = wl if bay == 0 else mains[bay - 1]
        right_id = wr if bay == m else mains[bay]
        x_lo = x0 + WALL if bay == 0 else us[bay - 1] + HALF_HI
        x_hi = x0 + w - WALL if bay == m else us[bay] - HALF_LO
        for j in range(r):
            if tid - first_sec >= keep:
                break
            place = "place %d on %d at-line grid %d v %d between t%d t%d +u +n" % (tid, s, g, j, left_id, right_id)
            add("secondary", "secondary", tid, place, (x_lo, vs[j] - HALF_LO, x_hi, vs[j] + HALF_HI))
            leaf = dict(id=tid, bay=bay, row=j, surface=s, grid=g, place=place,
                        timber="timber %d %d %d role secondary" % (tid, A, B))
            tid += 1
    return dict(head=head, blocks=blocks, leaf=leaf, spec=spec, next_id=tid, m=m, r=r)


def check_room(room):
    """純幾何自檢:矩形都在房間內、長度為正、兩兩不重疊。回傳錯誤字串清單(空 = 通過)。"""
    spec = room["spec"]
    box = (spec["x0"], spec["y0"], spec["x0"] + spec["width"], spec["y0"] + spec["height"])
    errors = []
    rects = [(b["id"], b["rect"]) for b in room["blocks"]]
    for tid, rc in rects:
        if rc[0] >= rc[2] or rc[1] >= rc[3]:
            errors.append("timber %d has non-positive extent %r" % (tid, rc))
        if rc[0] < box[0] or rc[1] < box[1] or rc[2] > box[2] or rc[3] > box[3]:
            errors.append("timber %d leaves the room %r" % (tid, rc))
    # 掃描線式的兩兩檢查(N<=512,O(N^2) 足夠)
    for i in range(len(rects)):
        for j in range(i + 1, len(rects)):
            if _overlap_positive(rects[i][1], rects[j][1]):
                errors.append("timbers %d and %d overlap" % (rects[i][0], rects[j][0]))
                if len(errors) > 20:
                    return errors
    return errors


# --------------------------------------------------------------------------------------- 整份場景

def allocate_house(n):
    if n < MIN_HOUSE:
        raise ValueError("family house needs N >= %d (got %d)" % (MIN_HOUSE, n))
    total_w = float(sum(HOUSE_WEIGHTS))
    raw = [n * w / total_w for w in HOUSE_WEIGHTS]
    counts = [max(MIN_ROOM, int(x)) for x in raw]
    # 最大餘數法補到剛好 n(必要時從最大房間扣)
    while sum(counts) < n:
        i = max(range(len(raw)), key=lambda k: raw[k] - counts[k])
        counts[i] += 1
    while sum(counts) > n:
        i = max(range(len(counts)), key=lambda k: counts[k])
        counts[i] -= 1
    return counts


def build(n, family="single"):
    """回傳 (scene_text, meta)。meta 是 JSON 可序列化的 dict,drive.py 讀它取得葉節點與格線指令。"""
    if n < 7:
        raise ValueError("N must be >= 7")
    if family == "single":
        counts = [n]
    elif family == "house":
        counts = allocate_house(n)
    else:
        raise ValueError("unknown family %r" % family)
    rooms, x0, id0 = [], 0, 1
    lines = [
        "# issue300 micro-benchmark scene (generated by gen_scene.py, do not edit)",
        "# family=%s N=%d rooms=%d  section %dx%d  z=%d" % (family, n, len(counts), A, B, Z),
    ]
    for k, cnt in enumerate(counts):
        spec = room_spec(cnt, surface=k + 1, grid=k + 1, x0=x0, y0=0)
        m, r = len(spec["u_lines"]), len(spec["v_lines"])
        room = build_room(spec, id0, keep_secondaries=cnt - 4 - m)
        errs = check_room(room)
        if errs:
            raise AssertionError("generated room %d is geometrically invalid: %s" % (k + 1, "; ".join(errs[:5])))
        if len(room["blocks"]) != cnt:
            raise AssertionError("room %d has %d timbers, wanted %d" % (k + 1, len(room["blocks"]), cnt))
        rooms.append(room)
        lines.append("")
        lines.append("# room %d (%s): %d timbers, %d mains, %d rows, %d x %d mm" % (
            k + 1, HOUSE_NAMES[k] if family == "house" else "single", cnt, m, r, spec["width"], spec["height"]))
        lines.extend(room["head"])
        for b in room["blocks"]:
            lines.append(b["timber"])
            lines.append(b["place"])
        id0 = room["next_id"]
        x0 += spec["width"] + ROOM_GAP
    text = "\n".join(lines) + "\n"
    ntimber = sum(1 for ln in lines if ln.startswith("timber "))
    if ntimber != n:
        raise AssertionError("scene has %d timber lines, wanted %d" % (ntimber, n))
    leaf_room = rooms[0]
    leaf = leaf_room["leaf"]
    area_m2 = sum(rm["spec"]["width"] * rm["spec"]["height"] for rm in rooms) / 1e6
    meta = {
        "family": family, "n": n, "placements": len(rooms),
        "rooms": [dict(surface=rm["spec"]["surface"], timbers=len(rm["blocks"]), mains=rm["m"], rows=rm["r"],
                       width=rm["spec"]["width"], height=rm["spec"]["height"], x0=rm["spec"]["x0"]) for rm in rooms],
        "area_m2": round(area_m2, 3), "density_per_m2": round(n / area_m2, 3),
        "grid_command": leaf_room["head"][1],
        "leaf": dict(id=leaf["id"], surface=leaf["surface"], grid=leaf["grid"], bay=leaf["bay"], row=leaf["row"],
                     timber=leaf["timber"], place=leaf["place"], delete="delete timber %d" % leaf["id"]),
        "scene_sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
    }
    return text, meta


def scene_name(family, n):
    return "%s-%04d" % (family, n)


def write(n, family, directory):
    """寫 <directory>/<family>-<NNNN>.scene 與 .json(原子寫入),回傳 (scene_path, meta)。"""
    text, meta = build(n, family)
    os.makedirs(directory, exist_ok=True)
    base = os.path.join(directory, scene_name(family, n))
    for path, data in ((base + ".scene", text), (base + ".json", json.dumps(meta, ensure_ascii=False, indent=1) + "\n")):
        tmp = path + ".tmp%d" % os.getpid()
        with open(tmp, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(data)
        os.replace(tmp, path)
    return base + ".scene", meta


# --------------------------------------------------------------------------------------- selftest

def _norm_place(line):
    return re.sub(r"^place \d+ ", "place * ", line)


def selftest(calib):
    """用 calib/f3-00.scene(探針產生、已被核心整場接受的 48 支房間)驗產生器的句型與幾何模型。"""
    with open(calib, "r", encoding="utf-8") as fh:
        raw = fh.read().splitlines()
    stmts = [ln for ln in raw if ln.strip() and not ln.startswith("#")]
    cal_head = [ln for ln in stmts if ln.startswith(("surface ", "grid "))]
    cal_t = [ln for ln in stmts if ln.startswith("timber ")]
    cal_p = [ln for ln in stmts if ln.startswith("place ")]
    cal_rects = []
    for ln in raw:
        mt = re.match(r"# probe-member (\{.*\})\s*$", ln)
        if mt:
            cal_rects.append(tuple(json.loads(mt.group(1))["rect"]))
    spec = dict(surface=1, grid=1, x0=5120, y0=3720, width=3880, height=3280,
                u_lines=[6036, 6953, 7870, 8787], v_lines=[4083, 4450, 4817, 5184, 5551, 5918, 6285, 6652])
    room = build_room(spec, 1)
    problems = []
    if room["head"] != cal_head:
        problems.append("head lines differ:\n  gen=%r\n  cal=%r" % (room["head"], cal_head))
    gen_t = [b["timber"] for b in room["blocks"]]
    gen_p = [b["place"] for b in room["blocks"]]
    if len(gen_t) != len(cal_t):
        problems.append("member count %d != calib %d" % (len(gen_t), len(cal_t)))
    if gen_t[:8] != cal_t[:8] or gen_p[:8] != cal_p[:8]:
        problems.append("first 8 members (boundaries, mains, walls) differ")
    if sorted(_norm_place(p) for p in gen_p[8:]) != sorted(_norm_place(p) for p in cal_p[8:]):
        problems.append("secondary place statements (id-stripped multiset) differ")
    if sorted(t.split(" ", 2)[2] for t in gen_t) != sorted(t.split(" ", 2)[2] for t in cal_t):
        problems.append("timber declarations (id-stripped multiset) differ")
    if sorted(b["rect"] for b in room["blocks"]) != sorted(cal_rects):
        problems.append("member rectangles differ from the oracle rects in the calib comments")
    errs = check_room(room)
    if errs:
        problems.append("geometry self-check failed: " + "; ".join(errs[:3]))
    # 幾個代表性 N 的建構與自檢
    for fam, ns in (("single", (7, 16, 32, 48, 64, 65, 95, 111, 128, 256, 300, 512)), ("house", (100, 128, 256, 300, 512))):
        for n in ns:
            try:
                text, meta = build(n, fam)
            except Exception as exc:       # noqa: BLE001 - 回報給使用者
                problems.append("build(%d,%s) failed: %s" % (n, fam, exc))
                continue
            if text.count("\ntimber ") != n:
                problems.append("build(%d,%s) timber count wrong" % (n, fam))
            if meta["leaf"]["delete"] != "delete timber %d" % meta["leaf"]["id"]:
                problems.append("leaf meta inconsistent for %s %d" % (fam, n))
    if problems:
        print("gen_scene selftest FAILED:", file=sys.stderr)
        for p in problems:
            print("  - " + p, file=sys.stderr)
        return 1
    print("gen_scene selftest OK: reproduced all %d statements and %d oracle rectangles of %s" % (
        len(cal_t) + len(cal_p) + len(cal_head), len(cal_rects), os.path.basename(calib)))
    return 0


def table():
    print("%-7s %5s %5s %5s %7s %8s %8s %9s" % ("family", "N", "rooms", "mains", "rows", "W(mm)", "H(mm)", "per m^2"))
    for fam, ns in (("single", (16, 32, 64, 128, 256, 512)), ("house", (128, 256, 300, 512))):
        for n in ns:
            _, meta = build(n, fam)
            r0 = meta["rooms"][0]
            print("%-7s %5d %5d %5d %7d %8d %8d %9.2f" % (fam, n, meta["placements"], r0["mains"], r0["rows"],
                                                          r0["width"], r0["height"], meta["density_per_m2"]))


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("n", nargs="?", type=int, help="number of timbers")
    ap.add_argument("--family", choices=("single", "house"), default="single")
    ap.add_argument("-o", "--out", help="scene output path (default: stdout)")
    ap.add_argument("--meta", help="write metadata JSON here")
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--calib", default=os.path.join(os.path.dirname(os.path.abspath(__file__)), "calib", "f3-00.scene"))
    ap.add_argument("--table", action="store_true")
    args = ap.parse_args(argv)
    if args.selftest:
        return selftest(args.calib)
    if args.table:
        table()
        return 0
    if args.n is None:
        ap.error("N is required")
    text, meta = build(args.n, args.family)
    if args.out:
        with open(args.out, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(text)
    else:
        sys.stdout.write(text)
    if args.meta:
        with open(args.meta, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(json.dumps(meta, ensure_ascii=False, indent=1) + "\n")
    print("family=%s N=%d placements=%d area=%.1f m^2 density=%.2f/m^2 leaf=%d sha=%s" % (
        meta["family"], meta["n"], meta["placements"], meta["area_m2"], meta["density_per_m2"],
        meta["leaf"]["id"], meta["scene_sha256"][:12]), file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
