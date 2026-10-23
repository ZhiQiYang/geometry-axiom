"""Native source references through the real H/W/K compilation path.

Synthetic transport derives from frozen native snapshot fixtures, not scene
syntax. It does not establish actual native execution or coverage completion.
"""
from base64 import b64encode
from copy import deepcopy
from dataclasses import replace
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
import geometry_kernel as kernel
from geometry_app.bootstrap import default_provider
from geometry_app.model_common import ModelError, digest
from geometry_app.model_runtime import ModelingRuntime
from geometry_app.model_sources import decode_candidate
from tests.test_geometry_kernel_runtime import cases, FROZEN_DIGESTS, snapshot, solid, request, ref, placement, profile


def envelope(base):
    """Build typed protocol fixtures without invoking any production translator."""
    base = deepcopy(base)
    base.update(ok=True, unplaced_timbers=[])
    nodes, roots = [], []
    def opaque(label):
        return {"namespace": "runtime.fixture", "keyBase64": b64encode((label + "\0opaque").encode()).decode()}
    def axes(item, owner=None):
        return {**{key: item[key] for key in ("origin", "u", "v", "n")},
                "coordinateDomain": "world" if owner is None else "local", "owner": owner}
    def add(kind, identity, slot, value_type, value, *, member=None, name=None, owner=None, placement=None, faces=None):
        key = opaque(repr((kind, identity, slot, member, name)))
        nodes.append({"ref": key, "descriptor": {"valueType": value_type, "unit": "length",
                      "context": {"placementId": placement, "axis": None, "owner": owner}}, "status": "ok", "value": value})
        root = {"kind": kind, "id": identity, "slot": slot, "memberId": member, "name": name, "ref": key}
        if faces is not None:
            root["faces"] = faces
        roots.append(root)
    def region(outer, holes=()):
        return {"components": [{"outer": outer, "holes": list(holes), "vertexKeys": None}]}
    def quantity(value):
        return {"num": str(value), "den": "1", "unit": "length", "quantityType": "dimension"}
    for item in base["placements"]:
        add("placement", item["id"], "placement.frame", "frame", axes(item), placement=item["id"])
        add("placement", item["id"], "placement.region", "region-set", region(item["outline"], item["holes"]), placement=item["id"])
    for item in base["solids"]:
        vertices = [point for face in item["faces"] for point in face["vertices"]]
        lo = [min(point[a] for point in vertices) for a in range(3)]
        hi = [max(point[a] for point in vertices) for a in range(3)]
        faces = [{"axis": a, "side": s, "legacyFeature": item["faces"][2*a+s]["feature"],
                  "featureKeyBase64": b64encode(f'{item["kind"]}:{item["id"]}:{a}:{s}\0face'.encode()).decode()}
                 for a in range(3) for s in range(2)]
        add(item["kind"], item["id"], "solid.box", "box", {"frame": axes({"origin": [0,0,0], "u": [1,0,0], "v": [0,1,0], "n": [0,0,1]}),
            "lo": lo, "hi": hi}, placement=item.get("placement_id"), faces=faces)
    for item in base["specs"]:
        add("spec", 0, "spec.value", "quantity", quantity(item["value"]), name=item["name"])
    for run in base.get("profile_runs", ()):
        owner = opaque(f'run-owner:{run["id"]}') if run["coordinate_space"] == "local" else None
        for member in (*run["members"], None):
            identity = None if member is None else member["id"]
            if member is None:
                outer = run["outline"]
            else:
                u0,v0,u1,v1 = member["rect"]
                outer = [[u0,v0],[u1,v0],[u1,v1],[u0,v1]]
            for slot, value_type, value in (("profile.frame", "frame", axes(run, owner)),
                ("profile.region", "region-set", region(outer)), ("profile.length", "quantity", quantity(run["length"]))):
                add("profile-run", run["id"], slot, value_type, value, member=identity, owner=owner)
    candidate = {"id": sha256(base["base_scene"].encode()).hexdigest(), "baseRevision": 0}
    source_hash = sha256(base["base_scene"].encode()).hexdigest()
    return {"ok": True, "schema": "geometry-neutral-source-envelope/1", "candidate": candidate,
            "source": {"sha256Before": source_hash, "sha256After": source_hash}, "legacySnapshot": base,
            "neutralSources": {"schema": "geometry-neutral-sources/1", "candidate": deepcopy(candidate),
                "coverage": {"complete": True, "rootsComplete": True, "missingGroups": []},
                "providers": [{"namespace": "runtime.fixture", "implementationFingerprint": "wire/1"}],
                "nodes": nodes, "edges": [], "roots": roots}}


def decode(value):
    return decode_candidate(json.dumps(value), source_bytes=value["legacySnapshot"]["base_scene"].encode(),
                            execution_identity=("fixture-process", "f"*64))


def runtime(candidate):
    return ModelingRuntime(provider=default_provider(), native_loader=lambda *a, **kw: candidate, source_graph=True)


def execute(inputs):
    base, definitions, req, options = deepcopy(inputs)
    try:
        return {"result": runtime(decode(envelope(base))).evaluate(definitions, req, **options)}
    except ModelError as error:
        return {"error": error.as_dict()}


class SourceRuntimeTests(unittest.TestCase):
    def test_source_bound_runtime_preserves_every_frozen_old_wire_oracle(self):
        for name, inputs in cases().items():
            with self.subTest(case=name):
                self.assertEqual(FROZEN_DIGESTS[name], digest(execute(inputs)))

    def test_geometry_templates_are_references_and_do_not_rebuild_native_values(self):
        base, definitions, req, options = cases()["local_profile"]
        candidate = decode(envelope(base))
        with mock.patch("geometry_app.model_runtime.solid_definition", side_effect=AssertionError("literal box")), \
             mock.patch("geometry_app.model_runtime._inputs", side_effect=AssertionError("literal placement")), \
             mock.patch("geometry_woodworking.section_profile.FrameDef", side_effect=AssertionError("literal profile")):
            compiled = runtime(candidate).compile(definitions, req, max_cells=200000)
        self.assertEqual(candidate.snapshot_identity, compiled.program.snapshot_identity)
        self.assertEqual({source.key for source in candidate.sources}, {source.key for source in compiled.program.sources})
        boxes = [node.definition for node in compiled.program.nodes if isinstance(node.definition, kernel.SourceBoxDef)]
        self.assertEqual(1, len(boxes))
        profile_regions = [node.definition for node in compiled.program.nodes if isinstance(node.definition, kernel.PlacedRegionDef)]
        self.assertEqual(3, len(profile_regions))
        self.assertTrue(all(isinstance(node.frame, kernel.SourceRef) and isinstance(node.region, kernel.SourceRef) for node in profile_regions))
        spans = [node.definition for node in compiled.program.nodes if isinstance(node.definition, kernel.ExtrusionDef)]
        self.assertTrue(all(isinstance(node.upper, kernel.SourceRef) for node in spans))
        output = runtime(candidate).evaluate(definitions, req)
        self.assertEqual(FROZEN_DIGESTS["local_profile"], digest({"result": output}))

    def test_same_identity_box_source_update_drives_real_product_mesh(self):
        base, definitions, req, options = cases()["keep"]
        candidate = decode(envelope(base))
        changed = candidate.sources[0]
        changed = replace(changed, value=replace(changed.value, upper=(30,20,20)))
        updated = replace(candidate, sources=(changed, *candidate.sources[1:]))
        before = runtime(candidate).evaluate(definitions, req)
        after = runtime(updated).evaluate(definitions, req)
        self.assertEqual(["1000", "8000"], [item["volume_mm3"] for item in before["derived"]["objects"]])
        self.assertEqual(["1000", "12000"], [item["volume_mm3"] for item in after["derived"]["objects"]])
        def provenance(output):
            return {json.dumps(source, sort_keys=True) for row in output["derived"]["objects"][1]["face_sources"] for source in row}
        self.assertEqual(provenance(before), provenance(after))

    def test_quantity_and_frame_source_updates_drive_extrusion_without_literal_substitution(self):
        base, definitions, req, options = cases()["extrusion"]
        candidate = decode(envelope(base))
        changed = []
        for source in candidate.sources:
            if source.value_type == kernel.ValueType.FRAME:
                source = replace(source, value=replace(source.value, origin=(3,4,5)))
            elif source.value_type == kernel.ValueType.QUANTITY and source.value.numerator == 20:
                source = replace(source, value=replace(source.value, numerator=30))
            changed.append(source)
        output = runtime(replace(candidate, sources=tuple(changed))).evaluate(definitions, req)
        mesh = output["derived"]["objects"][0]
        self.assertEqual("12000", mesh["volume_mm3"])
        self.assertEqual([3,4,5], [min(p[a] for p in mesh["vertices_mm"]) for a in range(3)])
        self.assertEqual([23,24,35], [max(p[a] for p in mesh["vertices_mm"]) for a in range(3)])

    def test_complete_source_graph_and_unselected_profile_inputs_are_retained(self):
        base, definitions, req, options = cases()["unselected_profile_dependencies"]
        value = envelope(base)
        graph = value["neutralSources"]
        # Native parameter roots carry the actual field name as well as card
        # and field IDs; they remain source definitions, not geometry roots.
        parameter = {"namespace": "runtime.fixture", "keyBase64": b64encode(b"parameter\0field").decode()}
        graph["nodes"].append({"ref": parameter, "descriptor": {"valueType": "quantity", "unit": "scalar",
            "context": {"placementId": None, "axis": None, "owner": None}}, "status": "ok",
            "value": {"num": "3", "den": "7", "unit": "scalar", "quantityType": "ratio"}})
        value["legacySnapshot"]["parameter_fields"] = [{"parameterId": 8, "fieldId": 3, "name": "ratio_field"}]
        graph["roots"].append({"kind": "parameter", "id": 8, "slot": "parameter.value", "memberId": 3,
                              "name": "ratio_field", "ref": parameter})
        box = graph["nodes"][0]["ref"]
        dependency = graph["nodes"][-1]["ref"]
        graph["edges"] = [{"consumer": box, "source": dependency, "kind": kind} for kind in
                          ("value-required", "definition-required", "evaluate-before")]
        candidate = decode(value)
        compiled = runtime(candidate).compile(definitions, req, max_cells=200000)
        self.assertEqual(len(candidate.sources), len(compiled.program.sources))
        closure = kernel.source_closure(compiled.program, (compiled.identities[("column",1)],))
        self.assertEqual({candidate.sources[0].key, candidate.sources[-1].key}, {source.key for source in closure})
        self.assertEqual(3, len(next(source for source in closure if source.key == candidate.sources[0].key).dependencies))
        self.assertEqual(kernel.QuantityType.RATIO, candidate.sources[-1].value.value_type)
        duplicate = deepcopy(value)
        duplicate["neutralSources"]["roots"].append({**graph["roots"][-1], "name": "different_name"})
        with self.assertRaises(ModelError) as error:
            decode(duplicate)
        self.assertEqual("BASE_SOURCE_BINDING", error.exception.code)
        # The decoder's root catalog refuses that wire by itself, so inject the
        # second name after decoding to reach the runtime's own binding guard.
        self.assertEqual(("parameter", 8, "parameter.value", 3, "ratio_field"), candidate.roots[-1].association)
        duplicate = replace(candidate, roots=(*candidate.roots, replace(candidate.roots[-1], name="different_name")))
        with self.assertRaises(ModelError) as error:
            runtime(duplicate).compile(definitions, req, max_cells=200000)
        self.assertEqual(("BASE_SOURCE_BINDING", "Native parameter fields cannot have multiple root names."),
                         (error.exception.code, error.exception.message))
        graph["edges"].append({"consumer": dependency, "source": box, "kind": "definition-required"})
        with self.assertRaises(ModelError) as error:
            decode(value)
        self.assertEqual("BASE_SOURCE_PROTOCOL", error.exception.code)

    def test_source_mode_refuses_snapshot_only_and_missing_extra_or_wrong_root_associations(self):
        base, definitions, req, options = cases()["extrusion"]
        with self.assertRaises(ModelError) as error:
            runtime(base).evaluate(definitions, req)
        self.assertEqual("BASE_SOURCE_PROTOCOL", error.exception.code)
        for mutation in ("missing", "extra", "wrong"):
            candidate = decode(envelope(base))
            if mutation == "missing":
                candidate = replace(candidate, roots=candidate.roots[:-1])
            elif mutation == "extra":
                candidate = replace(candidate, roots=(*candidate.roots, replace(candidate.roots[0], identity=999)))
            else:
                candidate = replace(candidate, roots=(replace(candidate.roots[0], source=candidate.roots[1].source), *candidate.roots[1:]))
            with self.subTest(mutation=mutation):
                with self.assertRaises(ModelError) as error:
                    runtime(candidate).evaluate(definitions, req)
                self.assertEqual("BASE_SOURCE_BINDING", error.exception.code)
        candidate = decode(envelope(base))
        spec = next(source for source in candidate.sources if source.value_type == kernel.ValueType.QUANTITY)
        wrong = replace(spec, value=kernel.Quantity(kernel.QuantityType.COUNT, 1, 1, kernel.Unit.UNITLESS))
        candidate = replace(candidate, sources=tuple(wrong if source.key == spec.key else source for source in candidate.sources))
        with self.assertRaises(ModelError) as error:
            runtime(candidate).compile(definitions, req, max_cells=200000)
        self.assertEqual("BASE_SOURCE_BINDING", error.exception.code)

    def test_opaque_native_box_provenance_survives_until_wire_encoding(self):
        base, definitions, req, options = cases()["cavity"]
        candidate = decode(envelope(base))
        compiled = runtime(candidate).compile(definitions, req, max_cells=200000)
        raw = kernel.evaluate(compiled.program, compiled.kernel_request, limits=compiled.limits)
        sources = [source for record in raw.records for row in record.mesh["face_sources"] for source in row]
        self.assertTrue(all(source.origin_handle[0] == "runtime.fixture" for source in sources))
        self.assertTrue(all(source.feature_key[0] == "face" and "00" in source.feature_key[1] for source in sources))
        self.assertTrue(any(source.contribution == "cut" for source in sources))
        self.assertEqual(FROZEN_DIGESTS["cavity"], digest(execute(cases()["cavity"])))

    def test_full_native_components_are_used_instead_of_legacy_single_outline(self):
        base, definitions, req, options = cases()["extrusion"]
        value = envelope(base)
        regions = next(node for node in value["neutralSources"]["nodes"] if node["descriptor"]["valueType"] == "region-set")
        regions["value"]["components"].append({"outer": [[30,0],[40,0],[40,10],[30,10]], "holes": [], "vertexKeys": None})
        host = runtime(decode(value))
        compiled = host.compile(definitions, req, max_cells=200000)
        output = kernel.evaluate(compiled.program, compiled.kernel_request, limits=compiled.limits)
        self.assertEqual(["8000", "2000"], [item.mesh["volume_mm3"] for item in output.records])
        self.assertEqual(2, len(output.records))
        # The unchanged legacy wire has no component feature identity slot.
        # Reject it explicitly rather than dropping the full neutral identity.
        with self.assertRaises(ModelError) as error:
            host.evaluate(definitions, req)
        self.assertEqual("BASE_SOURCE_PROTOCOL", error.exception.code)

    def test_rotated_box_local_face_identity_maps_to_original_wire(self):
        base = snapshot(solids=(solid(1, upper=(30,20,10)),))
        value = envelope(base)
        graph = value["neutralSources"]
        box = graph["nodes"][0]["value"]
        box["frame"].update(origin=[30,0,0], u=[0,1,0], v=[-1,0,0], n=[0,0,1])
        box["hi"] = [20,30,10]
        faces = graph["roots"][0]["faces"]
        # Local +u is world +y; local +v is world -x.
        for face, legacy_index in zip(faces, (2,3,1,0,4,5)):
            face["legacyFeature"] = f"face-{legacy_index}"
        definitions = {"base_scene": base["base_scene"], "extensions": []}
        req = request(ref("column",1))
        rotated = runtime(decode(value)).evaluate(definitions, req)
        identity = runtime(decode(envelope(base))).evaluate(definitions, req)
        self.assertEqual(identity, rotated)
        self.assertEqual("6000", rotated["derived"]["objects"][0]["volume_mm3"])

    def test_removed_source_binding_and_source_consumption_guards_are_detected(self):
        with tempfile.TemporaryDirectory(prefix="geometry-source-runtime-guards-") as directory:
            copied = Path(directory)
            for package in ("geometry-core/geometry_kernel", "geometry-core/modeling",
                            "geometry-app/geometry_app", "geometry-templates/woodworking/geometry_woodworking"):
                shutil.copytree(ROOT / package, copied / package, ignore=shutil.ignore_patterns("__pycache__"))
            (copied / "tests").mkdir()
            (copied / "tests/__init__.py").write_text("", encoding="utf-8")
            for name in ("test_geometry_source_runtime.py", "test_geometry_kernel_runtime.py"):
                shutil.copyfile(ROOT / "tests" / name, copied / "tests" / name)
            controls = (
                ("geometry-app/geometry_app/model_runtime.py",
                 "definition = solid_definition(solid, _source(key)) if bindings is None else SourceBoxDef(solid_sources[key])",
                 "definition = solid_definition(solid, _source(key))",
                 "test_same_identity_box_source_update_drives_real_product_mesh"),
                ("geometry-app/geometry_app/model_runtime.py",
                 "axes, region = _inputs(placement) if bindings is None else placement_sources[key]",
                 "axes, region = _inputs(placement)",
                 "test_full_native_components_are_used_instead_of_legacy_single_outline"),
                ("geometry-templates/woodworking/geometry_woodworking/model_sources.py",
                 "for association in set(associations) - consumed:",
                 "for association in ():",
                 "test_source_mode_refuses_snapshot_only_and_missing_extra_or_wrong_root_associations"),
                ("geometry-templates/woodworking/geometry_woodworking/model_sources.py",
                 "if (identity, member) in parameters:",
                 "if False:",
                 "test_complete_source_graph_and_unselected_profile_inputs_are_retained"),
            )
            for name, before, after, test in controls:
                with self.subTest(control=name, test=test):
                    source = copied / name
                    original = source.read_text(encoding="utf-8")
                    self.assertEqual(1, original.count(before))
                    command = [sys.executable, "-I", "-B", "-c",
                        "import sys,unittest;sys.path.insert(0,sys.argv.pop(1));unittest.main(module=None)",
                        str(copied), "tests.test_geometry_source_runtime.SourceRuntimeTests." + test]
                    def run():
                        return subprocess.run(command, cwd=copied, capture_output=True, text=True, timeout=30)
                    baseline = run()
                    self.assertEqual(0, baseline.returncode, baseline.stdout + baseline.stderr)
                    source.write_text(original.replace(before, after), encoding="utf-8")
                    mutant = run()
                    details = mutant.stdout + mutant.stderr
                    self.assertEqual(1, mutant.returncode, details)
                    self.assertIn("FAILED (failures=1)", details)
                    self.assertIn("Ran 1 test", details)
                    self.assertNotIn("ImportError", details)
                    self.assertNotIn("SyntaxError", details)
                    source.write_text(original, encoding="utf-8")
                    restored = run()
                    self.assertEqual(0, restored.returncode, restored.stdout + restored.stderr)


if __name__ == "__main__":
    unittest.main()
