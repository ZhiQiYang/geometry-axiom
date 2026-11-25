"""Independent R09b reference evaluator and relation checker (no product imports).

The finite sequence model specifies future host transactions, not capabilities
of the stateless D1 helper.  Its history/generation are abstract inputs to the
specification: a successful scan is not evidence that App ABA is implemented.
"""
from collections import Counter
from copy import deepcopy
from hashlib import sha256
from itertools import product
import json
import re
import subprocess
import sys


KINDS = frozenset(("boundary", "placement", "column", "beam", "timber",
                   "parameter", "parameter-field"))
STATES = ("unknown", "conflict", "absent", "replaced", "continuous")
EPOCH = "0123456789abcdef0123456789abcdef"


class OracleError(ValueError):
    pass


def key(item):
    kind, identity = item.get("kind"), item.get("id")
    if kind not in KINDS or type(identity) is not int or not 0 <= identity <= 2**32 - 1:
        raise OracleError("I75_TYPED_ENDPOINT")
    if kind == "parameter-field":
        field = item.get("fieldId")
        if type(field) is not int or not 0 <= field <= 2**32 - 1:
            raise OracleError("I75_TYPED_ENDPOINT")
        return kind, identity, field
    if "fieldId" in item:
        raise OracleError("I75_TYPED_ENDPOINT")
    return kind, identity


def valid_token(value):
    return (isinstance(value, str)
            and re.fullmatch(r"[0-9a-f]{32}:[1-9][0-9]{0,19}", value) is not None
            and int(value[33:]) <= 2**64 - 1)


def validate_snapshot(snapshot):
    if snapshot.get("complete") is not True:
        raise OracleError("I75_INCOMPLETE_SOURCE")
    if (type(snapshot.get("enabled")) is not bool or
            not isinstance(snapshot.get("project"), str) or not snapshot["project"]):
        raise OracleError("I75_SOURCE_CONTEXT")
    objects = snapshot.get("objects")
    if not isinstance(objects, list):
        raise OracleError("I75_INCOMPLETE_SOURCE")
    endpoints = [key(obj) for obj in objects]
    if len(set(endpoints)) != len(endpoints):
        raise OracleError("I70_DUPLICATE_KEY")
    marks = []
    for obj in objects:
        expected = snapshot["enabled"] and obj.get("covered", True)
        marker = obj.get("token")
        if expected:
            if not valid_token(marker):
                raise OracleError("I70_TOKEN")
            marks.append(marker)
        elif marker is not None:
            raise OracleError("I70_EXTRA_TOKEN")
    if len(set(marks)) != len(marks):
        raise OracleError("I70_DUPLICATE_TOKEN")


def classify(pin, snapshot):
    """Five predicates in SSOT order, after source/I70 structural checking."""
    validate_snapshot(snapshot)
    endpoint = key(pin)
    if not isinstance(pin.get("project"), str) or not pin["project"]:
        raise OracleError("I75_PIN_CONTEXT")
    marker = pin.get("token")
    if marker is not None and not valid_token(marker):
        raise OracleError("I75_PIN_TOKEN")
    covered = {key(obj): obj for obj in snapshot["objects"] if obj.get("covered", True)}
    current = covered.get(endpoint)
    conditions = (
        pin["project"] != snapshot["project"] or marker is None or not snapshot["enabled"],
        any(obj.get("token") == marker and other != endpoint for other, obj in covered.items()),
        current is None,
        current is not None and current.get("token") != marker,
        True,
    )
    return next(state for state, applies in zip(STATES, conditions) if applies)


def judge_roots(identity, graph, *, same_project=True):
    """Expected complete K3 rows on the declared valid, ordinary-source domain.

    This adapter is not a validator for arbitrary JS graphs.  Active covered
    nodes must have unique legal marks.  The real source reader establishes
    that premise; invalid native sources are tested separately.  An explicitly
    uncovered endpoint remains R57 absent here (the existing JS has a known
    discrepancy on assembly-owned timbers, outside this D1 faces domain).
    """
    enabled = (graph.get("data", {}).get("identityLedger", {}).get("schema") == "identity-ledger/1"
               and graph.get("data", {}).get("identityLedger", {}).get("active") is True)
    objects = []
    for typed, node in graph["nodes"].items():
        kind, identity_id = typed.split(":")
        objects.append({"kind": kind, "id": int(identity_id), "token": node.get("incarnation"),
                        "covered": node.get("covered", True)})
    snapshot = {"project": "current", "enabled": enabled, "complete": True, "objects": objects}
    validate_snapshot(snapshot)
    rows = []
    for root in identity["roots"]:
        pin = {"project": "current" if same_project else "other", "kind": root["kind"],
               "id": root["id"], "token": root.get("incarnation")}
        state = classify(pin, snapshot)
        node = graph["nodes"].get(root["kind"] + ":" + str(root["id"]))
        current = node.get("incarnation") if node is not None else None
        row = dict(deepcopy(root), id=root["id"], currentIncarnation=current,
                   status=state, confirmed=False)
        if state != "unknown":
            live_pin = (node.get("definitionFingerprint") or node.get("definitionPin") or None) if node else None
            row.update(definitionPin=live_pin, previousDefinitionPin=root.get("definitionPin"))
        rows.append(row)
    return rows


def matrix_cases():
    """Finite exhaustive ordinary domain, including zero and same-number kinds."""
    endpoints = (("placement", 0), ("placement", 1), ("boundary", 0))
    tokens = (None, EPOCH + ":1", EPOCH + ":2", EPOCH + ":3")
    for enabled in (False, True):
        for assignment in product(tokens if enabled else (None, "present"), repeat=len(endpoints)):
            marks = [token for token in assignment if token is not None]
            if enabled and len(set(marks)) != len(marks):
                continue
            for live_pin in (None, "definition-A", "definition-B"):
                nodes = {}
                for (kind, identity), token in zip(endpoints, assignment):
                    if token is not None:
                        nodes[kind + ":" + str(identity)] = {
                            "incarnation": token if enabled else None,
                            "definitionFingerprint": live_pin,
                        }
                graph = {"data": {"identityLedger": {"schema": "identity-ledger/1", "active": enabled}}, "nodes": nodes}
                for old_mark, old_pin in product(tokens, (None, "definition-A", "definition-B")):
                    roots = [{"role": "use" if kind == "placement" else "boundary", "kind": kind, "id": identity,
                              "incarnation": old_mark, "definitionPin": old_pin}
                             for kind, identity in endpoints]
                    yield {"identity": {"schema": "model-source-identity/1", "roots": roots},
                           "graph": graph, "same_project": True}


def _json_bytes(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _pin(snapshot, obj):
    return {"project": snapshot["project"], "kind": obj["kind"], "id": obj["id"], "token": obj.get("token")}


def _geometry(snapshot):
    return [{name: deepcopy(value) for name, value in obj.items() if name not in ("token", "covered")}
            for obj in sorted(snapshot["objects"], key=key)]


def initial():
    objects = [{"kind": "placement", "id": i, "token": EPOCH + ":" + str(i + 1),
                "definition": {"name": "original", "size": 1}, "effective": 1} for i in range(2)]
    source = {"project": "p", "enabled": True, "complete": True, "objects": objects}
    return {"source": source, "binding": _pin(source, objects[0]),
            "model_source": _geometry(source), "receipts": []}


def run_sequence(events, seed=None):
    """Specification constructor for one consumer; explicit confirm is sole rebind.

    Ordinary source commands, complete World replacement and history restore
    are distinct transitions.  Restoring an old mark is allowed; allocating a
    previously used mark is not.  Candidate generation never rewinds, including
    source ABA and activation followed by cancelling the later candidate.
    """
    current = deepcopy(initial() if seed is None else seed)
    past, future, pending = [], [], None
    serial, generation, epoch_number, epoch = 2, 0, 0, EPOCH
    # The finite allocator witnesses uniqueness, not real cryptographic RNG.
    # Its initial sequence high-water is 2; the four finite seeds use <= 2.
    used_epochs = {EPOCH} | {obj["token"].split(":")[0] for obj in current["source"]["objects"]
                             if obj.get("token") is not None}
    rows = []
    for event in events:
        before = deepcopy(current)
        action, target = event["op"], event.get("id", 0)
        outcome = "unchanged"
        objects = current["source"]["objects"]
        obj = next((item for item in objects if item["id"] == target), None)
        if action in ("create", "delete", "replace", "rename", "resize", "collision", "clear", "activate"):
            proposed = deepcopy(current)
            source = proposed["source"]
            selected = next((item for item in source["objects"] if item["id"] == target), None)
            allocations = []
            if action == "create" and selected is not None:
                outcome = "KEY_OCCUPIED"
            elif action in ("delete", "rename", "resize", "collision") and selected is None:
                outcome = "MISSING_ENDPOINT"
            elif action == "activate" and source["enabled"]:
                outcome = "ALREADY_ACTIVE"
            else:
                if action == "clear":
                    source["objects"].clear()
                elif action == "activate":
                    source["enabled"] = True
                    allocations = source["objects"]
                elif action == "delete":
                    source["objects"].remove(selected)
                elif action in ("create", "replace"):
                    if selected is not None:
                        source["objects"].remove(selected)
                    created = {"kind": "placement", "id": target, "token": None,
                               "definition": {"name": "original", "size": 1}, "effective": 1}
                    source["objects"].append(created)
                    allocations = [created] if source["enabled"] else []
                elif action == "rename":
                    selected["definition"]["name"] = event["name"]
                elif action == "resize":
                    selected["definition"]["size"] = event["size"]
                    selected["effective"] = event["size"]
                else:
                    other = next((item for item in source["objects"] if item["id"] != target), None)
                    if other is None or not source["enabled"]:
                        outcome = "MISSING_ENDPOINT"
                    else:
                        selected["token"] = other["token"]
                if (allocations or action == "activate") and epoch is None:
                    while True:
                        epoch_number += 1
                        selected_epoch = format(epoch_number, "032x")
                        if selected_epoch not in used_epochs:
                            break
                    epoch = selected_epoch
                    used_epochs.add(epoch)
                for index, item in enumerate(sorted(allocations, key=key), 1):
                    item["token"] = epoch + ":" + str(serial + index)
                try:
                    validate_snapshot(source)
                except OracleError as error:
                    outcome = str(error)
                if outcome == "unchanged" and proposed != current:
                    past.append(before)
                    future.clear()
                    current = proposed
                    generation += 1
                    serial += len(allocations)
                    outcome = "source-committed"
        elif action in ("load-inactive", "load-original", "branch"):
            source = deepcopy(initial()["source"] if action != "branch" else current["source"])
            if action == "load-inactive":
                source["enabled"] = False
                for item in source["objects"]:
                    item["token"] = None
            past.append(before)
            future.clear()
            current["source"] = source
            epoch = None
            generation += 1
            outcome = "world-replaced"
        elif action == "context":
            if current["source"]["project"] != event["project"]:
                current["source"]["project"] = event["project"]
                generation += 1
                epoch = None
                outcome = "context-changed"
        elif action == "preview":
            pending = None
            state = classify(current["binding"], current["source"])
            if obj is None:
                outcome = "MISSING_ENDPOINT"
            elif current["source"]["project"] != "p":
                outcome = "I75_SOURCE_CONTEXT"
            elif state == "continuous" and key(current["binding"]) != key(obj):
                outcome = "CARRIER_EDIT_REQUIRED"
            else:
                pending = {"before": deepcopy(current), "generation": generation,
                           "target": _pin(current["source"], obj), "old_status": state}
                outcome = "prepared"
        elif action == "confirm":
            plan, pending = pending, None
            if plan is None:
                outcome = "NO_PLAN"
            elif plan["generation"] != generation or plan["before"] != current:
                outcome = "I76_STALE"
            elif (current["binding"] == plan["target"] and current["model_source"] == _geometry(current["source"])
                  and (plan["old_status"] == "continuous" or bool(current["receipts"])
                       and current["receipts"][-1]["new"] == plan["target"]
                       and current["receipts"][-1]["source"] == current["source"])):
                outcome = "no-op"
            else:
                past.append(before)
                future.clear()
                current["binding"] = deepcopy(plan["target"])
                current["model_source"] = _geometry(current["source"])
                current["receipts"].append({"old": deepcopy(before["binding"]), "old_status": plan["old_status"],
                                            "source": deepcopy(current["source"]), "new": deepcopy(plan["target"])})
                generation += 1
                outcome = "association-committed"
        elif action == "cancel":
            pending = None
            outcome = "cancelled"
        elif action in ("undo", "redo"):
            take, put = (past, future) if action == "undo" else (future, past)
            if take:
                put.append(before)
                current = deepcopy(take.pop())
                generation += 1
                outcome = action
        else:
            raise OracleError("UNKNOWN_EVENT")
        validate_snapshot(current["source"])
        used_epochs.update(obj["token"].split(":")[0] for obj in current["source"]["objects"]
                           if obj.get("token") is not None)
        rows.append({"event": deepcopy(event), "before": before, "after": deepcopy(current),
                     "status": classify(current["binding"], current["source"]), "outcome": outcome,
                     "generation": generation, "allocation_highwater": serial, "allocation_epoch": epoch})
    return rows


def _check_judgment(pin, source, declared):
    """Relational checker, deliberately not classify()/validate_snapshot()."""
    assert source.get("complete") is True, "ORACLE_COMPLETE_SOURCE"
    inverse, covered, endpoints = {}, {}, set()
    for obj in source["objects"]:
        endpoint = key(obj)
        assert endpoint not in endpoints, "ORACLE_ONE_KEY"
        endpoints.add(endpoint)
        if obj.get("covered", True):
            covered[endpoint] = obj
        marker = obj.get("token")
        if source["enabled"] and obj.get("covered", True):
            assert valid_token(marker), "ORACLE_LEGAL_MARK"
        else:
            assert marker is None, "ORACLE_UNCOVERED_MARK"
        if marker is not None:
            assert marker not in inverse, "ORACLE_IDENTITY_INJECTIVE"
            inverse[marker] = endpoint
    endpoint, marker = key(pin), pin.get("token")
    if pin["project"] != source["project"] or marker is None or not source["enabled"]:
        expected = "unknown"
    elif marker in inverse and inverse[marker] != endpoint:
        expected = "conflict"
    elif endpoint not in covered:
        expected = "absent"
    elif covered[endpoint].get("token") == marker:
        expected = "continuous"
    else:
        expected = "replaced"
    assert declared == expected, "ORACLE_R57_ORDER"


def check_trace(rows):
    generation, highwater, pending, previous = 0, 2, None, None
    past, future, owners, allocated = [], [], {}, set()
    epoch, observed_epochs = EPOCH, {EPOCH}
    for row in rows:
        before, after, event, outcome = row["before"], row["after"], row["event"], row["outcome"]
        if previous is not None:
            assert before == previous, "ORACLE_COMPLETE_EVENT_CHAIN"
        previous = after
        _check_judgment(after["binding"], after["source"], row["status"])
        before_marks, after_marks = ({key(obj): (source["project"], obj["token"])
            for obj in source["objects"] if obj.get("token") is not None}
            for source in (before["source"], after["source"]))
        allocated.update(before_marks.values())
        observed_epochs.update(marker.split(":")[0] for _, marker in before_marks.values())
        for source in (before["source"], after["source"]):
            for obj in source["objects"]:
                if obj.get("token") is not None:
                    marker = (source["project"], obj["token"])
                    assert owners.setdefault(marker, key(obj)) == key(obj), "ORACLE_LIFETIME_OWNER"
        started = set()
        if outcome == "source-committed":
            ended = set(before_marks) - set(after_marks)
            if event["op"] == "replace":
                ended.add(("placement", event.get("id", 0)))
            for endpoint in (set(before_marks) & set(after_marks)) - ended:
                assert before_marks[endpoint] == after_marks[endpoint], "ORACLE_CONTINUING_MARK"
            started = (set(after_marks) - set(before_marks)) | (ended & set(after_marks))
            for endpoint in started:
                assert after_marks[endpoint] not in allocated, "ORACLE_FRESH_ALLOCATION"
            assert row["allocation_highwater"] == highwater + len(started), "ORACLE_EXACT_ALLOCATION"
        else:
            assert row["allocation_highwater"] == highwater, "ORACLE_NO_EXTRA_ALLOCATION"
        proposed_epoch = row["allocation_epoch"]
        if outcome in ("world-replaced", "context-changed"):
            assert proposed_epoch is None, "ORACLE_SESSION_EPOCH"
        elif epoch is None and outcome == "source-committed" and (started or event["op"] == "activate"):
            assert isinstance(proposed_epoch, str) and re.fullmatch(r"[0-9a-f]{32}", proposed_epoch), "ORACLE_SESSION_EPOCH"
            assert proposed_epoch not in observed_epochs, "ORACLE_SESSION_EPOCH"
        else:
            assert proposed_epoch == epoch, "ORACLE_SESSION_EPOCH"
        if proposed_epoch is not None:
            observed_epochs.add(proposed_epoch)
        for rank, endpoint in enumerate(sorted(started), 1):
            assert after_marks[endpoint][1] == proposed_epoch + ":" + str(highwater + rank), "ORACLE_EXACT_ALLOCATED_MARK"
        epoch = proposed_epoch
        observed_epochs.update(marker.split(":")[0] for _, marker in after_marks.values())
        allocated.update(after_marks.values())
        if event["op"] == "confirm":
            if pending is None:
                expected_effect = "NO_PLAN"
            elif pending[:2] != (before, generation):
                expected_effect = "I76_STALE"
            else:
                matches = [obj for obj in before["source"]["objects"] if obj["id"] == pending[2]]
                assert len(matches) == 1, "ORACLE_EXACT_NEW_TARGET"
                target = {"project": before["source"]["project"], "kind": matches[0]["kind"],
                          "id": matches[0]["id"], "token": matches[0].get("token")}
                geometry = [{name: deepcopy(value) for name, value in obj.items() if name not in ("token", "covered")}
                            for obj in sorted(before["source"]["objects"], key=lambda item: (item["kind"], item["id"]))]
                continuous = (before["source"]["enabled"] and target["token"] is not None and before["binding"] == target)
                prior_decision = (bool(before["receipts"]) and before["receipts"][-1]["new"] == target
                                  and before["receipts"][-1]["source"] == before["source"])
                unchanged = before["binding"] == target and before["model_source"] == geometry and (continuous or prior_decision)
                expected_effect = "no-op" if unchanged else "association-committed"
            assert outcome == expected_effect, "ORACLE_CONFIRM_EFFECT"
        if outcome in ("source-committed", "association-committed", "world-replaced"):
            past.append(deepcopy(before))
            future.clear()
        elif outcome in ("undo", "redo"):
            take, put = (past, future) if outcome == "undo" else (future, past)
            assert event["op"] == outcome and take, "ORACLE_RESTORE_AVAILABLE"
            assert after == take.pop(), "ORACLE_RESTORE_COMPLETE_RECORD"
            put.append(deepcopy(before))
        if event["op"] == "preview":
            pending = (deepcopy(before), generation, event.get("id", 0)) if outcome == "prepared" else None
        if outcome == "association-committed":
            assert event["op"] == "confirm", "ORACLE_CONFIRM_ONLY"
            assert pending is not None and pending[:2] == (before, generation), "ORACLE_EXACT_GENERATION"
            assert after["binding"] == target, "ORACLE_EXACT_NEW_TARGET"
            assert after["model_source"] == geometry, "ORACLE_FULL_MODEL_SOURCE"
            assert after["source"] == before["source"], "ORACLE_REBIND_NOT_WORLD_EDIT"
            assert len(after["receipts"]) == len(before["receipts"]) + 1, "ORACLE_RECEIPT_REQUIRED"
            receipt = after["receipts"][-1]
            assert receipt["old"] == before["binding"] and receipt["new"] == after["binding"], "ORACLE_EXACT_ENDPOINTS"
            assert receipt["source"] == after["source"], "ORACLE_EXACT_SOURCE"
        elif outcome not in ("undo", "redo"):
            assert after["binding"] == before["binding"], "ORACLE_NO_SILENT_REBIND"
            assert after["model_source"] == before["model_source"], "ORACLE_NO_SILENT_MODEL_UPDATE"
            assert after["receipts"] == before["receipts"], "ORACLE_RECEIPT_ONLY_AFTER_CONFIRM"
        if event["op"] in ("confirm", "cancel"):
            pending = None
        if outcome not in ("undo", "redo"):
            assert after["receipts"][:len(before["receipts"])] == before["receipts"], "ORACLE_IMMUTABLE_HISTORY"
        for receipt in after["receipts"]:
            _check_judgment(receipt["old"], receipt["source"], receipt["old_status"])
        if event["op"] in ("preview", "cancel") or outcome in ("NO_PLAN", "I76_STALE", "no-op", "unchanged"):
            assert before == after, "ORACLE_ZERO_WRITE"
        advanced = outcome in ("source-committed", "association-committed", "world-replaced", "context-changed", "undo", "redo")
        assert row["generation"] == generation + int(advanced), "ORACLE_EXACT_EXECUTION_GENERATION"
        generation, highwater = row["generation"], row["allocation_highwater"]
    return True


ALPHABET = (
    {"op": "delete", "id": 0}, {"op": "create", "id": 0}, {"op": "replace", "id": 0},
    {"op": "rename", "name": "renamed"}, {"op": "rename", "name": "original"},
    {"op": "collision"}, {"op": "clear"}, {"op": "activate"}, {"op": "load-inactive"},
    {"op": "load-original"}, {"op": "branch"}, {"op": "context", "project": "q"},
    {"op": "context", "project": "p"}, {"op": "preview", "id": 0},
    {"op": "preview", "id": 1}, {"op": "confirm"}, {"op": "cancel"}, {"op": "undo"}, {"op": "redo"},
)


def scan(depth=3):
    tracked, unknown, conflict, inactive = (initial() for _ in range(4))
    unknown["binding"]["token"] = None
    conflict["binding"]["token"] = EPOCH + ":2"
    inactive["source"]["enabled"] = False
    inactive["binding"]["token"] = None
    for obj in inactive["source"]["objects"]:
        obj["token"] = None
    sequences, steps, states, outcomes, checksum = 0, 0, Counter(), Counter(), sha256()
    for seed in (tracked, unknown, conflict, inactive):
        for length in range(depth + 1):
            for events in product(ALPHABET, repeat=length):
                trace = run_sequence(events, seed)
                check_trace(trace)
                assert trace == run_sequence(events, seed), "ORACLE_RECOMPUTABLE"
                sequences += 1
                steps += length
                states.update(row["status"] for row in trace)
                outcomes.update(row["outcome"] for row in trace)
                checksum.update(_json_bytes(trace) + b"\n")
    return {"depth": depth, "alphabet": len(ALPHABET), "seeds": 4, "sequences": sequences,
            "steps": steps, "states": dict(sorted(states.items())), "outcomes": dict(sorted(outcomes.items())),
            "trace_sha256": checksum.hexdigest(), "scope": "host-specification-only"}


CONTROLS = {"ORACLE_SILENT_REBIND": "ORACLE_NO_SILENT_REBIND",
            "ORACLE_DUPLICATE_IDENTITY": "ORACLE_IDENTITY_INJECTIVE",
            "ORACLE_REWRITTEN_HISTORY": "ORACLE_R57_ORDER",
            "ORACLE_REUSED_RETIRED_IDENTITY": "ORACLE_FRESH_ALLOCATION",
            "ORACLE_INVENTED_NEW_TARGET": "ORACLE_EXACT_NEW_TARGET",
            "ORACLE_STALE_FULL_MODEL": "ORACLE_FULL_MODEL_SOURCE",
            "ORACLE_FALSE_ALLOCATION": "ORACLE_EXACT_ALLOCATED_MARK",
            "ORACLE_UNCONFIRMED_RECEIPT": "ORACLE_RECEIPT_ONLY_AFTER_CONFIRM",
            "ORACLE_RESTORED_SESSION_EPOCH": "ORACLE_SESSION_EPOCH",
            "ORACLE_SKIPPED_UNKNOWN_DECISION": "ORACLE_CONFIRM_EFFECT",
            "ORACLE_NONCONFIRM_COMMIT": "ORACLE_CONFIRM_ONLY"}


def probe(name, corrupt=False):
    if name not in CONTROLS:
        raise ValueError(name)
    seed = None
    if name in ("ORACLE_REWRITTEN_HISTORY", "ORACLE_INVENTED_NEW_TARGET", "ORACLE_NONCONFIRM_COMMIT"):
        events = [{"op": "replace"}, {"op": "preview", "id": 0}, {"op": "confirm"}]
    elif name == "ORACLE_REUSED_RETIRED_IDENTITY":
        events = [{"op": "delete"}, {"op": "create"}]
    elif name == "ORACLE_STALE_FULL_MODEL":
        events = [{"op": "resize", "size": 2}, {"op": "preview"}, {"op": "confirm"}]
    elif name == "ORACLE_FALSE_ALLOCATION":
        events = [{"op": "replace"}]
    elif name == "ORACLE_RESTORED_SESSION_EPOCH":
        events = [{"op": "load-original"}, {"op": "undo"}]
    elif name == "ORACLE_SKIPPED_UNKNOWN_DECISION":
        seed = initial()
        seed["binding"]["token"] = None
        seed["source"]["enabled"] = False
        for obj in seed["source"]["objects"]:
            obj["token"] = None
        events = [{"op": "preview"}, {"op": "confirm"}]
    else:
        events = [{"op": "rename", "name": "renamed"}]
    rows = run_sequence(events, seed)
    if corrupt:
        if name == "ORACLE_SILENT_REBIND":
            rows[-1]["after"]["binding"]["token"] = EPOCH + ":99"
            rows[-1]["status"] = "replaced"
        elif name == "ORACLE_DUPLICATE_IDENTITY":
            rows[-1]["after"]["source"]["objects"][1]["token"] = EPOCH + ":1"
        elif name == "ORACLE_REWRITTEN_HISTORY":
            rows[-1]["after"]["receipts"][-1]["old_status"] = "continuous"
        elif name == "ORACLE_REUSED_RETIRED_IDENTITY":
            rows[-1]["after"]["source"]["objects"][-1]["token"] = EPOCH + ":1"
            rows[-1]["status"] = "continuous"
        elif name == "ORACLE_INVENTED_NEW_TARGET":
            rows[-1]["after"]["binding"]["token"] = EPOCH + ":999"
            rows[-1]["after"]["receipts"][-1]["new"]["token"] = EPOCH + ":999"
            rows[-1]["status"] = "replaced"
        elif name == "ORACLE_STALE_FULL_MODEL":
            rows[-1]["after"]["model_source"] = deepcopy(rows[-1]["before"]["model_source"])
        elif name == "ORACLE_FALSE_ALLOCATION":
            rows[-1]["after"]["source"]["objects"][-1]["token"] = EPOCH + ":999"
        elif name == "ORACLE_UNCONFIRMED_RECEIPT":
            state = rows[-1]["after"]
            state["receipts"].append({"old": deepcopy(state["binding"]), "new": deepcopy(state["binding"]),
                                       "source": deepcopy(state["source"]), "old_status": "continuous"})
        elif name == "ORACLE_RESTORED_SESSION_EPOCH":
            rows[-1]["allocation_epoch"] = EPOCH
        elif name == "ORACLE_NONCONFIRM_COMMIT":
            rows[-1]["event"] = {"op": "rename", "name": "forged"}
        else:
            rows[-1]["after"] = deepcopy(rows[-1]["before"])
            rows[-1]["outcome"] = "no-op"
            rows[-1]["generation"] = 0
    check_trace(rows)


def mutation_checks():
    results = []
    for name, marker in CONTROLS.items():
        command = [sys.executable, "-B", __file__, "--probe", name]
        calls = [subprocess.run(command + extra, capture_output=True, text=True, timeout=30)
                 for extra in ([], ["--corrupt"], [])]
        assert [call.returncode for call in calls] == [0, 1, 0], (name, calls)
        assert "AssertionError: " + marker in calls[1].stderr, calls[1].stderr
        results.append({"name": name, "exits": [call.returncode for call in calls], "marker": marker,
                        "commands": [command, command + ["--corrupt"], command],
                        "stdout": [call.stdout for call in calls], "stderr": [call.stderr for call in calls]})
    return results


if __name__ == "__main__":
    if "--probe" in sys.argv:
        probe(sys.argv[sys.argv.index("--probe") + 1], "--corrupt" in sys.argv)
    else:
        print(json.dumps({"scan": scan(), "checker_withdrawals": mutation_checks()}, indent=2, sort_keys=True))
