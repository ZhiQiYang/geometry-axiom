"""Behavioral graph oracles using only public, template-free kernel inputs."""
from dataclasses import replace
import importlib.util
from pathlib import Path
import sys
import unittest

if importlib.util.find_spec("geometry_kernel") is None:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "geometry-core"))

from geometry_kernel import (AssemblyChild, AssemblyDef, BoxDef, CoordinateDomain,
    DependencyEdge, DependencyKind, DifferenceDef, EvaluationError,
    EvaluationRequest, ExportRoot, ExportView, ExtrusionDef, FaceUse, InteriorDef,
    Limits, Node, NodeInput, OrientedShellDef, PlacedRegionDef, Program,
    ProgramBuilder, Provenance, ProvenanceTemplate, Quantity, QuantityType,
    RegionDef, RegionSetDef, SourceBoxDef, SourceContext, SourceDescriptor, SourceKey, SourceRef,
    SourceStatus, UnionDef, Unit, ValueType, evaluate, frame, source_closure,
    validate_program)


FRAME = frame((0, 0, 0), (1, 0, 0), (0, 1, 0))
RECT = RegionDef(((0, 0), (20, 0), (20, 20), (0, 20)))


def origins(identity=1):
    return tuple(Provenance(("fixture", identity), (i,), (identity, i)) for i in range(6))


def box_def(origin=(0, 0, 0), upper=(20, 20, 20), identity=1, domain=CoordinateDomain()):
    return BoxDef(replace(FRAME, origin=origin, domain=domain), (0, 0, 0), upper, origins(identity))


def provenance(identity=1):
    return ProvenanceTemplate(("fixture", identity), (identity,))


def region_node(p, region=RECT, axes=FRAME, identity=1):
    return p.add(PlacedRegionDef(axes, region, provenance(identity)))


def shell_node(p, *, closed=True, orientation=1):
    frames = [frame((0, 0, 0), (0, 0, 1), (0, 1, 0)),
              frame((20, 0, 0), (0, 1, 0), (0, 0, 1)),
              frame((0, 0, 0), (1, 0, 0), (0, 0, 1)),
              frame((0, 20, 0), (0, 0, 1), (1, 0, 0)),
              frame((0, 0, 0), (0, 1, 0), (1, 0, 0)),
              frame((0, 0, 20), (1, 0, 0), (0, 1, 0))]
    placed = [region_node(p, axes=f, identity=i) for i, f in enumerate(frames[:6 if closed else 5])]
    return p.add(OrientedShellDef(tuple(FaceUse(NodeInput(key, ("faces", str(i))), orientation) for i, key in enumerate(placed))))


def request(*keys, allow_partial=False, view=ExportView.GEOMETRY):
    return EvaluationRequest(tuple(ExportRoot(key, view) for key in keys), allow_partial)


def quantity_source(key, value=20, *, dependencies=(), status=SourceStatus.COMPLETE):
    return SourceDescriptor(key, ValueType.QUANTITY, SourceContext(), dependencies,
                            Quantity(QuantityType.DIMENSION, value, 1, Unit.MM) if value is not None else None,
                            status, ("full-origin", key.key))


class KernelGraphTests(unittest.TestCase):
    def assert_code(self, code, function, status="INVALID"):
        with self.assertRaises(EvaluationError) as caught:
            function()
        self.assertEqual((status, code), (caught.exception.status, caught.exception.code))
        return caught.exception

    def test_source_bound_box_recomputes_and_participates_in_boolean_closure(self):
        key = SourceKey("arbitrary-provider", ("fixed-fingerprint", "0080ff"))
        dependency = SourceKey("arbitrary-provider", ("fixed-fingerprint", "size"))
        source = SourceDescriptor(key, ValueType.BOX, SourceContext(FRAME.domain),
                                  (DependencyEdge(dependency),), box_def())
        p = ProgramBuilder((quantity_source(dependency), source))
        original_box = p.add(SourceBoxDef(SourceRef(key, ValueType.BOX)))
        cutter = p.add(box_def(origin=(10, 0, 0), upper=(20, 20, 20), identity=2))
        cut = p.add(DifferenceDef(NodeInput(original_box), (NodeInput(cutter),)))
        original = p.freeze()
        result = evaluate(original, request(cut))
        changed = replace(original, sources=(quantity_source(dependency, 30),
                          replace(source, value=box_def(upper=(30, 20, 20)))))
        expanded = evaluate(changed, request(original_box))
        self.assertEqual("4000", result.records[0].mesh["volume_mm3"])
        self.assertEqual("12000", expanded.records[0].mesh["volume_mm3"])
        self.assertEqual((dependency, key), tuple(item.key for item in expanded.sources))
        self.assertEqual((dependency, key), tuple(item.key for item in source_closure(original, (cut,))))
        self.assertEqual((20, 20, 20), original.sources[1].value.upper)

    def test_source_box_missing_wrong_type_and_domain_are_rejected(self):
        key = SourceKey("provider", (1,))
        absent = Program(nodes=(Node(0, SourceBoxDef(SourceRef(key, ValueType.BOX))),))
        self.assert_code("SOURCE_MISSING_REFERENCE", lambda: evaluate(absent, request(0)))
        wrong = Program(nodes=(Node(0, SourceBoxDef(SourceRef(key, ValueType.FRAME))),))
        self.assert_code("SOURCE_REFERENCE_TYPE", lambda: validate_program(wrong))
        self.assert_code("SOURCE_VALUE_TYPE", lambda: SourceDescriptor(key, ValueType.BOX, SourceContext(), (), FRAME))
        other_domain = CoordinateDomain(("local", 7))
        self.assert_code("SOURCE_CONTEXT", lambda: SourceDescriptor(key, ValueType.BOX,
                         SourceContext(other_domain), (), box_def()))

    def test_unavailable_source_box_obeys_root_atomic_partial_policy(self):
        key = SourceKey("provider", (1,))
        unavailable = SourceDescriptor(key, ValueType.BOX, SourceContext(), (), None,
                                       SourceStatus.INCOMPLETE)
        p = ProgramBuilder((unavailable,))
        missing = p.add(SourceBoxDef(SourceRef(key, ValueType.BOX)))
        solved = p.add(box_def())
        assembly = p.add(AssemblyDef((AssemblyChild(NodeInput(solved), "solved"),
                                      AssemblyChild(NodeInput(missing), "waiting"))))
        program = p.freeze()
        self.assert_code("SOURCE_UNAVAILABLE", lambda: evaluate(program, request(assembly)), "INCOMPLETE")
        partial = evaluate(program, request(assembly, solved, allow_partial=True))
        self.assertEqual("INCOMPLETE", partial.status)
        self.assertEqual((), partial.outcomes[0].records)
        self.assertEqual("8000", partial.outcomes[1].records[0].mesh["volume_mm3"])

    def test_source_owner_context_is_distinct_from_coordinate_domain(self):
        key = SourceKey("provider", ("frame",))
        context = SourceContext(FRAME.domain, 0, ("opaque-owner", 10))
        source = SourceDescriptor(key, ValueType.FRAME, context, (), FRAME)
        wrong_context = replace(context, owner=("opaque-owner", 11))
        p = ProgramBuilder((source,))
        placed = p.add(PlacedRegionDef(SourceRef(key, ValueType.FRAME, wrong_context), RECT, provenance()))
        self.assert_code("SOURCE_REFERENCE_TYPE", lambda: evaluate(p.freeze(), request(placed)))
        p = ProgramBuilder((source,))
        placed = p.add(PlacedRegionDef(SourceRef(key, ValueType.FRAME, context), RECT, provenance()))
        self.assertEqual("COMPLETE", evaluate(p.freeze(), request(placed)).status)
        self.assert_code("IDENTITY", lambda: SourceContext(owner=["mutable-owner"]))

    def test_source_bound_extrusion_recomputes_without_changing_identity(self):
        key = SourceKey("dimension", (7, "upper"))
        source = quantity_source(key)
        p = ProgramBuilder.from_sources((source,), snapshot_identity=("candidate", 1))
        placed = region_node(p)
        solid = p.add(ExtrusionDef(placed, 0, SourceRef(key, ValueType.QUANTITY), provenance()))
        original = p.freeze()
        first = evaluate(original, request(solid))
        second = evaluate(replace(original, sources=(replace(source, value=Quantity(QuantityType.DIMENSION, 30, 1, Unit.MM)),)), request(solid))
        self.assertEqual(["8000", "12000"], [r.records[0].mesh["volume_mm3"] for r in (first, second)])
        self.assertEqual((key,), tuple(item.key for item in second.sources))
        self.assertEqual(("candidate", 1), first.snapshot_identity)
        self.assertEqual(20, original.sources[0].value.value)

    def test_source_closure_retains_value_definition_and_ordering_edges(self):
        keys = tuple(SourceKey("source", (i,)) for i in range(5))
        deps = tuple(DependencyEdge(key, kind) for key, kind in zip(keys, DependencyKind))
        sources = tuple(quantity_source(key, None, status=SourceStatus.INCOMPLETE) for key in keys[:3])
        sources += (quantity_source(keys[3], dependencies=deps), quantity_source(keys[4]))
        p = ProgramBuilder(sources)
        placed = region_node(p)
        solid = p.add(ExtrusionDef(placed, 0, SourceRef(keys[3], ValueType.QUANTITY), provenance()))
        self.assertEqual(set(keys[:4]), {source.key for source in source_closure(p.freeze(), (solid,))})
        self.assert_code("SOURCE_UNAVAILABLE", lambda: evaluate(p.freeze(), request(solid)), "INCOMPLETE")
        accepted = replace(p.freeze(), sources=(*sources[:3], replace(sources[3], dependencies=deps[1:]), sources[4]))
        self.assertEqual("8000", evaluate(accepted, request(solid)).records[0].mesh["volume_mm3"])
        self.assertEqual(set(keys[1:4]), {source.key for source in source_closure(accepted, (solid,))})

    def test_source_unavailability_uses_strongest_dependency_status(self):
        keys = tuple(SourceKey("quantity", (i,)) for i in range(3))
        sources = (quantity_source(keys[0], None, status=SourceStatus.UNSUPPORTED),
                   quantity_source(keys[1], None, status=SourceStatus.INCOMPLETE),
                   quantity_source(keys[2], dependencies=tuple(DependencyEdge(key) for key in keys[:2])))
        p = ProgramBuilder(sources)
        solid = p.add(ExtrusionDef(region_node(p), 0, SourceRef(keys[2], ValueType.QUANTITY), provenance()))
        self.assert_code("SOURCE_UNAVAILABLE", lambda: evaluate(p.freeze(), request(solid, allow_partial=True)), "UNSUPPORTED")

    def test_source_type_context_and_identity_are_checked(self):
        key = SourceKey("frame", (1,))
        self.assert_code("SOURCE_CONTEXT", lambda: SourceDescriptor(key, ValueType.FRAME, SourceContext(CoordinateDomain(("local",))), (), FRAME))
        self.assert_code("IDENTITY", lambda: quantity_source(key).__class__(key, ValueType.QUANTITY, SourceContext(), (), Quantity(QuantityType.DIMENSION, 1, 1, Unit.MM), origin="mutable-shape"))
        source = SourceDescriptor(key, ValueType.FRAME, SourceContext(FRAME.domain), (), FRAME)
        bad = Node(0, PlacedRegionDef(SourceRef(key, ValueType.FRAME, SourceContext(CoordinateDomain(("other",)))), RECT, provenance()))
        self.assert_code("SOURCE_REFERENCE_TYPE", lambda: validate_program(Program((source,), (bad,))))

    def test_missing_and_cyclic_source_definitions_are_rejected_unselected(self):
        a, b = SourceKey("a", (1,)), SourceKey("a", (2,))
        first = quantity_source(a, dependencies=(DependencyEdge(b, DependencyKind.DEFINITION_REQUIRED),))
        self.assert_code("SOURCE_MISSING_REFERENCE", lambda: validate_program(Program((first,), ())))
        second = quantity_source(b, dependencies=(DependencyEdge(a, DependencyKind.EVALUATE_BEFORE),))
        self.assert_code("SOURCE_DEPENDENCY_CYCLE", lambda: validate_program(Program((first, second), ())))

    def test_invalid_unselected_source_cannot_be_hidden_by_partial(self):
        p = ProgramBuilder((quantity_source(SourceKey("unused", (1,)), None, status=SourceStatus.INVALID),))
        key = p.add(box_def())
        self.assert_code("SOURCE_INVALID", lambda: evaluate(p.freeze(), request(key, allow_partial=True)))

    def test_missing_unselected_node_and_wrong_operand_types_are_rejected(self):
        p = ProgramBuilder()
        good = p.add(box_def())
        p.add(UnionDef((NodeInput(good), NodeInput(99))))
        self.assert_code("MISSING_REFERENCE", lambda: evaluate(p.freeze(), request(good)))
        q = ProgramBuilder()
        placed = region_node(q)
        good = q.add(box_def())
        q.add(UnionDef((NodeInput(placed), NodeInput(good))))
        self.assert_code("OPERAND_TYPE", lambda: evaluate(q.freeze(), request(good)))

    def test_cycle_dominates_forward_reference_and_hidden_order_is_explicit(self):
        a = Node(1, AssemblyDef((AssemblyChild(NodeInput(2), 0),)))
        b = Node(2, AssemblyDef((AssemblyChild(NodeInput(1), 0),)))
        self.assert_code("DEPENDENCY_CYCLE", lambda: validate_program(Program(nodes=(a, b))))
        c = Node(2, box_def())
        self.assert_code("FORWARD_REFERENCE", lambda: validate_program(Program(nodes=(a, c))))
        validated = validate_program(Program(nodes=(a, c), declarations=(1,)))
        self.assertEqual((2, 1), validated.order)

    def test_external_geometry_dependencies_are_validated_and_select_grid(self):
        p = ProgramBuilder()
        cut = p.add(box_def(origin=(5, 5, 5), upper=(5, 5, 5), identity=2))
        large = p.add(box_def())
        normal = evaluate(p.freeze(), request(large)).records[0].mesh
        linked = evaluate(p.freeze(external_dependencies=((large, (cut,)),)), request(large)).records[0].mesh
        self.assertEqual(normal["volume_mm3"], linked["volume_mm3"])
        self.assertGreater(len(linked["triangles"]), len(normal["triangles"]))
        self.assert_code("DEPENDENCY_CYCLE", lambda: validate_program(p.freeze(external_dependencies=((large, (cut,)), (cut, (large,))))))
        self.assert_code("EXTERNAL_DEPENDENCIES", lambda: validate_program(p.freeze(external_dependencies=((large, (99,)),))))

    def test_node_depth_and_expanded_leaf_limits_are_real(self):
        p = ProgramBuilder()
        a = p.add(box_def())
        b = p.add(box_def(origin=(20, 0, 0), identity=2))
        both = p.add(AssemblyDef((AssemblyChild(NodeInput(a), "a"), AssemblyChild(NodeInput(b), "b"))))
        last = p.add(AssemblyDef((AssemblyChild(NodeInput(both), "both"),)))
        for limits in (Limits(max_nodes=3), Limits(max_depth=2), Limits(max_expanded_leaves=1)):
            self.assert_code("CAPACITY", lambda: evaluate(p.freeze(), request(last), limits=limits), "UNSUPPORTED")
        self.assertEqual(2, len(evaluate(p.freeze(), request(last)).records))

    def test_keep_preserves_internal_faces_member_order_and_operation_paths(self):
        p = ProgramBuilder()
        a = p.add(box_def())
        b = p.add(box_def(origin=(20, 0, 0), identity=2))
        together = p.add(AssemblyDef((AssemblyChild(NodeInput(b, ("inputs", "0")), "b"),
                                     AssemblyChild(NodeInput(a, ("inputs", "1")), "a"))))
        result = evaluate(p.freeze(), request(together))
        self.assertEqual([("b",), ("a",)], [item.member_path for item in result.records])
        self.assertEqual([12, 12], [len(item.mesh["triangles"]) for item in result.records])
        self.assertEqual(["8000", "8000"], [item.mesh["volume_mm3"] for item in result.records])
        for index, record in enumerate(result.records):
            self.assertTrue(all(source.operation_path == ("inputs", str(index)) for row in record.mesh["face_sources"] for source in row))

    def test_boolean_cut_keeps_origins_path_orientation_and_empty_result(self):
        p = ProgramBuilder()
        a = p.add(box_def())
        b = p.add(box_def(origin=(5, 5, 5), upper=(10, 10, 10), identity=2))
        difference = p.add(DifferenceDef(NodeInput(a, ("base",)), (NodeInput(b, ("tools", "0"), "cut"),)))
        empty = p.add(DifferenceDef(NodeInput(a), (NodeInput(a),)))
        result = evaluate(p.freeze(), request(difference, empty))
        mesh = result.records[0].mesh
        self.assertEqual("7000", mesh["volume_mm3"])
        self.assertEqual({"outer", "cavity"}, {s["role"] for s in mesh["boundary_shells"]})
        cut = [s for row in mesh["face_sources"] for s in row if s.contribution == "cut"]
        self.assertTrue(cut)
        self.assertTrue(all(s.origin_handle == ("fixture", 2) and s.operation_path == ("tools", "0") and s.normal_sign == -1 for s in cut))
        self.assertEqual("EMPTY", result.outcomes[1].status)

    def test_open_shell_has_surface_export_and_incomplete_interior(self):
        p = ProgramBuilder()
        shell = shell_node(p, closed=False)
        interior = p.add(InteriorDef(NodeInput(shell, ("shell",))))
        surface = evaluate(p.freeze(), request(interior, view=ExportView.INTERIOR_OR_BOUNDARY))
        self.assertEqual("COMPLETE", surface.status)
        self.assertEqual("open", surface.records[0].mesh["closure"])
        self.assertIsNone(surface.records[0].mesh["volume_mm3"])
        error = self.assert_code("OPEN_SHELL", lambda: evaluate(p.freeze(), request(interior, view=ExportView.INTERIOR_REQUIRED)), "INCOMPLETE")
        self.assertEqual(("shell",), error.path)

    def test_closed_shell_exports_boundary_without_inventing_volume(self):
        p = ProgramBuilder()
        shell = shell_node(p)
        interior = p.add(InteriorDef(NodeInput(shell)))
        result = evaluate(p.freeze(), EvaluationRequest((ExportRoot(shell, ExportView.BOUNDARY), ExportRoot(interior, ExportView.INTERIOR_REQUIRED))))
        self.assertEqual([None, "8000"], [record.mesh["volume_mm3"] for record in result.records])
        self.assertEqual(["closed", "closed"], [record.mesh["closure"] for record in result.records])

    def test_unselected_inward_interior_is_invalid(self):
        p = ProgramBuilder()
        good = p.add(box_def())
        p.add(InteriorDef(NodeInput(shell_node(p, orientation=-1))))
        self.assert_code("SHELL_INWARD", lambda: evaluate(p.freeze(), request(good)))

    def test_partial_is_atomic_for_a_whole_root(self):
        key = SourceKey("missing-value", (1,))
        p = ProgramBuilder((quantity_source(key, None, status=SourceStatus.INCOMPLETE),))
        good = p.add(box_def())
        bad = p.add(ExtrusionDef(region_node(p), 0, SourceRef(key, ValueType.QUANTITY), provenance()))
        group = p.add(AssemblyDef((AssemblyChild(NodeInput(good), 0), AssemblyChild(NodeInput(bad, ("children", "1")), 1))))
        result = evaluate(p.freeze(), request(group, good, allow_partial=True))
        self.assertEqual("INCOMPLETE", result.status)
        self.assertEqual((), result.outcomes[0].records)
        self.assertEqual(1, len(result.outcomes[1].records))
        self.assertEqual(0, result.diagnostics[0].root)
        self.assertEqual(("children", "1"), result.diagnostics[0].path)
        self.assert_code("SOURCE_UNAVAILABLE", lambda: evaluate(p.freeze(), request(group, good)), "INCOMPLETE")

    def test_invalid_unselected_geometry_dominates_incomplete_root(self):
        key = SourceKey("quantity", (1,))
        p = ProgramBuilder((quantity_source(key, None, status=SourceStatus.INCOMPLETE),))
        placed = region_node(p)
        incomplete = p.add(ExtrusionDef(placed, 0, SourceRef(key, ValueType.QUANTITY), provenance()))
        p.add(ExtrusionDef(placed, 10, 5, provenance(2)))
        self.assert_code("EXTRUSION_SPAN", lambda: evaluate(p.freeze(), request(incomplete, allow_partial=True)))

    def test_local_domains_do_not_add_world_arrangement_cuts(self):
        p = ProgramBuilder()
        world = p.add(box_def())
        local = p.add(box_def(origin=(3, 7, 11), upper=(5, 6, 7), identity=2, domain=CoordinateDomain(("local", 2))))
        local2 = p.add(box_def(origin=(1, 2, 3), upper=(3, 4, 5), identity=3, domain=CoordinateDomain(("local", 3))))
        before = evaluate(p.freeze(), request(world)).records[0].mesh
        result = evaluate(p.freeze(), request(world, local, local2))
        self.assertEqual(before, result.records[0].mesh)
        self.assertEqual(["8000", "210", "60"], [item.mesh["volume_mm3"] for item in result.records])
        self.assertEqual(3, len({item.domain for item in result.records}))
        self.assert_code("COORDINATE_DOMAIN", lambda: evaluate(p.freeze(), EvaluationRequest((ExportRoot(local, coordinate_domain=FRAME.domain),))))

    def test_mixed_domain_boolean_is_rejected_even_when_unselected(self):
        p = ProgramBuilder()
        a = p.add(box_def())
        b = p.add(box_def(identity=2, domain=CoordinateDomain(("local",))))
        p.add(UnionDef((NodeInput(a), NodeInput(b))))
        self.assert_code("COORDINATE_DOMAIN", lambda: evaluate(p.freeze(), request(a)))

    def test_cell_and_source_face_capacity_never_return_approximation(self):
        p = ProgramBuilder()
        a = p.add(box_def())
        b = p.add(box_def(origin=(5, 5, 5), upper=(10, 10, 10), identity=2))
        both = p.add(UnionDef((NodeInput(a), NodeInput(b))))
        for limits in (Limits(max_cells=1), Limits(max_source_faces=11)):
            self.assert_code("CAPACITY", lambda: evaluate(p.freeze(), request(both), limits=limits), "UNSUPPORTED")
        self.assertEqual("8000", evaluate(p.freeze(), request(both), limits=Limits(max_source_faces=12)).records[0].mesh["volume_mm3"])

    def test_empty_region_set_is_a_typed_empty_surface_and_solid(self):
        p = ProgramBuilder()
        surface = region_node(p, RegionSetDef(()))
        solid = p.add(ExtrusionDef(surface, 0, 20, provenance()))
        result = evaluate(p.freeze(), request(surface, solid))
        self.assertEqual("EMPTY", result.status)
        self.assertEqual([None, "0"], [item.mesh["volume_mm3"] for item in result.records])
        self.assertTrue(all(not item.mesh["triangles"] for item in result.records))

    def test_empty_boolean_retains_local_coordinate_domain(self):
        domain = CoordinateDomain(("empty-local",))
        p = ProgramBuilder()
        surface = region_node(p, RegionSetDef(()), replace(FRAME, domain=domain))
        solid = p.add(ExtrusionDef(surface, 0, 20, provenance()))
        difference = p.add(DifferenceDef(NodeInput(solid), (NodeInput(solid),)))
        result = evaluate(p.freeze(), request(difference))
        self.assertEqual("EMPTY", result.status)
        self.assertEqual(domain, result.records[0].domain)

    def test_malformed_public_collections_return_typed_errors(self):
        for code, operation in (("PROGRAM", lambda: Program(nodes=None)),
                                ("IDENTITY", lambda: Program(snapshot_identity="x")),
                                ("BOOLEAN_INPUTS", lambda: UnionDef(None)),
                                ("EVALUATION_REQUEST", lambda: EvaluationRequest(None)),
                                ("SHELL_USES", lambda: OrientedShellDef(None))):
            self.assert_code(code, operation)


if __name__ == "__main__":
    unittest.main()
