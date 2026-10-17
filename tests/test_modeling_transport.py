"""Exercise actual CLI files and the local HTTP service, with no UI assumptions."""
from copy import deepcopy
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import tempfile
import time
import unittest
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:  # `python tests/x.py` puts tests/ first, not the repo root
    sys.path.insert(0, str(ROOT))
from tests import _bridge  # noqa: E402
CLI = ROOT / "geometry-core/modeling_cli.py"
CASES = json.loads((ROOT / "geometry-core/modeling-cases.json").read_text())["cases"]


class ModelingTransport(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # The unchanged legacy bridge for a real service process: a fresh, checked exe or a skip (never a stale default).
        bridge = _bridge.find_bridge()
        cls.temporary = tempfile.TemporaryDirectory(prefix="model-transport-")
        cls.directory = Path(cls.temporary.name)
        cls.environment = dict(os.environ)
        cls.environment["GEOMETRY_BRIDGE"] = str(bridge)
        cls.environment.pop("GEOMETRY_MANAGED_PREVIEW", None)
        with socket.socket() as sock:
            sock.bind(("127.0.0.1", 0))
            port = sock.getsockname()[1]
        cls.url = f"http://127.0.0.1:{port}"
        cls.opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        cls.log = (cls.directory / "service.log").open("wb")
        cls.service = subprocess.Popen([sys.executable, str(ROOT / "geometry-web/serve.py"), str(port)],
                                       cwd=ROOT, env=cls.environment, stdout=cls.log, stderr=cls.log)
        for _ in range(100):
            try:
                with cls.opener.open(cls.url + "/model/capabilities", timeout=1) as response:
                    cls.capabilities = json.load(response)
                break
            except OSError:
                if cls.service.poll() is not None:
                    raise RuntimeError("Service exited during startup")
                time.sleep(0.05)
        else:
            cls.service.terminate()
            raise RuntimeError("Service startup timeout")

    @classmethod
    def tearDownClass(cls):
        # serve.py owns one legacy bridge child; terminate both through an
        # ordinary interrupt so its finally block also closes that child.
        import signal
        if os.name == "nt":
            # Windows 對子行程沒有 SIGINT(ValueError: Unsupported signal: 2);
            # 沒關掉 service 會讓 service.log 被佔住、暫存目錄清不掉。
            cls.service.terminate()
        else:
            cls.service.send_signal(signal.SIGINT)
        try:
            cls.service.wait(timeout=5)
        except subprocess.TimeoutExpired:
            cls.service.kill()
            cls.service.wait(timeout=5)
        cls.log.close()
        cls.temporary.cleanup()

    def post(self, path, data=None, raw=None):
        request = urllib.request.Request(self.url + path,
                                         data=raw if raw is not None else json.dumps(data).encode(),
                                         headers={"Content-Type": "application/json"})
        with self.opener.open(request, timeout=30) as response:
            return json.load(response)

    def test_http_models_are_isolated_and_reconstructible(self):
        self.assertIn("engineering-spec/1", self.capabilities["capabilities"])
        self.assertEqual(len(self.capabilities["capabilities"]), 9)
        self.assertIn("grid-card-reference/1", self.capabilities["capabilities"])
        self.assertIn("parameters/1", self.capabilities["capabilities"])
        self.assertIn("section-profile/1", self.capabilities["capabilities"])
        self.assertTrue(self.post("/api", {"cmd": "line spec transport_sentinel 419"})["ok"])
        def world():
            dump = self.post("/api", {"cmd": "dump"})
            engineering = self.post("/api", {"cmd": "engineering-read"})
            self.assertTrue(dump["ok"])
            self.assertTrue(engineering["ok"])
            # A render cannot expose a lost source or an extra undo entry.
            # These routes are read-only: their World revision must not advance.
            return dump["text"], engineering["definition_sha256"], engineering["revision"]
        before = world()
        def isolated(path, data=None, raw=None):
            result = self.post(path, data, raw)
            self.assertEqual(world(), before, path + " changed the live World")
            return result
        case = CASES[0]
        source = {"definitions": case["definitions"], "request": case["request"]}
        package = isolated("/model", source)
        self.assertEqual(package["derived"]["objects"][0]["volume_mm3"], "1171200000")
        self.assertEqual(isolated("/model/verify", package)["derived"], package["derived"])
        foreign = deepcopy(package)
        foreign["manifest"]["generator"] = {"name": "independent-project", "version": "test/1"}
        self.assertEqual(isolated("/model/verify", foreign)["derived"], package["derived"])
        invalid = deepcopy(source)
        invalid["definitions"]["extensions"][0]["hi_spec"] = "absent"
        self.assertEqual(isolated("/model", invalid)["status"], "INVALID")
        self.assertEqual(isolated("/model", raw=b'{"definitions":{},"definitions":{},"request":{}}')["status"], "INVALID")
        for field, value in [("axiom_sha256", "0" * 64), ("capabilities", ["future-model/9"]),
                             ("geometry_sha256", "0" * 64)]:
            with self.subTest(manifest_field=field):
                forged = deepcopy(package)
                forged["manifest"][field] = value
                result = isolated("/model/verify", forged)
                self.assertIn(result.get("status"), ("INVALID", "UNSUPPORTED"))
                self.assertNotIn("derived", result)

    def test_cli_exact_obj_and_failure_preserves_previous_file(self):
        package_path, obj_path = self.directory / "wall.json", self.directory / "wall.obj"
        result = subprocess.run([sys.executable, str(CLI), "example", "wall_through_hole",
                                 "-o", str(package_path), "--obj", str(obj_path)],
                                cwd=ROOT, env=self.environment, capture_output=True, timeout=60)
        self.assertEqual(result.returncode, 0, result.stderr.decode())
        package = json.loads(package_path.read_bytes())
        objects = package["derived"]["objects"]
        lines = obj_path.read_text().splitlines()
        vertices = [list(map(int, line.split()[1:])) for line in lines if line.startswith("v ")]
        triangles = [[int(n)-1 for n in line.split()[1:]] for line in lines if line.startswith("f ")]
        self.assertEqual(vertices, objects[0]["vertices_mm"])
        self.assertEqual(triangles, objects[0]["triangles"])
        # Independent acceptance vector; equal JSON/OBJ output alone could let
        # both writers agree on the wrong fixture or an empty/wrong mesh.
        expected = next(case["expected"] for case in CASES if case["id"] == "wall_through_hole")
        self.assertEqual(objects[0]["volume_mm3"], expected["volume_mm3"])
        self.assertEqual([[min(v[axis] for v in vertices) for axis in range(3)],
                          [max(v[axis] for v in vertices) for axis in range(3)]], expected["bounds_mm"])
        previous = package_path.read_bytes()
        failed = subprocess.run([sys.executable, str(CLI), "example", "open_room_has_no_volume", "-o", str(package_path)],
                                cwd=ROOT, env=self.environment, capture_output=True, timeout=60)
        self.assertEqual(failed.returncode, 3)
        self.assertEqual(json.loads(failed.stderr)["status"], "INCOMPLETE")
        self.assertEqual(package_path.read_bytes(), previous)

    def test_section_profile_http_and_cli_keep_frames_identity_and_atomic_exports(self):
        from tests.test_section_profile_modeling import scene, run, request
        source = {"definitions": {"base_scene": scene(), "extensions": []}, "request": request()}
        before = self.post("/api", {"cmd": "dump"})["text"]
        package = self.post("/model", source)
        self.assertEqual(package["derived"]["status"], "COMPLETE")
        self.assertEqual([obj["volume_mm3"] for obj in package["derived"]["objects"]], ["84960000", "2138400", "2138400", "2138400"])
        self.assertEqual([obj["member_path"] for obj in package["derived"]["objects"]], [[], [1], [2], [3]])
        self.assertEqual(self.post("/model/verify", package)["derived"], package["derived"])
        self.assertEqual(self.post("/api", {"cmd": "dump"})["text"], before)
        source_path = self.directory / "profile-source.json"
        package_path = self.directory / "profile.model.json"
        obj_path = self.directory / "profile.obj"
        source_path.write_text(json.dumps(source), encoding="utf-8")
        command = [sys.executable, str(CLI), "build", str(source_path), "-o", str(package_path), "--obj", str(obj_path)]
        result = subprocess.run(command, cwd=ROOT, env=self.environment, capture_output=True, timeout=60)
        self.assertEqual(result.returncode, 0, result.stderr.decode())
        self.assertEqual(json.loads(package_path.read_bytes()), package)
        self.assertIn("coordinates: local (u,v,w)", obj_path.read_text())
        previous = package_path.read_bytes(), obj_path.read_bytes()
        source["definitions"]["base_scene"] = scene(runs=[run(), run(2)])
        source["request"] = request(1, 2)
        source_path.write_text(json.dumps(source), encoding="utf-8")
        result = subprocess.run(command, cwd=ROOT, env=self.environment, capture_output=True, timeout=60)
        self.assertEqual(result.returncode, 4)
        self.assertEqual(json.loads(result.stderr)["diagnostics"][0]["code"], "OBJ_COORDINATE_SPACE")
        self.assertEqual((package_path.read_bytes(), obj_path.read_bytes()), previous)


if __name__ == "__main__":
    unittest.main(verbosity=2)
