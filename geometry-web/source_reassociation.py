"""R09b D1 v2: stateless ordinary-faces reassociation calculations.

Only complete, isolated native source inspection and model replay are trusted
here. Project membership and row labels are caller assertions. There is no App
owner, epoch, token, confirmation, history, allocator or project-file writer.
The returned draft is NOT a saved project, an effective receipt, or authority
to commit. A host must provide those safeguards in a later integration slice.
"""
from __future__ import annotations

from copy import deepcopy
import hashlib
from pathlib import Path
import re
import subprocess
import tempfile

import model_update
import space_modeling
from modeling import ModelError, canonical_bytes
from modeling.base import load_base
from modeling.common import strict_json_loads


CAPABILITY = "source-reassociation/1"
SCHEMA = "geometry-reassociation-draft/2"
MAX_FACES = 16
MAX_CARRIER_LABEL_BYTES = 128
MAX_DRAFT_BYTES = 16 * 1024 * 1024
MAX_RECORD_BYTES = model_update.MAX_INPUT_BYTES
IDENTITY_KINDS = frozenset(("boundary", "placement", "column", "beam", "timber",
                            "parameter", "parameter-field"))
MARK = re.compile(r"[a-f0-9]{32}:[1-9][0-9]{0,19}\Z")
MODULE_PATH = Path(__file__).resolve()
LOADED_SHA = hashlib.sha256(MODULE_PATH.read_bytes().replace(b"\r\n", b"\n")).hexdigest()
AUTHORITY = {"project": "caller-asserted", "history": "unverified",
             "confirmation": False, "carrierIds": "caller-provisional"}


def _fail(code, message, *, clause="I75", status="INVALID"):
    raise ModelError(status, code, clause, message)


def _keys(value, names):
    if type(value) is not dict or set(value) != set(names):
        _fail("REASSOCIATION_SHAPE", "欄位必須完整明示；未知欄位不能忽略。")


def _text(value, name):
    if type(value) is not str or not value.strip() or len(value.encode("utf-8")) > 256 or "\0" in value:
        _fail("REASSOCIATION_CONTEXT", name + " 必須是非空且有界的識別。")


def _sha(raw):
    return hashlib.sha256(raw).hexdigest()


def _valid_mark(value):
    return (type(value) is str and len(value) <= 53 and MARK.fullmatch(value) is not None
            and int(value[33:]) <= 0xFFFFFFFFFFFFFFFF)


def _raw(raw):
    if type(raw) is not bytes or not raw or len(raw) > MAX_RECORD_BYTES:
        _fail("REASSOCIATION_RECORD_CAPACITY", "舊模型須為非空 UTF-8 bytes，最多 8 MiB。",
              status="UNSUPPORTED", clause="I33")
    try:
        raw.decode("utf-8")
    except UnicodeDecodeError:
        _fail("REASSOCIATION_ENCODING", "舊模型不是合法 UTF-8。")
    return strict_json_loads(raw)


def capabilities():
    """Describe only this calculation helper; do not extend exchange caps."""
    return {"schema": "geometry-reassociation-helper/2", "complete": False,
            "draftCapability": CAPABILITY, "consumers": ["ordinary-faces-fixed"],
            "automaticReceiptKinds": [], "modelCarrierEdit": False,
            "commit": False, "save": False, "history": False,
            "authority": deepcopy(AUTHORITY),
            "capacities": {"faces": MAX_FACES, "recordBytes": MAX_RECORD_BYTES,
                           "draftBytes": MAX_DRAFT_BYTES,
                           "carrierLabelBytes": MAX_CARRIER_LABEL_BYTES,
                           "sceneBytes": model_update.MAX_SCENE_BYTES}}


def _root_valid(root):
    allowed = {"role", "kind", "id", "incarnation", "fieldId", "uncovered",
               "status", "definitionPin", "decision", "confirmed"}
    statuses = {"unknown", "conflict", "absent", "replaced", "continuous"}
    return (type(root) is dict and not set(root) - allowed
            and root.get("role") in ("placement", "boundary", "use")
            and root.get("kind") in ("placement", "boundary")
            and type(root.get("id")) is int and 0 <= root["id"] <= 0xFFFFFFFF
            and _valid_mark(root.get("incarnation")) and "uncovered" not in root
            and ("fieldId" not in root or type(root["fieldId"]) is int and root["fieldId"] >= 0)
            and ("status" not in root or root["status"] in statuses))


def judge_roots(identity, live, *, same_project=True):
    """Pure R57 calculation for ordinary placement/boundary roots.

    ``live`` is a complete, already I70-checked source-inspector graph view:
    {data: {identityLedger: ...}, nodes: {typed_key: node}}. This function does
    not prove that precondition. ``inspect`` and ``prepare_candidate`` do so
    by native execution. Project scope is an explicit caller condition, not
    something inferable from scene bytes. The output agrees field-for-field
    with IdentityLedger.judgeRoots on this valid, ordinary-source domain.
    """
    if (type(identity) is not dict or type(identity.get("roots")) is not list
            or type(live) is not dict or type(live.get("nodes")) is not dict
            or type(same_project) is not bool):
        _fail("REASSOCIATION_JUDGMENT_SHAPE", "身分根與完整來源檢查視圖必須明示。")
    roots, current = identity["roots"], live["nodes"]
    ledger = live.get("data", {}).get("identityLedger", {})
    active = ledger.get("schema") == "identity-ledger/1" and ledger.get("active") is True
    rows = []
    for root in roots:
        if type(root) is not dict or root.get("kind") not in ("placement", "boundary"):
            _fail("REASSOCIATION_JUDGMENT_SCOPE", "本片只判普通承載面與邊界根。",
                  status="UNSUPPORTED", clause="I32")
        key = root["kind"] + ":" + str(root.get("id"))
        node = current.get(key)
        marker = node.get("incarnation") if type(node) is dict else None
        row = {**deepcopy(root), "currentIncarnation": marker if _valid_mark(marker) else None,
               "confirmed": False}
        if not same_project or not active or not _root_valid(root):
            row["status"] = "unknown"
            rows.append(row)
            continue
        # Conflict precedes absence, including a mark on another typed kind.
        if ((type(node) is dict and node.get("conflict") is True) or
                any(other != key and type(value) is dict and value.get("incarnation") == root["incarnation"]
                    for other, value in current.items())):
            status = "conflict"
        elif node is None:
            status = "absent"
        elif marker is None:
            # Ordinary covered nodes without a mark are outside the valid
            # active I70 domain. Never turn an incomplete view into absence.
            _fail("REASSOCIATION_SOURCE_MARK", "啟用帳的普通來源缺少記號。", clause="I70")
        elif marker == root["incarnation"]:
            status = "continuous"
        else:
            status = "replaced"
        row.update(status=status,
                   definitionPin=(node.get("definitionFingerprint") or node.get("definitionPin") or None)
                   if type(node) is dict else None,
                   previousDefinitionPin=root.get("definitionPin"))
        rows.append(row)
    return rows


def _runtime(base, bridge):
    try:
        current = _sha(MODULE_PATH.read_bytes().replace(b"\r\n", b"\n"))
    except OSError:
        current = None
    if current != LOADED_SHA:
        _fail("REASSOCIATION_RUNTIME", "重新關聯執行器已變更，請重新啟動。", status="UNSUPPORTED", clause="I32")
    return {**model_update._runtime(base, bridge), "reassociation_sha256": current}


def _observe(scene, bridge):
    """Read the complete source through native I70, then native deidentify."""
    model_update._scene(scene, ("source_scene",))
    try:
        with tempfile.TemporaryDirectory(prefix="geometry-reassociation-") as directory:
            source = Path(directory) / "source.scene"
            output = Path(directory) / "out.jsonl"
            errors = Path(directory) / "errors.log"
            source.write_bytes(scene.encode("utf-8"))
            commands = ("source-inspect-file " + str(source) + "\nloadfile " + str(source) +
                        "\ndump-deidentified\n").encode("utf-8")
            with output.open("wb") as stdout, errors.open("wb") as stderr:
                child = subprocess.run([bridge], input=commands, stdout=stdout, stderr=stderr,
                                       cwd=directory, timeout=model_update.BRIDGE_TIMEOUT, check=False)
            if child.returncode:
                _fail("REASSOCIATION_NATIVE_EXIT", "原生來源驗證異常退出。", status="UNSUPPORTED", clause="I32")
            if output.stat().st_size > model_update.MAX_GRAPH_BYTES + 2 * model_update.MAX_SCENE_BYTES:
                _fail("REASSOCIATION_NATIVE_CAPACITY", "原生來源輸出超過容量。", status="UNSUPPORTED", clause="I33")
            answers = [strict_json_loads(line) for line in output.read_bytes().splitlines()]
    except subprocess.TimeoutExpired:
        _fail("REASSOCIATION_NATIVE_TIMEOUT", "原生來源驗證超過執行時間。", status="UNSUPPORTED", clause="I33")
    except OSError:
        _fail("REASSOCIATION_NATIVE_IO", "無法執行隔離原生來源驗證。", status="UNSUPPORTED", clause="I32")
    if len(answers) != 3 or any(type(item) is not dict or item.get("ok") is not True for item in answers):
        _fail("REASSOCIATION_SOURCE_INVALID", "完整來源未通過原生讀取與 I70，不能判為 absent。", clause="I70")
    graph, loaded, deidentified = answers
    ledger = graph.get("identityLedger")
    if (graph.get("schema") != "source-inspector/1" or graph.get("complete") is not True or
            graph.get("live") is not False or graph.get("identityContinuity") != "unknown" or
            type(ledger) is not dict or ledger.get("schema") != "identity-ledger/1" or
            type(ledger.get("active")) is not bool or type(graph.get("nodes")) is not list or
            len(graph["nodes"]) > 2048 or type(graph.get("edges")) is not list or len(graph["edges"]) > 8192 or
            loaded.get("definition_sha256") != graph.get("sourceFingerprint") or
            deidentified.get("definition_sha256") != graph.get("sourceFingerprint")):
        _fail("REASSOCIATION_SOURCE_INCOMPLETE", "原生來源閉包或同一性驗證不完整。", status="UNSUPPORTED", clause="I32")
    scene_without_identity = deidentified.get("text")
    model_update._scene(scene_without_identity, ("deidentified_scene",))
    nodes, marks = {}, {}
    for node in graph["nodes"]:
        if (type(node) is not dict or type(node.get("key")) is not str or node["key"] in nodes or
                any(type(node.get(key)) is not str or not model_update.HASH.fullmatch(node[key])
                    for key in ("definitionFingerprint", "valueFingerprint"))):
            _fail("REASSOCIATION_SOURCE_NODE", "原生來源節點或內容指紋不完整。", clause="I70")
        nodes[node["key"]] = node
        if node.get("kind") not in IDENTITY_KINDS:
            if node.get("incarnation") is not None:
                _fail("REASSOCIATION_SOURCE_MARK", "未涵蓋種類不能宣稱持續身分。", clause="I70")
            continue
        if type(node.get("id")) is not str or not re.fullmatch(r"0|[1-9][0-9]*", node["id"]):
            _fail("REASSOCIATION_SOURCE_KEY", "來源端點不是具型別的整數鍵。", clause="I70")
        model_update._uid(int(node["id"]), ("source", "id"))
        model_update._uid(node.get("fieldId"), ("source", "fieldId"))
        expected_key = node["kind"] + ":" + node["id"]
        if node["kind"] == "parameter-field":
            expected_key += ":f" + str(node["fieldId"])
        if node["key"] != expected_key:
            _fail("REASSOCIATION_SOURCE_KEY", "來源節點鍵與種類、編號不相符。", clause="I70")
        if node["kind"] == "timber" and node.get("nativeOwner") is not None:
            _fail("REASSOCIATION_SCOPE", "第一片不支援 owned 組構來源。", status="UNSUPPORTED", clause="I32")
        marker = node.get("incarnation")
        if ledger["active"]:
            if not _valid_mark(marker) or marker in marks:
                _fail("REASSOCIATION_SOURCE_MARK", "原生記號不合法或未保持單射。", clause="I70")
            marks[marker] = node["key"]
        elif marker is not None:
            _fail("REASSOCIATION_SOURCE_MARK", "未啟用來源不得補造記號。", clause="I70")
    return {"nodes": nodes, "active": ledger["active"], "scene": scene_without_identity,
            "view": {"data": {"identityLedger": deepcopy(ledger)}, "nodes": nodes}}


def _record(value, base):
    model_update._record(value)
    inputs = value["input"]
    if inputs["mode"] != "faces" or inputs["obstacles"]:
        _fail("REASSOCIATION_SCOPE", "第一片只支援無障礙物的普通固定載體集合。", status="UNSUPPORTED", clause="I32")
    if not 1 <= len(inputs["uses"]) <= MAX_FACES:
        _fail("REASSOCIATION_CARRIERS", "本片載體容量為 1 至 16；增減載體另需能力。", status="UNSUPPORTED", clause="I33")
    actual = space_modeling.replay_stored(inputs, value["result"], base_executable=base)
    if canonical_bytes(actual) != canonical_bytes(value["result"]) or actual["source_sha256"] != value["source"]["scene_hash"]:
        _fail("REASSOCIATION_OLD_REPLAY", "完整舊模型與原生重播不相符。", clause="I32")


def _identity(record):
    stored = {root["id"]: root for root in record.get("sourceIdentity", {}).get("roots", [])}
    return {"schema": "model-source-identity/1", "roots": [
        deepcopy(stored.get(use["placement_id"], {"role": "use", "kind": "placement",
                   "id": use["placement_id"], "incarnation": None}))
        for use in record["input"]["uses"]]}


def _context(record_raw, source_scene, project_id, record_project_id, base_executable, bridge_executable):
    _text(project_id, "project_id")
    if record_project_id is not None:
        _text(record_project_id, "record_project_id")
    base = model_update._program(base_executable, base=True)[0]
    bridge = model_update._program(bridge_executable)[0]
    runtime = _runtime(base, bridge)
    record = _raw(record_raw)
    _record(record, base)
    source = _observe(source_scene, bridge)
    old_source = _observe(record["input"]["base_scene"], bridge)
    comparison = judge_roots(_identity(record), source["view"], same_project=record_project_id == project_id)
    for row in comparison:
        key = row["kind"] + ":" + str(row["id"])
        old, current = old_source["nodes"].get(key), source["nodes"].get(key)
        row["definitionChanged"] = (old["definitionFingerprint"] != current["definitionFingerprint"]
                                    if old is not None and current is not None else None)
        row["valueChanged"] = (old["valueFingerprint"] != current["valueFingerprint"]
                               if old is not None and current is not None else None)
    return record, source, comparison, base, bridge, runtime


def inspect(record_raw, source_scene, *, project_id, record_project_id=None,
            base_executable=None, bridge_executable=None):
    """Read-only snapshot comparison; never upgrades legacy model bytes."""
    _, _, comparison, base, bridge, runtime = _context(
        record_raw, source_scene, project_id, record_project_id, base_executable, bridge_executable)
    if runtime != _runtime(base, bridge):
        _fail("REASSOCIATION_RUNTIME", "來源比較期間執行版本改變。", status="UNSUPPORTED", clause="I32")
    return {"schema": "geometry-reassociation-inspection/2", "authority": deepcopy(AUTHORITY),
            "beforeSha256": _sha(record_raw), "sourceSha256": _sha(source_scene.encode("utf-8")),
            "comparison": comparison, "proposals": []}


def _selection(selection, carrier_ids, record, comparison):
    if type(carrier_ids) is not list or len(carrier_ids) != len(record["input"]["uses"]):
        _fail("REASSOCIATION_CARRIER_LABELS", "必須明示與全部舊列對應的暫態列標籤。")
    for value in carrier_ids:
        _text(value, "carrier_ids")
        if len(value.encode("utf-8")) > MAX_CARRIER_LABEL_BYTES:
            _fail("REASSOCIATION_CARRIER_LABELS", "暫態列標籤最多 128 個 UTF-8 bytes。")
    if len(set(carrier_ids)) != len(carrier_ids):
        _fail("REASSOCIATION_CARRIER_LABELS", "暫態列標籤不得重複。")
    if type(selection) is not list or len(selection) != len(carrier_ids):
        _fail("REASSOCIATION_SELECTION", "必須依原順序明選全部固定載體。", clause="R61")
    seen = set()
    for choice, label, use, judgment in zip(selection, carrier_ids, record["input"]["uses"], comparison):
        _keys(choice, ("carrierId", "placement_id", "orientation", "purpose"))
        model_update._uid(choice["placement_id"], ("selection", "placement_id"))
        if (choice["carrierId"] != label or choice["placement_id"] in seen or
                type(choice["orientation"]) is not int or choice["orientation"] != use["orientation"] or
                choice["purpose"] != use["purpose"]):
            _fail("REASSOCIATION_FIXED_CARRIER", "載體順序、用途與朝向必須明示且保持原值；來源不可重複。", clause="R61")
        if judgment["status"] == "continuous" and choice["placement_id"] != use["placement_id"]:
            _fail("REASSOCIATION_CONTINUOUS_RETARGET", "本片不改指仍延續的列；載體編輯由後續能力處理。",
                  status="UNSUPPORTED", clause="R62")
        seen.add(choice["placement_id"])


def _frames(scene, base):
    return {item["id"]: {key: deepcopy(item[key]) for key in ("origin", "u", "v", "n")}
            for item in load_base(scene, executable=base)["placements"]}


def prepare_candidate(record_raw, source_scene, selection, *, project_id, carrier_ids,
                      record_project_id=None, base_executable=None, bridge_executable=None):
    """Build a full, uncommitted draft; it has no execution authority."""
    record, source, comparison, base, bridge, runtime = _context(
        record_raw, source_scene, project_id, record_project_id, base_executable, bridge_executable)
    if record_project_id is not None and record_project_id != project_id:
        _fail("REASSOCIATION_IMPORT", "本片未實作跨專案匯入對應，不能補造歷史同一性。", status="UNSUPPORTED")
    _selection(selection, carrier_ids, record, comparison)
    producer = model_update.prepare_update({"record": deepcopy(record), "current_scene": source["scene"],
                "selection": {"mode": "faces", "uses": [{"placement_id": item["placement_id"]}
                                                         for item in selection], "obstacles": []}},
                base_executable=base, bridge_executable=bridge)
    after = producer["record"]
    references, roots = [], []
    for label, choice in zip(carrier_ids, selection):
        identifier = choice["placement_id"]
        node = source["nodes"].get("placement:" + str(identifier))
        if node is None:
            _fail("REASSOCIATION_TARGET_ABSENT", "明選的新來源不存在。")
        references.append({"carrierId": label,
                           "pin": {"projectId": project_id, "kind": "placement", "id": identifier,
                                   "incarnation": node["incarnation"]},
                           "unknownReason": None if source["active"] else "ledger-inactive"})
        if source["active"]:
            roots.append({"role": "use", "kind": "placement", "id": identifier, "incarnation": node["incarnation"]})
    if roots:
        after["sourceIdentity"] = {"schema": "model-source-identity/1", "roots": roots}
    old_core = {key: value for key, value in record.items() if key != "sourceIdentity"}
    new_core = {key: value for key, value in after.items() if key != "sourceIdentity"}
    same = canonical_bytes(old_core) == canonical_bytes(new_core) and all(
        row["status"] == "continuous" and choice["placement_id"] == row["id"]
        for row, choice in zip(comparison, selection))
    if same:
        after = deepcopy(record)
    # This is a proposed new-data decision, not a history mutation. Even an
    # unknown/equal-geometry manual choice must retain its unknown old facts.
    changed = not same
    model_update._record(after)
    old_frames = _frames(record["input"]["base_scene"], base)
    new_frames = _frames(source["scene"], base)
    frames = [{"carrierId": label, "before": old_frames[old["placement_id"]],
               "after": new_frames[choice["placement_id"]],
               "orientation": choice["orientation"], "purpose": choice["purpose"]}
              for label, old, choice in zip(carrier_ids, record["input"]["uses"], selection)]
    if runtime != _runtime(base, bridge):
        _fail("REASSOCIATION_RUNTIME", "候選產生期間執行版本改變。", status="UNSUPPORTED", clause="I32")
    draft = {"schema": SCHEMA, "requiredCapabilities": [CAPABILITY],
             "candidateNotSaveable": True, "committed": False, "authority": deepcopy(AUTHORITY),
             "beforeRaw": record_raw.decode("utf-8"), "beforeSha256": _sha(record_raw),
             "source": {"projectId": project_id, "recordProjectId": record_project_id,
                        "scene": source_scene, "sha256": _sha(source_scene.encode("utf-8"))},
             "carrierIds": deepcopy(carrier_ids), "selection": deepcopy(selection),
             "comparison": comparison, "frames": frames, "record": after,
             "currentReferences": references, "contract": runtime, "changed": changed}
    if len(canonical_bytes(draft)) > MAX_DRAFT_BYTES:
        _fail("REASSOCIATION_DRAFT_CAPACITY", "完整候選超過 16 MiB，不能截斷來源或足跡。", status="UNSUPPORTED", clause="I33")
    return draft


def validate_candidate(candidate, record_raw, source_scene, *, project_id, record_project_id=None,
                       base_executable=None, bridge_executable=None):
    """Rebuild and compare all draft values against caller-supplied snapshots.

    This proves structural and native replay consistency, NOT current App
    identity, elapsed revisions, same-byte ABA freshness, or user consent.
    Callers must not convert True into permission to publish or save.
    """
    if type(candidate) is not dict or len(canonical_bytes(candidate)) > MAX_DRAFT_BYTES:
        _fail("REASSOCIATION_DRAFT_SHAPE", "候選須完整且在宣告容量內。")
    _keys(candidate, ("schema", "requiredCapabilities", "candidateNotSaveable", "committed", "authority",
                      "beforeRaw", "beforeSha256", "source", "carrierIds", "selection", "comparison", "frames",
                      "record", "currentReferences", "contract", "changed"))
    expected = prepare_candidate(record_raw, source_scene, candidate["selection"], project_id=project_id,
                                 record_project_id=record_project_id, carrier_ids=candidate["carrierIds"],
                                 base_executable=base_executable, bridge_executable=bridge_executable)
    if canonical_bytes(expected) != canonical_bytes(candidate):
        _fail("REASSOCIATION_DRAFT_REPLAY", "完整候選、歷史原件、來源見證或逐列新引用不能逐值重播。", clause="I77")
    return True
