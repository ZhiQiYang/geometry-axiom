import http.server
import importlib.util
import io
import json
import pathlib
import queue
import threading
import time
import unittest
import urllib.request
from unittest.mock import Mock, patch


class BridgeServerTests(unittest.TestCase):
    def setUp(self):
        self.responses = queue.Queue()
        self.process = Mock()
        self.process.stdin = io.BytesIO()
        self.process.stdout.readline.side_effect = self.responses.get
        path = pathlib.Path(__file__).resolve().parents[1] / "geometry-web" / "serve.py"
        spec = importlib.util.spec_from_file_location("geometry_serve_test", path)
        self.server_module = importlib.util.module_from_spec(spec)
        with patch("subprocess.Popen", return_value=self.process), patch("sys.argv", [str(path)]):
            spec.loader.exec_module(self.server_module)
        self.server_module.BRIDGE_TIMEOUT = 0.1
        self.server_module.BRIDGE_WSL = False

    def tearDown(self):
        self.responses.put(b"")
        self.server_module.bridge_reader.join(timeout=2)
        self.assertFalse(self.server_module.bridge_reader.is_alive())

    def ask(self, cmd):
        return json.loads(self.server_module.ask_bridge(cmd))

    def test_empty_commands_do_not_reach_bridge(self):
        for cmd in ["", "   ", "\t", None, 12]:
            with self.subTest(cmd=cmd):
                self.assertFalse(self.ask(cmd)["ok"])
        self.assertEqual(self.process.stdin.getvalue(), b"")
        self.responses.put(b'{"ok":true,"boundary":1}\n')
        self.assertEqual(self.ask("newid"), {"ok": True, "boundary": 1})

    def test_invalid_frames_do_not_reach_bridge(self):
        for cmd in ["newid\nreset", "newid\rreset", "newid\0reset", "x" * 4095]:
            with self.subTest(cmd=cmd[:25]):
                self.assertFalse(self.ask(cmd)["ok"])
        self.assertEqual(self.process.stdin.getvalue(), b"")

    def test_maximum_bridge_frame(self):
        self.responses.put(b'{"ok":true}\n')
        self.assertTrue(self.ask("x" * 4094)["ok"])
        self.assertEqual(len(self.process.stdin.getvalue()), 4095)

    def test_timeout_fails_closed_without_reusing_late_response(self):
        start = time.monotonic()
        result = self.ask("render")
        self.assertFalse(result["ok"])
        self.assertIn("逾時", result["error"])
        self.assertLess(time.monotonic() - start, 1)
        written = self.process.stdin.getvalue()
        self.responses.put(b'{"ok":true,"stale":true}\n')
        self.assertFalse(self.ask("newid")["ok"])
        self.assertEqual(self.process.stdin.getvalue(), written)
        self.process.terminate.assert_not_called()

    def test_bridge_eof_returns_json_error(self):
        self.responses.put(b"")
        self.assertIn("已結束", self.ask("render")["error"])
        self.assertFalse(self.ask("newid")["ok"])

    def test_broken_pipe_returns_json_error(self):
        self.process.stdin = Mock()
        self.process.stdin.write.side_effect = BrokenPipeError()
        self.assertIn("連線中斷", self.ask("render")["error"])
        self.assertFalse(self.ask("newid")["ok"])
        self.assertEqual(self.process.stdin.write.call_count, 1)

    def test_busy_lock_has_bounded_wait(self):
        self.server_module.bridge_lock.acquire()
        try:
            start = time.monotonic()
            self.assertIn("忙碌", self.ask("render")["error"])
            self.assertLess(time.monotonic() - start, 1)
            self.assertEqual(self.process.stdin.getvalue(), b"")
        finally:
            self.server_module.bridge_lock.release()
        self.responses.put(b'{"ok":true}\n')
        self.assertTrue(self.ask("newid")["ok"])

    def test_http_rejects_empty_and_bad_json_then_recovers(self):
        server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), self.server_module.Handler)
        thread = threading.Thread(target=server.serve_forever)
        thread.start()
        url = f"http://127.0.0.1:{server.server_port}/api"
        try:
            for body in [{"cmd": ""}, {"cmd": "   "}, [], None, {"cmd": 1}]:
                request = urllib.request.Request(url, data=json.dumps(body).encode(),
                                                 headers={"Content-Type": "application/json"})
                with urllib.request.urlopen(request, timeout=2) as response:
                    self.assertFalse(json.load(response)["ok"])
            self.assertEqual(self.process.stdin.getvalue(), b"")
            self.responses.put(b'{"ok":true,"boundary":1}\n')
            request = urllib.request.Request(url, data=b'{"cmd":"newid"}',
                                             headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(request, timeout=2) as response:
                self.assertEqual(json.load(response)["boundary"], 1)
        finally:
            server.shutdown()
            thread.join(timeout=2)
            server.server_close()


if __name__ == "__main__":
    unittest.main()
