"""R09b D2/S1: native-backed, stateless ordinary-faces carrier drafts.

This module computes a complete replacement projection.  It does not own a
project, allocate permanent carrier IDs, commit, save, or maintain history.
Old row labels and project membership are explicit caller assertions.  The
draft cannot be used as an I77 saved record or as permission to publish.
"""
from __future__ import annotations

from copy import deepcopy
import hashlib
from pathlib import Path

import model_update
import source_reassociation as reassociation
import space_modeling
from modeling import ModelError, canonical_bytes


CAPABILITY = "model-carrier-edit/1"
SCHEMA = "geometry-model-carrier-draft/1"
MAX_FACES = 16
MAX_LABEL_BYTES = 128
MAX_DRAFT_BYTES = 16 * 1024 * 1024
MAX_REQUEST_BYTES = 8 * 1024 * 1024
MODULE_PATH = Path(__file__).resolve()
LOADED_SHA = hashlib.sha256(MODULE_PATH.read_bytes().replace(b"\r\n", b"\n")).hexdigest()
AUTHORITY = {"project": "caller-asserted", "history": "unverified",
             "confirmation": False, "carrierIds": "caller-provisional"}


def _fail(code, message, *, status="INVALID", clause="I76"):
    raise ModelError(status, code, clause, message)


def _sha(raw):
    return hashlib.sha256(raw).hexdigest()


def _keys(value, expected):
    if type(value) is not dict or set(value) != set(expected):
        _fail("CARRIER_EDIT_SHAPE", "載體欄位必須完整明示，不能略過未知欄位。")


def _label(value):
    if type(value) is not str:
        _fail("CARRIER_EDIT_LABEL", "暫態列標籤須為非空 UTF-8 文字。", clause="D65")
    try:
        size = len(value.encode("utf-8"))
    except UnicodeEncodeError:
        _fail("CARRIER_EDIT_LABEL", "暫態列標籤不是合法 UTF-8。", clause="D65")
    if not value.strip() or "\0" in value or size > MAX_LABEL_BYTES:
        _fail("CARRIER_EDIT_LABEL", "暫態列標籤須非空且不超過 128 個 UTF-8 bytes。", clause="D65")


def _use(value, *, selected=False):
    _keys(value, ("carrierId", "placement_id", "orientation", "purpose") if selected else
          ("placement_id", "orientation", "purpose"))
    if type(value["placement_id"]) is not int or not 0 <= value["placement_id"] <= 0xFFFFFFFF:
        _fail("CARRIER_EDIT_TARGET", "承載面編號須為 uint32 整數，合法零號不可丟棄。", clause="I75")
    if type(value["orientation"]) is not int or value["orientation"] not in (-1, 1):
        _fail("CARRIER_EDIT_ORIENTATION", "必須明選 +1 或 -1 朝向，不猜預設。")
    if type(value["purpose"]) is not str or value["purpose"] not in ("boundary", "calculation-cap"):
        _fail("CARRIER_EDIT_PURPOSE", "必須明選 boundary 或 calculation-cap 用途，不猜預設。")
    if selected:
        _label(value["carrierId"])


def capabilities():
    return {"schema": "geometry-model-carrier-helper/1", "complete": False,
            "draftCapability": CAPABILITY, "consumers": ["ordinary-faces"],
            "commit": False, "save": False, "history": False,
            "permanentCarrierAllocation": False, "automaticReceiptKinds": [],
            "authority": deepcopy(AUTHORITY),
            "capacities": {"faces": MAX_FACES, "carrierLabelBytes": MAX_LABEL_BYTES,
                           "requestBytes": MAX_REQUEST_BYTES, "draftBytes": MAX_DRAFT_BYTES,
                           "recordBytes": reassociation.MAX_RECORD_BYTES,
                           "sceneBytes": model_update.MAX_SCENE_BYTES}}


def judge_roots(identity, live, *, same_project=True):
    """Reuse D1's R57 calculation; its complete/I70-checked domain is required.

    ``prepare_candidate`` obtains that premise from the native reader.  This
    pure helper alone cannot establish source completeness or project scope.
    """
    return reassociation.judge_roots(identity, live, same_project=same_project)


def plan_selection(carrier_ids, old_uses, selection):
    """Pair every selected row by its caller-supplied label, never by index.

    An omitted old label is an explicit removal from this full selection.
    A new label is only provisional: no persisted allocator is implemented.
    Empty editing state is permitted in a future UI, but cannot be evaluated
    as an effective faces model by this operation.
    """
    if type(old_uses) is not list or not 1 <= len(old_uses) <= MAX_FACES:
        _fail("CARRIER_EDIT_OLD_CAPACITY", "舊普通面模型必須有 1 至 16 列。", status="UNSUPPORTED", clause="I33")
    if type(carrier_ids) is not list or len(carrier_ids) != len(old_uses):
        _fail("CARRIER_EDIT_LABELS", "必須明示與全部舊列逐列對應的暫態標籤。", clause="D65")
    for label in carrier_ids:
        _label(label)
    if len(set(carrier_ids)) != len(carrier_ids):
        _fail("CARRIER_EDIT_DUPLICATE_LABEL", "同一模型中的列標籤不得重複。", clause="D65")
    for use in old_uses:
        _use(use)
    if len({use["placement_id"] for use in old_uses}) != len(old_uses):
        _fail("CARRIER_EDIT_OLD_DUPLICATE_TARGET", "舊模型的承載面不可重複。")
    if type(selection) is not list:
        _fail("CARRIER_EDIT_SELECTION", "請明選完整的新載體清單。")
    if not selection:
        _fail("CARRIER_EDIT_EMPTY", "零列只能是編輯草稿，不能形成有效模型。")
    if len(selection) > MAX_FACES:
        _fail("CARRIER_EDIT_CAPACITY", "本片最多 16 個承載面，超限整筆拒絕。", status="UNSUPPORTED", clause="I33")
    old_by_label = {label: (index, use) for index, (label, use) in enumerate(zip(carrier_ids, old_uses))}
    labels, targets, rows = set(), set(), []
    for index, choice in enumerate(selection):
        _use(choice, selected=True)
        label, target = choice["carrierId"], choice["placement_id"]
        if label in labels:
            _fail("CARRIER_EDIT_DUPLICATE_LABEL", "同一模型中的列標籤不得重複。", clause="D65")
        if target in targets:
            _fail("CARRIER_EDIT_DUPLICATE_TARGET", "同一承載面不得重複納入。")
        labels.add(label)
        targets.add(target)
        old_index, old = old_by_label.get(label, (None, None))
        operation = "added" if old is None else "retained" if old["placement_id"] == target else "retargeted"
        if operation == "retained" and (choice["orientation"] != old["orientation"] or
                                        choice["purpose"] != old["purpose"]):
            _fail("CARRIER_EDIT_RETAINED_SETTINGS", "保留列的設定須隨列鍵保留；本片不另改同目標設定。")
        rows.append({"carrierId": label, "operation": operation,
                     "beforeIndex": old_index, "afterIndex": index,
                     "before": deepcopy(old), "after": {key: deepcopy(choice[key]) for key in
                                                          ("placement_id", "orientation", "purpose")}})
    removed = [{"carrierId": label, "beforeIndex": index, "before": deepcopy(use)}
               for index, (label, use) in enumerate(zip(carrier_ids, old_uses)) if label not in labels]
    old_order = [label for label in carrier_ids if label in labels]
    new_order = [row["carrierId"] for row in rows if row["carrierId"] in old_by_label]
    return {"rows": rows, "removed": removed, "orderChanged": old_order != new_order}


def _runtime(base, bridge):
    try:
        actual = _sha(MODULE_PATH.read_bytes().replace(b"\r\n", b"\n"))
    except OSError:
        actual = None
    if actual != LOADED_SHA:
        _fail("CARRIER_EDIT_RUNTIME", "載體執行器已改變，請重新啟動。", status="UNSUPPORTED", clause="I32")
    return {**reassociation._runtime(base, bridge), "carrier_edit_sha256": actual}


def _fixed_sources(record, source_scene, plan, bridge):
    """Keep the existing fixed-source guards separately for every kept label.

    A singleton root gives _protected the same selected-root normalization on
    each side without its selected-use:index labels transferring settings
    between reordered carriers.  Other typed endpoints remain exact.  An
    explicit added/removed carrier may add/remove its dependencies, but may
    not mask a version or field/topology change on another retained carrier.
    """
    old_graph = model_update._graph(record["input"]["base_scene"], bridge)
    new_graph = model_update._graph(source_scene, bridge)
    for row in plan["rows"]:
        if row["before"] is None:
            # New roots still need a complete, supported fixed-source closure.
            model_update._protected(new_graph, {"mode": "faces", "uses": [row["after"]], "obstacles": []})
            continue
        old_fixed, old_paths = model_update._protected(
            old_graph, {"mode": "faces", "uses": [row["before"]], "obstacles": []})
        new_fixed, new_paths = model_update._protected(
            new_graph, {"mode": "faces", "uses": [row["after"]], "obstacles": []})
        model_update._fixed_versions(old_fixed, new_fixed)
        model_update._fixed_associations(old_paths, new_paths)


def _frame_rows(plan, old_frames, new_frames):
    rows = []
    for row in plan["rows"]:
        old, new = row["before"], row["after"]
        before = old_frames.get(old["placement_id"]) if old is not None else None
        after = new_frames.get(new["placement_id"])
        if after is None or old is not None and before is None:
            _fail("CARRIER_EDIT_TARGET_ABSENT", "明選承載面缺少可完整求值的世界框架。", clause="D4")
        old_orientation = old["orientation"] if old is not None else None
        rows.append({"carrierId": row["carrierId"], "before": deepcopy(before), "after": deepcopy(after),
                     "beforeOrientation": old_orientation, "afterOrientation": new["orientation"],
                     "beforeEffectiveNormal": [old_orientation * value for value in before["n"]]
                     if before is not None else None,
                     "afterEffectiveNormal": [new["orientation"] * value for value in after["n"]]})
    return rows


def prepare_candidate(record_raw, source_scene, selection, *, project_id, carrier_ids,
                      record_project_id=None, base_executable=None, bridge_executable=None):
    """Compute one complete draft from verified old and new native snapshots.

    ``geometryRecord`` is a projection for replay, not a new persistent record
    format.  Its identity-free inputs are the only geometry inputs.  The
    unchanged old bytes and proposed current references remain separate; this
    does not choose a future stored sourceIdentity/trail encoding.
    """
    # Check scalar types before serializing potentially large caller objects.
    if type(record_raw) is not bytes or type(source_scene) is not str:
        _fail("CARRIER_EDIT_REQUEST", "舊紀錄須為 bytes，完整來源須為文字。")
    try:
        source_bytes = source_scene.encode("utf-8")
    except UnicodeEncodeError:
        _fail("CARRIER_EDIT_REQUEST", "完整來源不是合法 UTF-8。")
    if len(record_raw) > reassociation.MAX_RECORD_BYTES or len(source_bytes) > model_update.MAX_SCENE_BYTES:
        _fail("CARRIER_EDIT_REQUEST_CAPACITY", "舊紀錄或來源超過既有容量。", status="UNSUPPORTED", clause="I33")
    try:
        request_bytes = len(record_raw) + len(canonical_bytes({"source_scene": source_scene,
            "selection": selection, "carrier_ids": carrier_ids, "project_id": project_id,
            "record_project_id": record_project_id}))
    except UnicodeEncodeError:
        _fail("CARRIER_EDIT_REQUEST", "選擇或上下文不是合法 UTF-8。")
    if request_bytes > MAX_REQUEST_BYTES:
        _fail("CARRIER_EDIT_REQUEST_CAPACITY", "完整載體更新請求超過 8 MiB。", status="UNSUPPORTED", clause="I33")
    record, source, comparison, base, bridge, context_runtime = reassociation._context(
        record_raw, source_scene, project_id, record_project_id, base_executable, bridge_executable)
    runtime = _runtime(base, bridge)
    if context_runtime != {key: value for key, value in runtime.items() if key != "carrier_edit_sha256"}:
        _fail("CARRIER_EDIT_RUNTIME", "讀取舊紀錄與來源期間執行版本改變。", status="UNSUPPORTED", clause="I32")
    if record_project_id is not None and record_project_id != project_id:
        _fail("CARRIER_EDIT_IMPORT", "本片不處理跨專案匯入對照，也不追認舊身分。", status="UNSUPPORTED", clause="I75")
    plan = plan_selection(carrier_ids, record["input"]["uses"], selection)
    for row in plan["rows"]:
        if "placement:" + str(row["after"]["placement_id"]) not in source["nodes"]:
            _fail("CARRIER_EDIT_TARGET_ABSENT", "明選的新承載面不存在；不以其他型別的同號物件替代。", clause="I75")
    inputs = {"mode": "faces", "base_scene": source["scene"],
              "uses": [deepcopy(row["after"]) for row in plan["rows"]], "obstacles": []}
    _fixed_sources(record, source["scene"], plan, bridge)
    # The original producer determines every necessary package and its status.
    # An open surface-set is legal; an unavailable optional volume remains null.
    result = space_modeling.preview(inputs, base_executable=base)
    projection = {"id": record["id"], "name": record["name"], "created_at": record["created_at"],
                  "source": {"kind": "scene", "placement_id": None, "boundary_id": None,
                             "scene_hash": result["source_sha256"]},
                  "input": inputs, "result": result}
    model_update._record(projection)
    references = []
    for row in plan["rows"]:
        identifier = row["after"]["placement_id"]
        node = source["nodes"]["placement:" + str(identifier)]
        references.append({"carrierId": row["carrierId"],
                           "pin": {"projectId": project_id, "kind": "placement", "id": identifier,
                                   "incarnation": node["incarnation"]},
                           "unknownReason": None if source["active"] else "ledger-inactive"})
    frames = _frame_rows(plan, reassociation._frames(record["input"]["base_scene"], base),
                         reassociation._frames(source["scene"], base))
    old_projection = {key: deepcopy(value) for key, value in record.items() if key != "sourceIdentity"}
    original_selection = [{"carrierId": label, **deepcopy(use)}
                          for label, use in zip(carrier_ids, record["input"]["uses"])]
    draft = {"schema": SCHEMA, "requiredCapabilities": [reassociation.CAPABILITY, CAPABILITY],
             "candidateNotSaveable": True, "committed": False, "authority": deepcopy(AUTHORITY),
             "beforeRaw": record_raw.decode("utf-8"), "beforeSha256": _sha(record_raw),
             "source": {"projectId": project_id, "recordProjectId": record_project_id,
                        "scene": source_scene, "sha256": _sha(source_scene.encode("utf-8"))},
             "carrierIds": deepcopy(carrier_ids), "selection": deepcopy(selection), "plan": plan,
             "comparison": [{"carrierId": label, **deepcopy(row)} for label, row in zip(carrier_ids, comparison)],
             "frames": frames, "geometryRecord": projection, "currentReferences": references,
             "impact": {"carrierListChanged": canonical_bytes(original_selection) != canonical_bytes(selection),
                        "geometryChanged": canonical_bytes(old_projection) != canonical_bytes(projection),
                        "nonContinuousCarrierIds": [label for label, row in zip(carrier_ids, comparison)
                                                    if row["status"] != "continuous"]},
             "contract": runtime}
    if len(canonical_bytes(draft)) > MAX_DRAFT_BYTES:
        _fail("CARRIER_EDIT_DRAFT_CAPACITY", "完整候選超過 16 MiB，不截斷來源或足跡。", status="UNSUPPORTED", clause="I33")
    if runtime != _runtime(base, bridge):
        _fail("CARRIER_EDIT_RUNTIME", "產生候選期間執行版本改變。", status="UNSUPPORTED", clause="I32")
    return draft


def validate_candidate(candidate, record_raw, source_scene, selection, *, project_id, carrier_ids,
                       record_project_id=None, base_executable=None, bridge_executable=None):
    """Rebuild from independently supplied original choices and compare all bytes.

    A self-consistent draft for a different choice is not this caller's draft.
    Success proves replay consistency, never App epoch, consent or commitment.
    """
    if type(candidate) is not dict or len(canonical_bytes(candidate)) > MAX_DRAFT_BYTES:
        _fail("CARRIER_EDIT_DRAFT_SHAPE", "候選須完整且在宣告容量內。")
    expected = prepare_candidate(record_raw, source_scene, selection, project_id=project_id,
                                 carrier_ids=carrier_ids, record_project_id=record_project_id,
                                 base_executable=base_executable, bridge_executable=bridge_executable)
    if canonical_bytes(candidate) != canonical_bytes(expected):
        _fail("CARRIER_EDIT_DRAFT_REPLAY", "候選與外部原明選、舊原件、完整來源或原生結果不一致。", clause="I77")
    return True
