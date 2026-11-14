"""R363: R06 and the identity ledger share native save/replay and capability gates.

These are native behavior tests, not source-shape assertions.  The existing R06
fixture is composed without inheriting its test methods, so discovery runs each
old R06 test exactly once in its own registered suite.  Missing native binaries
remain skips and are never counted as mutation kills.
"""
from copy import deepcopy
from pathlib import Path
import secrets
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
for directory in (ROOT, ROOT / "geometry-core", ROOT / "geometry-web"):
    if str(directory) not in sys.path:
        sys.path.insert(0, str(directory))

from tests import test_assembly_bay_repeat as bay_fixture
from tests._bridge import BridgeSession
from modeling import ModelError
import scenario_verify


BAY = "assembly-bay-repeat/1"
IDENTITY = "identity-ledger/1"
AVAILABLE = frozenset(("engineering-spec/1", "parameters/1", "assembly-rule-authoring/1",
                       "assembly-timber-generation/1", BAY, "grid-subdivision-rules/1",
                       "grid-subdivision-rules/2", "section-profile/1", "grid-card-reference/1", IDENTITY, "definition-import/1"))


class R363CapabilityBounds(unittest.TestCase):
    def test_full_bridge_union_and_model_boundary(self):
        self.assertEqual(11, len(AVAILABLE), "R379_R363_EXACT_ELEVEN_CAPABILITIES")
        self.assertEqual(AVAILABLE, scenario_verify.BRIDGE_CAPABILITIES,
                         "R363_N01_VERIFIER_CAPABILITY_UNION")
        self.assertEqual(set(AVAILABLE), scenario_verify._capabilities(
            sorted(AVAILABLE), ("native", "capabilities"), supported=scenario_verify.BRIDGE_CAPABILITIES),
            "R363_N01_ALL_TEN_CAPABILITIES")
        for invalid in (sorted(AVAILABLE) + ["future/1"], [BAY, BAY], [IDENTITY, 1], None):
            with self.subTest(invalid=invalid), self.assertRaises(ModelError) as rejected:
                scenario_verify._capabilities(invalid, ("native", "capabilities"),
                                              supported=scenario_verify.BRIDGE_CAPABILITIES)
            self.assertEqual("SCENARIO_CAPABILITY", rejected.exception.code)
        for bridge_only in (BAY, IDENTITY, "definition-import/1", "grid-subdivision-rules/1", "grid-subdivision-rules/2"):
            with self.subTest(model_capability=bridge_only), self.assertRaises(ModelError) as rejected:
                scenario_verify._capabilities([bridge_only], ("models", "requiredCapabilities"))
            self.assertEqual("SCENARIO_CAPABILITY", rejected.exception.code,
                             "R363_N01_MODEL_ADAPTER_STAYS_NARROW")


class R363NativeMerge(unittest.TestCase):
    def setUp(self):
        self.h = bay_fixture.BayRepeat()
        self.addCleanup(self.h.doCleanups)
        self.h.setUp()

    def activate(self):
        epoch = self.h.command("identity-epoch " + secrets.token_hex(16))
        self.assertTrue(epoch.get("ok"), epoch)
        self.h.line("identity-ledger activate")
        identity = self.h.command("identity-read")
        self.assertTrue(identity.get("ok") and identity.get("active"), identity)
        return identity

    def mixed(self):
        self.h.apply([self.h.create()])
        self.activate()
        return self.h.dump()

    def test_bridge_and_candidate_advertise_both_capabilities(self):
        before = self.h.command("engineering-read")
        self.assertTrue(before.get("ok"), before)
        self.assertEqual(AVAILABLE, set(before["state"]["capabilities"]),
                         "R363_N02_BRIDGE_CAPABILITY_UNION")
        self.assertEqual(len(AVAILABLE), len(before["state"]["capabilities"]),
                         "R363_N02_BRIDGE_CAPABILITIES_NOT_DUPLICATED")
        self.assertNotIn("panel-fill/1", before["state"]["capabilities"],
                         "R363_N02_NO_FULL_PANEL_FILL_CLAIM")
        self.assertEqual(bay_fixture.LIMITS, {key: self.h.read()["state"]["limits"][key]
                                            for key in bay_fixture.LIMITS},
                         "R363_N02_R06_LIMITS_PRESERVED")
        scene = self.mixed()
        path = self.h.directory / "mixed-capabilities.scene"
        path.write_text(scene, encoding="utf-8", newline="\n")
        state = self.h.command("engineering-read")["state"]
        required = {line.split()[1] for line in scene.splitlines() if line.startswith("requires ")}
        self.assertTrue({BAY, IDENTITY, "assembly-timber-generation/1"}.issubset(required),
                        "R363_N02_MIXED_SCENE_REQUIRES")
        self.assertEqual(required, set(state["required_capabilities"]),
                         "R363_N02_LIVE_REQUIRED_UNION")
        candidate = self.h.command("load-prepare " + str(path))
        self.assertTrue(candidate.get("ok"), candidate)
        self.assertEqual(AVAILABLE, set(candidate["capabilities"]),
                         "R363_N02_CANDIDATE_AVAILABLE_UNION")
        self.assertEqual(required, set(candidate["required_capabilities"]),
                         "R363_N02_CANDIDATE_REQUIRED_UNION")
        self.assertEqual(scene, candidate["final_scene"])
        self.assertTrue(self.h.command("load-cancel " + str(candidate["token"]))["cancelled"])

    def test_dump_keeps_bay_and_identity_and_deidentified_keeps_bay(self):
        self.h.apply([self.h.create()])
        inactive = self.h.dump()
        self.activate()
        complete = self.h.dump()
        self.assertEqual(1, complete.splitlines().count("requires " + BAY),
                         "R363_N03_BAY_DUMP_REQUIREMENT")
        self.assertEqual(1, complete.splitlines().count("requires " + IDENTITY),
                         "R363_N03_IDENTITY_DUMP_REQUIREMENT")
        self.assertEqual(inactive, self.h.command("dump-deidentified")["text"],
                         "R363_N03_DEIDENTIFIED_BYTES")
        owned = {row["timberId"] for row in self.h.instance()["value"]["mapping"]}
        marks = self.h.command("identity-read")["marks"]
        self.assertEqual({("boundary", 1), ("placement", 1), ("timber", 90), ("timber", 91)},
                         {(row["kind"], row["id"]) for row in marks},
                         "R363_N03_ONLY_COVERED_KEYS_MARKED")
        self.assertFalse(owned & {row["id"] for row in marks if row["kind"] == "timber"},
                         "R363_N03_OWNED_TIMBERS_EXCLUDED")

    def test_mixed_scene_roundtrip_and_stripped_requirements_reject_atomically(self):
        scene = self.mixed()
        before = self.h.command("identity-read")
        assembly = self.h.read()["state"]
        path = self.h.directory / "mixed-roundtrip.scene"
        path.write_text(scene, encoding="utf-8", newline="\n")
        with BridgeSession(self.h.binary, cwd=self.h.directory) as fresh:
            serial = fresh.command("identity-read")["nextSerial"]
            loaded = fresh.command("loadfile " + str(path))
            self.assertTrue(loaded.get("ok"), "R363_N04_MIXED_REPLAY " + repr(loaded))
            self.assertEqual(scene, fresh.command("dump")["text"], "R363_N04_DUMP_ROUNDTRIP")
            restored = fresh.command("identity-read")
            self.assertEqual(before["marks"], restored["marks"], "R363_N04_MARKS_ROUNDTRIP")
            self.assertEqual(serial, restored["nextSerial"], "R363_N04_REPLAY_DOES_NOT_ALLOCATE")
            self.assertEqual(assembly, fresh.command("assembly-read")["state"],
                             "R363_N04_BAY_MAPPING_ROUNDTRIP")
            for capability in (BAY, IDENTITY, "future/1"):
                invalid = (scene + "requires future/1\n" if capability == "future/1"
                           else scene.replace("requires " + capability + "\n", ""))
                path.write_text(invalid, encoding="utf-8", newline="\n")
                rejected = fresh.command("loadfile " + str(path))
                self.assertFalse(rejected.get("ok"), "R363_N04_CAPABILITY_FAIL_CLOSED " + capability)
                self.assertEqual(scene, fresh.command("dump")["text"], "R363_N04_REJECTION_ATOMIC")
                self.assertEqual(restored, fresh.command("identity-read"))

    def test_bay_candidate_settlement_keeps_existing_marks_and_serial(self):
        before = self.activate()
        preview = self.h.request([self.h.create()])
        self.assertTrue(preview["valid"], preview)
        self.assertEqual(before, self.h.command("identity-read"), "R363_N05_PREVIEW_NO_MARKS")
        accepted = self.h.command("assembly-confirm " + str(preview["token"]))
        self.assertTrue(accepted.get("ok"), accepted)
        self.assertEqual(before, self.h.command("identity-read"),
                         "R363_N05_OWNED_CREATION_DOES_NOT_ALLOCATE")
        old_scene = self.h.dump()
        old_mapping = bay_fixture.mapping(self.h.instance())
        candidate = self.h.request([self.h.edit(self.h.insert())])
        self.assertTrue(candidate["valid"], candidate)
        self.assertEqual(before, self.h.command("identity-read"), "R363_N05_EDIT_PREVIEW_NO_MARKS")
        self.assertTrue(self.h.command("assembly-confirm " + str(candidate["token"]))["ok"])
        self.assertNotEqual(old_mapping, bay_fixture.mapping(self.h.instance()))
        self.assertEqual(before, self.h.command("identity-read"), "R363_N05_REPLACEMENT_NO_MARKS")
        self.h.line("undo")
        self.assertEqual(old_scene, self.h.dump(), "R363_N05_UNDO_RESTORES_BOTH_FEATURES")
        self.assertEqual(before, self.h.command("identity-read"))

    def test_scenario_verification_accepts_complete_mixed_scene(self):
        scene = self.mixed()
        required = sorted({line.split()[1] for line in scene.splitlines() if line.startswith("requires ")})
        value = {"manifest": {"requiredCapabilities": required, "faces": [], "faceProjections": [],
                              "reconstructionReviews": [], "models": []}, "scene": scene}
        original = deepcopy(value)
        receipt = scenario_verify.verify_project(value, bridge_executable=self.h.binary)
        self.assertTrue(receipt.get("ok"), "R363_N06_SCENARIO_MIXED_ACCEPTANCE")
        self.assertEqual(AVAILABLE, set(receipt["capabilities"]), "R363_N06_SCENARIO_CAPABILITY_UNION")
        self.assertEqual(required, receipt["requiredCapabilities"])
        self.assertEqual(scene, receipt["final_scene"], "R363_N06_SCENARIO_FULL_IDENTITY_BYTES")
        self.assertEqual(value, original)


if __name__ == "__main__":
    unittest.main()
