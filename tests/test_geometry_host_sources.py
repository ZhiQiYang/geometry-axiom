"""Strict transport fixtures through the actual neutral geometry consumer.

The envelopes are synthetic protocol fixtures, not native execution evidence.
No scene parser, compiler or executable is used by this suite.
"""
from base64 import b64encode
from copy import deepcopy
from hashlib import sha256
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "geometry-core"))
import modeling._host
from geometry_app.model_sources import decode_candidate
from geometry_app import model_native
from modeling import ModelError
from geometry_kernel import (DefinitionValue, DependencyKind, DifferenceDef, EvaluationError, EvaluationRequest,
    ExportRoot, ExtrusionDef, NodeInput, PlacedRegionDef, ProgramBuilder,
    ProvenanceTemplate, QuantityType, SourceBoxDef, SourceStatus, UnionDef,
    ValueType, evaluate, source_closure)


RAW_SOURCE = b"# raw fixture\nspec H 20\n"
CANONICAL_SCENE = "spec H 20\n"
EXECUTION = ("fixture-binary", "b" * 64)


def encoded(value):
    return b64encode(value).decode("ascii")


def ref(key, namespace="fixture.provider"):
    return {"namespace": namespace, "keyBase64": encoded(key)}


def context(owner=None, placement=None, axis=None):
    return {"placementId": placement, "axis": axis, "owner": owner}


def frame(owner=None):
    return {"origin": [0, 0, 0], "u": [1, 0, 0], "v": [0, 1, 0], "n": [0, 0, 1],
            "coordinateDomain": "world" if owner is None else "local", "owner": owner}


def node(key, kind, value, *, unit="length", status="ok", owner=None, placement=None, axis=None):
    return {"ref": ref(key), "descriptor": {"valueType": kind, "unit": unit,
            "context": context(owner, placement, axis)}, "status": status, "value": value}


# The H adapter names column and beam faces by local axis and side.
RECTANGULAR_FACES = ("-X", "+X", "-Y", "+Y", "-Z", "+Z")


def root(key, slot, identity=1, *, kind="fixture", member=None, name=None):
    result = {"kind": kind, "id": identity, "slot": slot, "memberId": member, "name": name, "ref": ref(key)}
    if slot == "solid.box":
        result["faces"] = [{"axis": a, "side": s,
            "legacyFeature": RECTANGULAR_FACES[2 * a + s] if kind in ("column", "beam") else f"face-{a}-{s}",
            "featureKeyBase64": encoded(key + bytes((a, s)))} for a in range(3) for s in range(2)]
    return result


def fixture():
    region = {"components": [{"outer": [[0, 0], [20, 0], [20, 20], [0, 20]],
        "holes": [[[5, 5], [5, 10], [10, 10], [10, 5]]],
        "vertexKeys": [[1, 2, 3, 4], [5, 6, 7, 8]]}]}
    nodes = [node(b"frame\0\xff", "frame", frame()), node(b"region", "region-set", region),
             node(b"height", "quantity", {"num": "20", "den": "1", "unit": "length", "quantityType": "dimension"}),
             node(b"box", "box", {"frame": frame(), "lo": [0, 0, 0], "hi": [20, 20, 20]})]
    candidate = {"id": sha256(CANONICAL_SCENE.encode()).hexdigest(), "baseRevision": 0}
    digest = sha256(RAW_SOURCE).hexdigest()
    return {"ok": True, "schema": "geometry-neutral-source-envelope/1", "candidate": candidate,
        "source": {"sha256Before": digest, "sha256After": digest},
        "legacySnapshot": {"ok": True, "schema": "geometry-base-snapshot/1", "base_scene": CANONICAL_SCENE,
            "specs": [{"name": "H", "value": 20}], "placements": [{"id": 1}],
            "solids": [{"kind": "column", "id": 1}], "parameter_fields": [],
            "unplaced_timbers": [], "dependencies": []},
        "neutralSources": {"schema": "geometry-neutral-sources/1", "candidate": deepcopy(candidate),
            "coverage": {"complete": True, "rootsComplete": True, "missingGroups": []},
            "providers": [{"namespace": "fixture.provider", "implementationFingerprint": "contract/1"}],
            "nodes": nodes, "edges": [
                {"consumer": ref(b"box"), "source": ref(b"height"), "kind": kind}
                for kind in ("value-required", "definition-required", "evaluate-before")],
            "roots": [root(b"frame\0\xff", "placement.frame", kind="placement"), root(b"region", "placement.region", kind="placement"),
                      root(b"height", "spec.value", 0, kind="spec", name="H"), root(b"box", "solid.box", kind="column")]}}


def decode(value):
    return decode_candidate(json.dumps(value), source_bytes=RAW_SOURCE, execution_identity=EXECUTION)


def native_wire(value):
    """Adapt synthetic provider refs to the native H wire, never an oracle.

    Snapshot catalogs are authored independently by each fixture. This helper
    only changes opaque transport identities, root refs and box face keys, for
    mocked process-boundary tests; face names stay as each fixture wrote them.
    """
    value = deepcopy(value)
    if value.get("schema") != "geometry-neutral-source-envelope/1":
        return value
    graph = value["neutralSources"]
    mapping = {}
    for item in graph["roots"]:
        key = ("spec:" + item["name"] if item["kind"] == "spec" else
               f'{item["kind"]}:{item["id"]}:{item["slot"]}:' +
               ("envelope:0" if item["memberId"] is None else "member:" + str(item["memberId"])))
        old = item["ref"]
        mapping[old["namespace"], old["keyBase64"]] = ref(key.encode(), "app.model-snapshot")
    def replace_refs(item):
        if type(item) is dict:
            if set(item) == {"namespace", "keyBase64"}:
                return mapping.get((item["namespace"], item["keyBase64"]), item)
            return {key: replace_refs(part) for key, part in item.items()}
        if type(item) is list:
            return [replace_refs(part) for part in item]
        return item
    value["neutralSources"] = replace_refs(graph)
    value["neutralSources"]["providers"].append({"namespace": "app.model-snapshot",
        "implementationFingerprint": "geo261-model-snapshot/1"})
    for item in value["neutralSources"]["roots"]:
        for face in item.get("faces", ()):
            face["featureKeyBase64"] = encoded(f'{item["kind"]}:{item["id"]}:face:{face["legacyFeature"]}'.encode())
    return value


def definition_closure_fixture():
    value = fixture()
    graph = value["neutralSources"]
    graph["nodes"].extend((
        node(b"definition-only", "definition", None, unit="scalar", status="unevaluated"),
        node(b"ordering-only", "quantity", None, status="unevaluated", placement=3, axis=1)))
    graph["edges"].extend((
        {"consumer": ref(b"box"), "source": ref(b"definition-only"), "kind": "definition-required"},
        {"consumer": ref(b"box"), "source": ref(b"ordering-only"), "kind": "evaluate-before"}))
    return value


class NativeSourceTests(unittest.TestCase):
    def rejected(self, value, code="BASE_SOURCE_PROTOCOL"):
        with self.assertRaises(ModelError) as error:
            decode(value)
        self.assertEqual(("UNSUPPORTED", code), (error.exception.status, error.exception.code))
        return error.exception

    def test_decoded_sources_drive_the_real_kernel_with_hole_and_box(self):
        candidate = decode(fixture())
        roots = {item.slot: item.source for item in candidate.roots}
        builder = ProgramBuilder(candidate.sources, snapshot_identity=candidate.snapshot_identity)
        provenance = ProvenanceTemplate(("transport-fixture",), (1,))
        placed = builder.add(PlacedRegionDef(roots["placement.frame"], roots["placement.region"], provenance))
        extrusion = builder.add(ExtrusionDef(placed, 0, roots["spec.value"], provenance))
        box = builder.add(SourceBoxDef(roots["solid.box"]))
        difference = builder.add(DifferenceDef(NodeInput(box), (NodeInput(extrusion),)))
        result = evaluate(builder.freeze(), EvaluationRequest((ExportRoot(extrusion), ExportRoot(difference))))
        self.assertEqual(["7500", "500"], [item.mesh["volume_mm3"] for item in result.records])
        self.assertEqual(candidate.snapshot_identity, result.snapshot_identity)
        self.assertEqual(3, len(candidate.sources[-1].dependencies))
        self.assertEqual(tuple(face.feature_key.hex() for face in candidate.roots[-1].faces),
                         tuple(origin.feature_key[1] for origin in candidate.sources[-1].value.face_origins))
        self.assertEqual(tuple(range(1, 9)), candidate.sources[1].value.components[0].vertex_keys)
        caller_copy = candidate.legacy_snapshot
        caller_copy["base_scene"] = "corrupted caller copy"
        self.assertEqual(CANONICAL_SCENE, candidate.legacy_snapshot["base_scene"])

    def test_opaque_bytes_and_provider_fingerprints_are_not_collapsed(self):
        original = decode(fixture())
        self.assertEqual("6672616d6500ff", original.sources[0].key.key[1])
        changed = fixture()
        changed["neutralSources"]["providers"][0]["implementationFingerprint"] = "contract/2"
        self.assertNotEqual(original.sources[0].key, decode(changed).sources[0].key)
        changed = fixture()
        extra = deepcopy(changed["neutralSources"]["nodes"][0])
        extra["ref"] = ref(b"frame\0\xfe")
        changed["neutralSources"]["nodes"].append(extra)
        sources = decode(changed).sources
        self.assertEqual(sources[0].value, sources[-1].value)
        self.assertNotEqual(sources[0].key, sources[-1].key)

    def test_quantity_count_ratio_position_and_feature_keep_exact_type(self):
        value = fixture()
        added = [node(b"count", "quantity", {"num": "3", "den": "1", "unit": "scalar", "quantityType": "count"}, unit="scalar"),
            node(b"ratio", "quantity", {"num": "3", "den": "7", "unit": "scalar", "quantityType": "ratio"}, unit="scalar"),
            node(b"position", "axis-position", {"coordinate": 7, "context": context(placement=3, axis=1)}, placement=3, axis=1),
            node(b"feature", "feature", {"keyBase64": encoded(b"edge\0\xfe"), "segment": [[0, 0, 0], [20, 0, 0]]})]
        value["neutralSources"]["nodes"].extend(added)
        sources = decode(value).sources[-4:]
        self.assertEqual([QuantityType.COUNT, QuantityType.RATIO, QuantityType.AXIS_POSITION], [s.value.value_type for s in sources[:3]])
        self.assertEqual((3, 7), (sources[1].value.numerator, sources[1].value.denominator))
        self.assertEqual(("6564676500fe", (0, 0, 0), (20, 0, 0)), sources[-1].value)
        for patch in ({"num": "1.0"}, {"num": "-0"}, {"den": "0"}, {"quantityType": "scalar"}, {"quantityType": []}, {"unit": "scalar"}):
            changed = fixture()
            changed["neutralSources"]["nodes"][2]["value"].update(patch)
            self.rejected(changed)

    def test_local_owners_define_distinct_domains_even_with_equal_geometry(self):
        value = fixture()
        for identity in (1, 2):
            owner = ref(f"owner:{identity}".encode())
            key = f"local:{identity}".encode()
            value["neutralSources"]["nodes"].append(node(key, "box", {"frame": frame(owner), "lo": [0, 0, 0], "hi": [20, 20, 20]}, owner=owner))
            value["neutralSources"]["roots"].append(root(key, "solid.box", identity+10))
            value["legacySnapshot"]["solids"].append({"kind": "fixture", "id": identity+10})
        candidate = decode(value)
        self.assertNotEqual(candidate.sources[-1].context.domain, candidate.sources[-2].context.domain)
        builder = ProgramBuilder(candidate.sources)
        a, b = (builder.add(SourceBoxDef(r.source)) for r in candidate.roots[-2:])
        union = builder.add(UnionDef((NodeInput(a), NodeInput(b))))
        with self.assertRaises(EvaluationError) as error:
            evaluate(builder.freeze(), EvaluationRequest((ExportRoot(union),)))
        self.assertEqual("COORDINATE_DOMAIN", error.exception.code)
        value["neutralSources"]["nodes"][-1]["value"]["frame"]["owner"] = ref(b"other-owner")
        self.rejected(value)

    def test_incomplete_coverage_is_always_rejected(self):
        for patch in ({"complete": False}, {"complete": 1}, {"rootsComplete": False}, {"missingGroups": ["parameter-ast"]}):
            value = fixture()
            value["neutralSources"]["coverage"].update(patch)
            self.rejected(value, "BASE_SOURCE_COVERAGE")

    def test_input_and_candidate_identity_are_bound_together(self):
        for field in ("sha256Before", "sha256After"):
            value = fixture()
            value["source"][field] = "0" * 64
            self.rejected(value, "BASE_RUNTIME_CHANGED")
        value = fixture()
        value["candidate"]["id"] = "0" * 64
        value["neutralSources"]["candidate"]["id"] = "0" * 64
        self.rejected(value)
        value = fixture()
        value["neutralSources"]["candidate"]["baseRevision"] = 1
        self.rejected(value)
        value = fixture()
        value["neutralSources"]["candidate"]["baseRevision"] = False
        self.rejected(value)
        value = fixture()
        value["legacySnapshot"]["specs"] = None
        self.rejected(value)

    def test_duplicate_keys_and_float_json_cannot_enter_transport(self):
        raw = json.dumps(fixture())
        for malformed in (raw.replace('"ok": true', '"ok": true, "ok": true', 1),
                          raw.replace('"baseRevision": 0', '"baseRevision": 0.0', 1)):
            with self.assertRaises(ModelError) as error:
                decode_candidate(malformed, source_bytes=RAW_SOURCE, execution_identity=EXECUTION)
            self.assertEqual("BASE_SOURCE_PROTOCOL", error.exception.code)

    def test_duplicate_and_outside_graph_identities_are_rejected(self):
        for collection in ("providers", "nodes", "edges", "roots"):
            value = fixture()
            value["neutralSources"][collection].append(deepcopy(value["neutralSources"][collection][0]))
            self.rejected(value)
        value = fixture()
        value["neutralSources"]["edges"][0]["source"] = ref(b"not-defined")
        self.rejected(value)
        value = fixture()
        value["neutralSources"]["nodes"][0]["ref"]["namespace"] = "not-declared"
        self.rejected(value)
        value = fixture()
        value["neutralSources"]["roots"][0]["id"] = True
        self.rejected(value)

    def test_unused_source_cycles_are_not_hidden_by_root_selection(self):
        value = fixture()
        value["neutralSources"]["edges"].append({"consumer": ref(b"height"), "source": ref(b"box"), "kind": "definition-required"})
        error = self.rejected(value)
        self.assertIn("SOURCE_DEPENDENCY_CYCLE", error.message)

    def test_missing_source_value_remains_a_typed_incomplete_root(self):
        value = fixture()
        value["neutralSources"]["nodes"][-1].update(status="missing", value=None)
        candidate = decode(value)
        self.assertEqual(SourceStatus.INCOMPLETE, candidate.sources[-1].status)
        builder = ProgramBuilder(candidate.sources)
        box = builder.add(SourceBoxDef(candidate.roots[-1].source))
        result = evaluate(builder.freeze(), EvaluationRequest((ExportRoot(box),), True))
        self.assertEqual("INCOMPLETE", result.status)
        self.assertEqual((), result.records)
        value["neutralSources"]["nodes"][-1]["status"] = "ok"
        self.rejected(value)

    def test_unevaluated_definition_and_ordering_edges_keep_complete_root(self):
        candidate = decode(definition_closure_fixture())
        pending = candidate.sources[-2:]
        self.assertEqual([SourceStatus.INCOMPLETE, SourceStatus.INCOMPLETE], [source.status for source in pending])
        self.assertEqual([ValueType.DEFINITION, ValueType.QUANTITY], [source.value_type for source in pending])
        self.assertEqual([None, None], [source.value for source in pending])
        self.assertEqual(1, pending[-1].context.axis)
        self.assertEqual(("native-context", 3, ()), pending[-1].context.owner)
        box_source = candidate.sources[3]
        self.assertEqual((DependencyKind.DEFINITION_REQUIRED, DependencyKind.EVALUATE_BEFORE),
                         tuple(edge.kind for edge in box_source.dependencies[-2:]))
        builder = ProgramBuilder(candidate.sources)
        box = builder.add(SourceBoxDef(candidate.roots[-1].source))
        result = evaluate(builder.freeze(), EvaluationRequest((ExportRoot(box),)))
        self.assertEqual("COMPLETE", result.status)
        self.assertEqual("8000", result.records[0].mesh["volume_mm3"])
        closure = source_closure(builder.freeze(), (box,))
        self.assertTrue({source.key for source in pending} <= {source.key for source in closure})
        self.assertTrue(all(source.value is None for source in closure if source.key in {entry.key for entry in pending}))

    def test_unevaluated_value_required_dependencies_are_incomplete(self):
        for index in (-2, -1):
            with self.subTest(edge=index):
                value = definition_closure_fixture()
                value["neutralSources"]["edges"][index]["kind"] = "value-required"
                candidate = decode(value)
                builder = ProgramBuilder(candidate.sources)
                box = builder.add(SourceBoxDef(candidate.roots[-1].source))
                with self.assertRaises(EvaluationError) as error:
                    evaluate(builder.freeze(), EvaluationRequest((ExportRoot(box),)))
                self.assertEqual(("INCOMPLETE", "SOURCE_UNAVAILABLE"), (error.exception.status, error.exception.code))
                self.assertEqual(candidate.sources[index].key, error.exception.missing)
                partial = evaluate(builder.freeze(), EvaluationRequest((ExportRoot(box),), True))
                self.assertEqual(("INCOMPLETE", ()), (partial.status, partial.records))

    def test_unevaluated_status_cannot_carry_a_value(self):
        value = fixture()
        value["neutralSources"]["nodes"][2]["status"] = "unevaluated"
        error = self.rejected(value)
        self.assertEqual("Native source status and value availability disagree.", error.message)

    def test_ok_status_cannot_hide_a_missing_value(self):
        value = fixture()
        value["neutralSources"]["nodes"][2]["value"] = None
        error = self.rejected(value)
        self.assertEqual("Native source status and value availability disagree.", error.message)

    def test_failure_statuses_keep_their_existing_outcomes(self):
        for native_status, expected in (("failed", SourceStatus.INCOMPLETE), ("missing", SourceStatus.INCOMPLETE),
                                       ("cycle", SourceStatus.INVALID), ("invalid", SourceStatus.INVALID),
                                       ("memory", SourceStatus.UNSUPPORTED)):
            with self.subTest(native_status=native_status):
                value = fixture()
                value["neutralSources"]["nodes"][2].update(status=native_status, value=None)
                candidate = decode(value)
                self.assertEqual(expected, candidate.sources[2].status)
                builder = ProgramBuilder(candidate.sources)
                box = builder.add(SourceBoxDef(candidate.roots[-1].source))
                with self.assertRaises(EvaluationError) as error:
                    evaluate(builder.freeze(), EvaluationRequest((ExportRoot(box),)))
                self.assertEqual(expected.value, error.exception.status)
                self.assertEqual("SOURCE_INVALID" if expected == SourceStatus.INVALID else "SOURCE_UNAVAILABLE", error.exception.code)

    def test_unevaluated_descriptors_require_complete_valid_types_and_contexts(self):
        for mutation in ("missing-type", "unknown-type", "wrong-unit", "incomplete-context", "invalid-axis"):
            value = definition_closure_fixture()
            descriptor = value["neutralSources"]["nodes"][-2]["descriptor"]
            if mutation == "missing-type":
                descriptor.pop("valueType")
            elif mutation == "unknown-type":
                descriptor["valueType"] = "undefined"
            elif mutation == "wrong-unit":
                descriptor["unit"] = "length"
            elif mutation == "incomplete-context":
                descriptor["context"].pop("owner")
            else:
                descriptor["context"]["axis"] = True
            with self.subTest(mutation=mutation):
                self.rejected(value)

    def test_definition_sources_keep_full_bytes_schema_and_empty_content(self):
        value = fixture()
        expected = [("unrelated-provider/1", b"\x00\xfffull\ncontent\x00"), (" ", b"")]
        for index, (schema, content) in enumerate(expected):
            key = ("definition:" + str(index)).encode()
            value["neutralSources"]["nodes"].append(node(key, "definition",
                {"schema": schema, "contentBase64": encoded(content)}, unit="scalar"))
            value["neutralSources"]["edges"].append({"consumer": ref(b"box"), "source": ref(key), "kind": "definition-required"})
        candidate = decode(value)
        definitions = candidate.sources[-2:]
        self.assertTrue(all(source.value_type == ValueType.DEFINITION and isinstance(source.value, DefinitionValue)
                            for source in definitions))
        self.assertEqual(expected, [(source.value.schema, source.value.content) for source in definitions])
        builder = ProgramBuilder(candidate.sources)
        box = builder.add(SourceBoxDef(candidate.roots[-1].source))
        result = evaluate(builder.freeze(), EvaluationRequest((ExportRoot(box),)))
        self.assertEqual("8000", result.records[0].mesh["volume_mm3"])
        self.assertTrue({source.key for source in definitions} <= {source.key for source in result.sources})

    def test_definition_sources_reject_malformed_payloads_and_units(self):
        payloads = ({"schema": "", "contentBase64": ""}, {"schema": 7, "contentBase64": ""},
                    {"schema": "x\0y", "contentBase64": ""}, {"schema": "x"},
                    {"schema": "x", "contentBase64": "", "extra": 0},
                    {"schema": "x", "contentBase64": None}, {"schema": "x", "contentBase64": "!"},
                    {"schema": "x", "contentBase64": "Zg"}, {"schema": "x", "contentBase64": "Zg==\n"})
        for payload in payloads:
            value = fixture()
            value["neutralSources"]["nodes"].append(node(b"definition", "definition", payload, unit="scalar"))
            with self.subTest(payload=payload):
                self.rejected(value)
        value = fixture()
        value["neutralSources"]["nodes"].append(node(b"definition", "definition", {"schema": "x", "contentBase64": ""}))
        self.rejected(value)

    def test_definition_content_rejects_noncanonical_base64(self):
        value = fixture()
        # Standard decoding accepts these nonzero pad bits, but the unique
        # encoding of b"f" is Zg==. Identity must not accept alternate spellings.
        value["neutralSources"]["nodes"].append(node(b"definition", "definition",
            {"schema": "x", "contentBase64": "Zh=="}, unit="scalar"))
        error = self.rejected(value)
        self.assertEqual("Native definition content must use canonical Base64.", error.message)

    def test_complete_loops_and_six_face_provenance_are_required(self):
        value = fixture()
        value["neutralSources"]["nodes"][1]["value"]["components"][0]["vertexKeys"] = [[1, 2, 3], [4, 5, 6, 7, 8]]
        self.rejected(value)
        value = fixture()
        value["neutralSources"]["nodes"][1]["value"]["components"][0]["holes"] = [[[25, 25], [25, 30], [30, 30], [30, 25]]]
        self.rejected(value)
        for mutation in ("missing", "duplicate-side", "duplicate-key"):
            value = fixture()
            faces = value["neutralSources"]["roots"][-1]["faces"]
            if mutation == "missing":
                faces.pop()
            elif mutation == "duplicate-side":
                faces[-1].update(axis=0, side=0)
            else:
                faces[-1]["featureKeyBase64"] = faces[0]["featureKeyBase64"]
            self.rejected(value)

    def test_noncanonical_opaque_keys_and_wrong_root_types_are_rejected(self):
        for malformed in ("", "!@#", "YWJj====", "Zg"):
            value = fixture()
            value["neutralSources"]["nodes"][0]["ref"]["keyBase64"] = malformed
            self.rejected(value)
        value = fixture()
        value["neutralSources"]["roots"][0]["ref"] = ref(b"height")
        self.rejected(value)
        for malformed in ([], None, "unknown"):
            value = fixture()
            value["neutralSources"]["nodes"][0]["descriptor"]["valueType"] = malformed
            self.rejected(value)


class NativeRootCatalogTests(unittest.TestCase):
    def rejected(self, value, code="BASE_SOURCE_BINDING"):
        with self.assertRaises(ModelError) as error:
            decode(value)
        self.assertEqual(("UNSUPPORTED", code, "I32"),
            (error.exception.status, error.exception.code, error.exception.clause))

    def test_missing_extra_and_equal_count_wrong_roots_fail_with_true_flags(self):
        original = fixture()
        expected = {("placement", 1, "placement.frame", None, None),
                    ("placement", 1, "placement.region", None, None),
                    ("spec", 0, "spec.value", None, "H"),
                    ("column", 1, "solid.box", None, None)}
        self.assertEqual(expected, {item.association for item in decode(original).roots})
        for index in range(4):
            with self.subTest(missing=index):
                changed = deepcopy(original)
                del changed["neutralSources"]["roots"][index]
                self.rejected(changed)
        for mode in ("extra", "wrong-id", "wrong-name"):
            with self.subTest(mode=mode):
                changed = deepcopy(original)
                roots = changed["neutralSources"]["roots"]
                if mode == "extra":
                    roots.append({**roots[-1], "id": 999})
                elif mode == "wrong-id":
                    roots[0]["id"] = 999
                else:
                    roots[2]["name"] = "not-H"
                self.assertEqual({"complete": True, "rootsComplete": True, "missingGroups": []},
                                 changed["neutralSources"]["coverage"])
                self.rejected(changed)
        reordered = deepcopy(original)
        reordered["neutralSources"]["roots"].reverse()
        self.assertEqual(expected, {item.association for item in decode(reordered).roots})

    def test_parameter_catalog_is_independent_of_optional_root_selection(self):
        original = fixture()
        original["legacySnapshot"]["required_capabilities"] = ["parameters/1"]
        original["legacySnapshot"]["parameter_fields"] = [
            {"parameterId": 8, "fieldId": 3, "name": "ratio_field"}]
        graph = original["neutralSources"]
        graph["nodes"].append(node(b"parameter\0field", "quantity",
            {"num": "3", "den": "7", "unit": "scalar", "quantityType": "ratio"}, unit="scalar"))
        graph["roots"].append(root(b"parameter\0field", "parameter.value", 8,
            kind="parameter", member=3, name="ratio_field"))
        self.assertEqual(("parameter", 8, "parameter.value", 3, "ratio_field"), decode(original).roots[-1].association)
        for mode in ("missing-root", "extra-root", "wrong-name", "missing-catalog", "duplicate-catalog"):
            with self.subTest(mode=mode):
                changed = deepcopy(original)
                roots = changed["neutralSources"]["roots"]
                code = "BASE_SOURCE_BINDING"
                if mode == "missing-root":
                    roots.pop()
                elif mode == "extra-root":
                    roots.append({**roots[-1], "memberId": 99})
                elif mode == "wrong-name":
                    roots[-1]["name"] = "other_name"
                elif mode == "missing-catalog":
                    del changed["legacySnapshot"]["parameter_fields"]
                    code = "BASE_SOURCE_PROTOCOL"
                else:
                    changed["legacySnapshot"]["parameter_fields"].append(
                        {"parameterId": 8, "fieldId": 3, "name": "another_name"})
                    code = "BASE_SOURCE_PROTOCOL"
                self.rejected(changed, code)

    def test_duplicate_snapshot_identity_is_not_hidden_by_set_conversion(self):
        changed = fixture()
        changed["legacySnapshot"]["placements"].append({"id": 1})
        self.rejected(changed, "BASE_SOURCE_PROTOCOL")

    def test_public_native_loader_rejects_equal_value_quantity_ref_swaps(self):
        value = fixture()
        value["legacySnapshot"]["specs"].append({"name": "L", "value": 20})
        graph = value["neutralSources"]
        graph["nodes"].append(node(b"other-height", "quantity",
            {"num": "20", "den": "1", "unit": "length", "quantityType": "dimension"}))
        graph["roots"].append(root(b"other-height", "spec.value", 0, kind="spec", name="L"))
        original = native_wire(value)
        actual = [item["ref"]["keyBase64"] for item in original["neutralSources"]["roots"] if item["kind"] == "spec"]
        self.assertEqual([encoded(b"spec:H"), encoded(b"spec:L")], actual)
        def invoke(wire):
            def process(command, **options):
                self.assertEqual(RAW_SOURCE, Path(command[-1]).read_bytes())
                return subprocess.CompletedProcess(command, 0, json.dumps(wire).encode(), b"")
            with mock.patch.object(model_native, "_execution_identity", return_value=EXECUTION), \
                 mock.patch.object(model_native.subprocess, "run", side_effect=process) as run:
                result = model_native.load_candidate(RAW_SOURCE.decode(), executable="fixture-not-executed")
            self.assertEqual(1, run.call_count)
            return result
        self.assertEqual(5, len(invoke(original).roots))
        changed = deepcopy(original)
        specs = [item for item in changed["neutralSources"]["roots"] if item["kind"] == "spec"]
        specs[0]["ref"], specs[1]["ref"] = specs[1]["ref"], specs[0]["ref"]
        self.assertEqual({root.association for root in decode(original).roots},
                         {root.association for root in decode(changed).roots})
        with self.assertRaises(ModelError) as error:
            invoke(changed)
        self.assertEqual(("UNSUPPORTED", "BASE_SOURCE_BINDING", "I32"),
                         (error.exception.status, error.exception.code, error.exception.clause))
        for mode in ("fingerprint", "provider", "incomplete"):
            with self.subTest(mode=mode):
                changed = deepcopy(original)
                if mode == "fingerprint":
                    changed["neutralSources"]["providers"][-1]["implementationFingerprint"] = "geo261-model-snapshot/999"
                elif mode == "provider":
                    # Keep a declared, consistently renamed provider so only
                    # the native adapter binding, not basic shape, rejects it.
                    def rename(item):
                        if type(item) is dict:
                            return {key: ("alternate.provider" if key == "namespace" and part == "app.model-snapshot" else rename(part))
                                    for key, part in item.items()}
                        return [rename(part) for part in item] if type(item) is list else item
                    changed["neutralSources"] = rename(changed["neutralSources"])
                else:
                    changed["neutralSources"]["nodes"][-1].update(status="missing", value=None)
                self.assertEqual(5, len(decode(changed).roots))
                with self.assertRaises(ModelError) as error:
                    invoke(changed)
                self.assertEqual("BASE_SOURCE_BINDING", error.exception.code)

    def native_load(self, wire):
        def process(command, **options):
            self.assertEqual(RAW_SOURCE, Path(command[-1]).read_bytes())
            return subprocess.CompletedProcess(command, 0, json.dumps(wire).encode(), b"")
        with mock.patch.object(model_native, "_execution_identity", return_value=EXECUTION), \
             mock.patch.object(model_native.subprocess, "run", side_effect=process) as run, \
             mock.patch.object(model_native, "load_base", side_effect=AssertionError("root-catalog-fallback")):
            try:
                return model_native.load_candidate(RAW_SOURCE.decode(), executable="fixture-not-executed")
            finally:
                self.assertEqual(1, run.call_count)

    def native_rejected(self, wire, code="BASE_SOURCE_BINDING"):
        with self.assertRaises(ModelError) as error:
            self.native_load(wire)
        self.assertEqual(("UNSUPPORTED", code, "I32"),
            (error.exception.status, error.exception.code, error.exception.clause))
        return error.exception

    @staticmethod
    def boxes():
        """Two columns and a timber, each box authored with its own face catalog."""
        value = fixture()
        timber = ("A0", "A1", "B0", "B1", "START", "END")
        value["legacySnapshot"]["solids"] += [{"kind": "column", "id": 2},
            {"kind": "timber", "id": 3, "faces": [{"feature": name} for name in timber]}]
        graph = value["neutralSources"]
        for key, size in ((b"box2", 10), (b"timber3", 30)):
            graph["nodes"].append(node(key, "box", {"frame": frame(), "lo": [0, 0, 0], "hi": [size, size, size]}))
        graph["roots"].append(root(b"box2", "solid.box", 2, kind="column"))
        member = root(b"timber3", "solid.box", 3, kind="timber")
        # Wood faces are not in X/Y/Z order: names follow the template's sides.
        for face, name in zip(member["faces"], ("START", "END", "B0", "B1", "A0", "A1")):
            face["legacyFeature"] = name
        graph["roots"].append(member)
        return native_wire(value)

    def by_box(self, wire):
        return {(item["kind"], item["id"]): item for item in wire["neutralSources"]["roots"] if item["slot"] == "solid.box"}

    def test_native_loader_rejects_box_faces_swapped_between_two_columns(self):
        wire = self.boxes()
        self.assertEqual(6, len(self.native_load(wire).roots))
        changed = deepcopy(wire)
        boxes = self.by_box(changed)
        boxes["column", 1]["faces"], boxes["column", 2]["faces"] = boxes["column", 2]["faces"], boxes["column", 1]["faces"]
        # Every box still has six distinct sides, keys and the same names, so
        # generic opaque decoding admits it; only the face binding can refuse.
        self.assertEqual(6, len(decode(changed).roots))
        error = self.native_rejected(changed)
        self.assertEqual("Native box face identity disagrees with its adapter root.", error.message)

    def test_native_loader_rejects_legacy_features_swapped_within_one_box(self):
        wire = self.boxes()
        self.assertEqual(6, len(self.native_load(wire).roots))
        for box, mode in ((("column", 1), "names"), (("column", 1), "names-and-keys"),
                          (("timber", 3), "names"), (("timber", 3), "renamed")):
            with self.subTest(box=box, mode=mode):
                changed = deepcopy(wire)
                faces = self.by_box(changed)[box]["faces"]
                if mode == "renamed":
                    # A consistent name and key outside the snapshot's own catalog.
                    faces[0]["legacyFeature"] = "SIDE"
                    faces[0]["featureKeyBase64"] = encoded(f"{box[0]}:{box[1]}:face:SIDE".encode())
                else:
                    moved = ("legacyFeature", "featureKeyBase64") if mode == "names-and-keys" else ("legacyFeature",)
                    for field in moved:
                        faces[0][field], faces[1][field] = faces[1][field], faces[0][field]
                self.assertEqual(6, len(decode(changed).roots))
                error = self.native_rejected(changed)
                self.assertEqual("Native box face identity disagrees with its adapter root.", error.message)

    def test_native_loader_rejects_an_appended_identical_root(self):
        wire = native_wire(fixture())
        self.assertEqual(4, len(self.native_load(wire).roots))
        for index in range(4):
            with self.subTest(root=index):
                changed = deepcopy(wire)
                changed["neutralSources"]["roots"].append(deepcopy(changed["neutralSources"]["roots"][index]))
                error = self.native_rejected(changed, "BASE_SOURCE_PROTOCOL")
                self.assertEqual("Native root associations must be unique.", error.message)


class NativeSourceGuardControls(unittest.TestCase):
    def test_removed_transport_guards_fail_the_same_real_consumers(self):
        with tempfile.TemporaryDirectory(prefix="geo261-source-guards-") as directory:
            copied = Path(directory)
            for package in ("geometry-core/geometry_kernel", "geometry-core/modeling",
                            "geometry-app/geometry_app",
                            "geometry-templates/woodworking/geometry_woodworking"):
                shutil.copytree(ROOT / package, copied / package,
                                ignore=shutil.ignore_patterns("__pycache__"))
            (copied / "tests").mkdir()
            (copied / "tests/__init__.py").write_text("", encoding="utf-8")
            shutil.copyfile(__file__, copied / "tests/test_geometry_host_sources.py")
            source = copied / "geometry-app/geometry_app/model_sources.py"
            original = source.read_text(encoding="utf-8")
            runner = "import sys,unittest;sys.path.insert(0,sys.argv.pop(1));unittest.main(module=None)"

            def execute(name):
                return subprocess.run([sys.executable, "-I", "-B", "-c", runner,
                    str(copied), "tests.test_geometry_host_sources." + name], cwd=copied,
                    capture_output=True, text=True, timeout=30)

            baseline = execute("NativeSourceTests")
            self.assertEqual(0, baseline.returncode, baseline.stdout + baseline.stderr)
            self.assertIn("Ran 21 tests", baseline.stderr)
            mutants = (
                ('if coverage["complete"] is not True or coverage["rootsComplete"] is not True or _array(coverage["missingGroups"]):',
                 'if False:', "test_incomplete_coverage_is_always_rejected"),
                ('if sha256(snapshot["base_scene"].encode("utf-8")).hexdigest() != identity:',
                 'if False:', "test_input_and_candidate_identity_are_bound_together"),
                ('dependencies[consumer].append(DependencyEdge(source, relation))', 'pass',
                 "test_unused_source_cycles_are_not_hidden_by_root_selection"),
                ('if (node["status"] == "ok") != (node["value"] is not None):', 'if False:',
                 "test_unevaluated_status_cannot_carry_a_value"),
                ('if (node["status"] == "ok") != (node["value"] is not None):', 'if False:',
                 "test_ok_status_cannot_hide_a_missing_value"),
                ('"unevaluated": SourceStatus.INCOMPLETE', '"unevaluated": SourceStatus.INVALID',
                 "test_unevaluated_definition_and_ordering_edges_keep_complete_root"),
                ('if b64encode(result).decode("ascii") != value:', 'if False:',
                 "test_definition_content_rejects_noncanonical_base64"),
                ('return DefinitionValue(_text(value["schema"]), _content_bytes(value["contentBase64"]))',
                 'return DefinitionValue(_text(value["schema"]), b"")',
                 "test_definition_sources_keep_full_bytes_schema_and_empty_content"),
            )
            for before, after, case in mutants:
                with self.subTest(case=case):
                    self.assertEqual(1, original.count(before))
                    source.write_text(original.replace(before, after), encoding="utf-8")
                    result = execute("NativeSourceTests." + case)
                    details = result.stdout + result.stderr
                    self.assertEqual(1, result.returncode, details)
                    self.assertIn("Ran 1 test", details)
                    self.assertIn("FAILED (failures=1)", details)
                    self.assertNotIn("ImportError", details)
                    self.assertNotIn("SyntaxError", details)
            source.write_text(original, encoding="utf-8")
            restored = execute("NativeSourceTests")
            self.assertEqual(0, restored.returncode, restored.stdout + restored.stderr)


class NativeCandidateTransportTests(unittest.TestCase):
    def invoke(self, value, *, command_builder=None, returncode=0, identities=None, source=RAW_SOURCE):
        calls = []
        value = native_wire(value)

        def process(command, **options):
            calls.append(command)
            self.assertEqual(source, Path(command[-1]).read_bytes())
            return subprocess.CompletedProcess(command, returncode, json.dumps(value).encode(), b"")

        with mock.patch.object(model_native, "_execution_identity", side_effect=identities or [EXECUTION, EXECUTION]) as pin:
            with mock.patch.object(model_native.subprocess, "run", side_effect=process):
                result = model_native.load_candidate(source.decode(), executable="fixture-not-executed",
                                                     command_builder=command_builder)
        self.assertEqual(2, pin.call_count)
        self.assertEqual(1, len(calls))
        return result, calls[0]

    def snapshot_rejected(self, value, source=RAW_SOURCE):
        with self.assertRaises(ModelError) as error:
            self.invoke(value, source=source)
        failure = error.exception
        return failure.status, failure.code, failure.clause, failure.message

    def test_missing_profile_runs_keep_the_section_profile_diagnostic(self):
        # The root catalog also reads profile_runs; the snapshot contract that
        # predates it must still decide this input, with its own clause.
        scene = "requires section-profile/1\n" + CANONICAL_SCENE
        digest = sha256(scene.encode()).hexdigest()
        value = fixture()
        value["candidate"]["id"] = value["neutralSources"]["candidate"]["id"] = digest
        value["source"] = {"sha256Before": digest, "sha256After": digest}
        value["legacySnapshot"].update(base_scene=scene, required_capabilities=["section-profile/1"], profile_runs=[])
        candidate, _ = self.invoke(value, source=scene.encode())
        self.assertEqual([], candidate.legacy_snapshot["profile_runs"])
        del value["legacySnapshot"]["profile_runs"]
        self.assertEqual(("UNSUPPORTED", "BASE_PROTOCOL", "I51", "C scene adapter omitted section-profile definitions."),
                         self.snapshot_rejected(value, scene.encode()))

    def test_non_array_capabilities_keep_the_snapshot_capability_diagnostic(self):
        value = fixture()
        value["legacySnapshot"]["required_capabilities"] = []
        candidate, _ = self.invoke(value)
        self.assertEqual([], candidate.legacy_snapshot["required_capabilities"])
        value["legacySnapshot"]["required_capabilities"] = "parameters/1"
        self.assertEqual(("UNSUPPORTED", "BASE_PROTOCOL", "I32", "C scene adapter returned unsupported source capabilities."),
                         self.snapshot_rejected(value))

    def test_one_pinned_invocation_returns_a_real_source_bound_geometry(self):
        candidate, command = self.invoke(fixture())
        self.assertEqual(["fixture-not-executed", "--neutral-sources"], command[:-1])
        builder = ProgramBuilder(candidate.sources, snapshot_identity=candidate.snapshot_identity)
        box = builder.add(SourceBoxDef(candidate.roots[-1].source))
        result = evaluate(builder.freeze(), EvaluationRequest((ExportRoot(box),)))
        self.assertEqual("8000", result.records[0].mesh["volume_mm3"])
        self.assertEqual(EXECUTION, candidate.execution_identity)

    def test_old_or_incomplete_adapter_never_falls_back(self):
        incomplete = fixture()
        incomplete["neutralSources"]["coverage"]["complete"] = False
        for value, code in ((fixture()["legacySnapshot"], "BASE_SOURCE_PROTOCOL"),
                            (incomplete, "BASE_SOURCE_COVERAGE")):
            with self.subTest(code=code), mock.patch.object(model_native, "load_base", side_effect=AssertionError("fallback called")):
                with self.assertRaises(ModelError) as error:
                    self.invoke(value)
                self.assertEqual(code, error.exception.code)

    def test_existing_native_errors_and_runtime_drift_remain_distinct(self):
        rejected = {"ok": False, "status": "INVALID", "code": "BASE_LINE", "clause": "I9", "message": "Fixture rejection."}
        with self.assertRaises(ModelError) as error:
            self.invoke(rejected)
        self.assertEqual(("INVALID", "BASE_LINE", "I9", "Fixture rejection."),
                         (error.exception.status, error.exception.code, error.exception.clause, error.exception.message))
        with self.assertRaises(ModelError) as error:
            self.invoke(fixture(), identities=[EXECUTION, ("changed-binary", "c" * 64)])
        self.assertEqual("BASE_RUNTIME_CHANGED", error.exception.code)
        with self.assertRaises(ModelError) as error:
            self.invoke(fixture(), returncode=1)
        self.assertEqual("BASE_PROTOCOL", error.exception.code)

    def test_mode_argument_keeps_an_existing_transport_prefix(self):
        def command_builder(program, source, **options):
            return ["transport", "--literal-program", program, str(source)]
        _, command = self.invoke(fixture(), command_builder=command_builder)
        self.assertEqual(["transport", "--literal-program", "fixture-not-executed", "--neutral-sources"], command[:-1])

    def test_candidate_facade_preserves_historical_builder_and_argv_seams(self):
        from modeling import base as facade
        commands = []
        def process(command, **options):
            commands.append(command)
            self.assertEqual(RAW_SOURCE, Path(command[-1]).read_bytes())
            return subprocess.CompletedProcess(command, 0, json.dumps(native_wire(fixture())).encode(), b"")
        def argv(program, source, **options):
            return ["transport", "--literal-program", program, str(source)]
        with mock.patch.dict(os.environ, {}, clear=True), \
             mock.patch.object(facade, "_build_adapter", return_value="facade-program") as build, \
             mock.patch.object(facade, "_adapter_command", side_effect=argv) as command, \
             mock.patch.object(model_native, "_build_adapter", side_effect=AssertionError("default-facade-builder-bypassed")), \
             mock.patch.object(model_native, "_adapter_command", side_effect=AssertionError("default-facade-argv-bypassed")), \
             mock.patch.object(model_native, "_execution_identity", return_value=EXECUTION) as pin, \
             mock.patch.object(model_native.subprocess, "run", side_effect=process):
            candidate = facade.load_candidate(RAW_SOURCE.decode())
        build.assert_called_once_with()
        self.assertEqual(1, command.call_count)
        self.assertEqual(2, pin.call_count)
        self.assertEqual(1, len(commands))
        self.assertEqual(["transport", "--literal-program", "facade-program", "--neutral-sources"], commands[0][:-1])
        self.assertEqual(EXECUTION, candidate.execution_identity)

    def test_public_default_rejects_incomplete_or_mismatched_transport_once(self):
        from modeling.engine import evaluate as default_evaluate
        from tests.test_geometry_kernel_runtime import cases
        from tests.test_geometry_source_runtime import envelope
        base, definitions, req, options = cases()["keep"]
        original = envelope(base)
        variations = [(original["legacySnapshot"], "BASE_SOURCE_PROTOCOL", False)]
        for patch in ({"complete": False}, {"rootsComplete": False}, {"missingGroups": ["missing-definition"]}):
            value = deepcopy(original)
            value["neutralSources"]["coverage"].update(patch)
            variations.append((value, "BASE_SOURCE_COVERAGE", False))
        value = deepcopy(original)
        value["source"]["sha256After"] = "0" * 64
        variations.append((value, "BASE_RUNTIME_CHANGED", False))
        value = deepcopy(original)
        value["neutralSources"]["candidate"]["id"] = "0" * 64
        variations.append((value, "BASE_SOURCE_PROTOCOL", False))
        variations.append((original, "BASE_RUNTIME_CHANGED", True))
        for value, code, drift in variations:
            calls = []
            def process(command, **ignored):
                calls.append(command)
                self.assertEqual(definitions["base_scene"].encode(), Path(command[-1]).read_bytes())
                return subprocess.CompletedProcess(command, 0, json.dumps(value).encode(), b"")
            identities = [EXECUTION, ("changed-binary", "c" * 64) if drift else EXECUTION]
            with self.subTest(code=code, drift=drift), \
                 mock.patch.object(model_native, "_execution_identity", side_effect=identities) as pin, \
                 mock.patch.object(model_native.subprocess, "run", side_effect=process), \
                 mock.patch("modeling.base.load_base", side_effect=AssertionError("public-default-legacy-fallback")):
                with self.assertRaises(ModelError) as error:
                    default_evaluate(definitions, req, base_executable="fixture-not-executed", **options)
                self.assertEqual(code, error.exception.code)
            self.assertEqual(1, len(calls))
            self.assertEqual(2, pin.call_count)
            self.assertEqual(["fixture-not-executed", "--neutral-sources"], calls[0][:-1])

    def test_public_default_transport_preserves_unchanged_wire_in_one_invocation(self):
        from modeling.engine import evaluate as default_evaluate
        from modeling.common import digest
        from tests.test_geometry_kernel_runtime import cases, FROZEN_DIGESTS
        from tests.test_geometry_source_runtime import envelope
        base, definitions, req, options = cases()["keep"]
        # The frozen kernel fixture names column faces face-0..face-5 in local
        # side order, which the H adapter never emits. Rename them on the wire
        # to the adapter's names and invert that one-to-one renaming on the
        # output, so the frozen legacy digest still decides this test.
        legacy = {}
        for solid in base["solids"]:
            for index, face in enumerate(solid["faces"]):
                self.assertEqual(face["feature"], legacy.setdefault(RECTANGULAR_FACES[index], face["feature"]))
                face["feature"] = RECTANGULAR_FACES[index]
        self.assertEqual(6, len(set(legacy.values())))
        def process(command, **ignored):
            self.assertEqual(["fixture-not-executed", "--neutral-sources"], command[:-1])
            self.assertEqual(definitions["base_scene"].encode(), Path(command[-1]).read_bytes())
            return subprocess.CompletedProcess(command, 0, json.dumps(native_wire(envelope(base))).encode(), b"")
        with mock.patch.object(model_native, "_execution_identity", return_value=EXECUTION) as pin, \
             mock.patch.object(model_native.subprocess, "run", side_effect=process) as run:
            output = default_evaluate(definitions, req, base_executable="fixture-not-executed", **options)
        def restore(item):
            if type(item) is dict:
                return {key: legacy[part] if key == "feature" and part in legacy else restore(part)
                        for key, part in item.items()}
            return [restore(part) for part in item] if type(item) is list else item
        self.assertIn('"feature": "-X"', json.dumps(output))
        self.assertEqual(FROZEN_DIGESTS["keep"], digest({"result": restore(output)}))
        self.assertEqual(1, run.call_count)
        self.assertEqual(2, pin.call_count)


if __name__ == "__main__":
    unittest.main()
