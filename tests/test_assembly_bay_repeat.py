"""R06 / D58 I69 R55: independent, real-native bay-repeat acceptance.

The input fixtures contain definitions, not precomputed generated timbers.  The
numeric oracles below are integer geometry worked out independently of the
generator.  A missing implementation fails an assertion about its public reply;
missing tools, invalid JSON, crashes and skips are never mutation detections.
"""
from copy import deepcopy
import base64
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from tests._bridge import BridgeSession, find_bridge
from tests.test_assembly_rules import binding, rule, killer, REACHED


CAPABILITY = "assembly-bay-repeat/1"
LIMITS = {"instances": 16, "ownedTimbers": 512, "worldTimbers": 512,
          "instanceRecordBytes": 65535, "bayPrimaries": 12,
          "baySecondaryLines": 24, "bayOmit": 24}


def grid_at(index, axis="u", grid=1):
    return {"kind": "grid-line", "gridId": grid, "axis": axis, "index": str(index)}


def primary(key, at, ends=(90, 91)):
    return {"key": key, "at": at, "ends": {
        "start": {"kind": "timber", "id": ends[0]},
        "finish": {"kind": "timber", "id": ends[1]}}}


def line_source(key, at):
    return {"key": key, "at": at}


def identity(row):
    if "primary" in row:
        return ("primary", row["primary"])
    secondary = row.get("secondary")
    if isinstance(secondary, dict):
        return ("secondary", secondary.get("line"), secondary.get("left"), secondary.get("right"))
    return ("invalid-owner", json.dumps(row, sort_keys=True))


def mapping(instance):
    return {identity(row): row["timberId"] for row in instance["value"]["mapping"]}


class BayRepeat(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="r06-bay-repeat-")
        self.addCleanup(self.temp.cleanup)
        self.directory = Path(self.temp.name)
        self.binary = find_bridge()
        self.bridge = BridgeSession(self.binary, cwd=self.directory)
        self.addCleanup(self.bridge.stop)
        self.fixture()

    def command(self, text):
        return self.bridge.command(text)

    def line(self, text):
        result = self.command("line " + text)
        if result.get("preview", {}).get("valid"):
            result = self.command("line confirm " + str(result["preview"]["token"]))
        self.assertTrue(result.get("ok"), {"fixtureLine": text, "reply": result})
        return result

    def guide(self, identifier, axis, coordinate):
        self.line(f"spec brguide{identifier} {coordinate}")
        self.line(f"guide {identifier} 1 {axis} spec:brguide{identifier}")

    def fixture(self, height=3000, hole=False):
        self.assertTrue(self.command("reset").get("ok"))
        outline = f"surface 1 origin 0 0 2500 u +x v +y outline 0,0 4000,0 4000,{height} 0,{height}"
        if hole:
            outline += " hole 1800,1900 2000,1900 2000,2100 1800,2100"
        for text in [outline, "grid 1 on 1 u 500 1000 1500 2500 v 1000 2000",
                     "timber 90 20 20 role boundary", "place 90 on 1 at-face e0 +u +n",
                     "timber 91 20 20 role boundary", "place 91 on 1 at-face e2 +u +n"]:
            self.line(text)
        value = binding()
        for slot in value["slots"]:
            slot["orientation"] = "A"
        self.apply([{"op": "publish-rule", "value": rule()},
                    {"op": "create-binding", "value": value}], generation=False)

    def read(self):
        result = self.command("assembly-read")
        self.assertTrue(result.get("ok"), result)
        self.assertIsInstance(result.get("state"), dict, result)
        return result

    def dump(self):
        result = self.command("dump")
        self.assertTrue(result.get("ok"), result)
        return result["text"]

    def stable(self):
        return {"dump": self.dump(), "assembly": self.read()}

    def source(self, identifier=1, surface=1):
        fixed = self.read()["state"]["rules"][0]
        return {"id": identifier, "name": "R06 explicit finite bays", "bindingId": 1,
                "rule": {"id": 1, "version": 1, "fingerprint": fixed["fingerprint"]},
                "surfaceId": surface, "layout": "bay-repeat",
                "primaries": [primary(10, grid_at(0)), primary(20, grid_at(2)), primary(30, grid_at(3))],
                "secondaryLines": [line_source(101, grid_at(0, "v")), line_source(202, grid_at(1, "v"))],
                "omit": []}

    def instance(self, identifier=1):
        rows = [r for r in self.read()["state"].get("instances", [])
                if r.get("value", {}).get("source", {}).get("id") == identifier]
        self.assertEqual(1, len(rows), {"missingInstance": identifier, "rows": rows})
        return rows[0]

    def create(self, value=None):
        value = value if value is not None else self.source()
        bound = next(r for r in self.read()["state"]["bindings"] if r["value"]["id"] == value["bindingId"])
        return {"op": "create-instance", "value": value, "expectedBindingFingerprint": bound["fingerprint"]}

    def edit(self, value=None, identifier=1):
        old = self.instance(identifier)
        value = deepcopy(old["value"]["source"]) if value is None else value
        result = self.create(value)
        result.update(op="edit-instance", id=identifier, expectedFingerprint=old["fingerprint"])
        return result

    def delete(self, identifier=1):
        return {"op": "delete-instance", "id": identifier,
                "expectedFingerprint": self.instance(identifier)["fingerprint"]}

    def request(self, operations, generation=True):
        path = self.directory / "candidate.json"
        path.write_text(json.dumps({"schema": "assembly-generation-transaction/1" if generation else "assembly-transaction/1",
                                    "expectedRevision": self.read()["revision"], "operations": operations}), encoding="utf-8")
        result = self.command(("assembly-generation-preview " if generation else "assembly-preview ") + str(path))
        self.assertTrue(result.get("ok"), {"publicPreviewTransport": result})
        self.assertIsInstance(result.get("preview"), dict, {"publicPreviewSchema": result})
        self.assertIs(type(result["preview"].get("valid")), bool, result)
        return result["preview"]

    def apply(self, operations, generation=True):
        preview = self.request(operations, generation)
        self.assertTrue(preview["valid"], {"requiredValidFixtureCandidate": preview})
        result = self.command("assembly-confirm " + str(preview["token"]))
        self.assertTrue(result.get("ok"), result)
        return result

    def cell_rows(self, preview):
        rows = preview.get("bayCells")
        self.assertIsInstance(rows, list, {"missingNativeBayCells": preview})
        return rows

    def rejection(self, operations, category, code=None, generation=True):
        before = self.stable()
        preview = self.request(operations, generation)
        violations = preview.get("violations", [])
        matched = [v for v in violations if v.get("category") == category and (code is None or v.get("code") == code)]
        # Return the observation before asserting its contract. The individual
        # killer assertion, not an unrelated helper assertion, detects a mutant.
        result = {"valid": preview["valid"], "matched": bool(matched), "unchanged": before == self.stable()}
        return result, preview, matched

    def geometry(self, instance=None):
        instance = self.instance() if instance is None else instance
        members = instance.get("members")
        self.assertIsInstance(members, list, {"missingNativeMembers": instance})
        return {identity(member): member.get("geometry") for member in members}

    def rectangle_expected(self):
        expected = {("primary", key): 2960 for key in (10, 20, 30)}
        expected.update({("secondary", line, left, right): 973
                         for line in (101, 202) for left, right in ((10, 20), (20, 30))})
        return expected

    def assert_native_provenance(self, command, instance):
        refs = command("references")
        self.assertTrue(refs.get("ok"), refs)
        support = refs.get("timberSupports", {})
        self.assertEqual("native-timber-supports/1", support.get("schema"))
        entries = {r["id"]: r for r in support.get("entries", [])}
        state = command("assembly-read")["state"]
        binding_row = next(b for b in state["bindings"] if b["value"]["id"] == instance["value"]["source"]["bindingId"])
        graph = command("source-inspect")
        self.assertTrue(graph.get("ok") and graph.get("complete"), graph)
        nodes = {n["key"]: n for n in graph.get("nodes", [])}
        for row in instance["value"]["mapping"]:
            tid = row["timberId"]
            owner = entries.get(tid, {}).get("owner")
            expected_identity = {k: v for k, v in row.items() if k != "timberId"}
            expected = {"instanceId": instance["value"]["source"]["id"], "identity": expected_identity,
                        "bindingId": binding_row["value"]["id"], "ruleId": binding_row["value"]["rule"]["id"],
                        "ruleVersion": binding_row["value"]["rule"]["version"],
                        "ruleFingerprint": instance["value"]["source"]["rule"]["fingerprint"],
                        "instanceFingerprint": instance["fingerprint"], "bindingFingerprint": binding_row["fingerprint"]}
            self.assertEqual(expected, owner, {"timber": tid, "projection": "references.timberSupports"})
            self.assertEqual(expected, nodes.get("timber:" + str(tid), {}).get("nativeOwner"))
            ident = identity(row)
            field = ":".join(str(part) for part in ident)
            self.assertTrue(any(edge.get("relation") == "member" and edge.get("field") == field and
                                edge.get("from") == "timber:" + str(tid) and
                                edge.get("to") == "assembly-instance:" + str(instance["value"]["source"]["id"])
                                for edge in graph.get("edges", [])),
                            {"missingOwnedSourceEdge": field, "timber": tid})

    def insert(self):
        value = deepcopy(self.instance()["value"]["source"])
        value["primaries"].append(primary(15, grid_at(1)))
        return value

    def configured_grid(self, u_stagger=None, v_stagger=None):
        self.line("delete grid 1")
        u = "repeat 2500 1000" + (" stagger " + str(u_stagger) if u_stagger is not None else "")
        v = "repeat 1000 1000" + (" stagger " + str(v_stagger) if v_stagger is not None else "")
        self.line("grid-system 2 name-hex 523036 main-along none u " + u + " v " + v)
        boundary = self.command("boundary 1")
        self.assertTrue(boundary.get("ok"), boundary)
        self.line("grid-binding 2 on-boundary 1 from-system 2 vertex outer 0 geometry-hash " +
                  boundary["geometryFingerprint"] + " cell -3 -1 anchor 1 2 0 1")
        self.line("grid 2 on 1 from-binding 2")
        source = self.source()
        for member, index in zip(source["primaries"], (-2, -1, 0)):
            member["at"] = grid_at(index, grid=2)
        source["secondaryLines"] = [line_source(101, grid_at(0, "v", 2)), line_source(202, grid_at(1, "v", 2))]
        return source

    def replace_fixture_grid(self, declaration):
        self.assertFalse(self.read()["state"].get("instances"), "fixture replacement precedes repeat creation")
        self.line("delete grid 1")
        self.line(declaration)

    def foreign_transaction(self, namespace, operations):
        path = self.directory / (namespace + ".json")
        path.write_text(json.dumps({"schema": namespace + "-transaction/1", "expectedRevision": self.read()["revision"],
                                    "operations": operations}), encoding="utf-8")
        reply = self.command(namespace + "-preview " + str(path))
        self.assertTrue(reply.get("ok") and reply.get("preview", {}).get("valid"), reply)
        self.assertTrue(self.command(namespace + "-confirm " + str(reply["preview"]["token"]))["ok"])

    def l_room(self, create_right=True):
        self.fixture()
        self.line("delete timber 91")
        self.line("delete timber 90")
        self.line("delete grid 1")
        self.line("surface 1 origin 0 0 2500 u +x v +y outline 0,0 4000,0 4000,1500 2000,1500 2000,3000 0,3000")
        self.line("grid 1 on 1 u 500 1500 2500 3500 v 1000 1480 2000")
        for tid, edge in ((90, 0), (94, 4)):
            self.line(f"timber {tid} 20 20 role boundary")
            self.line(f"place {tid} on 1 at-face e{edge} +u +n")
        left = self.source()
        left["primaries"] = [primary(1, {"kind": "outline-edge", "edge": 5}, (90, 94)),
                             primary(2, grid_at(0), (90, 94)), primary(3, grid_at(1), (90, 94))]
        left["secondaryLines"] = [line_source(101, grid_at(0, "v")), line_source(202, grid_at(2, "v"))]
        self.apply([self.create(left)])
        left_id = mapping(self.instance())[("primary", 3)]
        self.line("timber 92 20 20 role boundary")
        self.line(f"place 92 on 1 at-face e2 between e1 t{left_id} +u +n")
        right = self.source(2)
        right["primaries"] = [primary(4, grid_at(2), (90, 92)), primary(5, grid_at(3), (90, 92)),
                              primary(6, {"kind": "outline-edge", "edge": 1}, (90, 92))]
        right["secondaryLines"] = deepcopy(left["secondaryLines"])
        if not create_right:
            return left, right
        self.apply([self.create(right)])
        self.l_room_cross_member()
        return left, right

    def l_room_cross_member(self):
        left_id = mapping(self.instance(1))[("primary", 3)]
        right_id = mapping(self.instance(2))[("primary", 4)]
        self.line("timber 93 27 33 role secondary")
        self.line(f"place 93 on 1 at-line grid 1 v 0 between t{left_id} t{right_id} +u +n")

    def test_br00_declared_capability_and_limits(self):
        state = self.read()["state"]
        self.assertIn(CAPABILITY, state.get("capabilities", []), "R06 native capability is absent")
        self.assertEqual(LIMITS, {k: state.get("limits", {}).get(k) for k in LIMITS})
        engineering = self.command("engineering-read")
        self.assertTrue(engineering.get("ok"), engineering)
        self.assertIn(CAPABILITY, engineering["state"].get("capabilities", []),
                      "I69: the project reader must advertise repeat support independently of current content")

    def test_br01_exact_rectangle_native_preview_and_confirm(self):
        before = self.stable()
        preview = self.request([self.create()])
        self.assertTrue(preview["valid"], killer("br01:rectangle-valid", preview))
        self.assertEqual(before, self.stable())
        instances = preview.get("after", {}).get("instances", [])
        self.assertEqual(1, len(instances), preview)
        got = {k: g["length"] for k, g in self.geometry(instances[0]).items()}
        self.assertEqual(self.rectangle_expected(), got, killer("br01:all-bays", got))
        self.assertEqual({(101, 10, 20), (101, 20, 30), (202, 10, 20), (202, 20, 30)},
                         {(c["line"], c["left"], c["right"]) for c in self.cell_rows(preview) if c["status"] == "generated"})
        self.assertTrue(self.command("assembly-confirm " + str(preview["token"]))["ok"])
        self.assertEqual(7, len(mapping(self.instance())))
        self.assertEqual(9, len(self.command("references")["timbers"]))
        self.assert_native_provenance(self.command, self.instance())
        for key, geometry in self.geometry().items():
            self.assertEqual((27, 33, "+n"), (geometry["A"], geometry["B"], geometry["side"]))
            self.assertEqual("+v" if key[0] == "primary" else "+u", geometry["dir"])

    def test_br02_outer_edges_are_primary_occurrences(self):
        source = self.source()
        source["primaries"] += [primary(5, {"kind": "outline-edge", "edge": 3}),
                                primary(40, {"kind": "outline-edge", "edge": 1})]
        preview = self.request([self.create(source)])
        self.assertTrue(preview["valid"], killer("br02:edge-valid", preview))
        expected = {("primary", k): 2960 for k in (5, 10, 20, 30, 40)}
        expected.update({("secondary", line, left, right): length for line in (101, 202)
                         for left, right, length in ((5, 10, 460), (10, 20, 973), (20, 30, 973), (30, 40, 1459))})
        actual = {k: g["length"] for k, g in self.geometry(preview["after"]["instances"][0]).items()}
        self.assertEqual(expected, actual, killer("br02:edge-offset", actual))

    def test_br03_l_room_uses_per_line_adjacency(self):
        _, source = self.l_room(create_right=False)
        preview = self.request([self.create(source)])
        self.assertTrue(preview["valid"], killer("br03:line-adjacency", preview))
        self.assertTrue(self.command("assembly-confirm " + str(preview["token"]))["ok"])
        self.l_room_cross_member()
        left = {k: g["length"] for k, g in self.geometry(self.instance(1)).items()}
        right = {k: g["length"] for k, g in self.geometry(self.instance(2)).items()}
        expected_left = {("primary", k): 2960 for k in (1, 2, 3)}
        expected_left.update({("secondary", line, a, b): length for line in (101, 202)
                              for a, b, length in ((1, 2, 460), (2, 3, 973))})
        expected_right = {("primary", k): 1460 for k in (4, 5, 6)}
        expected_right.update({("secondary", 101, 4, 5): 973, ("secondary", 101, 5, 6): 459})
        refs = {r["id"]: r["geometry"]["length"] for r in self.command("references")["timbers"]}
        self.assertEqual((expected_left, expected_right, 2486, 973, 16),
                         (left, right, refs[92], refs[93], len(refs)))

    def test_br03n_selected_endpoint_dependency_reports_self_support(self):
        left, right = self.l_room()
        left["primaries"] += deepcopy(right["primaries"])
        observation, preview, violations = self.rejection([self.edit(left)], "UNSUPPORTED", "SELF_SUPPORT")
        self.assertEqual({"valid": False, "matched": True, "unchanged": True}, observation,
                         killer("br03n:selected-stop-closure", preview))
        target = mapping(self.instance())[("primary", 3)]
        self.assertTrue(any(v.get("ownedTimberId") == target and
                            {"kind": "timber", "id": 92} in v.get("dependencyPath", []) and
                            {"kind": "timber", "id": target} in v.get("dependencyPath", []) for v in violations), preview)

    def test_br03n_automatic_endpoint_without_between_is_self_support(self):
        left, right = self.l_room(create_right=False)
        self.line("place 92 on 1 at-face e2 +u +n")
        support = next(t for t in self.command("references")["timbers"] if t["id"] == 92)
        self.assertEqual("", support["definition"]["selector"])
        self.assertEqual(2486, support["geometry"]["length"])
        left["primaries"] += deepcopy(right["primaries"])
        observed, preview, violations = self.rejection([self.edit(left)], "UNSUPPORTED", "SELF_SUPPORT")
        self.assertEqual({"valid": False, "matched": True, "unchanged": True}, observed,
                         killer("br03n:automatic-stop-closure", preview))
        target = mapping(self.instance())[("primary", 3)]
        self.assertTrue(any(v.get("ownedTimberId") == target and
                            {"kind": "timber", "id": 92} in v.get("dependencyPath", []) and
                            {"kind": "timber", "id": target} in v.get("dependencyPath", []) for v in violations), preview)

    def test_br04_insert_removes_old_identity_before_evaluation(self):
        self.apply([self.create()])
        before = mapping(self.instance())
        preview = self.request([self.edit(self.insert())])
        self.assertTrue(preview["valid"], killer("br04:minus-deleted-world", preview))
        self.assertTrue(self.command("assembly-confirm " + str(preview["token"]))["ok"])
        after = mapping(self.instance())
        removed = {("secondary", line, 10, 20) for line in (101, 202)}
        created = {( "secondary", line, a, b) for line in (101, 202) for a, b in ((10, 15), (15, 20))}
        created.add(("primary", 15))
        self.assertEqual((set(before) - removed) | created, set(after), killer("br04:full-identity", after))
        self.assertEqual({k: v for k, v in before.items() if k not in removed}, {k: after[k] for k in before if k not in removed})
        gone_ids = {before[k] for k in removed}
        present_ids = {r["id"] for r in self.command("references")["timbers"]}
        self.assertEqual(set(), gone_ids & (set(after.values()) | present_ids), killer("br04:no-id-reuse", after))
        self.assertTrue(all(self.geometry()[k]["length"] == 473 for k in created if k[0] == "secondary"))

    def test_br05_external_consumer_blocks_deleted_bay_before_new_ids(self):
        self.apply([self.create()])
        tid = mapping(self.instance())[("secondary", 101, 10, 20)]
        self.line(f"guide 8 1 u timber:{tid}:v:lo")
        observation, preview, _ = self.rejection([self.edit(self.insert())], "INVALID", "OWNED_REFERENCED")
        self.assertEqual({"valid": False, "matched": True, "unchanged": True}, observation,
                         killer("br05:external-reference", preview))
        diagnostic = json.dumps(preview.get("violations", []), ensure_ascii=False)
        self.assertIn("8", diagnostic)
        self.assertIn(str(tid), diagnostic)

    def test_br06_grid_recompute_preserves_keys_and_cancel(self):
        self.apply([self.create()])
        before = self.stable()
        original = mapping(self.instance())
        response = self.command("line grid 1 on 1 u 500 1100 1600 2600 v 1000 2000")
        preview = response.get("preview", {})
        self.assertTrue(preview.get("valid"), killer("br06:recompute-valid", response))
        self.assertEqual(before, self.stable())
        self.assertTrue(self.command("line cancel-preview")["ok"])
        self.assertEqual(before, self.stable())
        self.line("grid 1 on 1 u 500 1100 1600 2600 v 1000 2000")
        actual = {k: g["length"] for k, g in self.geometry().items()}
        expected = self.rectangle_expected()
        for key in (("secondary", 101, 10, 20), ("secondary", 202, 10, 20)):
            expected[key] = 1073
        self.assertEqual((original, expected), (mapping(self.instance()), actual), killer("br06:stable-keys", actual))

    def test_br07_hole_failure_is_explicit_and_omit_is_not_automatic(self):
        self.fixture(hole=True)
        before = self.stable()
        preview = self.request([self.create()])
        self.assertFalse(preview["valid"], killer("br07:no-auto-omit", preview))
        failed = [c for c in self.cell_rows(preview) if c["status"] == "failed"]
        self.assertEqual([(202, 20, 30)], [(c["line"], c["left"], c["right"]) for c in failed])
        self.assertTrue(failed[0]["violations"])
        for violation in failed[0]["violations"]:
            self.assertTrue(all(k in violation for k in ("code", "clause", "expected", "actual")), violation)
        self.assertEqual(before, self.stable())
        source = self.source()
        source["omit"] = [{"line": 202, "left": 20, "right": 30}]
        self.apply([self.create(source)])
        self.assertEqual(6, len(mapping(self.instance())))
        self.assertNotIn(("secondary", 202, 20, 30), mapping(self.instance()))

    def test_br07_all_failed_cells_keep_individual_diagnostics(self):
        self.line("surface 1 origin 0 0 2500 u +x v +y outline 0,0 4000,0 4000,3000 0,3000 "
                  "hole 800,900 1000,900 1000,1100 800,1100 hole 1800,1900 2000,1900 2000,2100 1800,2100")
        before = self.stable()
        preview = self.request([self.create()])
        self.assertFalse(preview["valid"])
        failed = [c for c in self.cell_rows(preview) if c["status"] == "failed"]
        self.assertEqual({(101, 10, 20), (202, 20, 30)},
                         {(c["line"], c["left"], c["right"]) for c in failed},
                         killer("br07:every-failed-cell", failed))
        self.assertTrue(all(c["violations"] and all(all(key in v for key in ("clause", "expected", "actual"))
                                                   for v in c["violations"]) for c in failed))
        self.assertEqual(before, self.stable())

    def test_br08_partial_width_band_is_not_a_bay(self):
        _, right = self.l_room()
        right["secondaryLines"].append(line_source(303, grid_at(1, "v")))
        observation, preview, violations = self.rejection([self.edit(right, 2)], "INVALID", "PARTIAL_COVERAGE")
        self.assertEqual({"valid": False, "matched": True, "unchanged": True}, observation,
                         killer("br08:full-width-coverage", preview))
        self.assertEqual({4, 5, 6}, {v.get("primaryKey") for v in violations})
        self.assertTrue(all(v.get("lineKey") == 303 for v in violations), preview)

    def test_br09_unsupported_reference_kind_does_not_fallback(self):
        source = self.source()
        source["primaries"][0]["at"] = {"kind": "hole-edge", "hole": 0, "edge": 1}
        observation, preview, _ = self.rejection([self.create(source)], "UNSUPPORTED")
        self.assertEqual({"valid": False, "matched": True, "unchanged": True}, observation,
                         killer("br09:unsupported-kind", preview))

    def test_br09_primary_rule_slots_must_be_equal(self):
        value = rule()
        value["id"] = 2
        value["members"][1]["slotId"] = 2
        self.apply([{"op": "publish-rule", "value": value}], generation=False)
        bound = binding()
        bound["id"] = 2
        bound["rule"]["id"] = 2
        for slot in bound["slots"]:
            slot["orientation"] = "A"
        self.apply([{"op": "create-binding", "value": bound}], generation=False)
        source = self.source()
        fixed = next(r for r in self.read()["state"]["rules"] if r["value"]["id"] == 2)
        source["bindingId"] = 2
        source["rule"] = {"id": 2, "version": 1, "fingerprint": fixed["fingerprint"]}
        observation, preview, _ = self.rejection([self.create(source)], "UNSUPPORTED")
        self.assertEqual({"valid": False, "matched": True, "unchanged": True}, observation,
                         killer("br09:same-primary-slot", preview))

    def test_br09_actual_orthogonal_split_is_unsupported(self):
        value = rule(2)
        value["joints"] = [{"id": 1, "kind": "ortho-split", "scope": "cross", "continuousMember": 1,
                            "splitMembers": [2, 3], "side": "+u", "dir": "v"}]
        self.apply([{"op": "publish-rule", "value": value}], generation=False)
        bound = binding()
        bound["id"], bound["rule"]["id"] = 2, 2
        for slot in bound["slots"]:
            slot["orientation"] = "A"
        self.apply([{"op": "create-binding", "value": bound}], generation=False)
        source = self.source()
        source["bindingId"] = 2
        source["rule"] = {"id": 2, "version": 1, "fingerprint": next(r["fingerprint"] for r in self.read()["state"]["rules"] if r["value"]["id"] == 2)}
        observed, preview, _ = self.rejection([self.create(source)], "UNSUPPORTED")
        self.assertEqual({"valid": False, "matched": True, "unchanged": True}, observed,
                         killer("br09:ortho-split", preview))

    def test_br09_real_child_grid_is_not_promoted_to_main_grid(self):
        self.line("subgrid 2 parent 1 cell u line:0 line:1 v min line:0 divisions u 2 v 2")
        source = self.source()
        source["primaries"][0]["at"] = grid_at(0, grid=2)
        observed, preview, _ = self.rejection([self.create(source)], "UNSUPPORTED")
        self.assertEqual({"valid": False, "matched": True, "unchanged": True}, observed,
                         killer("br09:child-grid", preview))

    def test_br09_real_staggered_axis_requires_unsupported(self):
        source = self.configured_grid(u_stagger=100)
        observed, preview, _ = self.rejection([self.create(source)], "UNSUPPORTED")
        self.assertEqual({"valid": False, "matched": True, "unchanged": True}, observed,
                         killer("br09:phased-axis", preview))

    def test_br09_unreferenced_staggered_axis_does_not_ban_plain_axis(self):
        source = self.configured_grid(v_stagger=100)
        self.guide(101, "u", 1000)
        self.guide(202, "u", 2000)
        source["secondaryLines"] = [line_source(key, {"kind": "guide", "id": key}) for key in (101, 202)]
        preview = self.request([self.create(source)])
        self.assertTrue(preview["valid"], killer("br09:unreferenced-phase", preview))
        self.assertEqual(self.rectangle_expected(), {ident: g["length"] for ident, g in self.geometry(preview["after"]["instances"][0]).items()})

    def test_br09_upstream_phase_is_unsupported_and_atomic(self):
        self.apply([self.create(self.configured_grid())])
        before = self.stable()
        reply = self.command("line grid-system 2 name-hex 523036 main-along none u repeat 2500 1000 stagger 100 v repeat 1000 1000")
        preview = reply.get("preview", {})
        matched = any(v.get("category") == "UNSUPPORTED" and v.get("clause") == "D58/I69" for v in preview.get("violations", []))
        observed = dict(valid=preview.get("valid"), matched=matched, unchanged=before == self.stable())
        self.assertEqual(dict(valid=False, matched=True, unchanged=True), observed, killer("br09:upstream-phase", preview))

    def derived_host_source(self, split=False):
        # Public native PF setup, adapted from fixed-main test_panel_fill_host /
        # test_panel_fill_layout. No fake at-kind stands in for a derived face.
        self.foreign_transaction("engineering", [
            {"op": "publish-material", "value": {"id": "r06-board", "version": 1, "name": "R06 board", "kind": "panel", "width": 4000, "length": 3000, "thickness": "9"}},
            {"op": "put-parameter", "value": {"id": 90, "name": "cut limit", "fields": [{"id": 1, "name": "X", "type": "dimension", "input": "8"}]}}])
        if split:
            self.line("beam 20 along x from 7800 to 8200 at 1500 width 3200 depth 33 top 2542")
        self.foreign_transaction("panel-fill", [
            {"op": "put-finish-surface", "value": {"id": 1, "name": "R06 derived host", "boundaryId": 1,
             "frame": {"origin": [6000, 0, 2500], "U": "+X", "V": "+Y", "N": "+Z"}, "structureSide": 1, "obstacles": ["b20"] if split else []}},
            {"op": "put-panel-fill", "value": {"id": 1, "finishSurfaceId": 1, "panel": {"id": "r06-board", "version": 1},
             "lengthAlong": "v", "origin": [0, 0], "gap": 0, "pattern": "straight", "threshold": {"parameterId": 90, "fieldId": 1}}},
            {"op": "put-derived-placement", "value": {"id": 10, "fillId": 1, "h": 33}}])
        hosts = self.command("panel-fill-read")["state"]["derivedPlacements"]
        self.assertEqual({"id": 10, "fillId": 1, "h": 33}, hosts[0]["definition"])
        for identifier, edge in ((100, 0), (101, 2)):
            key = json.dumps([["e" + str(edge), 1 if split and edge == 0 else 0, 2 if split else 1]], separators=(",", ":")).encode().hex()
            self.line(f"timber {identifier} 20 33 role boundary")
            self.line(f"place {identifier} on 10 at-face key-hex:{key} +u +n")
        for identifier, axis, coordinate in ((10, "v", 500), (11, "v", 1500), (12, "v", 2500), (13, "u", 1000), (14, "u", 2000)):
            self.line(f"spec derived{identifier} {coordinate}")
            self.line(f"guide {identifier} 10 {axis} spec:derived{identifier}")
        source = self.source(surface=10)
        source["primaries"] = [primary(key, {"kind": "guide", "id": identifier}, (100, 101)) for key, identifier in ((10, 10), (20, 11), (30, 12))]
        source["secondaryLines"] = [line_source(101, {"kind": "guide", "id": 13}), line_source(202, {"kind": "guide", "id": 14})]
        return source

    def assert_derived_host_repeat(self, source, tag, expected=None):
        before = self.stable()
        preview = self.request([self.create(source)])
        self.assertTrue(preview["valid"], killer(tag, preview))
        self.assertEqual(self.rectangle_expected() if expected is None else expected,
                         {ident: g["length"] for ident, g in self.geometry(preview["after"]["instances"][0]).items()})
        self.assertTrue(self.command("assembly-confirm " + str(preview["token"]))["ok"])
        saved = self.stable()
        self.assertEqual(source, self.instance()["value"]["source"])
        path = self.directory / "derived-repeat.scene"
        path.write_text(saved["dump"], encoding="utf-8")
        with BridgeSession(self.binary, cwd=self.directory) as fresh:
            loaded = fresh.command("loadfile " + str(path))
            self.assertTrue(loaded["ok"], killer(tag, {"load": loaded, "dump": saved["dump"]}))
            self.assertEqual(saved["dump"], fresh.command("dump")["text"])
            self.assertEqual(saved["assembly"]["state"], fresh.command("assembly-read")["state"])
        self.assertTrue(self.command("line undo")["ok"])
        self.assertEqual(before["dump"], self.dump())
        self.assertTrue(self.command("line redo")["ok"])
        self.assertEqual(saved["dump"], self.dump())

    def test_br09_derived_host_guides_are_supported(self):
        self.assert_derived_host_repeat(self.derived_host_source(), "br09:derived-guide")

    def test_br09_derived_host_finite_grid_is_supported(self):
        source = self.derived_host_source()
        self.line("grid 10 on 10 u 500 1000 1500 2500 v 1000 2000")
        source["primaries"] = [primary(key, grid_at(index, grid=10), (100, 101))
                               for key, index in ((10, 0), (20, 2), (30, 3))]
        source["secondaryLines"] = [line_source(key, grid_at(index, "v", grid=10))
                                    for key, index in ((101, 0), (202, 1))]
        self.assert_derived_host_repeat(source, "br09:derived-finite-grid")

    def test_br12_repeat_with_unrelated_derived_host_replays(self):
        self.derived_host_source()
        self.assert_derived_host_repeat(self.source(), "br12:mixed-derived-host")

    def test_br02_derived_outer_edges_preserve_r41_keys(self):
        source = self.derived_host_source()
        surface = next(p for p in self.command("surfaces")["surfaces"] if p["id"] == 10)
        self.assertEqual({json.dumps([["e1", 0, 1]]), json.dumps([["e3", 0, 1]])},
                         {json.dumps(edge["edgeKey"]) for edge in surface["outerEdges"] if edge["axis"] == "v"},
                         killer("br02:derived-outline-options", surface))
        source["primaries"][0]["at"] = {"kind": "outline-edge", "edgeKey": [["e3", 0, 1]]}
        source["primaries"][2]["at"] = {"kind": "outline-edge", "edgeKey": [["e1", 0, 1]]}
        expected = {("primary", key): 2960 for key in (10, 20, 30)}
        expected.update({("secondary", line, left, right): length for line in (101, 202)
                         for left, right, length in ((10, 20, 1460), (20, 30, 2459))})
        self.assert_derived_host_repeat(source, "br02:derived-outline-key", expected)

    def test_br02_second_derived_component_uses_exact_outer_keys(self):
        source = self.derived_host_source(split=True)
        source["primaries"] = [primary(10, {"kind": "outline-edge", "edgeKey": [["b20:u+", 0, 1]]}, (100, 101)),
                               primary(30, {"kind": "outline-edge", "edgeKey": [["e1", 0, 1]]}, (100, 101))]
        expected = {("primary", key): 2960 for key in (10, 30)}
        expected.update({("secondary", line, 10, 30): 1746 for line in (101, 202)})
        self.assert_derived_host_repeat(source, "br02:derived-second-component", expected)

    def test_br02_derived_outer_keys_reject_alias_hole_stale_and_duplicate(self):
        self.fixture(hole=True)
        source = self.derived_host_source()
        for at in [{"kind": "outline-edge", "edge": 3},
                   {"kind": "outline-edge", "edgeKey": [["h0e1", 0, 1]]},
                   {"kind": "outline-edge", "edgeKey": [["e3", 0, 2]]}]:
            invalid = deepcopy(source)
            invalid["primaries"][0]["at"] = at
            observed, preview, _ = self.rejection([self.create(invalid)], "INVALID")
            self.assertEqual(dict(valid=False, matched=True, unchanged=True), observed,
                             killer("br02:derived-key-reject", preview))
        ordinary = self.source()
        ordinary["primaries"][0]["at"] = {"kind": "outline-edge", "edgeKey": [["e3", 0, 1]]}
        observed, preview, _ = self.rejection([self.create(ordinary)], "INVALID")
        self.assertEqual(dict(valid=False, matched=True, unchanged=True), observed, killer("br02:ordinary-key-reject", preview))
        duplicate = deepcopy(source)
        for p in duplicate["primaries"][:2]:
            p["at"] = {"kind": "outline-edge", "edgeKey": [["e3", 0, 1]]}
        observed, preview, _ = self.rejection([self.create(duplicate)], "INVALID")
        self.assertEqual(dict(valid=False, matched=True, unchanged=True), observed, killer("br02:duplicate-derived-key", preview))

    def test_br10_configured_main_grid_retains_signed_indices(self):
        source = self.configured_grid()
        preview = self.request([self.create(source)])
        self.assertTrue(preview["valid"], killer("br10:signed-grid", preview))
        self.assertTrue(self.command("assembly-confirm " + str(preview["token"]))["ok"])
        self.assertEqual(["-2", "-1", "0"], [p["at"]["index"] for p in self.instance()["value"]["source"]["primaries"]])
        self.assertEqual(self.rectangle_expected(), {ident: g["length"] for ident, g in self.geometry().items()})

    def test_br10_malformed_or_missing_references_reject_without_coercion(self):
        self.line("surface 2 origin 6000 0 2500 u +x v +y outline 0,0 4000,0 4000,3000 0,3000")
        self.line("spec remote 500")
        self.line("guide 99 2 v spec:remote")
        references = [{"kind": "guide", "id": 99}, {"kind": "guide", "id": 4294967295}, grid_at(0, grid=4294967295)]
        references += [grid_at(raw) for raw in ("", " 0", "1e", "1.0", "-1", "4", "9223372036854775808", "-9223372036854775809")]
        references.append({"kind": "grid-line", "gridId": 1, "axis": "u", "index": 0})
        for reference in references:
            with self.subTest(reference=reference):
                source = self.source()
                source["primaries"][0]["at"] = reference
                observed, _, _ = self.rejection([self.create(source)], "INVALID")
                self.assertEqual({"valid": False, "matched": True, "unchanged": True}, observed)

    def test_br06_source_order_and_names_do_not_change_identity_or_world_order(self):
        self.apply([self.create()])
        old = self.instance()
        old_order = [r["id"] for r in self.command("references")["timbers"]]
        source = deepcopy(old["value"]["source"])
        source["name"] = "same keys, changed labels and list order"
        source["primaries"].reverse()
        source["secondaryLines"].reverse()
        self.apply([self.edit(source)])
        self.assertEqual((old["value"]["mapping"], self.geometry(old), old_order),
                         (self.instance()["value"]["mapping"], self.geometry(), [r["id"] for r in self.command("references")["timbers"]]),
                         killer("br06:source-order-invariance"))

    def test_br04_new_ids_append_in_primary_then_sorted_tuple_order(self):
        source = self.source()
        source["primaries"].reverse()
        source["secondaryLines"].reverse()
        self.apply([self.create(source)])
        expected = [("primary", key) for key in (10, 20, 30)]
        expected += [("secondary", line, left, right) for line in (101, 202) for left, right in ((10, 20), (20, 30))]
        rows = self.instance()["value"]["mapping"]
        self.assertEqual(expected, [identity(r) for r in rows], killer("br04:new-order", rows))
        self.assertEqual([90, 91] + [r["timberId"] for r in rows], [r["id"] for r in self.command("references")["timbers"]])

    def test_br10_dangling_omit_is_not_deleted_or_retargeted(self):
        source = self.source()
        source["omit"] = [{"line": 202, "left": 10, "right": 30}]
        observation, preview, _ = self.rejection([self.create(source)], "INVALID", "OMIT_NOT_A_BAY")
        self.assertEqual({"valid": False, "matched": True, "unchanged": True}, observation,
                         killer("br10:dangling-omit", preview))

    def test_br10_duplicate_positive_keys_reject(self):
        source = self.source()
        source["primaries"][1]["key"] = 10
        observation, preview, _ = self.rejection([self.create(source)], "INVALID")
        self.assertEqual({"valid": False, "matched": True, "unchanged": True}, observation,
                         killer("br10:unique-keys", preview))

    def test_br10_position_axis_is_semantic_not_ui_orientation(self):
        source = self.source()
        source["primaries"][0]["at"] = grid_at(0, "v")
        observation, preview, _ = self.rejection([self.create(source)], "INVALID")
        self.assertEqual({"valid": False, "matched": True, "unchanged": True}, observation,
                         killer("br10:axis", preview))

    def test_br10_numeric_index_aliases_are_the_same_reference(self):
        source = self.source()
        source["primaries"][1]["at"] = grid_at("00")
        observation, preview, _ = self.rejection([self.create(source)], "INVALID")
        self.assertEqual({"valid": False, "matched": True, "unchanged": True}, observation)

    def test_br10_external_reference_zero_is_a_real_uint32_id(self):
        # D58 keys are positive; ordinary native object IDs are uint32 and zero
        # is a real object. This exercises surface, guide, grid and support zero
        # together, without relying on a nonexistent surface to reject first.
        self.line("placement 0 origin 6000 0 2500 u +x v +y rect 0 0 4000 3000")
        self.line("grid 0 on 0 u 500 1500 2500 v 1000 2000")
        self.line("spec brzero 500")
        self.line("guide 0 0 v spec:brzero")
        for identifier, edge in ((0, 0), (92, 2)):
            self.line(f"timber {identifier} 20 20 role boundary")
            self.line(f"place {identifier} on 0 at-face e{edge} +u +n")
        source = self.source(surface=0)
        source["primaries"] = [primary(10, {"kind": "guide", "id": 0}, (0, 92)),
                               primary(20, grid_at(1, grid=0), (0, 92)),
                               primary(30, grid_at(2, grid=0), (0, 92))]
        source["secondaryLines"] = [line_source(101, grid_at(0, "v", 0)),
                                    line_source(202, grid_at(1, "v", 0))]
        preview = self.request([self.create(source)])
        self.assertTrue(preview["valid"], killer("br10:zero-reference-id"))
        self.assertTrue(self.command("assembly-confirm " + str(preview["token"]))["ok"])
        self.assertEqual(source, self.instance()["value"]["source"])
        self.assertEqual(self.rectangle_expected(), {ident: value["length"] for ident, value in self.geometry().items()})

    def test_br10_null_external_reference_is_unselected_not_zero(self):
        for field in ("surface", "guide", "grid", "support"):
            source = self.source()
            if field == "surface":
                source["surfaceId"] = None
            elif field == "guide":
                source["primaries"][0]["at"] = {"kind": "guide", "id": None}
            elif field == "grid":
                source["primaries"][0]["at"]["gridId"] = None
            else:
                source["primaries"][0]["ends"]["start"]["id"] = None
            with self.subTest(field=field):
                observed, _, _ = self.rejection([self.create(source)], "INVALID")
                self.assertEqual({"valid": False, "matched": True, "unchanged": True}, observed)

    def test_br10_direct_owned_support_is_self_support(self):
        self.apply([self.create()])
        source = deepcopy(self.instance()["value"]["source"])
        source["primaries"][0]["ends"]["start"]["id"] = mapping(self.instance())[("secondary", 101, 10, 20)]
        observation, preview, _ = self.rejection([self.edit(source)], "UNSUPPORTED", "SELF_SUPPORT")
        self.assertEqual({"valid": False, "matched": True, "unchanged": True}, observation,
                         killer("br10:direct-self-support", preview))

    def test_br10b_all_omitted_line_is_preserved_and_legal(self):
        source = self.source()
        source["omit"] = [{"line": line, "left": left, "right": right}
                          for line in (101, 202) for left, right in ((10, 20), (20, 30))]
        preview = self.request([self.create(source)])
        self.assertTrue(preview["valid"], killer("br10b:zero-generated", preview))
        self.assertTrue(all(c["status"] == "omitted" for c in self.cell_rows(preview)))
        self.assertTrue(self.command("assembly-confirm " + str(preview["token"]))["ok"])
        self.assertEqual(source["secondaryLines"], self.instance()["value"]["source"]["secondaryLines"])
        self.assertEqual({("primary", k) for k in (10, 20, 30)}, set(mapping(self.instance())))

    def test_br11_former_owned_overflow_56_is_fully_accepted(self):
        self.fixture(height=4000)
        self.replace_fixture_grid("grid 1 on 1 u 300 900 1500 2100 2700 3300 v 300 600 900 1200 1500 1800 2100 2400 2700 3000")
        source = self.source()
        source["primaries"] = [primary(i + 1, grid_at(i)) for i in range(6)]
        source["secondaryLines"] = [line_source(i + 1, grid_at(i, "v")) for i in range(10)]
        before = self.stable()
        preview = self.request([self.create(source)])
        self.assertTrue(preview["valid"], killer("br11:legacy56-accepted", preview))
        self.assertEqual(before, self.stable())
        expected = {("primary", key): 3960 for key in range(1, 7)}
        expected.update({("secondary", line, left, left + 1): 573
                         for line in range(1, 11) for left in range(1, 6)})
        self.assertEqual(56, len(expected))
        self.assertEqual(expected, {key: value["length"] for key, value in
                                   self.geometry(preview["after"]["instances"][0]).items()})
        self.assertTrue(self.command("assembly-confirm " + str(preview["token"]))["ok"])
        self.assertEqual(56, len(mapping(self.instance())))
        self.assertEqual(58, len(self.command("references")["timbers"]))

    def test_br11_generates_116_members_with_cancel_history_and_fresh_replay(self):
        self.fixture(height=4000)
        self.replace_fixture_grid("grid 1 on 1 u 300 900 1500 2100 2700 3300 v " +
                                  " ".join(str(150 + 150 * i) for i in range(22)))
        source = self.source()
        source["primaries"] = [primary(i + 1, grid_at(i)) for i in range(6)]
        source["secondaryLines"] = [line_source(i + 1, grid_at(i, "v")) for i in range(22)]
        # Independent integer oracle: six 3960 mm primaries and five 573 mm
        # clear spans on each of 22 lines; the two boundary supports are extra.
        expected = {("primary", key): 3960 for key in range(1, 7)}
        expected.update({("secondary", line, left, left + 1): 573
                         for line in range(1, 23) for left in range(1, 6)})
        self.assertEqual(116, len(expected))
        before = self.stable()
        preview = self.request([self.create(source)])
        self.assertTrue(preview["valid"], killer("br11:capacity116-valid", preview))
        self.assertEqual(before, self.stable(), "a 116-member preview cannot write the World")
        instances = preview["after"]["instances"]
        self.assertEqual(1, len(instances))
        geometry = self.geometry(instances[0])
        self.assertEqual(expected, {key: value["length"] for key, value in geometry.items()},
                         killer("br11:capacity116-geometry", geometry))
        self.assertEqual(116, len(mapping(instances[0])))
        self.assertEqual(116, len(set(mapping(instances[0]).values())))
        cells = self.cell_rows(preview)
        self.assertEqual(110, len(cells))
        self.assertEqual({(line, left, left + 1) for line in range(1, 23) for left in range(1, 6)},
                         {(cell["line"], cell["left"], cell["right"]) for cell in cells
                          if cell["status"] == "generated"})
        self.assertTrue(self.command("assembly-cancel " + str(preview["token"]))["ok"])
        self.assertFalse(self.command("assembly-confirm " + str(preview["token"]))["ok"])
        self.assertEqual(before, self.stable(), "cancelled 116-member token must stay inert")

        current = self.request([self.create(source)])
        self.assertTrue(current["valid"], current)
        self.assertNotEqual(preview["token"], current["token"])
        self.assertTrue(self.command("assembly-confirm " + str(current["token"]))["ok"])
        instance = self.instance()
        self.assertEqual(source, instance["value"]["source"])
        self.assertEqual(mapping(instances[0]), mapping(instance))
        self.assertEqual(expected, {key: value["length"] for key, value in self.geometry(instance).items()})
        self.assertEqual(118, len(self.command("references")["timbers"]))
        for key, value in self.geometry(instance).items():
            self.assertEqual((27, 33, "+n"), (value["A"], value["B"], value["side"]))
            self.assertEqual("+v" if key[0] == "primary" else "+u", value["dir"])
        self.assert_native_provenance(self.command, instance)
        created = self.stable()
        self.assertTrue(self.command("line undo")["ok"])
        self.assertEqual(before["dump"], self.dump())
        self.assertEqual(before["assembly"]["state"], self.read()["state"])
        self.assertTrue(self.command("line redo")["ok"])
        self.assertEqual(created["dump"], self.dump())
        self.assertEqual(created["assembly"]["state"], self.read()["state"])

        path = self.directory / "repeat-116.scene"
        path.write_text(created["dump"], encoding="utf-8")
        with BridgeSession(self.binary, cwd=self.directory) as fresh:
            loaded = fresh.command("loadfile " + str(path))
            self.assertTrue(loaded.get("ok"), killer("br11:capacity116-replay", loaded))
            self.assertEqual(created["dump"], fresh.command("dump")["text"])
            state = fresh.command("assembly-read")["state"]
            self.assertEqual(created["assembly"]["state"], state)
            self.assertEqual(118, len(fresh.command("references")["timbers"]))
            self.assert_native_provenance(fresh.command, state["instances"][0])

    def test_br11_instance_count_accepts_16_and_rejects_17_atomically(self):
        self.replace_fixture_grid("grid 1 on 1 u " + " ".join(str(i * 100) for i in range(1, 35)) + " v 1000 2000")
        def value(identifier):
            source = self.source(identifier)
            source["primaries"] = [primary(10, grid_at((identifier - 1) * 2)), primary(20, grid_at((identifier - 1) * 2 + 1))]
            source["secondaryLines"] = [line_source(101, grid_at(0, "v"))]
            source["omit"] = [{"line": 101, "left": 10, "right": 20}]
            return source
        preview = self.request([self.create(value(i)) for i in range(1, 17)])
        self.assertTrue(preview["valid"], killer("br11:instance-boundary-accepted", preview))
        self.assertTrue(self.command("assembly-confirm " + str(preview["token"]))["ok"])
        self.assertEqual(16, len(self.read()["state"]["instances"]))
        observed, rejected, _ = self.rejection([self.create(value(17))], "CAPACITY")
        self.assertEqual({"valid": False, "matched": True, "unchanged": True}, observed,
                         killer("br11:instance-capacity", rejected))

    def test_br11_input_count_capacity_precedes_truncation(self):
        source = self.source()
        source["primaries"] = [primary(i + 1, grid_at(i)) for i in range(13)]
        observation, preview, _ = self.rejection([self.create(source)], "CAPACITY", "CAPACITY")
        self.assertEqual({"valid": False, "matched": True, "unchanged": True}, observation,
                         killer("br11:primary-capacity", preview))

    def test_br11_primary_count_has_valid_12_and_overflow_13(self):
        self.replace_fixture_grid("grid 1 on 1 u " + " ".join(str(200 + 280 * i) for i in range(13)) + " v 1000")
        source = self.source()
        source["primaries"] = [primary(i + 1, grid_at(i)) for i in range(12)]
        source["secondaryLines"] = [line_source(1, grid_at(0, "v"))]
        preview = self.request([self.create(source)])
        self.assertTrue(preview["valid"], preview)
        self.command("assembly-cancel " + str(preview["token"]))
        source["primaries"].append(primary(13, grid_at(12)))
        observation, preview, _ = self.rejection([self.create(source)], "CAPACITY", "CAPACITY")
        self.assertEqual({"valid": False, "matched": True, "unchanged": True}, observation)

    def test_br11_secondary_line_count_has_valid_24_and_overflow_25(self):
        self.replace_fixture_grid("grid 1 on 1 u 500 2500 v " + " ".join(str(100 + 100 * i) for i in range(25)))
        source = self.source()
        source["primaries"] = [primary(1, grid_at(0)), primary(2, grid_at(1))]
        source["secondaryLines"] = [line_source(i + 1, grid_at(i, "v")) for i in range(24)]
        preview = self.request([self.create(source)])
        self.assertTrue(preview["valid"], preview)
        self.command("assembly-cancel " + str(preview["token"]))
        source["secondaryLines"].append(line_source(25, grid_at(24, "v")))
        observation, preview, _ = self.rejection([self.create(source)], "CAPACITY", "CAPACITY")
        self.assertEqual({"valid": False, "matched": True, "unchanged": True}, observation,
                         killer("br11:line-capacity", preview))

    def test_br11_omit_count_has_valid_24_and_overflow_25(self):
        self.replace_fixture_grid("grid 1 on 1 u 500 1500 2500 3500 v " + " ".join(str(200 + 200 * i) for i in range(9)))
        source = self.source()
        source["primaries"] = [primary(i + 1, grid_at(i)) for i in range(4)]
        source["secondaryLines"] = [line_source(i + 1, grid_at(i, "v")) for i in range(9)]
        cells = [{"line": line, "left": left, "right": left + 1} for line in range(1, 10) for left in range(1, 4)]
        source["omit"] = cells[:24]
        preview = self.request([self.create(source)])
        self.assertTrue(preview["valid"], preview)
        self.command("assembly-cancel " + str(preview["token"]))
        source["omit"] = cells[:25]
        observation, preview, _ = self.rejection([self.create(source)], "CAPACITY", "CAPACITY")
        self.assertEqual({"valid": False, "matched": True, "unchanged": True}, observation,
                         killer("br11:omit-capacity", preview))

    def test_br11_owned_capacity_is_global_across_instances(self):
        coordinates = "u 500 1500 2500 3500 v 300 600 900 1200 1500 1800 2100"
        self.replace_fixture_grid("grid 1 on 1 " + coordinates)
        self.line("surface 2 origin 5000 0 2500 u +x v +y outline 0,0 4000,0 4000,3000 0,3000")
        self.line("grid 2 on 2 " + coordinates)
        for tid, edge in ((190, 0), (191, 2)):
            self.line(f"timber {tid} 20 20 role boundary")
            self.line(f"place {tid} on 2 at-face e{edge} +u +n")
        sources = []
        for identifier, ends in ((1, (90, 91)), (2, (190, 191))):
            source = self.source(identifier, identifier)
            source["primaries"] = [primary(i + 1, grid_at(i, grid=identifier), ends) for i in range(4)]
            source["secondaryLines"] = [line_source(i + 1, grid_at(i, "v", identifier)) for i in range(7)]
            source["omit"] = [{"line": 7, "left": 3, "right": 4}]
            sources.append(source)
        empty_fixture = self.dump()
        self.apply([self.create(source) for source in sources])
        self.assertEqual([24, 24], [len(mapping(self.instance(i))) for i in (1, 2)])
        original = self.stable()
        source = deepcopy(sources[0]); source["omit"] = []
        accepted = self.request([self.edit(source)])
        self.assertTrue(accepted["valid"], killer("br11:global49-accepted", accepted))
        self.assertEqual(original, self.stable())
        self.assertTrue(self.command("assembly-confirm " + str(accepted["token"]))["ok"])
        self.assertEqual([25, 24], [len(mapping(self.instance(i))) for i in (1, 2)])
        self.assertEqual(53, len(self.command("objects")["timbers"]))
        self.assertTrue(self.command("line undo")["ok"])
        self.assertEqual(original["dump"], self.dump())

        # Complete the ordinary source graph before creating either instance.
        # Four original supports plus 460 ordinary placed members leave exactly
        # 48 free slots; the two repeat instances must fill all 512 together.
        heads, declarations, placements = [], [], []
        next_id = 1000
        for room in range(14):
            surface = room + 3
            count = 31 if room < 12 else 30
            bottom, top = next_id, next_id + 1
            heads.extend([
                f"surface {surface} origin {10000 + 40000 * room} 0 2500 u +x v +y outline 0,0 32000,0 32000,3000 0,3000",
                f"grid {surface} on {surface} u " + " ".join(str(500 + 1000 * i) for i in range(count)),
            ])
            declarations.extend([f"timber {bottom} 20 20 role boundary", f"timber {top} 20 20 role boundary"])
            placements.extend([f"place {bottom} on {surface} at-face e0 +u +n",
                               f"place {top} on {surface} at-face e2 +u +n"])
            for index in range(count):
                tid = bottom + 2 + index
                declarations.append(f"timber {tid} 27 33 role primary")
                placements.append(f"place {tid} on {surface} at-line grid {surface} u {index} between t{bottom} t{top} +v +n")
            next_id += count + 2
        self.assertEqual(1460, next_id)
        path = self.directory / "repeat-mixed-ordinary-464.scene"
        path.write_text("\n".join(heads + declarations + placements) + "\n" + empty_fixture, encoding="utf-8")
        self.assertTrue(self.command("loadfile " + str(path))["ok"])
        self.assertEqual([], self.read()["state"]["instances"])
        self.assertEqual(464, len(self.command("objects")["timbers"]))
        admitted = self.request([self.create(value) for value in sources])
        self.assertTrue(admitted["valid"], killer("br11:world512-accepted", admitted))
        self.assertTrue(self.command("assembly-confirm " + str(admitted["token"]))["ok"])
        declared = []
        for text in self.dump().splitlines():
            words = text.split()
            if words and (words[0] == "timber" or (words[0] == "owned" and "timber" in words)):
                declared.append(int(words[words.index("timber") + 1]))
        expected_ids = {90, 91, 190, 191} | set(range(1000, 1460))
        expected_ids.update(mapping(self.instance(1)).values())
        expected_ids.update(mapping(self.instance(2)).values())
        self.assertEqual(512, len(declared))
        self.assertEqual(512, len(set(declared)))
        self.assertEqual(expected_ids, set(declared))
        self.assertEqual(512, len(self.command("objects")["timbers"]))
        self.assertEqual([24, 24], [len(mapping(self.instance(i))) for i in (1, 2)])
        full = self.stable()
        observation, preview, _ = self.rejection([self.edit(source)], "CAPACITY", "CAPACITY")
        self.assertEqual({"valid": False, "matched": True, "unchanged": True}, observation,
                         killer("br11:global-owned-capacity", preview))
        self.assertFalse(self.command("assembly-confirm " + str(preview["token"]))["ok"])
        self.assertEqual(full, self.stable())
        self.assertEqual(512, len(self.command("objects")["timbers"]))

    def test_br11_instance_record_exact_byte_boundary(self):
        source = self.source()
        preview = self.request([self.create(source)])
        self.assertTrue(preview["valid"], preview)
        value = preview["after"]["instances"][0]["value"]
        size = len(json.dumps(value, ensure_ascii=False, separators=(",", ":")).encode("utf-8"))
        limit = LIMITS["instanceRecordBytes"]
        self.assertLess(size, limit)
        # A field larger than 8192 but a complete record smaller than 32768
        # distinguishes the source field buffer from the whole-index buffer.
        field_source = deepcopy(source)
        field_source["primaries"][0]["at"]["index"] = "0" * (9000 - size) + "0"
        field_preview = self.request([self.create(field_source)])
        self.assertTrue(field_preview["valid"], field_preview)
        field_value = field_preview["after"]["instances"][0]["value"]
        self.assertEqual(9000, len(json.dumps(field_value, ensure_ascii=False, separators=(",", ":")).encode("utf-8")))
        self.assertGreater(len(json.dumps(field_value["source"], ensure_ascii=False,
                                          separators=(",", ":")).encode("utf-8")), 8192)
        self.assertTrue(self.command("assembly-confirm " + str(field_preview["token"]))["ok"])
        field_graph = self.command("source-inspect")
        self.assertTrue(field_graph.get("ok") and field_graph.get("complete"),
                        killer("br11:record-field-complete", field_graph))
        self.assertEqual(field_value, self.instance()["value"])
        # Decimal leading zeroes do not change the signed index or its source
        # identity. They remain source text, allowing an exact byte boundary
        # without an unknown field, invalid geometry or another capacity limit.
        source["primaries"][0]["at"]["index"] = "0" * (limit - size) + "0"
        accepted = self.request([self.edit(source)])
        self.assertTrue(accepted["valid"], killer("br11:record-boundary-accepted", accepted))
        saved = accepted["after"]["instances"][0]["value"]
        self.assertEqual(limit, len(json.dumps(saved, ensure_ascii=False, separators=(",", ":")).encode("utf-8")))
        self.assertTrue(self.command("assembly-confirm " + str(accepted["token"]))["ok"])
        instance = self.instance()
        self.assertEqual(saved, instance["value"])
        self.assertEqual(7, len(mapping(instance)))
        graph = self.command("source-inspect")
        self.assertTrue(graph.get("ok") and graph.get("complete"),
                        killer("br11:record-source-complete", graph))
        nodes = {node["key"]: node for node in graph["nodes"]}
        content = "".join(key + "=" + json.dumps(saved[key], ensure_ascii=False, sort_keys=True,
                                              separators=(",", ":")) + ";" for key in ("mapping", "source"))
        expected_definition = hashlib.sha256(content.encode("utf-8")).hexdigest()
        self.assertEqual(expected_definition, nodes["assembly-instance:1"]["definitionFingerprint"])
        self.assertEqual(expected_definition, nodes["assembly-instance:1"]["valueFingerprint"])
        self.assert_native_provenance(self.command, instance)
        source["primaries"][0]["at"]["index"] += "0"
        observation, rejected, _ = self.rejection([self.edit(source)], "CAPACITY", "CAPACITY")
        self.assertEqual({"valid": False, "matched": True, "unchanged": True}, observation,
                         killer("br11:record-byte-capacity", rejected))

    def test_br11_former_world_boundary_64_and_65_are_fully_accepted(self):
        self.line("surface 2 origin 5000 0 2500 u +x v +y outline 0,0 60000,0 60000,3000 0,3000")
        self.line("grid 2 on 2 u " + " ".join(str(500 + 1000 * i) for i in range(54)))
        for tid, edge in ((190, 0), (191, 2)):
            self.line(f"timber {tid} 20 20 role boundary")
            self.line(f"place {tid} on 2 at-face e{edge} +u +n")
        for i in range(53):
            self.line(f"timber {1000 + i} 27 33 role primary")
            self.line(f"place {1000 + i} on 2 at-line grid 2 u {i} between t190 t191 +v +n")
        self.assertEqual(57, len(self.command("references")["timbers"]))
        preview = self.request([self.create()])
        self.assertTrue(preview["valid"], preview)  # 57 external + 7 generated = 64.
        self.command("assembly-cancel " + str(preview["token"]))
        self.line("timber 1053 27 33 role primary")
        self.line("place 1053 on 2 at-line grid 2 u 53 between t190 t191 +v +n")
        before = self.stable()
        preview = self.request([self.create()])
        self.assertTrue(preview["valid"], killer("br11:legacy65-accepted", preview))
        self.assertEqual(before, self.stable())
        self.assertEqual(self.rectangle_expected(), {key: value["length"] for key, value in
                                                   self.geometry(preview["after"]["instances"][0]).items()})
        self.assertTrue(self.command("assembly-confirm " + str(preview["token"]))["ok"])
        self.assertEqual(65, len(self.command("references")["timbers"]))
        self.assertEqual(7, len(mapping(self.instance())))

    def test_br11_mixed_repeat_and_legacy_owners_above_48_fresh_replay(self):
        self.line("surface 2 origin 5000 0 2500 u +x v +y outline 0,0 4000,0 4000,3000 0,3000")
        self.line("grid 2 on 2 u 500 1500 2500 3500 v " +
                  " ".join(str(100 + 150 * i) for i in range(15)))
        for tid, edge in ((190, 0), (191, 2)):
            self.line(f"timber {tid} 20 20 role boundary")
            self.line(f"place {tid} on 2 at-face e{edge} +u +n")
        repeat = self.source(surface=2)
        repeat["primaries"] = [primary(i + 1, grid_at(i, grid=2), (190, 191)) for i in range(4)]
        repeat["secondaryLines"] = [line_source(i + 1, grid_at(i, "v", 2)) for i in range(15)]
        repeat["omit"] = [{"line": 15, "left": 3, "right": 4}]
        self.apply([self.create(repeat)])
        self.assertEqual(48, len(mapping(self.instance())))
        for gid, axis, coordinate in ((1, "v", 500), (2, "v", 2500), (3, "u", 1500)):
            self.guide(gid, axis, coordinate)
        legacy = self.source(identifier=2)
        for field in ("layout", "primaries", "secondaryLines", "omit"):
            del legacy[field]
        legacy["members"] = [{"memberId": i, "role": "primary" if i < 3 else "secondary", "guideId": i,
                              "dir": "+v" if i < 3 else "+u", "depthSide": "+n",
                              "ends": primary(1, {})["ends"] if i < 3 else
                              {"start": {"kind": "member", "memberId": 1}, "finish": {"kind": "member", "memberId": 2}}}
                             for i in (1, 2, 3)]
        preview = self.request([self.create(legacy)])
        self.assertTrue(preview["valid"], killer("br11:mixed51-valid", preview))
        self.assertTrue(self.command("assembly-confirm " + str(preview["token"]))["ok"])
        self.assertEqual(55, len(self.command("objects")["timbers"]))
        self.assertEqual([2960, 2960, 1973], [member["geometry"]["length"]
                                           for member in self.instance(2)["members"]])
        created = self.stable()
        path = self.directory / "repeat48-legacy3.scene"
        path.write_text(created["dump"], encoding="utf-8")
        with BridgeSession(self.binary, cwd=self.directory) as fresh:
            loaded = fresh.command("loadfile " + str(path))
            self.assertTrue(loaded.get("ok"), killer("br11:mixed51-replay", loaded))
            self.assertEqual(created["dump"], fresh.command("dump")["text"])
            self.assertEqual(created["assembly"]["state"], fresh.command("assembly-read")["state"])
            self.assertEqual(55, len(fresh.command("objects")["timbers"]))

        def padded_legacy_record(size):
            rows = created["dump"].splitlines(keepends=True)
            for start, row in enumerate(rows):
                if not row.startswith("assembly record "):
                    continue
                meta = json.loads(base64.b64decode(row.split()[2]))
                if meta.get("kind") != "instance":
                    continue
                end, chunks = start + 1, []
                while rows[end].startswith("assembly data "):
                    chunks.append(base64.b64decode(rows[end].split()[2])); end += 1
                self.assertEqual("assembly commit\n", rows[end])
                original = b"".join(chunks)
                value = json.loads(original)
                if value["source"]["id"] != 2:
                    continue
                self.assertNotIn("layout", value["source"])
                self.assertLess(len(original), size)
                padded = b" " * (size - len(original)) + original
                self.assertEqual(value, json.loads(padded))
                meta.update(bytes=len(padded), sha256=hashlib.sha256(padded).hexdigest())
                replacement = ["assembly record " + base64.b64encode(
                    json.dumps(meta, separators=(",", ":")).encode()).decode() + "\n"]
                replacement += ["assembly data " + base64.b64encode(padded[i:i + 768]).decode() + "\n"
                                for i in range(0, len(padded), 768)]
                rows[start:end] = replacement
                return "".join(rows)
            self.fail("fixture must contain the separate legacy instance record")

        # Both transports contain the same valid legacy JSON and correct hash.
        # The larger bay-record allowance must not widen the legacy raw limit.
        path = self.directory / "legacy-record-8191.scene"
        path.write_text(padded_legacy_record(8191), encoding="utf-8")
        self.assertTrue(self.command("loadfile " + str(path))["ok"])
        self.assertEqual(created["dump"], self.dump())
        self.assertEqual(created["assembly"]["state"], self.read()["state"])
        before = self.stable()
        path = self.directory / "legacy-record-8192.scene"
        path.write_text(padded_legacy_record(8192), encoding="utf-8")
        rejected = self.command("loadfile " + str(path))
        self.assertEqual((False, before), (rejected.get("ok"), self.stable()),
                         killer("br11:legacy-record-raw-capacity", rejected))
        self.assertIn("CAPACITY", json.dumps(rejected, ensure_ascii=False))

    def test_br12_fresh_native_replay_preserves_definitions_and_mapping(self):
        source = self.source()
        source["omit"] = [{"line": 202, "left": 20, "right": 30}]
        self.apply([self.create(source)])
        before = self.stable()
        path = self.directory / "repeat.scene"
        path.write_text(before["dump"], encoding="utf-8")
        with BridgeSession(self.binary, cwd=self.directory) as fresh:
            result = fresh.command("loadfile " + str(path))
            self.assertTrue(result.get("ok"), killer("br12:replay-accepted", result))
            actual = {"dump": fresh.command("dump")["text"], "state": fresh.command("assembly-read")["state"]}
            self.assert_native_provenance(fresh.command, actual["state"]["instances"][0])
            candidate = fresh.command("load-prepare " + str(path))
            self.assertTrue(candidate.get("ok"), candidate)
            for capability in (CAPABILITY, "assembly-timber-generation/1"):
                self.assertIn(capability, candidate.get("capabilities", []),
                              "I69: detached project candidates must advertise both generation capabilities")
                self.assertIn(capability, candidate.get("required_capabilities", []),
                              "I69: repeat scene candidates must require both generation capabilities")
            self.assertTrue(fresh.command("load-cancel " + str(candidate["token"]))["cancelled"])
        self.assertEqual({"dump": before["dump"], "state": before["assembly"]["state"]}, actual,
                         killer("br12:replay-mapping", actual))
        self.assertIn("requires " + CAPABILITY + "\n", before["dump"])
        self.assertIn("requires assembly-timber-generation/1\n", before["dump"])

    def test_br12_stripped_native_capability_rejects_atomically(self):
        self.apply([self.create()])
        before = self.stable()
        path = self.directory / "stripped.scene"
        path.write_text(before["dump"].replace("requires " + CAPABILITY + "\n", ""), encoding="utf-8")
        response = self.command("loadfile " + str(path))
        self.assertEqual((False, before), (response.get("ok"), self.stable()),
                         killer("br12:required-capability", response))

    def test_br12_forged_mapping_with_valid_record_hash_rejects(self):
        self.apply([self.create()])
        before = self.stable()
        rows = before["dump"].splitlines(keepends=True)
        changed = False
        for start, row in enumerate(rows):
            if not row.startswith("assembly record "):
                continue
            meta = json.loads(base64.b64decode(row.split()[2]))
            if meta.get("kind") != "instance":
                continue
            end = start + 1
            chunks = []
            while rows[end].startswith("assembly data "):
                chunks.append(base64.b64decode(rows[end].split()[2])); end += 1
            self.assertEqual("assembly commit\n", rows[end])
            value = json.loads(b"".join(chunks))
            # A permutation preserves all timber IDs and count, but changes the
            # stable owner identities. Recompute the transport checksum so this
            # reaches ownership verification rather than a corrupt-hash guard.
            value["mapping"][0]["timberId"], value["mapping"][1]["timberId"] = value["mapping"][1]["timberId"], value["mapping"][0]["timberId"]
            encoded = json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode()
            meta.update(bytes=len(encoded), sha256=hashlib.sha256(encoded).hexdigest())
            replacement = ["assembly record " + base64.b64encode(json.dumps(meta, separators=(",", ":")).encode()).decode() + "\n"]
            replacement += ["assembly data " + base64.b64encode(encoded[i:i + 768]).decode() + "\n" for i in range(0, len(encoded), 768)]
            rows[start:end] = replacement
            changed = True
            break
        self.assertTrue(changed, "fixture must contain a native instance record")
        path = self.directory / "forged-mapping.scene"
        path.write_text("".join(rows), encoding="utf-8")
        response = self.command("loadfile " + str(path))
        self.assertEqual((False, before), (response.get("ok"), self.stable()),
                         killer("br12:forged-mapping", response))

    def test_br13_create_edit_delete_undo_redo_are_whole_transactions(self):
        original = self.dump()
        self.apply([self.create()])
        created = self.dump()
        self.apply([self.edit(self.insert())])
        edited = self.dump()
        self.apply([self.delete()])
        deleted = self.dump()
        backwards = []
        for _ in range(3):
            self.assertTrue(self.command("line undo")["ok"])
            backwards.append(self.dump())
        forwards = []
        for _ in range(3):
            self.assertTrue(self.command("line redo")["ok"])
            forwards.append(self.dump())
        self.assertEqual(([edited, created, original], [created, edited, deleted]), (backwards, forwards),
                         killer("br13:whole-history", backwards))

    def test_br13_cancelled_and_stale_tokens_never_commit(self):
        preview = self.request([self.create()])
        self.assertTrue(preview["valid"], preview)
        self.command("assembly-cancel " + str(preview["token"]))
        before = self.stable()
        cancelled = self.command("assembly-confirm " + str(preview["token"]))
        self.assertEqual((False, before), (cancelled.get("ok"), self.stable()),
                         killer("br13:cancelled-token", cancelled))
        preview = self.request([self.create()])
        self.assertTrue(preview["valid"], preview)
        self.line("spec unrelated 7")
        before = self.stable()
        stale = self.command("assembly-confirm " + str(preview["token"]))
        self.assertEqual((False, before), (stale.get("ok"), self.stable()), killer("br13:stale-token", stale))

    def test_br15_legacy_single_bay_mapping_and_geometry_remain_exact(self):
        for gid, axis, coordinate in ((1, "v", 500), (2, "v", 2500), (3, "u", 1500)):
            self.guide(gid, axis, coordinate)
        source = self.source()
        for field in ("layout", "primaries", "secondaryLines", "omit"):
            del source[field]
        source["members"] = [{"memberId": i, "role": "primary" if i < 3 else "secondary", "guideId": i,
                              "dir": "+v" if i < 3 else "+u", "depthSide": "+n",
                              "ends": primary(1, {})["ends"] if i < 3 else
                              {"start": {"kind": "member", "memberId": 1}, "finish": {"kind": "member", "memberId": 2}}}
                             for i in (1, 2, 3)]
        self.apply([self.create(source)])
        instance = self.instance()
        actual = (instance["value"]["source"], [(m["memberId"], m["geometry"]["length"]) for m in instance["members"]],
                  all(set(m) == {"memberId", "timberId"} for m in instance["value"]["mapping"]),
                  CAPABILITY in self.dump())
        self.assertEqual((source, [(1, 2960), (2, 2960), (3, 1973)], True, False), actual,
                         killer("br15:legacy-single-bay", actual))

    def test_br16_upstream_reference_preview_contains_native_created_rows(self):
        for gid, coordinate in ((1, 500), (2, 1500), (3, 2500)):
            self.guide(gid, "v", coordinate)
        source = self.source()
        for member, gid in zip(source["primaries"], (1, 2, 3)):
            member["at"] = {"kind": "guide", "id": gid}
        self.apply([self.create(source)])
        before = self.stable()
        response = self.command("line spec brguide1 2000")
        preview = response.get("preview", {})
        self.assertTrue(preview.get("valid"), response)
        # The native reference preview owns these rows. No DOM reconstruction.
        rows = preview.get("timbers", [])
        created = [r for r in rows if r.get("change") == "created"]
        deleted = [r for r in rows if r.get("change") == "deleted"]
        moved = [r for r in rows if r.get("change") == "moved"]
        actual = (len(created), len(deleted), len(moved),
                  all(r.get("before") is None and r.get("owner", {}).get("instance") == 1 for r in created))
        self.assertEqual((4, 4, 1, True), actual, killer("br16:native-created-rows", rows))
        self.assertEqual(before, self.stable())
        self.assertTrue(self.command("line cancel-preview")["ok"])
        self.assertEqual(before, self.stable())


if __name__ == "__main__":
    unittest.main()
