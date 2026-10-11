# -*- coding: utf-8 -*-
"""區網測試模式（P-008／P-041／P-043；W-B DESIGN r2 §4）的驗收與攻擊面測試。

兩層，都在行程內直接建構 LanHTTPServer，不經 argv：
- 守門層（GateLayer）：以 http 建構、綁 127.0.0.1 臨時埠。守門只看「哪個監聽器收到」與
  Host／Origin／Fetch-Metadata／cookie，不看對端 IP，所以設定裡的區網 IP 用不屬本機的
  192.168.77.10，請求照樣送到 127.0.0.1。不需要 cryptography，一定會跑。
- TLS 層（TlsLayer）：需要 cryptography；缺套件時是 tests/run_all.py ALLOWED_SKIPS 的明確 expected-skip。

本檔不綁任何非 loopback 位址、不寫使用者的 %LOCALAPPDATA%（一律換成暫存目錄）、
不呼叫真的 NetworkCategory 查詢（查詢函式注入），也不讀任何真實的配對碼檔。
"""
import contextlib
import datetime
import http.client
import http.server
import importlib.util
import io
import ipaddress
import json
import os
import pathlib
import queue
import re
import socket
import ssl
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from unittest.mock import Mock, patch

ROOT = pathlib.Path(__file__).resolve().parents[1]
SERVE = ROOT / "geometry-web" / "serve.py"
LAN_IP = "192.168.77.10"
_DEFAULT = object()
try:
    import cryptography  # noqa: F401
    HAVE_CRYPTOGRAPHY = True
except ImportError:
    HAVE_CRYPTOGRAPHY = False
NEEDS_CRYPTOGRAPHY = unittest.skipUnless(HAVE_CRYPTOGRAPHY, "requires cryptography (TLS layer; the gate layer still runs)")


def free_port():
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        return probe.getsockname()[1]


def local_lan_ipv4():
    """本機的非 loopback IPv4。UDP connect 只查路由表，不送任何封包。"""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as probe:
            probe.connect(("192.0.2.1", 9))
            ip = probe.getsockname()[0]
    except OSError:
        return None
    address = ipaddress.IPv4Address(ip)
    return None if address.is_loopback or address.is_unspecified else ip


def refused(host, port, timeout=5.0):
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return False
    except OSError:
        return True


class FakeClock:
    def __init__(self, now=1000.0):
        self.now = now

    def __call__(self):
        return self.now

    def advance(self, seconds):
        self.now += seconds


class Reply:
    def __init__(self, status, headers, body):
        self.status = status
        self.header_list = headers
        self.headers = {name.lower(): value for name, value in headers}
        self.body = body

    def all(self, name):
        return [value for key, value in self.header_list if key.lower() == name.lower()]


def parse_set_cookie(value):
    parts = [part.strip() for part in value.split(";")]
    name, _, token = parts[0].partition("=")
    attributes = {}
    for part in parts[1:]:
        key, _, val = part.partition("=")
        attributes[key.lower()] = val
    return name, token, attributes


class LanCase(unittest.TestCase):
    def setUp(self):
        self.responses = queue.Queue()
        self.process = Mock()
        self.process.stdin = io.BytesIO()
        self.process.stdout.readline.side_effect = self.responses.get
        spec = importlib.util.spec_from_file_location("geometry_serve_lan_test", SERVE)
        self.mod = importlib.util.module_from_spec(spec)
        with patch("subprocess.Popen", return_value=self.process), patch("sys.argv", [str(SERVE)]):
            spec.loader.exec_module(self.mod)
        self.mod.BRIDGE_TIMEOUT = 0.5
        self.mod.BRIDGE_WSL = False
        self.guard = self.mod.lan_guard
        self.logs = []

    def tearDown(self):
        self.responses.put(b"")
        self.mod.root_context.reader.join(timeout=2)

    # -- helpers
    def start_lan(self, clock=None, ssl_context=None, ca_der=None, **overrides):
        port = free_port()
        overrides.setdefault("poll", 0.05)
        config = self.guard.LanConfig(ip=LAN_IP, port=port, **overrides)
        kwargs = {"clock": clock} if clock is not None else {}
        gate = self.guard.LanGate(config, log=self.logs.append, **kwargs)
        server = self.mod.LanHTTPServer(("127.0.0.1", port), gate, ssl_context, ca_der)
        mode = self.mod.LanMode(gate, server, log=self.logs.append).start()
        self.addCleanup(mode.stop)
        return gate, server, mode

    def start_loopback(self):
        server = self.mod.PreviewHTTPServer(("127.0.0.1", 0), self.mod.Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()

        def stop():
            server.shutdown()
            thread.join(timeout=2)
            server.server_close()
        self.addCleanup(stop)
        return server.server_port

    def send(self, port, method, target, *, host=_DEFAULT, origin=None, cookie=None, headers=(), body=b"",
             length=None, timeout=5):
        connection = http.client.HTTPConnection("127.0.0.1", port, timeout=timeout)
        try:
            connection.putrequest(method, target, skip_host=True, skip_accept_encoding=True)
            if host is _DEFAULT:
                host = f"{LAN_IP}:{port}"
            if host is not None:
                connection.putheader("Host", host)
            if origin is not None:
                connection.putheader("Origin", origin)
            if cookie is not None:
                connection.putheader("Cookie", cookie)
            for name, value in headers:
                connection.putheader(name, value)
            if length is not None or body or method in ("POST", "PUT"):
                connection.putheader("Content-Length", str(len(body) if length is None else length))
            connection.endheaders(body or None)
            response = connection.getresponse()
            return Reply(response.status, response.getheaders(), response.read())
        finally:
            connection.close()

    def origin(self, gate):
        return gate.config.origin

    def pair(self, gate, code=None, **kwargs):
        code = gate.display_codes()[0] if code is None else code
        kwargs.setdefault("origin", gate.config.origin)
        return self.send(gate.config.port, "POST", "/lan/pair", body=code.encode("utf-8"), **kwargs)

    def paired_cookie(self, gate):
        reply = self.pair(gate)
        self.assertEqual(reply.status, 204, "配對流程本身失敗，後續守門測試沒有對照組")
        name, token, _ = parse_set_cookie(reply.headers["set-cookie"])
        self.assertEqual(name, "__Host-geometry-lan")
        return f"{name}={token}", token

    def wait_closed(self, mode, limit):
        started = time.monotonic()
        mode.closed.wait(limit)
        return mode.closed.is_set(), time.monotonic() - started


class GateLayer(LanCase):
    # §4-1 ------------------------------------------------------------------
    def test_01_without_flag_handler_and_loopback_rules_are_unchanged(self):
        mod = self.mod
        base = http.server.BaseHTTPRequestHandler
        for name in ("parse_request", "end_headers"):
            self.assertIs(getattr(mod.Handler, name), getattr(base, name),
                          f"loopback Handler.{name} 被改了；區網守門只能在子類別 LanHandler")
        self.assertEqual(mod.LOCAL_ORIGINS, {"http://127.0.0.1:8765", "http://localhost:8765"})
        self.assertEqual(mod.LOCAL_HOSTS, {"127.0.0.1", "localhost"})
        self.assertFalse(issubclass(mod.PreviewHTTPServer, mod.LanHTTPServer))
        for argv, expected in [([], False), (["--lang"], False), (["8766"], False), (["--lan", "x"], True),
                               (["--lan=192.168.1.2"], True), (["--lan-forget"], True), (["--lan-ttl", "5"], True)]:
            self.assertIs(self.guard.lan_requested(argv), expected, argv)
        # The loopback Handler still refuses a LAN Host (S9); LanHandler's override must not leak into it.
        port = self.start_loopback()
        self.assertEqual(self.send(port, "GET", "/runtime", host=f"{LAN_IP}:{port}").status, 403,
                         "loopback Handler 收了區網 Host：S9 的 Host 檢查被 LanHandler 的覆寫波及")
        self.assertEqual(self.send(port, "GET", "/runtime", host=f"127.0.0.1:{port}").status, 200)

    # §4-2 ------------------------------------------------------------------
    def serve_subprocess(self, *args):
        environ = {k: v for k, v in os.environ.items()
                   if k not in ("GEOMETRY_BRIDGE", "GEOMETRY_BRIDGE_WSL", "GEOMETRY_MANAGED_PREVIEW")}
        directory = tempfile.mkdtemp()
        self.addCleanup(lambda: __import__("shutil").rmtree(directory, ignore_errors=True))
        environ.update(GEOMETRY_BRIDGE_EXECUTABLE=sys.executable, GEOMETRY_FEEDBACK_DIR=directory,
                       LOCALAPPDATA=directory, PYTHONIOENCODING="utf-8")
        return subprocess.Popen([sys.executable, "-u", str(SERVE), *map(str, args)], stdin=subprocess.DEVNULL,
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=environ)

    def test_02_without_flag_the_lan_address_is_not_listening(self):
        ip = local_lan_ipv4()
        if ip is None:
            self.skipTest("no non-loopback IPv4 on this machine; cannot probe the LAN address")
        port = free_port()
        process = self.serve_subprocess(port)
        try:
            lines = queue.Queue()
            threading.Thread(target=lambda: lines.put(process.stdout.readline()), daemon=True).start()
            first = lines.get(timeout=60).decode("utf-8", "replace")
            self.assertIn(f"http://localhost:{port}", first)
            self.assertTrue(refused(ip, port), f"無旗標的 serve.py 在區網位址 {ip}:{port} 可被連線")
            reply = self.send(port, "GET", "/runtime", host=f"127.0.0.1:{port}")
            self.assertEqual(reply.status, 200, "無旗標時本機 loopback 應照常服務")
        finally:
            process.terminate()
            process.communicate(timeout=30)

    def test_02b_refused_flags_exit_2_before_any_listener(self):
        for args, needle in [(["--lan", "8.8.8.8"], "拒絕開啟區網測試模式"),
                             (["--lan", "192.168.77.10", "--lan-http"], "旗標錯誤"),
                             (["--lan"], "旗標錯誤")]:
            with self.subTest(args=args):
                port = free_port()
                process = self.serve_subprocess(port, *args)
                out, err = process.communicate(timeout=120)
                self.assertEqual(process.returncode, 2, err.decode("utf-8", "replace"))
                self.assertNotIn(b"http://localhost", out, "被拒絕時 loopback 不得啟動")
                self.assertIn(needle, err.decode("utf-8", "replace"))
                self.assertTrue(refused("127.0.0.1", port))

    # §4-3 ------------------------------------------------------------------
    def validate(self, argv, port=18766, **overrides):
        directory = tempfile.gettempdir()
        options = dict(platform="win32", environ={"GEOMETRY_FEEDBACK_DIR": directory},
                       category_query=lambda ip: "Private", crypto_check=lambda: None)
        options.update(overrides)
        return self.guard.validate(self.guard.parse_args(argv), port=port, repo_root=ROOT, **options)

    def test_03_flag_validation_is_fail_closed(self):
        config = self.validate(["--lan", "192.168.1.23"])
        self.assertEqual((config.ip, config.port, config.ttl, config.idle, config.devices, config.cert_days,
                          config.serve_ca), ("192.168.1.23", 18766, 7200, 1800, 1, 7, False))
        for ip in ("10.1.2.3", "172.16.0.1", "172.31.255.254", "192.168.255.1"):
            self.assertEqual(self.validate(["--lan", ip]).ip, ip)
        refused_cases = []
        for ip in ("0.0.0.0", "::", "127.0.0.1", "8.8.8.8", "169.254.1.1", "100.64.0.1", "198.18.0.1",
                   "172.32.0.1", "172.15.255.255", "192.169.0.1", "255.255.255.255", "192.168.1",
                   "192.168.001.023", "fe80::1", "localhost", ""):
            refused_cases.append((f"address {ip!r}", ["--lan", ip], {}, r"IPv4|RFC1918|標準寫法|缺少"))
        for platform in ("linux", "darwin", "cygwin"):
            refused_cases.append((f"platform {platform}", ["--lan", "192.168.1.23"], {"platform": platform}, "Windows"))
        for category in ("Public", "DomainAuthenticated", "", "private", "Private\nPublic"):
            refused_cases.append((f"category {category!r}", ["--lan", "192.168.1.23"],
                                  {"category_query": lambda ip, c=category: c}, "不是 Private"))

        def raises(error):
            def query(*_):
                raise error
            return query
        for error in (OSError("no powershell"), subprocess.TimeoutExpired("powershell", 10),
                      self.guard.LanRefused("查不到介面")):
            refused_cases.append((f"category query {type(error).__name__}", ["--lan", "192.168.1.23"],
                                  {"category_query": raises(error)}, "查不到|無法確認"))
        refused_cases += [
            ("port 8765", ["--lan", "192.168.1.23"], {"port": 8765}, "8765"),
            ("feedback dir unset", ["--lan", "192.168.1.23"], {"environ": {}}, "GEOMETRY_FEEDBACK_DIR"),
            ("feedback dir empty", ["--lan", "192.168.1.23"], {"environ": {"GEOMETRY_FEEDBACK_DIR": ""}},
             "GEOMETRY_FEEDBACK_DIR"),
            ("feedback dir in repo", ["--lan", "192.168.1.23"],
             {"environ": {"GEOMETRY_FEEDBACK_DIR": str(ROOT / "feedback")}}, "repository"),
            ("feedback dir is repo", ["--lan", "192.168.1.23"],
             {"environ": {"GEOMETRY_FEEDBACK_DIR": str(ROOT)}}, "repository"),
            ("managed preview", ["--lan", "192.168.1.23"],
             {"environ": {"GEOMETRY_FEEDBACK_DIR": tempfile.gettempdir(), "GEOMETRY_MANAGED_PREVIEW": "1"}},
             "受管預覽"),
            ("cryptography missing", ["--lan", "192.168.1.23"],
             {"crypto_check": raises(self.guard.LanRefused("缺少 Python 套件 cryptography"))}, "cryptography"),
        ]
        for flag, value in (("--lan-devices", 0), ("--lan-devices", 4), ("--lan-cert-days", 0),
                            ("--lan-cert-days", 8), ("--lan-ttl", 0), ("--lan-ttl", 481), ("--lan-idle", 0)):
            refused_cases.append((f"{flag} {value}", ["--lan", "192.168.1.23", flag, str(value)], {}, flag))
        for argv in (["--lan", "192.168.1.23", "--lan-http"], ["--lan", "192.168.1.23", "--lan-dev", "2"],
                     ["--lan"], ["--lan", "192.168.1.23", "--lan-ttl", "x"]):
            refused_cases.append((f"argv {argv}", argv, {}, "旗標錯誤"))
        for label, argv, overrides, pattern in refused_cases:
            with self.subTest(label):
                with self.assertRaises(self.guard.LanRefused, msg=f"{label} 應拒絕卻放行") as caught:
                    port = overrides.pop("port", 18766) if "port" in overrides else 18766
                    self.validate(argv, port=port, **overrides)
                self.assertRegex(str(caught.exception), pattern)

    def test_03b_network_category_query_is_read_only_and_parameterised(self):
        calls = []

        def run(argv, **kwargs):
            calls.append((argv, kwargs))
            return subprocess.CompletedProcess(argv, 0, stdout="Private\r\n", stderr="")
        self.assertEqual(self.guard.query_network_category("192.168.1.23", run=run), "Private")
        argv, kwargs = calls[0]
        self.assertEqual(argv[:4], ["powershell", "-NoProfile", "-NonInteractive", "-Command"])
        self.assertEqual(argv[5:], ["192.168.1.23"], "IP 必須是獨立的 argv 元素")
        self.assertNotIn("192.168.1.23", argv[4], "IP 不得內插進命令字串")
        self.assertEqual(set(re.findall(r"\b[A-Z][a-z]+-[A-Z][A-Za-z]+", argv[4])),
                         {"Get-NetConnectionProfile", "Get-NetIPAddress"}, "只准唯讀的 Get- 查詢")
        self.assertEqual(kwargs["timeout"], 10.0)
        failing = lambda argv, **kw: subprocess.CompletedProcess(argv, 1, stdout="", stderr="not found")
        with self.assertRaises(self.guard.LanRefused):
            self.guard.query_network_category("192.168.1.23", run=failing)
        calls.clear()
        with self.assertRaises(ValueError):
            self.guard.query_network_category("192.168.1.23; Set-NetConnectionProfile", run=run)
        self.assertEqual(calls, [], "非 IPv4 字面值不得送進 PowerShell")

    def test_03c_missing_cryptography_refuses_instead_of_falling_back_to_http(self):
        import lan_tls
        with patch.dict(sys.modules, {"cryptography": None}):
            with self.assertRaisesRegex(self.guard.LanRefused, "cryptography"):
                lan_tls.require()

    def test_03d_bind_failure_refuses_and_leaves_nothing_listening(self):
        config = self.guard.LanConfig(ip=LAN_IP, port=free_port())
        gate = self.guard.LanGate(config, log=self.logs.append)
        with patch.object(self.mod, "LanHTTPServer", side_effect=OSError(99, "Cannot assign requested address")):
            with self.assertRaisesRegex(self.guard.LanRefused, "無法綁定"):
                self.mod.bind_lan_listeners(config, gate, None)
        self.assertTrue(refused("127.0.0.1", config.port), "區網綁定失敗後 loopback 不得啟動")
        fake = Mock()
        with socket.socket() as occupied:
            occupied.bind(("127.0.0.1", config.port))
            occupied.listen(1)
            with patch.object(self.mod, "LanHTTPServer", return_value=fake):
                with self.assertRaisesRegex(self.guard.LanRefused, "127.0.0.1"):
                    self.mod.bind_lan_listeners(config, gate, None)
        fake.stop.assert_called_once_with()
        fake.server_close.assert_called_once_with()

    # §4-4 ------------------------------------------------------------------
    def test_04_every_method_and_route_needs_exactly_one_valid_cookie(self):
        gate, server, mode = self.start_lan(pair_interval=0.0)
        port, origin = gate.config.port, gate.config.origin
        vendor = sorted(self.mod.RUNTIME.vendor)[0]
        example = next((key for key in sorted(self.mod.RUNTIME.static) if key.startswith("/examples/")), "/axioms")
        routes = ["/", "/index.html", "/app.js", vendor, "/axioms", example, "/runtime", "/scenes",
                  "/scenarios/editor", "/rule-cases/binding", "/model/capabilities", "/no-such-route",
                  "/lan/ca.cer", "/lan/pair?c=1", "/lan/pair/", "/runtime?scenario=x"]
        sent = 0
        for route in routes:
            with self.subTest(route=route):
                reply = self.send(port, "GET", route)
                sent += 1
                self.assertEqual(reply.status, 403, f"cookie 守門失效：無 cookie 的 GET {route} 回 {reply.status}")
                self.assertEqual(reply.body, b"")
                self.assertNotIn("x-geometry-session", reply.headers)
        for method in ("HEAD", "OPTIONS", "PUT", "DELETE", "PATCH"):
            with self.subTest(method=method):
                reply = self.send(port, method, "/", origin=origin)
                sent += 1
                self.assertEqual(reply.status, 403, f"cookie 守門失效：無 cookie 的 {method} / 回 {reply.status}"
                                                    "（501 表示守門寫在 do_* 而不是 parse_request）")
        started = time.monotonic()
        try:
            reply = self.send(port, "POST", "/api", origin=origin, length=30 * 1024 * 1024, timeout=3)
        except (socket.timeout, TimeoutError):
            self.fail("cookie 守門在讀 body 之後：宣告 30MB 卻不送 body 的 POST /api 沒有被立即拒絕")
        sent += 1
        self.assertEqual(reply.status, 403)
        self.assertLess(time.monotonic() - started, 2.0)
        cookie, token = self.paired_cookie(gate)
        other_name = "geometry-lan=" + token
        for label, value in [("wrong value", "__Host-geometry-lan=bogus"), ("other name only", other_name),
                             ("two cookies (same)", f"{cookie}; {cookie}"), ("valid + bogus", f"{cookie}; __Host-geometry-lan=x"),
                             ("empty", "__Host-geometry-lan=")]:
            with self.subTest(cookie=label):
                reply = self.send(port, "GET", "/runtime", cookie=value)
                sent += 1
                self.assertEqual(reply.status, 403, f"cookie 守門失效：{label} 的 cookie 被接受")
        reply = self.send(port, "GET", "/runtime", cookie=cookie, headers=[("Cookie", cookie)])
        sent += 1
        self.assertEqual(reply.status, 403, "cookie 守門失效：兩個 Cookie 標頭各帶一次有效 cookie 被接受")
        self.assertEqual(gate.denials["cookie"], sent, f"拒絕原因分布 {dict(gate.denials)}")
        # Control: the same request with exactly one valid cookie is served.
        self.assertEqual(self.send(port, "GET", "/runtime", cookie=cookie).status, 200)
        self.assertEqual(self.process.stdin.getvalue(), b"", "未驗證的請求碰到了 bridge")

    # §4-5 ------------------------------------------------------------------
    def test_05_pairing_codes_are_single_use_rate_limited_and_never_logged(self):
        clock = FakeClock()
        gate, server, mode = self.start_lan(clock=clock, devices=2)
        first, second = gate.display_codes()
        raw_codes = [first, second, first.replace("-", ""), second.replace("-", "")]

        def attempt(code, ua="UnitTest/1.0"):
            reply = self.pair(gate, code, headers=[("User-Agent", ua)])
            clock.advance(1.1)
            return reply
        for label, code in [("wrong", "0000-0000-0000-0000-0000-0000-00"), ("empty", ""),
                            ("non-ascii", "配對碼")]:
            with self.subTest(code=label):
                reply = attempt(code)
                self.assertEqual(reply.status, 403, f"錯碼 {label} 被接受")
                self.assertNotIn("set-cookie", reply.headers)
        self.assertEqual(len([line for line in self.logs if "區網配對失敗" in line]), 3)
        self.assertTrue(all("127.0.0.1" in line for line in self.logs if "區網配對失敗" in line))
        ok = self.pair(gate, first, headers=[("User-Agent", "UnitTest/1.0\x07\x1b[31m")])
        self.assertEqual(ok.status, 204)
        # Within the same second: 429 even for the correct code, which is neither evaluated nor consumed.
        limited = self.pair(gate, second)
        self.assertEqual(limited.status, 429, "限速失效：1 秒內第二次配對嘗試被評估了")
        self.assertNotIn("set-cookie", limited.headers)
        self.assertIn(second, gate.display_codes(), "限速中的正確碼被消耗了")
        clock.advance(1.1)
        self.assertEqual(attempt(first).status, 403, "配對碼用後沒有作廢：同一組碼配對了第二台")
        reply = attempt(" " + second.lower().replace("-", " ") + " ")
        self.assertEqual(reply.status, 204, "限速過後正確碼（大小寫與空白正規化後）仍應可配對")
        self.assertEqual(attempt(first).status, 403, "第 N+1 台不得配對")
        self.assertEqual(attempt(second).status, 403, "第 N+1 台不得配對")
        self.assertEqual(gate.paired, 2)
        success = [line for line in self.logs if "區網已配對" in line]
        self.assertEqual(len(success), 2)
        self.assertRegex(success[0], r"第 1/2 台 \d\d:\d\d:\d\d 對端 127\.0\.0\.1 UA UnitTest/1\.0\[31m")
        self.assertNotIn("\x1b", "".join(self.logs))
        for code in raw_codes + [code.lower() for code in raw_codes]:
            self.assertNotIn(code, "\n".join(self.logs), "stderr 印出了配對碼")
        # Origin is mandatory on the pairing POST and the body is bounded.
        clock.advance(1.1)
        self.assertEqual(self.send(gate.config.port, "POST", "/lan/pair", body=b"x").status, 403)
        self.assertEqual(self.pair(gate, "A" * 129).status, 403)

    def test_05b_expired_codes_are_refused(self):
        clock = FakeClock()
        gate, server, mode = self.start_lan(clock=clock, devices=2, pair_interval=0.0)
        first, second = gate.display_codes()
        # A correct code without Origin is refused before it is evaluated, and stays usable.
        reply = self.send(gate.config.port, "POST", "/lan/pair", body=first.encode())
        self.assertEqual(reply.status, 403, "配對 POST 未帶 Origin 卻被評估")
        self.assertIn(first, gate.display_codes(), "配對 POST 未帶 Origin 卻被評估（碼被消耗）")
        self.assertEqual(self.pair(gate, first).status, 204)
        clock.advance(gate.config.pair_ttl + 1)
        self.assertEqual(self.pair(gate, second).status, 403, "逾期的配對碼仍可配對")
        self.assertEqual(gate.paired, 1)

    # §4-6 ------------------------------------------------------------------
    def test_06_wrong_host_is_refused_even_with_a_valid_cookie(self):
        gate, server, mode = self.start_lan(pair_interval=0.0)
        port = gate.config.port
        cookie, _ = self.paired_cookie(gate)
        self.assertEqual(self.send(port, "GET", "/runtime", cookie=cookie).status, 200)
        hosts = [f"evil.example:{port}", "evil.example", f"127.0.0.1:{port}", f"localhost:{port}",
                 f"{LAN_IP}:{port + 1}", LAN_IP, f"{LAN_IP}:{port}.evil.example",
                 f"{LAN_IP.upper()}:0{port}", "", None]
        for host in hosts:
            with self.subTest(host=host):
                self.assertEqual(self.send(port, "GET", "/runtime", host=host, cookie=cookie).status, 403,
                                 f"Host 守門失效：Host {host!r} 被接受")
        reply = self.send(port, "GET", "/runtime", cookie=cookie, headers=[("Host", f"{LAN_IP}:{port}")])
        self.assertEqual(reply.status, 403, "Host 守門失效：兩個 Host 標頭被接受")
        reply = self.send(port, "GET", f"https://{LAN_IP}:{port}/runtime", cookie=cookie)
        self.assertEqual(reply.status, 403, "absolute-form 請求列被路由了")
        self.assertEqual(gate.denials["target"], 1)
        self.assertEqual(gate.denials["host"], len(hosts) + 1, f"拒絕原因分布 {dict(gate.denials)}")

    # §4-7 ------------------------------------------------------------------
    def test_07_wrong_origin_and_fetch_metadata_are_refused(self):
        gate, server, mode = self.start_lan(pair_interval=0.0)
        port, origin = gate.config.port, gate.config.origin
        cookie, _ = self.paired_cookie(gate)
        body = b'{"cmd":"dump"}'
        self.responses.put(b'{"ok":true,"dump":"control"}\n')
        reply = self.send(port, "POST", "/api", origin=origin, cookie=cookie, body=body)
        self.assertEqual((reply.status, json.loads(reply.body)["dump"]), (200, "control"))
        self.assertEqual(self.send(port, "POST", "/api", cookie=cookie, body=body).status, 403,
                         "Origin 守門失效：區網上無 Origin 的 POST 被放行")
        for bad in ("null", f"http://{LAN_IP}:{port}", f"https://{LAN_IP}:{port + 1}", "https://evil.example",
                    f"https://{LAN_IP}:{port}/", f"https://localhost:{port}"):
            with self.subTest(origin=bad):
                self.assertEqual(self.send(port, "POST", "/api", origin=bad, cookie=cookie, body=body).status, 403,
                                 f"Origin 守門失效：POST 帶 Origin {bad!r} 被接受")
                self.assertEqual(self.send(port, "GET", "/runtime", origin=bad, cookie=cookie).status, 403,
                                 f"Origin 守門失效：GET 帶 Origin {bad!r} 被接受")
        reply = self.send(port, "POST", "/api", origin=origin, cookie=cookie, body=body,
                          headers=[("Origin", origin)])
        self.assertEqual(reply.status, 403, "Origin 守門失效：兩個 Origin 標頭被接受")
        for site in ("cross-site", "same-site", "bogus"):
            with self.subTest(site=site):
                reply = self.send(port, "GET", "/runtime", cookie=cookie, headers=[("Sec-Fetch-Site", site)])
                self.assertEqual(reply.status, 403, f"Sec-Fetch-Site 守門失效：{site} 被接受")
                reply = self.send(port, "GET", "/lan/pair", headers=[("Sec-Fetch-Site", site)])
                self.assertEqual(reply.status, 403, f"Sec-Fetch-Site 守門失效：配對頁接受了 {site}")
        for site in ("same-origin", "none"):
            reply = self.send(port, "GET", "/runtime", cookie=cookie, headers=[("Sec-Fetch-Site", site)])
            self.assertEqual(reply.status, 200, f"Sec-Fetch-Site {site} 是同源／使用者直接輸入，應放行")
        self.assertEqual(self.process.stdin.getvalue(), b"dump\n", "被拒絕的請求碰到了 bridge")

    # §4-8 ------------------------------------------------------------------
    def test_08_correct_flow_cookie_attributes_and_security_headers(self):
        gate, server, mode = self.start_lan(ttl=600.0)
        port, origin = gate.config.port, gate.config.origin
        page = self.send(port, "GET", "/lan/pair")
        self.assertEqual(page.status, 200)
        self.assertEqual(page.body, self.guard.PAIR_PAGE)
        self.assertEqual(page.headers["content-security-policy"], self.guard.PAIR_PAGE_CSP)
        self.assertNotIn("x-geometry-session", page.headers, "未驗證的配對頁洩露了 session")
        reply = self.pair(gate, headers=[("User-Agent", "Mozilla/5.0 (iPhone) UnitTest")])
        self.assertEqual(reply.status, 204)
        self.assertEqual(len(reply.all("Set-Cookie")), 1)
        name, token, attributes = parse_set_cookie(reply.headers["set-cookie"])
        self.assertEqual(name, "__Host-geometry-lan")
        self.assertGreaterEqual(len(token), 40)
        for flag in ("secure", "httponly"):
            self.assertIn(flag, attributes)
        self.assertEqual(attributes.get("samesite"), "Strict")
        self.assertEqual(attributes.get("path"), "/")
        self.assertNotIn("domain", attributes)
        self.assertTrue(0 < int(attributes["max-age"]) <= 600, attributes)
        self.assertNotIn(token, json.dumps(sorted(gate.sessions)), "伺服器應只存 cookie 的 SHA-256")
        success = [line for line in self.logs if "區網已配對" in line]
        self.assertEqual(len(success), 1)
        self.assertRegex(success[0], r"第 1/1 台 \d\d:\d\d:\d\d 對端 127\.0\.0\.1 UA Mozilla/5\.0 \(iPhone\) UnitTest")
        cookie = f"{name}={token}"
        home = self.send(port, "GET", "/", cookie=cookie, headers=[("Sec-Fetch-Site", "none")])
        self.assertEqual(home.status, 200 if self.mod.RUNTIME.fresh() else 409,
                         "區網 GET / 被擋：LanHandler 沒有覆寫 S9 的 loopback Host 檢查")
        runtime = self.send(port, "GET", "/runtime", cookie=cookie)
        self.assertEqual(runtime.status, 200)
        self.assertEqual(json.loads(runtime.body)["session"], self.mod.root_context.session)
        self.responses.put(b'{"ok":true,"dump":"lan"}\n')
        api = self.send(port, "POST", "/api", origin=origin, cookie=cookie, body=b'{"cmd":"dump"}')
        self.assertEqual(json.loads(api.body), {"ok": True, "dump": "lan"})
        denied = self.send(port, "GET", "/runtime")
        for response in (page, reply, home, runtime, api, denied):
            self.assertEqual((response.headers.get("referrer-policy"), response.headers.get("x-content-type-options"),
                              response.headers.get("x-frame-options")), ("no-referrer", "nosniff", "SAMEORIGIN"))

    # §4-9 ------------------------------------------------------------------
    def test_09a_ttl_closes_the_lan_listener_but_not_loopback(self):
        loopback = self.start_loopback()
        gate, server, mode = self.start_lan(ttl=1.0, pair_interval=0.0)
        port = gate.config.port
        cookie, _ = self.paired_cookie(gate)
        self.assertEqual(self.send(port, "GET", "/app.js", cookie=cookie).status, 200)
        closed, _ = self.wait_closed(mode, 3.0)
        self.assertTrue(closed, "TTL 到期沒有關閉區網模式")
        self.assertEqual(mode.reason, "TTL 到期")
        self.assertTrue(refused("127.0.0.1", port), "TTL 到期後區網埠仍在監聽")
        self.assertEqual(gate.check("GET", "/runtime", http.client.parse_headers(io.BytesIO(
            f"Host: {LAN_IP}:{port}\r\nCookie: {cookie}\r\n\r\n".encode()))), (None, "closed"),
            "守門第 1 條失效：已關閉的區網模式仍在評估請求")
        self.assertEqual(self.send(loopback, "GET", "/runtime", host=f"127.0.0.1:{loopback}").status, 200)
        self.assertTrue(any("區網測試模式已關閉（TTL 到期）" in line for line in self.logs))

    def test_09b_idle_is_reset_only_by_valid_cookie_requests(self):
        # /app.js is served from the startup snapshot (no freshness scan), so request time stays far below idle.
        gate, server, mode = self.start_lan(idle=1.5, pair_interval=0.0)
        port = gate.config.port
        cookie, _ = self.paired_cookie(gate)
        for _ in range(8):     # 2.4 s of valid traffic keeps an idle=1.5 s session open
            self.assertEqual(self.send(port, "GET", "/app.js", cookie=cookie).status, 200,
                             "有效 cookie 的請求沒有重設閒置計時")
            time.sleep(0.3)
        self.assertFalse(mode.closed.is_set(), "有效 cookie 的請求沒有重設閒置計時")
        last_valid = time.monotonic()
        while not mode.closed.is_set() and time.monotonic() - last_valid < 4.0:
            for target in ("/app.js", "/lan/pair"):
                try:
                    self.send(port, "GET", target, timeout=1)
                except OSError:
                    pass
            time.sleep(0.15)
        self.assertTrue(mode.closed.is_set(), "閒置計時被無效請求（無 cookie、GET /lan/pair）延後，4 秒內沒有關閉")
        self.assertLess(time.monotonic() - last_valid, 2.6, "閒置計時被無效請求延後")
        self.assertEqual(mode.reason, "閒置逾時")

    def test_09c_codes_expired_with_no_device_paired_closes_immediately(self):
        gate, server, mode = self.start_lan(pair_ttl=0.5)
        closed, elapsed = self.wait_closed(mode, 3.0)
        self.assertTrue(closed, "配對碼全部過期且零裝置時沒有關閉")
        self.assertEqual(mode.reason, "配對碼已全部過期且沒有裝置配對")
        self.assertTrue(refused("127.0.0.1", gate.config.port))
        # Control: with one device paired, the same expiry keeps serving that device.
        gate2, server2, mode2 = self.start_lan(pair_ttl=1.0, pair_interval=0.0)
        cookie, _ = self.paired_cookie(gate2)
        time.sleep(1.5)
        self.assertFalse(mode2.closed.is_set(), "已有裝置配對時不應因配對碼過期而關閉")
        self.assertEqual(self.send(gate2.config.port, "GET", "/runtime", cookie=cookie).status, 200)

    def test_09d_closing_cuts_open_connections_and_refuses_late_requests(self):
        gate, server, mode = self.start_lan(header_deadline=30.0)
        idle = socket.create_connection(("127.0.0.1", gate.config.port), timeout=5)
        self.addCleanup(idle.close)
        deadline = time.monotonic() + 2
        while len(server.active) < 1 and time.monotonic() < deadline:
            time.sleep(0.02)
        mode.stop("測試")
        try:
            data = idle.recv(1)
        except (socket.timeout, TimeoutError):
            self.fail("關閉區網模式時沒有切斷進行中的連線")
        except OSError:
            data = b""
        self.assertEqual(data, b"", "關閉區網模式時沒有切斷進行中的連線")
        self.assertEqual(mode.reason, "測試")

    # §4-10b ----------------------------------------------------------------
    def test_10b_slow_headers_are_cut_at_the_total_deadline(self):
        gate, server, mode = self.start_lan(header_deadline=0.6)
        client = socket.create_connection(("127.0.0.1", gate.config.port), timeout=5)
        self.addCleanup(client.close)
        started = time.monotonic()
        cut = None
        for byte in b"GET / HTTP/1.1\r\nHost: " + LAN_IP.encode() + b"\r\nX-Slow: " + b"a" * 40:
            time.sleep(0.1)     # each byte arrives well inside the 60 s per-read timeout
            try:
                client.sendall(bytes([byte]))
            except OSError:
                cut = time.monotonic() - started
                break
            if time.monotonic() - started > 4:
                break
        if cut is None:
            client.settimeout(1.0)
            try:
                data = client.recv(1)
            except (socket.timeout, TimeoutError):
                self.fail("標頭總期限沒有切斷慢速送標頭的連線（Slowloris）")
            except OSError:
                data = b""
            self.assertEqual(data, b"")
            cut = time.monotonic() - started
        self.assertLess(cut, 3.0, "標頭總期限沒有切斷慢速送標頭的連線（Slowloris）")
        self.assertEqual(len(server.pending), 0)

    def test_10b_connection_cap_is_non_blocking(self):
        gate, server, mode = self.start_lan(header_deadline=30.0)
        port = gate.config.port
        cap = gate.config.max_connections
        self.assertEqual(cap, 32)
        holders = []
        self.addCleanup(lambda: [sock.close() for sock in holders])
        for _ in range(cap):
            holders.append(socket.create_connection(("127.0.0.1", port), timeout=5))
        deadline = time.monotonic() + 5
        while len(server.active) < cap and time.monotonic() < deadline:
            time.sleep(0.02)
        self.assertEqual(len(server.active), cap)
        extra = socket.create_connection(("127.0.0.1", port), timeout=5)
        self.addCleanup(extra.close)
        extra.settimeout(1.0)
        try:
            data = extra.recv(1)
        except (socket.timeout, TimeoutError):
            self.fail("第 33 條連線沒有被立即關閉：accept 迴圈在等連線名額（semaphore 阻塞）")
        except OSError:
            data = b""
        self.assertEqual(data, b"", "第 33 條連線應被立即關閉")
        holders.pop().close()
        deadline = time.monotonic() + 2
        while len(server.active) >= cap and time.monotonic() < deadline:
            time.sleep(0.02)
        started = time.monotonic()
        try:
            reply = self.send(port, "GET", "/lan/pair", timeout=2)
        except (socket.timeout, TimeoutError):
            self.fail("名額釋出後正常 client 沒有在 2 秒內完成：accept 迴圈被阻塞")
        self.assertEqual(reply.status, 200)
        self.assertLess(time.monotonic() - started, 2.0)

    # §4-11 -----------------------------------------------------------------
    def test_11_secrets_stay_out_of_logs_banner_feedback_and_pair_page(self):
        gate, server, mode = self.start_lan(pair_interval=0.0, devices=2)
        codes = gate.display_codes()
        directory = pathlib.Path(tempfile.mkdtemp())
        self.addCleanup(lambda: __import__("shutil").rmtree(directory, ignore_errors=True))
        lines = []
        self.guard.announce(gate.config, gate, ca_path=directory / "ca.cer", fingerprint="AB:CD", reused=False,
                            pairing_path=directory / "pairing.txt", tty=False, log=lines.append)
        banner = "\n".join(lines)
        for code in codes:
            self.assertNotIn(code, banner, "非 TTY 時啟動提示印出了配對碼")
            self.assertNotIn(code.replace("-", ""), banner)
        self.assertIn(str(directory / "pairing.txt"), banner)
        self.assertEqual((directory / "pairing.txt").read_text(encoding="utf-8").split(), codes)
        tty_lines = []
        self.guard.announce(gate.config, gate, ca_path=directory / "ca.cer", fingerprint="AB:CD", reused=True,
                            pairing_path=directory / "unused.txt", tty=True, log=tty_lines.append)
        self.assertTrue(all(code in "\n".join(tty_lines) for code in codes), "TTY 對照組：應印出配對碼")
        self.assertFalse((directory / "unused.txt").exists())
        cookie, token = self.paired_cookie(gate)
        feedback = directory / "feedback"
        with patch.dict(os.environ, {"GEOMETRY_FEEDBACK_DIR": str(feedback)}):
            reply = self.send(gate.config.port, "POST", "/feedback", origin=gate.config.origin, cookie=cookie,
                              body=json.dumps({"kind": "bug", "note": "lan", "events": []}).encode(),
                              timeout=60)   # feedback_store records the git version (two git calls)
        self.assertTrue(json.loads(reply.body)["ok"], reply.body)
        stored = b"".join(path.read_bytes() for path in feedback.rglob("*") if path.is_file())
        self.assertTrue(stored)
        for secret in codes + [code.replace("-", "") for code in codes] + [token]:
            self.assertNotIn(secret.encode(), stored, "回報收件匣裡出現配對碼或 cookie")
            self.assertNotIn(secret, "\n".join(self.logs), "stderr 出現配對碼或 cookie")
        page = self.guard.PAIR_PAGE.decode("utf-8")
        self.assertNotRegex(page, r"(?i)\bsrc\s*=|<link|@import|url\(|https?:|<iframe|<img|<object|<embed")
        self.assertEqual(re.findall(r'href="([^"]*)"', page), ["/"])
        self.assertIn("history.replaceState(null, '', '/lan/pair')", page.split("fetch(")[0])


class TlsLayer(LanCase):
    def material(self, environ_root=None, now=None):
        import lan_tls
        root = pathlib.Path(environ_root or tempfile.mkdtemp())
        if environ_root is None:
            self.addCleanup(lambda: __import__("shutil").rmtree(root, ignore_errors=True))
        directory = lan_tls.state_directory(LAN_IP, 18766, {"LOCALAPPDATA": str(root)})
        return lan_tls, root, lan_tls.load_or_issue(LAN_IP, 18766, 7, directory, now=now)

    @NEEDS_CRYPTOGRAPHY
    def test_10a_tls_certificate_properties_and_storage(self):
        from cryptography import x509
        from cryptography.x509.oid import ExtendedKeyUsageOID
        lan_tls, root, material = self.material()
        self.assertFalse(material.reused)
        self.assertNotIn(ROOT.resolve(), material.directory.resolve().parents, "憑證目錄在 repository 內")
        self.assertEqual(material.directory, root.resolve() / "geometry-lan" / f"{LAN_IP}-18766")
        leaf = x509.load_pem_x509_certificate(material.leaf_path.read_bytes())
        ca = x509.load_der_x509_certificate(material.ca_path.read_bytes())
        self.assertEqual(material.ca_der, material.ca_path.read_bytes())
        leaf.verify_directly_issued_by(ca)
        san = leaf.extensions.get_extension_for_class(x509.SubjectAlternativeName)
        self.assertEqual(list(san.value), [x509.IPAddress(ipaddress.IPv4Address(LAN_IP))], "葉憑證 SAN 只能有該 IP")
        eku = leaf.extensions.get_extension_for_class(x509.ExtendedKeyUsage).value
        self.assertEqual(list(eku), [ExtendedKeyUsageOID.SERVER_AUTH])
        leaf_bc = leaf.extensions.get_extension_for_class(x509.BasicConstraints)
        self.assertTrue(leaf_bc.critical)
        self.assertFalse(leaf_bc.value.ca)
        leaf_ku = leaf.extensions.get_extension_for_class(x509.KeyUsage).value
        self.assertTrue(leaf_ku.digital_signature)
        self.assertFalse(leaf_ku.key_cert_sign)
        ca_bc = ca.extensions.get_extension_for_class(x509.BasicConstraints)
        self.assertTrue(ca_bc.critical)
        self.assertEqual((ca_bc.value.ca, ca_bc.value.path_length), (True, 0))
        ca_ku = ca.extensions.get_extension_for_class(x509.KeyUsage)
        self.assertTrue(ca_ku.critical)
        self.assertTrue(ca_ku.value.key_cert_sign and ca_ku.value.crl_sign)
        self.assertFalse(ca_ku.value.digital_signature)
        constraints = ca.extensions.get_extension_for_class(x509.NameConstraints)
        self.assertTrue(constraints.critical, "CA 的 NameConstraints 必須是 critical")
        self.assertEqual(constraints.value.permitted_subtrees,
                         [x509.IPAddress(ipaddress.ip_network(f"{LAN_IP}/32"))])
        self.assertIsNone(constraints.value.excluded_subtrees)
        for cert in (leaf, ca):
            before = getattr(cert, "not_valid_before_utc", None) or cert.not_valid_before.replace(
                tzinfo=datetime.timezone.utc)
            after = lan_tls._not_after(cert)
            self.assertLessEqual(after - before, datetime.timedelta(days=7, minutes=5))
        with self.assertRaises(self.guard.LanRefused):
            lan_tls.issue(LAN_IP, 8)
        stored = {path.name: path.read_bytes() for path in material.directory.iterdir()}
        self.assertEqual(set(stored), {"leaf.pem", "leaf.key", "ca.cer", "meta.json"})
        keys = {name: len(re.findall(rb"-----BEGIN [A-Z ]*PRIVATE KEY-----", data)) for name, data in stored.items()}
        self.assertEqual(sum(keys.values()), 1, f"儲存目錄裡的私鑰數不是 1（CA 私鑰落地？）{keys}")
        self.assertEqual(keys["leaf.key"], 1)
        self.assertNotIn(b"PRIVATE", stored["ca.cer"])
        self.assertEqual(material.fingerprint.count(":"), 31)
        again = lan_tls.load_or_issue(LAN_IP, 18766, 7, material.directory)
        self.assertTrue(again.reused, "同 IP 且剩餘效期 ≥1 小時應沿用")
        self.assertEqual(again.fingerprint, material.fingerprint)
        late = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=7, minutes=-30)
        renewed = lan_tls.load_or_issue(LAN_IP, 18766, 7, material.directory, now=late)
        self.assertFalse(renewed.reused, "剩餘效期不足 1 小時應重發")
        self.assertNotEqual(renewed.fingerprint, material.fingerprint)
        other = lan_tls.load_or_issue("192.168.77.11", 18766, 7, material.directory)
        self.assertFalse(other.reused, "不同 IP 不得沿用")
        with self.assertRaisesRegex(self.guard.LanRefused, "repository"):
            lan_tls.state_directory(LAN_IP, 18766, {"LOCALAPPDATA": str(ROOT)})
        with self.assertRaises(self.guard.LanRefused):
            lan_tls.state_directory(LAN_IP, 18766, {})
        self.assertEqual(lan_tls.forget({"LOCALAPPDATA": str(root)}), root.resolve() / "geometry-lan")
        self.assertFalse((root / "geometry-lan").exists())

    def tls_request(self, port, context, server_hostname, request):
        with socket.create_connection(("127.0.0.1", port), timeout=5) as raw:
            with context.wrap_socket(raw, server_hostname=server_hostname) as tls:
                tls.sendall(request)
                chunks = []
                while True:
                    chunk = tls.recv(65536)
                    if not chunk:
                        return b"".join(chunks)
                    chunks.append(chunk)

    @NEEDS_CRYPTOGRAPHY
    def test_10a_tls_handshake_trust_and_protocol(self):
        lan_tls, root, material = self.material()
        server_context = lan_tls.server_context(material)
        self.assertEqual(server_context.minimum_version, ssl.TLSVersion.TLSv1_2)
        gate, server, mode = self.start_lan(ssl_context=server_context, ca_der=material.ca_der, serve_ca=True)
        port = gate.config.port
        request = f"GET /lan/pair HTTP/1.1\r\nHost: {LAN_IP}:{port}\r\n\r\n".encode()
        trusting = ssl.create_default_context(cadata=material.ca_der)
        response = self.tls_request(port, trusting, LAN_IP, request)
        self.assertTrue(response.startswith(b"HTTP/1.0 200"), response[:80])
        self.assertIn(self.guard.PAIR_PAGE, response)
        ca = self.tls_request(port, trusting, LAN_IP, f"GET /lan/ca.cer HTTP/1.1\r\nHost: {LAN_IP}:{port}\r\n\r\n".encode())
        self.assertTrue(ca.endswith(material.ca_der), "--lan-serve-ca 時 /lan/ca.cer 應給出同一份根憑證")
        for label, context, name in [("untrusted root", ssl.create_default_context(), LAN_IP),
                                     ("other IP", trusting, "192.168.77.11"),
                                     ("DNS name", trusting, "lan.example")]:
            with self.subTest(label):
                with self.assertRaises(ssl.SSLCertVerificationError):
                    self.tls_request(port, context, name, request)
        old = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        old.check_hostname = False
        old.verify_mode = ssl.CERT_NONE
        with contextlib.suppress(ValueError, ssl.SSLError):
            old.set_ciphers("DEFAULT:@SECLEVEL=0")
        with contextlib.suppress(ValueError, ssl.SSLError):
            old.minimum_version = ssl.TLSVersion.TLSv1_1
        old.maximum_version = ssl.TLSVersion.TLSv1_1
        with self.assertRaises((ssl.SSLError, OSError)):
            self.tls_request(port, old, LAN_IP, request)
        with socket.create_connection(("127.0.0.1", port), timeout=5) as plain:
            plain.sendall(request)
            plain.settimeout(5)
            data = b""
            with contextlib.suppress(OSError):
                while True:
                    chunk = plain.recv(65536)
                    if not chunk:
                        break
                    data += chunk
        self.assertNotIn(b"HTTP/1.", data, "明文 HTTP 打區網埠拿到了 HTTP 回應")
        self.assertNotIn("區網測試配對".encode(), data)

    @NEEDS_CRYPTOGRAPHY
    def test_11b_lan_main_composition_never_prints_codes_or_cookies(self):
        lan_tls = __import__("lan_tls")
        root = pathlib.Path(tempfile.mkdtemp())
        self.addCleanup(lambda: __import__("shutil").rmtree(root, ignore_errors=True))
        port = free_port()
        config = self.guard.LanConfig(ip=LAN_IP, port=port, poll=0.05)
        lan_port = free_port()
        real_server = self.mod.LanHTTPServer

        def loopback_lan_server(address, *args):
            self.assertEqual(address, (LAN_IP, port))
            return real_server(("127.0.0.1", lan_port), *args)   # never bind the LAN address in a test
        captured = {}
        real_prepare = self.mod.lan_prepare

        def prepare(argv, log):
            captured["runtime"] = runtime = real_prepare(argv, log)
            return runtime
        stdout, stderr = io.StringIO(), io.StringIO()
        self.mod.PORT = port
        result = {}
        with patch.dict(os.environ, {"LOCALAPPDATA": str(root)}), \
                patch.object(self.guard, "validate", return_value=config), \
                patch.object(self.mod, "LanHTTPServer", side_effect=loopback_lan_server), \
                patch.object(self.mod, "lan_prepare", side_effect=prepare), \
                contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            worker = threading.Thread(target=lambda: result.setdefault("code", self.mod.lan_main(
                ["--lan", LAN_IP])), daemon=True)
            worker.start()
            deadline = time.monotonic() + 30
            directory = lan_tls.state_directory(LAN_IP, port)
            while not (directory / "pairing.txt").exists() and time.monotonic() < deadline:
                time.sleep(0.05)
            codes = (directory / "pairing.txt").read_text(encoding="utf-8").split()
            context = ssl.create_default_context(cadata=(directory / "ca.cer").read_bytes())
            body = codes[0].encode()
            response = self.tls_request(lan_port, context, LAN_IP, (
                f"POST /lan/pair HTTP/1.1\r\nHost: {LAN_IP}:{port}\r\nOrigin: https://{LAN_IP}:{port}\r\n"
                f"Content-Length: {len(body)}\r\n\r\n").encode() + body)
            self.assertTrue(response.startswith(b"HTTP/1.0 204"), response[:120])
            token = re.search(rb"__Host-geometry-lan=([^;]+);", response).group(1).decode()
            runtime = self.tls_request(lan_port, context, LAN_IP, (
                f"GET /runtime HTTP/1.1\r\nHost: {LAN_IP}:{port}\r\nCookie: __Host-geometry-lan={token}\r\n\r\n").encode())
            self.assertTrue(runtime.startswith(b"HTTP/1.0 200"), runtime[:120])
            loopback = self.send(port, "GET", "/runtime", host=f"127.0.0.1:{port}")
            self.assertEqual(loopback.status, 200, "區網模式下本機 loopback 應照常服務")
            captured["runtime"].loopback.shutdown()
            worker.join(15)
        self.assertEqual(result.get("code"), 0)
        out, err = stdout.getvalue(), stderr.getvalue()
        self.assertIn(f"http://localhost:{port}", out)
        self.assertIn("區網測試模式已開啟", err)
        self.assertIn(captured["runtime"].material.fingerprint, err)
        self.assertIn("區網已配對 第 1/1 台", err)
        for secret in codes + [code.replace("-", "") for code in codes] + [token]:
            self.assertNotIn(secret, out + err, "管線擷取的 stdout／stderr 出現配對碼或 cookie")
        self.assertFalse((directory / "pairing.txt").exists(), "結束後 pairing.txt 應刪除")
        self.assertTrue(refused("127.0.0.1", lan_port) and refused("127.0.0.1", port))


if __name__ == "__main__":
    unittest.main()
