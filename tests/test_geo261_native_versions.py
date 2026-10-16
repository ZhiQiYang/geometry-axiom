"""Neutral immutable version storage: owned bytes, exact fields and controls.

Only VersionBoundary is portable. Native builds/runs are queued by P1.
This isolated client does not claim W/H integration; that activation has its
own product witnesses. Build failures and crashes are never mutation kills.
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
from tests.test_geo261_native_kernel import native

KERNEL = ROOT / "geometry-core/kernel"
CONTROLS = (
    ("fingerprint", "if(memcmp(next.fingerprint,definition->fingerprint,GEO_VERSION_FINGERPRINT_BYTES))", "if(false)", "fingerprint", "fingerprint-verified"),
    ("immutable", "geo_version_record_equal(existing,next)?GEO_VERSION_OK:GEO_VERSION_IMMUTABLE", "GEO_VERSION_OK", "immutable", "immutable-content"),
    ("field-existence", "if(record->fields[i].id==field_id)", "if(true)", "lookup", "field-existence"),
    ("copy-isolation", "memcpy(copy,source,sizeof *copy);\n    *out=copy;", "free(copy);copy=(GeoVersionStore *)source;\n    *out=copy;", "ownership", "copy-independent"),
    ("duplicate-field", "if(at<i&&next.fields[at].id==definition->fields[i].id)", "if(false)", "fields", "duplicate-field-rejected"),
    ("decimal-integer", "if(field->literal[i]!='0')return GEO_VERSION_INTEGER;", "if(false)return GEO_VERSION_INTEGER;", "decimal-precision", "tiny-fraction-not-rounded"),
)


class VersionBoundary(unittest.TestCase):
    def test_kernel_public_api_and_source_do_not_depend_on_host_or_schema(self):
        public = (KERNEL / "versions.h").read_text(encoding="utf-8")
        source = (KERNEL / "versions.c").read_text(encoding="utf-8")
        code = re.sub(r"/\*.*?\*/|//[^\n]*", "", public + source, flags=re.S)
        self.assertNotRegex(code, r"\b(?:World|EngineeringState|EngMaterial|EngMethod|Wood\w*|geo_json_\w*|double|float)\b")
        self.assertNotIn("internal/", public)
        self.assertEqual(["exact.h"], re.findall(r'^#include "([^"]+)"', public, re.M))
        self.assertEqual(["internal/versions.h", "codec.h"], re.findall(r'^#include "([^"]+)"', source, re.M))
        self.assertIn("geo_sha256(next.content,next.content_length,next.fingerprint)", source)
        self.assertIn("geo_quantity_normalize(", source)
        harness = (ROOT / "tests/geo261_versions_harness.c").read_text(encoding="utf-8")
        self.assertEqual(["versions.h"], re.findall(r'^#include "([^"]+)"', harness, re.M))

    def test_backing_is_pointer_free_and_each_control_targets_one_expression(self):
        private = (KERNEL / "internal/versions.h").read_text(encoding="utf-8")
        code = re.sub(r"/\*.*?\*/|//[^\n]*", "", private, flags=re.S)
        self.assertNotIn("*", code)
        source = (KERNEL / "versions.c").read_text(encoding="utf-8")
        for name, before, _, _, _ in CONTROLS:
            with self.subTest(control=name):
                self.assertEqual(1, source.count(before))


class NativeVersions(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        build = native()
        source = build.work / "versions-client.c"
        shutil.copy2(ROOT / "tests/geo261_versions_harness.c", source)
        cls.client = build.compile(source, "versions-client")
        cls.exe = build.link("versions-client", [cls.client, build.versions_object, build.codec_object, build.exact_object])

    def run_case(self, case, exe=None):
        return subprocess.run([str(exe or self.exe), case], capture_output=True, text=True, encoding="utf-8", timeout=20)

    def succeeds(self, case, exe=None):
        run = self.run_case(case, exe)
        self.assertEqual(0, run.returncode, run.stderr)
        self.assertEqual("PASS " + case, run.stdout.strip())

    def test_binary_namespace_prefixes_and_fixed_uint32_versions(self):
        self.succeeds("identity")

    def test_sha256_known_answers_binary_content_and_explicit_fingerprint_length(self):
        self.succeeds("fingerprint")

    def test_exact_normalization_units_duplicate_fields_and_failure_atomicity(self):
        self.succeeds("fields")

    def test_content_and_every_field_metadata_are_immutable_per_identity(self):
        self.succeeds("immutable")

    def test_field_lookup_retains_identity_and_failure_outputs(self):
        self.succeeds("lookup")

    def test_owned_inputs_stable_views_clone_lifetime_and_order_independent_equality(self):
        self.succeeds("ownership")

    def test_maximum_byte_fields_and_invalid_input_are_atomic(self):
        self.succeeds("limits")

    def test_full_store_accepts_idempotence_and_keeps_immutable_error_precedence(self):
        self.succeeds("capacity")

    def test_full_decimal_precision_is_retained_and_conversion_never_rounds(self):
        self.succeeds("decimal-precision")

    def test_decimal_syntax_units_and_capacity_fail_atomically(self):
        self.succeeds("decimal-validation")

    def test_schema_is_owned_immutable_and_admission_check_never_mutates(self):
        self.succeeds("schemas-and-check")

    def test_six_missing_guards_fail_the_named_assertion_then_restore(self):
        build = native()
        text = (build.kernel / "versions.c").read_text(encoding="utf-8")
        for name, before, after, case, label in CONTROLS:
            with self.subTest(control=name):
                self.succeeds(case)
                self.assertEqual(1, text.count(before))
                # Keep the replacement under the isolated K root so private
                # includes resolve without giving it repository access.
                source = build.kernel / ("versions-" + name + ".c")
                source.write_text(text.replace(before, after), encoding="utf-8")
                changed = build.compile(source, "versions-" + name)
                exe = build.link("versions-mutant-" + name, [self.client, changed, build.codec_object, build.exact_object])
                run = self.run_case(case, exe)
                self.assertEqual(1, run.returncode, "Crash/build/runtime error is not an assertion: " + run.stderr)
                self.assertIn("ASSERT:" + label, run.stderr)
                self.succeeds(case)


if __name__ == "__main__":
    unittest.main(verbosity=2)
