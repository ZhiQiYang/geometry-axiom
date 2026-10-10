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
        for route, path in runtime_version.static_catalog(self.root).items():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(route.encode() + b'\r\n')

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

    def test_every_vendor_type_uses_exact_bytes_for_version_and_freshness(self):
        for name in ('map.bcmap', 'font.ttf', 'font.pfb', 'image.png', 'icon.ico',
                     'image.webp', 'data.json', 'LICENSE', 'unusual.payload',
                     'docs/nested.bcmap'):
            with self.subTest(name=name):
                path = self.web / 'vendor' / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(b'old\r\n')
                snapshot = runtime_version.RuntimeSnapshot(self.root)
                stamp = path.stat()
                path.write_bytes(b'new\r\n')
                os.utime(path, ns=(stamp.st_atime_ns, stamp.st_mtime_ns))
                self.assertFalse(snapshot.fresh())
                route = '/vendor/' + name
                self.assertEqual(snapshot.vendor[route], b'old\r\n')
                current = runtime_version.RuntimeSnapshot(self.root)
                self.assertTrue(current.fresh())
                self.assertNotEqual(snapshot.version, current.version)
                self.assertEqual(current.vendor[route], b'new\r\n')

    def test_vendor_route_addition_and_deletion_require_a_new_snapshot(self):
        vendor = self.web / 'vendor'
        vendor.mkdir()
        path = vendor / 'new.bcmap'
        before = runtime_version.RuntimeSnapshot(self.root)
        path.write_bytes(b'new cmap')
        self.assertFalse(before.fresh())
        self.assertNotIn('/vendor/new.bcmap', before.static)
        after = runtime_version.RuntimeSnapshot(self.root)
        self.assertNotEqual(before.version, after.version)
        path.unlink()
        self.assertFalse(after.fresh())
        self.assertEqual(after.static['/vendor/new.bcmap'], b'new cmap')
        deleted = runtime_version.RuntimeSnapshot(self.root)
        self.assertEqual(before.version, deleted.version)
        self.assertEqual(set(before.static), set(deleted.static))

    def test_catalog_documents_reader_and_archives_are_captured_and_fingerprinted(self):
        for route, path in runtime_version.static_catalog(self.root).items():
            with self.subTest(route=route):
                original = path.read_bytes()
                snapshot = runtime_version.RuntimeSnapshot(self.root)
                stamp = path.stat()
                changed = original.replace(b'/', b'!', 1)
                path.write_bytes(changed)
                os.utime(path, ns=(stamp.st_atime_ns, stamp.st_mtime_ns))
                self.assertFalse(snapshot.fresh())
                self.assertEqual(snapshot.static[route], original)
                current = runtime_version.RuntimeSnapshot(self.root)
                self.assertNotEqual(snapshot.version, current.version)
                self.assertEqual(current.static[route], changed)
                path.write_bytes(original)

    def test_deleted_catalog_file_is_stale_and_refuses_partial_startup(self):
        route = '/examples/assembly-generation-v1.gcanvas'
        path = runtime_version.static_catalog(self.root)[route]
        original = path.read_bytes()
        snapshot = runtime_version.RuntimeSnapshot(self.root)
        path.unlink()
        self.assertFalse(snapshot.fresh())
        self.assertEqual(snapshot.static[route], original)
        with self.assertRaises(FileNotFoundError):
            runtime_version.RuntimeSnapshot(self.root)

    def test_binary_and_served_text_line_endings_never_share_a_runtime_version(self):
        paths = [self.web / 'vendor/map.bcmap', self.web / 'vendor/font.ttf',
                 self.web / 'vendor/font.pfb', self.web / 'vendor/library.js',
                 self.web / 'examples/assembly-generation-v1.gcanvas', self.web / 'app.js']
        for path in paths:
            with self.subTest(path=path.name):
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(b'bytes\r\n')
                snapshot = runtime_version.RuntimeSnapshot(self.root)
                path.write_bytes(b'bytes\n')
                self.assertFalse(snapshot.fresh())
                self.assertNotEqual(snapshot.version, runtime_version.source_version(self.root))

    def test_vendor_and_catalog_read_failures_are_stale_and_refuse_startup(self):
        path = self.web / 'vendor/map.bcmap'
        path.parent.mkdir()
        path.write_bytes(b'cmap')
        snapshot = runtime_version.RuntimeSnapshot(self.root)
        read = Path.read_bytes
        for unreadable in (path, self.web / 'examples/assembly-generation-v1.gcanvas'):
            def fail(selected):
                if selected == unreadable:
                    raise PermissionError('locked public asset')
                return read(selected)
            with self.subTest(path=unreadable), patch.object(Path, 'read_bytes', fail):
                self.assertFalse(snapshot.fresh())
                with self.assertRaises(PermissionError):
                    runtime_version.RuntimeSnapshot(self.root)

    def test_vendor_edit_during_startup_refuses_to_publish_a_mixed_capture(self):
        path = self.web / 'vendor/map.bcmap'
        path.parent.mkdir()
        path.write_bytes(b'old cmap')
        version = runtime_version._content_version

        def change_after_hash(root, contents):
            result = version(root, contents)
            path.write_bytes(b'new cmap')
            return result

        with patch.object(runtime_version, '_content_version', side_effect=change_after_hash):
            with self.assertRaisesRegex(RuntimeError, '啟動期間變更'):
                runtime_version.RuntimeSnapshot(self.root)

    def test_vendor_route_changes_during_startup_refuse_a_mixed_capture(self):
        vendor = self.web / 'vendor'
        vendor.mkdir()
        path = vendor / 'map.bcmap'
        version = runtime_version._content_version
        for operation in ('add', 'delete'):
            path.write_bytes(b'old cmap')
            added = vendor / 'added.ttf'
            added.unlink(missing_ok=True)

            def change_after_hash(root, contents):
                result = version(root, contents)
                if operation == 'add':
                    added.write_bytes(b'new font')
                else:
                    path.unlink(missing_ok=True)
                return result

            with self.subTest(operation=operation), patch.object(runtime_version, '_content_version',
                    side_effect=change_after_hash):
                with self.assertRaisesRegex(RuntimeError, '啟動期間變更'):
                    runtime_version.RuntimeSnapshot(self.root)

    def test_vendor_added_during_freshness_check_is_rejected(self):
        snapshot = runtime_version.RuntimeSnapshot(self.root)
        read = Path.read_bytes

        def add_during_read(path):
            content = read(path)
            if path == self.web / 'app.js':
                asset = self.web / 'vendor/late.bcmap'
                asset.parent.mkdir(exist_ok=True)
                asset.write_bytes(b'late cmap')
            return content

        with patch.object(Path, 'read_bytes', add_during_read):
            self.assertFalse(snapshot.fresh())

    def test_public_file_symlink_bytes_are_tracked_without_following_directory_links(self):
        vendor = self.web / 'vendor'
        vendor.mkdir()
        target = self.root / 'public-fixture.bcmap'
        target.write_bytes(b'old map')
        link = vendor / 'linked.bcmap'
        directory_link = vendor / 'directory-link'
        external_directory = self.root / 'fixture-assets'
        external_directory.mkdir()
        (external_directory / 'map.bcmap').write_bytes(b'not a routed asset')
        try:
            link.symlink_to(target)
            directory_link.symlink_to(external_directory, target_is_directory=True)
        except OSError as error:
            self.skipTest('symlinks unavailable: ' + str(error))
        snapshot = runtime_version.RuntimeSnapshot(self.root)
        self.assertEqual(snapshot.vendor['/vendor/linked.bcmap'], b'old map')
        self.assertNotIn('/vendor/directory-link/map.bcmap', snapshot.vendor)
        target.write_bytes(b'new map')
        self.assertFalse(snapshot.fresh())
        current = runtime_version.RuntimeSnapshot(self.root)
        self.assertNotEqual(snapshot.version, current.version)
        target.unlink()
        self.assertFalse(current.fresh())

    def test_retargeted_public_file_symlink_same_size_and_timestamp_is_stale(self):
        vendor = self.web / 'vendor'
        vendor.mkdir()
        first, second = self.root / 'first.bcmap', self.root / 'second.bcmap'
        first.write_bytes(b'old map')
        second.write_bytes(b'new map')
        stamp = first.stat()
        os.utime(second, ns=(stamp.st_atime_ns, stamp.st_mtime_ns))
        link = vendor / 'linked.bcmap'
        try:
            link.symlink_to(first)
        except OSError as error:
            self.skipTest('symlinks unavailable: ' + str(error))
        snapshot = runtime_version.RuntimeSnapshot(self.root)
        link.unlink()
        link.symlink_to(second)
        self.assertFalse(snapshot.fresh())
        self.assertEqual(snapshot.vendor['/vendor/linked.bcmap'], b'old map')
        current = runtime_version.RuntimeSnapshot(self.root)
        self.assertNotEqual(snapshot.version, current.version)
        self.assertEqual(current.vendor['/vendor/linked.bcmap'], b'new map')

    def test_private_projects_feedback_and_assets_are_not_runtime_sources(self):
        snapshot = runtime_version.RuntimeSnapshot(self.root)
        private_paths = [self.root / 'feedback/F-test/page.html',
                         self.root / 'private.scene', self.web / 'examples/private.gcanvas',
                         self.web / 'assets/private.png']
        for path in private_paths:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(b'private fixture bytes')
        self.assertTrue(snapshot.fresh())
        self.assertEqual(snapshot.version, runtime_version.source_version(self.root))
        self.assertTrue(set(private_paths).isdisjoint(runtime_version.source_files(self.root)))

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
