"""Explicit face declarations and D21/D22 previews, evaluated by the model engine.

This module never touches the running bridge world. Generated placements are
independent declarations, not an invented live projection-to-space relation.
"""
from __future__ import annotations

from copy import deepcopy
from functools import lru_cache
import hashlib
from pathlib import Path
import re
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "geometry-core"))
from modeling import ModelError, build_package, canonical_bytes, verify_package
from modeling.base import load_base

LIMIT = 100_000_000
MAX_FACES = 16  # Authoritative C World boundary and placement capacities.
MAX_SPECS = 64


def _fail(code, message, *, path=(), status="INVALID", clause="D24"):
    raise ModelError(status, code, clause, message, path=list(path))


def _keys(value, required, optional=(), path=()):
    if type(value) is not dict:
        _fail("SPACE_INPUT", "請提供完整的建空間設定。", path=path)
    missing = set(required) - value.keys()
    extra = value.keys() - set(required) - set(optional)
    if missing:
        _fail("SPACE_MISSING_FIELD", "尚未設定：" + sorted(missing)[0], path=path)
    if extra:
        _fail("SPACE_UNKNOWN_FIELD", "不支援的設定：" + sorted(extra)[0], path=path)


def _integer(value, name, low=-LIMIT, high=LIMIT):
    if type(value) is not int or not low <= value <= high:
        _fail("SPACE_INPUT_RANGE", f"{name}必須是 {low} 至 {high} 的整數。", path=[name], clause="D1")
    return value


def _uid(value, name):
    return _integer(value, name, 0, 0xFFFFFFFF)


def _area2(points):
    return sum(a[0] * b[1] - b[0] * a[1]
               for a, b in zip(points, points[1:] + points[:1]))


def _world_loop(placement, loop):
    o, u, v = placement["origin"], placement["u"], placement["v"]
    return [[o[i] + p[0] * u[i] + p[1] * v[i] for i in range(2)] for p in loop]


def _axis(vector):
    for i, value in enumerate(vector):
        if value:
            return ("+" if value > 0 else "-") + "xyz"[i]
    raise AssertionError("validated edge cannot be zero length")


def _loop_text(points):
    return " ".join(f"{x},{y}" for x, y in points)


def _convex_corners(outline, edges):
    """Exactly the selected outer joins that require material carriers."""
    sign = 1 if _area2(outline) > 0 else -1
    for index, point in enumerate(outline):
        previous = (index - 1) % len(outline)
        if previous not in edges or index not in edges:
            continue
        a, c = outline[previous], outline[(index + 1) % len(outline)]
        turn = ((point[0] - a[0]) * (c[1] - point[1])
                - (point[1] - a[1]) * (c[0] - point[0]))
        if turn * sign > 0:
            yield index


class Declarations:
    """Allocate unused ids and check known storage bounds before generating DSL."""
    def __init__(self, base):
        self.scene = base["base_scene"]
        self.lines = []
        self.ids = set()
        self.boundaries, self.placements = set(), set()
        for line in self.scene.splitlines():
            tokens = line.split()
            if len(tokens) > 1 and re.fullmatch(r"[0-9]+", tokens[1]):
                value = int(tokens[1])
                self.ids.add(value)
                if tokens[0] in ("surface", "boundary"):
                    self.boundaries.add(value)
                if tokens[0] in ("surface", "placement"):
                    self.placements.add(value)
        self.specs = {s["name"] for s in base["specs"]}

    def check_plan_capacity(self, shell_faces, material_faces, material_requested):
        # Both namespaces count independently: unused boundaries and multiple
        # placements of one boundary consume different native capacities.
        faces = shell_faces + material_faces
        boundaries = len(self.boundaries) + faces
        placements = len(self.placements) + faces
        specs = len(self.specs) + (3 if material_requested else 0)
        if boundaries <= MAX_FACES and placements <= MAX_FACES and specs <= MAX_SPECS:
            return
        requirement = "含材料牆的建模要求" if material_requested else "空間邊界要求"
        detail = (f"邊界面需 {boundaries}/{MAX_FACES}，承載面需 {placements}/{MAX_FACES}"
                  f"（新增空間 {shell_faces} 面、材料載體 {material_faces} 面）")
        if material_requested:
            detail += f"，具名規格需 {specs}/{MAX_SPECS}"
        action = "請減少來源場景或選邊。"
        if material_requested:
            action += "若只需要空間邊界，請明確取消「同時建立有厚度的牆」後重新預覽。"
        _fail("SPACE_CAPACITY", f"{requirement}超過本版容量：{detail}。{action}",
              status="UNSUPPORTED", clause="I33",
              path=["settings", "wall_thickness"] if material_requested else ["settings"])

    def identifier(self):
        # Bounded world size means this search is small, even with UINT32_MAX ids.
        value = 1
        while value in self.ids:
            value += 1
        if value > 0xFFFFFFFF:
            _fail("SPACE_CAPACITY", "沒有可用的物件編號。", status="UNSUPPORTED", clause="I33")
        self.ids.add(value)
        return value

    def face(self, outline, origin, u="+x", v="+y", holes=()):
        if len(self.boundaries) >= MAX_FACES or len(self.placements) >= MAX_FACES:
            _fail("SPACE_CAPACITY", "本版最多保存 16 個邊界面與 16 個承載面；新增面會超過容量。請減少選邊或改用較小的來源場景。", status="UNSUPPORTED", clause="I33")
        for p in [origin, *outline, *(p for loop in holes for p in loop)]:
            for coordinate in p:
                _integer(coordinate, "新面的座標")
        identifier = self.identifier()
        boundary = f"boundary {identifier} outline {_loop_text(outline)}"
        boundary += "".join(" hole " + _loop_text(loop) for loop in holes)
        if len(boundary.encode("utf-8")) >= 2046 or len(boundary.split()) > 160:
            _fail("SPACE_CAPACITY", "新面的輪廓超過場景單行容量。", status="UNSUPPORTED", clause="I33")
        self.lines.extend([boundary,
            f"placement {identifier} on boundary {identifier} origin {' '.join(map(str, origin))} u {u} v {v}"])
        self.boundaries.add(identifier)
        self.placements.add(identifier)
        return identifier

    def spec(self, label, value):
        _integer(value, label)
        if len(self.specs) >= MAX_SPECS:
            _fail("SPACE_CAPACITY", "材料牆需要具名厚度與高度規格，但場景已達 64 個規格的容量。", status="UNSUPPORTED", clause="I33")
        name = "space_" + label
        suffix = 1
        while name in self.specs:
            suffix += 1
            name = f"space_{label}_{suffix}"
        self.specs.add(name)
        self.lines.append(f"spec {name} {value}")
        return name

    def text(self):
        return self.scene.rstrip("\n") + "\n" + "\n".join(self.lines) + ("\n" if self.lines else "")


def _package(definitions, root, role, target, options):
    request = {"roots": [root], "role": role, "target": target, "allow_partial": False}
    package = build_package(definitions, request, **options)
    # Deliver only exchange packages that reconstruct from their actual definitions.
    return verify_package(package, **options)


def _volume(package):
    if package is None:
        return None
    values = [item["volume_mm3"] for item in package["derived"]["objects"]]
    return str(sum(int(value) for value in values)) if all(v is not None for v in values) else None


def _obstacles(value, base):
    if type(value) is not list:
        _fail("SPACE_OBSTACLES", "請明選柱樑障礙物；没有障礙物請傳空清單。")
    available = {(s["kind"], s["id"]) for s in base["solids"]}
    result, seen = [], set()
    for obstacle in value:
        _keys(obstacle, ("kind", "id"), path=["obstacles"])
        if type(obstacle["kind"]) is not str or obstacle["kind"] not in ("column", "beam"):
            _fail("SPACE_OBSTACLES", "第一版障礙物只接受已定義的柱或樑。", clause="D22")
        key = (obstacle["kind"], _uid(obstacle["id"], "障礙物編號"))
        if key not in available:
            _fail("SPACE_OBSTACLES", "選取的柱樑没有可求值的 3D 定義；平面投影不能自動當作實體。", clause="D22")
        if key in seen:
            _fail("SPACE_OBSTACLES", "同一障礙物不可重複選取。", clause="I29")
        seen.add(key)
        result.append(deepcopy(obstacle))
    return result


def _timbers(value, base, placement_id, options):
    """Explicit material roots; support dependencies remain in the source scene."""
    if type(value) is not list or not value:
        _fail("SPACE_TIMBERS", "納入角材時請明選非空角材清單；不納入時請省略 timbers 欄位。", path=["timbers"])
    available = {s["id"]: s for s in base["solids"] if s["kind"] == "timber"}
    roots, seen = [], set()
    for index, ref in enumerate(value):
        path = ["timbers", index]
        _keys(ref, ("kind", "id"), path=path)
        identifier = ref["id"]
        if ref["kind"] != "timber" or type(identifier) is not int or not 0 <= identifier <= 0xFFFFFFFF:
            _fail("SPACE_TIMBERS", "角材引用須為 kind=timber 及合法整數編號（包含 0）。", path=path)
        if identifier in seen:
            _fail("SPACE_TIMBERS", f"角材 #{identifier} 重複選取。", path=path)
        solid = available.get(identifier)
        if solid is None:
            _fail("SPACE_TIMBERS", f"角材 #{identifier} 不存在或尚未完成放置。", path=path, clause="D7")
        if solid.get("placement_id") != placement_id:
            _fail("SPACE_TIMBERS", f"角材 #{identifier} 不屬於來源放置面 #{placement_id}。", path=path, clause="D4")
        roots.append({"kind": "timber", "id": identifier})
        seen.add(identifier)
    roots.sort(key=lambda ref: ref["id"])
    definitions = {"base_scene": base["base_scene"], "extensions": []}
    request = {"roots": roots, "role": "geometry", "target": "solid-set", "allow_partial": False}
    labels = "、".join(f"#{ref['id']}" for ref in roots)
    try:
        package = verify_package(build_package(definitions, request, **options), **options)
        objects = package["derived"]["objects"]
        actual = [obj["root"] for obj in objects]
        if (package["definitions"] != definitions or package["request"] != request or
                package["derived"]["status"] != "COMPLETE" or len(objects) != len(roots) or
                sorted(actual, key=lambda ref: ref["id"]) != roots or
                any(obj["status"] != "COMPLETE" or obj["role"] != "geometry" or
                    obj["closure"] != "closed" or obj["volume_mm3"] is None or
                    int(obj["volume_mm3"]) <= 0 for obj in objects)):
            _fail("SPACE_TIMBERS_INCOMPLETE", "指定角材沒有全部產生完整、封閉且可追溯的實體。", path=["timbers"])
        return package
    except ModelError as exc:
        # Selected material is mandatory: never silently return a partial model.
        message = f"角材 {labels} 無法完整建模：{exc.message}"
        diagnostics = deepcopy(exc.diagnostics or [exc.diagnostic()])
        for diagnostic in diagnostics:
            diagnostic["message"] = f"角材 {labels}：{diagnostic.get('message', exc.message)}"
        raise ModelError(exc.status, exc.code, exc.clause, message,
                         path=["timbers", *exc.path], root=exc.root,
                         missing=exc.missing, diagnostics=diagnostics) from exc


def _plan(data, base, declarations, *, historical_walls=False):
    _keys(data, ("base_scene", "mode", "placement_id", "settings", "obstacles"), ("timbers",))
    selected = _uid(data["placement_id"], "來源面編號")
    source = next((p for p in base["placements"] if p["id"] == selected), None)
    if source is None:
        _fail("SPACE_SOURCE", "來源面尚未放到三維位置，或已不存在。", clause="D4")
    if source["n"][:2] != [0, 0] or abs(source["n"][2]) != 1:
        _fail("SPACE_SOURCE_PLANE", "沿輪廓建立空間目前需要水平面（法向量為 +Z 或 -Z）。", clause="D4")
    settings = data["settings"]
    _keys(settings, ("bottom", "height", "edges", "floor", "ceiling", "holes", "wall_thickness"), path=["settings"])
    bottom = _integer(settings["bottom"], "底高")
    height = _integer(settings["height"], "高度", 1)
    top = _integer(bottom + height, "頂高")
    for cap in ("floor", "ceiling"):
        if type(settings[cap]) is not str or settings[cap] not in ("none", "boundary", "calculation-cap"):
            _fail("SPACE_CAP_PURPOSE", "請明選頂底面：不建立、邊界面或計算封口。", path=["settings", cap], clause="D21")
    if type(settings["holes"]) is not str or settings["holes"] not in ("none", "through"):
        _fail("SPACE_HOLE_PURPOSE", "請明選孔洞用途：無孔洞或沿高度貫通。", clause="D21")
    if source["holes"] and settings["holes"] != "through":
        _fail("SPACE_HOLE_PURPOSE", "來源含孔洞。請明選「孔洞沿高度貫通」才會建立孔內側面；不能猜測它是柱、門窗或樓板孔。", clause="D21")
    thickness = settings["wall_thickness"]
    if thickness is not None:
        _integer(thickness, "牆厚", 1)
    outline = _world_loop(source, source["outline"])
    holes = [_world_loop(source, loop) for loop in source["holes"]]
    edges = settings["edges"]
    if type(edges) is not list or not edges or any(type(e) is not int or not 0 <= e < len(outline) for e in edges):
        _fail("SPACE_EDGES", "請至少選取一條有效的外環邊。", path=["settings", "edges"])
    if len(set(edges)) != len(edges):
        _fail("SPACE_EDGES", "同一外環邊不可重複選取。")
    shell_faces = (len(edges) + sum(len(loop) for loop in holes)
                   + sum(settings[cap] != "none" for cap in ("floor", "ceiling")))
    # The current material algorithm keeps every corner carrier plus one outer
    # interior clipping carrier in its reconstructible definitions. Preflight
    # its actual allocation plan, before generating or evaluating packages.
    material_faces = (sum(1 for _ in _convex_corners(outline, edges)) + 1
                      if thickness is not None else 0)
    if not historical_walls:
        declarations.check_plan_capacity(shell_faces, material_faces, thickness is not None)
    uses, generated, sides, missing = [], [], {}, []

    def add_use(identifier, label, orientation=1, purpose="boundary"):
        use = {"placement_id": identifier, "orientation": orientation, "purpose": purpose}
        uses.append(use)
        generated.append({**use, "label": label})

    for loop_index, loop in enumerate([outline, *holes]):
        sign = (1 if _area2(loop) > 0 else -1) * (1 if loop_index == 0 else -1)
        for index, (a, b) in enumerate(zip(loop, loop[1:] + loop[:1])):
            if loop_index == 0 and index not in edges:
                missing.append(f"未建立外環第 {index + 1} 邊")
                continue
            start, end = (a, b) if sign > 0 else (b, a)
            length = abs(end[0] - start[0]) + abs(end[1] - start[1])
            direction = [(end[i] - start[i]) // length for i in range(2)]
            identifier = declarations.face([[0, 0], [length, 0], [length, height], [0, height]],
                [*start, bottom], _axis([*direction, 0]), "+z")
            label = f"外環第 {index + 1} 邊" if loop_index == 0 else f"孔洞 {loop_index} 第 {index + 1} 邊"
            add_use(identifier, label)
            if loop_index == 0:
                sides[index] = {"placement_id": identifier, "normal": [direction[1], -direction[0]]}
    for cap, z, direction, label in (("floor", bottom, -1, "底面"), ("ceiling", top, 1, "頂面")):
        if settings[cap] != "none":
            identifier = declarations.face(outline, [0, 0, z], holes=holes)
            add_use(identifier, label, direction, settings[cap])
        else:
            missing.append("未建立" + label)
    summary = {"source_placement": selected, "source_z": source["origin"][2],
               "bottom": bottom, "top": top, "generated_faces": generated, "missing": missing}
    return uses, summary, {"outline": outline, "sides": sides, "bottom": bottom,
                            "height": height, "thickness": thickness}


def _faces(data, base):
    _keys(data, ("base_scene", "mode", "uses", "obstacles"))
    if type(data["uses"]) is not list or not data["uses"]:
        _fail("SPACE_FACES", "請至少選取一個已有面，並設定朝向與用途。", clause="D21")
    available = {p["id"] for p in base["placements"]}
    uses, seen = [], set()
    for use in data["uses"]:
        _keys(use, ("placement_id", "orientation", "purpose"), path=["uses"])
        identifier = _uid(use["placement_id"], "面編號")
        if identifier not in available or identifier in seen:
            _fail("SPACE_FACES", "面必須已放置，且每個面只選取一次。", clause="D21")
        if type(use["orientation"]) is not int or use["orientation"] not in (-1, 1):
            _fail("SPACE_FACES", "請明選每個面的朝向 +1 或 -1。", clause="D21")
        if type(use["purpose"]) is not str or use["purpose"] not in ("boundary", "calculation-cap"):
            _fail("SPACE_FACES", "請明選每個面的用途：邊界面或計算封口。", clause="D21")
        uses.append(deepcopy(use))
        seen.add(identifier)
    return uses, {"source_placement": None, "source_z": None, "bottom": None, "top": None,
                  "generated_faces": [], "missing": []}, None


def _walls(declarations, wall, options):
    """Outward D20 strips + explicit square corners, UNION minus full interior."""
    thickness = wall["thickness"]
    if thickness is None:
        return None
    outline, sides = wall["outline"], wall["sides"]
    near = declarations.spec("near", 0)
    far = declarations.spec("wall_thickness", thickness)
    height_spec = declarations.spec("height", wall["height"])
    extensions, inputs = [], []

    def extrude(placement, hi, include=True):
        identifier = declarations.identifier()
        extensions.append({"kind": "extrusion", "id": identifier, "placement_id": placement,
                           "lo_spec": near, "hi_spec": hi})
        ref = {"kind": "extrusion", "id": identifier}
        if include:
            inputs.append(ref)
        return ref

    for index in sorted(sides):
        extrude(sides[index]["placement_id"], far)
    for index in _convex_corners(outline, sides):
        point = outline[index]
        previous = (index - 1) % len(outline)
        n1, n2 = sides[previous]["normal"], sides[index]["normal"]
        corners = [point, [point[i] + n1[i] * thickness for i in range(2)],
                   [point[i] + (n1[i] + n2[i]) * thickness for i in range(2)],
                   [point[i] + n2[i] * thickness for i in range(2)]]
        low = [min(p[i] for p in corners) for i in range(2)]
        high = [max(p[i] for p in corners) for i in range(2)]
        rectangle = [low, [high[0], low[1]], high, [low[0], high[1]]]
        carrier = declarations.face(rectangle, [0, 0, wall["bottom"]])
        extrude(carrier, height_spec)
    # No room-hole material is added: the clipping tool is the full outer interior.
    interior = declarations.face(outline, [0, 0, wall["bottom"]])
    tool = extrude(interior, height_spec, False)
    union = inputs[0]
    if len(inputs) > 1:
        union = {"kind": "composition", "id": declarations.identifier()}
        extensions.append({**union, "op": "UNION", "inputs": inputs})
    root = {"kind": "composition", "id": declarations.identifier()}
    extensions.append({**root, "op": "DIFFERENCE", "base": union, "tools": [tool]})
    return _package({"base_scene": declarations.text(), "extensions": extensions},
                    root, "geometry", "solid-set", options)


def preview(data, *, base_executable=None, max_cells=200000):
    """Build an isolated candidate; never mutate input data or the user's world."""
    return _preview(data, base_executable=base_executable, max_cells=max_cells)


def replay_stored(data, expected, *, base_executable=None, max_cells=200000):
    """Verify an existing result, including the original optional-wall contract.

    History replay is never a generation candidate. A missing material package
    must reproduce the saved semantics, including its original diagnostics;
    no package, setting, or summary is trusted merely because walls is null.
    The caller must retain the saved input/result rather than replacing it.
    """
    canonical_bytes(expected)
    settings = data.get("settings") if type(data) is dict else None
    summary = expected.get("summary") if type(expected) is dict else None
    historical_walls = (type(settings) is dict and settings.get("wall_thickness") is not None
                        and type(expected) is dict and expected.get("walls") is None
                        and type(summary) is dict and bool(summary.get("wall_diagnostics")))
    rebuilt = _preview(data, base_executable=base_executable, max_cells=max_cells,
                       historical_walls=historical_walls)
    if type(expected) is not dict:
        _fail("SPACE_STORED_REPLAY", "保存的空間結果必須為完整記錄。", path=["result"], clause="I31")
    saved_semantics, rebuilt_semantics = deepcopy(expected), deepcopy(rebuilt)
    for key in ("space", "volume", "clearance", "walls", "timbers"):
        package = expected.get(key)
        if package is not None:
            # Keep the existing exchange-package version/provenance contract.
            # verify_package validates all metadata/digests and actual native
            # geometry, while allowing enumerated legacy revisions/generators.
            verify_package(package, base_executable=base_executable, max_cells=max_cells)
            saved_semantics[key] = {field: package[field] for field in ("definitions", "request", "derived")}
        if rebuilt.get(key) is not None:
            rebuilt_semantics[key] = {field: rebuilt[key][field] for field in ("definitions", "request", "derived")}
    if canonical_bytes(rebuilt_semantics) != canonical_bytes(saved_semantics):
        _fail("SPACE_STORED_REPLAY", "保存的模型、設定、幾何或診斷與歷史重播不一致。",
              path=["result"], clause="I31")
    # Reading history must not replace valid archival provenance with today's.
    return deepcopy(expected)


def _preview(data, *, base_executable=None, max_cells=200000, historical_walls=False):
    canonical_bytes(data)
    if type(data) is not dict or data.get("mode") not in ("plan", "faces"):
        _fail("SPACE_MODE", "請選擇沿平面輪廓建立，或組合已有面。")
    if type(data.get("base_scene")) is not str:
        _fail("SPACE_SOURCE", "缺少來源場景。")
    base = load_base(data["base_scene"], executable=base_executable)
    declarations = Declarations(base)
    if data["mode"] == "plan":
        uses, summary, wall = _plan(data, base, declarations, historical_walls=historical_walls)
    else:
        uses, summary, wall = _faces(data, base)
    obstacles = _obstacles(data["obstacles"], base)
    shell_id, space_id = declarations.identifier(), declarations.identifier()
    root = {"kind": "composite_space", "id": space_id}
    definitions = {"base_scene": declarations.text(), "extensions": [
        {"kind": "shell", "id": shell_id, "uses": uses},
        {**root, "shell_id": shell_id, "obstacles": obstacles}]}
    options = {"base_executable": base_executable, "max_cells": max_cells}
    timbers = _timbers(data["timbers"], base, data["placement_id"], options) if "timbers" in data else None
    space = _package(definitions, root, "enclosure", "surface-set", options)
    volume = clearance = None
    diagnostics = []
    try:
        volume = _package(definitions, root, "enclosure", "solid-set", options)
        clearance = _package(definitions, root, "clearance", "solid-set", options)
    except ModelError as exc:
        if exc.status != "INCOMPLETE":
            raise
        diagnostics.extend(exc.diagnostics or [exc.diagnostic()])
        if not summary["missing"]:
            summary["missing"].append("邊界仍有開口，尚不能確定空間體積與淨空。")
    walls, wall_diagnostics = None, []
    if wall and wall["thickness"] is not None:
        try:
            walls = _walls(deepcopy(declarations), wall, options)
        except ModelError as exc:
            if historical_walls:
                # Reproduce old definitions and the actual old failure. The
                # complete expected result is compared by replay_stored.
                wall_diagnostics.extend(exc.diagnostics or [exc.diagnostic()])
            else:
                # Like explicitly selected timbers, selected walls are mandatory.
                # I31 forbids downgrading UNSUPPORTED/INVALID into partial success.
                diagnostics = deepcopy(exc.diagnostics or [exc.diagnostic()])
                for diagnostic in diagnostics:
                    diagnostic["message"] = "材料牆無法完整建模：" + diagnostic.get("message", exc.message)
                raise ModelError(exc.status, exc.code, exc.clause,
                                 "材料牆無法完整建模：" + exc.message,
                                 path=["settings", "wall_thickness", *exc.path], root=exc.root,
                                 missing=exc.missing, diagnostics=diagnostics) from exc
    summary.update({"face_count": len(uses), "closed": volume is not None,
                    "volume_mm3": _volume(volume), "clearance_mm3": _volume(clearance),
                    "wall_volume_mm3": _volume(walls), "wall_diagnostics": wall_diagnostics})
    result = {"ok": True, "schema": "geometry-space-preview/1", "space": space,
              "volume": volume, "clearance": clearance, "walls": walls,
              "summary": summary, "diagnostics": diagnostics,
              "source_sha256": hashlib.sha256(base["base_scene"].encode("utf-8")).hexdigest()}
    if timbers is not None:
        result.update(schema="geometry-space-preview/2", timbers=timbers)
        summary.update(timber_count=len(data["timbers"]), timber_volume_mm3=_volume(timbers))
    return result


@lru_cache(maxsize=1)
def _timber_frame_example():
    """Fixed declarations; candidate dimensions come from validated C geometry."""
    outline = [[0, 0], [4000, 0], [4000, 3000], [0, 3000]]
    scene = (f"boundary 1 outline {_loop_text(outline)} kind room_plan\n"
             "placement 1 on boundary 1 origin 0 0 2500 u +x v +y\n")
    roles = {10: "boundary", 11: "boundary", 12: "primary", 13: "primary",
             20: "primary", 30: "secondary", 31: "secondary"}
    for identifier, edge, direction in ((10, 0, "+u"), (11, 2, "+u"), (12, 1, "+v"), (13, 3, "+v")):
        scene += (f"timber {identifier} 27 33 role {roles[identifier]}\n"
                  f"place {identifier} on 1 at-face e{edge} {direction} +n\n")
    scene += ("spec main_x 2000\nguide 1 1 v spec:main_x\n"
              "timber 20 27 33 role primary\nplace 20 on 1 at-line guide 1 +v +n\n"
              "spec cross_y 1500\nguide 2 1 u spec:cross_y\n"
              "timber 30 27 33 role secondary\nplace 30 on 1 at-line guide 2 between t13 t20 +u +n\n"
              "timber 31 27 33 role secondary\nplace 31 on 1 at-line guide 2 between t20 t12 +u +n\n")
    base = load_base(scene)
    candidates = []
    for solid in base["solids"]:
        faces = {face["feature"]: face["vertices"] for face in solid["faces"]}
        points = [point for face in solid["faces"] for point in face["vertices"]]
        # START is an A×B end face. Its first and last walks expose B and A;
        # START/END centroids give exact axial length without assuming world axes.
        start, end = faces["START"], faces["END"]
        length = sum(abs(sum(p[axis] for p in end) - sum(p[axis] for p in start)) for axis in range(3)) // 4
        a = sum(abs(start[3][axis] - start[0][axis]) for axis in range(3))
        b = sum(abs(start[1][axis] - start[0][axis]) for axis in range(3))
        candidates.append({"id": solid["id"], "role": roles[solid["id"]], "A": a, "B": b,
                           "length": length, "placement_id": solid["placement_id"],
                           "z_min": min(p[2] for p in points), "z_max": max(p[2] for p in points)})
    return {"id": "timber-frame", "name": "z=2500 角材骨架・4 × 3 m",
            "description": "7 支角材底面與 z=2500 共面，厚度 33 mm 朝上；牆高 3000 mm、牆厚 100 mm。",
            "base_scene": base["base_scene"], "placement_id": 1,
            "timbers": [{"kind": "timber", "id": item["id"]} for item in candidates],
            "source": {"boundary_id": 1, "origin": [0, 0, 2500], "u": [1, 0, 0], "v": [0, 1, 0],
                       "loops": [{"verts": outline, "fixity": [1] * 4}], "timbers": candidates},
            "settings": {"bottom": 0, "height": 3000, "edges": [0, 1, 2, 3],
                         "floor": "boundary", "ceiling": "boundary", "holes": "none", "wall_thickness": 100}}


def examples():
    """Complete candidates only; selecting one does not replace the bridge world."""
    shapes = [
        ("rectangle", "矩形房間 4 × 3 m", [[0, 0], [4000, 0], [4000, 3000], [0, 3000]]),
        ("l-shape", "L 形房間", [[0, 0], [6000, 0], [6000, 3000], [4200, 3000], [4200, 4500], [0, 4500]])]
    result = []
    for identifier, name, outline in shapes:
        result.append({"id": identifier, "name": name,
            "description": "圖面 z = 2500 mm；空間底高 0 mm、高度 2800 mm，外牆厚 100 mm。",
            "base_scene": f"boundary 1 outline {_loop_text(outline)} kind room_plan\nplacement 1 on boundary 1 origin 0 0 2500 u +x v +y\n",
            "placement_id": 1,
            "source": {"boundary_id": 1, "origin": [0, 0, 2500], "u": [1, 0, 0], "v": [0, 1, 0],
                       "loops": [{"verts": deepcopy(outline), "fixity": [1] * len(outline)}]},
            "settings": {"bottom": 0, "height": 2800, "edges": list(range(len(outline))),
                         "floor": "boundary", "ceiling": "boundary", "holes": "none", "wall_thickness": 100}})
    result.append(deepcopy(_timber_frame_example()))
    return {"ok": True, "schema": "geometry-space-examples/1", "examples": result}
