"""W support extraction: fixed oracles, frozen equivalence and guard controls.

The isolated client compiles only the public W/K closure. Its value assertions
do not derive expectations from W. A second object is built from the frozen
product's literal function bodies for additional compatibility comparison.
Product consumption and bridge controls belong to the native integration tests.
"""
from __future__ import annotations

from functools import lru_cache
import hashlib
from pathlib import Path
import re
import shutil
import subprocess
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from tests.test_geo261_native_kernel import native

MODULE = ROOT / "geometry-templates/woodworking/native"
BASELINE = "debd47ead0881f4cd15ab8a6ceae6f23f92dc81e"
FROZEN_FIXTURE = ROOT / "tests/geo261_supports_legacy_fixture.txt"
FROZEN_FIXTURE_SHA256 = "2b3e8d7f9c4e226e22c3764ed9045e977430097d1aa7a99aa408e850ec84e04f"
FUNCTIONS = {
    "stop_face_matches_ref": "wood_stop_matches_ref",
    "stop_ref_candidates": "wood_stop_ref_candidates",
    "stop_face_shadowed": "wood_stop_shadowed",
    "pick_stop": "wood_stop_pick",
    "count_legal_stops": "wood_stop_count_legal",
    "timber_role_props": "wood_member_boundary_props",
}
RENAMED = {
    **FUNCTIONS,
    "StopFaceKind": "WoodStopFaceKind",
    "StopFace": "WoodStopFace",
    "StopFaceRef": "WoodStopRef",
    "STOP_OUTLINE_EDGE": "WOOD_STOP_OUTLINE_EDGE",
    "STOP_HOLE_EDGE": "WOOD_STOP_HOLE_EDGE",
    "STOP_TIMBER_SIDE": "WOOD_STOP_MEMBER_SIDE",
    "EDGE_FREE": "WOOD_STOP_FREE",
    "EDGE_FIXED": "WOOD_STOP_FIXED",
    "SurfaceId": "uint32_t",
    "TimberId": "uint32_t",
    "Coord": "GeoCoord",
    "SurfaceSegment2": "GeoSegment2",
    "coord_min": "wood_support_min",
    "coord_max": "wood_support_max",
}


@lru_cache(maxsize=1)
def frozen_source():
    # The judge was extracted directly from BASELINE, not from W. It travels
    # with git archives so isolated validation needs no repository history.
    # Checkout CRLF is normalized before hashing, not treated as source drift.
    raw = FROZEN_FIXTURE.read_bytes().replace(b"\r\n", b"\n")
    actual = hashlib.sha256(raw).hexdigest()
    if actual != FROZEN_FIXTURE_SHA256:
        raise AssertionError("Frozen support judge hash mismatch: " + actual)
    source = raw.decode("utf-8")
    if BASELINE + ":current_geometry.c" not in source:
        raise AssertionError("Frozen support judge has lost its original provenance")
    return source


def without_comments(source):
    return re.sub(r"/\*.*?\*/|//[^\n]*", "", source, flags=re.S)


def definition(source, name):
    source = without_comments(source)
    match = re.search(r"^(?:static\s+)?(?:bool|size_t|Coord|GeoCoord)\s+" + re.escape(name)
                      + r"\s*\([^;]*?\)\s*\{", source, flags=re.M | re.S)
    if not match:
        raise AssertionError("Missing function definition: " + name)
    depth = 1
    end = match.end()
    while depth:
        if end >= len(source):
            raise AssertionError("Unbalanced function: " + name)
        depth += (source[end] == "{") - (source[end] == "}")
        end += 1
    return source[match.start():end]


def body(source, name):
    text = definition(source, name)
    return text[text.index("{"):]


def tokens(source):
    return [RENAMED.get(token, token) for token in re.findall(r"[A-Za-z_]\w*|\d+|[^\s]", source)]


def adapted_boundary_body(source):
    text = body(source, "timber_role_props")
    text = text.replace("boundary->outline.count", "outline->count")
    text = text.replace("boundary == NULL", "outline == NULL")
    pattern = r"if\s*\(!loop_get_edge_segment\(&boundary->outline,\s*i,\s*&seg\)\)\s*\{\s*continue;\s*\}"
    text, count = re.subn(pattern,
        "seg.start = outline->v[i]; seg.end = outline->v[(i + 1) % outline->count];", text)
    if count != 1:
        raise AssertionError("Frozen boundary-to-view adapter must replace one edge read")
    return text


def frozen_translation_unit():
    """Use the unmodified old bodies, including the old loop getter.

    The tiny carrier represents only the outline field actually read by the
    frozen helper. It has no behavior; the wrapper passes the same view through.
    """
    prefix = '''#include "supports.h"
typedef GeoCoord Coord;
typedef GeoLoop2View PolygonLoop2;
typedef GeoSegment2 SurfaceSegment2;
typedef struct { PolygonLoop2 outline; } SpaceBoundarySurface;
typedef WoodStopFace StopFace;
typedef WoodStopRef StopFaceRef;
enum { STOP_OUTLINE_EDGE=0, STOP_HOLE_EDGE=1, STOP_TIMBER_SIDE=2 };
enum { EDGE_FREE=0, EDGE_FIXED=1 };
'''
    original = frozen_source()
    names = {name: "frozen_" + current.removeprefix("wood_") for name, current in FUNCTIONS.items()}
    # The role helper retains the old boundary carrier and gets a view adapter.
    names["timber_role_props"] = "frozen_timber_role_props"
    bodies = [definition(original, name) for name in
              ("coord_min", "coord_max", "loop_get_edge_segment", *FUNCTIONS)]
    for i, text in enumerate(bodies):
        text = re.sub(r"\b(" + "|".join(names) + r")\b", lambda match: names[match[0]], text)
        # Expose stop functions to the harness; utility/role helpers stay local.
        if i >= 3 and i < 8:
            text = text.removeprefix("static ")
        bodies[i] = text
    suffix = '''
bool frozen_boundary_props(const GeoLoop2View *outline, bool along_v,
    GeoCoord span_lo, GeoCoord span_hi, GeoCoord cross_lo, GeoCoord cross_hi,
    bool *on, bool *covers, int *edge)
{
    SpaceBoundarySurface boundary;
    if (outline != NULL) boundary.outline = *outline;
    return frozen_timber_role_props(outline == NULL ? NULL : &boundary, along_v,
        span_lo, span_hi, cross_lo, cross_hi, on, covers, edge);
}
'''
    return prefix + "\n\n".join(bodies) + suffix


class WoodSupportsSourcePreservation(unittest.TestCase):
    def test_extracted_bodies_preserve_frozen_product(self):
        source = (MODULE / "supports.c").read_text(encoding="utf-8")
        old = frozen_source()
        for original, current in FUNCTIONS.items():
            with self.subTest(function=current):
                expected = adapted_boundary_body(old) if original == "timber_role_props" else body(old, original)
                self.assertEqual(tokens(expected), tokens(body(source, current)), current)

    def test_storage_layout_and_signed_index_definitions_preserve_frozen_product(self):
        current = without_comments((MODULE / "supports.h").read_text(encoding="utf-8"))
        old = without_comments(frozen_source())
        for original in ("StopFaceKind", "StopFace", "StopFaceRef"):
            with self.subTest(definition=original):
                kind = "enum" if original == "StopFaceKind" else "struct"
                pattern = r"typedef\s+" + kind + r"\s*\{([^{}]+)\}\s*"
                expected = re.search(pattern + original + r"\s*;", old, flags=re.S)
                actual = re.search(pattern + RENAMED[original] + r"\s*;", current, flags=re.S)
                self.assertIsNotNone(expected)
                self.assertIsNotNone(actual)
                self.assertEqual(tokens(expected[1]), tokens(actual[1]))

    def test_imports_only_own_header_and_public_geometry(self):
        for filename, includes in (("supports.h", ["geometry.h"]), ("supports.c", ["supports.h"])):
            source = (MODULE / filename).read_text(encoding="utf-8")
            self.assertEqual(includes, re.findall(r'^\s*#include\s+"([^"]+)"', source, flags=re.M))
            self.assertNotRegex(without_comments(source), r"\b(?:World|SpaceBoundarySurface|PlacementSurface|TimberId|SurfaceId)\b")

    def test_frozen_comparison_contains_actual_bodies_and_no_product_include(self):
        frozen_source.cache_clear()
        with patch("subprocess.check_output", side_effect=AssertionError("Archive judge must not invoke Git")):
            source = frozen_translation_unit()
        self.assertEqual(["supports.h"], re.findall(r'^\s*#include\s+"([^"]+)"', source, flags=re.M))
        self.assertIn("frozen_stop_matches_ref", source)
        self.assertIn("frozen_stop_count_legal", source)
        self.assertIn("loop_get_edge_segment(&boundary->outline", source)


class WoodSupports(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        build = native()
        client = build.woodworking / "wood-supports-client.c"
        shutil.copy2(ROOT / "tests/geo261_supports_harness.c", client)
        frozen = build.woodworking / "wood-supports-frozen.c"
        frozen.write_text(frozen_translation_unit(), encoding="utf-8")
        cls.client_object = build.compile(client, "wood-supports-client")
        cls.frozen_object = build.compile(frozen, "wood-supports-frozen")
        cls.exe = build.link("wood-supports-client", [cls.client_object, cls.frozen_object, build.wood_supports_object])

    def case(self, name, exe=None):
        result = subprocess.run([str(exe or self.exe), name], capture_output=True, text=True, timeout=10)
        self.assertIn(result.returncode, (0, 1), "Crash/setup failure is not a support assertion: " + result.stderr)
        if result.returncode == 1:
            self.assertRegex(result.stderr, r"ASSERT:[a-z0-9-]+")
        return result

    def test_layout_and_fixity_compatibility(self):
        self.assertEqual(0, self.case("layout").returncode)

    def test_reference_identity_zero_full_uint32_and_negative_indices(self):
        self.assertEqual(0, self.case("references").returncode)

    def test_candidate_filter_order_capacity_and_accumulated_flags(self):
        self.assertEqual(0, self.case("candidates").returncode)

    def test_shadowing_respects_face_order_and_exposed_partial_overlap(self):
        self.assertEqual(0, self.case("shadow").returncode)

    def test_pick_includes_free_and_only_writes_unique_hit(self):
        self.assertEqual(0, self.case("pick").returncode)

    def test_legal_count_excludes_free_without_requiring_uniqueness(self):
        self.assertEqual(0, self.case("legal").returncode)

    def test_boundary_role_exact_geometry_and_tiebreaks(self):
        self.assertEqual(0, self.case("boundary").returncode)

    def test_runtime_matches_separately_compiled_frozen_bodies(self):
        self.assertEqual(0, self.case("equivalence").returncode)

    def mutant(self, name, function, before, after):
        build = native()
        source = (build.woodworking / "supports.c").read_text(encoding="utf-8")
        original = definition(source, function)
        self.assertEqual(1, original.count(before), "Guard mutation must hit once: " + name)
        changed = original.replace(before, after)
        # definitions() strips comments; source contains no internal comments in
        # exported bodies, so replacement must still be byte-for-byte unique.
        self.assertEqual(1, source.count(original))
        path = build.woodworking / ("supports-" + name + ".c")
        path.write_text(source.replace(original, changed), encoding="utf-8")
        obj = build.compile(path, "wood-supports-" + name)
        return build.link("wood-supports-" + name, [self.client_object, self.frozen_object, obj])

    def test_guard_mutations_fail_named_independent_assertions(self):
        # Every listed negative control changes a real W decision. No source
        # grep, compiler failure or crash is accepted as the behavioral verdict.
        controls = (
            ("null-ref", "wood_stop_matches_ref", "return false;", "return true;", "references", "reference-null-face"),
            ("ref-kind", "wood_stop_matches_ref", "r->kind == 1", "false", "references", "reference-member-uint32-max"),
            ("ref-hole-sign", "wood_stop_matches_ref", "r->hole < 0", "false", "references", "reference-outline"),
            ("member-kind", "wood_stop_matches_ref", "f->kind == WOOD_STOP_MEMBER_SIDE", "true", "references", "reference-member-kind"),
            ("member-id", "wood_stop_matches_ref", "f->timber_id == r->timber", "true", "references", "reference-member-id"),
            ("outline-kind", "wood_stop_matches_ref", "f->kind == WOOD_STOP_OUTLINE_EDGE", "true", "references", "reference-outline-kind"),
            ("outline-index", "wood_stop_matches_ref", "f->kind == WOOD_STOP_OUTLINE_EDGE && f->edge_index == r->edge", "f->kind == WOOD_STOP_OUTLINE_EDGE", "references", "reference-outline-edge"),
            ("hole-kind", "wood_stop_matches_ref", "f->kind == WOOD_STOP_HOLE_EDGE", "true", "references", "reference-hole-kind"),
            ("hole-index", "wood_stop_matches_ref", "f->hole_index == r->hole", "true", "references", "reference-hole-index"),
            ("hole-edge", "wood_stop_matches_ref", "f->hole_index == r->hole && f->edge_index == r->edge", "f->hole_index == r->hole", "references", "reference-hole-edge"),
            ("match-filter", "wood_stop_ref_candidates", "!wood_stop_matches_ref(f, r)", "false", "candidates", "candidates-match-width-free"),
            ("candidate-low", "wood_stop_ref_candidates", "f->lo > cross_lo", "false", "candidates", "candidates-width-before-free"),
            ("candidate-high", "wood_stop_ref_candidates", "f->hi < cross_hi", "false", "candidates", "candidates-match-width-free"),
            ("candidate-free", "wood_stop_ref_candidates", "f->fixity == WOOD_STOP_FREE", "false", "candidates", "candidates-match-width-free"),
            ("candidate-cap", "wood_stop_ref_candidates", "n < out_cap", "true", "candidates", "candidates-capacity-count"),
            ("shadow-kind", "wood_stop_shadowed", "faces[i].kind != WOOD_STOP_MEMBER_SIDE", "false", "shadow", "shadow-only-member"),
            ("shadow-order", "wood_stop_shadowed", "j < i", "j <= i", "shadow", "shadow-exposed-extension"),
            ("shadow-coordinate", "wood_stop_shadowed", "faces[j].fixed == faces[i].fixed", "true", "shadow", "shadow-same-coordinate"),
            ("shadow-low", "wood_stop_shadowed", "faces[j].lo <= lo", "true", "shadow", "shadow-full-low"),
            ("shadow-high", "wood_stop_shadowed", "faces[j].hi >= hi", "true", "shadow", "shadow-exposed-extension"),
            ("pick-coordinate", "wood_stop_pick", "f->fixed != at", "false", "pick", "pick-coordinate-filter"),
            ("pick-low", "wood_stop_pick", "f->lo > lo", "false", "pick", "pick-shadowed-one"),
            ("pick-high", "wood_stop_pick", "f->hi < hi", "false", "pick", "pick-exposed-extension"),
            ("pick-shadow", "wood_stop_pick", "wood_stop_shadowed(faces, i, lo, hi)", "false", "pick", "pick-shadowed-one"),
            ("pick-unique", "wood_stop_pick", "hits == 1", "hits > 0", "pick", "pick-ambiguous-output-unchanged"),
            ("pick-output", "wood_stop_pick", "out_face != NULL", "false", "pick", "pick-shadowed-one"),
            ("legal-coordinate", "wood_stop_count_legal", "f->fixed == at", "true", "legal", "legal-coordinate-filter"),
            ("legal-low", "wood_stop_count_legal", "f->lo <= lo", "true", "legal", "legal-low-filter"),
            ("legal-high", "wood_stop_count_legal", "f->hi >= hi", "true", "legal", "legal-high-filter"),
            ("legal-free", "wood_stop_count_legal", "f->fixity != WOOD_STOP_FREE", "true", "legal", "legal-free-excluded-and-shadows"),
            ("legal-shadow", "wood_stop_count_legal", "!wood_stop_shadowed(faces, i, lo, hi)", "true", "legal", "legal-free-excluded-and-shadows"),
            ("boundary-null", "wood_member_boundary_props", "return false;", "return true;", "boundary", "boundary-null-defaults"),
            ("boundary-axis", "wood_member_boundary_props", "edge_along_v != along_v", "false", "boundary", "boundary-cover-high-required"),
            ("boundary-side", "wood_member_boundary_props", "edge_fixed != cross_lo && edge_fixed != cross_hi", "false", "boundary", "boundary-no-collinear-side"),
            ("boundary-touch", "wood_member_boundary_props", "ov <= 0", "ov < 0", "boundary", "boundary-positive-overlap-only"),
            ("boundary-cover-low", "wood_member_boundary_props", "span_lo <= edge_lo", "true", "boundary", "boundary-cover-low-required"),
            ("boundary-cover-high", "wood_member_boundary_props", "span_hi >= edge_hi", "true", "boundary", "boundary-cover-high-required"),
            ("boundary-cover", "wood_member_boundary_props", "(covers && !best_covers)", "false", "boundary", "boundary-cover-beats-longer"),
            ("boundary-overlap", "wood_member_boundary_props", "ov > best_overlap", "false", "boundary", "boundary-later-longer-wins"),
            ("boundary-tie", "wood_member_boundary_props", "ov > best_overlap", "ov >= best_overlap", "boundary", "boundary-tie-earlier-index"),
            ("boundary-output", "wood_member_boundary_props", "best >= 0", "false", "boundary", "boundary-low-side"),
        )
        for name, function, before, after, case, assertion in controls:
            with self.subTest(guard=name):
                self.assertEqual(0, self.case(case).returncode)
                mutant = self.mutant(name, function, before, after)
                result = self.case(case, mutant)
                self.assertEqual(1, result.returncode, "W guard mutation survived: " + name)
                self.assertIn("ASSERT:" + assertion, result.stderr)
                self.assertEqual(0, self.case(case).returncode)


if __name__ == "__main__":
    unittest.main(verbosity=2)
