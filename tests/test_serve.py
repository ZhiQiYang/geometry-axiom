import contextlib
import http.server
import importlib.util
import io
import json
import os
import pathlib
import queue
import sys
import tempfile
import threading
import time
import unittest
import urllib.request
import urllib.error
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

    def post_handler(self, route, body=b"", length=None):
        handler = object.__new__(self.server_module.Handler)
        handler.path = route
        handler.headers = {"Content-Length": str(len(body) if length is None else length)}
        handler.rfile = Mock(wraps=io.BytesIO(body))
        handler._local_only = lambda: False
        handler._send = Mock()
        handler.send_error = Mock()
        return handler

    def test_post_body_limits_reject_before_reading_and_accept_the_boundary(self):
        limits = {"/api": 64 * 1024, "/upload": 16 * 1024 * 1024,
                  "/feedback": 32 * 1024 * 1024,
                  "/model": 16 * 1024 * 1024, "/model/verify": 16 * 1024 * 1024,
                  "/model/space-preview": 16 * 1024 * 1024,
                  "/engineering/read": 1024 * 1024,
                  "/engineering/preview": 1024 * 1024,
                  "/engineering/validate-project": 1024 * 1024}
        for route, limit in limits.items():
            with self.subTest(route=route):
                handler = self.post_handler(route, length=limit + 1)
                handler.do_POST()
                handler.send_error.assert_called_once_with(413)
                handler.rfile.read.assert_not_called()
                # Stop at read(): no need to allocate 32 MiB to check the boundary.
                handler = self.post_handler(route, length=limit)
                handler.rfile.read.side_effect = RuntimeError("body read reached")
                with self.assertRaisesRegex(RuntimeError, "body read reached"):
                    handler.do_POST()
                handler.send_error.assert_not_called()
                handler.rfile.read.assert_called_once_with(limit)

    def test_unknown_routes_and_invalid_lengths_do_not_read_the_body(self):
        for route in ["/missing", "/model/missing", "/engineering/missing", "/api?query=1"]:
            with self.subTest(route=route):
                handler = self.post_handler(route, length=2 ** 40)
                handler.do_POST()
                handler.send_error.assert_called_once_with(404)
                handler.rfile.read.assert_not_called()
        for length, status in [("bad", 400), (-1, 413)]:
            with self.subTest(length=length):
                handler = self.post_handler("/api", length=length)
                handler.do_POST()
                handler.send_error.assert_called_once_with(status)
                handler.rfile.read.assert_not_called()

    def test_api_limit_allows_maximum_escaped_command_and_receipt_acknowledgements(self):
        command = "\x01" * self.server_module.BRIDGE_MAX_CMD
        data = self.receipt_request(requestId=str(uuid.uuid4()), cmd=command,
                                    ack=[str(uuid.uuid4()) for _ in range(256)])
        body = json.dumps(data).encode("utf-8")
        self.assertLess(len(body), self.server_module.API_MAX_BYTES)
        body += b" " * (self.server_module.API_MAX_BYTES - len(body))
        handler = self.post_handler("/api", body)
        with patch.object(self.server_module, "recorded_api", return_value=b'{"ok":true}') as recorded:
            handler.do_POST()
        recorded.assert_called_once_with(data)
        handler.send_error.assert_not_called()
        handler._send.assert_called_once_with(b'{"ok":true}')

    def test_feedback_storage_errors_return_json_without_dropping_connection(self):
        with patch.object(self.server_module.feedback_store, "save", side_effect=OSError("disk full")), self.http_server() as base:
            request = urllib.request.Request(base + "/feedback", data=b'{"kind":"bug"}',
                                             headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(request, timeout=2) as response:
                self.assertEqual(response.status, 200)
                self.assertEqual(json.load(response), {"ok": False, "error": "disk full"})

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
        entered, release = threading.Event(), threading.Event()
        def hold_bridge():
            with self.server_module.bridge_lock:
                entered.set()
                release.wait(3)
        owner = threading.Thread(target=hold_bridge)
        owner.start()
        try:
            self.assertTrue(entered.wait(2))
            start = time.monotonic()
            self.assertIn("忙碌", self.ask("render")["error"])
            self.assertLess(time.monotonic() - start, 1)
            self.assertEqual(self.process.stdin.getvalue(), b"")
        finally:
            release.set()
            owner.join(2)
        self.assertFalse(owner.is_alive())
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

    def test_runtime_identity_and_assets_are_from_the_same_snapshot(self):
        with self.http_server() as base:
            with urllib.request.urlopen(base + '/runtime') as response:
                status = json.load(response)
                self.assertTrue(status['fresh'])
                self.assertEqual(status['version'], response.headers['X-Geometry-Version'])
            with urllib.request.urlopen(base + '/') as response:
                self.assertIn(status['version'].encode(), response.read())
            with urllib.request.urlopen(base + '/grid-trial.js') as response:
                self.assertIn(b'root.GridTrial', response.read())
        self.assertEqual(self.process.stdin.getvalue(), b'')

    def test_stale_server_refuses_new_pages_and_writes_but_preserves_dump(self):
        with patch.object(self.server_module.RUNTIME, 'fresh', return_value=False), self.http_server() as base:
            for path in ['/', '/index.html']:
                with self.assertRaises(urllib.error.HTTPError) as error:
                    urllib.request.urlopen(base + path)
                self.assertEqual(error.exception.code, 409)
                self.assertIn('重新啟動', error.exception.read().decode())
            # A page that was already loading can finish with matching OLD assets.
            with urllib.request.urlopen(base + '/app.js') as response:
                self.assertEqual(response.read(), self.server_module.RUNTIME.assets['/app.js'])
            for route, body in [('/api', {'cmd': 'reset'}), ('/upload', {}),
                                ('/model/space-preview', {}), ('/assembly/preview', {})]:
                request = urllib.request.Request(base + route, data=json.dumps(body).encode(),
                                                 headers={'Content-Type': 'application/json'})
                with self.assertRaises(urllib.error.HTTPError) as error:
                    urllib.request.urlopen(request)
                self.assertEqual(error.exception.code, 409)
                self.assertEqual(error.exception.headers['X-Geometry-Stale'], '1')
                self.assertFalse(json.load(error.exception)['ok'])
            self.assertEqual(self.process.stdin.getvalue(), b'')
            self.responses.put(b'{"ok":true,"text":"saved world"}\n')
            request = urllib.request.Request(base + '/api', data=b'{"cmd":"dump"}',
                                             headers={'Content-Type': 'application/json'})
            with urllib.request.urlopen(request) as response:
                self.assertEqual(json.load(response)['text'], 'saved world')
            self.assertEqual(self.process.stdin.getvalue(), b'dump\n')

    def test_old_browser_cannot_mutate_a_new_server_even_if_sources_are_fresh(self):
        with self.http_server() as base:
            request = urllib.request.Request(base + '/api', data=b'{"cmd":"reset"}',
                       headers={'Content-Type': 'application/json', 'X-Geometry-Version': 'older-page'})
            with self.assertRaises(urllib.error.HTTPError) as error:
                urllib.request.urlopen(request)
            self.assertEqual(error.exception.code, 409)
            self.assertEqual(self.process.stdin.getvalue(), b'')

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
                                 ("/grid-trial.js", "text/javascript"),
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

    def test_catalog_and_vendor_get_use_the_same_captured_bytes_and_routes(self):
        from runtime_version import RuntimeSnapshot, static_catalog
        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory)
            web = root / 'geometry-web'
            web.mkdir()
            (root / 'geometry-core').mkdir()
            (web / 'index.html').write_bytes(b'<head></head>')
            for route, path in static_catalog(root).items():
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(route.encode() + b' old bytes\r\n')
            vendor = web / 'vendor'
            vendor.mkdir()
            (vendor / 'map.bcmap').write_bytes(b'old cmap\r\n')
            runtime = RuntimeSnapshot(root)
            self.server_module.RUNTIME = runtime
            # Files may be changed/deleted later; requests still use this one
            # startup capture and an added file cannot expand its route set.
            (vendor / 'map.bcmap').unlink()
            (vendor / 'new.ttf').write_bytes(b'new unversioned font')
            for path in static_catalog(root).values():
                path.write_bytes(b'new live bytes')
            for route in [*static_catalog(root), '/vendor/map.bcmap']:
                with self.subTest(route=route), patch.object(pathlib.Path, 'read_bytes',
                        side_effect=AssertionError('HTTP static request reread filesystem')):
                    handler = object.__new__(self.server_module.Handler)
                    handler.path = route
                    handler._send = Mock()
                    handler.send_error = Mock()
                    handler.do_GET()
                    self.assertEqual(handler._send.call_args.args[0], runtime.static[route])
                    expected = ('text/html; charset=utf-8' if route == '/axioms' else
                                'text/plain; charset=utf-8' if route.startswith('/documents/') else
                                'application/octet-stream')
                    self.assertEqual(handler._send.call_args.args[1], expected)
                    handler.send_error.assert_not_called()
            handler.path = '/vendor/new.ttf'
            handler.send_error.reset_mock()
            handler.do_GET()
            handler.send_error.assert_called_once_with(404)

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

    def test_prepared_upload_cancel_stale_and_confirm_preserve_source_ownership(self):
        mod = self.server_module
        with tempfile.TemporaryDirectory() as directory:
            prior = pathlib.Path(directory) / 'prior.scene'
            prior.write_bytes(b'prior')
            mod._upload_temps[:] = [str(prior)]
            for rejected in ['cancel', 'stale', 'success']:
                mod._upload_outcomes.clear()
                self.responses.put(b'{"ok":true,"token":7,"final_objects":{"boundaries":[1],"placements":[]}}\n')
                prepared = json.loads(mod.upload_scene(b'boundary 1 outline 0,0 80,0 80,70 0,70\n', 'prepare'))
                self.assertEqual(prepared['token'], 7)
                path = mod._prepared_upload[1]
                self.assertTrue(os.path.exists(path))
                self.assertEqual(mod._upload_temps, [str(prior)])
                self.assertTrue(prior.exists())
                self.assertFalse(json.loads(mod.upload_scene(b'8', 'confirm'))['ok'])
                self.assertTrue(os.path.exists(path))
                phase = 'cancel' if rejected == 'cancel' else 'confirm'
                reply = b'{"ok":false,"code":"STALE"}\n' if rejected == 'stale' else b'{"ok":true,"cancelled":true}\n'
                self.responses.put(reply)
                if rejected == 'success':
                    self.responses.put(b'{"ok":true,"text":"committed scene\\n"}\n')
                result = json.loads(mod.upload_scene(b'7', phase))
                self.assertIsNone(mod._prepared_upload)
                if rejected == 'success':
                    self.assertEqual(mod._upload_temps, [path])
                    self.assertEqual(result['path'], path)
                    self.assertFalse(prior.exists())
                    os.unlink(path)
                else:
                    self.assertFalse(os.path.exists(path))
                    self.assertTrue(prior.exists())
                    self.assertEqual(mod._upload_temps, [str(prior)])
            mod._upload_temps.clear()

    def test_terminal_cancel_blocks_a_confirm_that_arrives_after_retry(self):
        mod = self.server_module
        self.responses.put(b'{"ok":true,"token":31}\n')
        mod.upload_scene(b'reset\n', 'prepare')
        self.responses.put(b'{"ok":true,"cancelled":true}\n')
        cancelled = json.loads(mod.upload_scene(b'31', 'cancel'))
        self.assertEqual(cancelled['state'], 'cancelled')
        commands = self.process.stdin.getvalue()
        self.assertFalse(json.loads(mod.upload_scene(b'31', 'confirm'))['ok'])
        self.assertEqual(json.loads(mod.upload_scene(b'31', 'cancel')), cancelled)
        self.assertEqual(self.process.stdin.getvalue(), commands)
        self.assertEqual(mod._upload_temps, [])

    def test_lost_confirm_is_recovered_as_committed_without_a_second_native_load(self):
        mod = self.server_module
        self.responses.put(b'{"ok":true,"token":32}\n')
        mod.upload_scene(b'reset\n', 'prepare')
        self.responses.put(b'{"ok":true,"revision":2}\n')
        self.responses.put(b'{"ok":true,"text":"reset\\n"}\n')
        committed = json.loads(mod.upload_scene(b'32', 'confirm'))
        self.assertEqual(committed['state'], 'committed')
        self.assertEqual(committed['scene_sha256'], mod.hashlib.sha256(b'reset\n').hexdigest())
        commands = self.process.stdin.getvalue()
        self.assertEqual(json.loads(mod.upload_scene(b'32', 'cancel')), committed)
        self.assertEqual(json.loads(mod.upload_scene(b'32', 'confirm')), committed)
        self.assertEqual(self.process.stdin.getvalue(), commands)
        for source in mod._upload_temps:
            os.unlink(source)
        mod._upload_temps.clear()

    def test_concurrent_uploads_preserve_load_and_source_retirement_order(self):
        for reject_second in [False, True]:
            with self.subTest(reject_second=reject_second), tempfile.TemporaryDirectory() as directory:
                mod = self.server_module
                mod.BRIDGE_TIMEOUT = 2
                prior = pathlib.Path(directory) / "prior.scene"
                prior.write_bytes(b"prior")
                mod._upload_temps[:] = [str(prior)]
                cleanup_entered, release_cleanup, second_started, second_loaded = (threading.Event() for _ in range(4))
                loaded, world, results, failures = {}, [], {}, []
                original_temp = tempfile.NamedTemporaryFile
                original_unlink = os.unlink

                def new_temp(*args, **kwargs):
                    return original_temp(*args, **kwargs, dir=directory)

                def bridge(command):
                    source = pathlib.Path(command.removeprefix("loadfile "))
                    label = source.read_bytes()
                    loaded[label] = source
                    if label == b"B":
                        second_loaded.set()
                        if reject_second:
                            return b'{"ok":false,"error":"invalid scene"}'
                    world[:] = [source]
                    return b'{"ok":true}'

                def unlink(path, *args, **kwargs):
                    if path == str(prior):
                        cleanup_entered.set()
                        if not release_cleanup.wait(3):
                            raise RuntimeError("cleanup was not released")
                    return original_unlink(path, *args, **kwargs)

                def post(label):
                    try:
                        handler = self.post_handler("/upload", label)
                        if label == b"B":
                            handler.rfile.read.side_effect = lambda _: (second_started.set(), label)[1]
                        handler.do_POST()
                        results[label] = json.loads(handler._send.call_args.args[0])
                    except Exception as exc:
                        failures.append(exc)

                with patch.object(mod.tempfile, "NamedTemporaryFile", side_effect=new_temp), \
                        patch.object(mod, "ask_bridge", side_effect=bridge), \
                        patch.object(mod.os, "unlink", side_effect=unlink):
                    first = threading.Thread(target=post, args=(b"A",))
                    second = threading.Thread(target=post, args=(b"B",))
                    first.start()
                    try:
                        self.assertTrue(cleanup_entered.wait(2))
                        second.start()
                        self.assertTrue(second_started.wait(2))
                        self.assertFalse(second_loaded.wait(0.05), "second load overtook first source cleanup")
                    finally:
                        release_cleanup.set()
                        first.join(3)
                        if second.ident is not None:
                            second.join(3)
                    self.assertFalse(first.is_alive())
                    self.assertFalse(second.is_alive())
                    self.assertEqual(failures, [])
                self.assertTrue(results[b"A"]["ok"])
                self.assertEqual(results[b"B"]["ok"], not reject_second)
                active = loaded[b"A" if reject_second else b"B"]
                retired = loaded[b"B" if reject_second else b"A"]
                self.assertEqual(world, [active])
                self.assertEqual(mod._upload_temps, [str(active)])
                self.assertTrue(active.exists())
                self.assertFalse(retired.exists())
                self.assertFalse(prior.exists())
                mod._upload_temps.clear()

    def test_upload_busy_lock_has_bounded_wait_and_creates_no_file(self):
        mod = self.server_module
        mod.upload_lock.acquire()
        try:
            handler = self.post_handler("/upload", b"scene")
            with patch.object(mod.tempfile, "NamedTemporaryFile") as temporary, patch.object(mod, "ask_bridge") as bridge:
                start = time.monotonic()
                handler.do_POST()
                self.assertLess(time.monotonic() - start, 1)
                self.assertFalse(json.loads(handler._send.call_args.args[0])["ok"])
                temporary.assert_not_called()
                bridge.assert_not_called()
        finally:
            mod.upload_lock.release()

    def test_api_reload_waits_until_upload_source_retirement_finishes(self):
        mod = self.server_module
        mod.BRIDGE_TIMEOUT = 2
        with tempfile.TemporaryDirectory() as directory:
            prior = pathlib.Path(directory) / "prior.scene"
            prior.write_bytes(b"prior")
            mod._upload_temps[:] = [str(prior)]
            cleanup_entered, release_cleanup, reload_started, reload_done = (threading.Event() for _ in range(4))
            results, failures = [], []
            original_temp, original_unlink = tempfile.NamedTemporaryFile, os.unlink

            def new_temp(*args, **kwargs):
                return original_temp(*args, **kwargs, dir=directory)

            def unlink(path, *args, **kwargs):
                if path == str(prior):
                    cleanup_entered.set()
                    if not release_cleanup.wait(3):
                        raise RuntimeError("cleanup was not released")
                return original_unlink(path, *args, **kwargs)

            upload = self.post_handler("/upload", b"new scene")
            def do_upload():
                try:
                    upload.do_POST()
                except Exception as exc:
                    failures.append(exc)

            def reload():
                reload_started.set()
                try:
                    results.append(self.ask("loadfile " + str(prior)))
                except Exception as exc:
                    failures.append(exc)
                finally:
                    reload_done.set()

            with patch.object(mod.tempfile, "NamedTemporaryFile", side_effect=new_temp), \
                    patch.object(mod.os, "unlink", side_effect=unlink):
                self.responses.put(b'{"ok":true}\n')
                first = threading.Thread(target=do_upload)
                second = threading.Thread(target=reload)
                first.start()
                try:
                    self.assertTrue(cleanup_entered.wait(2))
                    before_reload = self.process.stdin.getvalue()
                    # The bridge rejects the retired path once the upload completes.
                    self.responses.put(b'{"ok":false,"error":"source no longer exists"}\n')
                    second.start()
                    self.assertTrue(reload_started.wait(2))
                    self.assertFalse(reload_done.wait(0.05))
                    self.assertEqual(self.process.stdin.getvalue(), before_reload)
                finally:
                    release_cleanup.set()
                    first.join(3)
                    if second.ident is not None:
                        second.join(3)
                self.assertFalse(first.is_alive())
                self.assertFalse(second.is_alive())
                self.assertEqual(failures, [])
            self.assertEqual(results, [{"ok": False, "error": "source no longer exists"}])
            result = json.loads(upload._send.call_args.args[0])
            self.assertTrue(result["ok"])
            self.assertTrue(pathlib.Path(result["path"]).exists())
            self.assertEqual(mod._upload_temps, [result["path"]])
            self.assertFalse(prior.exists())
            mod._upload_temps.clear()

    def test_failed_temp_write_removes_new_file_and_preserves_previous_source(self):
        mod = self.server_module
        with tempfile.TemporaryDirectory() as directory:
            prior = pathlib.Path(directory) / "prior.scene"
            prior.write_bytes(b"prior")
            created = pathlib.Path(directory) / "new.scene"
            created.touch()
            mod._upload_temps[:] = [str(prior)]
            file = Mock(name=str(created))
            file.name = str(created)
            file.write.side_effect = OSError("disk full")
            context = Mock()
            context.__enter__ = Mock(return_value=file)
            context.__exit__ = Mock(return_value=False)
            with patch.object(mod.tempfile, "NamedTemporaryFile", return_value=context), patch.object(mod, "ask_bridge") as bridge:
                handler = self.post_handler("/upload", b"scene")
                handler.do_POST()
                self.assertFalse(json.loads(handler._send.call_args.args[0])["ok"])
                bridge.assert_not_called()
            self.assertFalse(created.exists())
            self.assertTrue(prior.exists())
            self.assertEqual(mod._upload_temps, [str(prior)])
            self.assertFalse(mod.upload_lock.locked())
            mod._upload_temps.clear()

    def test_upload_does_not_hold_lock_while_sending_response(self):
        mod = self.server_module
        handler = self.post_handler("/upload", b"invalid scene")
        def send(_):
            acquired = mod.upload_lock.acquire(blocking=False)
            self.assertTrue(acquired)
            if acquired:
                mod.upload_lock.release()
        handler._send.side_effect = send
        with patch.object(mod, "ask_bridge", return_value=b'{"ok":false,"error":"invalid scene"}'):
            handler.do_POST()
        handler._send.assert_called_once()

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
