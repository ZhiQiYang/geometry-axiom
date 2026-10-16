"""Real C -> public default runtime integration; no simulated positive graph.

Requires explicit, registry-verified GEOMETRY_MODEL_BASE and (for finish) a
GEOMETRY_TEST_BRIDGE built from this checkout. This module never builds a native
binary. Missing configuration skips; stale configuration fails. A release gate
must require all eight tests with zero skips. The independent legacy runtime is
only a comparison oracle, never a fallback when the default runtime rejects.
"""
import base64
from copy import deepcopy
from hashlib import sha256
import json
import os
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
for directory in (ROOT, ROOT / "geometry-core"):
    if str(directory) not in sys.path:
        sys.path.insert(0, str(directory))

from modeling import ModelError
from modeling import base as public_base
from modeling.engine import evaluate as default_evaluate
import geometry_kernel as kernel
from geometry_app import model_native
from geometry_app.bootstrap import default_provider
from geometry_app.model_runtime import ModelingRuntime
from geometry_app.model_sources import decode_candidate
from tests import _bridge, binaries
from tests import test_geo261_model_sources as fixtures
from tests.test_geo261_grid_definitions_product import SCENE as GRID_SCENE
from tests.test_geo261_engineering_sources import engineering_product_scene
from tests import test_section_profile_modeling as profiles
from tests import test_panel_fill_host as panel_fill_host


MISSING_GROUPS = (
    "grid-fields-and-bindings", "material-source-overrides",
    "profile-definition-edges", "derived-region-provenance",
    "ordered-stop-features",
)
FROZEN = ROOT / "tests/fixtures/domain-decoupling-main-a898ad6e"


def reference(value):
    return value["namespace"], base64.b64decode(value["keyBase64"], validate=True)


def request(kind="timber", identifier=1, target="solid-set"):
    return {"roots": [{"kind": kind, "id": identifier}], "role": "geometry",
            "target": target, "allow_partial": False}


def definitions(scene):
    return {"base_scene": scene, "extensions": []}


def parameter_ast_scene():
    literal = lambda value: {"op": "literal", "num": str(value), "den": "1", "unit": "1"}
    ref = lambda field: {"op": "ref", "parameterId": 8, "fieldId": field}
    fields = [
        (3, 0, {"op": "mul", "left": ref(2), "right": ref(4)}),
        (2, 0, {"op": "mul", "left": ref(1), "right": literal(2)}),
        (1, 0, {"op": "literal", "num": "7", "den": "2", "unit": "mm"}),
        (4, 1, literal(3)),
        (5, 2, {"op": "literal", "num": "1", "den": "3", "unit": "1"}),
    ]
    rows = ["requires parameters/1", "parameters begin", "parameters card " +
            fixtures.encoded({"id": 8, "name": "typed graph", "nextFieldId": 6})]
    rows += ["parameters field " + fixtures.encoded({"parameterId": 8, "id": number,
        "name": str(number), "type": kind, "expression": expression})
        for number, kind, expression in fields]
    return "\n".join([*rows, "parameters end", ""])


class DefaultNativeIntegration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        configured = os.environ.get("GEOMETRY_MODEL_BASE")
        if not configured:
            raise unittest.SkipTest("Explicit fresh GEOMETRY_MODEL_BASE is required; no automatic build")
        cls.base = binaries.require_fresh("model-base", configured)

    def pin(self):
        self.assertEqual(self.base, binaries.require_fresh("model-base", self.base))
        identity = model_native._execution_identity(self.base)
        self.assertEqual(identity[0], identity[1], "Loaded and current source closures must match")
        self.assertEqual(sha256(Path(self.base).read_bytes()).hexdigest(), identity[2][2])
        return identity

    def setUp(self):
        self.identity = self.pin()

    def tearDown(self):
        self.assertEqual(self.identity, self.pin(), "Source or binary changed during this test")

    def capture(self, scene, *, admitted=True):
        """Capture an actual producer response, then compare the real loader."""
        before = self.pin()
        source_bytes = scene.encode("utf-8")
        with tempfile.TemporaryDirectory(prefix="geo261-default-native-") as directory:
            path = Path(directory) / "input.scene"
            path.write_bytes(source_bytes)
            result = subprocess.run([self.base, "--neutral-sources", str(path)],
                capture_output=True, timeout=30, check=False)
            self.assertEqual(source_bytes, path.read_bytes())
        self.assertEqual(0, result.returncode, result.stdout.decode("utf-8", "replace") +
                         result.stderr.decode("utf-8", "replace"))
        self.assertEqual(before, self.pin())
        envelope = json.loads(result.stdout)
        self.assertIs(envelope["ok"], True)
        bundle = envelope["neutralSources"]
        self.assertEqual({"complete": True, "rootsComplete": True, "missingGroups": []},
                         bundle["coverage"], "Only genuine complete native output is admissible")
        digest = sha256(source_bytes).hexdigest()
        self.assertEqual({"sha256Before": digest, "sha256After": digest}, envelope["source"])
        self.assertEqual(sha256(envelope["legacySnapshot"]["base_scene"].encode()).hexdigest(),
                         envelope["candidate"]["id"])
        self.assertEqual(envelope["candidate"], bundle["candidate"])
        nodes = {reference(node["ref"]): node for node in bundle["nodes"]}
        self.assertEqual(len(nodes), len(bundle["nodes"]))
        providers = {provider["namespace"] for provider in bundle["providers"]}
        self.assertEqual(len(providers), len(bundle["providers"]))
        self.assertTrue(all(key[0] in providers for key in nodes))
        for edge in bundle["edges"]:
            self.assertIn(reference(edge["consumer"]), nodes)
            self.assertIn(reference(edge["source"]), nodes)
        for root in bundle["roots"]:
            self.assertEqual("ok", nodes[reference(root["ref"])]["status"])
        candidate = decode_candidate(result.stdout, source_bytes=source_bytes,
                                     execution_identity=before)
        if admitted:
            self.assertEqual(candidate, model_native.load_candidate(scene, executable=self.base))
        self.assertEqual(before, self.pin())
        return envelope, candidate, nodes

    @staticmethod
    def edges(envelope):
        return {(reference(edge["consumer"]), reference(edge["source"]), edge["kind"])
                for edge in envelope["neutralSources"]["edges"]}

    def evaluate_default(self, source_definitions, req):
        """Observe the actual loader and K call without replacing native output."""
        candidates, snapshots = [], []
        real_loader = public_base.load_candidate

        def observe_loader(*args, **kwargs):
            candidate = real_loader(*args, **kwargs)
            candidates.append(candidate)
            snapshots.append(deepcopy(candidate.legacy_snapshot))
            return candidate

        with mock.patch.object(public_base, "load_candidate", side_effect=observe_loader) as loader, \
             mock.patch.object(public_base, "load_base", side_effect=AssertionError("actual-default-must-not-load-legacy-snapshot")), \
             mock.patch.object(kernel, "evaluate", wraps=kernel.evaluate) as evaluator:
            result = default_evaluate(source_definitions, req, base_executable=self.base)
        loader.assert_called_once_with(source_definitions["base_scene"], executable=self.base)
        self.assertEqual(1, len(candidates), "actual-default-must-load-one-typed-candidate")
        self.assertEqual(1, evaluator.call_count, "actual-default-must-evaluate-one-typed-program")
        candidate, program = candidates[0], evaluator.call_args.args[0]
        self.assertEqual(candidate.snapshot_identity, program.snapshot_identity)
        self.assertEqual(tuple(source.key for source in candidate.sources),
                         tuple(source.key for source in program.sources))
        self.assertEqual(tuple((source.value_type, source.context, source.dependencies, source.status)
                               for source in candidate.sources),
                         tuple((source.value_type, source.context, source.dependencies, source.status)
                               for source in program.sources))
        self.assertEqual(snapshots[0], candidate.legacy_snapshot)
        return result

    def compare_default(self, source_definitions, req):
        original = deepcopy((source_definitions, req))
        result = self.evaluate_default(source_definitions, req)
        legacy = ModelingRuntime(provider=default_provider(), native_loader=model_native.load_base,
                                 source_graph=False).evaluate(source_definitions, req, base_executable=self.base)
        self.assertEqual(legacy, result)
        self.assertEqual(original, (source_definitions, req))
        return result

    def reject_wire(self, envelope, scene, code):
        with self.assertRaises(ModelError) as caught:
            decode_candidate(json.dumps(envelope).encode(), source_bytes=scene.encode(),
                             execution_identity=self.identity)
        self.assertEqual(("UNSUPPORTED", code, "I32"),
                         (caught.exception.status, caught.exception.code, caught.exception.clause))

    def test_five_frozen_packages_use_the_unmocked_public_default(self):
        for name in ("profile", "finite-grid", "infinite-grid", "stagger", "parameter"):
            with self.subTest(package=name):
                input_path, output_path = FROZEN / (name + ".input.json"), FROZEN / (name + ".json")
                input_bytes, output_bytes = input_path.read_bytes(), output_path.read_bytes()
                original, frozen = json.loads(input_bytes), json.loads(output_bytes)
                envelope, _, _ = self.capture(original["definitions"]["base_scene"])
                actual = self.evaluate_default(original["definitions"], original["request"])
                for field in ("definitions", "request", "derived", "diagnostics"):
                    self.assertEqual(frozen[field], actual[field], name + ": " + field)
                self.assertEqual(sorted(envelope["legacySnapshot"].get("required_capabilities", [])),
                                 sorted(actual["required_capabilities"]))
                self.assertEqual(input_bytes, input_path.read_bytes())
                self.assertEqual(output_bytes, output_path.read_bytes())

    def test_actual_boxes_parameters_ast_and_ordered_stop_edges(self):
        scene = fixtures.SCENE + parameter_ast_scene()
        envelope, _, nodes = self.capture(scene)
        roots, edges = envelope["neutralSources"]["roots"], self.edges(envelope)
        root = next(root for root in roots if root["kind"] == "timber")
        self.assertEqual(([0, 0, 0], [1000, 40, 50]),
                         (nodes[reference(root["ref"])]["value"]["lo"], nodes[reference(root["ref"])]["value"]["hi"]))
        self.assertEqual(["A0", "A1", "B0", "B1", "START", "END"],
                         [face["legacyFeature"] for face in root["faces"]])
        self.assertEqual([(2, 0), (2, 1), (1, 0), (1, 1), (0, 0), (0, 1)],
                         [(face["axis"], face["side"]) for face in root["faces"]])
        self.assertEqual(6, len({face["featureKeyBase64"] for face in root["faces"]}))
        core = lambda number: ("core.parameter.field", struct.pack("=II", 8, number))
        expected = {1: ("dimension", "7", "2", "length"), 2: ("dimension", "7", "1", "length"),
                    3: ("dimension", "21", "1", "length"), 4: ("count", "3", "1", "scalar"),
                    5: ("ratio", "1", "3", "scalar")}
        for number, value in expected.items():
            self.assertEqual(value, tuple(nodes[core(number)]["value"][field]
                             for field in ("quantityType", "num", "den", "unit")))
        self.assertEqual({(core(3), core(2), "value-required"), (core(3), core(4), "value-required"),
                          (core(2), core(1), "value-required")},
                         {edge for edge in edges if edge[0][0] == edge[1][0] == "core.parameter.field"
                          and edge[2] == "value-required"})
        for number in expected:
            self.assertEqual({(core(number), ("core.parameter.definition", struct.pack(">III", 2, 8, number)),
                               "definition-required")},
                             {edge for edge in edges if edge[0] == core(number)
                              and edge[2] == "definition-required"})
        for parameter in (root for root in roots if root["kind"] == "parameter"):
            self.assertIn((reference(parameter["ref"]), core(parameter["memberId"]), "value-required"), edges)
        placement = ("core.placement", bytes([2]) + struct.pack(">I", 1))
        self.assertIn((placement, ("core.region", struct.pack(">I", 1)), "value-required"), edges)
        features = {key: node for key, node in nodes.items()
                    if key[0] == "wood.contact" and node["descriptor"]["valueType"] == "feature"}
        self.assertEqual({((0, 0, 0), (0, 1000, 0)), ((1000, 0, 0), (1000, 1000, 0))},
                         {tuple(map(tuple, node["value"]["segment"])) for node in features.values()})
        self.assertTrue(any(a[0] == "woodworking.member.pose" and b in features and kind == "value-required"
                            for a, b, kind in edges))
        for key, node in features.items():
            self.assertEqual(24, len(base64.b64decode(node["value"]["keyBase64"], validate=True)))
            self.assertTrue(any(a == key and b[0] == "wood.contact" and b[1][0] == 1 and kind == "value-required"
                                for a, b, kind in edges))
        result = self.compare_default(definitions(scene), request())
        self.assertEqual("2000000", result["derived"]["objects"][0]["volume_mm3"])

    def test_placed_unplaced_and_zero_member_profile_definitions(self):
        for placed in (False, True):
            with self.subTest(placed=placed):
                scene = fixtures.profile_scene(placed)
                envelope, _, nodes = self.capture(scene)
                roots = envelope["neutralSources"]["roots"]
                frames = {root["id"]: nodes[reference(root["ref"])]["value"] for root in roots
                          if root["slot"] == "profile.frame" and root["memberId"] is None}
                self.assertEqual("local", frames[2]["coordinateDomain"])
                if placed:
                    self.assertEqual({"origin": [1000, 2000, 2700], "u": [1, 0, 0], "v": [0, 0, -1],
                                      "n": [0, 1, 0], "coordinateDomain": "world", "owner": None}, frames[1])
                else:
                    self.assertEqual("local", frames[1]["coordinateDomain"])
                    self.assertNotEqual(frames[1]["owner"], frames[2]["owner"])
                self.assertTrue(any(a[0] == b[0] == "wood.section-profile" and kind == "definition-required"
                                    for a, b, kind in self.edges(envelope)))
                inactive_frame = ("wood.section-profile", bytes([8]) + struct.pack(">I", 2))
                self.assertEqual("unevaluated", nodes[inactive_frame]["status"])
                self.assertIsNone(nodes[inactive_frame]["value"])
                self.assertTrue(any(b == inactive_frame and kind == "definition-required"
                                    for _, b, kind in self.edges(envelope)))
                self.compare_default(definitions(scene), profiles.request(1, 2))
        scene = profiles.scene(profiles=[profiles.profile(), profiles.profile(2)], members=[], runs=[profiles.run()])
        self.capture(scene)
        result = self.compare_default(definitions(scene), profiles.request())
        self.assertEqual(2, result["definitions"]["base_scene"].count("section-profile profile "))
        self.assertEqual(1, len(result["derived"]["objects"]))
        obj = result["derived"]["objects"][0]
        self.assertEqual("84960000", obj["volume_mm3"])
        self.assertEqual("0", obj["section_profile"]["material_volume_mm3"])

    def test_grid_definitions_vertex_bindings_and_material_override_values(self):
        envelope, _, nodes = self.capture(GRID_SCENE)
        grid = lambda kind, number: ("wood.grid", bytes([kind]) + struct.pack(">I", number) + bytes(59))
        edges = self.edges(envelope)
        for kind, number, schema in ((1, 2, "wood.grid.system/1"), (3, 3, "wood.grid.binding/1"),
                (5, 4, "wood.grid.application/1"), (5, 5, "wood.grid.application/1"), (5, 6, "wood.grid.application/1")):
            self.assertEqual(schema, nodes[grid(kind, number)]["value"]["schema"])
        self.assertIn((grid(5, 6), grid(5, 5), "definition-required"), edges)
        ledger = ("core.region-key", struct.pack(">4I", 1, 1, 0, 0))
        self.assertEqual(struct.pack(">8I", 1, 5, 1, 4, 1, 2, 3, 4),
                         base64.b64decode(nodes[ledger]["value"]["contentBase64"], validate=True))
        self.assertIn((grid(3, 3), ledger, "definition-required"), edges)
        for axis, value in enumerate((10, 20)):
            coordinate = ("core.region-key", struct.pack(">4I", 2, 1, 1, axis))
            self.assertEqual(str(value), nodes[coordinate]["value"]["num"])
            self.assertIn((grid(4, 3), coordinate, "value-required"), edges)
            self.assertIn((coordinate, ledger, "definition-required"), edges)
        self.compare_default(definitions(GRID_SCENE), request("placement", target="surface-set"))
        original = engineering_product_scene()
        for override, width in ((None, 30), ({"kind": "literal", "value": 17}, 17)):
            with self.subTest(override=override):
                rows = original.splitlines()
                index = next(i for i, line in enumerate(rows) if line.startswith("engineering timber "))
                timber = json.loads(base64.b64decode(rows[index].split()[2]))
                timber["A"]["override"] = override
                rows[index] = "engineering timber " + fixtures.encoded(timber)
                scene = "\n".join([*rows, ""])
                envelope, _, nodes = self.capture(scene)
                edges = self.edges(envelope)
                material = {key for key, node in nodes.items() if node["value"] is not None and
                            node["value"].get("schema") == "woodworking.material-version/1"}
                self.assertEqual(1, len(material))
                material_key = next(iter(material))
                content = json.loads(base64.b64decode(nodes[material_key]["value"]["contentBase64"], validate=True))
                self.assertEqual({"id": "t", "version": 1, "kind": "timber", "name": "Member", "A": 30, "B": 40}, content)
                binding = ("woodworking.dimension-binding", bytes([2]) + struct.pack(">4I", 1, 1, 0, 0))
                binding_definition = ("woodworking.dimension-binding", bytes([1]) + struct.pack(">4I", 1, 1, 0, 0))
                material_definition = ("core.version", struct.pack(">BIII", 1, 2, 1, 0) + b"\x01t")
                material_a = ("core.version", struct.pack(">BIII", 2, 2, 1, 2) + b"\x01t")
                quantity = {"num": str(width), "den": "1", "unit": "length", "quantityType": "dimension"}
                self.assertEqual(quantity, nodes[binding]["value"])
                self.assertEqual({**quantity, "num": "30"}, nodes[material_a]["value"])
                self.assertEqual("geometry.version/1", nodes[material_definition]["value"]["schema"])
                self.assertIn((binding, binding_definition, "definition-required"), edges)
                self.assertIn((material_a, material_definition, "definition-required"), edges)
                self.assertTrue(any(a[0] == "woodworking.dimension-source" and b == material_a and kind == "value-required"
                                    for a, b, kind in edges))
                active_sources = {b for a, b, kind in edges if a == binding and
                                  b[0] == "woodworking.dimension-source" and kind == "value-required"}
                self.assertEqual({30, width}, {int(nodes[key]["value"]["num"]) for key in active_sources})
                self.assertTrue(any(a[0] == "woodworking.dimension-source" and b == material_key and kind == "definition-required"
                                    for a, b, kind in edges))
                self.assertTrue(any(key[0] == "woodworking.dimension-source" and node["value"] is not None and
                                    node["value"].get("num") == "30" for key, node in nodes.items()))
                result = self.compare_default(definitions(scene), request())
                self.assertEqual(str(1000 * width * 40), result["derived"]["objects"][0]["volume_mm3"])

    def test_actual_finish_policy_graph_preserves_existing_capability_refusal(self):
        configured = os.environ.get("GEOMETRY_TEST_BRIDGE")
        if not configured:
            self.skipTest("Explicit fresh GEOMETRY_TEST_BRIDGE is required for the finish fixture")
        bridge_path = binaries.require_fresh("bridge", configured)
        bridge_hash = sha256(Path(bridge_path).read_bytes()).hexdigest()
        with tempfile.TemporaryDirectory(prefix="geo261-default-finish-") as directory:
            with _bridge.BridgeSession(bridge_path, cwd=directory) as bridge:
                fixture = panel_fill_host.PanelFillHost()
                fixture.bridge, fixture.directory = bridge, Path(directory)
                self.assertTrue(bridge.command("reset")["ok"])
                fixture.region()
                key = fixture.key([["e1", 0, 1]]).split(":")[1]
                self.assertTrue(bridge.command("line guide 1 10 v edge-key:" + key + ":u")["ok"])
                scene = bridge.command("dump")["text"]
        self.assertEqual(bridge_path, binaries.require_fresh("bridge", bridge_path))
        self.assertEqual(bridge_hash, sha256(Path(bridge_path).read_bytes()).hexdigest())
        envelope, _, nodes = self.capture(scene, admitted=False)
        finish = lambda kind, number: ("wood.finish", bytes([kind]) + struct.pack(">I", number))
        policy, edges = finish(21, 10), self.edges(envelope)
        self.assertEqual("wood.finish.derived-policy/1", nodes[policy]["value"]["schema"])
        for kind in (18, 19, 20):
            self.assertIn((policy, finish(kind, 10), "value-required"), edges)
        self.assertIn((policy, finish(22, 8), "definition-required"), edges)
        self.assertIn((finish(22, 8), finish(5, 8), "value-required"), edges)
        self.assertTrue(any(a[0] == "app.legacy-reference" and b == policy and kind == "definition-required"
                            for a, b, kind in edges))
        content = base64.b64decode(nodes[policy]["value"]["contentBase64"], validate=True)
        self.assertEqual(bytes([1]) + struct.pack(">I", 10) + bytes([0]) + struct.pack(">III", 1, 0, 4), content[:18])
        self.assertEqual(b'[["e0",0,1]]', content[21:21 + int.from_bytes(content[19:21], "big")])
        self.assertEqual(100, nodes["app.guide", struct.pack("=I", 1)]["value"]["coordinate"])
        original = definitions(scene)
        with self.assertRaises(ModelError) as caught:
            default_evaluate(original, request("placement", 10, "surface-set"), base_executable=self.base)
        self.assertEqual(("UNSUPPORTED", "CAPABILITY", "I32"),
                         (caught.exception.status, caught.exception.code, caught.exception.clause))
        self.assertEqual(definitions(scene), original)

    def test_actual_wire_rejects_incomplete_coverage_and_each_missing_group(self):
        envelope, _, _ = self.capture(fixtures.SCENE)
        for field in ("complete", "rootsComplete"):
            with self.subTest(flag=field):
                changed = deepcopy(envelope)
                changed["neutralSources"]["coverage"][field] = False
                self.reject_wire(changed, fixtures.SCENE, "BASE_SOURCE_COVERAGE")
        for group in MISSING_GROUPS:
            with self.subTest(group=group):
                changed = deepcopy(envelope)
                changed["neutralSources"]["coverage"]["missingGroups"] = [group]
                self.reject_wire(changed, fixtures.SCENE, "BASE_SOURCE_COVERAGE")

    def test_actual_wire_rejects_absent_nodes_dangling_edges_and_unknown_edge_kind(self):
        envelope, _, _ = self.capture(fixtures.SCENE)
        missing = deepcopy(envelope)
        root_ref = missing["neutralSources"]["roots"][0]["ref"]
        missing["neutralSources"]["nodes"] = [node for node in missing["neutralSources"]["nodes"] if node["ref"] != root_ref]
        dangling = deepcopy(envelope)
        present = {reference(node["ref"]) for node in dangling["neutralSources"]["nodes"]}
        unknown = deepcopy(dangling["neutralSources"]["edges"][0]["source"])
        key = b"absent-in-real-native-graph"
        while (unknown["namespace"], key) in present:
            key += b"!"
        unknown["keyBase64"] = base64.b64encode(key).decode()
        dangling["neutralSources"]["edges"][0]["source"] = unknown
        unknown_kind = deepcopy(envelope)
        unknown_kind["neutralSources"]["edges"][0]["kind"] = "unknown-required"
        for name, changed in (("missing-node", missing), ("dangling-edge", dangling), ("unknown-kind", unknown_kind)):
            with self.subTest(control=name):
                self.reject_wire(changed, fixtures.SCENE, "BASE_SOURCE_PROTOCOL")

    def test_source_and_binary_pins_follow_canonical_candidate_changes(self):
        original, candidate, _ = self.capture(fixtures.SCENE)
        moved, moved_candidate, _ = self.capture(fixtures.SCENE + "canvas-pos placement 1 31 29\n")
        changed, changed_candidate, nodes = self.capture(fixtures.SCENE.replace("spec x 500", "spec x 501"))
        self.assertEqual(original["candidate"], moved["candidate"])
        self.assertNotEqual(candidate.source_hash, moved_candidate.source_hash)
        self.assertNotEqual(original["candidate"], changed["candidate"])
        self.assertNotEqual(candidate.candidate_id, changed_candidate.candidate_id)
        self.assertEqual(501, nodes["app.guide", struct.pack("=I", 1)]["value"]["coordinate"])
        for result in (candidate, moved_candidate, changed_candidate):
            self.assertEqual(self.identity, result.execution_identity)
            self.assertEqual(self.identity[2][2], sha256(Path(self.base).read_bytes()).hexdigest())
        first = self.evaluate_default(definitions(fixtures.SCENE), request())
        second = self.evaluate_default(definitions(fixtures.SCENE + "canvas-pos placement 1 31 29\n"), request())
        self.assertEqual(first, second)


if __name__ == "__main__":
    unittest.main(verbosity=2)
