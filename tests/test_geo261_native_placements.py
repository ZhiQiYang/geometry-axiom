"""Neutral plane-domain ownership and the actual K geometric queries.

Native clients build only K objects. Independent explicit examples preserve
the original rectangle/contact/component behavior; source checks do not claim
that the application's adapters have been integrated or dynamically tested.
"""
from __future__ import annotations

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


def code(source):
    return re.sub(r"/\*.*?\*/|//[^\n]*", "", source, flags=re.S)


def definition(source, name):
    text = code(source)
    match = re.search(r"^[\w *]+\b" + re.escape(name) + r"\s*\([^;]*?\)\s*\{", text, re.M | re.S)
    if match is None:
        raise AssertionError("Missing placement function " + name)
    depth, end = 1, match.end()
    while depth:
        depth += (text[end] == "{") - (text[end] == "}")
        end += 1
    return text[match.start():end]


class PlacementSource(unittest.TestCase):
    def test_public_schema_and_implementation_have_no_template_or_host_policy(self):
        source = "\n".join((KERNEL / name).read_text(encoding="utf-8") for name in ("placements.h", "placements.c", "internal/placements.h"))
        self.assertNotRegex(code(source), r"\b(?:World|FinishSurface|PanelFill|PlacementSurface|derived_fill_id|derived_h|EdgeFixity|Timber|boundary_id)\b")
        self.assertEqual(["regions.h", "internal/placements.h", "../placements.h"], re.findall(r'^\s*#include\s+"([^"]+)"', source, re.M))

    def test_private_store_is_inline_pod_and_public_api_returns_const_definitions(self):
        private = code((KERNEL / "internal/placements.h").read_text(encoding="utf-8"))
        body = private[private.index("struct GeoPlacementStore {"):private.index("};")]
        self.assertNotIn("*", body)
        self.assertIn("GeoPlacementDefinition items[GEO_PLACEMENT_CAPACITY]", body)
        public = (KERNEL / "placements.h").read_text(encoding="utf-8")
        self.assertIn("const GeoPlacementDefinition *geo_placements_find", public)
        self.assertIn("const GeoPlacementDefinition *geo_placements_at", public)

    def test_stage_and_full_validation_are_separate_and_geometry_calls_actual_kernel(self):
        source = (KERNEL / "placements.c").read_text(encoding="utf-8")
        stage = definition(source, "geo_placements_stage")
        self.assertIn("placement_structure(definition)", stage)
        self.assertNotRegex(stage, r"geo_(?:frame_is_valid|region_is_valid|regions_find|placement_is_valid)")
        valid = definition(source, "geo_placement_is_valid")
        self.assertIn("geo_frame_is_valid", valid)
        self.assertIn("geo_region_is_valid", valid)
        self.assertIn("geo_regions_find", valid)
        self.assertIn("geo_region_contains_point", definition(source, "geo_placement_contains_point"))
        self.assertIn("geo_region_contains_rect", definition(source, "geo_placement_component_for_rect"))
        self.assertIn("geo_loop_bbox", definition(source, "geo_placement_local_bounds"))


class NativePlacements(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        build = native()
        client = build.work / "placements-client.c"
        shutil.copy2(ROOT / "tests/geo261_placements_harness.c", client)
        cls.client = build.compile(client, "placements-client")
        cls.exe = build.link("placements-client", [cls.client, build.placements_object, build.regions_object, build.geometry_object])

    def case(self, name, exe=None):
        result = subprocess.run([str(exe or self.exe), name], capture_output=True, text=True, timeout=20)
        self.assertIn(result.returncode, (0, 1), "Native crash/setup failure is not a placement verdict: " + result.stderr)
        if result.returncode == 1:
            self.assertRegex(result.stderr, r"ASSERT:[a-z0-9-]+")
        return result

    def test_owns_geometry_zeroes_unused_bytes_and_supports_independent_inline_clones(self):
        self.assertEqual(0, self.case("storage").returncode)

    def test_capacity_replacement_deletion_order_and_full_uint32_identity(self):
        self.assertEqual(0, self.case("capacity").returncode)

    def test_full_validation_checks_frame_rect_reference_and_every_component(self):
        self.assertEqual(0, self.case("validation").returncode)

    def test_staging_preserves_candidate_order_but_rejects_unbounded_active_counts(self):
        self.assertEqual(0, self.case("stage").returncode)

    def test_rectangle_contact_original_degenerate_query_and_failed_output_contract(self):
        self.assertEqual(0, self.case("rectangle").returncode)

    def test_exact_region_reference_holes_contact_and_current_region_updates(self):
        self.assertEqual(0, self.case("reference").returncode)

    def test_every_component_empty_set_first_match_and_no_bbox_or_spanning_union(self):
        self.assertEqual(0, self.case("components").returncode)

    def test_views_use_independent_caller_scratch_and_borrow_explicit_coordinate_owners(self):
        self.assertEqual(0, self.case("views").returncode)

    def test_single_guard_controls_fail_named_independent_oracles(self):
        controls = (
            ("capacity", "geo_placements_stage", "if (at>=GEO_PLACEMENT_CAPACITY)", "if (at>=GEO_PLACEMENT_CAPACITY-1)", "capacity", "capacity-full-sixteen"),
            ("frame", "geo_placement_is_valid", "!geo_frame_is_valid(&definition->frame)", "false", "validation", "validation-handed-frame"),
            ("range", "geo_placement_is_valid", "geo_coord_in_range(rect->max_u)", "true", "validation", "validation-rect-range"),
            ("positive", "geo_placement_is_valid", "rect->min_u<rect->max_u", "true", "validation", "validation-positive-rect"),
            ("missing-reference", "geo_placement_is_valid", "if (!region || !placement_region_structure(region)) return false;", "if (!region || !placement_region_structure(region)) return true;", "validation", "validation-missing-reference"),
            ("component-validation", "geo_placement_is_valid", "if (!geo_region_is_valid(&view)) return false;", "if (false) return false;", "validation", "validation-every-component"),
            ("empty-set", "geo_placement_is_valid", "    return true;\n}", "    return definition->component_count>0;\n}", "validation", "validation-empty-set"),
            ("zero-tail", "geo_placements_remove", "memset(&store->items[--store->count],0,sizeof *store->items);", "--store->count;", "storage", "store-zero-removed-tail"),
            ("zero-inactive", "geo_placements_stage", "memset(&next,0,sizeof next);", "memset(&next,0xa5,sizeof next);", "storage", "store-zero-inactive"),
            ("contact", "geo_placement_contains_point", "point.u<=definition->rect.max_u", "point.u<definition->rect.max_u", "rectangle", "rect-contact-point"),
            ("hole", "geo_placement_contains_point", "geo_region_contains_point(&domain.regions[c],point)", "geo_loop_contains_point(&domain.regions[c].outline,point)", "reference", "reference-hole-interior"),
            ("second-component", "geo_placement_contains_point", "c<domain.count", "c<domain.count&&c<1", "components", "set-second-point"),
            ("component-identity", "geo_placement_component_for_rect", "if (index) *index=c;", "if (index) *index=0;", "components", "set-second-rectangle"),
            ("bounds", "geo_placement_local_bounds", "c<domain.count", "c<domain.count&&c<1", "components", "set-all-component-bounds"),
        )
        build = native()
        original = (build.kernel / "placements.c").read_text(encoding="utf-8")
        for name, function, before, after, case, marker in controls:
            with self.subTest(mutation=name):
                body = definition(original, function)
                self.assertEqual(1, body.count(before), "Mutation must hit one guard: " + name)
                # Remove comments once so the exact parsed definition occurs in
                # the translation unit; no executable token is altered here.
                source = code(original)
                self.assertEqual(1, source.count(body))
                path = build.kernel / ("placements-" + name + ".c")
                path.write_text(source.replace(body, body.replace(before, after)), encoding="utf-8")
                obj = build.compile(path, "placements-" + name)
                exe = build.link("placements-" + name, [self.client, obj, build.regions_object, build.geometry_object])
                result = self.case(case, exe)
                self.assertEqual(1, result.returncode, "Surviving placement guard: " + name)
                self.assertIn("ASSERT:" + marker, result.stderr)


if __name__ == "__main__":
    unittest.main()
