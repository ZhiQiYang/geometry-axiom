"""把下角材 oracle 的可施工排法轉成原生核心場景 DSL。

只產生探針，不改座標去遷就核心。place 不寫長度（D7）；矩形留在
# probe-member 註解，供測試與 oracle 逐支比對。
"""

from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
DEFAULT_GOLDEN = HERE.parents[0] / "oracle" / "oracle-golden.json"
# parents[0] 是 framing-template。golden 在其 oracle/ 下。

CORE_MAX_TIMBERS = 64  # current_geometry.c WORLD_MAX_TIMBERS；尚未實跑
SECTION_B = 33  # 既有天花場景的 B，不在 golden
ORIGIN_Z = 2500
SURFACE_ID = 1
GRID_ID = 1

SLUGS = {
    "F1客廳": "f1",
    "F2主臥": "f2",
    "F3次臥": "f3",
    "F4走道": "f4",
    "F5廚房": "f5",
    "例:3700×2000 矩形(最後一條縫挪動)": "ex3700",
    "例:940×2000 矩形(第一條縫就要挪)": "ex940",
    "例:縫寬 3 的 3700×4000 矩形(反向起鋪首縫取上界)": "ex3700-gap3",
}


class ProbeError(Exception):
    pass


def slug_for(name: str) -> str:
    if name in SLUGS:
        return SLUGS[name]
    chars = []
    for ch in name:
        chars.append(ch.lower() if ch.isascii() and ch.isalnum() else "-")
    slug = "".join(chars).strip("-")
    while "--" in slug:
        slug = slug.replace("--", "-")
    if not slug:
        raise ProbeError(f"無法為房間取檔名：{name}")
    return slug


def as_int(value, what: str) -> int:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ProbeError(f"{what} 不是整數：{value!r}")
    if isinstance(value, float) and not value.is_integer():
        raise ProbeError(f"{what} 不是整數：{value!r}")
    return int(value)


def layout_kept(layout: dict) -> bool:
    return bool(layout.get("buildable")) and not layout.get("conflict_codes")


def rect_of(raw) -> tuple[int, int, int, int]:
    if len(raw) != 4:
        raise ProbeError(f"矩形不是四個數：{raw!r}")
    x0, y0, x1, y1 = (as_int(v, "矩形座標") for v in raw)
    if x1 <= x0 or y1 <= y0:
        raise ProbeError(f"矩形不是正面積：{[x0, y0, x1, y1]}")
    return x0, y0, x1, y1


class Edge:
    def __init__(self, kind: str, hole: int | None, index: int, pts):
        self.kind = kind  # outer | hole
        self.hole = hole
        self.index = index
        (self.x0, self.y0), (self.x1, self.y1) = pts
        self.ref = f"e{index}" if hole is None else f"h{hole}e{index}"
        if self.y0 == self.y1 and self.x0 != self.x1:
            self.along = "x"
            self.lo = min(self.x0, self.x1)
            self.hi = max(self.x0, self.x1)
        elif self.x0 == self.x1 and self.y0 != self.y1:
            self.along = "y"
            self.lo = min(self.y0, self.y1)
            self.hi = max(self.y0, self.y1)
        else:
            raise ProbeError(f"邊 {self.ref} 不是軸對齊或退化")

    def material_strip(self, width: int) -> tuple[str, int, int]:
        """回傳 (寬向軸, lo, hi)。外輪廓 CCW 材料在左側；孔 CCW 材料在外側。"""
        dx = self.x1 - self.x0
        dy = self.y1 - self.y0
        flip = -1 if self.hole is not None else 1
        if self.along == "x":
            left_plus = 1 if dx > 0 else -1
            sign = left_plus * flip
            coord = self.y0
            axis = "y"
        else:
            left_plus = -1 if dy > 0 else 1
            sign = left_plus * flip
            coord = self.x0
            axis = "x"
        if sign > 0:
            return axis, coord, coord + width
        return axis, coord - width, coord


def loop_edges(points, kind: str, hole: int | None) -> list[Edge]:
    pts = [(as_int(p[0], "頂點"), as_int(p[1], "頂點")) for p in points]
    if len(pts) < 3:
        raise ProbeError("輪廓少於 3 個頂點")
    return [Edge(kind, hole, i, (pts[i], pts[(i + 1) % len(pts)])) for i in range(len(pts))]


def room_edges(room: dict) -> list[Edge]:
    spec = room["room"]
    edges = loop_edges(spec["outer"], "outer", None)
    for hi, hole in enumerate(spec.get("holes") or []):
        edges.extend(loop_edges(hole, "hole", hi))
    return edges


def axis_interval(rect, axis: str) -> tuple[int, int]:
    if axis == "x":
        return rect[0], rect[2]
    return rect[1], rect[3]


def cover_kind(rect, edge: Edge, along: str) -> str:
    lo, hi = axis_interval(rect, along)
    if lo < edge.lo or hi > edge.hi:
        return "ext"
    if lo == edge.lo and hi == edge.hi:
        return "full"
    return "partial"


def match_edge(rect, edges: list[Edge], width: int):
    """唯一貼邊。沒有則回 None。多於一條直接失敗。"""
    dx = rect[2] - rect[0]
    dy = rect[3] - rect[1]
    hits = []
    for edge in edges:
        strip_axis, slo, shi = edge.material_strip(width)
        if strip_axis == "x":
            if dx != width or (rect[0], rect[2]) != (slo, shi):
                continue
            along = "y"
        else:
            if dy != width or (rect[1], rect[3]) != (slo, shi):
                continue
            along = "x"
        if min(axis_interval(rect, along)[1], edge.hi) <= max(axis_interval(rect, along)[0], edge.lo):
            continue
        hits.append((edge, along, cover_kind(rect, edge, along)))
    if len(hits) > 1:
        refs = ", ".join(hit[0].ref for hit in hits)
        raise ProbeError(f"矩形 {list(rect)} 同時貼到多條邊：{refs}")
    return hits[0] if hits else None


def assign_role(kind: str, where: str | None, cover: str | None):
    """回傳 (role, priority, pending, tier)。孔邊 boundary 不在這裡拍板。"""
    if kind == "main":
        return "primary", None, None, 1
    if kind.startswith("secondary:"):
        return "secondary", None, None, 4
    if kind == "rc_parallel:custom":
        return "custom", 3, None, 3
    if kind == "rc_parallel":
        if where not in ("outer", "hole"):
            raise ProbeError(f"rc_parallel 沒有貼到外輪廓或孔：{where}")
        return "primary", None, None, 1
    if kind == "boundary":
        if where == "hole":
            return "secondary", None, "hole-perpendicular", 4
        if where == "outer":
            return "boundary", None, None, (2 if cover == "ext" else 0)
        raise ProbeError("boundary 沒有貼到外輪廓或孔邊")
    raise ProbeError(f"未知的 oracle 種類：{kind}")


class Member:
    def __init__(self, golden: int, kind: str, rect, hit, role, priority, pending, tier):
        self.golden = golden
        self.kind = kind
        self.rect = rect
        self.role = role
        self.priority = priority
        self.pending = pending
        self.tier = tier
        self.edge = hit[0] if hit else None
        self.along = hit[1] if hit else None
        self.cover = hit[2] if hit else None
        self.id = 0
        self.where = self.edge.kind if self.edge else "interior"
        self.length_axis = None
        self.grid_axis = None
        self.grid_index = None
        self.direction = None
        self.span = None
        self.span_note = None

    def length_bounds(self) -> tuple[int, int]:
        return axis_interval(self.rect, self.length_axis)

    def width_bounds(self) -> tuple[int, int]:
        other = "y" if self.length_axis == "x" else "x"
        return axis_interval(self.rect, other)


def _finish_axes(member: Member, width: int) -> None:
    rect = member.rect
    dx, dy = rect[2] - rect[0], rect[3] - rect[1]
    if member.edge is not None:
        member.length_axis = member.along
    elif dx == width and dy != width:
        member.length_axis = "y"
    elif dy == width and dx != width:
        member.length_axis = "x"
    elif dx == width and dy == width:
        raise ProbeError(f"正方形 {list(rect)} 沒有貼邊，分不出寬向")
    else:
        raise ProbeError(f"矩形沒有一邊等於角材寬 {width}：{list(rect)}")
    if member.edge is not None:
        if member.length_axis == "x":
            member.direction = "+u" if member.edge.x1 > member.edge.x0 else "-u"
        else:
            member.direction = "+v" if member.edge.y1 > member.edge.y0 else "-v"
    else:
        member.direction = "+u" if member.length_axis == "x" else "+v"


def timber_stops(member: Member, others: list[Member], end: str) -> list[Member]:
    lo, hi = member.length_bounds()
    wlo, whi = member.width_bounds()
    target = lo if end == "lo" else hi
    found = []
    for other in others:
        if other is member:
            continue
        olo, ohi = axis_interval(other.rect, member.length_axis)
        owlo, owhi = axis_interval(other.rect, "y" if member.length_axis == "x" else "x")
        if owlo > wlo or owhi < whi:
            continue
        if end == "lo" and ohi == target and olo < target:
            found.append(other)
        elif end == "hi" and olo == target and ohi > target:
            found.append(other)
    return found


def edge_stops(member: Member, edges: list[Edge], end: str) -> list[Edge]:
    lo, hi = member.length_bounds()
    wlo, whi = member.width_bounds()
    target = lo if end == "lo" else hi
    width_axis = "y" if member.length_axis == "x" else "x"
    found = []
    for edge in edges:
        if edge.along != width_axis:
            continue
        coord = edge.x0 if member.length_axis == "x" else edge.y0
        if coord != target:
            continue
        if edge.lo <= wlo and edge.hi >= whi and edge.hi > edge.lo:
            found.append(edge)
    return found


def build_members(kind_rects, edges: list[Edge], width: int) -> list[Member]:
    prepared = []
    for index, (kind, raw) in enumerate(kind_rects):
        rect = rect_of(raw)
        hit = match_edge(rect, edges, width)
        where = hit[0].kind if hit else None
        cover = hit[2] if hit else None
        role, priority, pending, tier = assign_role(kind, where, cover)
        member = Member(index, kind, rect, hit, role, priority, pending, tier)
        _finish_axes(member, width)
        prepared.append(member)
    return prepared


def order_members(members: list[Member], edges: list[Edge]) -> list[int]:
    """擋面依賴的拓撲序。同層 boundary 轉角互頂不建依賴。回傳 golden 序號。"""
    deps: dict[int, set[int]] = {m.golden: set() for m in members}
    by_golden = {m.golden: m for m in members}
    for member in members:
        for end in ("lo", "hi"):
            stops = timber_stops(member, members, end)
            if len(stops) != 1:
                continue
            other = stops[0]
            if member.role == "boundary" and other.role == "boundary" and member.tier == other.tier:
                continue
            deps[member.golden].add(other.golden)
    remaining = set(deps)
    placed: list[int] = []
    forced: list[int] = []
    while remaining:
        ready = [g for g in remaining if deps[g] <= set(placed)]
        if ready:
            pick = min(ready, key=lambda g: (by_golden[g].tier, g))
        else:
            pick = min(remaining, key=lambda g: (by_golden[g].tier, g))
            forced.append(pick)
        remaining.remove(pick)
        placed.append(pick)
    return placed, forced


def _span_for(member: Member, members: list[Member], edges: list[Edge]) -> None:
    refs = []
    fallback = None
    for end in ("lo", "hi"):
        timbers = timber_stops(member, members, end)
        walls = edge_stops(member, edges, end)
        if len(timbers) == 1 and timbers[0].id and timbers[0].id < member.id:
            refs.append(f"t{timbers[0].id}")
        elif len(timbers) == 0 and len(walls) == 1:
            refs.append(walls[0].ref)
        else:
            if len(timbers) == 1 and timbers[0].id > member.id:
                fallback = "擋面角材尚未放置，改用 through"
            elif len(timbers) > 1 or len(walls) > 1:
                fallback = "全寬擋面多於一個，改用 through"
            else:
                fallback = "這一端沒有唯一的全寬擋面，改用 through"
            refs = None
            break
    lo, hi = member.length_bounds()
    if refs is not None and len(refs) == 2:
        member.span = ("between", refs[0], refs[1])
        return
    if hi - lo >= 2:
        coord = lo + (hi - lo) // 2
    else:
        coord = lo
        fallback = (fallback + "；" if fallback else "") + "長度不足 2 mm，沒有整數內點，through 用 lo"
    member.span = ("through", coord)
    member.span_note = fallback


def _grid_for(members: list[Member], width: int) -> dict[str, list[int]]:
    axes: dict[str, set[int]] = {"u": set(), "v": set()}
    for member in members:
        if member.edge is not None:
            continue
        wlo, _whi = member.width_bounds()
        center = wlo + width // 2
        if member.length_axis == "y":
            member.grid_axis = "u"
        else:
            member.grid_axis = "v"
        axes[member.grid_axis].add(center)
        member._center = center
    lines = {axis: sorted(values) for axis, values in axes.items() if values}
    for member in members:
        if member.grid_axis is None:
            continue
        member.grid_index = lines[member.grid_axis].index(member._center)
    return lines


def render_scene(room: str, layout_index: int, name: str, members: list[Member],
                 forced: list[int], edges_src: dict, width: int, lines: dict[str, list[int]]) -> str:
    by_golden = {m.golden: m for m in members}
    ordered = sorted(members, key=lambda m: m.id)
    pending = sum(1 for m in members if m.pending)
    out = []
    out.append(f"# 下角材 oracle 探針：{room}／{name}")
    out.append("# 每支角材的矩形與 oracle-golden.json 相同，不為了讓核心接受而改座標、不縮短延伸段。")
    out.append("# 放置順序依端面的全寬角材擋面，而不是把全部邊界材機械地放在主支之前：")
    out.append("# 1. tier 0 不延伸的外輪廓 boundary。D15 優先級 1；別的料的端面要頂它的側面（I19、R19(d)）。")
    out.append("# 2. tier 1 primary（main，以及未標 custom 的 rc_parallel）。R19(d) 端面頂 boundary 側面，所以 boundary 先在。第一支 primary 定義主支軸（D17、I21）。")
    out.append("# 3. tier 2 有延伸的外輪廓 boundary。延伸端要先有被頂的料（R19(e)、I22）。")
    out.append("# 4. tier 3 custom priority 3。I22 把延伸段側面當優先級 2，同為 2 的 primary 不能頂；D15 要求 custom 明寫 priority。這裡寫 3，與 oracle 標籤及既有探針相同，不是「只能是 3」的裁定。")
    out.append("# 5. tier 4 secondary，含孔邊上種類仍是 boundary、暫寫 secondary 的料。D17 副支在主支軸之後；R19(f) 長度由相鄰主支側面量出。")
    out.append("# 同一階以 golden 原序打破平手。兩支同階 boundary 的轉角互頂不建角材依賴（I19 例外，避免環）。")
    out.append("# 有環就強制取出 tier 最小者，標 probe-cycle，不刪料。被省略的拒絕料會改變後面的擋面，見 run_probe.sh。")
    out.append("# place 不寫長度（D7）。貼邊用 at-face，引用該邊，深度 +n。室內用 at-line，中線 = 寬向 lo + w//2（I13，奇數寬多的 1 mm 在 +cross）。")
    out.append("# 跨距優先 between（兩端都恰有一個全寬擋面，角材側面優先於輪廓或孔邊，R6(d)、R21）。否則 through 取長度開區間內的整數點，不把延伸段縮成固定段。")
    out.append(f"# 截面 A={width} B={SECTION_B}，承載面 z={ORIGIN_Z}。這兩項不在 golden，沿用既有天花場景。孔洞用 surface hole，不另寫 column。")
    if pending:
        out.append("# 孔邊上、golden 種類仍是 boundary 的料暫寫 secondary，probe-member 的 pending 為 hole-perpendicular。這不是裁定，見 mapping.md。")
    meta = {"room": room, "layout": layout_index, "name": name}
    out.append("# probe-meta " + json.dumps(meta, ensure_ascii=False, sort_keys=True, separators=(",", ":")))
    if len(members) > CORE_MAX_TIMBERS:
        out.append(f"# probe-capacity timbers={len(members)} core_max={CORE_MAX_TIMBERS}")
    if forced:
        ids = ",".join(str(by_golden[g].id) for g in forced)
        out.append(f"# probe-cycle {ids}")
    outer = " ".join(f"{as_int(p[0], '頂點')},{as_int(p[1], '頂點')}" for p in edges_src["outer"])
    holes = edges_src.get("holes") or []
    hole_text = ""
    for hole in holes:
        hole_text += " hole " + " ".join(f"{as_int(p[0], '頂點')},{as_int(p[1], '頂點')}" for p in hole)
    out.append(
        f"surface {SURFACE_ID} origin 0 0 {ORIGIN_Z} u +x v +y outline {outer}{hole_text}"
    )
    out.append("")
    if lines:
        parts = []
        for axis in ("u", "v"):
            if axis in lines:
                parts.append(axis + " " + " ".join(str(v) for v in lines[axis]))
        for axis, coords in lines.items():
            if len(coords) > 64:
                out.append(f"# probe-capacity grid_{axis}={len(coords)} core_max_lines=64")
        out.append("# 格線只收 at-line 用到的中線，嚴格遞增。不寫 main-along，避免格線角色預設蓋過 timber 宣告。")
        out.append(f"grid {GRID_ID} on {SURFACE_ID} " + " ".join(parts))
        out.append("")
    for member in ordered:
        payload = {
            "anchor": member.edge.ref if member.edge else f"grid:{member.grid_axis}:{member._center}",
            "cover": member.cover,
            "golden": member.golden,
            "id": member.id,
            "kind": member.kind,
            "pending": member.pending,
            "priority": member.priority,
            "rect": list(member.rect),
            "role": member.role,
            "tier": member.tier,
            "where": member.where,
        }
        out.append("# probe-member " + json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")))
        if member.span_note:
            out.append(f"# probe-span {member.span_note}")
        if member.role == "custom":
            out.append(
                f"timber {member.id} {width} {SECTION_B} role custom priority {member.priority}"
            )
        else:
            out.append(f"timber {member.id} {width} {SECTION_B} role {member.role}")
        if member.edge is not None:
            loc = f"at-face {member.edge.ref}"
        else:
            loc = f"at-line grid {GRID_ID} {member.grid_axis} {member.grid_index}"
        if member.span[0] == "between":
            extra = f" between {member.span[1]} {member.span[2]}"
        else:
            extra = f" through {member.span[1]}"
        out.append(
            f"place {member.id} on {SURFACE_ID} {loc}{extra} {member.direction} +n"
        )
        out.append("")
    return "\n".join(out).rstrip() + "\n"


def _shift_first(golden: dict, delta: int) -> None:
    for room in golden["rooms"].values():
        for layout in room["layouts"]:
            if layout_kept(layout) and layout.get("timbers"):
                kind, rect = layout["timbers"][0]
                layout["timbers"][0] = [kind, [rect[0] + delta, rect[1], rect[2] + delta, rect[3]]]
                return
    raise ProbeError("沒有可施工排法可做座標突變")


class Scene:
    def __init__(self, room, layout, name, filename, text, members, cycles, pending, over_cap):
        self.room = room
        self.layout = layout
        self.name = name
        self.filename = filename
        self.text = text
        self.members = members
        self.cycles = cycles
        self.pending = pending
        self.over_cap = over_cap


class Build:
    def __init__(self, scenes: list[Scene], skipped: list[dict]):
        self.scenes = scenes
        self.skipped = skipped


def build(golden: dict, delta: int | None = None) -> Build:
    data = copy.deepcopy(golden)
    if delta:
        _shift_first(data, delta)
    base = data["params"]
    scenes: list[Scene] = []
    skipped: list[dict] = []
    seen = set()
    for room_name, room in data["rooms"].items():
        slug = slug_for(room_name)
        if slug in seen:
            raise ProbeError(f"房間檔名衝突：{slug}")
        seen.add(slug)
        params = dict(base)
        params.update((room.get("room") or {}).get("params") or {})
        width = as_int(params["w"], "角材寬 w")
        edges = room_edges(room)
        for index, layout in enumerate(room["layouts"]):
            if not layout_kept(layout):
                skipped.append({
                    "room": room_name,
                    "layout": index,
                    "name": layout.get("name") or "",
                    "buildable": bool(layout.get("buildable")),
                    "conflict_codes": list(layout.get("conflict_codes") or []),
                })
                continue
            members = build_members(layout["timbers"], edges, width)
            placed, forced = order_members(members, edges)
            for order, golden_index in enumerate(placed, start=1):
                next(m for m in members if m.golden == golden_index).id = order
            for member in members:
                _span_for(member, members, edges)
            lines = _grid_for(members, width)
            text = render_scene(
                room_name, index, layout.get("name") or "", members, forced,
                room["room"], width, lines,
            )
            scenes.append(Scene(
                room=room_name,
                layout=index,
                name=layout.get("name") or "",
                filename=f"{slug}-{index:02d}.scene",
                text=text,
                members=members,
                cycles=len(forced),
                pending=sum(1 for m in members if m.pending),
                over_cap=len(members) > CORE_MAX_TIMBERS,
            ))
    return Build(scenes, skipped)


def index_document(built: Build, golden_name: str) -> dict:
    return {
        "golden": golden_name,
        "buildable_count": len(built.scenes),
        "scene_count": len(built.scenes),
        "skipped": built.skipped,
        "scenes": [
            {
                "file": scene.filename,
                "room": scene.room,
                "layout": scene.layout,
                "name": scene.name,
                "timbers": len(scene.members),
                "pending": scene.pending,
                "cycles": scene.cycles,
                "over_core_cap": scene.over_cap,
            }
            for scene in built.scenes
        ],
    }


def write_build(built: Build, out_dir: Path, index_path: Path, golden_name: str) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    keep = {scene.filename for scene in built.scenes}
    for old in out_dir.glob("*.scene"):
        if old.name not in keep:
            old.unlink()
    for scene in built.scenes:
        (out_dir / scene.filename).write_text(scene.text, encoding="utf-8", newline="\n")
    payload = json.dumps(index_document(built, golden_name), ensure_ascii=False, indent=2) + "\n"
    index_path.write_text(payload, encoding="utf-8", newline="\n")


def assert_member_rects(golden: dict, built: Build) -> None:
    """註解 rect 與 golden 逐支相等。不符時列出房間、排法、編號、種類與兩個矩形。"""
    lines = []
    by_key = {(scene.room, scene.layout): scene for scene in built.scenes}
    for room_name, room in golden["rooms"].items():
        for index, layout in enumerate(room["layouts"]):
            if not layout_kept(layout):
                continue
            scene = by_key.get((room_name, index))
            expected = [(kind, rect_of(raw)) for kind, raw in layout["timbers"]]
            if scene is None:
                lines.append(f"{room_name} / {layout.get('name') or ''} / 場景缺失 / 共 {len(expected)} 支")
                continue
            got = {}
            for member in scene.members:
                got[member.golden] = (member.kind, tuple(member.rect))
            if len(scene.members) != len(expected) or set(got) != set(range(len(expected))):
                lines.append(
                    f"{room_name} / {scene.name} / 支數 oracle {len(expected)} scene {len(scene.members)}"
                )
            for number, (kind, rect) in enumerate(expected):
                have = got.get(number)
                if have is None:
                    lines.append(
                        f"{room_name} / {layout.get('name') or ''} / 編號 {number} / {kind}"
                        f" / oracle {list(rect)} / scene 缺失"
                    )
                elif have != (kind, rect):
                    lines.append(
                        f"{room_name} / {layout.get('name') or ''} / 編號 {number} / {kind}"
                        f" / oracle {list(rect)} / scene {list(have[1])}"
                    )
    if lines:
        raise AssertionError("\n".join(lines + [f"共 {len(lines)} 支不符"]))


def _pts(text: str) -> list[tuple[int, int]]:
    pts = []
    for token in text.split():
        if "," not in token:
            raise AssertionError(f"頂點不是 u,v：{token}")
        u, v = token.split(",", 1)
        pts.append((int(u), int(v)))
    return pts


def parse_surface(line: str):
    if " outline " not in line:
        raise AssertionError("場景沒有 outline")
    tail = line.split(" outline ", 1)[1]
    parts = tail.split(" hole ")
    holes = [_pts(part) for part in parts[1:]]
    return _pts(parts[0]), holes


def parse_grid(line: str) -> dict[str, list[int]]:
    tokens = line.split()
    if tokens[:4] != ["grid", "1", "on", "1"]:
        raise AssertionError(f"格線宣告不符：{line}")
    axes: dict[str, list[int]] = {}
    index = 4
    while index < len(tokens):
        axis = tokens[index]
        if axis not in ("u", "v"):
            raise AssertionError(f"格線軸不符：{line}")
        index += 1
        coords = []
        while index < len(tokens) and tokens[index] not in ("u", "v"):
            coords.append(int(tokens[index]))
            index += 1
        if axis in axes or not coords:
            raise AssertionError(f"格線軸重複或是空的：{line}")
        axes[axis] = coords
    return axes


def parse_place(line: str) -> dict:
    tokens = line.split()
    if len(tokens) < 8 or tokens[0] != "place" or tokens[2] != "on" or not tokens[4].startswith("at-"):
        raise AssertionError(f"place 讀不懂：{line}")
    body = tokens[5:-2]
    span = None
    if "through" in body:
        at = body.index("through")
        span = ("through", int(body[at + 1]))
        body = body[:at]
    elif "between" in body:
        at = body.index("between")
        span = ("between", body[at + 1], body[at + 2])
        body = body[:at]
    return {
        "id": int(tokens[1]),
        "on": int(tokens[3]),
        "kind": tokens[4][3:],
        "body": body,
        "direction": tokens[-2],
        "side": tokens[-1],
        "span": span,
    }


def audit_scene(text: str) -> None:
    """place、格線與註解 rect 必須由同一支矩形推出，且沒有把寬度改掉。"""
    surface = None
    grid = {}
    pending = None
    seen = []
    for line in text.splitlines():
        if line.startswith("surface "):
            surface = parse_surface(line)
        elif line.startswith("grid "):
            grid = parse_grid(line)
        elif line.startswith("# probe-member "):
            if pending is not None:
                raise AssertionError("上一支角材沒有 place")
            pending = json.loads(line[len("# probe-member "):])
        elif line.startswith("timber ") and pending is not None:
            tokens = line.split()
            pending["_timber"] = tokens
        elif line.startswith("place ") and pending is not None:
            pending["_place"] = parse_place(line)
            seen.append(pending)
            pending = None
    if pending is not None:
        raise AssertionError("最後一支角材沒有 place")
    if surface is None:
        raise AssertionError("場景沒有承載面")
    edges = loop_edges(surface[0], "outer", None)
    for hole_index, hole in enumerate(surface[1]):
        edges.extend(loop_edges(hole, "hole", hole_index))
    for member in seen:
        rect = tuple(member["rect"])
        width_x = rect[2] - rect[0]
        width_y = rect[3] - rect[1]
        place = member["_place"]
        timber = member["_timber"]
        if int(timber[1]) != member["id"] or place["id"] != member["id"] or place["on"] != 1 or place["side"] != "+n":
            raise AssertionError(f"place 與註解不一致：{member['id']}")
        role = timber[5]
        if role != member["role"]:
            raise AssertionError(f"角色與註解不一致：{member['id']}")
        if member["role"] == "custom":
            if timber[6:] != ["priority", str(member["priority"])]:
                raise AssertionError(f"custom priority 與註解不一致：{member['id']}")
        section = int(timber[2])
        if place["kind"] == "line":
            axis = place["body"][2]
            index = int(place["body"][3])
            center = grid[axis][index]
            if axis == "u":
                lo, hi = rect[0], rect[2]
                if width_x != section:
                    raise AssertionError(f"at-line 寬向不是截面：{member['id']}")
            else:
                lo, hi = rect[1], rect[3]
                if width_y != section:
                    raise AssertionError(f"at-line 寬向不是截面：{member['id']}")
            half = section // 2
            if center != lo + half or (center - half, center - half + section) != (lo, hi):
                raise AssertionError(f"at-line 中線與矩形不合：{member['id']} grid {center} rect {list(rect)}")
            expect_dir = "+v" if axis == "u" else "+u"
            if place["direction"] != expect_dir:
                raise AssertionError(f"at-line 方向與寬向不合：{member['id']}")
            length = (rect[1], rect[3]) if axis == "u" else (rect[0], rect[2])
        else:
            ref = place["body"][0]
            edge = next(item for item in edges if item.ref == ref)
            strip_axis, slo, shi = edge.material_strip(section)
            have = (rect[0], rect[2]) if strip_axis == "x" else (rect[1], rect[3])
            if have != (slo, shi) or shi - slo != section:
                raise AssertionError(f"at-face 沒有貼在 {ref} 的材料側：{member['id']} {list(rect)}")
            length = (rect[1], rect[3]) if strip_axis == "x" else (rect[0], rect[2])
            expect_dir = ("+u" if edge.x1 > edge.x0 else "-u") if edge.along == "x" else ("+v" if edge.y1 > edge.y0 else "-v")
            if place["direction"] != expect_dir:
                raise AssertionError(f"at-face 方向沒有跟著邊 {ref}：{member['id']}")
        if place["span"] and place["span"][0] == "through":
            coord = place["span"][1]
            if coord < length[0] or coord > length[1]:
                raise AssertionError(f"through {coord} 不在長度閉區間 {length}：{member['id']}")


def load_golden(path: Path | None = None) -> dict:
    src = path or DEFAULT_GOLDEN
    return json.loads(src.read_text(encoding="utf-8"))


def main() -> None:
    parser = argparse.ArgumentParser(description="由 oracle-golden.json 產生核心探針場景")
    parser.add_argument("--golden", type=Path, default=DEFAULT_GOLDEN)
    parser.add_argument("--out", type=Path, default=HERE / "scenes")
    parser.add_argument("--index", type=Path, default=HERE / "index.json")
    parser.add_argument("--delta", type=int, default=None)
    args = parser.parse_args()
    golden = load_golden(args.golden)
    built = build(golden, delta=args.delta)
    write_build(built, args.out, args.index, args.golden.name)
    if built.skipped:
        print("跳過：")
        for row in built.skipped:
            print(f"  {row['room']} / {row['name']} / {row['conflict_codes']}")
    else:
        print("跳過：（無）")
    print(f"場景 {len(built.scenes)}")


if __name__ == "__main__":
    main()
