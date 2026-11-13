"""W assembly policies with independent JSON/hash/contact facts and real consumer controls.

This suite does not compile at import or in the portable boundary class. Native
execution belongs to the serialized P1 queue; compile failures are never kills.
"""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from tests import _bridge
from tests.test_geo261_native_kernel import native

MODULE = ROOT / "geometry-templates/woodworking/native"


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def digest(value):
    return hashlib.sha256(canonical(value).encode("utf-8")).hexdigest()


def rule():
    return {"id": 8, "version": 1, "name": "single bay", "slots": [{"id": 17, "name": "primary"}, {"id": 41, "name": "secondary"}],
            "members": [{"id": 11, "slotId": 17}, {"id": 37, "slotId": 17}, {"id": 89, "slotId": 41}],
            "joints": [{"id": 4, "kind": "end-to-side", "scope": "left", "terminatedMember": 89, "targetMember": 11, "end": "start", "side": "+u", "dir": "u"},
                       {"id": 7, "kind": "end-to-side", "scope": "right", "terminatedMember": 89, "targetMember": 37, "end": "finish", "side": "-u", "dir": "u"}]}


def binding():
    return {"id": 9, "name": "unequal", "rule": {"id": 8, "version": 1}, "slots": [
        {"slotId": sid, "A": {"kind": "literal", "value": a}, "B": {"kind": "literal", "value": b}, "contactFace": "A", "orientation": "A"}
        for sid, a, b in ((41, 40, 50), (17, 27, 33))]}


def source():
    return {"id": 2, "name": "bay", "bindingId": 9, "rule": {"id": 8, "version": 1, "fingerprint": digest(rule())}, "surfaceId": 1,
            "members": [{"memberId": mid, "role": "secondary" if mid == 89 else "primary", "guideId": guide,
                         "dir": "+u" if mid == 89 else "+v", "depthSide": "+n", "ends":
                         {"start": {"kind": "member", "memberId": 11}, "finish": {"kind": "member", "memberId": 37}} if mid == 89 else
                         {"start": {"kind": "timber", "id": 90}, "finish": {"kind": "timber", "id": 91}}}
                        for mid, guide in ((11, 1), (37, 2), (89, 3))]}


def seed():
    return [{"kind": "publish", "value": rule()}, {"kind": "bind", "value": binding()}]


def create(value=None):
    return {"kind": "generation", "value": {"op": "create-instance", "expectedBindingFingerprint": digest(binding()), "value": value or source()}}


def record(value=None):
    return {"source": value or source(), "mapping": [{"memberId": 11, "timberId": 1}, {"memberId": 37, "timberId": 2}, {"memberId": 89, "timberId": 3}]}


class AssemblyBoundary(unittest.TestCase):
    def test_w_policy_has_no_host_types_storage_or_private_kernel_headers(self):
        for filename in ("assembly.h", "assembly.c"):
            text = (MODULE / filename).read_text(encoding="utf-8")
            code = re.sub(r"/\*.*?\*/|//[^\n]*", "", text, flags=re.S)
            self.assertNotRegex(code, r"\b(?:World|TimberAnchor|PlacementSurface|ReferenceFace|g_assembly_replay|g_engineering_error)\b")
            self.assertNotIn("internal/", text)
            self.assertNotIn("geometry-app", text)
        self.assertEqual(["assembly.h"], re.findall(r'^#include "([^"]+)"', (MODULE / "assembly.c").read_text(encoding="utf-8"), re.M))

    def test_actual_host_policy_entries_are_thin_w_adapters(self):
        host = (ROOT / "geometry-core/assembly.inc").read_text(encoding="utf-8") + (ROOT / "geometry-core/assembly_generation.inc").read_text(encoding="utf-8")
        for name in ("assembly_rule", "assembly_binding", "assembly_rebuild", "assembly_operation", "assembly_generation_prepare", "assembly_generation_check", "assembly_generation_integrity"):
            match = re.search(r"static [^\n]+\b" + name + r"\([^\n]+\)\s*\{([^{}]*)\}", host)
            self.assertIsNotNone(match, name)
            self.assertIn("wood_" + name + "(&c", match[1])
        self.assertIn("woodworking/native/assembly.h", (ROOT / "geometry-core/assembly_types.h").read_text(encoding="utf-8"))


CONTROLS = (
    ("scope", '!strcmp(scopes[k],scopes[i])', 'false'),
    ("endpoint", 'ends[q]==term[k]&&end_types[q]==et[k]', 'false'),
    ("immutable", '!strcmp(old->fingerprint,rule.fingerprint)||wood_asm_rule_immutable(w,rule.id,rule.version)', 'true'),
    ("contact", 'f.min_u!=l.max_u', 'false'),
    ("ownership", 'w->state->owner_count!=w->state->instance_count*3', 'false'),
)


class WoodAssembly(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        build = native()
        client = build.woodworking / "assembly-client.c"
        shutil.copy2(ROOT / "tests/geo261_assembly_harness.c", client)
        cls.client = build.compile(client, "assembly-client")
        cls.exe = build.link("assembly-client", cls.objects(build, build.wood_assembly_object))

    @classmethod
    def objects(cls, build, assembly_object):
        return [cls.client, assembly_object, build.wood_engineering_object, build.wood_members_object, *build.kernel_objects()]

    def call(self, actions, exe=None):
        path = native().work / "assembly-client-input.json"
        path.write_text(json.dumps(actions, ensure_ascii=False), encoding="utf-8")
        run = subprocess.run([str(exe or self.exe), str(path)], capture_output=True, text=True, timeout=20)
        self.assertEqual(0, run.returncode, "Process crash/error is not a domain verdict: " + run.stderr)
        values = [json.loads(line) for line in run.stdout.splitlines()]
        self.assertEqual(len(actions), len(values))
        return values

    def test_rule_canonical_hash_fixed_identity_and_idempotence_at_capacity(self):
        changed = dict(rule(), name="changed")
        values = self.call([{"kind": "publish", "value": rule()}, {"kind": "full-catalog"}, {"kind": "publish", "value": rule()}, {"kind": "publish", "value": changed}])
        self.assertEqual({"value": rule(), "hash": digest(rule())}, values[0]["rules"][0])
        self.assertTrue(values[2]["ok"])
        self.assertFalse(values[3]["ok"])
        self.assertEqual("D32: published rule 8@1 is immutable", values[3]["error"])
        self.assertEqual([2, 8, 0, 1], values[3]["diagnostic"])

    def test_joint_scope_endpoint_and_missing_slot_error_order(self):
        for mutate, expected in ((lambda r: r["joints"][1].update(scope="left", kind="unknown"), "I40: joints 4 and 7 conflict at scope left"),
                                 (lambda r: r["joints"][1].update(end="start"), "I40: joints 4 and 7 assign the same endpoint of member 89"),
                                 (lambda r: r["members"][0].update(slotId=999), "I40: member 11 refers to a missing slot")):
            with self.subTest(error=expected):
                value = rule();mutate(value)
                result = self.call([{"kind": "publish", "value": value}])[0]
                self.assertFalse(result["ok"]);self.assertEqual(expected, result["error"]);self.assertEqual(0, result["ruleCount"])

    def test_fixed_slot_mapping_unset_and_resolution_is_deferred_until_rebuild(self):
        value = binding();value["slots"][0]["A"] = {"kind": "spec", "name": "missing"}
        results = self.call([seed()[0], {"kind": "bind", "value": value}, {"kind": "rebuild"}])
        self.assertTrue(results[1]["ok"]);self.assertFalse(results[2]["ok"])
        self.assertIn("I40: binding 9 slot 41.A:", results[2]["error"])
        value = binding();value["slots"][0]["A"] = None;value["slots"][0]["orientation"] = None
        results = self.call([seed()[0], {"kind": "bind", "value": value}, {"kind": "rebuild"}])
        self.assertTrue(results[-1]["ok"]);self.assertFalse(results[-1]["bindings"][0]["complete"])
        value["slots"][0]["orientation"] = "C"
        self.assertEqual("I40: binding 9 slot 41 needs explicit A/B or unset orientation", self.call([seed()[0], {"kind": "bind", "value": value}])[-1]["error"])

    def test_parameter_dimension_failure_retains_precise_transient_identity(self):
        value = binding();value["slots"][0]["A"] = {"kind": "parameter", "parameterId": 10, "fieldId": 99}
        result = self.call([seed()[0], {"kind": "bind", "value": value}, {"kind": "rebuild"}])[-1]
        self.assertFalse(result["ok"]);self.assertEqual([1, 10, 99, 0], result["diagnostic"])

    def test_entry_identity_guard_rejects_delete_reinsert_without_consumers(self):
        changed = dict(rule(), name="replacement")
        result = self.call([seed()[0], {"kind": "save"}, {"kind": "operation", "value": {"op": "delete-rule", "id": 8, "version": 1}}, {"kind": "publish", "value": changed}, {"kind": "immutable"}])[-1]
        self.assertFalse(result["ok"]);self.assertEqual([2, 8, 0, 1], result["diagnostic"])

    def test_sparse_slots_primary_first_and_exact_owned_mapping(self):
        value = source();value["members"].reverse()
        result = self.call(seed() + [create(value), {"kind": "prepare"}, {"kind": "check"}, {"kind": "integrity"}])[-1]
        self.assertTrue(result["ok"]);self.assertEqual([1, 2, 3], result["writes"])
        self.assertEqual([{ "memberId": 89, "timberId": 3}, {"memberId": 37, "timberId": 1}, {"memberId": 11, "timberId": 2}], result["instances"][0]["mapping"])
        self.assertEqual([(1, 1, 27, 33, 2, [90, 91]), (2, 1, 27, 33, 1, [90, 91]), (3, 2, 40, 50, 3, [2, 1])],
                         [(m["id"], m["role"], m["width"], m["depth"], m["guide"], m["between"]) for m in result["members"] if m["id"] < 90])

    def test_support_role_and_inward_contact_reject_one_unit_error(self):
        result = self.call(seed() + [create(), {"kind": "member-fact", "id": 90, "role": 1}, {"kind": "prepare"}])[-1]
        self.assertFalse(result["ok"]);self.assertIn("primary requires existing same-face boundary supports", result["error"])
        for field, value in (("min_u", 515), ("max_u", 2486), ("min_v", 19), ("max_v", 2981)):
            with self.subTest(field=field):
                result = self.call(seed() + [create(), {"kind": "prepare"}, {"kind": "member-fact", "id": 3, field: value}, {"kind": "check"}])[-1]
                self.assertFalse(result["ok"]);self.assertEqual("I42: secondary endpoints do not contact the declared inward primary sides", result["error"])

    def test_owned_mapping_capability_and_saved_source_checks(self):
        for change, error in (({"kind": "owner-count", "count": 2}, "I42: orphan owned records or missing instance mapping"),
                              ({"kind": "duplicate-owner"}, "I42: duplicate owner identity"),
                              ({"kind": "require-generation", "required": 0}, "I42: missing required generation capability")):
            result = self.call(seed() + [create(), {"kind": "prepare"}, change, {"kind": "integrity"}])[-1]
            self.assertFalse(result["ok"]);self.assertEqual(error, result["error"])
        for change in ({"kind": "member-fact", "id": 1, "width": 28}, {"kind": "member-fact", "id": 1, "anchor": 0}):
            result = self.call(seed() + [create(), {"kind": "prepare"}, {"kind": "clear-instances"}, change, {"kind": "load", "value": record()}])[-1]
            self.assertFalse(result["ok"]);self.assertEqual("I42: saved owned definitions differ from instance sources", result["error"])

    def test_stale_edit_priority_and_delete_clears_ownership(self):
        bad = {"op": "edit-instance", "id": 2, "expectedFingerprint": "0" * 64, "expectedBindingFingerprint": "0" * 64, "value": None}
        result = self.call(seed() + [create(), {"kind": "generation", "value": bad}])[-1]
        self.assertFalse(result["ok"]);self.assertEqual("STALE: instance source changed", result["error"])
        delete = {"op": "delete-instance", "id": 2, "expectedFingerprint": digest(record())}
        result = self.call(seed() + [create(), {"kind": "generation", "value": delete}])[-1]
        self.assertTrue(result["ok"]);self.assertEqual((0, 0, 2, False), (result["instanceCount"], result["ownerCount"], result["memberCount"], result["required"]))

    def mutant(self, control):
        name, before, after = control;build = native()
        text = (build.woodworking / "assembly.c").read_text(encoding="utf-8")
        self.assertEqual(1, text.count(before), name)
        path = build.woodworking / ("assembly-" + name + ".c")
        path.write_text(text.replace(before, after), encoding="utf-8")
        changed = build.compile(path, "assembly-" + name)
        return changed, build.link("assembly-mutant-" + name, self.objects(build, changed))

    def test_five_removed_guards_change_the_named_domain_verdict(self):
        scope = rule();scope["joints"][1]["scope"] = "left"
        endpoint = rule();endpoint["joints"][1]["end"] = "start"
        cases = ([{"kind": "publish", "value": scope}], [{"kind": "publish", "value": endpoint}],
                 [seed()[0], {"kind": "publish", "value": dict(rule(), name="changed")}],
                 seed() + [create(), {"kind": "prepare"}, {"kind": "member-fact", "id": 3, "min_u": 515}, {"kind": "check"}],
                 seed() + [create(), {"kind": "owner-count", "count": 2}, {"kind": "integrity"}])
        for control, actions in zip(CONTROLS, cases):
            with self.subTest(control=control[0]):
                self.assertFalse(self.call(actions)[-1]["ok"], "baseline guard: " + control[0])
                _, mutant = self.mutant(control)
                self.assertTrue(self.call(actions, mutant)[-1]["ok"], "guard removal must expose policy failure: " + control[0])
                self.assertFalse(self.call(actions)[-1]["ok"], "restored guard: " + control[0])

    def product_scope_preview(self, executable, suffix):
        build = native();value = rule();value["joints"][1]["scope"] = "left"
        with _bridge.BridgeSession(executable) as bridge:
            read = bridge.command("assembly-read");self.assertTrue(read["ok"], read)
            path = build.work / ("assembly-product-" + suffix + ".json")
            path.write_text(json.dumps({"schema": "assembly-transaction/1", "expectedRevision": read["revision"], "operations": [{"op": "publish-rule", "value": value}]}), encoding="utf-8")
            before = bridge.command("dump")["text"]
            result = bridge.command("assembly-preview " + str(path));self.assertTrue(result["ok"], result)
            self.assertEqual(before, bridge.command("dump")["text"])
            return result["preview"]

    def test_same_scope_guard_is_consumed_by_actual_bridge_preview(self):
        build = native();baseline = build.bridge()
        self.assertFalse(self.product_scope_preview(baseline, "baseline")["valid"])
        changed, _ = self.mutant(CONTROLS[0]);objects = build.product_objects()
        self.assertEqual(1, objects.count(build.wood_assembly_object))
        mutant = build.link("assembly-mutant-bridge", [build.bridge_object, *[changed if obj == build.wood_assembly_object else obj for obj in objects]])
        self.assertTrue(self.product_scope_preview(mutant, "removed")["valid"])
        self.assertFalse(self.product_scope_preview(baseline, "restored")["valid"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
