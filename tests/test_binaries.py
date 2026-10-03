"""Public, non-destructive binary freshness oracles; fixture bytes are never executed."""
import hashlib
import io
import json
import os
import shutil
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent))
import binaries
import _bridge
import run_all


class BinaryFreshnessTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='binary-freshness-')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.out = self.root / 'out'
        self.out.mkdir()
        (self.root / 'current_geometry.c').write_bytes(b'public source\r\n')
        self.b = binaries.Binary('bridge', 'bridge', 'current_geometry.c', [], [], [],
                                 ['GEOMETRY_TEST_BRIDGE'], smoke='bridge')
        for name, value in [('ROOT', self.root), ('OUT_DIR', self.out),
                            ('REGISTRY', [self.b]), ('BY_NAME', {'bridge': self.b})]:
            p = patch.object(binaries, name, value)
            p.start()
            self.addCleanup(p.stop)
        self.compile = patch.object(binaries, '_compile', side_effect=self.fake_compile).start()
        self.addCleanup(patch.stopall)
        self.smoke = patch.object(binaries, 'smoke_with_sac_retry', return_value=None).start()

    def fake_compile(self, binary, source):
        binary.path.write_bytes(b'public fixture\r\nnever execute')
        return 0, '', False

    def build(self):
        result = binaries.build_one(self.b, log=lambda *_: None)
        self.assertTrue(result.ok, result.detail)
        return result

    def tamper(self, path=None):
        path = path or self.b.path
        before = path.stat()
        data = path.read_bytes()
        path.write_bytes(bytes([data[0] ^ 1]) + data[1:])
        os.utime(path, ns=(before.st_atime_ns, before.st_mtime_ns))
        self.assertEqual(path.stat().st_size, before.st_size)
        self.assertEqual(path.stat().st_mtime_ns, before.st_mtime_ns)

    def test_same_size_mtime_byte_change_is_stale_and_not_exported(self):
        self.build()
        self.tamper()
        info = binaries.inspect_one(self.b)
        self.assertEqual(info.state, 'stale')
        self.assertIn('SHA-256', info.reason)
        self.assertEqual(binaries.env_vars({'bridge': info}), {})
        self.assertEqual(self.smoke.call_count, 1)  # only mock smoke before tamper

    def test_fresh_reuses_without_compile_smoke_or_metadata_write(self):
        self.assertEqual(self.build().status, 'built')
        before = (self.b.path.stat(), self.b.sidecar.read_bytes(), self.b.sidecar.stat())
        self.assertEqual(self.build().status, 'reused')
        self.assertEqual(before, (self.b.path.stat(), self.b.sidecar.read_bytes(), self.b.sidecar.stat()))
        self.assertEqual(self.compile.call_count, 1)
        self.assertEqual(self.smoke.call_count, 1)

    def test_sidecar_records_raw_binary_hash(self):
        self.build()
        side = json.loads(self.b.sidecar.read_text())
        raw = hashlib.sha256(self.b.path.read_bytes()).hexdigest()
        self.assertEqual(side['exe_sha256'], raw)
        self.assertNotEqual(raw, binaries._normalized_sha(self.b.path))
        self.assertEqual(side['fingerprint'], binaries.compute_fingerprint(self.b)[0])

    def test_missing_binary_is_missing(self):
        self.assertEqual(binaries.inspect_one(self.b).state, 'missing')

    def test_missing_legacy_and_malformed_sidecars_are_stale(self):
        self.build()
        valid = json.loads(self.b.sidecar.read_text())
        for data in [None, '{bad', '[]', 'null', '42', '{"files": []}',
                     json.dumps({k: v for k, v in valid.items() if k != 'exe_sha256'}),
                     json.dumps({**valid, 'exe_sha256': '0' * 64}),
                     json.dumps({**valid, 'fingerprint': 'old', 'files': 42})]:
            with self.subTest(data=data):
                self.b.sidecar.unlink(missing_ok=True)
                if data is not None:
                    self.b.sidecar.write_text(data)
                self.assertEqual(binaries.inspect_one(self.b).state, 'stale')

    def test_source_and_command_change_stale_but_crlf_checkout_does_not(self):
        self.build()
        (self.root / 'current_geometry.c').write_bytes(b'public source\n')
        self.assertEqual(binaries.inspect_one(self.b).state, 'fresh')
        self.b.posix_flags.append('-changed')
        self.b.win_flags.append('/changed')
        self.assertEqual(binaries.inspect_one(self.b).state, 'stale')
        self.b.posix_flags.clear()
        self.b.win_flags.clear()
        (self.root / 'current_geometry.c').write_bytes(b'changed source\n')
        self.assertEqual(binaries.inspect_one(self.b).state, 'stale')

    def test_blocked_pending_retries_without_recompile_and_then_publishes(self):
        self.smoke.return_value = 'winerror=4551'
        self.assertEqual(binaries.build_one(self.b).status, 'blocked')
        self.assertFalse(self.b.sidecar.exists())
        self.assertEqual(binaries.inspect_one(self.b).state, 'stale')
        pend = json.loads(binaries._pending_path(self.b).read_text())
        self.assertEqual(pend['exe_sha256'], hashlib.sha256(self.b.path.read_bytes()).hexdigest())
        self.smoke.return_value = None
        self.assertEqual(self.build().status, 'built')
        self.assertEqual(self.compile.call_count, 1)
        self.assertFalse(binaries._pending_path(self.b).exists())

    def test_tampered_pending_is_never_smoked_before_recompile(self):
        self.smoke.return_value = 'winerror=4551'
        binaries.build_one(self.b)
        self.tamper()
        self.assertFalse(binaries._pending_matches(self.b, binaries.compute_fingerprint(self.b)[0]))
        self.smoke.return_value = None
        self.compile.side_effect = lambda b, src: (1, 'controlled failure', False)
        self.assertEqual(binaries.build_one(self.b).status, 'compile-failed')
        self.assertEqual(self.smoke.call_count, 1)
        self.assertFalse(self.b.sidecar.exists())
        self.assertFalse(binaries._pending_path(self.b).exists())

    def test_bad_and_legacy_pending_cannot_authorize_reuse(self):
        self.smoke.return_value = 'winerror=4551'
        binaries.build_one(self.b)
        valid = json.loads(binaries._pending_path(self.b).read_text())
        for data in ['[]', 'null', '{bad', json.dumps({k: v for k, v in valid.items() if k != 'exe_sha256'})]:
            with self.subTest(data=data):
                binaries._pending_path(self.b).write_text(data)
                self.assertFalse(binaries._pending_matches(self.b, valid['fingerprint']))

    def test_source_change_during_compile_refuses_smoke_and_sidecar(self):
        def compile_changed(b, src):
            self.fake_compile(b, src)
            src.write_bytes(b'changed during build')
            return 0, '', False
        self.compile.side_effect = compile_changed
        self.assertEqual(binaries.build_one(self.b).status, 'compile-failed')
        self.smoke.assert_not_called()
        self.assertFalse(self.b.sidecar.exists())

    def test_source_or_binary_change_during_smoke_cannot_be_blessed(self):
        for kind in ['source', 'binary']:
            with self.subTest(kind=kind):
                def smoke_changed(*_):
                    if kind == 'binary':
                        self.tamper()
                    else:
                        src = self.root / 'current_geometry.c'
                        src.write_bytes(src.read_bytes() + b'changed')
                self.smoke.side_effect = smoke_changed
                self.assertEqual(binaries.build_one(self.b, force=True).status, 'compile-failed')
                self.assertFalse(self.b.sidecar.exists())

    def test_compile_and_launch_failure_leave_no_fresh_credentials(self):
        self.build()
        self.compile.return_value = (1, 'controlled failure', False)
        self.compile.side_effect = None
        self.assertEqual(binaries.build_one(self.b, force=True).status, 'compile-failed')
        self.assertFalse(self.b.sidecar.exists())
        self.compile.side_effect = self.fake_compile
        self.smoke.return_value = 'other launch error'
        self.assertEqual(binaries.build_one(self.b).status, 'compile-failed')
        self.assertFalse(self.b.sidecar.exists())
        self.assertFalse(binaries._pending_path(self.b).exists())

    def test_atomic_sidecar_write_failure_leaves_no_partial_or_fresh_record(self):
        original = os.replace
        def replace(src, dst):
            if Path(dst) == self.b.sidecar:
                raise OSError('controlled write failure')
            return original(src, dst)
        with patch.object(binaries.os, 'replace', side_effect=replace):
            self.assertEqual(binaries.build_one(self.b).status, 'compile-failed')
        self.assertFalse(self.b.sidecar.exists())
        self.assertFalse(list(self.out.glob('*.tmp')))
        self.assertEqual(binaries.inspect_one(self.b).state, 'stale')

    def test_explicit_bridge_path_is_rechecked_after_same_metadata_tamper(self):
        self.build()
        with patch.dict(os.environ, {'GEOMETRY_TEST_BRIDGE': str(self.b.path)}, clear=True):
            self.assertEqual(_bridge.find_bridge(), str(self.b.path))
            self.tamper()
            with self.assertRaises(unittest.SkipTest):
                _bridge.find_bridge()
            with patch.object(_bridge.subprocess, 'Popen') as spawn:
                with self.assertRaises(unittest.SkipTest):
                    _bridge.BridgeSession(self.b.path)
                spawn.assert_not_called()
            with patch.object(_bridge.subprocess, 'run') as run:
                with self.assertRaises(unittest.SkipTest):
                    _bridge.run_once('reset\n', bridge=self.b.path)
                run.assert_not_called()

    def test_copied_override_uses_its_own_sidecar_and_bytes(self):
        self.build()
        copied = self.root / self.b.exe
        sidecar = copied.with_name(copied.name + binaries.SIDECAR_SUFFIX)
        shutil.copy2(self.b.path, copied)
        shutil.copy2(self.b.sidecar, sidecar)
        self.assertEqual(binaries.require_fresh('bridge', copied), str(copied))
        self.tamper(copied)
        with self.assertRaises(RuntimeError):
            binaries.require_fresh('bridge', copied)
        sidecar.unlink()
        with self.assertRaises(RuntimeError):
            binaries.require_fresh('bridge', copied)
        self.assertEqual(binaries.inspect_one(self.b).state, 'fresh')

    def test_binary_hash_read_failure_is_stale(self):
        self.build()
        with patch.object(binaries, '_binary_identity', side_effect=PermissionError('controlled unreadable')):
            self.assertEqual(binaries.inspect_one(self.b).state, 'stale')

    def test_pending_atomic_write_failure_never_smokes(self):
        with patch.object(binaries.os, 'replace', side_effect=OSError('controlled pending failure')):
            self.assertEqual(binaries.build_one(self.b).status, 'compile-failed')
        self.smoke.assert_not_called()
        self.assertFalse(self.b.sidecar.exists())
        self.assertFalse(binaries._pending_path(self.b).exists())
        self.assertFalse(list(self.out.glob('*.tmp')))

    def test_cc_override_is_part_of_source_fingerprint(self):
        with patch.object(binaries, 'IS_WIN', False):
            before = binaries.compute_fingerprint(self.b)[0]
            with patch.dict(os.environ, {'CC': 'another-compiler'}):
                self.assertNotEqual(before, binaries.compute_fingerprint(self.b)[0])

    def test_full_runner_refuses_tampered_binary_without_invoking_suite(self):
        self.build()
        self.tamper()
        args = type('Args', (), {'simulate_missing': [], 'build': False, 'update_expected': False,
                                'allow_skip': False})()
        suite = run_all.Suite('py:fixture', 'unittest', [], ['bridge'], 10)
        with patch.object(run_all, 'run_suite') as run, patch.object(run_all, 'compare_expected', return_value=[]), \
                patch('sys.stdout', new_callable=io.StringIO):
            self.assertEqual(run_all.run(args, [suite], [], []), 2)
        run.assert_not_called()


if __name__ == '__main__':
    unittest.main()
