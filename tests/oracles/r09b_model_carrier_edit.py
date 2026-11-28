"""S1 independent reference model: carrier selection and ordinary R57 rows.

No product module is imported.  Source sequences are a finite specification,
not a second application history or evidence that the host implements ABA.
The relation checkers do not call the constructors or their validation helpers.
Only a stateless draft is modelled: no save, commit or permanent carrier ID
allocation is inferred from a caller's provisional labels.
"""
from __future__ import annotations

from collections import Counter
from copy import deepcopy
from hashlib import sha256
from itertools import product
import argparse
import json
from pathlib import Path
import re
import subprocess
import sys


STATES = ("unknown", "conflict", "absent", "replaced", "continuous")
COVERED = frozenset(("boundary", "placement", "column", "beam", "timber",
                     "parameter", "parameter-field"))
EVENTS = ("add", "delete", "replace", "same_number_other_kind", "rename",
          "name_back", "activate", "clear", "restore_initial", "load_swapped",
          "undo", "redo")
PURPOSES = ("boundary", "calculation-cap")


class OracleError(ValueError):
    """A rejected oracle input, kept separate from an assertion failure."""


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":"), allow_nan=False).encode("utf-8")


def _mark(value):
    return (type(value) is str and
            re.fullmatch(r"[0-9a-f]{32}:[1-9][0-9]{0,19}", value) is not None and
            int(value[33:]) <= 2**64 - 1)


def _validate_graph(graph):
    if (type(graph) is not dict or type(graph.get("nodes")) is not dict or
            type(graph.get("data", {}).get("identityLedger", {})) is not dict):
        raise OracleError("S1_SOURCE_SHAPE")
    ledger = graph["data"]["identityLedger"]
    if ledger.get("schema") != "identity-ledger/1" or type(ledger.get("active")) is not bool:
        raise OracleError("S1_SOURCE_LEDGER")
    seen = set()
    for typed, node in graph["nodes"].items():
        # The complete graph can contain compound parameter-field keys.  Root
        # lookup below uses the known ordinary key; never unpack every key.
        if type(typed) is not str or type(node) is not dict:
            raise OracleError("S1_SOURCE_NODE")
        kind = node.get("kind", typed.partition(":")[0])
        covered = kind in COVERED and not (kind == "timber" and node.get("nativeOwner") is not None)
        marker = node.get("incarnation")
        if ledger["active"] and covered:
            if not _mark(marker) or marker in seen:
                raise OracleError("S1_I70_SOURCE_MARK")
            seen.add(marker)
        elif marker is not None:
            raise OracleError("S1_I70_EXTRA_MARK")


def _ordinary_root(root):
    allowed = {"role", "kind", "id", "incarnation", "fieldId", "uncovered",
               "status", "definitionPin", "decision", "confirmed"}
    return (type(root) is dict and not set(root) - allowed and
            root.get("role") in ("placement", "boundary", "use") and
            root.get("kind") in ("placement", "boundary") and
            type(root.get("id")) is int and 0 <= root["id"] <= 2**32 - 1 and
            _mark(root.get("incarnation")) and "uncovered" not in root and
            ("fieldId" not in root or type(root["fieldId"]) is int and root["fieldId"] >= 0) and
            ("status" not in root or root["status"] in STATES))


def classify_rows(identity, live, *, same_project=True):
    """Whole expected judgeRoots rows on the valid ordinary shared domain.

    IdentityLedger.judgeRoots has no project argument.  Its three-way domain
    therefore uses same_project=True; cross-project is an oracle/Python-only
    check and must not be made green by altering the JS input.
    """
    _validate_graph(live)
    if type(identity) is not dict or type(identity.get("roots")) is not list or type(same_project) is not bool:
        raise OracleError("S1_ROOTS_SHAPE")
    rows = []
    for root in identity["roots"]:
        if type(root) is not dict or root.get("kind") not in ("placement", "boundary"):
            raise OracleError("S1_ORDINARY_ROOT_SCOPE")
        endpoint = root["kind"] + ":" + str(root.get("id"))
        current = live["nodes"].get(endpoint)
        marker = current.get("incarnation") if current is not None else None
        row = {**deepcopy(root), "currentIncarnation": marker if _mark(marker) else None,
               "confirmed": False}
        if not same_project or not live["data"]["identityLedger"]["active"] or not _ordinary_root(root):
            row["status"] = "unknown"
        else:
            predicates = (
                (current is not None and current.get("conflict") is True) or
                any(key != endpoint and node.get("incarnation") == root["incarnation"]
                    for key, node in live["nodes"].items()),
                current is None,
                current is not None and marker != root["incarnation"],
                True,
            )
            row["status"] = next(state for state, applies in zip(STATES[1:], predicates) if applies)
            row["definitionPin"] = (current.get("definitionFingerprint") or current.get("definitionPin") or None) if current else None
            row["previousDefinitionPin"] = root.get("definitionPin")
        rows.append(row)
    return rows


def check_rows(identity, live, rows, *, same_project=True):
    """Independent relational checker; no call to classify_rows or validators."""
    assert type(rows) is list and len(rows) == len(identity["roots"]), "S1_CHECK_ROW_COUNT"
    ledger = live["data"]["identityLedger"]
    assert ledger["schema"] == "identity-ledger/1" and type(ledger["active"]) is bool, "S1_CHECK_SOURCE_LEDGER"
    reverse = {}
    for key, node in live["nodes"].items():
        marker = node.get("incarnation")
        kind = node.get("kind", key.partition(":")[0])
        is_covered = kind in {"placement", "boundary", "column", "beam", "timber", "parameter", "parameter-field"}
        is_covered = is_covered and not (kind == "timber" and node.get("nativeOwner") is not None)
        if ledger["active"] and is_covered:
            assert (type(marker) is str and re.fullmatch(r"[0-9a-f]{32}:[1-9][0-9]*", marker) and
                    len(marker) <= 53 and int(marker[33:]) <= 18446744073709551615 and
                    marker not in reverse), "S1_CHECK_I70"
            reverse[marker] = key
        else:
            assert marker is None, "S1_CHECK_I70_EXTRA"
    for old, observed in zip(identity["roots"], rows):
        endpoint = "%s:%s" % (old["kind"], old["id"])
        current = live["nodes"].get(endpoint)
        old_marker = old.get("incarnation")
        valid_old = (type(old_marker) is str and re.fullmatch(r"[0-9a-f]{32}:[1-9][0-9]*", old_marker) is not None
                     and len(old_marker) <= 53 and int(old_marker[33:]) <= 18446744073709551615)
        valid_old = valid_old and not (set(old) - {"role", "kind", "id", "incarnation", "fieldId", "uncovered", "status", "definitionPin", "decision", "confirmed"})
        valid_old = valid_old and old.get("role") in {"placement", "boundary", "use"} and "uncovered" not in old
        valid_old = valid_old and type(old.get("id")) is int and 0 <= old["id"] <= 4294967295
        valid_old = valid_old and ("fieldId" not in old or type(old["fieldId"]) is int and old["fieldId"] >= 0)
        valid_old = valid_old and ("status" not in old or old["status"] in {"unknown", "conflict", "absent", "replaced", "continuous"})
        unknown = not same_project or not ledger["active"] or not valid_old
        elsewhere = valid_old and old_marker in reverse and reverse[old_marker] != endpoint
        conflict = not unknown and (elsewhere or current is not None and current.get("conflict") is True)
        absent = not unknown and not conflict and current is None
        replaced = not unknown and not conflict and not absent and current.get("incarnation") != old_marker
        truths = {"unknown": unknown, "conflict": conflict, "absent": absent, "replaced": replaced,
                  "continuous": not (unknown or conflict or absent or replaced)}
        assert sum(bool(value) for value in truths.values()) == 1, "S1_CHECK_UNIQUE_STATUS"
        assert observed.get("status") in truths and truths[observed["status"]], "S1_CHECK_STATUS"
        marker = current.get("incarnation") if current else None
        valid_current = (type(marker) is str and re.fullmatch(r"[0-9a-f]{32}:[1-9][0-9]*", marker) is not None
                         and len(marker) <= 53 and int(marker[33:]) <= 18446744073709551615)
        expected = deepcopy(old)
        expected.update(status=observed["status"], currentIncarnation=marker if valid_current else None, confirmed=False)
        if not unknown:
            expected["definitionPin"] = (current.get("definitionFingerprint") or current.get("definitionPin") or None) if current else None
            expected["previousDefinitionPin"] = old.get("definitionPin")
        assert canonical(expected) == canonical(observed), "S1_CHECK_ROW_VALUES"
    return True


def _use_valid(use):
    return (type(use) is dict and set(use) == {"placement_id", "orientation", "purpose"} and
            type(use["placement_id"]) is int and 0 <= use["placement_id"] <= 2**32 - 1 and
            type(use["orientation"]) is int and use["orientation"] in (-1, 1) and
            type(use["purpose"]) is str and use["purpose"] in PURPOSES)


def _label_valid(label):
    if type(label) is not str or not label.strip() or "\0" in label:
        return False
    try:
        return len(label.encode("utf-8")) <= 128
    except UnicodeEncodeError:
        return False


def expected_selection(carrier_ids, old_uses, selection):
    """Construct an independently specified full carrier plan or rejection."""
    def reject(code):
        return {"outcome": "rejected", "code": code}
    if (type(old_uses) is not list or not 1 <= len(old_uses) <= 16 or
            any(not _use_valid(use) for use in old_uses) or
            len({use["placement_id"] for use in old_uses}) != len(old_uses)):
        return reject("S1_OLD_USES")
    if (type(carrier_ids) is not list or len(carrier_ids) != len(old_uses) or
            any(not _label_valid(label) for label in carrier_ids) or len(set(carrier_ids)) != len(carrier_ids)):
        return reject("S1_OLD_LABELS")
    if type(selection) is not list or not 1 <= len(selection) <= 16:
        return reject("S1_SELECTION_COUNT")
    seen_labels, seen_targets, rows = set(), set(), []
    old = {label: (index, use) for index, (label, use) in enumerate(zip(carrier_ids, old_uses))}
    for index, choice in enumerate(selection):
        if type(choice) is not dict or set(choice) != {"carrierId", "placement_id", "orientation", "purpose"}:
            return reject("S1_SELECTION_SHAPE")
        label = choice["carrierId"]
        use = {key: deepcopy(choice[key]) for key in ("placement_id", "orientation", "purpose")}
        if not _label_valid(label) or not _use_valid(use):
            return reject("S1_SELECTION_VALUE")
        if label in seen_labels or use["placement_id"] in seen_targets:
            return reject("S1_SELECTION_DUPLICATE")
        seen_labels.add(label)
        seen_targets.add(use["placement_id"])
        before_index, before = old.get(label, (None, None))
        operation = "added" if before is None else "retained" if before["placement_id"] == use["placement_id"] else "retargeted"
        if operation == "retained" and (before["orientation"], before["purpose"]) != (use["orientation"], use["purpose"]):
            return reject("S1_RETAIN_SETTINGS")
        rows.append({"carrierId": label, "operation": operation, "beforeIndex": before_index,
                     "afterIndex": index, "before": deepcopy(before), "after": use})
    removed = [{"carrierId": label, "beforeIndex": index, "before": deepcopy(use)}
               for index, (label, use) in enumerate(zip(carrier_ids, old_uses)) if label not in seen_labels]
    old_order = [label for label in carrier_ids if label in seen_labels]
    new_order = [choice["carrierId"] for choice in selection if choice["carrierId"] in old]
    return {"outcome": "prepared", "rows": rows, "removed": removed,
            "orderChanged": old_order != new_order,
            "uses": [deepcopy(row["after"]) for row in rows],
            "carrierIds": [row["carrierId"] for row in rows]}


def check_selection(carrier_ids, old_uses, selection, observed):
    """Check admission and bijections independently of expected_selection.

    In particular, an invalid request cannot become legal by changing only
    the reported outcome from rejected to prepared (the D1 review countercase).
    """
    bad = False
    before_table = {}
    if type(old_uses) is not list or type(carrier_ids) is not list:
        bad = True
    elif not 1 <= len(old_uses) <= 16 or len(carrier_ids) != len(old_uses):
        bad = True
    else:
        old_targets = []
        for index in range(len(old_uses)):
            label, item = carrier_ids[index], old_uses[index]
            if (type(label) is not str or not label.strip() or "\0" in label or
                    label in before_table):
                bad = True
                continue
            try:
                encoded_label = label.encode("utf-8")
            except UnicodeEncodeError:
                bad = True
                continue
            if len(encoded_label) > 128:
                bad = True
                continue
            if (type(item) is not dict or set(item) != {"placement_id", "orientation", "purpose"} or
                    type(item.get("placement_id")) is not int or not 0 <= item["placement_id"] <= 4294967295 or
                    type(item.get("orientation")) is not int or item["orientation"] not in {1, -1} or
                    type(item.get("purpose")) is not str or item["purpose"] not in {"boundary", "calculation-cap"}):
                bad = True
                continue
            before_table[label] = (index, item)
            old_targets.append(item["placement_id"])
        bad = bad or len(set(old_targets)) != len(old_targets)
    after_table, selected_order = {}, []
    if type(selection) is not list or not 1 <= len(selection) <= 16:
        bad = True
    else:
        selected_targets = []
        for index, item in enumerate(selection):
            if type(item) is not dict or set(item) != {"carrierId", "placement_id", "orientation", "purpose"}:
                bad = True
                continue
            label = item["carrierId"]
            if (type(label) is not str or not label.strip() or "\0" in label or
                    label in after_table):
                bad = True
                continue
            try:
                label_bytes = label.encode("utf-8")
            except UnicodeEncodeError:
                bad = True
                continue
            if len(label_bytes) > 128:
                bad = True
                continue
            if (type(item["placement_id"]) is not int or not 0 <= item["placement_id"] <= 4294967295 or
                    type(item["orientation"]) is not int or item["orientation"] not in {1, -1} or
                    type(item["purpose"]) is not str or item["purpose"] not in {"boundary", "calculation-cap"}):
                bad = True
                continue
            if label in before_table:
                old = before_table[label][1]
                if item["placement_id"] == old["placement_id"] and (item["orientation"] != old["orientation"] or item["purpose"] != old["purpose"]):
                    bad = True
            after_table[label] = (index, item)
            selected_order.append(label)
            selected_targets.append(item["placement_id"])
        bad = bad or len(set(selected_targets)) != len(selected_targets)
    if bad:
        assert observed.get("outcome") == "rejected", "S1_CHECK_ADMISSION_REJECT"
        assert set(observed) == {"outcome", "code"} and type(observed["code"]) is str, "S1_CHECK_REJECTION_SHAPE"
        return True
    assert observed.get("outcome") == "prepared", "S1_CHECK_ADMISSION_ACCEPT"
    assert set(observed) == {"outcome", "rows", "removed", "orderChanged", "uses", "carrierIds"}, "S1_CHECK_PLAN_SHAPE"
    assert observed["carrierIds"] == selected_order, "S1_CHECK_LABEL_ORDER"
    assert type(observed["rows"]) is list and len(observed["rows"]) == len(selection), "S1_CHECK_SELECTION_COUNT"
    assert type(observed["uses"]) is list and len(observed["uses"]) == len(selection), "S1_CHECK_USE_COUNT"
    for index, row in enumerate(observed["rows"]):
        chosen = selection[index]
        label = chosen["carrierId"]
        old_index, old_use = before_table.get(label, (None, None))
        want_kind = "added" if label not in before_table else "retargeted" if chosen["placement_id"] != old_use["placement_id"] else "retained"
        after = {name: deepcopy(chosen[name]) for name in ("placement_id", "orientation", "purpose")}
        expected = {"carrierId": label, "beforeIndex": old_index, "afterIndex": index,
                    "operation": want_kind, "before": old_use, "after": after}
        assert canonical(row) == canonical(expected), "S1_CHECK_ROW_CORRESPONDENCE"
        assert canonical(observed["uses"][index]) == canonical(after), "S1_CHECK_USE_PROJECTION"
    expected_removed = [{"carrierId": label, "beforeIndex": index, "before": old_uses[index]}
                        for index, label in enumerate(carrier_ids) if label not in after_table]
    assert canonical(observed["removed"]) == canonical(expected_removed), "S1_CHECK_REMOVED"
    old_survivors = [label for label in carrier_ids if label in after_table]
    new_survivors = [label for label in selected_order if label in before_table]
    assert observed["orderChanged"] is (old_survivors != new_survivors), "S1_CHECK_REORDER"
    return True


def selection_cases():
    """Exhaust every length 0..3 selection over 3 labels, 3 targets and settings."""
    labels = ["old-A", "old-B"]
    uses = [{"placement_id": 0, "orientation": 1, "purpose": "boundary"},
            {"placement_id": 1, "orientation": -1, "purpose": "calculation-cap"}]
    options = [{"carrierId": label, "placement_id": target, "orientation": sign, "purpose": purpose}
               for label, target, sign, purpose in product(("old-A", "old-B", "new-C"), range(3), (-1, 1), PURPOSES)]
    for length in range(4):
        for choice in product(options, repeat=length):
            yield {"carrier_ids": deepcopy(labels), "old_uses": deepcopy(uses), "selection": deepcopy(list(choice))}


def _fingerprint(name):
    return sha256(name.encode("utf-8")).hexdigest()


def _initial(active):
    nodes = {}
    keys = ("boundary:0", "placement:0", "placement:1", "parameter:9", "parameter-field:9:f2")
    for index, key in enumerate(keys, 1):
        kind, _, identifier = key.partition(":")
        nodes[key] = {"kind": kind, "id": identifier.split(":", 1)[0],
                      "incarnation": "0123456789abcdef0123456789abcdef:" + str(index) if active else None,
                      "definitionFingerprint": _fingerprint(key + ":original"),
                      "valueFingerprint": _fingerprint(key + ":value"), "name": "original"}
    return {"data": {"identityLedger": {"schema": "identity-ledger/1", "active": active}}, "nodes": nodes}


def _run_sources(events, active):
    initial = _initial(active)
    current, past, future, traces = deepcopy(initial), [], [], []
    serial = 5
    for event in events:
        before = deepcopy(current)
        outcome = "observed"
        if event == "undo":
            if past:
                future.append(deepcopy(current))
                current = past.pop()
            else:
                outcome = "no-history"
        elif event == "redo":
            if future:
                past.append(deepcopy(current))
                current = future.pop()
            else:
                outcome = "no-history"
        else:
            after = deepcopy(current)
            nodes = after["nodes"]
            def fresh():
                nonlocal serial
                serial += 1
                return "0123456789abcdef0123456789abcdef:" + str(serial) if after["data"]["identityLedger"]["active"] else None
            if event == "delete":
                nodes.pop("placement:0", None)
            elif event in ("replace", "add", "same_number_other_kind"):
                key = "placement:0" if event == "replace" else "placement:2" if event == "add" else "boundary:2"
                if event == "replace" or key not in nodes:
                    kind, _, identifier = key.partition(":")
                    nodes[key] = {"kind": kind, "id": identifier, "incarnation": fresh(), "name": "original",
                                  "definitionFingerprint": _fingerprint(key + ":original"),
                                  "valueFingerprint": _fingerprint(key + ":value")}
            elif event in ("rename", "name_back"):
                if "placement:0" in nodes:
                    name = "renamed" if event == "rename" else "original"
                    nodes["placement:0"]["name"] = name
                    nodes["placement:0"]["definitionFingerprint"] = _fingerprint("placement:0:" + name)
            elif event == "activate":
                if not after["data"]["identityLedger"]["active"]:
                    after["data"]["identityLedger"]["active"] = True
                    kind_order = {kind: index for index, kind in enumerate(("boundary", "placement", "column", "beam", "timber", "parameter", "parameter-field"))}
                    for key in sorted(nodes, key=lambda key: (kind_order[nodes[key]["kind"]], int(nodes[key]["id"]), key)):
                        nodes[key]["incarnation"] = fresh()
                else:
                    outcome = "rejected-already-active"
            elif event == "clear":
                after["nodes"] = {}
            elif event in ("restore_initial", "load_swapped"):
                # External complete snapshot restore, not a native edit that
                # purports to move existing incarnation marks between keys.
                after = deepcopy(initial)
                if event == "load_swapped" and active:
                    a, b = after["nodes"]["placement:0"], after["nodes"]["placement:1"]
                    a["incarnation"], b["incarnation"] = b["incarnation"], a["incarnation"]
            else:
                raise OracleError("S1_UNKNOWN_EVENT")
            if canonical(after) != canonical(before):
                past.append(before)
                future.clear()
                current = after
        traces.append({"event": event, "outcome": outcome, "before": before, "after": deepcopy(current)})
    return initial, current, traces


def check_source_trace(initial, trace):
    """Transition relations, independently tracking undo/redo snapshots."""
    current, past, future, seen_marks = deepcopy(initial), [], [], set()
    seen_marks.update(node["incarnation"] for node in initial["nodes"].values() if node["incarnation"] is not None)
    for step in trace:
        event, before, after = step["event"], step["before"], step["after"]
        assert canonical(current) == canonical(before), "S1_CHECK_TRACE_CHAIN"
        bnodes, anodes = before["nodes"], after["nodes"]
        if event in ("undo", "redo"):
            origin, destination = (past, future) if event == "undo" else (future, past)
            expected = origin.pop() if origin else before
            assert canonical(after) == canonical(expected), "S1_CHECK_HISTORY_RESTORE"
            if canonical(after) != canonical(before):
                destination.append(deepcopy(before))
        else:
            if event not in ("activate", "restore_initial", "load_swapped"):
                assert before["data"] == after["data"], "S1_CHECK_ACTIVE_PRESERVED"
            if event == "delete":
                assert set(anodes) == set(bnodes) - {"placement:0"}, "S1_CHECK_DELETE"
                assert all(anodes[key] == bnodes[key] for key in anodes), "S1_CHECK_DELETE_OTHER"
            elif event in ("add", "replace", "same_number_other_kind"):
                key = {"add": "placement:2", "replace": "placement:0", "same_number_other_kind": "boundary:2"}[event]
                assert set(anodes) == set(bnodes) | {key}, "S1_CHECK_NEW_TYPED_KEY"
                assert all(anodes[other] == bnodes[other] for other in bnodes if other != key), "S1_CHECK_NEW_OTHER"
                if event != "replace" and key in bnodes:
                    assert anodes[key] == bnodes[key], "S1_CHECK_REDECLARE_NO_CHANGE"
                elif after["data"]["identityLedger"]["active"]:
                    assert anodes[key]["incarnation"] not in seen_marks, "S1_CHECK_NEW_EXISTENCE"
                else:
                    assert anodes[key]["incarnation"] is None, "S1_CHECK_NO_IMPLICIT_ACTIVATION"
            elif event in ("rename", "name_back"):
                assert set(anodes) == set(bnodes), "S1_CHECK_NAME_KEYS"
                for key in bnodes:
                    assert anodes[key]["incarnation"] == bnodes[key]["incarnation"], "S1_CHECK_NAME_IDENTITY"
                    if key != "placement:0":
                        assert anodes[key] == bnodes[key], "S1_CHECK_NAME_OTHER"
                    else:
                        target_name = "renamed" if event == "rename" else "original"
                        assert anodes[key]["name"] == target_name, "S1_CHECK_NAME_VALUE"
                        assert anodes[key]["definitionFingerprint"] == sha256((key + ":" + target_name).encode()).hexdigest(), "S1_CHECK_NAME_PIN"
                        assert anodes[key]["valueFingerprint"] == bnodes[key]["valueFingerprint"], "S1_CHECK_NAME_EFFECTIVE"
            elif event == "clear":
                assert not anodes, "S1_CHECK_CLEAR"
            elif event == "activate":
                assert after["data"]["identityLedger"]["active"] is True and set(anodes) == set(bnodes), "S1_CHECK_ACTIVATE"
                if before["data"]["identityLedger"]["active"]:
                    assert step["outcome"] == "rejected-already-active", "S1_CHECK_ACTIVATE_REJECTION"
                    assert canonical(after) == canonical(before), "S1_CHECK_ACTIVATE_ALREADY"
                else:
                    for key in bnodes:
                        assert anodes[key]["incarnation"] not in seen_marks, "S1_CHECK_ACTIVATE_FRESH"
                        assert {k: v for k, v in anodes[key].items() if k != "incarnation"} == {k: v for k, v in bnodes[key].items() if k != "incarnation"}, "S1_CHECK_ACTIVATE_GEOMETRY"
            elif event == "restore_initial":
                assert canonical(after) == canonical(initial), "S1_CHECK_EXTERNAL_RESTORE"
            elif event == "load_swapped":
                expected = deepcopy(initial)
                if expected["data"]["identityLedger"]["active"]:
                    expected["nodes"]["placement:0"]["incarnation"] = initial["nodes"]["placement:1"]["incarnation"]
                    expected["nodes"]["placement:1"]["incarnation"] = initial["nodes"]["placement:0"]["incarnation"]
                assert canonical(after) == canonical(expected), "S1_CHECK_EXTERNAL_CONFLICT"
            else:
                raise AssertionError("S1_CHECK_EVENT")
            if canonical(after) != canonical(before):
                past.append(deepcopy(before))
                future.clear()
        seen_marks.update(node["incarnation"] for node in anodes.values() if node["incarnation"] is not None)
        current = deepcopy(after)
    return True


def sequence_cases(depth=3):
    """Every word of length 0..depth over EVENTS, starting active/inactive.

    Graphs retain a three-segment parameter-field key outside the roots.  The
    swapped snapshot is a legal I70 input used to diagnose inconsistent old
    pins, never claimed to be a legal operation moving marks in a live World.
    """
    if type(depth) is not int or not 0 <= depth <= 3:
        raise OracleError("S1_SCAN_DEPTH")
    for active in (False, True):
        for length in range(depth + 1):
            for events in product(EVENTS, repeat=length):
                initial, graph, trace = _run_sources(events, active)
                check_source_trace(initial, trace)
                roots = []
                for kind, identifier in (("placement", 0), ("placement", 1), ("boundary", 0), ("placement", 2)):
                    node = initial["nodes"].get(kind + ":" + str(identifier))
                    roots.append({"role": "use" if kind == "placement" else "boundary", "kind": kind,
                                  "id": identifier, "incarnation": node["incarnation"] if node else None,
                                  "definitionPin": node["definitionFingerprint"] if node else None})
                yield {"identity": {"schema": "model-source-identity/1", "roots": roots},
                       "graph": graph, "same_project": True, "events": list(events), "initial_active": active}


def _probe_fixture(name):
    if name.startswith("state_"):
        event = {"state_conflict": "load_swapped", "state_absent": "delete",
                 "state_replaced": "replace", "state_unknown": "activate",
                 "state_current_mark": "replace", "state_definition_pin": "rename"}[name]
        active = name != "state_unknown"
        initial, graph, _ = _run_sources((event,), active)
        root = {"role": "use", "kind": "placement", "id": 0,
                "incarnation": initial["nodes"]["placement:0"]["incarnation"],
                "definitionPin": initial["nodes"]["placement:0"]["definitionFingerprint"]}
        identity = {"schema": "model-source-identity/1", "roots": [root]}
        observed = classify_rows(identity, graph)
        return (identity, graph), observed
    labels = ["old-A", "old-B"]
    uses = [{"placement_id": 0, "orientation": 1, "purpose": "boundary"},
            {"placement_id": 1, "orientation": -1, "purpose": "calculation-cap"}]
    rows = [{"carrierId": label, **deepcopy(use)} for label, use in zip(labels, uses)]
    if name == "carrier_empty":
        rows = []
    elif name == "carrier_duplicate_target":
        rows[1]["placement_id"] = 0
    elif name == "carrier_missing_settings":
        rows.append({"carrierId": "new-C", "placement_id": 2, "purpose": "boundary"})
    elif name == "carrier_capacity":
        rows = [{"carrierId": "new-" + str(index), "placement_id": index,
                 "orientation": 1, "purpose": "boundary"} for index in range(17)]
    elif name == "carrier_surrogate_old":
        labels[0] = "old-\ud800"
    elif name == "carrier_surrogate_new":
        rows.append({"carrierId": "new-\udfff", "placement_id": 2,
                     "orientation": 1, "purpose": "boundary"})
    elif name in ("carrier_reorder", "carrier_settings"):
        rows.reverse()
    elif name == "carrier_removed":
        rows.pop()
    elif name == "carrier_target":
        rows[0]["placement_id"] = 2
    elif name == "carrier_old_index":
        rows.reverse()
    else:
        raise OracleError("S1_PROBE_NAME")
    return (labels, uses, rows), expected_selection(labels, uses, rows)


PROBES = {
    "state_conflict": "S1_CHECK_STATUS", "state_absent": "S1_CHECK_STATUS",
    "state_replaced": "S1_CHECK_STATUS", "state_unknown": "S1_CHECK_STATUS",
    "state_current_mark": "S1_CHECK_ROW_VALUES", "state_definition_pin": "S1_CHECK_ROW_VALUES",
    "carrier_empty": "S1_CHECK_ADMISSION_REJECT", "carrier_duplicate_target": "S1_CHECK_ADMISSION_REJECT",
    "carrier_missing_settings": "S1_CHECK_ADMISSION_REJECT", "carrier_reorder": "S1_CHECK_REORDER",
    "carrier_capacity": "S1_CHECK_ADMISSION_REJECT",
    "carrier_surrogate_old": "S1_CHECK_ADMISSION_REJECT",
    "carrier_surrogate_new": "S1_CHECK_ADMISSION_REJECT",
    "carrier_settings": "S1_CHECK_ROW_CORRESPONDENCE", "carrier_removed": "S1_CHECK_REMOVED",
    "carrier_target": "S1_CHECK_ROW_CORRESPONDENCE", "carrier_old_index": "S1_CHECK_ROW_CORRESPONDENCE",
}


def run_probe(name, phase):
    inputs, result = _probe_fixture(name)
    if phase == "withdraw":
        if name in ("state_conflict", "state_absent", "state_replaced", "state_unknown"):
            result[0]["status"] = "continuous"
        elif name == "state_current_mark":
            result[0]["currentIncarnation"] = result[0]["incarnation"]
        elif name == "state_definition_pin":
            result[0]["definitionPin"] = result[0]["previousDefinitionPin"]
        elif name in ("carrier_empty", "carrier_duplicate_target", "carrier_missing_settings", "carrier_capacity",
                      "carrier_surrogate_old", "carrier_surrogate_new"):
            result = {"outcome": "prepared", "rows": [], "removed": [], "orderChanged": False,
                      "uses": [], "carrierIds": []}
        elif name == "carrier_reorder":
            result["orderChanged"] = False
        elif name == "carrier_settings":
            result["rows"][0]["after"]["orientation"] = 1
        elif name == "carrier_removed":
            result["removed"] = []
        elif name == "carrier_target":
            result["rows"][0]["after"]["placement_id"] = 0
        elif name == "carrier_old_index":
            result["rows"][0]["beforeIndex"] = 0
    try:
        if name.startswith("state_"):
            check_rows(*inputs, result)
        else:
            check_selection(*inputs, result)
    except AssertionError as exc:
        print("ASSERTION " + str(exc), file=sys.stderr)
        return 1
    print("S1_ORACLE_PROBE " + name + " " + phase + " PASS")
    return 0


def negative_controls():
    result = []
    for name, assertion in PROBES.items():
        runs = []
        for phase in ("baseline", "withdraw", "restore"):
            cmd = [sys.executable, "-B", str(Path(__file__).resolve()), "--probe", name, "--phase", phase]
            child = subprocess.run(cmd, capture_output=True, text=True, timeout=30, check=False)
            runs.append({"command": cmd, "exit": child.returncode, "stdout": child.stdout, "stderr": child.stderr})
        assert [run["exit"] for run in runs] == [0, 1, 0], "S1_ORACLE_NEGATIVE_EXITS:" + name
        assert runs[1]["stderr"] == "ASSERTION " + assertion + "\n", "S1_ORACLE_NEGATIVE_NAMED:" + name
        assert not runs[0]["stderr"] and not runs[2]["stderr"], "S1_ORACLE_NEGATIVE_CLEAN:" + name
        result.append({"id": name, "assertion": assertion, "runs": runs})
    return result


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--probe", choices=tuple(PROBES))
    parser.add_argument("--phase", choices=("baseline", "withdraw", "restore"), default="baseline")
    parser.add_argument("--depth", type=int, default=3)
    args = parser.parse_args(argv)
    if args.probe:
        return run_probe(args.probe, args.phase)
    states, source_digest, selection_digest = Counter(), sha256(), sha256()
    source_count = selection_count = accepted = 0
    for case in sequence_cases(args.depth):
        before = canonical(case)
        rows = classify_rows(case["identity"], case["graph"], same_project=case["same_project"])
        check_rows(case["identity"], case["graph"], rows, same_project=case["same_project"])
        assert canonical(case) == before, "S1_ORACLE_SOURCE_INPUT_UNCHANGED"
        source_digest.update(canonical([case, rows]))
        states.update(row["status"] for row in rows)
        source_count += 1
    for case in selection_cases():
        before = canonical(case)
        outcome = expected_selection(**case)
        check_selection(**case, observed=outcome)
        assert canonical(case) == before, "S1_ORACLE_SELECTION_INPUT_UNCHANGED"
        selection_digest.update(canonical([case, outcome]))
        selection_count += 1
        accepted += outcome["outcome"] == "prepared"
    print(json.dumps({"schema": "r09b-model-carrier-oracle-scan/1", "depth": args.depth,
                      "source_cases": source_count, "source_rows": sum(states.values()),
                      "states": dict(sorted(states.items())), "source_sha256": source_digest.hexdigest(),
                      "selection_cases": selection_count, "selection_prepared": accepted,
                      "selection_rejected": selection_count - accepted,
                      "selection_sha256": selection_digest.hexdigest(),
                      "negative_controls": negative_controls()}, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
