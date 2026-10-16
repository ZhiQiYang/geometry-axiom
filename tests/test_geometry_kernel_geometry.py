"""Exact geometric behavior through the standalone, template-free package."""
from dataclasses import replace
from fractions import Fraction
import importlib.util
from pathlib import Path
import sys
import unittest

if importlib.util.find_spec("geometry_kernel") is None:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "geometry-core"))

from geometry_kernel import (BoxDef, CoordinateDomain, EvaluationError, FrameDef,
    Provenance, Quantity, QuantityType, RegionDef, RegionSetDef, SourceKey, Unit,
    canonical_bytes, frame, strict_json_loads)
from geometry_kernel import geometry as geo


FRAME = FrameDef((0, 0, 0), (1, 0, 0), (0, 1, 0), (0, 0, 1))
RECT = ((0, 0), (20, 0), (20, 20), (0, 20))
HOLE = ((5, 5), (15, 5), (15, 15), (5, 15))


def origin(feature=("surface", -1, -1), identity=1):
    return Provenance(("fixture", identity), feature, (identity, *feature))


def extrude(region=None, lo=0, hi=20, identity=1, axes=FRAME):
    region = region or RegionDef(RECT)
    keys = [("bottom_cap", -1, -1), ("top_cap", -1, -1)]
    keys += [("outer_side" if i == 0 else "hole_side", i, j)
             for i, loop in enumerate((region.outer, *region.holes)) for j in range(len(loop))]
    return geo.extrusion_geometry(axes, region, lo, hi, {key: origin(key, identity) for key in keys})


def meshes(geometry):
    return geo.mesh_objects(geometry, geo.build_grid([geometry]))


class KernelGeometryTests(unittest.TestCase):
    def assert_code(self, code, operation):
        with self.assertRaises(EvaluationError) as caught:
            operation()
        self.assertEqual(code, caught.exception.code)

    def test_exact_quantities_and_stable_source_identity(self):
        value = Quantity(QuantityType.DIMENSION, 10, 6, Unit.MM)
        self.assertEqual((5, 3), (value.numerator, value.denominator))
        self.assertEqual(1, value.value * 3 - 4)
        self.assertNotEqual(SourceKey("fixture", (1, "x")), SourceKey("fixture", (2, "x")))
        self.assert_code("QUANTITY_VALUE", lambda: Quantity(QuantityType.COUNT, True, 1, Unit.UNITLESS))
        self.assert_code("QUANTITY_UNIT", lambda: Quantity(QuantityType.COUNT, 1, 1, Unit.MM))

    def test_canonical_json_rejects_duplicate_float_and_surrogate(self):
        self.assertEqual(b'{"a":1,"b":2}', canonical_bytes({"b": 2, "a": 1}))
        for text, code in [(' {"a":1,"a":2}', "DUPLICATE_KEY"), ('1.0', "JSON_TYPE"), ('NaN', "JSON_TYPE")]:
            self.assert_code(code, lambda: strict_json_loads(text))
        self.assert_code("UNICODE", lambda: canonical_bytes("\ud800"))

    def test_frame_is_exact_right_handed_and_checks_input_shape(self):
        axes = frame((10, 20, 30), (0, 1, 0), (0, 0, -1))
        self.assertEqual((6, 22, 27), axes.world((2, 3), 4))
        for bad in ((1, 1, 0), (0, 0, 0)):
            self.assert_code("FACE_FRAME", lambda: frame((0, 0, 0), bad, (0, 1, 0)))
        self.assert_code("VECTOR", lambda: frame((0, 0, 0), (1,), (0, 1, 0)))
        self.assert_code("COORD_RANGE", lambda: frame((True, 0, 0), (1, 0, 0), (0, 1, 0)))

    def test_region_preserves_concavity_holes_and_boundary_contact(self):
        region = RegionDef(((0, 0), (20, 0), (20, 10), (10, 10), (10, 20), (0, 20)), (((2, 2), (8, 2), (8, 8), (2, 8)),))
        self.assertEqual(0, region.location((15, 15)))
        self.assertEqual(0, region.location((3, 3)))
        self.assertEqual(1, region.location((2, 3)))
        self.assertEqual(2, region.location((9, 3)))

    def test_region_rejects_nonorthogonal_zero_and_self_touching_loops(self):
        for points in (((0, 0), (20, 0), (15, 20), (0, 20)),
                       ((0, 0), (20, 0), (20, 0), (0, 20)),
                       ((0, 0), (20, 0), (20, 20), (10, 20), (10, 0), (0, 0), (0, 20))):
            with self.subTest(points=points), self.assertRaises(EvaluationError):
                RegionDef(points)

    def test_region_rejects_holes_crossing_touching_nested_or_overlapping(self):
        examples = [(((0, 2), (3, 2), (3, 5), (0, 5)),),
                    (((18, 2), (22, 2), (22, 5), (18, 5)),),
                    (HOLE, ((6, 6), (8, 6), (8, 8), (6, 8))),
                    (HOLE, ((14, 6), (18, 6), (18, 8), (14, 8)))]
        for holes in examples:
            with self.subTest(holes=holes), self.assertRaises(EvaluationError):
                RegionDef(RECT, holes)

    def test_region_set_validates_actual_interiors_and_accepts_empty(self):
        ring = RegionDef(RECT, (HOLE,))
        island = RegionDef(((6, 6), (8, 6), (8, 8), (6, 8)))
        self.assertEqual(2, len(RegionSetDef((ring, island)).components))
        self.assertEqual((), RegionSetDef(()).components)
        self.assert_code("REGION_COMPONENT_OVERLAP", lambda: RegionSetDef((ring, RegionDef(RECT))))

    def test_public_box_constructs_real_oriented_faces(self):
        axes = frame((10, 20, 30), (0, 1, 0), (0, 0, -1))
        definition = BoxDef(axes, (0, 0, 0), (2, 3, 4), tuple(origin((str(i),)) for i in range(6)))
        result = meshes(geo.box_geometry(definition))
        self.assertEqual("24", result[0]["volume_mm3"])
        self.assertEqual(8, len(result[0]["vertices_mm"]))
        self.assertEqual(12, len(result[0]["triangles"]))
        self.assert_code("BOX_EXTENTS", lambda: replace(definition, upper=(0, 3, 4)))
        self.assert_code("COORD_RANGE", lambda: replace(definition, frame=replace(axes, origin=(100_000_000, 100_000_000, 100_000_000))))

    def test_through_hole_extrusion_has_exact_volume_and_inward_hole_faces(self):
        geometry = extrude(RegionDef(RECT, (HOLE,)))
        result = meshes(geometry)[0]
        self.assertEqual("6000", result["volume_mm3"])
        self.assertEqual("closed", result["closure"])
        self.assertFalse(geometry.inside((10, 10, 10)))
        self.assertTrue(geometry.inside((2, 2, 10)))
        holes = [f for f in geometry.faces if f.sources[0].feature_key[0] == "hole_side"]
        self.assertEqual(4, len(holes))
        self.assertTrue(all(s.normal_sign == 1 for row in result["face_sources"] for s in row))

    def test_extrusion_bounds_and_world_range_are_not_approximated(self):
        self.assert_code("EXTRUSION_SPAN", lambda: extrude(lo=0, hi=True))
        self.assert_code("EXTRUSION_SPAN", lambda: extrude(lo=0, hi=0))
        self.assert_code("EXTRUSION_RANGE", lambda: extrude(hi=100_000_001))
        self.assert_code("EXTRUSION_RANGE", lambda: extrude(axes=replace(FRAME, origin=(100_000_000, 0, 0))))

    def test_l_shell_is_not_replaced_by_its_bounding_box(self):
        region = RegionDef(((0, 0), (20, 0), (20, 10), (10, 10), (10, 20), (0, 20)))
        original = extrude(region)
        enclosed = geo.enclosed_geometry(original.faces)
        self.assertEqual("6000", meshes(enclosed)[0]["volume_mm3"])
        self.assertFalse(enclosed.inside((15, 15, 10)))

    def test_open_shell_has_surface_but_no_known_interior(self):
        faces = extrude().faces[:-1]
        self.assertFalse(geo.analyze_shell(faces)["closed"])
        result = meshes(geo._Geometry(faces))[0]
        self.assertEqual("open", result["closure"])
        self.assertIsNone(result["volume_mm3"])
        self.assert_code("OPEN_SHELL", lambda: geo.enclosed_geometry(faces))

    def test_inward_and_duplicate_shell_faces_are_rejected(self):
        faces = extrude().faces
        self.assert_code("SHELL_INWARD", lambda: geo.enclosed_geometry([replace(f, sign=-f.sign) for f in faces]))
        self.assert_code("SHELL_FACE_OVERLAP", lambda: geo.analyze_shell([*faces, faces[0]]))

    def test_vertex_pinches_and_nonmanifold_edges_are_rejected(self):
        first = extrude().faces
        second = extrude(axes=replace(FRAME, origin=(20, 20, 20)), identity=2).faces
        self.assert_code("SHELL_VERTEX_PINCH", lambda: geo.analyze_shell(first + second))
        a, b, c, d, e = (0, 0, 0), (1, 0, 0), (0, 1, 0), (0, 0, 1), (0, -1, 0)
        self.assert_code("SHELL_NONMANIFOLD_EDGE", lambda: geo._mesh_topology([(a, b, c), (b, a, d), (a, b, e)]))

    def test_boolean_cavity_records_all_shells_and_tool_normal_sign(self):
        first = extrude()
        second = extrude(RegionDef(HOLE), lo=5, hi=15, identity=2)
        second.faces = [replace(f, sources=[s.prefixed(("tools", "0"), contribution="cut") for s in f.sources]) for f in second.faces]
        result = meshes(geo.boolean_geometry("DIFFERENCE", [first, second]))[0]
        self.assertEqual("7000", result["volume_mm3"])
        self.assertEqual({"outer", "cavity"}, {s["role"] for s in result["boundary_shells"]})
        cut = [s for row in result["face_sources"] for s in row if s.contribution == "cut"]
        self.assertTrue(cut)
        self.assertTrue(all(s.normal_sign == -1 and s.operation_path == ("tools", "0") for s in cut))

    def test_difference_keeps_every_component_and_explicit_empty(self):
        first = extrude()
        tool = extrude(RegionDef(((8, -1), (12, -1), (12, 21), (8, 21))), lo=-1, hi=21, identity=2)
        result = meshes(geo.boolean_geometry("DIFFERENCE", [first, tool]))
        self.assertEqual(["3200", "3200"], [r["volume_mm3"] for r in result])
        self.assertEqual("EMPTY", meshes(geo.boolean_geometry("DIFFERENCE", [first, first]))[0]["status"])

    def test_point_touching_components_remain_separate(self):
        first = extrude()
        second = extrude(axes=replace(FRAME, origin=(20, 20, 20)), identity=2)
        result = meshes(geo.boolean_geometry("UNION", [first, second]))
        self.assertEqual(2, len(result))
        self.assertEqual([8, 8], [len(r["vertices_mm"]) for r in result])

    def test_capacity_refuses_the_exact_arrangement(self):
        geometry = extrude(RegionDef(RECT, (HOLE,)))
        with self.assertRaises(EvaluationError) as caught:
            geo.build_grid([geometry], max_cells=1)
        self.assertEqual(("UNSUPPORTED", "CAPACITY"), (caught.exception.status, caught.exception.code))


if __name__ == "__main__":
    unittest.main()
