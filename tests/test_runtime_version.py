import importlib.util
import json
import os
from pathlib import Path
import sys
import tempfile
import threading
import unittest
from unittest.mock import patch
import io

WEB = Path(__file__).resolve().parents[1] / 'geometry-web'
sys.path.insert(0, str(WEB))
import runtime_version


class RuntimeVersionTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.web = self.root / 'geometry-web'
        self.web.mkdir()
        (self.root / 'geometry-core').mkdir()
        (self.root / '公理層.md').write_bytes(b'axioms\r\n')
        (self.web / 'index.html').write_bytes(b'<html><head></head><script src="app.js"></script></html>')
        (self.web / 'app.js').write_bytes(b'old app\n')

    def tearDown(self):
        self.tmp.cleanup()

    def test_live_update_cannot_mix_assets_and_marks_runtime_stale(self):
        snapshot = runtime_version.RuntimeSnapshot(self.root)
        (self.web / 'app.js').write_bytes(b'new app with new dependency\n')
        (self.web / 'grid-trial.js').write_bytes(b'new dependency\n')
        self.assertFalse(snapshot.fresh())
        self.assertEqual(snapshot.assets['/app.js'], b'old app\n')
        self.assertNotIn('/grid-trial.js', snapshot.assets)
        self.assertIn(snapshot.version.encode(), snapshot.index())
        current = runtime_version.RuntimeSnapshot(self.root)
        self.assertTrue(current.fresh())
        self.assertIn('/grid-trial.js', current.assets)
        self.assertNotEqual(current.version, snapshot.version)

    def test_source_identity_ignores_checkout_line_endings_and_tracks_native_source(self):
        version = runtime_version.source_version(self.root)
        (self.root / '公理層.md').write_bytes(b'axioms\n')
        self.assertEqual(version, runtime_version.source_version(self.root))
        snapshot = runtime_version.RuntimeSnapshot(self.root)
        (self.root / 'geometry-core/new.c').write_text('changed native code')
        self.assertFalse(snapshot.fresh())

    def test_missing_script_refuses_startup_instead_of_opening_a_blank_editor(self):
        (self.web / 'index.html').write_bytes(b'<head><script src="grid-trial.js"></script></head>')
        with self.assertRaisesRegex(RuntimeError, 'grid-trial.js'):
            runtime_version.RuntimeSnapshot(self.root)

    def test_vendor_snapshot_is_immutable_and_updates_require_restart(self):
        vendor = self.web / 'vendor'
        vendor.mkdir()
        (vendor / 'library.js').write_bytes(b'old library')
        snapshot = runtime_version.RuntimeSnapshot(self.root)
        stamp = (vendor / 'library.js').stat()
        (vendor / 'library.js').write_bytes(b'new library')
        os.utime(vendor / 'library.js', ns=(stamp.st_atime_ns, stamp.st_mtime_ns))
        self.assertFalse(snapshot.fresh())
        self.assertEqual(snapshot.vendor['/vendor/library.js'], b'old library')

    def test_same_size_same_timestamp_edit_is_detected_on_every_check(self):
        snapshot = runtime_version.RuntimeSnapshot(self.root)
        app = self.web / 'app.js'
        stamp = app.stat()
        self.assertTrue(snapshot.fresh())
        app.write_bytes(b'new app\n')
        os.utime(app, ns=(stamp.st_atime_ns, stamp.st_mtime_ns))
        self.assertFalse(snapshot.fresh())

    def test_freshness_uses_canonical_text_but_binary_bytes_are_exact(self):
        wasm = self.web / 'library.wasm'
        wasm.write_bytes(b'wasm\r\n')
        snapshot = runtime_version.RuntimeSnapshot(self.root)
        (self.root / '公理層.md').write_bytes(b'axioms\n')
        self.assertTrue(snapshot.fresh())
        wasm.write_bytes(b'wasm\n')
        self.assertFalse(snapshot.fresh())

    def test_deleted_source_and_read_failure_are_stale(self):
        snapshot = runtime_version.RuntimeSnapshot(self.root)
        with patch.object(Path, 'read_bytes', side_effect=PermissionError('locked')):
            self.assertFalse(snapshot.fresh())
        (self.web / 'app.js').unlink()
        self.assertFalse(snapshot.fresh())

    def test_startup_rejects_source_change_during_capture(self):
        version = runtime_version._content_version

        def change_after_hash(root, contents):
            result = version(root, contents)
            (self.web / 'app.js').write_bytes(b'new app\n')
            return result

        with patch.object(runtime_version, '_content_version', side_effect=change_after_hash):
            with self.assertRaisesRegex(RuntimeError, '啟動期間變更'):
                runtime_version.RuntimeSnapshot(self.root)

    def test_captured_asset_bytes_are_not_reread_for_serving(self):
        read = Path.read_bytes
        reads = []

        def record(path):
            reads.append(path)
            return read(path)

        with patch.object(Path, 'read_bytes', record):
            snapshot = runtime_version.RuntimeSnapshot(self.root)
        # One read captures the version/asset; the second validates startup.
        self.assertEqual(reads.count(self.web / 'app.js'), 2)
        self.assertEqual(snapshot.assets['/app.js'], b'old app\n')

    def test_concurrent_addition_during_check_is_rejected(self):
        snapshot = runtime_version.RuntimeSnapshot(self.root)
        reading = threading.Event()
        edited = threading.Event()
        read = Path.read_bytes

        def edit():
            if reading.wait(2):
                (self.web / 'new.js').write_bytes(b'new dependency')
            edited.set()

        def read_with_edit(path):
            content = read(path)
            if path == self.web / 'app.js':
                reading.set()
                if not edited.wait(2):
                    raise RuntimeError('source edit did not finish')
            return content

        writer = threading.Thread(target=edit)
        writer.start()
        try:
            with patch.object(Path, 'read_bytes', read_with_edit):
                self.assertFalse(snapshot.fresh())
        finally:
            writer.join(2)
        self.assertFalse(writer.is_alive())

    def test_unchanged_checks_do_not_rehash_content(self):
        snapshot = runtime_version.RuntimeSnapshot(self.root)
        with patch.object(runtime_version.hashlib, 'sha256', side_effect=AssertionError('rehash')):
            self.assertTrue(snapshot.fresh())

    def test_probe_rejects_old_unknown_stale_and_other_repository_services(self):
        good = {'schema': 'geometry-runtime/1', 'fresh': True,
                'version': runtime_version.source_version(self.root), 'root': str(self.root)}
        bad = [{}, {**good, 'fresh': False}, {**good, 'version': 'old'},
               {**good, 'root': str(self.root / 'other')}]
        for status in bad + [good]:
            with self.subTest(status=status), patch.object(runtime_version, 'urlopen',
                    return_value=io.BytesIO(json.dumps(status).encode())):
                if status == good:
                    self.assertEqual(runtime_version.probe(8765, self.root), good)
                else:
                    with self.assertRaises(RuntimeError):
                        runtime_version.probe(8765, self.root)


if __name__ == '__main__':
    unittest.main()
