import contextlib
import http.server
import importlib.util
import io
import json
import os
import pathlib
import queue
import sys
import threading
import time
import unittest
import urllib.request
import uuid
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

    @contextlib.contextmanager
    def http_server(self):
        server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), self.server_module.Handler)
        thread = threading.Thread(target=server.serve_forever)
        thread.start()
        try:
            yield f"http://127.0.0.1:{server.server_port}"
        finally:
            server.shutdown()
            thread.join(timeout=2)
            server.server_close()

    def test_timber_space_release_is_advertised_without_changing_the_world(self):
        with self.http_server() as base:
            with urllib.request.urlopen(base + "/model/capabilities", timeout=5) as response:
                self.assertEqual(response.headers["X-Geometry-Release"], "engineering-spec-v1-20260928")
                capabilities = json.load(response)
            self.assertEqual(capabilities["release"], "engineering-spec-v1-20260928")
            self.assertEqual(capabilities["space_preview_schemas"],
                             ["geometry-space-preview/1", "geometry-space-preview/2"])
            self.assertEqual(self.process.stdin.getvalue(), b"")

    def test_example_adapter_failure_is_reported_without_dropping_connection(self):
        sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "geometry-web"))
        import space_modeling
        from modeling import ModelError
        failure = ModelError("UNSUPPORTED", "BASE_COMPILER", "D25", "Test adapter unavailable")
        with patch.object(space_modeling, "examples", side_effect=failure), self.http_server() as base:
            with urllib.request.urlopen(base + "/model/space-examples", timeout=5) as response:
                self.assertEqual(json.load(response), failure.as_dict())
            self.assertEqual(self.process.stdin.getvalue(), b"")

    def test_engineering_http_routes_preserve_payload_and_choose_the_correct_core_operation(self):
        # Exercise Handler wiring as well as file_request: testing the latter
        # alone would miss preview accidentally routed as scene validation.
        transaction = json.dumps({"schema":"engineering-transaction/1", "expectedRevision":7,
                                  "operations":[{"op":"publish-material", "value":{"notes":"尺寸來源"}}]},
                                 ensure_ascii=False).encode("utf-8")
        for route, payload, operation in [("/engineering/preview", transaction, "engineering-preview"),
                                           ("/engineering/validate-project", b"", "engineering-validate")]:
            paths = []
            def bridge(command):
                prefix, name = command.split(" ", 1)
                self.assertEqual(prefix, operation)
                source = pathlib.Path(name); paths.append(source)
                self.assertEqual(source.read_bytes(), payload)
                return b'{"ok":true,"route_evidence":"real handler"}'
            with self.subTest(route=route), patch.object(self.server_module, "ask_bridge", side_effect=bridge) as called, self.http_server() as base:
                request = urllib.request.Request(base + route, data=payload, headers={"Content-Type":"application/json"})
                with urllib.request.urlopen(request, timeout=2) as response:
                    self.assertEqual(json.load(response), {"ok":True,"route_evidence":"real handler"})
                called.assert_called_once()
                self.assertEqual(len(paths), 1)
                self.assertFalse(paths[0].exists())
        self.assertEqual(self.process.stdin.getvalue(), b"")

    def test_reference_assets_are_local_and_path_allowlisted(self):
        with self.http_server() as base:
            for route, ctype in [("/project-store.js", "text/javascript"),
                                 ("/reference-workspace.js", "text/javascript"),
                                 ("/vendor/pdfjs-dist/build/pdf.mjs", "text/javascript"),
                                 ("/vendor/pdfjs-dist/build/pdf.worker.mjs", "text/javascript"),
                                 ("/vendor/fflate/umd/index.js", "text/javascript")]:
                with self.subTest(route=route), urllib.request.urlopen(base + route) as response:
                    self.assertTrue(response.headers["Content-Type"].startswith(ctype))
                    self.assertGreater(len(response.read()), 100)
            for route in ["/vendor/../serve.py", "/vendor/not-present.js", "/sources/private.pdf"]:
                with self.subTest(route=route), self.assertRaises(urllib.error.HTTPError) as result:
                    urllib.request.urlopen(base + route)
                self.assertEqual(result.exception.code, 404)
                result.exception.close()

    def receipt_request(self, **fields):
        return {"session": self.server_module.API_SESSION, **fields}

    def test_lost_api_response_is_recovered_without_repeating_command(self):
        request_id = str(uuid.uuid4())
        with self.http_server() as base:
            def post(data):
                request = urllib.request.Request(base + "/api", data=json.dumps(data).encode(),
                                                 headers={"Content-Type": "application/json"})
                with urllib.request.urlopen(request, timeout=2) as response:
                    self.assertEqual(response.headers["X-Geometry-Session"], self.server_module.API_SESSION)
                    return json.load(response)
            self.responses.put(b'{"ok":true}\n')
            command = self.receipt_request(requestId=request_id, cmd="line history-end")
            self.assertTrue(post(command)["ok"])
            written = self.process.stdin.getvalue()
            self.assertEqual(post(self.receipt_request(receipt=request_id)), {"ok": True, "result": {"ok": True}})
            self.assertTrue(post(command)["ok"])
            self.assertEqual(self.process.stdin.getvalue(), written)
            self.assertFalse(post({**command, "cmd": "line reset"})["ok"])
            self.assertEqual(self.process.stdin.getvalue(), written)

    def test_result_lookup_seals_a_command_that_has_not_arrived(self):
        request_id = str(uuid.uuid4())
        lookup = self.receipt_request(receipt=request_id)
        result = json.loads(self.server_module.recorded_api(lookup))
        self.assertTrue(result["ok"])
        self.assertFalse(result["result"]["ok"])
        late = self.receipt_request(requestId=request_id, cmd="line reset", ack=[request_id])
        self.assertFalse(json.loads(self.server_module.recorded_api(late))["ok"])
        self.assertEqual(self.process.stdin.getvalue(), b"")

    def test_receipts_acknowledge_results_and_bound_unconfirmed_operations(self):
        self.server_module.MAX_RECEIPTS = 1
        first, second = str(uuid.uuid4()), str(uuid.uuid4())
        self.responses.put(b'{"ok":false,"error":"core rejection"}\n')
        result = json.loads(self.server_module.recorded_api(self.receipt_request(requestId=first, cmd="line invalid")))
        self.assertFalse(result["ok"])
        self.assertEqual(json.loads(self.server_module.recorded_api(self.receipt_request(receipt=first)))["result"], result)
        full = self.receipt_request(requestId=second, cmd="line reset")
        self.assertFalse(json.loads(self.server_module.recorded_api(full))["ok"])
        self.assertEqual(self.process.stdin.getvalue(), b"line invalid\n")
        self.responses.put(b'{"ok":true}\n')
        self.assertTrue(json.loads(self.server_module.recorded_api({**full, "ack": [first]}))["ok"])
        self.assertNotIn(first, self.server_module.api_receipts)
        self.assertEqual(len(self.server_module.api_receipts), 1)

    def test_wrong_server_session_cannot_execute_or_recover_operations(self):
        for key in ["requestId", "receipt"]:
            result = json.loads(self.server_module.recorded_api({key: str(uuid.uuid4()), "session": "old-server", "cmd": "line reset"}))
            self.assertFalse(result["ok"])
        self.assertEqual(self.process.stdin.getvalue(), b"")

    def test_receipt_lookup_waits_for_an_inflight_command_result(self):
        request_id = str(uuid.uuid4())
        entered, release, lookup_started, lookup_done = (threading.Event() for _ in range(4))
        results = []
        self.server_module.BRIDGE_TIMEOUT = 2
        def blocked_command(cmd):
            entered.set()
            self.assertTrue(release.wait(2))
            return b'{"ok":true}'
        def lookup():
            lookup_started.set()
            results.append(json.loads(self.server_module.recorded_api(self.receipt_request(receipt=request_id))))
            lookup_done.set()
        with patch.object(self.server_module, "ask_bridge", side_effect=blocked_command) as bridge_call:
            writer = threading.Thread(target=lambda: self.server_module.recorded_api(
                self.receipt_request(requestId=request_id, cmd="line reset")))
            reader = threading.Thread(target=lookup)
            writer.start()
            try:
                self.assertTrue(entered.wait(2))
                reader.start()
                self.assertTrue(lookup_started.wait(2))
                self.assertFalse(lookup_done.wait(0.05))
            finally:
                release.set()
                writer.join(2)
                if reader.ident is not None:
                    reader.join(2)
            self.assertEqual(results, [{"ok": True, "result": {"ok": True}}])
            bridge_call.assert_called_once_with("line reset")

    def upload(self, base, scene, bridge_reply):
        """送一次 /upload,回傳 (解析後的回應, bridge 收到的 loadfile 路徑)。"""
        self.responses.put(bridge_reply)
        request = urllib.request.Request(base + "/upload", data=scene.encode("utf-8"),
                                         headers={"Content-Type": "text/plain"})
        with urllib.request.urlopen(request, timeout=2) as response:
            payload = json.load(response)
        sent = self.process.stdin.getvalue().decode("utf-8").splitlines()[-1]
        self.assertTrue(sent.startswith("loadfile "), sent)
        return payload, sent[len("loadfile "):]

    def test_failed_upload_keeps_the_live_scene_reloadable(self):
        """GEO-154：bridge 的 loadfile 是交易式的,失敗後畫面上還是舊場景。

        舊場景的來源檔必須活著,否則前端 curScene 指向一個已刪的路徑,
        「重新載入場景」從此壞掉。修好之前:舊暫存在新檔驗證前就被刪了。
        """
        temps = self.server_module._upload_temps
        with self.http_server() as base:
            good, first = self.upload(base, "spec 低 300\n", b'{"ok":true}\n')
            self.assertEqual(good["path"], first)
            self.assertEqual(temps, [first])
            self.assertTrue(os.path.exists(first))

            bad, second = self.upload(base, "這不是場景\n",
                                      b'{"ok":false,"error":"parse failed"}\n')
            self.assertTrue(os.path.exists(first), "還活著的場景的來源檔被刪了")
            self.assertEqual(temps, [first])       # 舊暫存原封不動
            self.assertIs(bad["ok"], False)
            self.assertNotIn("path", bad)          # 失敗不得讓前端改指到新檔
            self.assertFalse(os.path.exists(second), "載不起來的新檔應該自己被清掉")

            # 成功的下一次上傳才輪到舊暫存被回收。
            _, third = self.upload(base, "spec 高 2900\n", b'{"ok":true}\n')
            self.assertEqual(temps, [third])
            self.assertFalse(os.path.exists(first))
        for path in list(temps):
            with contextlib.suppress(OSError):
                os.unlink(path)
        temps.clear()

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
