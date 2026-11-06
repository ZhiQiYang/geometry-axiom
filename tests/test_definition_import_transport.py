import hashlib
import json
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "geometry-web"))
import definition_import_transport as transport


def envelope(scene="spec 柱寬 27\n", **extra):
    raw = scene.encode("utf-8")
    body = {
        "schema": "definition-import/1",
        "expectedRevision": 3,
        "sourceSceneSha256": hashlib.sha256(raw).hexdigest(),
        "sourceScene": scene,
        "roots": {"rules": [], "bindings": [1]},
        "names": {},
    }
    body.update(extra)
    return json.dumps(body, ensure_ascii=False).encode("utf-8"), raw


class DefinitionImportTransport(unittest.TestCase):
    def test_read_writes_exact_bytes_and_removes_the_file(self):
        payload = "spec 柱寬 27\n".encode("utf-8")
        paths = []

        def bridge(command):
            self.assertTrue(command.startswith("definition-import-read "))
            path = Path(command.split(" ", 1)[1])
            paths.append(path)
            self.assertEqual(path.read_bytes(), payload)
            return b'{"ok":true}'

        self.assertEqual(transport.read_request(payload, bridge), b'{"ok":true}')
        self.assertFalse(paths[0].exists())

    def test_preview_splits_scene_from_request_and_removes_the_directory(self):
        body, raw = envelope()
        seen = []

        def bridge(command):
            self.assertTrue(command.startswith("definition-import-preview "))
            directory = Path(command.split(" ", 1)[1])
            seen.append(directory)
            self.assertEqual((directory / "source.scene").read_bytes(), raw)
            request = json.loads((directory / "request.json").read_text(encoding="utf-8"))
            self.assertNotIn("sourceScene", request)
            self.assertEqual(request["sourceSceneSha256"], hashlib.sha256(raw).hexdigest())
            return b'{"ok":true}'

        self.assertEqual(transport.preview_request(body, bridge), b'{"ok":true}')
        self.assertFalse(seen[0].exists())

    def test_invalid_preview_never_reaches_the_bridge(self):
        body, raw = envelope()
        digest = hashlib.sha256(raw).hexdigest()
        cases = [
            b"",
            b"\xff",
            b"{}",
            ('{"schema":"definition-import/1","schema":"other","expectedRevision":3,"sourceSceneSha256":"%s","sourceScene":"spec A 1\\n","roots":{"rules":[],"bindings":[1]},"names":{}}' % digest).encode(),
            json.dumps({"schema": "definition-import/1", "expectedRevision": True, "sourceSceneSha256": digest,
                        "sourceScene": "spec 柱寬 27\n", "roots": {"rules": [], "bindings": [1]}, "names": {}}).encode(),
            json.dumps({"schema": "definition-import/1", "expectedRevision": 3, "sourceSceneSha256": digest.upper(),
                        "sourceScene": "spec 柱寬 27\n", "roots": {"rules": [], "bindings": [1]}, "names": {}}).encode(),
            json.dumps({"schema": "definition-import/1", "expectedRevision": 3, "sourceSceneSha256": digest,
                        "sourceScene": "spec 柱寬 99\n", "roots": {"rules": [], "bindings": [1]}, "names": {}}).encode(),
            json.dumps({"schema": "definition-import/1", "expectedRevision": 3, "sourceSceneSha256": digest,
                        "sourceScene": "spec 柱寬 27\n", "roots": {"rules": [], "bindings": [1]}, "names": {}, "instances": []}).encode(),
            b"x" * (transport.PREVIEW_MAX + 1),
        ]
        for data in cases:
            def forbidden(_command):
                self.fail("invalid preview reached the bridge")
            self.assertFalse(json.loads(transport.preview_request(data, forbidden))["ok"])

    def test_oversized_scene_and_request_never_reach_the_bridge(self):
        huge = "x" * (transport.SCENE_MAX + 1)
        body = json.dumps({"schema": "definition-import/1", "expectedRevision": 0, "sourceSceneSha256": "a" * 64,
                           "sourceScene": huge, "roots": {"rules": [], "bindings": []}, "names": {}}).encode("utf-8")
        self.assertLessEqual(len(body), transport.PREVIEW_MAX)
        self.assertEqual(json.loads(transport.preview_request(body, lambda _command: self.fail("scene reached bridge")))["code"], "CAPACITY")
        reduced = {"schema": "definition-import/1", "expectedRevision": 0,
                   "sourceSceneSha256": hashlib.sha256(b"spec A 1\n").hexdigest(),
                   "sourceScene": "spec A 1\n", "roots": {"rules": [], "bindings": [1]},
                   "names": {"x": {"mode": "rename", "name": "n" * (transport.REQUEST_MAX + 1)}}}
        packed = json.dumps(reduced, ensure_ascii=False).encode("utf-8")
        self.assertEqual(json.loads(transport.preview_request(packed, lambda _command: self.fail("request reached bridge")))["code"], "CAPACITY")

    def test_read_rejects_empty_nul_and_oversize_without_a_file(self):
        for data in (b"", b"\0spec", b"x" * (transport.READ_MAX + 1), "不是 utf-8".encode("utf-16")):
            self.assertFalse(json.loads(transport.read_request(data, lambda _command: self.fail("read reached bridge")))["ok"])

    def test_preview_cleanup_runs_when_the_bridge_fails(self):
        body, _raw = envelope()
        seen = []

        def bridge(command):
            seen.append(Path(command.split(" ", 1)[1]))
            raise OSError("bridge down")

        with self.assertRaises(OSError):
            transport.preview_request(body, bridge)
        self.assertFalse(seen[0].exists())


if __name__ == "__main__":
    unittest.main()
