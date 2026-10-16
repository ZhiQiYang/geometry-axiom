"""Strict transport fixtures through the actual neutral geometry consumer.

The envelopes are synthetic protocol fixtures, not native execution evidence.
No scene parser, compiler or executable is used by this suite.
"""
from base64 import b64encode
from copy import deepcopy
from hashlib import sha256
import json
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
from geometry_kernel import (DifferenceDef, EvaluationError, EvaluationRequest,
    ExportRoot, ExtrusionDef, NodeInput, PlacedRegionDef, ProgramBuilder,
    ProvenanceTemplate, QuantityType, SourceBoxDef, SourceStatus, UnionDef,
    ValueType, evaluate)


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


def root(key, slot, identity=1, *, kind="fixture", member=None, name=None):
    result = {"kind": kind, "id": identity, "slot": slot, "memberId": member, "name": name, "ref": ref(key)}
    if slot == "solid.box":
        result["faces"] = [{"axis": a, "side": s, "legacyFeature": f"face-{a}-{s}",
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
            "specs": [], "placements": [], "solids": [], "unplaced_timbers": [], "dependencies": []},
        "neutralSources": {"schema": "geometry-neutral-sources/1", "candidate": deepcopy(candidate),
            "coverage": {"complete": True, "rootsComplete": True, "missingGroups": []},
            "providers": [{"namespace": "fixture.provider", "implementationFingerprint": "contract/1"}],
            "nodes": nodes, "edges": [
                {"consumer": ref(b"box"), "source": ref(b"height"), "kind": kind}
                for kind in ("value-required", "definition-required", "evaluate-before")],
            "roots": [root(b"frame\0\xff", "placement.frame"), root(b"region", "placement.region"),
                      root(b"height", "spec.value", 0, kind="spec", name="H"), root(b"box", "solid.box")]}}


def decode(value):
    return decode_candidate(json.dumps(value), source_bytes=RAW_SOURCE, execution_identity=EXECUTION)


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
            self.assertIn("Ran 12 tests", baseline.stderr)
            mutants = (
                ('if coverage["complete"] is not True or coverage["rootsComplete"] is not True or _array(coverage["missingGroups"]):',
                 'if False:', "test_incomplete_coverage_is_always_rejected"),
                ('if sha256(snapshot["base_scene"].encode("utf-8")).hexdigest() != identity:',
                 'if False:', "test_input_and_candidate_identity_are_bound_together"),
                ('dependencies[consumer].append(DependencyEdge(source, relation))', 'pass',
                 "test_unused_source_cycles_are_not_hidden_by_root_selection"),
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
    def invoke(self, value, *, command_builder=None, returncode=0, identities=None):
        calls = []

        def process(command, **options):
            calls.append(command)
            self.assertEqual(RAW_SOURCE, Path(command[-1]).read_bytes())
            return subprocess.CompletedProcess(command, returncode, json.dumps(value).encode(), b"")

        with mock.patch.object(model_native, "_execution_identity", side_effect=identities or [EXECUTION, EXECUTION]) as pin:
            with mock.patch.object(model_native.subprocess, "run", side_effect=process):
                result = model_native.load_candidate(RAW_SOURCE.decode(), executable="fixture-not-executed",
                                                     command_builder=command_builder)
        self.assertEqual(2, pin.call_count)
        self.assertEqual(1, len(calls))
        return result, calls[0]

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


if __name__ == "__main__":
    unittest.main()
