#!/usr/bin/env python3
"""Project fresh U476 native artifacts into finite research facts.

No model geometry or native replies are authored here. Scope/owner/context
strings are explicitly offline study assumptions, not product service proof.
Original live marks are read from the real model sourceIdentity, never from
the deidentified native replay. Diagnostic `consistent` fields are not used.
"""
from __future__ import annotations
import argparse
import copy
import hashlib
import json
from pathlib import Path
import re


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def save(path, value):
    Path(path).write_text(json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8", newline="\n")


def uint(value):
    return type(value) is int and 0 <= value <= 4294967295


def graph_index(graph):
    assert graph.get("ok") is True and graph.get("schema") == "source-inspector/1", "U476_NATIVE_GRAPH_SCHEMA"
    assert graph.get("complete") is True, "U476_NATIVE_COMPLETE"
    nodes = {}
    for node in graph["nodes"]:
        assert type(node.get("key")) is str and node["key"] not in nodes, "U476_NATIVE_KEY_DUPLICATE"
        nodes[node["key"]] = node
    return nodes


def typed_root(nodes, kind, identifier):
    assert uint(identifier), "U476_EXPECTED_ROOT_UINT32"
    expected_key = kind + ":" + str(identifier)
    node = nodes.get(expected_key)
    assert isinstance(node, dict), "U476_NATIVE_TYPED_ROOT_MISSING"
    raw_id = node.get("id")
    if type(raw_id) is str:
        assert re.fullmatch(r"0|[1-9][0-9]*", raw_id), "U476_NATIVE_ROOT_ID_CANONICAL"
        numeric_id = int(raw_id)
    else:
        assert uint(raw_id), "U476_NATIVE_ROOT_ID_UINT32"
        numeric_id = raw_id
    assert uint(numeric_id) and node.get("key") == expected_key and node.get("kind") == kind and numeric_id == identifier, "U476_NATIVE_TYPED_ROOT_MISMATCH"
    return node


def project(folder):
    record = read(folder / "saved-record.json")
    live, refs = read(folder / "live-graph.json"), read(folder / "live-references.json")
    saved, package = read(folder / "snapshot.json"), read(folder / "package-snapshot.json")
    validation, producer, readonly = [read(folder / name) for name in ("saved-validation.json", "producer-proof.json", "native-readonly-proof.json")]
    assert all(validation[key] is True for key in ("validateSpaceModel", "validateSpaceModelHashes", "native_input_package_fingerprint_equal", "pack_unpack_record_equal", "live_saved_rows_equal")), "U476_MODEL_VALIDATION"
    assert producer["historical_replay_equal"] is True and set(producer["independently_rebuilt_packages"]) == {"space", "volume", "clearance", "timbers"}, "U476_REAL_PRODUCER"
    assert readonly["graph_equal_including_revision"] is True and readonly["dump_equal"] is True, "U476_NATIVE_READONLY"
    assert saved["sourceFingerprint"] == package["sourceFingerprint"], "U476_DUAL_NATIVE_READ"
    assert live["live"] is True and saved["live"] is False and package["live"] is False, "U476_WORLD_KIND"
    assert live["identityLedger"]["active"] is True and record["sourceIdentity"]["schema"] == "model-source-identity/1", "U476_ORIGINAL_MARKS"
    selected = record["input"]["timbers"]
    assert record["input"]["mode"] == "plan", "U476_ORDINARY_PLAN"
    indices = [graph_index(graph) for graph in (live, saved, package)]
    for nodes in indices:
        placement = typed_root(nodes, "placement", record["input"]["placement_id"])
        for selected_root in selected:
            assert selected_root["kind"] == "timber", "U476_SELECTED_TYPED_ROOT"
            timber = typed_root(nodes, "timber", selected_root["id"])
            assert timber.get("placed") is True and timber.get("surface") == record["input"]["placement_id"] and timber.get("nativeOwner") is None, "U476_ORDINARY_PLACED_ROOT"
    scope, scenario = "u476-offline-study-project:" + folder.name, "u476-offline-selected-scenario"
    owner, record_hash = scope + "/" + scenario, sha(folder / "saved-record.json")
    context = {"projectScope": scope, "scenario": scenario, "projectRevision": live["revision"],
               "liveReadPin": live["sourceFingerprint"], "attachmentPin": "pending-study-declarations",
               "settingsPin": sha(folder.parent / "cutting-settings.json"),
               "modelPins": {record["id"]: {"owner": owner, "recordSha256": record_hash, "readPin": saved["sourceFingerprint"]}}}

    def normalize(graph, references, schedule, kind):
        nodes = graph_index(graph)
        pins = {(pin["kind"], pin["id"]): pin for pin in record["sourceIdentity"]["roots"]}
        result = []
        for row in schedule["rows"]:
            root = typed_root(nodes, "timber", row["id"])
            placement = typed_root(nodes, "placement", row["surface"])
            native_ref = next(item for item in references["timbers"] if item["id"] == row["id"])
            assert not references["engineeringSources"], "U476_LITERAL_DIMENSIONS_ONLY"
            assert row.get("sources") == [], "U476_LITERAL_DIMENSION_ROWS_ONLY"
            assert row["assembly"] is None and root["nativeOwner"] is None and root["placed"] is True, "U476_ORDINARY_PLACED"
            assert all(row["supports"][end]["status"] == "exact" for end in ("start", "finish")), "U476_EXACT_SUPPORTS"
            closure = {root["key"]}
            while True:
                expanded = closure | {edge["to"] for edge in graph["edges"] if edge["from"] in closure and edge["active"]}
                if expanded == closure:
                    break
                closure = expanded
            assert closure <= nodes.keys(), "U476_SOURCE_CLOSURE_COMPLETE"
            closure_nodes = [{key: value for key, value in nodes[name].items() if key not in ("incarnation", "label")} for name in sorted(closure)]
            closure_edges = [edge for edge in graph["edges"] if edge["from"] in closure and edge["to"] in closure]
            timber_mark = root["incarnation"] if kind == "live" else pins[("timber", row["id"])]["incarnation"]
            placement_mark = placement["incarnation"] if kind == "live" else pins[("placement", row["surface"])]["incarnation"]
            assert type(timber_mark) is str and type(placement_mark) is str, "U476_DURABLE_MARKS"
            if kind == "model":
                assert pins[("timber", row["id"])]["definitionPin"] == root["definitionFingerprint"] and pins[("placement", row["surface"])]["definitionPin"] == placement["definitionFingerprint"], "U476_MODEL_ORIGINAL_PINS"
                assert root["incarnation"] is None and placement["incarnation"] is None, "U476_NO_MARK_FROM_REPLAY"
            content = {"A": row["A"], "B": row["B"], "L": row["L"],
                       "material": {"A": {"kind": "literal", "value": row["A"]}, "B": {"kind": "literal", "value": row["B"]}},
                       "direction": {"dir": row["dir"], "side": row["side"]}, "surface": {"kind": "placement", "id": row["surface"]},
                       "placement": copy.deepcopy(native_ref), "supports": copy.deepcopy(row["supports"]),
                       "typedSources": {"nodes": closure_nodes, "edges": closure_edges}}
            result.append({"ref": ("live:" if kind == "live" else "model:" + record["id"] + ":") + str(row["id"]),
                           "kind": kind, "category": "ordinary-d7", "projectScope": scope, "scenario": scenario,
                           "timber": {"kind": "timber", "id": row["id"], "mark": timber_mark},
                           "placement": {"kind": "placement", "id": row["surface"], "mark": placement_mark},
                           "native": {"readPin": graph["sourceFingerprint"], "complete": graph["complete"],
                                      "definitionPin": {"timber": root["definitionFingerprint"], "placement": placement["definitionFingerprint"]},
                                      "effectivePin": {"timber": root["valueFingerprint"], "placement": placement["valueFingerprint"]},
                                      "rootNodes": {"timber": {"key": root["key"], "kind": root["kind"], "id": row["id"], "placed": True, "surface": row["surface"]},
                                                    "placement": {"key": placement["key"], "kind": placement["kind"], "id": row["surface"]}},
                                      "content": content},
                           "model": None if kind == "live" else {"recordId": record["id"], "owner": owner, "recordSha256": record_hash,
                                      "sourceKind": "ordinary-plan", "inputTimbers": [item["id"] for item in selected],
                                      "inputOutcome": "COMPLETE", "resultOutcome": "COMPLETE"}})
        return result

    current = normalize(live, refs, read(folder / "live-schedule.json"), "live")
    historical = normalize(saved, saved["timberReferences"], read(folder / "saved-schedule.json"), "model")
    assert len(current) == len(historical)
    for left, right in zip(current, historical):
        assert all(left[key] == right[key] for key in ("timber", "placement")), "U476_PROJECTION_CONTINUITY"
        assert all(left["native"][key] == right["native"][key] for key in ("definitionPin", "effectivePin", "content", "rootNodes")), "U476_PROJECTION_CONTENT"
    return {"studySchema": "U476-facts/1", "context": context, "endContext": copy.deepcopy(context),
            "current": current, "representations": current + historical, "declarations": {"items": [], "excluded": []}}


def run(root, destination):
    destination.mkdir(parents=True, exist_ok=True)
    cases = []
    for name in ("single", "independent-control"):
        original = project(root / name)
        for treatment in ("unresolved", "explicit", "exclude-model", "revoked"):
            data = copy.deepcopy(original)
            if treatment in ("unresolved", "revoked"):
                data["declarations"]["items"] = [{"itemKey": i + 1, "members": [row["ref"]], "representative": row["ref"]} for i, row in enumerate(data["representations"])]
            elif treatment == "explicit":
                for i, row in enumerate(data["current"]):
                    members = [candidate["ref"] for candidate in data["representations"] if candidate["timber"] == row["timber"] and candidate["placement"] == row["placement"]]
                    data["declarations"]["items"].append({"itemKey": i + 1, "members": members, "representative": row["ref"]})
            else:
                data["declarations"]["items"] = [{"itemKey": i + 1, "members": [row["ref"]], "representative": row["ref"]} for i, row in enumerate(data["current"])]
                data["declarations"]["excluded"] = [row["ref"] for row in data["representations"] if row["kind"] == "model"]
            data["context"]["attachmentPin"] = hashlib.sha256(canonical(data["declarations"]).encode("utf-8")).hexdigest()
            data["endContext"] = copy.deepcopy(data["context"])
            label = name + "-" + treatment
            path = destination / (label + ".input.json")
            save(path, data)
            cases.append({"name": label, "representations": len(data["representations"]), "physicalSources": len(data["current"]),
                          "expectedStatus": "INCOMPLETE" if treatment in ("unresolved", "revoked") else "COMPLETE",
                          "inputSha256": sha(path)})
    summary = {"researchOnly": True, "studySchema": "U476-facts/1", "cases": cases,
               "contextLimit": "Offline project/scenario/owner assumptions; not a product owner service or formal capability.",
               "sourceLimit": "Native fixture covers literal A/B ordinary placed D7 only; no engineering terminal positive case.",
               "originalSourceMarks": True, "candidateMarksUsed": False,
               "nativeRootChecks": "For live, saved-input and saved-result: raw key, kind and canonical uint32 id checked before numeric projection.",
               "sourceArtifactPins": {str(path.relative_to(root)): {"bytes": path.stat().st_size, "sha256": sha(path)}
                                      for name in ("single", "independent-control") for path in sorted((root / name).iterdir()) if path.is_file()}}
    save(destination / "summary.json", summary)
    print(json.dumps({"researchOnly": True, "studySchema": "U476-facts/1", "cases": cases}, ensure_ascii=False))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--native-artifacts", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    run(args.native_artifacts.resolve(), args.out.resolve())
