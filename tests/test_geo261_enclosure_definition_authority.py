"""Actual returned enclosure membership and result values govern K consumers.

Portable checks never compile. Native tests run only in the serialized lane;
controls require their exact assertion between passing unchanged baselines.
"""
from pathlib import Path
import re
import shutil
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from tests.test_geo261_native_kernel import kernel_only_native
from tests.test_geo261_enclosure_sources import code, definition

KERNEL = ROOT / "geometry-core/kernel"
HARNESS = ROOT / "tests/geo261_enclosure_definition_authority_harness.c"
RESULT_RETURN = ("return value.kind==GEO_SOURCE_DEFINITION&&\n        "
                 "geo_enclosure_source_decode_definition(GEO_ENCLOSURE_SOURCE_RESULT,&value.as.definition,id,out);")
CONTROLS = (
    ("result-raw-members", "geo_enclosure_sources_evaluate", "geo_enclosure_source_result(s,at,&resolved)",
     "geo_enclosure_source_result(s,at,geo_enclosures_at(s->enclosures,at))", "result", "returned-members-control-result"),
    ("axis-raw-members", "geo_enclosure_sources_evaluate", "geo_enclosure_source_axis(s,&resolved,axis,slot,&coordinate)",
     "geo_enclosure_source_axis(s,geo_enclosures_at(s->enclosures,at),axis,slot,&coordinate)", "axis", "returned-members-control-axis-order"),
    ("result-sidecache", "geo_enclosure_sources_value", RESULT_RETURN,
     "memcpy(out,&s->values[at],sizeof *out);return true;", "result-value", "returned-result-controls-public-value"),
    ("definition-kind", "geo_enclosure_sources_evaluate", "||input.kind!=GEO_SOURCE_DEFINITION", "",
     "invalid", "malformed-return-blocks-geometry-atomically"),
    ("result-kind", "geo_enclosure_sources_value", "value.kind==GEO_SOURCE_DEFINITION&&", "",
     "invalid-result", "malformed-result-preserves-output-and-fault"),
    ("schema", "geo_enclosure_source_decode_definition", "strcmp(value->schema,schema)", "false",
     "malformed", "codec-malformed-rejected-atomically"),
    ("exact-length", "geo_enclosure_source_decode_definition", "value->content_size!=length", "value->content_size<length",
     "malformed", "codec-malformed-rejected-atomically"),
    ("expected-id", "geo_enclosure_source_decode_definition", "id!=expected_id||", "",
     "malformed", "codec-malformed-rejected-atomically"),
    ("canonical-bool", "geo_enclosure_source_decode_definition", "bytes[length-1]>1", "false",
     "malformed", "codec-malformed-rejected-atomically"),
    ("member-order", "geo_enclosure_source_decode_definition", "bytes+8+4*i", "bytes+8+4*(count-1-i)",
     "wire", "codec-independent-member-vector"),
    ("signed-result", "geo_enclosure_source_read_i64", "-1-(GeoCoord)(~value)", "0",
     "wire", "codec-independent-signed-result-vector"),
    ("full-capacity", "geo_enclosure_source_decode_definition", "count>GEO_ENCLOSURE_MEMBER_CAPACITY", "count>=GEO_ENCLOSURE_MEMBER_CAPACITY",
     "wire", "codec-full-capacity-decode"),
)


class EnclosureDefinitionAuthorityBoundary(unittest.TestCase):
    def test_real_result_and_axis_read_the_returned_definition_and_value(self):
        source = (KERNEL / "enclosure_sources.c").read_text(encoding="utf-8")
        body = definition(source, "geo_enclosure_sources_evaluate")
        self.assertIn("geo_eval_source(graph,geo_enclosure_source_ref(s->token,GEO_ENCLOSURE_SOURCE_DEFINITION", body)
        self.assertIn("GEO_DEPENDENCY_DEFINITION_REQUIRED,&input", body)
        self.assertIn("geo_enclosure_source_decode_definition(GEO_ENCLOSURE_SOURCE_DEFINITION,&input.as.definition,id,&resolved)", body)
        for name in ("geo_enclosure_source_result", "geo_enclosure_source_axis"):
            self.assertNotIn("geo_enclosures_at", definition(source, name))
        accessor = definition(source, "geo_enclosure_sources_value")
        self.assertIn(RESULT_RETURN, accessor)
        self.assertNotIn("s->values", accessor)

    def test_public_codec_and_harness_have_no_host_template_or_private_layout(self):
        for path in (KERNEL / "enclosure_sources.h", KERNEL / "enclosure_sources.c", HARNESS):
            text = code(path.read_text(encoding="utf-8"))
            self.assertNotRegex(text, r"\b(?:World|Space|Timber|Wood\w*|App\w*)\b|internal/")
        harness = HARNESS.read_text(encoding="utf-8")
        self.assertIn("geo_enclosure_source_encode_definition", harness)
        self.assertIn("const unsigned char members_wire[]", harness)
        self.assertIn("const unsigned char result_wire[]", harness)
        self.assertIn("*out=replacement", harness)
        self.assertNotRegex(harness, r"s->(?:definitions|results|values)|struct Geo(?:EvalContext|EnclosureSources)\s*\{")

    def test_controls_have_unique_actual_anchors_and_named_assertions(self):
        source = (KERNEL / "enclosure_sources.c").read_text(encoding="utf-8")
        harness = HARNESS.read_text(encoding="utf-8")
        self.assertEqual(12, len(CONTROLS))
        self.assertEqual(len(CONTROLS), len({row[0] for row in CONTROLS}))
        for name, function, before, after, case, marker in CONTROLS:
            with self.subTest(control=name):
                self.assertEqual(1, definition(source, function).count(before))
                self.assertNotEqual(before, after)
                self.assertEqual(1, harness.count('"' + marker + '"'))
                self.assertIn('"' + case + '"', harness)


class NativeEnclosureDefinitionAuthority(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        build = kernel_only_native()
        cls.directory = build.work / "enclosure-definition-authority"
        cls.directory.mkdir(exist_ok=True)
        for name in ("geo261_enclosure_definition_authority_harness.c", "geo261_enclosure_sources_harness.c"):
            shutil.copy2(ROOT / "tests" / name, cls.directory / name)
        shutil.copy2(build.kernel / "enclosure_sources.c", cls.directory / "enclosure_sources.c")
        cls.source = cls.directory / HARNESS.name
        cls.client = build.compile(cls.source, "enclosure-definition-authority-client")
        objects = build.kernel_objects()
        if objects.count(build.enclosure_sources_object) != 1:
            raise AssertionError("Expected exactly one original enclosure source object")
        cls.objects = [obj for obj in objects if obj != build.enclosure_sources_object]
        cls.exe = build.link("enclosure-definition-authority-client", [cls.client, *cls.objects])

    def case(self, name, executable=None, marker=None):
        run = subprocess.run([str(executable or self.exe), name], capture_output=True, text=True, encoding="utf-8", timeout=20)
        self.assertEqual(1 if marker else 0, run.returncode, "Crash/setup failure is not a detection:\n" + run.stderr)
        self.assertEqual("ASSERT:" + marker + "\n" if marker else "", run.stderr)
        self.assertEqual("", run.stdout)

    def test_independent_canonical_wire_vectors_and_signed_extremes(self): self.case("wire")
    def test_malformed_wire_is_bounded_canonical_and_atomic(self): self.case("malformed")
    def test_returned_members_control_result_identity_and_geometry(self): self.case("result")
    def test_returned_members_control_axis_member_order(self): self.case("axis")
    def test_returned_members_preserve_ordered_partial_faults(self): self.case("fault")
    def test_bad_definition_values_and_failed_dependency_block_geometry_atomically(self): self.case("invalid")
    def test_returned_result_controls_public_accessor(self): self.case("result-value")
    def test_bad_result_keeps_output_and_fault_unchanged(self): self.case("invalid-result")
    def test_memo_storage_candidate_isolation_empty_members_and_reset(self): self.case("lifetime")

    def test_link_uses_real_kernel_only_and_exactly_one_enclosure_implementation(self):
        build = kernel_only_native()
        self.assertTrue(build.kernel_only)
        self.assertNotIn(build.enclosure_sources_object, self.objects)
        self.assertFalse((build.work / "isolated-host").exists())
        self.assertFalse((build.work / "isolated-woodworking").exists())
        self.assertEqual((build.kernel / "enclosure_sources.c").read_bytes(), (self.directory / "enclosure_sources.c").read_bytes())

    def test_twelve_controls_require_exact_assertions_between_passing_baselines(self):
        build = kernel_only_native()
        path = self.directory / "enclosure_sources.c"
        original = path.read_bytes()
        text = code(original.decode("utf-8"))
        for name, function, before, after, case, marker in CONTROLS:
            with self.subTest(control=name):
                self.case(case)
                body = definition(text, function)
                self.assertEqual(1, body.count(before))
                self.assertEqual(1, text.count(body))
                try:
                    path.write_text(text.replace(body, body.replace(before, after)), encoding="utf-8")
                    client = build.compile(self.source, "enclosure-authority-control-" + name)
                    mutant = build.link("enclosure-authority-control-" + name, [client, *self.objects])
                finally:
                    path.write_bytes(original)
                self.case(case, mutant, marker)
                self.case(case)


if __name__ == "__main__":
    unittest.main(verbosity=2)
