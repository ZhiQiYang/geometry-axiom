import importlib.util
import json
import os
from pathlib import Path
import sys
import tempfile
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
