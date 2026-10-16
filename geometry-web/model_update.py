"""#44 F1b: an isolated, explicit ordinary-plan replacement producer.

No state, identity ledger, live bridge, or history is owned here. The caller
must compare the receipt against current state again before one atomic update.
Package diff pins are SHA-256 of canonical JSON of the complete manifest.
"""
from __future__ import annotations

from copy import deepcopy
from datetime import datetime
import hashlib
import os
from pathlib import Path
import re
import subprocess
import tempfile

import space_modeling
from geometry_app import source_closure
from modeling import ModelError, canonical_bytes
from modeling.base import _build_adapter, load_base
from modeling.common import digest, scene_required_capabilities, strict_json_loads

ROOT = Path(__file__).resolve().parents[1]
MAX_SCENE_BYTES = 1024 * 1024
MAX_INPUT_BYTES = 8 * 1024 * 1024
MAX_GRAPH_BYTES = 16 * 1024 * 1024
BRIDGE_TIMEOUT = 20
PACKAGES = ("space", "volume", "clearance", "walls", "timbers")
PROTECTED = frozenset(("material", "method", "assembly-rule"))
HASH = re.compile(r"[a-f0-9]{64}\Z")
IDENTIFIER = re.compile(r"[A-Za-z0-9_-]{1,100}\Z")


def _fail(code, message, *, path=(), status="INVALID", clause="I31", diagnostics=None):
    raise ModelError(status, code, clause, message, path=list(path), diagnostics=diagnostics)


def _keys(value, required, optional=(), path=()):
    if type(value) is not dict or set(value) - set(required) - set(optional) or set(required) - set(value):
        _fail("UPDATE_SHAPE", "更新設定必須包含完整且明示的欄位。", path=path)


def _uid(value, path):
    if type(value) is not int or not 0 <= value <= 0xFFFFFFFF:
        _fail("UPDATE_ID", "來源編號必須是 uint32 整數（包含 0）。", path=path)


def _projection(value, path):
    _keys(value, ("kind", "view", "region", "wallSide"), path=path)
    if (value["kind"] != "space-boundary-plan" or value["view"] not in ("top", "bottom") or
            value["region"] != "interior" or value["wallSide"] != "outside"):
        _fail("UPDATE_PROJECTION", "請明選既有合法的空間邊界平面投影。", path=path)


def _scene(value, path):
    if type(value) is not str:
        _fail("UPDATE_SCENE", "請提供明選來源的完整場景。", path=path)
    encoded = value.encode("utf-8")
    if len(encoded) > MAX_SCENE_BYTES:
        _fail("UPDATE_CAPACITY", "來源場景超過 1 MiB 容量。", path=path, status="UNSUPPORTED", clause="I33")
    if b"\0" in encoded:
        _fail("UPDATE_SCENE", "來源場景不可含 NUL。", path=path)
    capabilities = scene_required_capabilities(value)
    if any(capability.startswith("assembly-") for capability in capabilities):
        _fail("UPDATE_SCOPE", "第一版來源更新不支援組構規則或 owned 角材場景。", path=path,
              status="UNSUPPORTED", clause="I32")


def _references(value, kinds, path, *, nonempty=False):
    if type(value) is not list or len(value) > 512 or (nonempty and not value):
        _fail("UPDATE_SELECTION", "請明選完整來源清單；不納入時請傳空清單。", path=path)
    seen = set()
    for index, reference in enumerate(value):
        here = (*path, index)
        _keys(reference, ("kind", "id"), path=here)
        if type(reference["kind"]) is not str or reference["kind"] not in kinds:
            _fail("UPDATE_SELECTION", "來源種類不在本次更新範圍。", path=here)
        _uid(reference["id"], (*here, "id"))
        key = (reference["kind"], reference["id"])
        if key in seen:
            _fail("UPDATE_SELECTION", "同一來源不可重複選取。", path=here)
        seen.add(key)


def _selection(value):
    _keys(value, ("placement_id", "boundary_id", "edges", "obstacles", "timbers", "projection"), path=("selection",))
    for name in ("placement_id", "boundary_id"):
        _uid(value[name], ("selection", name))
    edges = value["edges"]
    if (type(edges) is not list or not edges or len(edges) > 512 or
            any(type(edge) is not int or not 0 <= edge <= 0xFFFFFFFF for edge in edges) or
            len(set(edges)) != len(edges)):
        _fail("UPDATE_EDGES", "請明選非空、無重複的整數輪廓邊清單。", path=("selection", "edges"))
    _references(value["obstacles"], ("column", "beam"), ("selection", "obstacles"))
    _references(value["timbers"], ("timber",), ("selection", "timbers"))
    if value["timbers"] and value["boundary_id"] == 0:
        _fail("UPDATE_TIMBER_BOUNDARY", "納入角材必須明選有正式邊界輪廓的放置面；內含矩形目前不支援保存角材模型。",
              status="UNSUPPORTED", clause="I32", path=("selection", "boundary_id"))
    if value["projection"] is not None:
        _projection(value["projection"], ("selection", "projection"))
        if value["boundary_id"] == 0:
            _fail("UPDATE_PROJECTION", "平面投影必須明選具正編號的既有邊界。", path=("selection", "boundary_id"))


def _record(record):
    _keys(record, ("id", "name", "created_at", "source", "input", "result"), path=("record",))
    if type(record["id"]) is not str or not IDENTIFIER.fullmatch(record["id"]):
        _fail("UPDATE_RECORD", "模型身分欄位不合法。", path=("record", "id"))
    if type(record["name"]) is not str or not record["name"].strip() or len(record["name"]) > 200:
        _fail("UPDATE_RECORD", "模型名稱不合法。", path=("record", "name"))
    created = record["created_at"]
    try:
        if type(created) is not str or not created or len(created) > 100:
            raise ValueError()
        datetime.fromisoformat(created.replace("Z", "+00:00"))
    except ValueError:
        _fail("UPDATE_RECORD", "模型建立時間不合法。", path=("record", "created_at"))
    source, inputs = record["source"], record["input"]
    _keys(source, ("kind", "placement_id", "boundary_id", "scene_hash"), ("projection",), path=("record", "source"))
    if source["kind"] not in ("scene", "example") or type(source["scene_hash"]) is not str or not HASH.fullmatch(source["scene_hash"]):
        _fail("UPDATE_RECORD", "模型来源中繼資料不合法。", path=("record", "source"))
    if type(inputs) is not dict or inputs.get("mode") != "plan":
        _fail("UPDATE_SCOPE", "第一版來源更新只支援普通單一平面模型。", status="UNSUPPORTED", clause="I32", path=("record", "input"))
    _keys(inputs, ("mode", "base_scene", "obstacles", "placement_id", "settings"), ("timbers",), path=("record", "input"))
    _uid(source["placement_id"], ("record", "source", "placement_id"))
    if source["boundary_id"] is not None:
        _uid(source["boundary_id"], ("record", "source", "boundary_id"))
    if source["placement_id"] != inputs["placement_id"]:
        _fail("UPDATE_RECORD", "舊模型來源面與輸入不一致。", path=("record", "source", "placement_id"))
    if "projection" in source:
        _projection(source["projection"], ("record", "source", "projection"))
        if not source["boundary_id"]:
            _fail("UPDATE_PROJECTION", "舊模型投影缺少既有邊界。", path=("record", "source"))
    _scene(inputs["base_scene"], ("record", "input", "base_scene"))
    _references(inputs["obstacles"], ("column", "beam"), ("record", "input", "obstacles"))
    if "timbers" in inputs:
        _references(inputs["timbers"], ("timber",), ("record", "input", "timbers"), nonempty=True)
        if not source["boundary_id"]:
            _fail("UPDATE_TIMBER_BOUNDARY", "舊角材模型缺少正式邊界輪廓，不符合現行保存契約；請重新建立有輪廓來源的模型。",
                  status="UNSUPPORTED", clause="I32", path=("record", "source", "boundary_id"))


def _program(value, *, base=False):
    candidate = value or os.environ.get("GEOMETRY_MODEL_BASE" if base else "GEOMETRY_MODEL_UPDATE_BRIDGE")
    if not candidate:
        candidate = _build_adapter() if base else os.environ.get("GEOMETRY_TEST_BRIDGE") or ROOT / "geometry-web" / "web_bridge.exe"
    try:
        path = Path(candidate).resolve(strict=True)
        if not path.is_file() or not os.access(path, os.X_OK):
            raise OSError()
        fingerprint = hashlib.sha256(path.read_bytes()).hexdigest()
    except (OSError, TypeError, ValueError):
        _fail("UPDATE_EXECUTABLE", "無法確認來源更新使用的實際原生執行檔。", status="UNSUPPORTED", clause="I32")
    return str(path), fingerprint


def _producer_hash():
    """Pin this producer and every local Python/native helper in its closure."""
    paths = {Path(__file__).resolve(), ROOT / "geometry-web" / "space_modeling.py", ROOT / "current_geometry.c"}
    paths.update(path for _, path in source_closure.source_paths(ROOT))
    for directory in (ROOT / "geometry-core", ROOT / "geometry-web"):
        paths.update(path for path in directory.rglob("*") if path.suffix in (".c", ".h", ".inc") and "vendor" not in path.parts)
    paths.update(ROOT.glob("*.h"))
    paths.update(ROOT.glob("*.inc"))
    try:
        return digest([[path.relative_to(ROOT).as_posix(), hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()]
                       for path in sorted(paths)])
    except OSError:
        _fail("UPDATE_RUNTIME", "來源更新 producer 的完整來源無法核對。", status="UNSUPPORTED", clause="I32")


def _runtime(base, bridge):
    try:
        if not source_closure.current_identity()["fresh"]:
            _fail("UPDATE_RUNTIME", "來源更新模組已改變，請重新啟動 Python 程序。", status="UNSUPPORTED", clause="I32")
        axiom = hashlib.sha256((ROOT / "公理層.md").read_bytes().replace(b"\r\n", b"\n")).hexdigest()
    except OSError:
        _fail("UPDATE_RUNTIME", "來源更新公理版本無法核對。", status="UNSUPPORTED", clause="I32")
    return {"base_binary_sha256": _program(base, base=True)[1], "bridge_binary_sha256": _program(bridge)[1],
            "producer_sha256": _producer_hash(), "axiom_sha256": axiom}


def _graph(scene, program):
    """One fresh native child and owned files; stdin EOF exits the bridge."""
    try:
        with tempfile.TemporaryDirectory(prefix="geometry-model-update-") as directory:
            source = Path(directory) / "input.scene"
            output = Path(directory) / "output.json"
            error = Path(directory) / "error.log"
            source.write_bytes(scene.encode("utf-8"))
            with output.open("wb") as stdout, error.open("wb") as stderr:
                result = subprocess.run([program], input=("source-inspect-file " + str(source) + "\n").encode("utf-8"),
                                        stdout=stdout, stderr=stderr, cwd=directory, timeout=BRIDGE_TIMEOUT, check=False)
            if result.returncode:
                _fail("UPDATE_GRAPH_EXIT", "原生來源檢查異常退出。", status="UNSUPPORTED", clause="I32")
            if output.stat().st_size > MAX_GRAPH_BYTES:
                _fail("UPDATE_GRAPH_CAPACITY", "來源檢查輸出超過容量。", status="UNSUPPORTED", clause="I33")
            value = strict_json_loads(output.read_bytes())
    except subprocess.TimeoutExpired:
        _fail("UPDATE_GRAPH_TIMEOUT", "來源檢查超過執行時間。", status="UNSUPPORTED", clause="I33")
    except OSError:
        _fail("UPDATE_GRAPH_EXECUTABLE", "無法啟動隔離來源檢查。", status="UNSUPPORTED", clause="I32")
    if (type(value) is not dict or value.get("ok") is not True or value.get("schema") != "source-inspector/1" or
            value.get("live") is not False or value.get("complete") is not True or
            value.get("identityContinuity") != "unknown" or type(value.get("nodes")) is not list or
            type(value.get("edges")) is not list or len(value["nodes"]) > 2048 or len(value["edges"]) > 8192):
        _fail("UPDATE_GRAPH_UNCHECKED", "原生來源圖不完整，不能確認固定材料或規則。", status="UNSUPPORTED", clause="I32")
    nodes, edges = {}, {}
    for node in value["nodes"]:
        if (type(node) is not dict or any(type(node.get(name)) is not str for name in ("key", "kind", "id")) or
                node["key"] in nodes or type(node.get("version")) is not int or not 0 <= node["version"] <= 0xFFFFFFFF or
                any(type(node.get(name)) is not str or not HASH.fullmatch(node[name]) for name in ("definitionFingerprint", "valueFingerprint"))):
            _fail("UPDATE_GRAPH_UNCHECKED", "原生來源節點不完整。", status="UNSUPPORTED", clause="I32")
        if node["kind"] == "timber" and node.get("nativeOwner") is not None:
            _fail("UPDATE_SCOPE", "第一版來源更新不支援 owned 組構角材。", status="UNSUPPORTED", clause="I32")
        nodes[node["key"]] = node
    for edge in value["edges"]:
        if (type(edge) is not dict or type(edge.get("active")) is not bool or
                any(type(edge.get(name)) is not str for name in ("from", "to", "relation", "field")) or
                edge.get("from") not in nodes or edge.get("to") not in nodes):
            _fail("UPDATE_GRAPH_UNCHECKED", "原生來源引用不完整。", status="UNSUPPORTED", clause="I32")
        # I9 candidates and RC container membership do not define fixed sources.
        if (edge["relation"] in ("span-candidate", "confirmed-support") or
                edge["relation"] == "member" and nodes[edge["from"]]["kind"] in ("column", "beam")):
            continue
        # Even overridden fixed source definitions must not be upgraded silently.
        edges.setdefault(edge["from"], []).append(edge)
    projection = value.get("timberSupports")
    if (type(projection) is not dict or projection.get("schema") != "native-timber-supports/1" or
            type(value.get("sourceFingerprint")) is not str or not HASH.fullmatch(value["sourceFingerprint"]) or
            projection.get("sourceFingerprint") != value["sourceFingerprint"] or
            type(projection.get("entries")) is not list or len(projection["entries"]) > 2048):
        _fail("UPDATE_GRAPH_UNCHECKED", "原生實際支撐來源版本無法核對。", status="UNSUPPORTED", clause="I32")
    support_known = {}
    for entry in projection["entries"]:
        if type(entry) is not dict or type(entry.get("id")) is not int or not 0 <= entry["id"] <= 0xFFFFFFFF:
            _fail("UPDATE_GRAPH_UNCHECKED", "原生實際支撐引用不完整。", status="UNSUPPORTED", clause="I32")
        key = "timber:" + str(entry["id"])
        node = nodes.get(key)
        if (key in support_known or node is None or node.get("placed") is not True or
                entry.get("surface") != node.get("surface") or entry.get("owner") is not None):
            _fail("UPDATE_GRAPH_UNCHECKED", "原生實際支撐所屬角材無法核對。", status="UNSUPPORTED", clause="I32")
        support_known[key] = True
        for end in ("start", "finish"):
            endpoint = entry.get(end)
            if type(endpoint) is not dict or endpoint.get("status") != "exact":
                support_known[key] = False
                continue
            relation = endpoint.get("relation")
            source = relation.get("source") if type(relation) is dict else None
            if (type(source) is not dict or source.get("kind") not in ("timber", "boundary", "placement") or
                    type(source.get("id")) is not int or not 0 <= source["id"] <= 0xFFFFFFFF or
                    relation.get("surface") != node.get("surface") or relation.get("owner") is not None):
                _fail("UPDATE_GRAPH_UNCHECKED", "原生已確認支撐的具型別來源不完整。", status="UNSUPPORTED", clause="I32")
            target = source["kind"] + ":" + str(source["id"])
            if target not in nodes:
                _fail("UPDATE_GRAPH_UNCHECKED", "原生已確認支撐來源不存在。", status="UNSUPPORTED", clause="I32")
            if source["kind"] == "timber":
                if (relation.get("kind") != "timber-face" or target == key or nodes[target].get("placed") is not True or
                        nodes[target].get("surface") != node.get("surface") or
                        relation.get("localFace") not in ("A0", "A1", "B0", "B1", "START", "END")):
                    _fail("UPDATE_GRAPH_UNCHECKED", "原生已確認角材端面來源無法核對。", status="UNSUPPORTED", clause="I32")
            elif (relation.get("kind") not in ("outline-edge", "hole-edge") or
                  source["kind"] == "placement" and source["id"] != node.get("surface") or
                  source["kind"] == "boundary" and not any(edge["to"] == target and edge["relation"] == "position" and edge["field"] == "boundary"
                      for edge in edges.get("placement:" + str(node.get("surface")), []))):
                _fail("UPDATE_GRAPH_UNCHECKED", "原生已確認邊界端點來源無法核對。", status="UNSUPPORTED", clause="I32")
            # These are exact relations emitted by the existing native F1a
            # projection; no candidate contact or nearby-position inference.
            edges.setdefault(key, []).append({"from": key, "to": target, "relation": "confirmed-support",
                                               "field": end + ":" + str(relation.get("localFace")), "active": True})
    return nodes, edges, support_known


def _protected(graph, inputs):
    nodes, edges, support_known = graph
    roots = ["placement:" + str(inputs["placement_id"])]
    roots.extend(reference["kind"] + ":" + str(reference["id"]) for reference in [*inputs["obstacles"], *inputs.get("timbers", [])])
    protected, associations = set(), {}
    for root in roots:
        pending, seen, fixed, reverse = [root], set(), set(), {}
        while pending:
            key = pending.pop()
            if key in seen:
                continue
            node = nodes.get(key)
            if node is None:
                _fail("UPDATE_GRAPH_UNCHECKED", "明選來源沒有完整原生引用圖：" + key, status="UNSUPPORTED", clause="I32")
            if node["kind"] == "timber" and support_known.get(key) is not True:
                _fail("UPDATE_SUPPORT_UNCHECKED", "明選來源的原生實際支撐身分仍不確定：" + key,
                      status="UNSUPPORTED", clause="I32")
            seen.add(key)
            if node["kind"] in PROTECTED:
                fixed.add(key)
                protected.add((node["kind"], node["id"], node["version"], node["definitionFingerprint"]))
            for edge in edges.get(key, []):
                reverse.setdefault(edge["to"], []).append(key)
                pending.append(edge["to"])
        # Keep the typed fields and topology of every path leading to a fixed
        # definition. A global node set alone misses A/B or cross-timber swaps.
        relevant, pending = set(), list(fixed)
        while pending:
            key = pending.pop()
            if key not in relevant:
                relevant.add(key)
                pending.extend(reverse.get(key, []))
        def label(key):
            if key == root:
                return "selected-root"
            if key == roots[0]:
                return "selected-placement"
            return key
        signatures = {(label(edge["from"]), label(edge["to"]), edge["relation"], edge["field"], edge["active"])
                      for key in relevant for edge in edges.get(key, []) if edge["to"] in relevant}
        # The sole placement has an explicit old/new correspondence. Other
        # roots can only be compared when the user explicitly selected that key.
        associations["selected-placement" if root == roots[0] else root] = signatures
    return protected, associations


def _fixed_associations(before, after):
    for root in sorted(set(before) | set(after)):
        old, new = before.get(root, set()), after.get(root, set())
        if old == new:
            continue
        if root not in before or root not in after:
            _fail("UPDATE_FIXED_ASSOCIATION", "明選的新舊來源含固定版本，但缺少可核對的逐物件對應：" + root,
                  path=("selection",), status="UNSUPPORTED", clause="I32")
        diagnostic = {"root": None, "path": ["selection"], "code": "UPDATE_FIXED_VERSION", "clause": "R31",
                      "message": "明選來源的固定材料／規則欄位引用已改變；本次更新不包含版本或綁定改換。",
                      "missing": {"selected_root": root, "before_only": [list(value) for value in sorted(old - new)],
                                  "after_only": [list(value) for value in sorted(new - old)]}}
        _fail("UPDATE_FIXED_VERSION", diagnostic["message"], path=("selection",), clause="R31", diagnostics=[diagnostic])


def _fixed_versions(before, after):
    if before == after:
        return
    removed, added = sorted(before - after), sorted(after - before)
    def refs(values):
        return [{"kind": kind, "id": identifier, "version": version, "fingerprint": fingerprint}
                for kind, identifier, version, fingerprint in values]
    diagnostic = {"root": None, "path": ["selection"], "code": "UPDATE_FIXED_VERSION", "clause": "R31",
                  "message": "固定材料／規則版本引用已改變；本次來源更新不包含版本升級。",
                  "missing": {"before_only": refs(removed), "after_only": refs(added)}}
    _fail("UPDATE_FIXED_VERSION", diagnostic["message"], path=("selection",), clause="R31", diagnostics=[diagnostic])


def _placement(base, placement, boundary, projection, path):
    selected = next((item for item in base["placements"] if item["id"] == placement), None)
    if selected is None or (selected.get("boundary_id") or 0) != (boundary or 0):
        _fail("UPDATE_SOURCE", "明選承載面不存在，或沒有引用明選邊界。", path=path, clause="D4")
    if projection is not None and (boundary == 0 or selected["n"][:2] != [0, 0] or abs(selected["n"][2]) != 1):
        _fail("UPDATE_PROJECTION", "明選平面投影與承載面不一致。", path=path, clause="D4")


def _diff(before, after):
    def pair(left, right):
        return {"before": deepcopy(left), "after": deepcopy(right)}
    def manifest(record, kind):
        package = record["result"].get(kind)
        return digest(package["manifest"]) if package is not None else None
    return {"source": pair(before["source"], after["source"]), "input": pair(before["input"], after["input"]),
            "settings": pair(before["input"]["settings"], after["input"]["settings"]),
            "summary": pair(before["result"]["summary"], after["result"]["summary"]),
            "packages": [{"kind": kind, "before": manifest(before, kind), "after": manifest(after, kind)} for kind in PACKAGES]}


def prepare_update(data, *, base_executable=None, bridge_executable=None, max_cells=200000):
    """Return a full replacement receipt from actual native, isolated replay."""
    encoded = canonical_bytes(data)
    if len(encoded) > MAX_INPUT_BYTES:
        _fail("UPDATE_CAPACITY", "完整更新設定超過 8 MiB 容量。", status="UNSUPPORTED", clause="I33")
    _keys(data, ("record", "current_scene", "selection"))
    _record(data["record"])
    _scene(data["current_scene"], ("current_scene",))
    _selection(data["selection"])
    if type(max_cells) is not int or max_cells < 1:
        _fail("UPDATE_CAPACITY", "建模容量須為正整數。", status="UNSUPPORTED", clause="I33")
    base, _ = _program(base_executable, base=True)
    bridge, _ = _program(bridge_executable)
    runtime = _runtime(base, bridge)
    record, selection = data["record"], data["selection"]
    old_base = load_base(record["input"]["base_scene"], executable=base)
    _placement(old_base, record["source"]["placement_id"], record["source"]["boundary_id"],
               record["source"].get("projection"), ("record", "source"))
    try:
        replay = space_modeling.replay_stored(record["input"], record["result"],
                                             base_executable=base, max_cells=max_cells)
    except ModelError as exc:
        if exc.code != "SPACE_STORED_REPLAY" and exc.status != "INVALID":
            raise
        _fail("UPDATE_OLD_REPLAY", "舊模型紀錄與原生歷史重播不一致。", path=("record", "result"))
    if canonical_bytes(replay) != canonical_bytes(record["result"]) or record["source"]["scene_hash"] != replay["source_sha256"]:
        _fail("UPDATE_OLD_REPLAY", "完整舊模型紀錄與原生重播不一致。", path=("record", "result"))
    new_base = load_base(data["current_scene"], executable=base)
    _placement(new_base, selection["placement_id"], selection["boundary_id"], selection["projection"], ("selection",))
    inputs = {"mode": "plan", "base_scene": new_base["base_scene"], "placement_id": selection["placement_id"],
              "settings": deepcopy(record["input"]["settings"]), "obstacles": deepcopy(selection["obstacles"])}
    inputs["settings"]["edges"] = deepcopy(selection["edges"])
    if selection["timbers"]:
        inputs["timbers"] = deepcopy(selection["timbers"])
    old_graph = _graph(record["input"]["base_scene"], bridge)
    new_graph = _graph(data["current_scene"], bridge)
    old_fixed, old_associations = _protected(old_graph, record["input"])
    new_fixed, new_associations = _protected(new_graph, inputs)
    _fixed_versions(old_fixed, new_fixed)
    _fixed_associations(old_associations, new_associations)
    result = space_modeling.preview(inputs, base_executable=base, max_cells=max_cells)
    source = {"kind": "scene", "placement_id": selection["placement_id"], "boundary_id": selection["boundary_id"],
              "scene_hash": result["source_sha256"]}
    if selection["projection"] is not None:
        source["projection"] = deepcopy(selection["projection"])
    replacement = {"id": record["id"], "name": record["name"], "created_at": record["created_at"],
                   "source": source, "input": inputs, "result": result}
    if runtime != _runtime(base, bridge):
        _fail("UPDATE_RUNTIME_CHANGED", "執行檔、producer 或公理在產生候選期間已改變。", status="UNSUPPORTED", clause="I32")
    return {"ok": True, "schema": "geometry-model-update-candidate/1", "identity": "unknown",
            "old_record_sha256": digest(record), "current_scene_sha256": hashlib.sha256(data["current_scene"].encode("utf-8")).hexdigest(),
            "selection": deepcopy(selection), "record": replacement, "diff": _diff(record, replacement), "runtime": runtime}
