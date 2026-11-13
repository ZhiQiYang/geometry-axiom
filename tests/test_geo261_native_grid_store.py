"""Grid definitions/bindings own their data and retain the frozen arithmetic.

The two token digests were computed once from c94c11e1's grid_systems.inc and
grid_bindings.inc. Tests need no Git repository, and never regenerate expected
answers from the candidate implementation. The client links actual K objects.
"""
import hashlib
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

AXIS_BASELINE = "98255a1a8601d51dc36d69036ec81fb4cf327f718b4425d6390074cc6cf10be8"
TRANSLATION_BASELINE = "aa3e47ff0101d789fc0b53f6535b1aef0cee77156855c411ae7714ca400aa5e5"


def body(text, name):
    match = re.search(r"\b" + re.escape(name) + r"\s*\([^;{}]*\)\s*\{", text)
    if not match:
        raise AssertionError("Missing function " + name)
    start = match.end() - 1
    return braced(text, start)


def braced(text, start):
    level = 0
    for at in range(start, len(text)):
        if text[at] == "{":
            level += 1
        elif text[at] == "}":
            level -= 1
            if not level:
                return text[start:at + 1]
    raise AssertionError("Unclosed body")


def tokens(text):
    text = re.sub(r"/\*.*?\*/|//[^\n]*", "", text, flags=re.S)
    return " ".join(re.findall(r"[A-Za-z_]\w*|\d+|==|!=|<=|>=|&&|\|\||\+\+|--|->|\+=|-=|\S", text))


def axis_digest(text, function):
    value = body(text, function)
    # Public null handling is a new boundary precondition, not old arithmetic.
    value = re.sub(r"if\s*\(\s*!a\s*\)\s*return\s+false\s*;", "", value)
    aliases = {
        "GRID_SRC_NONE": "GEO_GRID_SOURCE_NONE", "GRID_SRC_REPEAT": "GEO_GRID_SOURCE_REPEAT",
        "GRID_SRC_REPEAT_PANEL": "GEO_GRID_SOURCE_REPEAT_BODY_GAP", "GRID_SRC_PANEL": "GEO_GRID_SOURCE_BODY_GAP",
        "GRID_SRC_EXPLICIT": "GEO_GRID_SOURCE_EXPLICIT", "GRID_SRC_SERIES": "GEO_GRID_SOURCE_SERIES",
        "GRID_MAX_LINES": "GEO_GRID_COORDINATE_CAPACITY", "Coord": "GeoCoord", "panel": "body",
        "coord_in_range": "geo_coord_in_range", "grid_coord_list_is_valid": "geo_coordinates_increasing",
    }
    value = re.sub(r"\b[A-Za-z_]\w*\b", lambda m: aliases.get(m[0], m[0]), value)
    return hashlib.sha256(tokens(value).encode()).hexdigest()


def translation_digest(text, function):
    value = body(text, function)
    match = re.search(r"for\s*\(\s*int\s+a\s*=\s*0\s*;", value)
    if not match:
        raise AssertionError("Missing two-axis arithmetic loop")
    start = value.index("{", match.start())
    value = value[match.start():start] + braced(value, start)
    value = re.sub(r"if\s*\(error\)\s*error->axis\s*=\s*a\s*;", "", value)
    value = re.sub(r"return\s+geo_grid_error\(error,\s*GEO_GRID_STORE_BINDING_TRANSLATION_RANGE\)\s*;", "return false;", value)
    value = re.sub(r"g\.lattice_base\[a\]", "cache.lattice[a].base", value)
    value = re.sub(r"g\.lattice_step\[a\]", "cache.lattice[a].pitch", value)
    aliases = {"index": "cell", "s": "system", "grid_axis_phase": "geo_grid_axis_phase"}
    value = re.sub(r"\b[A-Za-z_]\w*\b", lambda m: aliases.get(m[0], m[0]), value)
    return hashlib.sha256(tokens(value).encode()).hexdigest()


class GridStoreBoundary(unittest.TestCase):
    def test_public_module_has_no_host_role_parser_or_world_dependency(self):
        code = (ROOT / "geometry-core/kernel/grid_store.h").read_text(encoding="utf-8")
        code += (ROOT / "geometry-core/kernel/grid_store.c").read_text(encoding="utf-8")
        code = re.sub(r"/\*.*?\*/|//[^\n]*", "", code, flags=re.S)
        self.assertNotRegex(code, r"\b(?:World|ReferenceGrid|main_along|panel|snprintf|FILE|scene_error|parse_coord)\b")
        self.assertEqual(["grid.h", "parameters.h", "internal/grid_store.h", "codec.h"],
            re.findall(r'^\s*#include\s+"([^"]+)"', code, flags=re.M))

    def test_axis_validation_matches_frozen_pre_extraction_tokens(self):
        source = (ROOT / "geometry-core/kernel/grid_store.c").read_text(encoding="utf-8")
        self.assertEqual(AXIS_BASELINE, axis_digest(source, "geo_grid_axis_valid"))

    def test_translation_unsigned_arithmetic_matches_frozen_pre_extraction_tokens(self):
        source = (ROOT / "geometry-core/kernel/grid_store.c").read_text(encoding="utf-8")
        self.assertEqual(TRANSLATION_BASELINE, translation_digest(source, "geo_grid_binding_translation"))


class NativeGridStore(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        build = native()
        source = build.work / "grid-store-client.c"
        shutil.copy2(ROOT / "tests/geo261_grid_store_harness.c", source)
        cls.client = build.compile(source, "grid-store-client")
        cls.exe = build.link("grid-store-client", [cls.client, build.grid_store_object,
            build.grid_object, build.geometry_object, build.codec_object])

    def case(self, name, exe=None):
        result = subprocess.run([str(exe or self.exe), name], capture_output=True, text=True, timeout=10)
        self.assertIn(result.returncode, (0, 1), "Native crash/setup failure is not a grid-store verdict: " + result.stderr)
        return result.returncode

    def test_owned_arrays_refs_rules_clone_and_alias_safe_replacement(self):
        self.assertEqual(0, self.case("ownership"))

    def test_capacity_order_replacement_removal_and_full_uint32_ids(self):
        self.assertEqual(0, self.case("capacity"))

    def test_structural_rejection_preserves_existing_owned_value(self):
        self.assertEqual(0, self.case("invalid-inputs"))

    def test_six_axis_modes_limits_and_derived_phase_outside_output_domain(self):
        self.assertEqual(0, self.case("axes"))

    def test_definition_validation_order_utf8_mixed_space_and_separate_rules(self):
        self.assertEqual(0, self.case("system-validation"))

    def test_redeclaration_preserves_rule_highwater_and_forbids_implicit_space_conversion(self):
        self.assertEqual(0, self.case("redeclaration"))

    def test_parameter_callback_order_partial_cache_and_stagger_short_circuit(self):
        self.assertEqual(0, self.case("parameters"))

    def test_explicit_zero_stagger_negative_values_and_rejection_precedence(self):
        self.assertEqual(0, self.case("stagger"))

    def test_rule_identity_highwater_overlap_divisibility_and_cell_limits(self):
        self.assertEqual(0, self.case("rules"))

    def test_fraction_reduction_is_atomic_for_both_axes(self):
        self.assertEqual(0, self.case("fractions"))

    def test_binding_uses_exact_vertex_key_and_opposite_negative_cell_parity(self):
        self.assertEqual(0, self.case("binding-geometry"))

    def test_binding_failures_preserve_prior_or_partial_axis_cache(self):
        self.assertEqual(0, self.case("binding-failures"))

    def test_translation_uses_unsigned_magnitudes_at_int64_limits(self):
        self.assertEqual(0, self.case("translation-limits"))

    def mutant(self, name, before, after):
        build = native()
        source = (build.kernel / "grid_store.c").read_text(encoding="utf-8")
        self.assertEqual(1, source.count(before), "Negative control must change exactly one expression")
        path = build.work / ("grid-store-" + name + ".c")
        path.write_text(source.replace(before, after), encoding="utf-8")
        obj = build.compile(path, "grid-store-" + name)
        return build.link("grid-store-" + name, [self.client, obj, build.grid_object, build.geometry_object, build.codec_object])

    def test_wrong_axis_parity_negative_control_fails_an_independent_coordinate(self):
        self.assertEqual(0, self.case("binding-geometry"))
        exe = self.mutant("wrong-parity", "binding->cell[1 - a] & 1", "binding->cell[a] & 1")
        self.assertEqual(1, self.case("binding-geometry", exe))
        self.assertEqual(0, self.case("binding-geometry"))

    def test_explicit_zero_acceptance_negative_control_fails_a_normal_assertion(self):
        self.assertEqual(0, self.case("stagger"))
        exe = self.mutant("zero-stagger", "if (a->stagger == 0) return geo_grid_error(error, GEO_GRID_STORE_STAGGER_ZERO);",
            "if (a->stagger == 0) return true;")
        self.assertEqual(1, self.case("stagger", exe))
        self.assertEqual(0, self.case("stagger"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
