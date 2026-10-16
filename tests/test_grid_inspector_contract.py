"""Production compact-inspector declarations through the real native bridge.

The JS fixture executes saveSource; Python supplies independent declarations and
compares native objects, source tuples, segment geometry, history and new process
load. Actual DOM and full .gcanvas reopening are separate P72 browser gates.
"""
import copy
import json
import os
from pathlib import Path
import shutil
import subprocess
import unittest

from tests import _bridge
from tests import test_infinite_grid_contract as infinite
from tests.test_grid_system_contract import native_path

ROOT = Path(__file__).resolve().parents[1]


class GridInspectorContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        infinite.InfiniteGridContract.setUpClass.__func__(cls)
        cls.node = shutil.which("node")
        if not cls.node:
            raise unittest.SkipTest("node required to execute the production inspector serializer")

    setUp = infinite.InfiniteGridContract.setUp
    command = infinite.InfiniteGridContract.command
    line = infinite.InfiniteGridContract.line
    commit = infinite.InfiniteGridContract.commit
    dump = infinite.InfiniteGridContract.dump
    refs = infinite.InfiniteGridContract.refs
    objects = infinite.InfiniteGridContract.objects
    snapshot = infinite.InfiniteGridContract.snapshot
    preview = infinite.InfiniteGridContract.preview
    reject = infinite.InfiniteGridContract.reject
    boundary = infinite.InfiniteGridContract.boundary
    geometry = infinite.InfiniteGridContract.geometry
    fingerprint = infinite.InfiniteGridContract.fingerprint
    binding_command = infinite.InfiniteGridContract.binding_command
    binding = infinite.InfiniteGridContract.binding
    bindings = infinite.InfiniteGridContract.bindings
    query = infinite.InfiniteGridContract.query
    axis = infinite.InfiniteGridContract.axis
    band_segments = infinite.InfiniteGridContract.band_segments
    RECT = infinite.InfiniteGridContract.RECT

    def parameters(self, value=400):
        path = Path(self.directory.name) / "parameters.json"
        path.write_text(json.dumps({"schema": "engineering-transaction/1",
            "expectedRevision": self.command("engineering-read")["revision"],
            "operations": [{"op": "put-parameter", "value": {"id": 901, "name": "相位來源", "fields": [
                {"id": 1, "name": "正", "type": "dimension", "input": str(value)},
                {"id": 2, "name": "負", "type": "dimension", "input": "-400"},
            ]}}]}, ensure_ascii=False), encoding="utf-8")
        preview = self.command("engineering-preview " + native_path(path))
        self.assertTrue(preview["ok"] and preview["preview"]["valid"], preview)
        self.assertTrue(self.command("engineering-confirm " + str(preview["preview"]["token"]))["ok"])

    def rename(self, identifier=0, name="只改名稱", fields=None):
        source = next(o for o in self.objects()["gridSystems"] if o["id"] == identifier)
        result = subprocess.run([self.node, str(ROOT / "tests/fixtures/grid_inspector_command.cjs")],
            input=json.dumps({"object": source, "name": name, "fields": fields or {}}, ensure_ascii=False),
            text=True, encoding="utf-8", capture_output=True, check=True, env=os.environ.copy())
        return json.loads(result.stdout)["line"]

    def test_six_rename_shapes_preserve_sources_segments_and_cancel_history(self):
        self.parameters()
        cases = [
            ("repeat 0 600 stagger 400", "repeat 0 400"),
            ("repeat 0 600", "repeat 0 600 stagger -400"),
            ("repeat 0 600 stagger -400", "repeat-panel 400 gap 5 from -100 stagger 200"),
            ("repeat-panel 400 gap 5 from -100 stagger param:901:1", "repeat 0 600"),
            ("repeat 0 600", "repeat-panel 400 gap 5 from -100 stagger param:901:2"),
            ("repeat-panel 400 gap 5 from -100 stagger param:901:1", "repeat 0 600 stagger param:901:2"),
        ]
        for identifier, (u, v) in enumerate(cases):
            with self.subTest(u=u, v=v):
                self.commit(infinite.infinite(identifier, name="Before", u=u, v=v))
                self.boundary(identifier+1)
                self.binding(identifier, boundary=identifier+1, source=identifier, cell=(0, 1))
                self.commit(f"placement {identifier+1} on boundary {identifier+1} origin 0 0 0 u +x v +y")
                self.commit(f"grid {identifier+10} on {identifier+1} from-binding {identifier}")
                before = self.snapshot()
                segments = self.query("binding", identifier, rect=(-900, -900, 1500, 1500), limit=64)
                self.assertTrue(segments["ok"], segments)
                command = self.rename(identifier)
                preview = self.preview(command)
                self.assertTrue(preview["valid"], preview)
                self.assertTrue(self.line("cancel-preview")["ok"])
                self.assertEqual(before, self.snapshot(), "cancel preserves the whole world")
                self.commit(command)
                expected_objects = copy.deepcopy(before[2])
                next(o for o in expected_objects["gridSystems"] if o["id"] == identifier)["name"] = "只改名稱"
                self.assertEqual(expected_objects, self.objects(), "only the intended name may change")
                expected_scene = before[0].replace(
                    f"grid-system {identifier} name-hex {b'Before'.hex()} ",
                    f"grid-system {identifier} name-hex {'只改名稱'.encode().hex()} ")
                self.assertEqual(expected_scene, self.dump())
                self.assertEqual(before[1], self.refs(), "applied grid and reference identities remain unchanged")
                self.assertEqual(segments, self.query("binding", identifier, rect=(-900, -900, 1500, 1500), limit=64))
                after = self.snapshot()
                self.assertTrue(self.command("undo")["ok"])
                self.assertEqual(before, self.snapshot())
                self.assertTrue(self.command("redo")["ok"])
                self.assertEqual(after, self.snapshot())
        path = Path(self.directory.name) / "renamed.scene"
        path.write_text(self.dump(), encoding="utf-8")
        old_pid = self.session.process.pid
        self.session.stop()
        self.session = _bridge.BridgeSession(self.bridge)
        self.addCleanup(self.session.stop)
        self.assertNotEqual(old_pid, self.session.process.pid)
        self.assertTrue(self.command("loadfile " + native_path(path))["ok"])
        self.assertEqual(after, self.snapshot(), "a fresh native process retains every declared source")

    def test_parameter_after_rename_stays_live_and_negative_band_geometry_is_exact(self):
        self.parameters()
        self.commit(infinite.infinite(u="repeat 0 600 stagger param:901:1", v="repeat 0 400"))
        self.boundary()
        self.binding(cell=(0, 1))
        self.binding(1, cell=(0, -1))
        self.commit(self.rename())
        query = self.query("binding", rect=(-900, -900, 1500, 1500), limit=64)
        rows = {band: (a, b) for k, band, a, b in self.band_segments(query, "u") if k == 1}
        self.assertEqual(300, rows[2][0][0])
        self.assertEqual(700, rows[1][0][0])
        negative = {band: (a, b) for k, band, a, b in self.band_segments(
            self.query("binding", 1, rect=(-900, -900, 1500, 1500)), "u") if k == 1}
        self.assertEqual(700, negative[-1][0][0], "negative odd band uses the same retained delta")
        self.assertEqual(300, negative[0][0][0])
        graph_before = self.command("source-inspect")
        self.parameters(401)
        definition = self.objects()["gridSystems"][0]["uDefinition"]
        self.assertEqual(401, definition["stagger"])
        self.assertEqual({"kind": "parameter", "parameterId": 901, "fieldId": 1}, definition["parameterRefs"]["stagger"])
        self.assertIn("stagger param:901:1", self.dump())
        graph_after = self.command("source-inspect")
        self.assertEqual(graph_before["edges"], graph_after["edges"], "parameter usage edges remain connected")
        rows = {band: (a, b) for k, band, a, b in self.band_segments(self.query("binding", rect=(-900, -900, 1500, 1500), limit=64), "u") if k == 1}
        self.assertEqual(299, rows[2][0][0])
        self.assertEqual(700, rows[1][0][0])

    def test_omission_still_clears_and_invalid_stagger_is_atomic(self):
        self.commit(infinite.infinite(u="repeat 0 600 stagger 400"))
        self.reject(self.rename(fields={"giUStep": "400"}), "整數倍")
        for value in (0, 600, -1200):
            self.reject(infinite.infinite(u=f"repeat 0 600 stagger {value}"), "相位差為 0" if value == 0 else "整數倍")
        self.commit(infinite.infinite())
        self.assertNotIn("stagger", self.dump(), "complete declaration omission still removes stagger")
        self.commit(self.rename())
        self.assertNotIn("stagger", self.dump(), "renaming an absent value cannot introduce zero")


if __name__ == "__main__":
    unittest.main()
