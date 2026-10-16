"""W-owned engineering policies, independent oracles and real product removal.

The host exposes geometry/parameter facts and writes caches. These tests make
no claim that remaining legacy codecs or commands have already left H.
"""
from pathlib import Path
import json
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


class EngineeringBoundary(unittest.TestCase):
    def test_policy_uses_only_public_kernel_types_and_explicit_host_facts(self):
        for name in ("engineering.h", "engineering.c"):
            source = (MODULE / name).read_text(encoding="utf-8")
            code = re.sub(r"/\*.*?\*/|//[^\n]*", "", source, flags=re.S)
            self.assertNotRegex(code, r"\b(?:World|ReferenceGrid|Timber|PlacementSurface|g_engineering_error)\b")
            self.assertNotIn("internal/", source)
            self.assertNotIn("geometry-app", source)
        self.assertEqual(["engineering.h"], re.findall(r'^#include "([^"]+)"', (MODULE / "engineering.c").read_text(encoding="utf-8"), re.M))

    def test_actual_host_delegates_all_domain_entry_points(self):
        source = (ROOT / "geometry-core/engineering.inc").read_text(encoding="utf-8")
        for name in ("eng_publish_material", "eng_publish_method", "eng_put_application", "eng_bind", "eng_target_context", "eng_resolve", "eng_effective", "engineering_rebuild", "engineering_follow_fragment", "engineering_drop_owned"):
            match = re.search(r"static [^\n]+\b" + name + r"\([^\n]+\)\s*\{([^{}]*)\}", source)
            self.assertIsNotNone(match, name)
            self.assertIn("wood_" + name + "(&c,", match[1])
            self.assertNotIn("for (", match[1])
        self.assertIn('woodworking/native/engineering.h', (ROOT / "geometry-core/engineering_types.h").read_text(encoding="utf-8"))


CONTROLS = (
    ("fingerprint", 'fingerprint && strcmp(fingerprint,m.fingerprint)', 'false', "materials", "material-fingerprint-refusal", 1),
    ("immutable", '!strcmp(old->content,m.content) || wood_eng_fail(w,"I34: material ID/version already has different immutable content")', 'true', "materials", "material-immutable", 1),
    ("material-kind", 'mat->kind!=(r<0?0:1)', 'false', "methods", "method-kind", 1),
    ("application-face", 'existing && existing->placement_id!=a.placement_id', 'false', "applications", "application-cannot-move", 1),
    ("application-derived", 'if(derived)', 'if(false)', "applications", "application-derived", 1),
    ("object-override", 'b->has_override?&b->override_value:&b->source', '&b->source', "resolution", "resolve-object-precedence", 1),
    ("inactive-base", 'b->has_override && b->source.kind!=ENG_APPLICATION', 'false', "resolution", "override-inactive-base-required", 1),
    ("axis-mapping", 'axis==target->axis+1?ENG_LENGTH:ENG_WIDTH', 'axis==target->axis+1?ENG_WIDTH:ENG_LENGTH', "resolution", "resolve-width-axis", 1),
    ("owned-member", 'target->kind&&w->member_owned(w->user,target->id)', 'false', "roles", "owned-member-bind", 1),
    ("serial-capacity", '!w->serializable(w->user,w->error,w->error_capacity)', 'false', "rebuild", "rebuild-record-capacity", 1),
    ("fragment-conflict", 'found && destination!=pid', 'false', "fragments", "fragment-conflict", 1),
    ("binding-kind", 'e->bindings[i].target.kind!=target_kind || e->bindings[i].target.id!=id', 'false', "deletion", "delete-only-owned", 1),
)


class WoodEngineering(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        build = native()
        client = build.woodworking / "engineering-client.c"
        shutil.copy2(ROOT / "tests/geo261_engineering_harness.c", client)
        cls.client = build.compile(client, "engineering-client")
        cls.exe = build.link("engineering-client", [cls.client, build.wood_engineering_object, *build.kernel_objects()])

    def case(self, name, exe=None):
        result = subprocess.run([str(exe or self.exe), name], capture_output=True, text=True, timeout=15)
        self.assertIn(result.returncode, (0, 1), "Crash/process error is not a policy verdict: " + result.stderr)
        if result.returncode:
            self.assertRegex(result.stderr, r"ASSERT:[a-z0-9-]+")
        return result

    def test_material_versions_canonical_fingerprints_and_immutability(self):
        self.assertEqual(0, self.case("materials").returncode)

    def test_method_fixed_versions_types_and_explicit_zero_gap(self):
        self.assertEqual(0, self.case("methods").returncode)

    def test_application_identity_face_and_override_contract(self):
        self.assertEqual(0, self.case("applications").returncode)

    def test_resolution_precedence_and_inactive_base_validation(self):
        self.assertEqual(0, self.case("resolution").returncode)

    def test_role_material_axis_and_unplaced_replay_context(self):
        self.assertEqual(0, self.case("roles").returncode)

    def test_rebuild_error_order_partial_caches_and_final_capacity(self):
        self.assertEqual(0, self.case("rebuild").returncode)

    def test_fragment_rewrite_identity_and_canonical_content(self):
        self.assertEqual(0, self.case("fragments").returncode)

    def test_deletion_keeps_unrelated_references_and_clears_owned_tail(self):
        self.assertEqual(0, self.case("deletion").returncode)

    def mutant(self, control):
        name, before, after, _, _, count = control
        build = native()
        source = (build.woodworking / "engineering.c").read_text(encoding="utf-8")
        # Fingerprints exist independently in material and method publication.
        self.assertEqual(2 if name == "fingerprint" else count, source.count(before), name)
        path = build.woodworking / ("engineering-" + name + ".c")
        path.write_text(source.replace(before, after, count), encoding="utf-8")
        return build.compile(path, "engineering-" + name)

    def test_twelve_guard_controls_fail_named_assertions(self):
        build = native()
        for control in CONTROLS:
            with self.subTest(control=control[0]):
                self.assertEqual(0, self.case(control[3]).returncode)
                changed = self.mutant(control)
                exe = build.link("engineering-mutant-" + control[0], [self.client, changed, *build.kernel_objects()])
                result = self.case(control[3], exe)
                self.assertEqual(1, result.returncode, "W guard removal survived: " + control[0])
                self.assertIn("ASSERT:" + control[4], result.stderr)
                self.assertEqual(0, self.case(control[3]).returncode)

    def preview_immutable_change(self, exe, suffix):
        build = native()
        with _bridge.BridgeSession(exe) as bridge:
            material = {"id": "p", "version": 1, "kind": "panel", "name": "Panel", "width": 100, "length": 200}
            def preview(value):
                read = bridge.command("engineering-read")
                self.assertTrue(read["ok"], read)
                request = {"schema": "engineering-transaction/1", "expectedRevision": read["revision"], "operations": [{"op": "publish-material", "value": value}]}
                path = build.work / ("engineering-policy-" + suffix + ".json")
                path.write_text(json.dumps(request), encoding="utf-8")
                before = bridge.command("dump")["text"]
                result = bridge.command("engineering-preview " + str(path))
                self.assertTrue(result["ok"], result)
                self.assertEqual(before, bridge.command("dump")["text"])
                return result["preview"]
            first = preview(material)
            self.assertTrue(first["valid"], first)
            self.assertTrue(bridge.command("engineering-confirm " + str(first["token"]))["ok"])
            return preview(dict(material, name="Changed"))

    def test_same_w_guard_controls_actual_product_preview(self):
        build = native()
        baseline = build.bridge()
        self.assertFalse(self.preview_immutable_change(baseline, "original")["valid"])
        changed = self.mutant(CONTROLS[1])
        client = build.link("engineering-product-mutant-client", [self.client, changed, *build.kernel_objects()])
        self.assertIn("ASSERT:material-immutable", self.case("materials", client).stderr)
        product_objects = build.product_objects()
        self.assertEqual(1, product_objects.count(build.wood_engineering_object))
        mutant = build.link("engineering-product-mutant-bridge", [build.bridge_object, *[changed if obj == build.wood_engineering_object else obj for obj in product_objects]])
        self.assertTrue(self.preview_immutable_change(mutant, "mutant")["valid"])
        self.assertFalse(self.preview_immutable_change(baseline, "restored")["valid"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
