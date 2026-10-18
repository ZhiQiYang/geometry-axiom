"""獨立讀場景檔文字，重算每支角材的足跡。

這個模組刻意不 import gen_scenes：產生器自己的邊、材料側、角色表一概不借用，
免得「拿產生器的答案去驗產生器」。它只讀場景檔文字，規則來源是 公理層.md
與 mapping.md：

- I13 at-line：足跡 = 中線 ± ⌊w/2⌋/⌈w/2⌉，奇數寬多的 1 mm 在 +cross 側。
- I13 at-face：足跡貼齊該邊，向材料側展一個寬度。外輪廓的材料側在邊的區域一側；
  孔邊的材料側 = 外向法線側（孔以外）。區域在哪一側由頂點順序的有號面積算出，不假設逆時針。
- D7：place 不寫長度。between X Y 的兩個擋面決定長度：邊 = 邊所在座標，
  角材 = 面向本支的那一個側面（較低的擋面取它的高側面，較高的擋面取它的低側面）。
- R6(d)：擋面必須在寬向上蓋住整段，點接觸不算。

只認 between。遇到 through 就把該支標成「長度無法由場景文字推出」，不猜。
"""

from __future__ import annotations

import json
import re

PLACE_AT_FACE = "face"
PLACE_AT_LINE = "line"


class SceneError(Exception):
    """場景文字讀不懂，或推不出足跡。"""


def _points(text: str) -> list[tuple[int, int]]:
    pts = []
    for token in text.split():
        if "," not in token:
            raise SceneError(f"頂點不是 u,v：{token}")
        u, v = token.split(",", 1)
        pts.append((int(u), int(v)))
    if len(pts) < 3:
        raise SceneError("輪廓少於 3 個頂點")
    return pts


def _signed_area(pts: list[tuple[int, int]]) -> int:
    total = 0
    for i, (x0, y0) in enumerate(pts):
        x1, y1 = pts[(i + 1) % len(pts)]
        total += x0 * y1 - x1 * y0
    return total  # 兩倍面積；正 = 逆時針


class Edge:
    """一條軸對齊的輪廓邊。axis 是邊延伸的軸，coord 是它在另一軸上的固定座標。"""

    def __init__(self, ref: str, hole: int | None, p0, p1, region_left: bool):
        self.ref = ref
        self.hole = hole
        (x0, y0), (x1, y1) = p0, p1
        if y0 == y1 and x0 != x1:
            self.axis = "x"
            self.coord = y0
            self.lo, self.hi = min(x0, x1), max(x0, x1)
            self.step = 1 if x1 > x0 else -1
            normal_left = (0, 1) if x1 > x0 else (0, -1)
        elif x0 == x1 and y0 != y1:
            self.axis = "y"
            self.coord = x0
            self.lo, self.hi = min(y0, y1), max(y0, y1)
            self.step = 1 if y1 > y0 else -1
            normal_left = (-1, 0) if y1 > y0 else (1, 0)
        else:
            raise SceneError(f"邊 {ref} 不是軸對齊或退化")
        # 材料側的單位法向量（只有一個分量非零）
        sign = 1 if region_left else -1
        self.region_normal = (normal_left[0] * sign, normal_left[1] * sign)


def _loop_edges(pts, hole: int | None) -> list[Edge]:
    area = _signed_area(pts)
    if area == 0:
        raise SceneError("輪廓面積為 0")
    ccw = area > 0
    # 外輪廓：區域在邊的左側（逆時針）。孔：區域在孔的外面，與外輪廓相反。
    region_left = ccw if hole is None else (not ccw)
    edges = []
    for i, p0 in enumerate(pts):
        p1 = pts[(i + 1) % len(pts)]
        ref = f"e{i}" if hole is None else f"h{hole}e{i}"
        edges.append(Edge(ref, hole, p0, p1, region_left))
    return edges


class Member:
    def __init__(self, line_no: int, ident: int, section_a: int, role: str, priority):
        self.line_no = line_no
        self.id = ident
        self.a = section_a
        self.role = role
        self.priority = priority
        self.place_kind = None
        self.ref = None  # at-face 的邊名
        self.grid_axis = None
        self.grid_index = None
        self.stops: tuple[str, str] | None = None
        self.through = None
        self.direction = None
        self.side = None
        self.meta: dict | None = None  # 緊鄰其前的 # probe-member 註解（只供一致性比對，不用來算足跡）

    @property
    def length_axis(self) -> str:
        return "x" if self.direction[1] == "u" else "y"

    @property
    def cross_axis(self) -> str:
        return "y" if self.length_axis == "x" else "x"


class Scene:
    def __init__(self):
        self.edges: dict[str, Edge] = {}
        self.grid: dict[str, list[int]] = {}
        self.members: list[Member] = []  # 檔案順序 = 放置順序
        self.meta: dict = {}
        self.surface_seen = False


_TIMBER = re.compile(r"^timber (\d+) (\d+) (\d+) role (\w+)(?: priority (\d+))?$")


def parse_scene(text: str) -> Scene:
    scene = Scene()
    pending_meta = None
    by_id: dict[int, Member] = {}
    for line_no, raw in enumerate(text.replace("\r\n", "\n").split("\n"), start=1):
        line = raw.strip()
        if not line:
            continue
        if line.startswith("# probe-meta "):
            scene.meta = json.loads(line[len("# probe-meta "):])
            continue
        if line.startswith("# probe-member "):
            pending_meta = json.loads(line[len("# probe-member "):])
            continue
        if line.startswith("#"):
            continue
        head = line.split()[0]
        if head == "surface":
            if scene.surface_seen:
                raise SceneError(f"第 {line_no} 行：不只一個承載面")
            scene.surface_seen = True
            tokens = line.split()
            if tokens[1:3] != ["1", "origin"] or tokens[3:5] != ["0", "0"]:
                raise SceneError(f"第 {line_no} 行：只支援原點在 (0,0) 的承載面")
            if "u +x v +y" not in line:
                raise SceneError(f"第 {line_no} 行：只支援 u +x v +y")
            if " outline " not in line:
                raise SceneError(f"第 {line_no} 行：沒有 outline")
            tail = line.split(" outline ", 1)[1]
            parts = tail.split(" hole ")
            for edge in _loop_edges(_points(parts[0]), None):
                scene.edges[edge.ref] = edge
            for hole_index, part in enumerate(parts[1:]):
                for edge in _loop_edges(_points(part), hole_index):
                    scene.edges[edge.ref] = edge
        elif head == "grid":
            tokens = line.split()
            if tokens[:4] != ["grid", "1", "on", "1"]:
                raise SceneError(f"第 {line_no} 行：格線宣告讀不懂")
            axis = None
            for token in tokens[4:]:
                if token in ("u", "v"):
                    axis = token
                    scene.grid.setdefault(axis, [])
                else:
                    scene.grid[axis].append(int(token))
        elif head == "timber":
            match = _TIMBER.match(line)
            if not match:
                raise SceneError(f"第 {line_no} 行：timber 讀不懂")
            ident, a, _b, role, priority = match.groups()
            member = Member(line_no, int(ident), int(a), role, int(priority) if priority else None)
            if member.id in by_id:
                raise SceneError(f"第 {line_no} 行：角材 {member.id} 重複宣告")
            member.meta = pending_meta
            pending_meta = None
            by_id[member.id] = member
        elif head == "place":
            _read_place(line, line_no, by_id, scene)
        else:
            raise SceneError(f"第 {line_no} 行：不認得的指令 {head}")
    for member in by_id.values():
        if member.place_kind is None:
            raise SceneError(f"角材 {member.id} 有 timber 宣告卻沒有 place")
    return scene


def _read_place(line: str, line_no: int, by_id: dict, scene: Scene) -> None:
    tokens = line.split()
    if len(tokens) < 9 or tokens[2] != "on" or tokens[3] != "1":
        raise SceneError(f"第 {line_no} 行：place 讀不懂")
    member = by_id.get(int(tokens[1]))
    if member is None:
        raise SceneError(f"第 {line_no} 行：place 的角材 {tokens[1]} 沒有 timber 宣告")
    if member.place_kind is not None:
        raise SceneError(f"第 {line_no} 行：角材 {member.id} 重複 place")
    member.direction = tokens[-2]
    member.side = tokens[-1]
    if member.direction not in ("+u", "-u", "+v", "-v") or member.side not in ("+n", "-n"):
        raise SceneError(f"第 {line_no} 行：方向或深度讀不懂")
    kind = tokens[4]
    body = tokens[5:-2]
    if kind == "at-face":
        member.place_kind = PLACE_AT_FACE
        member.ref = body[0]
        body = body[1:]
    elif kind == "at-line":
        if body[:2] != ["grid", "1"]:
            raise SceneError(f"第 {line_no} 行：只支援 at-line grid 1")
        member.place_kind = PLACE_AT_LINE
        member.grid_axis = body[2]
        member.grid_index = int(body[3])
        body = body[4:]
    else:
        raise SceneError(f"第 {line_no} 行：不認得的錨法 {kind}")
    if body and body[0] == "between" and len(body) == 3:
        member.stops = (body[1], body[2])
    elif body and body[0] == "through" and len(body) == 2:
        member.through = int(body[1])
    else:
        raise SceneError(f"第 {line_no} 行：跨距讀不懂 {body}")
    scene.members.append(member)


def _span(rect, axis: str) -> tuple[int, int]:
    return (rect[0], rect[2]) if axis == "x" else (rect[1], rect[3])


def _cross_extent(member: Member, scene: Scene) -> tuple[int, int]:
    w = member.a
    if member.place_kind == PLACE_AT_LINE:
        # grid 軸 u 的線是 x = 常數；v 的線是 y = 常數
        line_axis = "x" if member.grid_axis == "u" else "y"
        if line_axis != member.cross_axis:
            raise SceneError(f"角材 {member.id}：格線軸與長度方向不垂直")
        coords = scene.grid.get(member.grid_axis)
        if not coords or not (0 <= member.grid_index < len(coords)):
            raise SceneError(f"角材 {member.id}：格線索引 {member.grid_index} 不存在")
        center = coords[member.grid_index]
        return center - w // 2, center + (w - w // 2)
    edge = scene.edges.get(member.ref)
    if edge is None:
        raise SceneError(f"角材 {member.id}：邊 {member.ref} 不存在")
    if edge.axis != member.length_axis:
        raise SceneError(f"角材 {member.id}：方向 {member.direction} 沒有平行於邊 {member.ref}")
    if member.side != "+n":
        raise SceneError(f"角材 {member.id}：只支援深度 +n（材料側）")
    normal = edge.region_normal[0] if edge.axis == "y" else edge.region_normal[1]
    return (edge.coord, edge.coord + w) if normal > 0 else (edge.coord - w, edge.coord)


def derive_footprints(scene: Scene) -> dict[int, tuple | None]:
    """依檔案順序（= 放置順序）推每支足跡。回傳 {id: (x0,y0,x1,y1) 或 None}。

    None 表示長度推不出來（through），或擋面角材還沒放置／本身推不出。
    擋面角材必須在本支之前出現；這就是「擋面先放」的獨立檢查。
    """
    rects: dict[int, tuple | None] = {}
    for member in scene.members:
        cross = _cross_extent(member, scene)
        if member.stops is None:
            rects[member.id] = None
            continue
        la, cr = member.length_axis, member.cross_axis
        resolved = []
        for ref in member.stops:
            if ref.startswith("t"):
                other = int(ref[1:])
                if other not in rects:
                    raise SceneError(f"角材 {member.id} 的擋面 {ref} 在它之後才放置（或不存在）")
                orect = rects[other]
                if orect is None:
                    resolved = None
                    break
                olo, ohi = _span(orect, la)
                clo, chi = _span(orect, cr)
                if clo > cross[0] or chi < cross[1]:
                    raise SceneError(f"角材 {member.id} 的擋面 {ref} 在寬向上沒有蓋住整段")
                resolved.append(("timber", olo, ohi))
            else:
                edge = scene.edges.get(ref)
                if edge is None:
                    raise SceneError(f"角材 {member.id} 的擋面 {ref} 不存在")
                if edge.axis == la:
                    raise SceneError(f"角材 {member.id} 的擋面邊 {ref} 與長度方向平行，頂不到端面")
                if edge.lo > cross[0] or edge.hi < cross[1]:
                    raise SceneError(f"角材 {member.id} 的擋面邊 {ref} 在寬向上沒有蓋住整段")
                resolved.append(("edge", edge.coord, edge.coord))
        if resolved is None:
            rects[member.id] = None
            continue
        low, high = sorted(resolved, key=lambda item: item[1] + item[2])
        start = low[2]  # 較低的擋面：取它的高側面（邊則是座標本身）
        end = high[1]  # 較高的擋面：取它的低側面
        if end <= start:
            raise SceneError(f"角材 {member.id}：兩個擋面之間沒有正長度 [{start}, {end}]")
        if la == "x":
            rects[member.id] = (start, cross[0], end, cross[1])
        else:
            rects[member.id] = (cross[0], start, cross[1], end)
    return rects


def end_stoppers(rects: dict, axes: dict, ident: int, end: str) -> list[int]:
    """本支某一端頂住的角材：垂直本支、端面座標相接、且在寬向上蓋住本支整個寬度。"""
    mine = rects[ident]
    la = axes[ident]
    cr = "y" if la == "x" else "x"
    lo, hi = _span(mine, la)
    wlo, whi = _span(mine, cr)
    face = lo if end == "lo" else hi
    found = []
    for other, orect in rects.items():
        if other == ident or orect is None or axes[other] == la:
            continue
        olo, ohi = _span(orect, la)
        owlo, owhi = _span(orect, cr)
        touches = (ohi == face and olo < face) if end == "lo" else (olo == face and ohi > face)
        if touches and owlo <= wlo and owhi >= whi:
            found.append(other)
    return found
