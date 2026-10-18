"""Frozen legacy wire oracles for the product path through the neutral graph.

The exact native snapshot fixtures are supplied at the established loader seam.
This suite does not replace the real native adapter replay gate.
"""
from copy import deepcopy
from dataclasses import replace
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "geometry-core"))
from modeling import ModelError, canonical_bytes
from modeling.common import digest
from modeling.engine import evaluate


def placement(identity=1, *, origin=(0, 0, 0), u=(1, 0, 0), v=(0, 1, 0), n=(0, 0, 1), holes=()):
    return {"id": identity, "boundary_id": identity, "origin": list(origin), "u": list(u), "v": list(v), "n": list(n),
            "outline": [[0, 0], [20, 0], [20, 20], [0, 20]], "holes": list(holes)}


def solid(identity=1, origin=(0, 0, 0), upper=(20, 20, 20), kind="column"):
    local = [
        [(0, 0, 0), (0, 0, 1), (0, 1, 1), (0, 1, 0)],
        [(1, 0, 0), (1, 1, 0), (1, 1, 1), (1, 0, 1)],
        [(0, 0, 0), (1, 0, 0), (1, 0, 1), (0, 0, 1)],
        [(0, 1, 0), (0, 1, 1), (1, 1, 1), (1, 1, 0)],
        [(0, 0, 0), (0, 1, 0), (1, 1, 0), (1, 0, 0)],
        [(0, 0, 1), (1, 0, 1), (1, 1, 1), (0, 1, 1)],
    ]
    return {"kind": kind, "id": identity, "placement_id": None, "boundary_id": None,
            "faces": [{"feature": "face-" + str(i), "vertices": [[origin[a]+p[a]*upper[a] for a in range(3)] for p in points]} for i, points in enumerate(local)]}


def snapshot(*, placements=(), solids=(), specs=(), profiles=(), dependencies=()):
    return {"schema": "geometry-base-snapshot/1", "base_scene": "# preserved native source\n",
            "placements": list(placements), "solids": list(solids), "specs": list(specs),
            "profile_runs": list(profiles), "dependencies": list(dependencies), "required_capabilities": []}


def ref(kind, identity):
    return {"kind": kind, "id": identity}


def request(*roots, role="geometry", target="solid-set", partial=False):
    return {"roots": list(roots), "role": role, "target": target, "allow_partial": partial}


def case(base, extensions, req, **options):
    return base, {"base_scene": base["base_scene"], "extensions": extensions}, req, options


def shell_case(*, closed=True, inward=False, obstacles=()):
    rows = [placement(1, u=(0, 0, 1), v=(0, 1, 0), n=(-1, 0, 0)),
            placement(2, origin=(20, 0, 0), u=(0, 1, 0), v=(0, 0, 1), n=(1, 0, 0)),
            placement(3, u=(1, 0, 0), v=(0, 0, 1), n=(0, -1, 0)),
            placement(4, origin=(0, 20, 0), u=(0, 0, 1), v=(1, 0, 0), n=(0, 1, 0)),
            placement(5, u=(0, 1, 0), v=(1, 0, 0), n=(0, 0, -1)),
            placement(6, origin=(0, 0, 20))]
    rows = rows[:6 if closed else 5]
    base = snapshot(placements=rows, solids=obstacles)
    extensions = [{"kind": "shell", "id": 9, "uses": [{"placement_id": p["id"], "orientation": -1 if inward else 1, "purpose": "boundary"} for p in reversed(rows)]},
                  {"kind": "composite_space", "id": 10, "shell_id": 9, "obstacles": [ref(item["kind"], item["id"]) for item in obstacles]}]
    return base, extensions


def profile(identity=8, coordinate_space="local"):
    return {"id": identity, "profile_id": 7, "coordinate_space": coordinate_space, "origin": [3, 7, 11],
            "u": [1, 0, 0], "v": [0, 1, 0], "n": [0, 0, 1], "length": 30,
            "outline": [[0, 0], [10, 0], [10, 10], [0, 10]],
            "members": [{"id": 1, "kind": "panel", "rect": [0, 0, 10, 2], "dimensions_mm": [10, 2, 30], "definition": {"orientation": "uv"}},
                        {"id": 2, "kind": "timber", "rect": [0, 2, 2, 10], "dimensions_mm": [2, 8, 30], "definition": {"orientation": "vu"}}]}


def cases():
    results = {}
    base = snapshot(placements=(placement(),), specs=({"name": "lo", "value": 0}, {"name": "hi", "value": 20}))
    extrusion = {"kind": "extrusion", "id": 50, "placement_id": 1, "lo_spec": "lo", "hi_spec": "hi"}
    results["placement"] = case(base, [], request(ref("placement", 1), target="surface-set"))
    results["extrusion"] = case(base, [extrusion], request(ref("extrusion", 50)))
    holed = deepcopy(base)
    holed["placements"][0]["holes"] = [[[5, 5], [15, 5], [15, 15], [5, 15]]]
    results["holed"] = case(holed, [extrusion], request(ref("extrusion", 50)))
    boxes = snapshot(solids=(solid(), solid(2, (5, 5, 5), (10, 10, 10))))
    difference = {"kind": "composition", "id": 90, "op": "DIFFERENCE", "base": ref("column", 1), "tools": [ref("column", 2)]}
    results["cavity"] = case(boxes, [difference], request(ref("composition", 90)))
    results["empty"] = case(boxes, [{**difference, "tools": [ref("column", 1)]}], request(ref("composition", 90)))
    keep = {"kind": "composition", "id": 80, "op": "KEEP", "inputs": [ref("column", 2), ref("column", 1)]}
    results["keep"] = case(boxes, [keep], request(ref("composition", 80)))
    nested = {"kind": "composition", "id": 81, "op": "KEEP", "inputs": [ref("composition", 80)]}
    results["nested_keep"] = case(boxes, [keep, nested], request(ref("composition", 81)))
    base_closed, extensions = shell_case(obstacles=(solid(20, (5, 5, 5), (10, 10, 10)),))
    results["enclosure"] = case(base_closed, extensions, request(ref("composite_space", 10), role="enclosure"))
    results["clearance"] = case(base_closed, extensions, request(ref("composite_space", 10), role="clearance"))
    results["shell"] = case(base_closed, extensions, request(ref("shell", 9), target="surface-set"))
    base_open, opened = shell_case(closed=False)
    results["open_boundary"] = case(base_open, opened, request(ref("composite_space", 10), role="enclosure", target="surface-set"))
    results["open_interior"] = case(base_open, opened, request(ref("composite_space", 10), role="clearance"))
    results["open_partial"] = case(base_open, opened, request(ref("composite_space", 10), role="clearance", partial=True))
    inward_base, inward = shell_case(inward=True)
    results["unselected_inward"] = case(inward_base, inward, request(ref("placement", 1), target="surface-set"))
    results["missing_reference"] = case(boxes, [{**difference, "tools": [ref("column", 99)]}], request(ref("column", 1)))
    results["forward_reference"] = case(boxes, [nested, keep], request(ref("composition", 81)))
    cycle = {**keep, "inputs": [ref("composition", 81)]}
    results["cycle"] = case(boxes, [cycle, nested], request(ref("column", 1)))
    results["keep_operand"] = case(boxes, [keep, {**difference, "tools": [ref("composition", 80)]}], request(ref("column", 1)))
    results["unknown_capability"] = case(boxes, [difference], request(ref("composition", 90)), capabilities=["unknown/1"])
    results["invalid_before_capability"] = case(inward_base, inward, request(ref("placement", 1), target="surface-set"), capabilities=[])
    inward_box_base, inward_box = shell_case(inward=True, obstacles=(solid(20, (5, 5, 5), (10, 10, 10)),))
    results["inward_with_obstacle"] = case(inward_box_base, inward_box, request(ref("placement", 1), target="surface-set"))
    missing_two = {**difference, "tools": [ref("column", 98), ref("column", 99)]}
    results["multiple_missing_references"] = case(boxes, [missing_two], request(ref("column", 1)))
    results["missing_root"] = case(boxes, [], request(ref("column", 99)))
    results["wrong_role"] = case(boxes, [], request(ref("column", 1), role="enclosure"))
    results["local_profile"] = case(snapshot(solids=(solid(),), profiles=(profile(),)), [], request(ref("column", 1), ref("profile-run", 8)))
    results["world_profile"] = case(snapshot(solids=(solid(),), profiles=(profile(coordinate_space="world"),)), [], request(ref("column", 1), ref("profile-run", 8)))
    profile_dependencies = ({"kind": "profile-run", "id": 8, "refs": [ref("column", 1)]},)
    results["unselected_profile_dependencies"] = case(snapshot(solids=(solid(),), profiles=(profile(),), dependencies=profile_dependencies), [], request(ref("column", 1)))
    return results


def execute(evaluator, inputs):
    from tests.test_geometry_source_runtime import decode, envelope
    base, definitions, req, options = deepcopy(inputs)
    with mock.patch("modeling.base.load_candidate", return_value=decode(envelope(base))):
        try:
            return {"result": evaluator(definitions, req, **options)}
        except ModelError as error:
            return {"error": error.as_dict()}


# Captured from 3a9dc84 (pre-neutral-controller engine), not the new compiler.
FROZEN_DIGESTS = {
    "placement": "bfa6a8f85d0d724f8abd82cae1d6f133ed88c8110f49534dd8bda8f9dde70251",
    "extrusion": "9b5d167490dddd483971f93a3e5f2313603df09ea968469a58b9d8ca83c67b32",
    "holed": "46aa481d950ef45103f192501407611f5da9922165ffe34f6129dbab3f421316",
    "cavity": "118b27caf9a15cee8ac5487135dcdd5c958e9728fc592d0c2ff826fdc818d04d",
    "empty": "0933bcfa4ce96d862dfa4b0ca6366d6544fcec8b08508f47fe89841d2d5e2d7c",
    "keep": "661863c4c92d48d6360011d78c350209a6a0b7b708ed5d2d7b3b49225c8f4939",
    "nested_keep": "bee210fa29ffc46791d9d593ef0f5816dda6c8a9d15b71c3a54972383a9f33cb",
    "enclosure": "ef4bd399363b2e98cb206c0d0b480ff97c26e100a78e2a7932ef22f375f6543f",
    "clearance": "3d259284ec4e936580f96b787daa607616f83abce77f0a2f90b5fcf8dc51a93f",
    "shell": "0bc304dd87915dd9683ad8057cc83e763e7f1afe1c77d92b9918dd6b6951c9d8",
    "open_boundary": "2e457d0328295a7e6a8133277f7b5f890bdab147138c7908d3b955467c8d154a",
    "open_interior": "266a10372eac4e222817c131bebf92615b8f33d84aa1b3a2c3e0700fdc19ea17",
    "open_partial": "9af8f280aabc647f342ec3584c3e82f2a40d22b44bf4a79ed6ea293d14141122",
    "unselected_inward": "8e3882a9012dbbaa98d76ec2bc920549aea20796825e99e2ee5e7de61da11e0a",
    "missing_reference": "6700e6137525eaad955cebd3372cc016f763ee785234d6abaadd475266e7a287",
    "forward_reference": "fa8231d08486bb260ffc2fb0de9c0ba6f204f40c2ab654282cfae7ad6960392e",
    "cycle": "0e15ef4d4b70add6214c0ab345a46511d05c6bdae1f5a5751dcf634d76b4326a",
    "keep_operand": "c2c6e1580df5065176256e57835d22fead68ff043a8f215b1425b7e69f5ac82d",
    "unknown_capability": "b7f98335838aca703d79df9967dd7c1b1ae2db6b4b496ad52ca5a72f94235419",
    "invalid_before_capability": "a11e48df9ee5cec1ff750ee995aae61fd22a89406c44af35a1be4298ae5cc1f7",
    "inward_with_obstacle": "8e3882a9012dbbaa98d76ec2bc920549aea20796825e99e2ee5e7de61da11e0a",
    "multiple_missing_references": "99c2acdc94d9b63e373249639d9b43efd284f35669d17b1d600cffd834cfff13",
    "missing_root": "103784876321b87273680554f023ea22524ec34fa8ad8f4bc1606ac084183129",
    "wrong_role": "f600581d6f13b82290747b8d668f55c027a8638fff9f1dc2e26db03c6f392231",
    "local_profile": "1f05d7152cce63efc5486d1274dabaec724076fdfec9afd9dc88b7b2920ae877",
    "world_profile": "217760df66e49881376ff33d560dfa6574dd93d9ca7331dc056957c244d069cf",
    "unselected_profile_dependencies": "a692f2a71692f030c345ae6f599c32b20a3d2d0c73da2b73b7b0418a538ada6b",
}


class KernelRuntimeTests(unittest.TestCase):
    def test_policy_error_cause_supports_standard_unittest_reporting(self):
        from io import StringIO
        from geometry_woodworking.model_policy import PolicyIssue
        from tests.test_geometry_source_runtime import decode, envelope

        # Keep the real typed geometry, but provide inconsistent R37 metadata.
        # The actual W provider must reject it and H must preserve that cause.
        base, definitions, req, options = deepcopy(cases()["local_profile"])
        base["profile_runs"][0]["members"][0]["dimensions_mm"][0] += 1
        candidate = decode(envelope(base))
        captured = []

        def rejected_profile():
            with mock.patch("modeling.base.load_candidate", return_value=candidate):
                try:
                    evaluate(definitions, req, **options)
                except ModelError as error:
                    captured.append((error, error.__cause__))
                    raise

        stream = StringIO()
        protocol_error = None
        try:
            # The normal Python runner formats/cleans the complete cause chain.
            # No custom collector, exception replacement or cause suppression.
            result = unittest.TextTestRunner(stream=stream, verbosity=2).run(
                unittest.FunctionTestCase(rejected_profile))
        except Exception as error:
            protocol_error = (type(error).__module__ + "." + type(error).__qualname__, str(error))
        # Assert outside the handler, so a runner failure is an ordinary red
        # test rather than a second failure while rendering a frozen cause.
        self.assertIsNone(protocol_error, "POLICY_EXCEPTION_STANDARD_PROTOCOL: " + repr(protocol_error))
        self.assertEqual(1, result.testsRun)
        self.assertEqual([], result.failures)
        self.assertEqual(1, len(result.errors))
        self.assertEqual([], result.skipped)
        self.assertFalse(result.wasSuccessful())
        self.assertEqual(1, len(captured))
        error, original_cause = captured[0]
        self.assertIs(type(error), ModelError)
        self.assertIs(type(original_cause), PolicyIssue)
        self.assertIs(original_cause, error.__cause__)
        expected = ("INVALID", "PROFILE_VOLUME", "R37",
                    "Native dimensions and derived exact member volume disagree")
        for failure in (error, original_cause):
            self.assertEqual(expected, (failure.status, failure.code, failure.clause, failure.message))
        self.assertEqual({"kind": "profile-run", "id": 8}, error.root)
        self.assertEqual(("profile-run", 8), original_cause.root)
        self.assertIsNotNone(original_cause.__traceback__)
        self.assertIn("geometry_woodworking.model_policy.PolicyIssue", stream.getvalue())
        self.assertIn("geometry_app.model_common.ModelError", stream.getvalue())
        self.assertIn(expected[3], stream.getvalue())
        self.assertNotIn("FrozenInstanceError", stream.getvalue())

    def test_public_build_capabilities_gate_export_after_full_definition_validation(self):
        import geometry_kernel
        from modeling import build_package
        opened_base, opened = shell_case(closed=False)
        checks = (
            (case(opened_base, opened, request(ref("composite_space", 10), role="clearance"), capabilities=[]),
             ["composite-space/1", "model-export/1", "shell/1"]),
            (case(snapshot(solids=(solid(), solid(2, (40, 40, 40)))), [],
                  request(ref("column", 1), ref("column", 2)), capabilities=[], max_cells=1),
             ["model-export/1"]),
        )
        for inputs, missing in checks:
            with self.subTest(missing=missing), mock.patch.object(geometry_kernel, "evaluate", wraps=geometry_kernel.evaluate) as call:
                actual = execute(build_package, inputs)
            expected = {"error": {"status": "UNSUPPORTED", "diagnostics": [{
                "root": None, "path": [], "code": "CAPABILITY", "clause": "I32",
                "message": "Required capabilities are unavailable: " + ", ".join(missing),
                "missing": missing}]}}
            self.assertEqual(expected, actual)
            self.assertEqual(1, call.call_count)
            self.assertIsInstance(call.call_args.args[0], geometry_kernel.Program)
        # The capability refusal must not hide an unselected inward interior.
        self.assertEqual(FROZEN_DIGESTS["invalid_before_capability"],
                         digest(execute(build_package, cases()["invalid_before_capability"])))

    def test_capability_export_phase_guard_removal_is_detected(self):
        with tempfile.TemporaryDirectory(prefix="geometry-capability-guard-") as directory:
            copied = Path(directory)
            for package in ("geometry-core/geometry_kernel", "geometry-core/modeling",
                            "geometry-app/geometry_app",
                            "geometry-templates/woodworking/geometry_woodworking"):
                shutil.copytree(ROOT / package, copied / package,
                                ignore=shutil.ignore_patterns("__pycache__"))
            (copied / "tests").mkdir()
            (copied / "tests/__init__.py").write_text("", encoding="utf-8")
            for name in ("test_geometry_kernel_runtime.py", "test_geometry_source_runtime.py"):
                shutil.copyfile(ROOT / "tests" / name, copied / "tests" / name)
            source = copied / "geometry-app/geometry_app/model_runtime.py"
            original = source.read_text(encoding="utf-8")
            before = "validation_only=bool(capability_errors)"
            self.assertEqual(1, original.count(before))
            command = [sys.executable, "-I", "-B", "-c",
                       "import sys,unittest;sys.path.insert(0,sys.argv.pop(1));unittest.main(module=None)",
                       str(copied), "tests.test_geometry_kernel_runtime.KernelRuntimeTests.test_public_build_capabilities_gate_export_after_full_definition_validation"]
            def run():
                return subprocess.run(command, cwd=copied, capture_output=True, text=True, timeout=30)
            baseline = run()
            self.assertEqual(0, baseline.returncode, baseline.stdout + baseline.stderr)
            source.write_text(original.replace(before, "validation_only=False"), encoding="utf-8")
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

    def test_product_evaluator_preserves_frozen_wire_and_diagnostics(self):
        fixtures = cases()
        self.assertEqual(set(fixtures), set(FROZEN_DIGESTS))
        for name, inputs in fixtures.items():
            with self.subTest(case=name):
                self.assertEqual(FROZEN_DIGESTS[name], digest(execute(evaluate, inputs)))

    def test_product_path_calls_public_neutral_evaluator(self):
        import geometry_kernel
        with mock.patch.object(geometry_kernel, "evaluate", wraps=geometry_kernel.evaluate) as call:
            output = execute(evaluate, cases()["cavity"])
        self.assertEqual("7000", output["result"]["derived"]["objects"][0]["volume_mm3"])
        self.assertEqual(1, call.call_count)
        self.assertIsInstance(call.call_args.args[0], geometry_kernel.Program)

    def test_default_consumes_changed_typed_box_and_preserves_complete_candidate(self):
        import geometry_kernel as kernel
        from tests.test_geometry_source_runtime import decode, envelope
        base, definitions, req, options = cases()["keep"]
        candidate = decode(envelope(base))
        changed = replace(candidate.sources[0], value=replace(candidate.sources[0].value, upper=(30, 20, 20)))
        candidate = replace(candidate, sources=(changed, *candidate.sources[1:]))
        original = candidate.legacy_snapshot
        with mock.patch("modeling.base.load_candidate", return_value=candidate) as loader, \
             mock.patch("modeling.base.load_base", side_effect=AssertionError("default-must-not-load-legacy-snapshot")), \
             mock.patch("geometry_app.model_runtime.solid_definition", side_effect=AssertionError("default-must-not-build-literal-box")), \
             mock.patch.object(kernel, "evaluate", wraps=kernel.evaluate) as evaluator:
            result = evaluate(definitions, req, **options)
        self.assertEqual(["1000", "12000"], [item["volume_mm3"] for item in result["derived"]["objects"]],
                         "default-must-consume-returned-box")
        loader.assert_called_once_with(definitions["base_scene"], executable=None)
        self.assertEqual(1, evaluator.call_count)
        program = evaluator.call_args.args[0]
        self.assertEqual(candidate.snapshot_identity, program.snapshot_identity)
        # H binds legacy output tokens onto opaque face provenance; it must
        # retain every source identity, typed context and dependency edge.
        self.assertEqual(tuple(source.key for source in candidate.sources), tuple(source.key for source in program.sources))
        self.assertEqual(tuple((source.value_type, source.context, source.dependencies, source.status) for source in candidate.sources),
                         tuple((source.value_type, source.context, source.dependencies, source.status) for source in program.sources))
        self.assertEqual(original, candidate.legacy_snapshot)

    def test_default_consumes_changed_typed_frame_and_quantity(self):
        import geometry_kernel as kernel
        from tests.test_geometry_source_runtime import decode, envelope
        base, definitions, req, options = cases()["extrusion"]
        candidate = decode(envelope(base))
        changed = []
        for source in candidate.sources:
            if source.value_type == kernel.ValueType.FRAME:
                source = replace(source, value=replace(source.value, origin=(3, 4, 5)))
            elif source.value_type == kernel.ValueType.QUANTITY and source.value.numerator == 20:
                source = replace(source, value=replace(source.value, numerator=30))
            changed.append(source)
        with mock.patch("modeling.base.load_candidate", return_value=replace(candidate, sources=tuple(changed))), \
             mock.patch("geometry_app.model_runtime._inputs", side_effect=AssertionError("default-must-not-build-literal-placement")):
            mesh = evaluate(definitions, req, **options)["derived"]["objects"][0]
        self.assertEqual("12000", mesh["volume_mm3"], "default-must-consume-returned-quantity")
        self.assertEqual([3, 4, 5], [min(point[a] for point in mesh["vertices_mm"]) for a in range(3)])
        self.assertEqual([23, 24, 35], [max(point[a] for point in mesh["vertices_mm"]) for a in range(3)])

    def test_default_retains_unused_definition_edges_without_forcing_values(self):
        from tests.test_geometry_source_runtime import decode, envelope
        base, definitions, req, options = cases()["keep"]
        value = envelope(base)
        graph = value["neutralSources"]
        key = {"namespace": "runtime.fixture", "keyBase64": "dW51c2VkLWRlZmluaXRpb24="}
        graph["nodes"].append({"ref": key, "descriptor": {"valueType": "definition", "unit": "scalar",
            "context": {"placementId": None, "axis": None, "owner": None}}, "status": "unevaluated", "value": None})
        graph["edges"].append({"consumer": graph["nodes"][0]["ref"], "source": key, "kind": "definition-required"})
        candidate = decode(value)
        with mock.patch("modeling.base.load_candidate", return_value=candidate):
            self.assertEqual(FROZEN_DIGESTS["keep"], digest({"result": evaluate(definitions, req, **options)}))
        graph["edges"][0]["kind"] = "value-required"
        with mock.patch("modeling.base.load_candidate", return_value=decode(value)):
            with self.assertRaises(ModelError) as error:
                evaluate(definitions, req, **options)
        self.assertEqual("INCOMPLETE", error.exception.status)
        self.assertEqual("SOURCE_UNAVAILABLE", error.exception.code)

    def test_removed_default_source_selection_is_detected(self):
        with tempfile.TemporaryDirectory(prefix="geometry-default-source-guards-") as directory:
            copied = Path(directory)
            for package in ("geometry-core/geometry_kernel", "geometry-core/modeling",
                            "geometry-app/geometry_app", "geometry-templates/woodworking/geometry_woodworking"):
                shutil.copytree(ROOT / package, copied / package, ignore=shutil.ignore_patterns("__pycache__"))
            (copied / "tests").mkdir()
            (copied / "tests/__init__.py").write_text("", encoding="utf-8")
            for name in ("test_geometry_kernel_runtime.py", "test_geometry_source_runtime.py"):
                shutil.copyfile(ROOT / "tests" / name, copied / "tests" / name)
            source = copied / "geometry-core/modeling/engine.py"
            original = source.read_text(encoding="utf-8")
            command = [sys.executable, "-I", "-B", "-c",
                "import sys,unittest;sys.path.insert(0,sys.argv.pop(1));unittest.main(module=None)", str(copied),
                "tests.test_geometry_kernel_runtime.KernelRuntimeTests.test_default_consumes_changed_typed_box_and_preserves_complete_candidate"]
            def run():
                return subprocess.run(command, cwd=copied, capture_output=True, text=True, timeout=30)
            baseline = run()
            self.assertEqual(0, baseline.returncode, baseline.stdout + baseline.stderr)
            mutations = (
                ("from .base import load_candidate", "from .base import load_base as load_candidate",
                 "default-must-not-load-legacy-snapshot"),
                ("native_loader=load_candidate,\n                              source_graph=True",
                 "native_loader=lambda *a, **kw: load_candidate(*a, **kw).legacy_snapshot,\n                              source_graph=False",
                 "default-must-not-build-literal-box"),
            )
            for before, after, marker in mutations:
                with self.subTest(marker=marker):
                    self.assertEqual(1, original.count(before))
                    source.write_text(original.replace(before, after), encoding="utf-8")
                    mutant = run()
                    details = mutant.stdout + mutant.stderr
                    self.assertEqual(1, mutant.returncode, details)
                    self.assertIn("Ran 1 test", details)
                    self.assertIn("FAILED (failures=1)", details)
                    self.assertIn(marker, details)
                    self.assertNotIn("ImportError", details)
                    self.assertNotIn("SyntaxError", details)
            source.write_text(original, encoding="utf-8")
            restored = run()
            self.assertEqual(0, restored.returncode, restored.stdout + restored.stderr)


if __name__ == "__main__":
    unittest.main()
