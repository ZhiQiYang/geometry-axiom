"""L12: real native content, model/scenario boundaries, and rule-case receipts.

The #49 probe injects activation into its real private child after reset. It
does not fabricate native replies, replace allocation, or bypass freshness.
Browser-owned capture/recovery is covered separately by the Node contract.
"""
from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path
import secrets
import sys
import tempfile
import unittest
import urllib.error
import urllib.request
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
for directory in (ROOT, ROOT / "geometry-core", ROOT / "geometry-web"):
    if str(directory) not in sys.path:
        sys.path.insert(0, str(directory))

from tests import _bridge, binaries
from modeling import ModelError, canonical_bytes
from modeling.base import load_base
from rule_cases.catalog import case
from rule_cases import executor
import model_update
import scenario_verify
import space_modeling

CAPABILITY = "identity-ledger/1"
SCENE = ("boundary 1 outline 0,0 4000,0 4000,3000 0,3000 kind room_plan\n"
         "placement 1 on boundary 1 origin 0 0 2500 u +x v +y\n"
         "timber 5 27 33 role boundary\nplace 5 on 1 at-face e0 +u +n\n")


def sha(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


class IdentityContentContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.bridge = _bridge.find_bridge()
        info = binaries.inspect_one(binaries.BY_NAME["model-base"],
                                    path=os.environ.get("GEOMETRY_MODEL_BASE"))
        if info.state != "fresh":
            raise RuntimeError("L12 requires a fresh model-base: " + info.reason)
        cls.base = str(info.path)
        with tempfile.TemporaryDirectory(prefix="identity-content-") as name:
            source = Path(name) / "source.scene"
            source.write_text(SCENE, encoding="utf-8", newline="\n")
            with _bridge.BridgeSession(cls.bridge, cwd=name) as native:
                for command in ("loadfile " + str(source),):
                    reply = native.command(command)
                    if reply.get("ok") is not True:
                        raise AssertionError((command, reply))
                cls.inactive = native.command("dump")["text"]
                cls.inactive_capabilities = native.command("engineering-read")["state"]
                for command in ("identity-epoch " + secrets.token_hex(16),
                                "line identity-ledger activate"):
                    reply = native.command(command)
                    if reply.get("ok") is not True:
                        raise AssertionError((command, reply))
                cls.active = native.command("dump")["text"]
                cls.deidentified = native.command("dump-deidentified")["text"]
                cls.active_capabilities = native.command("engineering-read")["state"]
                cls.marks = native.command("identity-read")["marks"]
        cls.record = cls.make_record(cls.inactive)

    @classmethod
    def make_record(cls, text):
        base = load_base(text, executable=cls.base)
        inputs = {"mode": "plan", "base_scene": base["base_scene"], "placement_id": 1,
                  "obstacles": [], "timbers": [{"kind": "timber", "id": 5}],
                  "settings": {"bottom": 0, "height": 3000, "edges": [0, 1, 2, 3],
                               "floor": "boundary", "ceiling": "boundary",
                               "holes": "none", "wall_thickness": 100}}
        result = space_modeling.preview(inputs, base_executable=cls.base)
        return {"id": "identity-content", "name": "Identity content boundary",
                "created_at": "2026-11-03T00:00:00Z",
                "source": {"kind": "scene", "placement_id": 1, "boundary_id": 1,
                           "scene_hash": result["source_sha256"]},
                "input": inputs, "result": result}

    def project(self, *, model=True):
        return {"scene": self.active,
                "manifest": {"sceneHash": sha(self.active),
                             "requiredCapabilities": [CAPABILITY], "faces": [],
                             "faceProjections": [], "reconstructionReviews": [],
                             "models": [deepcopy(self.record)] if model else []}}

    def test_L12_bridge_and_model_capability_gates_are_distinct(self):
        self.assertIn(CAPABILITY, scenario_verify.BRIDGE_CAPABILITIES,
                      "L12_BRIDGE_CAPABILITY_PRESENT")
        self.assertNotIn(CAPABILITY, scenario_verify.NATIVE_CAPABILITIES,
                         "L12_MODEL_CAPABILITY_MUST_NOT_BE_WIDENED")
        with self.assertRaises(ModelError) as caught:
            scenario_verify._capabilities([CAPABILITY], ("models", "requiredCapabilities"))
        self.assertEqual((caught.exception.status, caught.exception.code),
                         ("UNSUPPORTED", "SCENARIO_CAPABILITY"))
        self.assertEqual(scenario_verify._capabilities([CAPABILITY], ("manifest",),
                         supported=scenario_verify.BRIDGE_CAPABILITIES), {CAPABILITY})
        for state in (self.inactive_capabilities, self.active_capabilities):
            self.assertIn(CAPABILITY, state["capabilities"],
                          "L12_FIXED_NATIVE_CAPABILITY_PRESENT")
        self.assertNotIn(CAPABILITY, self.inactive_capabilities["required_capabilities"])
        self.assertIn(CAPABILITY, self.active_capabilities["required_capabilities"])

    def test_L12_activation_keeps_D25_packages_and_summary_byte_identical(self):
        self.assertEqual(self.deidentified, self.inactive, "L12_NATIVE_PLAIN_BYTES")
        self.assertNotEqual(self.active, self.inactive)
        self.assertTrue(self.marks)
        regenerated = self.make_record(self.deidentified)
        self.assertEqual(canonical_bytes(regenerated), canonical_bytes(self.record),
                         "L12_D25_PACKAGES_AND_SUMMARY_IGNORE_MARKS")
        self.assertEqual(regenerated["result"]["summary"]["timber_volume_mm3"],
                         str(4000 * 27 * 33))
        self.assertNotIn("identity-ledger", regenerated["input"]["base_scene"])
        self.assertNotIn(b"identity-ledger", canonical_bytes(regenerated["result"]))

    def test_L12_complete_scenario_retains_marks_and_verified_model_is_deidentified(self):
        project = self.project()
        before = canonical_bytes(project)
        receipt = scenario_verify.verify_project(project, bridge_executable=self.bridge,
                                                  base_executable=self.base)
        self.assertTrue(receipt["ok"], "L12_ACTIVATED_SCENARIO_VERIFIED")
        self.assertEqual(receipt["scene_sha256"], project["manifest"]["sceneHash"])
        self.assertEqual(receipt["final_scene"], self.active,
                         "L12_SCENARIO_FINAL_SCENE_RETAINS_MARKS")
        self.assertNotEqual(receipt["scene_sha256"], sha(self.deidentified))
        self.assertEqual(canonical_bytes(project), before, "L12_VERIFIER_DOES_NOT_REWRITE_SNAPSHOT")
        self.assertNotIn("identity-ledger", project["manifest"]["models"][0]["input"]["base_scene"])

    def test_L12_identity_bearing_model_source_is_rejected_by_real_replay(self):
        bad = self.project()
        bad["manifest"]["models"][0]["input"]["base_scene"] = self.active
        before = canonical_bytes(bad)
        with self.assertRaises(ModelError) as caught:
            scenario_verify.verify_project(bad, bridge_executable=self.bridge,
                                            base_executable=self.base)
        self.assertEqual((caught.exception.status, caught.exception.code),
                         ("UNSUPPORTED", "CAPABILITY"), "L12_MODEL_SOURCE_IDENTITY_REJECTED")
        self.assertEqual(canonical_bytes(bad), before)

    def test_L12_model_update_graphs_receive_only_the_real_deidentified_source(self):
        request = {"record": deepcopy(self.record), "current_scene": self.deidentified,
                   "selection": {"placement_id": 1, "boundary_id": 1, "edges": [0, 1, 2, 3],
                                 "obstacles": [], "timbers": [{"kind": "timber", "id": 5}],
                                 "projection": None}}
        seen = []
        native_graph = model_update._graph
        def capture(text, program):
            seen.append(text)
            return native_graph(text, program)
        with mock.patch.object(model_update, "_graph", side_effect=capture):
            result = model_update.prepare_update(request, base_executable=self.base,
                                                  bridge_executable=self.bridge)
        self.assertTrue(result["ok"])
        self.assertEqual(seen, [self.record["input"]["base_scene"], self.deidentified],
                         "L12_BOTH_UPDATE_GRAPH_INPUTS_DEIDENTIFIED")
        self.assertTrue(all("identity-ledger" not in text for text in seen))
        self.assertEqual(result["record"], self.record)
        self.assertEqual(result["current_scene_sha256"], sha(self.inactive))

    def test_L12_rule_case_hashes_use_deidentified_dump_in_an_actual_active_child(self):
        definition = case("legal-rule")
        native_executor = executor.NativeExecutor(self.bridge)
        plain = native_executor.run(definition, project_id="identity-content", generation=0)
        self.assertEqual(plain["status"], "passed", plain)
        observations, activations = [], []
        native_child = executor._Child
        class ActiveChild(native_child):
            def command(self, text):
                reply = super().command(text)
                if text == "reset" and reply.get("ok") is True:
                    for command in ("identity-epoch " + secrets.token_hex(16),
                                    "line identity-ledger activate"):
                        activated = super().command(command)
                        if activated.get("ok") is not True:
                            raise AssertionError((command, activated))
                    activations.append(super().command("identity-read"))
                if text in ("dump", "dump-deidentified"):
                    full = super().command("dump")["text"]
                    bare = super().command("dump-deidentified")["text"]
                    observations.append((text, full, bare))
                return reply
        with mock.patch.object(executor, "_Child", ActiveChild):
            active = native_executor.run(definition, project_id="identity-content", generation=0)
        self.assertEqual(active["status"], "passed", active)
        self.assertEqual(len(activations), 1)
        self.assertTrue(activations[0]["active"])
        self.assertEqual(len(observations), 2)
        for key, (command, full, bare) in zip(("beforeDumpHash", "afterDumpHash"), observations):
            self.assertIn("requires identity-ledger/1\n", full)
            self.assertNotEqual(full, bare)
            self.assertEqual(command, "dump-deidentified", "L12_RULE_CASE_DEIDENTIFIED_COMMAND")
            self.assertEqual(active["observations"][key], sha(bare), "L12_RULE_CASE_HASH_" + key)
            self.assertEqual(active["observations"][key], plain["observations"][key])
            self.assertNotEqual(active["observations"][key], sha(full))

    def test_L12_stale_host_allows_deidentified_read_and_blocks_new_writes(self):
        # This one test exercises the actual HTTP routing/freshness gate with
        # the existing controlled pipe fixture. Native semantics above use the
        # real bridge; this routing test is not a second native execution claim.
        from tests.test_serve import BridgeServerTests
        fixture = BridgeServerTests()
        fixture.setUp()
        self.addCleanup(fixture.tearDown)
        with mock.patch.object(fixture.server_module.RUNTIME, "fresh", return_value=False), fixture.http_server() as base:
            write = urllib.request.Request(base + "/api", data=b'{"cmd":"line timber 9 27 33 role primary"}',
                                           headers={"Content-Type": "application/json"})
            with self.assertRaises(urllib.error.HTTPError) as caught:
                urllib.request.urlopen(write, timeout=3)
            self.assertEqual(caught.exception.code, 409, "L12_STALE_HOST_WRITES_REJECTED")
            caught.exception.close()
            self.assertEqual(fixture.process.stdin.getvalue(), b"")
            expected = {"ok": True, "text": self.deidentified}
            fixture.responses.put(json.dumps(expected).encode() + b"\n")
            read = urllib.request.Request(base + "/api", data=b'{"cmd":"dump-deidentified"}',
                                          headers={"Content-Type": "application/json"})
            try:
                with urllib.request.urlopen(read, timeout=3) as response:
                    self.assertEqual(response.status, 200)
                    self.assertEqual(json.load(response), expected)
            except urllib.error.HTTPError as error:
                error.close()
                self.fail("L12_STALE_HOST_MUST_ALLOW_DEIDENTIFIED_DUMP: " + str(error.code))
            self.assertEqual(fixture.process.stdin.getvalue(), b"dump-deidentified\n")


if __name__ == "__main__":
    unittest.main(verbosity=2)
