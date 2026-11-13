"""Typed guide ownership and exact preservation of rejected cache semantics.

This standalone client links actual K guide/linear/datum geometry objects.
Product adapter and transaction witnesses belong to the integration suite.
"""
import re
import shutil
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from tests.test_geo261_native_kernel import native


class GuideBoundary(unittest.TestCase):
    def test_store_uses_public_geometry_without_host_grammar_or_provider_namespace(self):
        source = (ROOT / "geometry-core/kernel/guides.h").read_text(encoding="utf-8")
        source += (ROOT / "geometry-core/kernel/guides.c").read_text(encoding="utf-8")
        code = re.sub(r"/\*.*?\*/|//[^\n]*", "", source, flags=re.S)
        self.assertNotRegex(code, r"\b(?:World|AppLinearContext|APP_LINEAR_SOURCE|reference_compile_text|reference_issue)\b")
        self.assertEqual(["datums.h", "internal/guides.h"], re.findall(r'^\s*#include\s+"([^"]+)"', code, flags=re.M))


class NativeGuides(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        build = native()
        source = build.work / "guides-client.c"
        shutil.copy2(ROOT / "tests/geo261_guides_harness.c", source)
        cls.client = build.compile(source, "guides-client")
        cls.exe = build.link("guides-client", [cls.client, build.guides_object,
            build.datums_object, build.linear_object, build.exact_object, build.geometry_object])

    def case(self, name, exe=None):
        result = subprocess.run([str(exe or self.exe), name], capture_output=True, text=True, timeout=10)
        self.assertIn(result.returncode, (0, 1), "Native crash/setup failure is not a guide verdict: " + result.stderr)
        return result.returncode

    def test_owned_keys_clone_aliasing_and_canonical_unused_fields(self):
        self.assertEqual(0, self.case("ownership"))

    def test_capacity_replacement_order_deletion_and_uint32_identity(self):
        self.assertEqual(0, self.case("capacity"))

    def test_invalid_input_does_not_partially_replace_stored_definition(self):
        self.assertEqual(0, self.case("invalid-inputs"))

    def test_local_rationals_floor_once_exact_final_and_only_require_frame_presence(self):
        self.assertEqual(0, self.case("local-values"))

    def test_local_failures_preserve_offset_and_resolved_even_for_range(self):
        self.assertEqual(0, self.case("local-failures"))

    def test_incomplete_expression_retains_prefix_source_failure_order(self):
        self.assertEqual(0, self.case("incomplete-prefix"))

    def test_all_signed_frames_preserve_intersection_axis_and_coordinate(self):
        self.assertEqual(0, self.case("datum-frames"))

    def test_missing_coincident_parallel_and_invalid_datums_preserve_existing_cache(self):
        self.assertEqual(0, self.case("datum-failures"))

    def test_datum_range_failure_still_writes_attempted_axis_and_offset(self):
        self.assertEqual(0, self.case("datum-range"))

    def test_reset_is_independent_and_move_retains_cache_until_success(self):
        self.assertEqual(0, self.case("reset-move"))

    def mutant(self, name, before, after):
        build = native()
        source = (build.kernel / "guides.c").read_text(encoding="utf-8")
        self.assertEqual(1, source.count(before), "Negative control must change exactly one expression")
        path = build.work / ("guides-" + name + ".c")
        path.write_text(source.replace(before, after), encoding="utf-8")
        obj = build.compile(path, "guides-" + name)
        return build.link("guides-" + name, [self.client, obj, build.datums_object,
            build.linear_object, build.exact_object, build.geometry_object])

    def test_local_range_write_negative_control_is_a_normal_assertion_failure(self):
        self.assertEqual(0, self.case("local-failures"))
        exe = self.mutant("local-range", "if (result.linear.status != GEO_LINEAR_OK)",
            "if (result.linear.status != GEO_LINEAR_OK && result.linear.status != GEO_LINEAR_RANGE)")
        self.assertEqual(1, self.case("local-failures", exe))
        self.assertEqual(0, self.case("local-failures"))

    def test_datum_range_omission_negative_control_is_a_normal_assertion_failure(self):
        self.assertEqual(0, self.case("datum-range"))
        exe = self.mutant("datum-range", "result.intersection == GEO_DATUM_INTERSECTION_OK || result.intersection == GEO_DATUM_INTERSECTION_RANGE",
            "result.intersection == GEO_DATUM_INTERSECTION_OK")
        self.assertEqual(1, self.case("datum-range", exe))
        self.assertEqual(0, self.case("datum-range"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
