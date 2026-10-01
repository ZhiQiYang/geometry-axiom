"""Actual native engineering sources through model packages and saved previews.

Set GEOMETRY_TEST_BRIDGE and GEOMETRY_MODEL_BASE to freshly built C
executables. Every world below belongs to a private subprocess, never a server.
"""
from copy import deepcopy
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "geometry-core"))
sys.path.insert(0, str(ROOT / "geometry-web"))
sys.path.insert(0, str(ROOT))
import modeling
from modeling import ModelError, build_package, verify_package
from modeling.base import load_base
from modeling.common import digest
from space_modeling import preview
from tests import _bridge
from tests.test_space_modeling import assert_exact_box


class EngineeringModelSources(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not os.environ.get("GEOMETRY_MODEL_BASE"):
            raise unittest.SkipTest("set GEOMETRY_MODEL_BASE to a freshly built model adapter executable")
        bridge = _bridge.find_bridge()
        with tempfile.TemporaryDirectory(prefix="engineering-model-source-") as directory:
            session = _bridge.BridgeSession(bridge)
            def command(text):
                result = session.command(text)
                if not result.get("ok"):
                    raise AssertionError(result)
                return result
            try:
                for line in ("reset", "line surface 1 origin 0 0 2500 u +x v +y outline 0,0 4000,0 4000,3000 0,3000",
                             "line timber 10 27 33 role boundary", "line place 10 on 1 at-face e0 +u +n"):
                    command(line)
                operations = [
                    {"op":"publish-material","value":{"id":"wood-a","version":1,"kind":"timber","name":"Boundary wood","A":30,"B":33}},
                    {"op":"publish-material","value":{"id":"unused-panel","version":1,"kind":"panel","name":"Unused catalogue panel","width":915,"length":1830,"thickness":"6.00"}},
                    {"op":"publish-method","value":{"id":"frame","version":1,"name":"Frame","roles":{"boundary":{"id":"wood-a","version":1}}}},
                    {"op":"put-application","value":{"id":"face-frame","placement_id":1,"method":{"id":"frame","version":1}}},
                    {"op":"bind-timber","id":10,"application":"face-frame","slot":"boundary"},
                ]
                request = {"schema":"engineering-transaction/1","expectedRevision":command("engineering-read")["revision"],"operations":operations}
                path = Path(directory) / "request.json"
                path.write_text(json.dumps(request), encoding="utf-8")
                candidate = command("engineering-preview " + str(path))
                if not candidate["preview"]["valid"]:
                    raise AssertionError(candidate)
                command("engineering-confirm " + str(candidate["preview"]["token"]))
                cls.scene = command("dump")["text"]
            finally:
                session.stop()
        cls.canonical = load_base(cls.scene)["base_scene"]
        cls.definitions = {"base_scene":cls.canonical,"extensions":[]}
        cls.request = {"roots":[{"kind":"timber","id":10}],"role":"geometry","target":"solid-set","allow_partial":False}

    def package(self):
        return build_package(self.definitions, self.request)

    def test_native_source_and_unused_published_catalogue_survive_canonical_model_export(self):
        package = self.package()
        self.assertIn("engineering-spec/1", package["manifest"]["capabilities"])
        self.assertEqual(package["definitions"]["base_scene"], self.canonical)
        self.assertEqual(sum(line.startswith("engineering material ") for line in self.canonical.splitlines()), 2)
        self.assertIn("engineering timber ", self.canonical)
        self.assertNotIn("timber 10 30 33", self.canonical)
        self.assertEqual(verify_package(package)["derived"], package["derived"])
        mesh = package["derived"]["objects"][0]
        self.assertEqual(mesh["closure"], "closed")
        self.assertEqual(mesh["volume_mm3"], str(4000 * 30 * 33))

    def test_missing_dependency_and_removed_capability_fail_without_literal_fallback(self):
        incomplete = deepcopy(self.definitions)
        incomplete["base_scene"] = "\n".join(line for line in self.canonical.splitlines() if not line.startswith("engineering material ")) + "\n"
        with self.assertRaises(ModelError):
            build_package(incomplete, self.request)
        package = self.package()
        package["manifest"]["capabilities"].remove("engineering-spec/1")
        with self.assertRaises(ModelError) as caught:
            verify_package(package)
        self.assertEqual(caught.exception.code, "CAPABILITY")
        package = self.package()
        package["manifest"]["axiom_revision"], package["manifest"]["axiom_sha256"] = next(iter(modeling.LEGACY_AXIOM_VERSIONS))
        with self.assertRaises(ModelError) as caught:
            verify_package(package)
        self.assertEqual(caught.exception.code, "AXIOM_VERSION")

    def test_native_engineering_source_has_exact_world_position_and_outward_faces(self):
        package = self.package()
        self.assertEqual(len(package["derived"]["objects"]), 1)
        obj = package["derived"]["objects"][0]
        self.assertEqual(obj["root"], {"kind": "timber", "id": 10})
        # Hand-derived from e0, +u/+n and the published 30×33 source, not from
        # adapter bbox/metadata or verify_package's replay of the same engine.
        assert_exact_box(self, obj, [[0, 0, 2500], [4000, 30, 2533]])
        for sources in obj["face_sources"]:
            self.assertTrue(sources)
            self.assertTrue(all(s["origin"] == obj["root"] and s["placement_id"] == 1 and s["boundary_id"] == 1 for s in sources))

    def test_saved_plan_height_replay_retains_fixed_engineering_timber_sources(self):
        source = {"base_scene":self.canonical,"mode":"plan","placement_id":1,"obstacles":[],"timbers":[{"kind":"timber","id":10}],
                  "settings":{"bottom":0,"height":2800,"edges":[0,1,2,3],"floor":"calculation-cap","ceiling":"calculation-cap","holes":"none","wall_thickness":None}}
        original = preview(source)
        changed = deepcopy(source); changed["settings"]["height"] = 3200
        higher = preview(changed)
        self.assertEqual(original["schema"], "geometry-space-preview/2")
        self.assertEqual(original["source_sha256"], higher["source_sha256"])
        for key in ("definitions", "request", "derived"):
            self.assertEqual(original["timbers"][key], higher["timbers"][key])
        self.assertEqual(original["summary"]["timber_volume_mm3"], str(4000 * 30 * 33))
        self.assertEqual(higher["summary"]["top"], 3200)
        for result in (original, higher):
            for key in ("space", "volume", "clearance", "timbers"):
                self.assertIn("engineering-spec/1", result[key]["manifest"]["capabilities"])
                self.assertEqual(verify_package(result[key])["derived"], result[key]["derived"])


if __name__ == "__main__":
    unittest.main()
