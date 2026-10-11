"""PR #194 review regressions. Synthetic certificates and loopback only.

PureReview opens no listener and runs no executable. SocketReview exercises the
real HTTP handler with the existing mock native bridge, never a LAN interface.
"""
import datetime as dt
import email.message
import http.cookiejar
import http.client
import io
import ipaddress
import pathlib
import socket
import ssl
import sys
import tempfile
import threading
import time
import types
import unittest
import urllib.request
from unittest.mock import Mock, patch

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import test_serve_lan as base


def certificate_utc(cert, field):
    """Read the independent certificate oracle on cryptography 41 and 42+."""
    value = getattr(cert, field + "_utc", None)
    if value is None:
        value = getattr(cert, field).replace(tzinfo=dt.timezone.utc)
    return value


class PureReview(base.LanCase):
    def test_ttl_and_idle_are_hard_maxima(self):
        def validate(*argv):
            return self.guard.validate(self.guard.parse_args(["--lan", base.LAN_IP, *argv]),
                port=18766, repo_root=base.ROOT, platform="win32",
                environ={"GEOMETRY_FEEDBACK_DIR": tempfile.gettempdir()},
                category_query=lambda ip: "Private", crypto_check=lambda: None)
        self.assertEqual((validate().ttl, validate().idle), (7200, 1800))
        self.assertEqual((validate("--lan-ttl", "1").ttl, validate("--lan-idle", "1").idle), (60, 60))
        for flag, values in (("--lan-ttl", (121, 480)), ("--lan-idle", (31, 480))):
            for value in values:
                with self.subTest(flag=flag, value=value):
                    with self.assertRaises(self.guard.LanRefused, msg="TTL/idle hard maximum bypassed"):
                        validate(flag, str(value))

    def test_powershell_ttl_matches_the_python_limit(self):
        source = (base.ROOT / "geometry-web/start.ps1").read_text(encoding="utf-8")
        self.assertRegex(source, r"\[ValidateRange\(1,\s*120\)\]\[int\]\$LanTtlMinutes",
                         "PowerShell TTL hard maximum is not 120 minutes")

    def test_finished_headers_check_deadline_without_waiting_for_watchdog(self):
        for offset, expected in ((-0.001, True), (0, False), (0.15, False)):
            with self.subTest(offset=offset):
                server = object.__new__(self.mod.LanHTTPServer)
                request, connection = object(), Mock()
                server.worker = types.SimpleNamespace(request=request)
                server.pending = {request: [connection, 100.0]}
                server.table_lock = threading.Lock()
                lock_observed = []
                def clock():
                    lock_observed.append(server.table_lock.locked())
                    return 100.0 + offset
                with patch.object(self.mod.time, "monotonic", side_effect=clock), \
                        patch.object(self.mod, "_cut") as cut:
                    result = server.headers_complete()
                self.assertEqual(result, expected, "completed headers escaped their accept deadline")
                self.assertEqual(lock_observed, [True], "deadline must be checked inside table_lock")
                self.assertEqual(cut.call_count, 0 if expected else 1)
                self.assertEqual(server.pending, {})

    def test_cookie_names_also_separate_restarts_on_the_same_port(self):
        config = self.guard.LanConfig(ip=base.LAN_IP, port=18766)
        gates = [self.guard.LanGate(config, log=self.logs.append) for _ in range(2)]
        names = [getattr(gate, "cookie_name", self.guard.COOKIE_NAME) for gate in gates]
        self.assertNotEqual(*names, "restarted listeners share a cookie name")
        for name in names:
            self.assertRegex(name, r"^__Host-geometry-lan-18766-[a-f0-9]+$")

    def test_stop_reports_incomplete_cleanup_instead_of_returning_success(self):
        gate = self.guard.LanGate(self.guard.LanConfig(ip=base.LAN_IP, port=18766), log=self.logs.append)
        mode = self.mod.LanMode(gate, Mock(), log=self.logs.append)
        mode.closed = Mock()
        mode.closed.is_set.return_value = False
        mode.closed.wait.return_value = False
        with self.assertRaisesRegex(RuntimeError, "尚未完成", msg="incomplete LAN shutdown returned silently"):
            mode.stop()
        mode.closed.wait.assert_called_once_with(10)
        self.assertTrue(mode.stop_request.is_set())

    def issued(self):
        import lan_tls
        from cryptography import x509
        from cryptography.hazmat.primitives import serialization
        from cryptography.hazmat.primitives.asymmetric import ec
        now = dt.datetime.now(dt.timezone.utc).replace(microsecond=0)
        ca_key, leaf_key = [ec.generate_private_key(ec.SECP256R1()) for _ in range(2)]
        with patch.object(ec, "generate_private_key", side_effect=[ca_key, leaf_key]):
            pem, key, der = lan_tls.issue(base.LAN_IP, 7, now)
        return lan_tls, now, x509.load_pem_x509_certificate(pem), x509.load_der_x509_certificate(der), ca_key, leaf_key

    def rewrite(self, cert, signer, *, replacements=(), omit=(), before=None, after=None, subject=None, issuer=None):
        from cryptography import x509
        from cryptography.hazmat.primitives import hashes
        builder = (x509.CertificateBuilder().subject_name(cert.subject if subject is None else subject)
            .issuer_name(cert.issuer if issuer is None else issuer)
            .public_key(cert.public_key()).serial_number(cert.serial_number)
            .not_valid_before(before or certificate_utc(cert, "not_valid_before"))
            .not_valid_after(after or certificate_utc(cert, "not_valid_after")))
        replacements = {type(value): (value, critical) for value, critical in replacements}
        for ext in cert.extensions:
            if type(ext.value) not in omit:
                value, critical = replacements.pop(type(ext.value), (ext.value, ext.critical))
                builder = builder.add_extension(value, critical)
        for value, critical in replacements.values():
            builder = builder.add_extension(value, critical)
        return builder.sign(signer, hashes.SHA256())

    def chain_validates(self, ca, leaf, key, *, hostname=None, common_name=True):
        """Actual OpenSSL chain validation via MemoryBIO; hostname matching defaults off.

        All leaves use the same CA and key. A wrong-name failure therefore
        proves a chain constraint, not a mismatch against the normal IP SAN.
        """
        from cryptography.hazmat.primitives import serialization as ser
        with tempfile.TemporaryDirectory(prefix="geometry-lan-chain-") as root:
            cert_path, key_path = pathlib.Path(root) / "leaf.pem", pathlib.Path(root) / "leaf.key"
            cert_path.write_bytes(leaf.public_bytes(ser.Encoding.PEM))
            key_path.write_bytes(key.private_bytes(ser.Encoding.PEM, ser.PrivateFormat.PKCS8, ser.NoEncryption()))
            server = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
            server.load_cert_chain(str(cert_path), str(key_path))
            client = ssl.create_default_context(cadata=ca.public_bytes(ser.Encoding.PEM).decode())
            client.check_hostname = hostname is not None
            client.hostname_checks_common_name = common_name
            incoming = [ssl.MemoryBIO(), ssl.MemoryBIO()]
            outgoing = [ssl.MemoryBIO(), ssl.MemoryBIO()]
            peers = [client.wrap_bio(incoming[0], outgoing[0], server_hostname=hostname or base.LAN_IP),
                     server.wrap_bio(incoming[1], outgoing[1], server_side=True)]
            done = [False, False]
            for _ in range(30):
                for i in range(2):
                    if not done[i]:
                        try:
                            peers[i].do_handshake()
                            done[i] = True
                        except ssl.SSLWantReadError:
                            pass
                        except ssl.SSLCertVerificationError:
                            return False
                    data = outgoing[i].read()
                    if data:
                        incoming[1 - i].write(data)
                if all(done):
                    return True
            self.fail("TLS MemoryBIO handshake did not finish")

    @base.NEEDS_CRYPTOGRAPHY
    def test_same_ca_rejects_other_ip_dns_email_and_uri_leaves(self):
        from cryptography import x509
        _, _, leaf, ca, ca_key, leaf_key = self.issued()
        cases = [("right IP", x509.IPAddress(ipaddress.IPv4Address(base.LAN_IP)), True),
                 ("wrong IP", x509.IPAddress(ipaddress.IPv4Address("192.168.77.11")), False),
                 ("DNS", x509.DNSName("audit.example"), False),
                 ("single-label DNS", x509.DNSName("localhost"), False),
                 ("email", x509.RFC822Name("audit@example.test"), False),
                 ("URI", x509.UniformResourceIdentifier("https://audit.example/path"), False),
                 ("excluded DNS", x509.DNSName("geometry-lan-names.invalid"), False),
                 ("excluded email", x509.RFC822Name("a@geometry-lan-names.invalid"), False),
                 ("excluded URI", x509.UniformResourceIdentifier("https://geometry-lan-names.invalid/"), False)]
        for label, name, expected in cases:
            with self.subTest(name=label):
                signed = self.rewrite(leaf, ca_key, replacements=[(x509.SubjectAlternativeName([name]), False)])
                self.assertEqual(self.chain_validates(ca, signed, leaf_key), expected,
                                 f"CA accepted forbidden {label} leaf (hostname matching disabled)")

    @base.NEEDS_CRYPTOGRAPHY
    def test_subject_whitelist_rejects_cn_variants_before_reuse(self):
        import json
        from cryptography import x509
        from cryptography.hazmat.primitives import serialization as ser
        from cryptography.x509.oid import NameOID
        tls, now, leaf, ca, ca_key, leaf_key = self.issued()
        cn = lambda value: x509.NameAttribute(NameOID.COMMON_NAME, value)
        subjects = {
            "wildcard CN": x509.Name([cn("*.example.test")]),
            "wrong single CN": x509.Name([cn("audit.example.test")]),
            "normal plus wildcard CN": x509.Name([cn(tls.LEAF_CN), cn("*.example.test")]),
            "repeated normal CN": x509.Name([cn(tls.LEAF_CN), cn(tls.LEAF_CN)]),
            "extra subject attribute": x509.Name([cn(tls.LEAF_CN), x509.NameAttribute(NameOID.ORGANIZATION_NAME, "extra")]),
            "empty subject": x509.Name([]),
        }
        cases = {label: (self.rewrite(leaf, ca_key, subject=subject), ca) for label, subject in subjects.items()}
        bad_ca_name = x509.Name([*ca.subject, cn("*.example.test")])
        bad_ca = self.rewrite(ca, ca_key, subject=bad_ca_name, issuer=bad_ca_name)
        cases["CA extra CN"] = (self.rewrite(leaf, ca_key, issuer=bad_ca_name), bad_ca)
        for label, (candidate, issuer) in {"valid control": (leaf, ca), **cases}.items():
            with self.subTest(subject=label), tempfile.TemporaryDirectory(prefix="geometry-lan-cn-") as temp:
                candidate.verify_directly_issued_by(issuer)
                issuer.verify_directly_issued_by(issuer)
                if label == "valid control":
                    tls.validate_material(base.LAN_IP, candidate, leaf_key, issuer, now)
                else:
                    with self.subTest(stage="validate"):
                        with self.assertRaisesRegex(self.guard.LanRefused, "subject", msg="non-whitelisted subject was accepted"):
                            tls.validate_material(base.LAN_IP, candidate, leaf_key, issuer, now)
                directory = pathlib.Path(temp)
                (directory / "leaf.pem").write_bytes(candidate.public_bytes(ser.Encoding.PEM))
                (directory / "leaf.key").write_bytes(leaf_key.private_bytes(ser.Encoding.PEM, ser.PrivateFormat.PKCS8, ser.NoEncryption()))
                (directory / "ca.cer").write_bytes(issuer.public_bytes(ser.Encoding.DER))
                (directory / "meta.json").write_text(json.dumps({"ip": base.LAN_IP, "port": 18766}), encoding="utf-8")
                result = tls.load_or_issue(base.LAN_IP, 18766, 7, directory, now)
                self.assertEqual(result.reused, label == "valid control", "non-whitelisted subject was reused")

    @base.NEEDS_CRYPTOGRAPHY
    def test_new_material_checks_subject_before_any_persistence(self):
        from cryptography import x509
        from cryptography.hazmat.primitives import serialization as ser
        from cryptography.x509.oid import NameOID
        tls, now, leaf, ca, ca_key, leaf_key = self.issued()
        bad = self.rewrite(leaf, ca_key, subject=x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "*.example.test")]))
        material = (bad.public_bytes(ser.Encoding.PEM),
            leaf_key.private_bytes(ser.Encoding.PEM, ser.PrivateFormat.PKCS8, ser.NoEncryption()),
            ca.public_bytes(ser.Encoding.DER))
        with tempfile.TemporaryDirectory(prefix="geometry-lan-cn-issue-") as temp:
            directory = pathlib.Path(temp) / "new"
            with patch.object(tls, "issue", return_value=material):
                with self.assertRaisesRegex(self.guard.LanRefused, "subject", msg="new malicious subject reached persistence"):
                    tls.load_or_issue(base.LAN_IP, 18766, 7, directory, now)
            self.assertFalse(directory.exists(), "refused material created a persistent directory")

    @base.NEEDS_CRYPTOGRAPHY
    def test_root_constraints_do_not_claim_to_disable_client_cn_fallback(self):
        from cryptography import x509
        from cryptography.x509.oid import NameOID
        tls, _, leaf, ca, ca_key, leaf_key = self.issued()
        cn = lambda value: x509.NameAttribute(NameOID.COMMON_NAME, value)
        for label, subject in [("single wildcard", x509.Name([cn("*.example.test")])),
                               ("extra wildcard", x509.Name([cn(tls.LEAF_CN), cn("*.example.test")]))]:
            with self.subTest(subject=label):
                signed = self.rewrite(leaf, ca_key, subject=subject)
                # This signed but locally forbidden leaf demonstrates the trust-boundary limitation.
                self.assertTrue(self.chain_validates(ca, signed, leaf_key, hostname="audit.example.test"),
                                "OpenSSL CN-fallback control changed; reassess the documented platform boundary")
                self.assertFalse(self.chain_validates(ca, signed, leaf_key, hostname="audit.example.test", common_name=False))
                self.assertTrue(self.chain_validates(ca, signed, leaf_key, hostname=base.LAN_IP))
        wrong_dns = self.rewrite(leaf, ca_key, replacements=[(x509.SubjectAlternativeName([x509.DNSName("audit.example.test")]), False)])
        self.assertFalse(self.chain_validates(ca, wrong_dns, leaf_key, hostname="audit.example.test"))

    @base.NEEDS_CRYPTOGRAPHY
    def test_certificate_total_validity_never_exceeds_seven_days(self):
        _, _, leaf, ca, _, _ = self.issued()
        for label, cert in (("CA", ca), ("leaf", leaf)):
            with self.subTest(cert=label):
                self.assertLessEqual(certificate_utc(cert, "not_valid_after") - certificate_utc(cert, "not_valid_before"),
                                     dt.timedelta(days=7), "certificate total validity exceeds seven days")

    @base.NEEDS_CRYPTOGRAPHY
    def test_signed_noncompliant_saved_material_is_not_reused(self):
        import json
        from cryptography import x509
        from cryptography.hazmat.primitives import serialization as ser
        from cryptography.x509.oid import ExtendedKeyUsageOID
        tls, now, leaf, ca, ca_key, leaf_key = self.issued()
        usage = lambda **grants: x509.KeyUsage(**{name: grants.get(name, False) for name in
            ("digital_signature", "content_commitment", "key_encipherment", "data_encipherment", "key_agreement",
             "key_cert_sign", "crl_sign", "encipher_only", "decipher_only")})
        cases = {
            "missing name constraints": (leaf, self.rewrite(ca, ca_key, omit=(x509.NameConstraints,))),
            "CA validity 365 days": (leaf, self.rewrite(ca, ca_key, after=now + dt.timedelta(days=365))),
            "leaf validity 365 days": (self.rewrite(leaf, ca_key, after=now + dt.timedelta(days=365)), ca),
            "CA not yet valid": (leaf, self.rewrite(ca, ca_key, before=now + dt.timedelta(hours=1))),
            "leaf not yet valid": (self.rewrite(leaf, ca_key, before=now + dt.timedelta(hours=1)), ca),
            "CA expired": (leaf, self.rewrite(ca, ca_key, before=now-dt.timedelta(days=2), after=now-dt.timedelta(days=1))),
            "leaf outlives CA": (leaf, self.rewrite(ca, ca_key, after=now+dt.timedelta(days=1))),
            "CA not a CA": (leaf, self.rewrite(ca, ca_key, replacements=[(x509.BasicConstraints(False, None), True)])),
            "CA path length": (leaf, self.rewrite(ca, ca_key, replacements=[(x509.BasicConstraints(True, 1), True)])),
            "CA key usage": (leaf, self.rewrite(ca, ca_key, replacements=[(usage(digital_signature=True), True)])),
            "leaf is a CA": (self.rewrite(leaf, ca_key, replacements=[(x509.BasicConstraints(True, 0), True)]), ca),
            "leaf key usage": (self.rewrite(leaf, ca_key, replacements=[(usage(key_cert_sign=True), True)]), ca),
            "leaf EKU": (self.rewrite(leaf, ca_key, replacements=[(x509.ExtendedKeyUsage([ExtendedKeyUsageOID.CLIENT_AUTH]), False)]), ca),
            "CA EKU excludes servers": (leaf, self.rewrite(ca, ca_key, replacements=[
                (x509.ExtendedKeyUsage([ExtendedKeyUsageOID.CLIENT_AUTH]), False)])),
            "noncritical constraints": (leaf, self.rewrite(ca, ca_key, replacements=[
                (ca.extensions.get_extension_for_class(x509.NameConstraints).value, False)])),
        }
        for label, (bad_leaf, bad_ca) in cases.items():
            with self.subTest(policy=label), tempfile.TemporaryDirectory(prefix="geometry-lan-policy-") as root:
                directory = pathlib.Path(root)
                bad_leaf.verify_directly_issued_by(bad_ca)  # failures must be policy failures, not a broken signature
                (directory / "leaf.pem").write_bytes(bad_leaf.public_bytes(ser.Encoding.PEM))
                (directory / "leaf.key").write_bytes(leaf_key.private_bytes(ser.Encoding.PEM, ser.PrivateFormat.PKCS8, ser.NoEncryption()))
                (directory / "ca.cer").write_bytes(bad_ca.public_bytes(ser.Encoding.DER))
                (directory / "meta.json").write_text(json.dumps({"ip": base.LAN_IP, "port": 18766}), encoding="utf-8")
                result = tls.load_or_issue(base.LAN_IP, 18766, 7, directory, now)
                self.assertFalse(result.reused, f"saved material bypassed policy: {label}")

    @base.NEEDS_CRYPTOGRAPHY
    def test_new_material_is_validated_before_any_persistence(self):
        from cryptography import x509
        from cryptography.hazmat.primitives import serialization as ser
        tls, now, leaf, ca, ca_key, leaf_key = self.issued()
        bad_ca = self.rewrite(ca, ca_key, omit=(x509.NameConstraints,))
        fabricated = (leaf.public_bytes(ser.Encoding.PEM), leaf_key.private_bytes(ser.Encoding.PEM,
            ser.PrivateFormat.PKCS8, ser.NoEncryption()), bad_ca.public_bytes(ser.Encoding.DER))
        with tempfile.TemporaryDirectory(prefix="geometry-lan-issue-") as root, \
                patch.object(tls, "issue", return_value=fabricated):
            target = pathlib.Path(root) / "material"
            with self.assertRaises(self.guard.LanRefused, msg="new material bypassed shared certificate policy"):
                tls.load_or_issue(base.LAN_IP, 18766, 7, target, now)
            self.assertFalse(target.exists(), "noncompliant new material was written to disk")


class SocketReview(base.LanCase):
    def test_denied_late_body_is_drained_after_response_before_socket_release(self):
        gate, _, _ = self.start_lan()
        body = b'{"cmd":"dump"}'
        drained, received = threading.Event(), bytearray()
        real_socket = self.mod.socket
        def observe_recv(sock, limit):
            chunk = real_socket.socket.recv(sock, limit)
            received.extend(chunk)
            if received == body:
                drained.set()
            return chunk
        observed_socket = types.SimpleNamespace(socket=types.SimpleNamespace(
            recv=observe_recv, shutdown=real_socket.socket.shutdown),
            SHUT_WR=real_socket.SHUT_WR, SHUT_RDWR=real_socket.SHUT_RDWR)
        with patch.object(self.mod, "socket", observed_socket):
            with socket.create_connection(("127.0.0.1", gate.config.port), timeout=3) as client:
                client.sendall((f"POST /api HTTP/1.1\r\nHost: {base.LAN_IP}:{gate.config.port}\r\n"
                    f"Origin: {gate.config.origin}\r\nContent-Length: {len(body)}\r\n\r\n").encode())
                header = b""
                while b"\r\n\r\n" not in header:
                    packet = client.recv(4096)
                    self.assertTrue(packet, "denied connection closed before its response")
                    header += packet
                self.assertIn(b" 403 ", header.split(b"\r\n", 1)[0])
                self.assertEqual(received, b"", "body was consumed before the refusal reached the client")
                try:
                    client.sendall(body)
                    client.shutdown(socket.SHUT_WR)
                except (BrokenPipeError, ConnectionResetError):
                    pass  # The assertion below still rejects a prematurely released socket.
                self.assertTrue(drained.wait(2), "refused late body was not drained after the response")
                self.assertEqual(bytes(received), body)
        self.assertEqual(self.process.stdin.getvalue(), b"", "rejected body reached the native bridge")

    def start_review_lan(self, category_query=lambda ip: "Private", **overrides):
        config = self.guard.LanConfig(ip=base.LAN_IP, port=base.free_port(), poll=0.02, **overrides)
        gate = self.guard.LanGate(config, log=self.logs.append)
        server = self.mod.LanHTTPServer(("127.0.0.1", config.port), gate, context_factory=self.lan_context)
        mode = self.mod.LanMode(gate, server, log=self.logs.append)
        # Attributes are injectable on the old head too: absent monitoring fails
        # a behavioral assertion instead of raising an unknown-keyword error.
        mode.category_query = category_query
        mode.network_interval = 0.04
        mode.network_timeout = 0.1
        mode.start()
        self.addCleanup(mode.stop)
        return gate, server, mode

    def test_missing_fetch_metadata_is_compatible_but_duplicates_are_refused(self):
        gate, _, _ = self.start_review_lan(pair_interval=0)
        reply = self.pair(gate, headers=[("Sec-Fetch-Site", "same-origin")])
        self.assertEqual(reply.status, 204)
        cookie = reply.headers["set-cookie"].split(";", 1)[0]
        for label, headers, expected in (
                ("same-origin", [("Sec-Fetch-Site", "same-origin")], 200),
                # P-048: Safari before iOS 16.4 omits Fetch Metadata. Host,
                # SameSite=Strict and the authenticated cookie still apply.
                ("legacy Safari", [], 200),
                ("duplicate", [("Sec-Fetch-Site", "same-origin")] * 2, 403),
                ("illegal", [("Sec-Fetch-Site", "same-site")], 403)):
            with self.subTest(case=label):
                self.assertEqual(self.send(gate.config.port, "GET", "/runtime", cookie=cookie,
                    headers=headers).status, expected, f"Fetch Metadata policy failed: {label}")

    def test_two_ports_keep_their_cookies_sessions_and_worlds(self):
        jar = http.cookiejar.CookieJar()
        endpoints = [self.start_review_lan(pair_interval=0) for _ in range(2)]
        expected = {}
        for gate, _, _ in endpoints:
            reply = self.pair(gate, headers=[("Sec-Fetch-Site", "same-origin")])
            self.assertEqual(reply.status, 204)
            headers = email.message.Message()
            for key, value in reply.header_list:
                headers.add_header(key, value)
            jar.extract_cookies(types.SimpleNamespace(info=lambda h=headers: h), urllib.request.Request(gate.config.origin))
            request = urllib.request.Request(gate.config.origin + "/runtime")
            jar.add_cookie_header(request)
            response = self.send(gate.config.port, "GET", "/runtime", cookie=request.get_header("Cookie"))
            self.assertEqual(response.status, 200)
            expected[gate.config.port] = __import__("json").loads(response.body)["session"]
        for gate, _, _ in endpoints * 2:
            request = urllib.request.Request(gate.config.origin + "/runtime")
            jar.add_cookie_header(request)
            response = self.send(gate.config.port, "GET", "/runtime", cookie=request.get_header("Cookie"))
            self.assertEqual(response.status, 200, "second port overwrote the first port's cookie")
            self.assertEqual(__import__("json").loads(response.body)["session"], expected[gate.config.port],
                             "interleaved requests replaced a device's world")
        self.assertEqual(len(jar), 2)
        self.assertEqual(len(set(expected.values())), 2)
        self.assertFalse(self.mod.root_context.closed)

    def test_delayed_pair_bodies_do_not_stockpile_comparison_slots(self):
        gate, server, _ = self.start_review_lan(pair_interval=0.2)
        clients = []
        self.addCleanup(lambda: [client.close() for client in clients])
        for _ in range(3):
            client = socket.create_connection(("127.0.0.1", gate.config.port), timeout=3)
            clients.append(client)
            client.sendall((f"POST /lan/pair HTTP/1.1\r\nHost: {gate.config.host}\r\n"
                            f"Origin: {gate.config.origin}\r\nSec-Fetch-Site: same-origin\r\n"
                            "Content-Length: 1\r\n\r\n").encode())
            time.sleep(0.25)
        with patch.object(self.guard, "normalize_code", wraps=self.guard.normalize_code) as compare:
            for client in clients:
                client.sendall(b"x")
            statuses = []
            for client in clients:
                response = http.client.HTTPResponse(client)
                response.begin()
                statuses.append(response.status)
                response.read()
            self.assertEqual(sorted(statuses), [403, 429, 429], "delayed bodies stockpiled pairing comparison slots")
            self.assertEqual(compare.call_count, 1, "more than one pairing code was evaluated in the burst")
        self.assertEqual(gate.paired, 0)
        self.assertEqual(len(gate.display_codes()), 1)

    def test_expired_pair_body_is_cut_before_watchdog_poll(self):
        # Disable only the scanner; actual request completion must enforce the
        # same accept deadline. No sleep races against a scanner are involved.
        with patch.object(self.mod.LanHTTPServer, "_watch", return_value=None):
            gate, server, _ = self.start_review_lan(header_deadline=0.1)
        client = socket.create_connection(("127.0.0.1", gate.config.port), timeout=3)
        self.addCleanup(client.close)
        code = gate.display_codes()[0].encode()
        client.sendall((f"POST /lan/pair HTTP/1.1\r\nHost: {gate.config.host}\r\nOrigin: {gate.config.origin}\r\n"
                        f"Content-Length: {len(code)}\r\n\r\n").encode())
        time.sleep(0.2)
        client.sendall(code)
        response = b""
        try:
            response = client.recv(4096)
        except OSError:
            pass
        self.assertEqual(response, b"", "expired pairing body escaped its accept deadline")
        self.assertEqual(gate.paired, 0, "expired pairing body consumed a code")

    def test_profile_changes_missing_ip_and_query_errors_close_lan(self):
        cases = [("Public", lambda ip: "Public"), ("missing IP", lambda ip: ""),
                 ("query error", Mock(side_effect=OSError("synthetic missing interface")))]
        for label, query in cases:
            with self.subTest(case=label):
                gate, server, mode = self.start_review_lan(category_query=query)
                self.assertTrue(mode.closed.wait(1.5), f"network profile monitor did not close LAN: {label}")
                self.assertTrue(gate.closed)
                self.assertEqual(gate.sessions, set())
                self.assertTrue(base.refused("127.0.0.1", gate.config.port))

    def test_network_query_timeout_closes_lan_without_blocking_ttl(self):
        for ttl, expected in ((10, "網路"), (0.08, "TTL")):
            release = threading.Event()
            self.addCleanup(release.set)
            def stalled(ip):
                release.wait(3)
                return "Private"
            gate, _, mode = self.start_review_lan(category_query=stalled, ttl=ttl)
            mode.network_timeout = 0.3
            self.assertTrue(mode.closed.wait(1.3), "blocked network query prevented LAN shutdown")
            self.assertIn(expected, mode.reason)
            release.set()

    def test_busy_bridge_shutdown_reaps_world_before_stop_returns(self):
        gate, server, mode = self.start_review_lan(pair_interval=0)
        reply = self.pair(gate)
        cookie = reply.headers["set-cookie"].split(";", 1)[0]
        self.assertEqual(self.send(gate.config.port, "GET", "/runtime", cookie=cookie).status, 200)
        native, responses, process = self.lan_bridges[0]
        self.mod.BRIDGE_TIMEOUT = 30
        process.terminate.side_effect = lambda: responses.put(b"")
        result = {}
        def ask():
            self.mod.request_context.native = native
            result["reply"] = self.mod.ask_bridge("dump")
        command = threading.Thread(target=ask, daemon=True)
        command.start()
        deadline = time.monotonic() + 1
        while not process.stdin.getvalue() and time.monotonic() < deadline:
            time.sleep(0.01)
        self.assertEqual(process.stdin.getvalue(), b"dump\n")
        stopper = threading.Thread(target=mode.stop, daemon=True)
        stopper.start()
        try:
            self.assertTrue(mode.closed.wait(2.5), "busy bridge was not reclaimed before LAN shutdown")
            stopper.join(0.5)
            self.assertFalse(stopper.is_alive(), "stop did not return after complete shutdown")
            command.join(0.5)
            self.assertFalse(command.is_alive())
            self.assertTrue(native.closed)
            process.terminate.assert_called_once_with()
            self.assertFalse(self.mod.root_context.closed)
        finally:
            responses.put(b"")
            command.join(1)
            stopper.join(2)

    def test_parser_failures_are_blank_and_never_dispatch(self):
        gate, server, _ = self.start_review_lan()
        cases = [(b"BROKEN REQUEST LINE EXTRA HTTP/1.1\r\n\r\n", True),
                 # Unsupported versions cannot safely receive an HTTP response.
                 (b"GET / HTTP/9.9\r\nHost: " + gate.config.host.encode() + b"\r\n\r\n", False),
                 (b"GET / HTTP/1.1\r\nHost: " + gate.config.host.encode() + b"\r\nX-Long: " + b"a"*65537 + b"\r\n\r\n", True)]
        for request, can_respond in cases:
            with self.subTest(prefix=request[:40]), \
                    patch.object(gate, "check", wraps=gate.check) as check:
                with socket.create_connection(("127.0.0.1", gate.config.port), timeout=3) as client:
                    client.sendall(request)
                    data = bytearray()
                    while True:
                        chunk = client.recv(65536)
                        if not chunk:
                            break
                        data.extend(chunk)
                self.assertEqual(check.call_count, 0, "parser rejection was confused with gate rejection")
                if can_respond:
                    self.assertTrue(data.startswith(b"HTTP/1.0 403"), "parser leaked a different unauthenticated response")
                    self.assertEqual(bytes(data).split(b"\r\n\r\n", 1)[1], b"", "parser error exposed an HTML body")
                else:
                    self.assertEqual(bytes(data), b"", "unsupported HTTP version received diagnostic content")
                self.assertNotIn(b"X-Geometry-Session", data)
                self.assertEqual(server.contexts, {})
        self.assertEqual(self.process.stdin.getvalue(), b"")


if __name__ == "__main__":
    unittest.main()
