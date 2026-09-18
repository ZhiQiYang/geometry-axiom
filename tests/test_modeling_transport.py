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
CLI = ROOT / "geometry-core/modeling_cli.py"
CASES = json.loads((ROOT / "geometry-core/modeling-cases.json").read_text())["cases"]


class ModelingTransport(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temporary = tempfile.TemporaryDirectory(prefix="model-transport-")
        cls.directory = Path(cls.temporary.name)
        cls.environment = dict(os.environ)
        # Build the unchanged legacy bridge for a real service process.
        bridge = cls.directory / "bridge"
        result = subprocess.run(["cc", "-std=c11", "-O0", str(ROOT / "geometry-web/web_bridge.c"),
                                 "-lm", "-o", str(bridge)], capture_output=True, timeout=60)
        if result.returncode:
            raise RuntimeError("Legacy bridge build failed: " + result.stderr.decode(errors="replace"))
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
        self.assertEqual(len(self.capabilities["capabilities"]), 5)
        before = self.post("/api", {"cmd": "render"})
        case = CASES[0]
        source = {"definitions": case["definitions"], "request": case["request"]}
        package = self.post("/model", source)
        self.assertEqual(package["derived"]["objects"][0]["volume_mm3"], "1171200000")
        self.assertEqual(self.post("/model/verify", package)["derived"], package["derived"])
        foreign = deepcopy(package)
        foreign["manifest"]["generator"] = {"name": "independent-project", "version": "test/1"}
        self.assertEqual(self.post("/model/verify", foreign)["derived"], package["derived"])
        invalid = deepcopy(source)
        invalid["definitions"]["extensions"][0]["hi_spec"] = "absent"
        self.assertEqual(self.post("/model", invalid)["status"], "INVALID")
        self.assertEqual(self.post("/model", raw=b'{"definitions":{},"definitions":{},"request":{}}')["status"], "INVALID")
        self.assertEqual(self.post("/api", {"cmd": "render"}), before)

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
        previous = package_path.read_bytes()
        failed = subprocess.run([sys.executable, str(CLI), "example", "open_room_has_no_volume", "-o", str(package_path)],
                                cwd=ROOT, env=self.environment, capture_output=True, timeout=60)
        self.assertEqual(failed.returncode, 3)
        self.assertEqual(json.loads(failed.stderr)["status"], "INCOMPLETE")
        self.assertEqual(package_path.read_bytes(), previous)


if __name__ == "__main__":
    unittest.main(verbosity=2)
