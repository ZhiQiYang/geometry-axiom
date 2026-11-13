"""Owned neutral regions and the extracted boundary-local identity algorithm.

The C witness uses only public region/geometry headers and actual K objects.
Host geometry hashes, binding checks and product mutation witnesses remain in
the integration suite; a passing isolated client is not product integration.
"""
from __future__ import annotations

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
from tests.test_geo261_native_kernel import native

BASELINE = "c28ea9639b79881f30995cd79ce843346373c31e"
BASELINE_RECONCILE_TOKENS = "65e0c0c8f7c40039fedc84cb0b88eb222953079c66fcb9abf29709d21b911b81"
ERRORS = {
    "the previous boundary identity table is invalid": "PREVIOUS_INVALID",
    "too many boundary loops": "TOO_MANY_LOOPS",
    "too many boundary vertices": "TOO_MANY_VERTICES",
    "an identified vertex moved, disappeared, or is ambiguous; use boundary-keyed with the current geometry-hash": "IDENTITY_CHANGED",
    "boundary vertex key space is exhausted": "EXHAUSTED",
    "invalid, zero, duplicate, or inconsistent boundary vertex keys": "INVALID",
    "a retired boundary vertex key cannot be reused": "RETIRED_KEY",
    "boundary vertex key allocation cannot move backwards": "HIGHWATER_BACKWARDS",
}


def reconcile_digest(source, *, legacy=False):
    """Ignore only extraction mechanics; retain every condition and its order.

    The host's prior lookup already guaranteed matching boundary ids. The
    public per-region API explicitly rejects a mismatched baseline. Zeroing
    and assignment use memory operations to preserve POD padding exactly.
    """
    source = re.sub(r"/\*.*?\*/|//[^\n]*", "", source.replace("\r", ""), flags=re.S)
    if legacy:
        begin = source.index("if (old && !boundary_keys_valid(old_boundary,old))")
        end = source.index("++m;", begin)
    else:
        begin = source.index("if (old && (!geo_region_keys_valid(old_boundary, old)")
        end = source.index("return GEO_REGION_KEYS_OK;", begin)
    source = source[begin:end]
    renamed = {
        "BoundaryVertexKeys": "GeoRegionKeys", "PolygonLoop2": "GeoRegionLoop",
        "SurfacePoint2": "GeoPoint2", "POLY_MAX_HOLES": "GEO_REGION_MAX_HOLES",
        "POLY_MAX_VERTICES": "GEO_LOOP_MAX_VERTICES",
        "boundary_keys_valid": "geo_region_keys_valid", "boundary_keys_loop": "geo_region_loop",
        "boundary_keys_has": "geo_region_keys_has",
    }
    for before, after in renamed.items():
        source = re.sub(r"\b" + before + r"\b", after, source)
    for message, status in ERRORS.items():
        source = re.sub(r'return\s+boundary_keys_error\(error,cap,"' + re.escape(message) + r'"\);',
                        "return GEO_REGION_KEYS_" + status + ";", source)
    source = re.sub(r"GeoRegionKeys\s+remapped\s*=\s*\{\s*0\s*\}\s*;",
                    "GeoRegionKeys remapped;memset(&remapped,0,sizeof remapped);", source)
    source = re.sub(r"\*keys\s*=\s*remapped\s*;", "memcpy(keys,&remapped,sizeof remapped);", source)
    source = re.sub(r"if\s*\(old\s*&&\s*\(!geo_region_keys_valid\(old_boundary,\s*old\)\s*\|\|\s*old->boundary_id\s*!=\s*b->id\)\)",
                    "if(old&&!geo_region_keys_valid(old_boundary,old))", source)
    tokens = re.findall(r'"(?:\\.|[^"\\])*"|[A-Za-z_]\w*|\d+|[^\s]', source)
    return hashlib.sha256(json.dumps(tokens, ensure_ascii=False, separators=(",", ":")).encode("utf-8")).hexdigest()


class RegionExtraction(unittest.TestCase):
    def test_reconciliation_conditions_and_order_preserve_frozen_product(self):
        source = (ROOT / "geometry-core/kernel/regions.c").read_text(encoding="utf-8")
        self.assertEqual(BASELINE_RECONCILE_TOKENS, reconcile_digest(source), BASELINE)

    def test_public_module_has_no_host_kind_fixity_world_or_binding_policy(self):
        source = (ROOT / "geometry-core/kernel/regions.h").read_text(encoding="utf-8")
        source += (ROOT / "geometry-core/kernel/regions.c").read_text(encoding="utf-8")
        code = re.sub(r"/\*.*?\*/|//[^\n]*", "", source, flags=re.S)
        self.assertNotRegex(code, r"\b(?:World|BoundaryKind|EdgeFixity|GridBinding|g_boundary_keyed_update|geometry_hash)\b")
        self.assertEqual(["geometry.h", "internal/regions.h"], re.findall(r'^\s*#include\s+"([^"]+)"', source, flags=re.M))


class NativeRegions(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        build = native()
        source = build.work / "regions-client.c"
        shutil.copy2(ROOT / "tests/geo261_regions_harness.c", source)
        cls.client = build.compile(source, "regions-client")
        cls.exe = build.link("regions-client", [cls.client, build.regions_object, build.geometry_object])

    def case(self, name, exe=None):
        run = subprocess.run([str(exe or self.exe), name], capture_output=True, text=True, timeout=10)
        self.assertIn(run.returncode, (0, 1), "Native crash/setup failure is not an identity verdict: " + run.stderr)
        return run.returncode

    def test_owned_geometry_keys_clone_aliasing_and_zero_inactive_storage(self):
        self.assertEqual(0, self.case("ownership"))

    def test_capacity_stable_replacement_deletion_order_and_uint32_identity(self):
        self.assertEqual(0, self.case("capacity"))

    def test_actual_kernel_validation_keeps_collinear_vertices_and_holes(self):
        self.assertEqual(0, self.case("geometry"))

    def test_explicit_initialization_keeps_existing_highwater_and_table_invariants(self):
        self.assertEqual(0, self.case("initialization"))

    def test_ordinary_reordering_insertion_and_repeated_reconciliation_preserve_identity(self):
        self.assertEqual(0, self.case("ordinary"))

    def test_moved_missing_ambiguous_and_invalid_baselines_are_distinct_failures(self):
        self.assertEqual(0, self.case("invalid-mapping"))

    def test_keyed_movement_retirement_and_highwater_follow_existing_rules(self):
        self.assertEqual(0, self.case("keyed"))

    def test_last_uint32_key_and_exhaustion_never_wrap_or_partially_assign(self):
        self.assertEqual(0, self.case("exhaustion"))

    def test_lookup_resolves_real_loop_vertex_without_touching_failed_output(self):
        self.assertEqual(0, self.case("lookup"))

    def mutant(self, name, before, after):
        build = native()
        source = (build.kernel / "regions.c").read_text(encoding="utf-8")
        self.assertEqual(1, source.count(before), "Negative control must change exactly one expression")
        path = build.work / ("regions-" + name + ".c")
        path.write_text(source.replace(before, after), encoding="utf-8")
        obj = build.compile(path, "regions-" + name)
        return build.link("regions-" + name, [self.client, obj, build.geometry_object])

    def test_coordinate_matching_negative_control_is_an_assertion_failure(self):
        self.assertEqual(0, self.case("ordinary"))
        exe = self.mutant("coordinate", "loop->v[i].u == p.u && loop->v[i].v == p.v", "loop->v[i].u == p.u || loop->v[i].v == p.v")
        self.assertEqual(1, self.case("ordinary", exe))
        self.assertEqual(0, self.case("ordinary"))

    def test_retired_key_negative_control_is_an_assertion_failure(self):
        self.assertEqual(0, self.case("keyed"))
        exe = self.mutant("retired", "(!old->next_key || key < old->next_key)", "(!old->next_key)")
        self.assertEqual(1, self.case("keyed", exe))
        self.assertEqual(0, self.case("keyed"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
