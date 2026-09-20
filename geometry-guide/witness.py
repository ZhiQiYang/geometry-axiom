# -*- coding: utf-8 -*-
"""公理層見證圖(witness):一條條文 ↔ 一個夾具 ↔ 一張由引擎推導、commit 進 repo 的 SVG + 接點 JSON。

定性(使用者 2026-09-20 拍板,BACKLOG GEO-131 / GEO-133):
  示意圖不是文件,是條文的**見證**。條文為真 ⇒ 圖不變,所以圖沒有版本問題;
  圖變了 ⇒ 不是「重出一張」,而是**警報**——某個依賴項(夾具、引擎、條文)動了,
  必須交由使用者確認要改哪一邊。本工具因此只做兩件事,而且第二件永遠不寫檔:

  --build   依 manifest 跑引擎、依《witness/規範.md》組版、寫進 witness/<條號>.svg 與 <條號>.joints.json。
            只在「第一次建立」或「使用者看過 diff 後明示重建」時用。
  --check   重跑一次,與 commit 的圖與接點**逐位元**比對。任何不同 → 印 diff、非 0 退出,**絕不覆寫**。

畫法只有一套(witness/規範.md v1):
  ① 主圖 = 引擎 SVG 指定視圖原樣,角材依角色著色,被裁端面加停止標記 + D18 擋面參照標籤(→t1 / →e0 / →h0e2);
  ② 接點列 = 每個角材端面一格,同一份幾何等比例放大(窗 = 8 × 料寬);
  ③ 圖例 = 每張相同。
本檔不畫任何幾何線;幾何全部來自引擎 SVG,拓樸全部由引擎文字輸出反推(端面共面且被涵蓋 → 唯一擋面,否則失敗)。

夾具 sha 只是**診斷線索**,讓 --check 失敗時能說「是夾具動了」還是「夾具沒動、引擎輸出變了」;
它不參與比對——比對的是整個檔案。行尾一律正規化(core.autocrlf 會在不同平台改 .scene 的行尾)。

manifest(`witness/manifest.json`)一條一項:
  { "I19": { "scene": "_role_rc_boundary_ok.scene", "expect": "accept",
             "view": "bottom", "gist": "boundary 頂外輪廓邊是合法的" } }
  view ∈ bottom / front / side / all;接點列固定在 joint_view(預設 bottom)上放大。

用法:
  python geometry-guide/witness.py --build [條號 ...] [--force]
  python geometry-guide/witness.py --check [條號 ...]
  python geometry-guide/witness.py --list
"""
import argparse
import difflib
import hashlib
import io
import json
import os
import re
import shutil
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

import axiom_examples as ax  # noqa: E402
import axiom_matrix as am    # noqa: E402

WITNESS_DIR = os.path.join(HERE, "witness")
MANIFEST = os.path.join(WITNESS_DIR, "manifest.json")

_STYLE = re.compile(r"<style>.*?</style>", re.S)
_CLAUSE_ID = re.compile(r"^[DIR]\d+[a-z]?$")

# 三視圖在 SVG 裡的順序與標題(current_geometry.c 的 VIEW_FRAMES:前/側/仰)與各視圖的投影。
VIEWS = {
    "front":  (0, "前視圖", lambda p: (p[0], -p[2])),
    "side":   (1, "側視圖", lambda p: (p[1], -p[2])),
    "bottom": (2, "仰視圖", lambda p: (p[0], p[1])),
}
ROLE_COLOR = {"boundary": "#e2a24a", "primary": "#63b3ed", "secondary": "#9ae6b4", "custom": "#d6bcfa"}
ROLE_LABEL = {"boundary": "boundary 邊界材(層級 1)", "primary": "primary 主支(層級 2)",
              "secondary": "secondary 副支(層級 3)", "custom": "custom 自訂料(priority N)"}
TILE = 900          # 接點格在版面座標裡的邊長(mm 單位的版面格)
TILE_GAP = 60
TILES_PER_ROW = 6
LEGEND_H = 680
WITNESS_CSS = (
    "<style id=\"witness\">"
    ".role-boundary{fill:%s;stroke:%s}.role-primary{fill:%s;stroke:%s}.role-secondary{fill:%s;stroke:%s}.role-custom{fill:%s;stroke:%s}"
    ".stop{stroke:none}"
    ".stop-label{font:bold 110px sans-serif;dominant-baseline:middle;paint-order:stroke;stroke:#ffffff;stroke-width:30px;stroke-linejoin:round}"
    ".tile-frame{fill:#ffffff;stroke:#888888;stroke-width:1px}"
    ".tile-title{font:bold 72px sans-serif;fill:#222222}"
    ".tile line.edge,.tile line.guide,.tile line.edge-free{stroke-width:2px}"
    ".legend-title{font:bold 110px sans-serif;fill:#222222}.legend-text{font:95px sans-serif;fill:#333333;dominant-baseline:middle}"
    ".legend-box{fill:#ffffff;stroke:#bbbbbb;stroke-width:1px}"
    ".section-title{font:bold 120px sans-serif;fill:#222222}"
    "</style>" % tuple(c for r in ("boundary", "primary", "secondary", "custom") for c in (ROLE_COLOR[r], ROLE_COLOR[r]))
)


class WitnessError(Exception):
    pass


# ------------------------------------------------------------------
# manifest
# ------------------------------------------------------------------
def load_manifest():
    if not os.path.exists(MANIFEST):
        raise WitnessError("找不到 manifest:%s" % MANIFEST)
    with io.open(MANIFEST, encoding="utf-8") as f:
        m = json.load(f)
    if not isinstance(m, dict) or not m:
        raise WitnessError("manifest 必須是非空物件 {條號: {...}}")
    clause_ids = {c[0] for c in am.parse_clauses(am.read_text(am.AXIOM))}
    for cid, ent in m.items():
        if not _CLAUSE_ID.match(cid):
            raise WitnessError("manifest 條號格式不合:%r" % cid)
        if cid not in clause_ids:
            raise WitnessError("manifest 條號 %s 不存在於 公理層.md——條文被改號或刪除,先確認" % cid)
        for k in ("scene", "expect", "view", "gist"):
            if k not in ent:
                raise WitnessError("manifest %s 缺欄位 %s" % (cid, k))
        if ent["expect"] not in ("accept", "reject"):
            raise WitnessError("manifest %s 的 expect 只能是 accept / reject" % cid)
        if ent["view"] not in list(VIEWS) + ["all"]:
            raise WitnessError("manifest %s 的 view=%r 不在 %s" % (cid, ent["view"], sorted(VIEWS) + ["all"]))
        if ent.get("joint_view", "bottom") not in VIEWS:
            raise WitnessError("manifest %s 的 joint_view 不合法" % cid)
        scene = os.path.join(ROOT, ent["scene"])
        if not os.path.exists(scene):
            raise WitnessError("manifest %s 指的夾具不存在:%s" % (cid, ent["scene"]))
        text = io.open(scene, encoding="utf-8", errors="replace").read()
        if not re.search(r"(?<![A-Za-z0-9])%s(?![0-9a-z])" % re.escape(cid), text):
            raise WitnessError("夾具 %s 的註解沒有提到 %s——先在夾具裡把連結寫下來(axiom_matrix 的判準),不要只靠 manifest"
                               % (ent["scene"], cid))
    return m


def svg_path(cid):
    return os.path.join(WITNESS_DIR, "%s.svg" % cid)


def joints_path(cid):
    return os.path.join(WITNESS_DIR, "%s.joints.json" % cid)


def _sha(data):
    """行尾正規化後再雜湊:同一個 .scene 在 Windows 是 CRLF、在 Linux 是 LF,那不是夾具內容的改變。"""
    return hashlib.sha256(data.replace(b"\r\n", b"\n")).hexdigest()[:16]


# ------------------------------------------------------------------
# 引擎文字輸出 → 邊 / 角材 / 六面
# ------------------------------------------------------------------
def parse_engine_text(text):
    """回傳 (edges, timbers)。edges: [{surface, hole, index, fixity, p0, p1, axis, value}];
    timbers: {id: {L, A, B, axis(vec), faces: {name: [4 個 3D 點]}}}。"""
    edges, timbers = [], {}
    surface = hole = None
    edge = None
    tid = face = None
    for raw in text.replace("\r\n", "\n").split("\n"):
        line = raw.strip()
        m = re.match(r"承載面 ID：(\d+)", line)
        if m:
            surface, hole = int(m[1]), None
            continue
        m = re.match(r"孔 #(\d+)：", line)
        if m:
            hole = int(m[1])
            continue
        if line.startswith("=== 參考線") or line.startswith("=== 已放置"):
            hole = None
        m = re.match(r"邊 #(\d+)（(FIXED|FREE)）", line)
        if m:
            edge = {"surface": surface, "hole": hole, "index": int(m[1]), "fixity": m[2]}
            continue
        m = re.match(r"房間三維線段：\((.+?)\) -> \((.+?)\)", line)
        if m and edge is not None:
            edge["p0"] = tuple(int(x) for x in m[1].split(", "))
            edge["p1"] = tuple(int(x) for x in m[2].split(", "))
            continue
        m = re.match(r"側向承載平面：([xyz]) = (-?\d+)", line)
        if m and edge is not None:
            edge["axis"], edge["value"] = "xyz".index(m[1]), int(m[2])
            edges.append(edge)
            edge = None
            continue
        m = re.match(r"角材 ID：(\d+)", line)
        if m:
            tid = int(m[1])
            timbers[tid] = {"faces": {}}
            continue
        m = re.match(r"尺寸：L=(\d+)，A=(\d+)，B=(\d+)", line)
        if m and tid is not None:
            timbers[tid].update(L=int(m[1]), A=int(m[2]), B=int(m[3]))
            continue
        m = re.match(r"長度軸：\((-?\d+), (-?\d+), (-?\d+)\)", line)
        if m and tid is not None:
            timbers[tid]["axis"] = (int(m[1]), int(m[2]), int(m[3]))
            continue
        m = re.match(r"角材 (\d+) 的 (A0|A1|B0|B1|START 端面|END 端面)", line)
        if m:
            tid, face = int(m[1]), m[2].split(" ")[0]
            timbers.setdefault(tid, {"faces": {}})["faces"][face] = []
            continue
        m = re.match(r"vertex\[\d\] = \((-?\d+), (-?\d+), (-?\d+)\)", line)
        if m and face is not None:
            timbers[tid]["faces"][face].append((int(m[1]), int(m[2]), int(m[3])))
            continue
    for tid, t in timbers.items():
        for name in ("A0", "A1", "B0", "B1", "START", "END"):
            if len(t["faces"].get(name, [])) != 4:
                raise WitnessError("角材 %d 的 %s 面在引擎輸出裡不完整" % (tid, name))
        if "axis" not in t or "L" not in t:
            raise WitnessError("角材 %d 缺長度軸或尺寸" % tid)
    return edges, timbers


def parse_scene_roles(scene_text):
    """角色是宣告(D15),從 .scene 讀;place 的 on <面> 用來限制邊的候選範圍。"""
    roles, surfaces = {}, {}
    for line in scene_text.replace("\r\n", "\n").split("\n"):
        m = re.match(r"\s*timber\s+(\d+)\s+\d+\s+\d+\s+role\s+(boundary|primary|secondary|custom)(?:\s+priority\s+(\d+))?", line)
        if m:
            roles[int(m[1])] = (m[2], int(m[3]) if m[3] else None)
        m = re.match(r"\s*place\s+(\d+)\s+on\s+(\d+)\b", line)
        if m:
            surfaces[int(m[1])] = int(m[2])
    return roles, surfaces


def _bbox(pts):
    return tuple((min(p[i] for p in pts), max(p[i] for p in pts)) for i in range(3))


def _const_axis(pts):
    b = _bbox(pts)
    axes = [i for i in range(3) if b[i][0] == b[i][1]]
    return axes[0] if len(axes) == 1 else None


def resolve_joints(edges, timbers, roles, surfaces):
    """每個角材端面 → 唯一擋面(D11 三種來源),否則失敗。回傳依 (id, START/END) 排序的清單。"""
    joints = []
    for tid in sorted(timbers):
        t = timbers[tid]
        if tid not in roles:
            raise WitnessError("角材 %d 在 .scene 裡沒有 role(I18)" % tid)
        for end in ("START", "END"):
            pts = t["faces"][end]
            axis = _const_axis(pts)
            if axis is None:
                raise WitnessError("角材 %d 的 %s 端面不是軸對齊平面" % (tid, end))
            value = pts[0][axis]
            eb = _bbox(pts)
            # D11「擋面涵蓋端面全寬」的寬 = 面內橫向(既非長度軸、也非承載面法向 = A0 的法向);
            # 厚度方向(沿法向)不要求涵蓋——27×33 的主支停在 20×20 的邊界材側面是合法的。
            n_axis = _const_axis(t["faces"]["A0"])
            if n_axis is None or n_axis == axis:
                raise WitnessError("角材 %d 的 A0 面法向無法判定" % tid)
            others = [i for i in range(3) if i != axis and i != n_axis]
            cands = []
            # 來源 1:其他角材的側面(法向沿本支長度軸、且不是它自己的端面)
            for uid in sorted(timbers):
                if uid == tid:
                    continue
                u = timbers[uid]
                if u["axis"][axis] != 0:      # u 沿本支長度軸走 → 它在此平面上只有端面,不算側面
                    continue
                for name in ("A0", "A1", "B0", "B1"):
                    fp = u["faces"][name]
                    if _const_axis(fp) != axis or fp[0][axis] != value:
                        continue
                    fb = _bbox(fp)
                    if all(fb[i][0] <= eb[i][0] and eb[i][1] <= fb[i][1] for i in others):
                        cands.append(("t%d" % uid, {"kind": "timber", "id": uid, "face": name}))
                        break
            # 來源 2/3:同承載面的外輪廓邊 / 孔邊(平面相同且沿邊涵蓋端面)
            for e in edges:
                if e["surface"] != surfaces.get(tid) or e["axis"] != axis or e["value"] != value:
                    continue
                d = [i for i in range(3) if e["p0"][i] != e["p1"][i]]
                if len(d) != 1:
                    continue
                lo, hi = sorted((e["p0"][d[0]], e["p1"][d[0]]))
                if lo <= eb[d[0]][0] and eb[d[0]][1] <= hi:
                    ref = ("h%de%d" % (e["hole"], e["index"])) if e["hole"] is not None else ("e%d" % e["index"])
                    cands.append((ref, {"kind": "hole" if e["hole"] is not None else "outline",
                                        "surface": e["surface"], "index": e["index"], "hole": e["hole"], "fixity": e["fixity"]}))
            if len(cands) != 1:
                raise WitnessError("角材 %d 的 %s 端面找到 %d 個擋面候選 %s——反推不唯一,不出圖(規範 §0-2)"
                                   % (tid, end, len(cands), [c[0] for c in cands]))
            ref, info = cands[0]
            joints.append({"t": tid, "end": end, "stop": ref, "detail": info})
    check_no_overlap(timbers, surfaces)
    return joints


def _rect_overlap_area(a, b, axes):
    """兩個 3D bbox 在指定兩軸上的交集面積(邊相接 = 0)。"""
    w = min(a[axes[0]][1], b[axes[0]][1]) - max(a[axes[0]][0], b[axes[0]][0])
    h = min(a[axes[1]][1], b[axes[1]][1]) - max(a[axes[1]][0], b[axes[1]][0])
    return max(0, w) * max(0, h)


def check_no_overlap(timbers, surfaces):
    """物理碰撞自驗(I11):同一承載面上任兩支 A0 footprint 的正面積交集必須為 0。
    引擎本來就擋,這裡再驗一次,讓見證不依賴「引擎沒出錯」這個假設。"""
    ids = sorted(timbers)
    for i, a in enumerate(ids):
        for b in ids[i + 1:]:
            if surfaces.get(a) != surfaces.get(b):
                continue
            fa, fb = timbers[a]["faces"]["A0"], timbers[b]["faces"]["A0"]
            n = _const_axis(fa)
            if n is None or n != _const_axis(fb):
                continue
            axes = [k for k in range(3) if k != n]
            area = _rect_overlap_area(_bbox(fa), _bbox(fb), axes)
            if area > 0:
                raise WitnessError("角材 %d 與 %d 的 footprint 重疊 %d mm²——同一空間被兩個物體占用(I11),不出圖" % (a, b, area))


def check_marks_outside(joints, timbers, view):
    """標記碰撞自驗:每個停止標記矩形(主圖與接點格兩種厚度)不得與**任何**其他角材的 A0 footprint 有正面積交集。"""
    proj = VIEWS[view][2]
    foot = {u: _proj_bbox(timbers[u]["faces"]["A0"], proj) for u in timbers}
    for j in joints:
        for scale in (1.0, 1.6):
            box = stop_mark_box(j, timbers, view, scale)
            if box is None:
                continue
            for u, (ux0, ux1, uy0, uy1) in foot.items():
                if u == j["t"]:
                    continue
                ow = min(box[1], ux1) - max(box[0], ux0)
                oh = min(box[3], uy1) - max(box[2], uy0)
                if ow > 0 and oh > 0:
                    raise WitnessError("t%d·%s 的停止標記侵入 t%d 的 footprint(%g×%g mm)——標註不得暗示不存在的占用"
                                       % (j["t"], j["end"], u, ow, oh))


# ------------------------------------------------------------------
# 引擎 SVG → 版面
# ------------------------------------------------------------------
_G = re.compile(r'<g transform="translate\((-?\d+),(-?\d+)\)">\s*<rect class="frame" x="(-?\d+)" y="(-?\d+)" width="(\d+)" height="(\d+)"/>\s*<text[^>]*class="title">([^<]*)</text>(.*?)</g>', re.S)
_TIMBER_BLOCK = re.compile(r'(<polygon points="[^"]*" class="timber-face"/>)\s*(<polygon points="[^"]*" class="timber-face timber-face-near"/>)\s*(<text[^>]*class="label timber-label">角材(\d+) [^<]*</text>)')


def split_views(svg):
    gs = list(_G.finditer(svg))
    if len(gs) != 3 or "前視圖" not in gs[0][7] or "側視圖" not in gs[1][7] or "仰視圖" not in gs[2][7]:
        raise WitnessError("引擎 SVG 版面不是「前/側/仰」三個 <g>——emit_svg_three_views 變了,規範要跟著改")
    views = {}
    for name, (idx, _, _) in VIEWS.items():
        g = gs[idx]
        views[name] = {"tx": int(g[1]), "ty": int(g[2]), "x": int(g[3]), "y": int(g[4]),
                       "w": int(g[5]), "h": int(g[6]), "title": g[7], "body": g[8]}
    return views


def colorize(body, roles):
    """角材多邊形 → 加角色 class 與 data-t;對不上的角材就失敗(規範 §4)。"""
    seen = set()

    def sub(m):
        tid = int(m[4])
        if tid not in roles:
            raise WitnessError("SVG 裡的角材 %d 沒有角色" % tid)
        role = roles[tid][0]
        seen.add(tid)
        a = m[1].replace('class="timber-face"', 'class="timber-face role-%s" data-t="%d"' % (role, tid))
        b = m[2].replace('class="timber-face timber-face-near"', 'class="timber-face timber-face-near role-%s" data-t="%d"' % (role, tid))
        return a + "\n" + b + "\n" + m[3]
    out = _TIMBER_BLOCK.sub(sub, body)
    return out, seen


def _proj_bbox(pts, proj):
    xy = [proj(p) for p in pts]
    return min(x for x, _ in xy), max(x for x, _ in xy), min(y for _, y in xy), max(y for _, y in xy)


def _fmt(v):
    r = round(v, 1)
    return "%d" % r if r == int(r) else "%.1f" % r


def stop_mark_box(j, timbers, view, scale=1.0):
    """停止標記的矩形 (x0,x1,y0,y1),在該視圖座標;端面退化成點時回 None。
    範圍 = 端面本身的寬 × 向被裁料內側 thick(0.3×料寬×scale);整個在自己 footprint 內,不外延、不壓接觸面外側。"""
    proj = VIEWS[view][2]
    t = timbers[j["t"]]
    w = max(t["A"], t["B"])
    pts = t["faces"][j["end"]]
    x0, x1, y0, y1 = _proj_bbox(pts, proj)
    if (x1 - x0 == 0) == (y1 - y0 == 0):
        return None
    thick = max(4, int(w * 0.3 * scale))
    sgn_in = -1 if j["end"] == "END" else 1
    ix, iy = proj(tuple(sgn_in * c for c in t["axis"]))
    if y1 - y0 == 0:          # 端面是水平線段 → 長度軸沿 y
        lo, hi = sorted((y0, y0 + iy * thick))
        return (x0, x1, lo, hi)
    lo, hi = sorted((x0, x0 + ix * thick))
    return (lo, hi, y0, y1)


def stop_marks(joints, timbers, roles, view, with_label=False, scale=1.0):
    """停止標記 = 填色矩形(無 stroke)。不用 <line stroke-width>:引擎 CSS 的 vector-effect:non-scaling-stroke
    會讓線條粗度變成螢幕像素,縮小時穿過整支料(GEO-137)。矩形佔的範圍就是座標寫的範圍。"""
    out = []
    for j in joints:
        box = stop_mark_box(j, timbers, view, scale)
        if box is None:
            continue
        x0, x1, y0, y1 = box
        color = ROLE_COLOR[roles[j["t"]][0]]
        out.append('<rect x="%s" y="%s" width="%s" height="%s" class="stop" fill="%s" data-joint="t%d.%s"/>'
                   % (_fmt(x0), _fmt(y0), _fmt(x1 - x0), _fmt(y1 - y0), color, j["t"], j["end"]))
    return "\n".join(out)


def _strip_text(body):
    return re.sub(r"<text\b[^>]*>.*?</text>\s*", "", body, flags=re.S)


# ---- 接點格:預先裁切成平面幾何(GEO-136) ----
# 為什麼不用巢狀 <svg viewBox> 或 <g transform>:很多 SVG 檢視器不裁切巢狀 viewBox,
# 整個場景會不裁切地畫出來,看起來像料互相穿越。這裡在 Python 裡把每個形狀裁到視窗、
# 算成版面座標,只輸出 polygon / line / rect——任何檢視器只能畫出同一個結果。

def _clip_poly(pts, rect):
    """Sutherland–Hodgman:多邊形裁到軸對齊矩形 (x0,x1,y0,y1)。"""
    x0, x1, y0, y1 = rect

    def clip(poly, inside, intersect):
        out = []
        for i, cur in enumerate(poly):
            prev = poly[i - 1]
            if inside(cur):
                if not inside(prev):
                    out.append(intersect(prev, cur))
                out.append(cur)
            elif inside(prev):
                out.append(intersect(prev, cur))
        return out

    def ix(a, b, x):
        t = (x - a[0]) / (b[0] - a[0])
        return (x, a[1] + t * (b[1] - a[1]))

    def iy(a, b, y):
        t = (y - a[1]) / (b[1] - a[1])
        return (a[0] + t * (b[0] - a[0]), y)

    poly = list(pts)
    for inside, intersect in (
        (lambda p: p[0] >= x0, lambda a, b: ix(a, b, x0)),
        (lambda p: p[0] <= x1, lambda a, b: ix(a, b, x1)),
        (lambda p: p[1] >= y0, lambda a, b: iy(a, b, y0)),
        (lambda p: p[1] <= y1, lambda a, b: iy(a, b, y1)),
    ):
        if not poly:
            return []
        poly = clip(poly, inside, intersect)
    return poly


def _clip_line(a, b, rect):
    """Liang–Barsky:線段裁到矩形;不相交回 None。"""
    x0, x1, y0, y1 = rect
    dx, dy = b[0] - a[0], b[1] - a[1]
    t0, t1 = 0.0, 1.0
    for p, q in ((-dx, a[0] - x0), (dx, x1 - a[0]), (-dy, a[1] - y0), (dy, y1 - a[1])):
        if p == 0:
            if q < 0:
                return None
            continue
        t = q / p
        if p < 0:
            if t > t1:
                return None
            t0 = max(t0, t)
        else:
            if t < t0:
                return None
            t1 = min(t1, t)
    return (a[0] + t0 * dx, a[1] + t0 * dy), (a[0] + t1 * dx, a[1] + t1 * dy)


_EL = re.compile(r'<(polygon|line|rect)\b([^>]*)/>')
_ATTR = re.compile(r'([\w-]+)="([^"]*)"')


def flat_tile(body, marks, window, px, py, size):
    """把視圖內容(引擎 SVG 片段,已著色、已去文字)裁到 window=(wx0,wx1,wy0,wy1),
    映射到版面座標 (px,py) 起、邊長 size 的方格,輸出平面元素。"""
    wx0, wx1, wy0, wy1 = window
    k = size / float(wx1 - wx0)

    def M(pt):
        return (px + (pt[0] - wx0) * k, py + (pt[1] - wy0) * k)

    out = []
    for m in _EL.finditer(body + "\n" + marks):
        tag, attrs = m.group(1), dict(_ATTR.findall(m.group(2)))
        cls = attrs.get("class", "")
        if tag == "rect" and "frame" in cls:
            continue
        keep = " ".join('%s="%s"' % (k_, attrs[k_]) for k_ in ("class", "data-t", "data-joint", "fill") if k_ in attrs)
        if tag == "polygon":
            pts = [tuple(map(float, q.split(","))) for q in attrs["points"].split()]
            c = _clip_poly(pts, window)
            if len(c) >= 3:
                out.append('<polygon points="%s" %s/>' % (" ".join("%s,%s" % (_fmt(a), _fmt(b)) for a, b in map(M, c)), keep))
        elif tag == "rect":
            x, y, w, h = (float(attrs[k_]) for k_ in ("x", "y", "width", "height"))
            c = _clip_poly([(x, y), (x + w, y), (x + w, y + h), (x, y + h)], window)
            if len(c) >= 3:
                out.append('<polygon points="%s" %s/>' % (" ".join("%s,%s" % (_fmt(a), _fmt(b)) for a, b in map(M, c)), keep))
        else:
            a = (float(attrs["x1"]), float(attrs["y1"]))
            b = (float(attrs["x2"]), float(attrs["y2"]))
            c = _clip_line(a, b, window)
            if c:
                (ax, ay), (bx, by) = M(c[0]), M(c[1])
                sw = ' stroke-width="%s"' % _fmt(float(attrs["stroke-width"]) * k) if "stroke-width" in attrs else ""
                out.append('<line x1="%s" y1="%s" x2="%s" y2="%s" %s%s/>' % (_fmt(ax), _fmt(ay), _fmt(bx), _fmt(by), keep, sw))
    return "\n".join(out)


def compose(cid, ent, engine_svg, joints, timbers, roles):
    """依規範 v1 組版:① 主圖 ② 接點列 ③ 圖例。回傳 SVG 字串(LF)。"""
    engine_style = _STYLE.search(engine_svg)
    engine_style = engine_style.group(0) if engine_style else ""
    views = split_views(engine_svg)
    view = ent["view"]
    jview = ent.get("joint_view", "bottom")
    check_marks_outside(joints, timbers, jview)
    for name in views:
        views[name]["body"], seen = colorize(views[name]["body"], roles)
        if name == jview and seen != set(timbers):
            raise WitnessError("%s:主圖的角材多邊形 %s 與引擎輸出的角材 %s 對不上" % (cid, sorted(seen), sorted(timbers)))

    # ① 主圖
    if view == "all":
        names = ["front", "side", "bottom"]
        x0 = min(views[n]["tx"] + views[n]["x"] for n in names)
        y0 = min(views[n]["ty"] + views[n]["y"] for n in names)
        x1 = max(views[n]["tx"] + views[n]["x"] + views[n]["w"] for n in names)
        y1 = max(views[n]["ty"] + views[n]["y"] + views[n]["h"] for n in names)
    else:
        v = views[view]
        x0, y0, x1, y1 = v["tx"] + v["x"], v["ty"] + v["y"], v["tx"] + v["x"] + v["w"], v["ty"] + v["y"] + v["h"]
        names = [view]
    y0 -= 80
    main = []
    for n in names:
        v = views[n]
        main.append('<g transform="translate(%d,%d)" data-view="%s">\n<rect class="frame" x="%d" y="%d" width="%d" height="%d"/>\n<text x="%d" y="%d" class="title">%s</text>%s\n%s\n</g>'
                    % (v["tx"], v["ty"], n, v["x"], v["y"], v["w"], v["h"], v["x"] + 60, v["y"] + 110, v["title"], v["body"],
                       stop_marks(joints, timbers, roles, n, with_label=False)))
    W = x1 - x0

    # ② 接點列
    tiles = []
    ty = y1 + 80
    tiles.append('<text x="%d" y="%d" class="section-title">接點列(每格 = 一個角材端面,等比例放大,窗 = 8 × 料寬;視圖:%s)</text>'
                 % (x0 + 40, ty + 130, VIEWS[jview][1]))
    ty += 220
    if not joints:
        tiles.append('<text x="%d" y="%d" class="legend-text">本條無角材接點。</text>' % (x0 + 40, ty + 100))
        ty += 220
    else:
        tile = min(TILE, (W - TILE_GAP * (TILES_PER_ROW - 1)) // TILES_PER_ROW)
        per_row = max(1, min(TILES_PER_ROW, (W + TILE_GAP) // (tile + TILE_GAP)))
        v = views[jview]
        scene_body = _strip_text(v["body"])
        proj = VIEWS[jview][2]
        for k, j in enumerate(joints):
            t = timbers[j["t"]]
            w = max(t["A"], t["B"])
            cx0, cx1, cy0, cy1 = _proj_bbox(t["faces"][j["end"]], proj)
            cx, cy = (cx0 + cx1) / 2.0, (cy0 + cy1) / 2.0
            half = 4 * w
            col, row = k % per_row, k // per_row
            px = x0 + col * (tile + TILE_GAP)
            py = ty + row * (tile + TILE_GAP + 140)
            title = "t%d·%s→%s%s" % (j["t"], j["end"], j["stop"], "(RC)" if j["detail"]["kind"] == "outline" else "")
            inner = stop_marks([j], timbers, roles, jview, with_label=False, scale=1.6)
            window = (cx - half, cx + half, cy - half, cy + half)
            tiles.append(
                '<text x="%d" y="%d" class="tile-title">%s</text>\n'
                '<rect x="%d" y="%d" width="%d" height="%d" class="tile-frame"/>\n'
                '<g class="tile" data-joint="t%d.%s">\n%s\n</g>'
                % (px, py + 100, title, px, py + 130, tile, tile, j["t"], j["end"],
                   flat_tile(scene_body, inner, window, px, py + 130, tile)))
        rows = (len(joints) + per_row - 1) // per_row
        ty += rows * (tile + TILE_GAP + 140)

    # ③ 圖例
    legend = ['<rect x="%d" y="%d" width="%d" height="%d" class="legend-box"/>' % (x0, ty, W, LEGEND_H),
              '<text x="%d" y="%d" class="legend-title">圖例(每張見證圖相同;規範 v1)</text>' % (x0 + 40, ty + 130)]
    step = (W - 80) // 2
    for k, r in enumerate(("boundary", "primary", "secondary", "custom")):
        lx, ly = x0 + 40 + (k % 2) * step, ty + 200 + (k // 2) * 130
        legend.append('<rect x="%d" y="%d" width="160" height="80" class="role-%s"/><text x="%d" y="%d" class="legend-text">%s</text>'
                      % (lx, ly, r, lx + 190, ly + 40, ROLE_LABEL[r]))
    legend.append('<rect x="%d" y="%d" width="40" height="80" class="stop" fill="#333333"/>'
                  '<text x="%d" y="%d" class="legend-text">停止標記 = 端面被裁的位置(同角材色);接點格標題 t3·END→t2 = 角材 3 的 END 端面停在角材 2 的側面。</text>'
                  '<text x="%d" y="%d" class="legend-text">→e0 = 停在外輪廓邊 0(RC;只有 boundary 可頂,I19);→h0e2 = 停在孔 0 的邊 2。擋面參照寫法同 D18。</text>'
                  % (x0 + 60, ty + 460, x0 + 190, ty + 500, x0 + 190, ty + 600))
    H = ty + LEGEND_H - y0

    head = ('<?xml version="1.0" encoding="UTF-8"?>\n'
            '<!-- witness %s <- %s (%s, view=%s) scene-sha256=%s spec=v1 -->\n'
            '<!-- %s -->\n'
            '<svg xmlns="http://www.w3.org/2000/svg" width="100%%" viewBox="%d %d %d %d" data-full="%d %d %d %d">\n'
            % (cid, ent["scene"], ent["expect"], view, ent["_scene_sha"], ent["gist"].replace("--", "- -"),
               x0, y0, W, H, x0, y0, W, H))
    return head + engine_style + "\n" + WITNESS_CSS + "\n" + "\n".join(main) + "\n" + "\n".join(tiles) + "\n" + "\n".join(legend) + "\n</svg>\n"


# ------------------------------------------------------------------
# render
# ------------------------------------------------------------------
def render_one(exe, cid, ent, tmpdir):
    """回傳 (svg_bytes, joints_bytes, info)。任何一步不成立就 raise,不產空圖。"""
    scene = os.path.join(ROOT, ent["scene"])
    scene_bytes = open(scene, "rb").read()
    r = ax.run_scene(exe, scene, tmpdir)
    if ent["expect"] == "accept":
        if r["rc"] != 0:
            raise WitnessError("%s:夾具 %s 標 accept 但引擎拒絕(rc=%d):%s"
                               % (cid, ent["scene"], r["rc"], (r["err"] or "").strip()[:200]))
        full_svg, text = r["svg"], r["out"]
    else:
        if r["rc"] == 0:
            raise WitnessError("%s:夾具 %s 標 reject 但引擎接受(rc=0)——夾具或引擎變了,先確認" % (cid, ent["scene"]))
        full_svg, note, why = ax.before_failure(exe, scene, r["err"], tmpdir)
        if not full_svg:
            raise WitnessError("%s:拒絕型夾具無法重建失敗前狀態:%s" % (cid, why))
        text = ax.run_scene(exe, os.path.join(tmpdir, "_before.scene"), tmpdir)["out"]
    if not full_svg or 'class="surface"' not in full_svg:
        raise WitnessError("%s:引擎輸出沒有任何承載面(空框)" % cid)
    full_svg = full_svg.replace("\r\n", "\n")

    edges, timbers = parse_engine_text(text or "")
    roles, surfaces = parse_scene_roles(scene_bytes.decode("utf-8", "replace"))
    joints = resolve_joints(edges, timbers, roles, surfaces)
    ent = dict(ent, _scene_sha=_sha(scene_bytes))
    svg = compose(cid, ent, full_svg, joints, timbers, roles)

    jdoc = {
        "clause": cid, "scene": ent["scene"], "view": ent["view"], "spec": "v1",
        "timbers": {str(t): {"role": roles[t][0], "priority": roles[t][1], "L": timbers[t]["L"],
                             "A": timbers[t]["A"], "B": timbers[t]["B"], "axis": list(timbers[t]["axis"])}
                    for t in sorted(timbers)},
        "joints": [{"t": j["t"], "end": j["end"], "stop": j["stop"], "kind": j["detail"]["kind"]} for j in joints],
    }
    jbytes = (json.dumps(jdoc, ensure_ascii=False, indent=1) + "\n").encode("utf-8")
    return svg.encode("utf-8"), jbytes, {"scene_sha": ent["_scene_sha"], "joints": len(joints)}


# ------------------------------------------------------------------
# commands
# ------------------------------------------------------------------
def _select(manifest, ids):
    if not ids:
        return list(manifest.items())
    missing = [i for i in ids if i not in manifest]
    if missing:
        raise WitnessError("manifest 沒有這些條號:%s" % ", ".join(missing))
    return [(i, manifest[i]) for i in ids]


def cmd_build(exe, manifest, ids, force):
    os.makedirs(WITNESS_DIR, exist_ok=True)
    tmp = tempfile.mkdtemp(prefix="witness_")
    try:
        ax.smoke(exe, tmp)
        failed = 0
        for cid, ent in _select(manifest, ids):
            try:
                svg, jb, info = render_one(exe, cid, ent, tmp)
            except WitnessError as exc:
                print("  失敗   %-5s %s" % (cid, exc))
                failed += 1
                continue
            targets = [(svg_path(cid), svg), (joints_path(cid), jb)]
            if all(os.path.exists(p) and open(p, "rb").read() == d for p, d in targets):
                print("  不變   %-5s %s" % (cid, ent["scene"]))
                continue
            if any(os.path.exists(p) for p, _ in targets) and not force:
                raise WitnessError(
                    "%s 已有見證且與重跑結果不同。這是警報不是待更新:先跑 --check 看 diff,"
                    "確認是夾具/引擎/條文哪一邊該改;確定要以新圖為準時再加 --force。" % cid)
            for p, d in targets:
                open(p, "wb").write(d)
            print("  寫入   %-5s %s  (接點 %d,夾具 sha %s)" % (cid, os.path.relpath(svg_path(cid), ROOT), info["joints"], info["scene_sha"]))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    if failed:
        print("\n%d 條建不出見證(見上)。" % failed)
        return 1
    return 0


def _scene_sha_in(svg_bytes):
    m = re.search(rb"scene-sha256=([0-9a-f]{16})", svg_bytes)
    return m.group(1).decode() if m else None


def _print_diff(old, new, label):
    lines = list(difflib.unified_diff(old.decode("utf-8", "replace").splitlines(), new.decode("utf-8", "replace").splitlines(),
                                      label + " (commit)", label + " (重跑)", lineterm="", n=1))
    for ln in lines[:40]:
        print("      " + ln)
    if len(lines) > 40:
        print("      … 共 %d 行差異" % len(lines))


def cmd_check(exe, manifest, ids):
    tmp = tempfile.mkdtemp(prefix="witness_")
    bad = 0
    try:
        ax.smoke(exe, tmp)
        print("引擎 exe sha256=%s" % _sha(open(exe, "rb").read()))
        for cid, ent in _select(manifest, ids):
            if not os.path.exists(svg_path(cid)) or not os.path.exists(joints_path(cid)):
                print("  缺圖   %-5s 尚未 --build" % cid)
                bad += 1
                continue
            old_svg, old_j = open(svg_path(cid), "rb").read(), open(joints_path(cid), "rb").read()
            try:
                new_svg, new_j, info = render_one(exe, cid, ent, tmp)
            except WitnessError as exc:
                print("  失敗   %-5s %s" % (cid, exc))
                bad += 1
                continue
            if old_svg == new_svg and old_j == new_j:
                print("  一致   %-5s %s  (接點 %d)" % (cid, ent["scene"], info["joints"]))
                continue
            bad += 1
            old_sha = _scene_sha_in(old_svg)
            if old_sha and old_sha != info["scene_sha"]:
                cause = "夾具 %s 內容變了(sha %s → %s)" % (ent["scene"], old_sha, info["scene_sha"])
            elif old_j != new_j:
                cause = "夾具沒變,但**接點拓樸**變了(引擎對同一夾具的推導結果不同)"
            else:
                cause = "夾具沒變、拓樸沒變,引擎的幾何輸出變了"
            print("  ⚠ 警報 %-5s %s" % (cid, cause))
            if old_j != new_j:
                _print_diff(old_j, new_j, "witness/%s.joints.json" % cid)
            else:
                _print_diff(old_svg, new_svg, "witness/%s.svg" % cid)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    if bad:
        print("\n%d 條見證不成立。本工具不覆寫;請確認是夾具、引擎還是條文該改,確定後才以 --build --force 重建。" % bad)
        return 1
    print("\n全部 %d 條見證一致。" % len(_select(manifest, ids)))
    return 0


def cmd_list(manifest):
    for cid, ent in manifest.items():
        state = "有圖" if os.path.exists(svg_path(cid)) and os.path.exists(joints_path(cid)) else "缺圖"
        print("  %-5s %s  %-32s %s  %s" % (cid, state, ent["scene"], ent["expect"], ent["gist"]))
    return 0


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--build", action="store_true")
    g.add_argument("--check", action="store_true")
    g.add_argument("--list", action="store_true")
    p.add_argument("--force", action="store_true", help="--build 時允許覆蓋已存在且不同的見證")
    p.add_argument("--exe", help="geometry 執行檔;預設 GEO_EXE 或 tests/cg_new.exe")
    p.add_argument("ids", nargs="*", help="只處理這些條號;不給 = 全部")
    a = p.parse_args(argv)
    manifest = load_manifest()
    if a.list:
        return cmd_list(manifest)
    exe = ax.resolve_exe(a.exe)
    if a.build:
        return cmd_build(exe, manifest, a.ids, a.force)
    return cmd_check(exe, manifest, a.ids)


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (WitnessError, ax.RenderError) as exc:
        print("FAIL:%s" % exc)
        sys.exit(2)
