"""GEO-261 cost: process-local reuse of the host source inventory and binary digest.

source_closure.current_identity() runs before and after every native model call. It may
reuse a complete inventory only while every watched directory and listed file keeps the
stat signature captured with it. These negative controls edit real files in one process
and require the change to be seen; the last test re-runs the same controls with a memo
that always hits and requires every one of them to fail.
"""
from contextlib import ExitStack
import os
from pathlib import Path
import sys
import tempfile
import time
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
for directory in (ROOT / "geometry-app", ROOT / "geometry-core", ROOT / "geometry-templates/woodworking"):
    if str(directory) not in sys.path:
        sys.path.insert(0, str(directory))

from geometry_app import source_closure  # noqa: E402

FILES = {
    "geometry-core/geometry_kernel/evaluator.py": b"value = 'kernel-a'\n",
    "geometry-core/modeling/__init__.py": b"value = 'facade-a'\n",
    "geometry-app/geometry_app/provider.py": b"value = 'host-a'\n",
    "geometry-templates/woodworking/geometry_woodworking/catalog.json": b"{\"value\": \"template-a\"}\n",
    "current_geometry.c": b"int core_a;\n",
    "geometry-core/kernel/candidate.c": b"int kernel_a;\n",
    "geometry-core/deep/nested/rules.inc": b"int nested_a;\n",
    "geometry-app/native/world_candidate.inc": b"int host_a;\n",
    "geometry-templates/woodworking/native/members.h": b"int wood_a;\n",
}
TICK = 0.05  # longer than one filesystem timestamp tick on ext4, NTFS and drvfs


def reference(root):
    """The original, never-memoized inventory of the same layout."""
    return tuple((name, source_closure._hash(path, text=True)) for name, path in source_closure.source_paths(root))


class MemoFixture:
    def __init__(self, test):
        self.test = test
        stack = ExitStack()
        test.addCleanup(stack.close)
        self.root = Path(stack.enter_context(tempfile.TemporaryDirectory(prefix="source-closure-memo-")))
        for name, data in FILES.items():
            path = self.root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
        self.program = self.root / "adapter.bin"
        self.program.write_bytes(b"native-adapter-a")
        # Timestamps written above are within the racy window of the real clock.
        # Advance only the memo's clock so this process may store them: detection
        # must then come from the signatures themselves, not from racy refusal.
        stack.enter_context(mock.patch.object(source_closure, "_now_ns",
                                              side_effect=lambda: time.time_ns() + 10 * source_closure._RACY_NS))
        stack.enter_context(mock.patch.dict(source_closure._INVENTORIES, clear=True))
        stack.enter_context(mock.patch.dict(source_closure._BINARIES, clear=True))
        self.hashes = 0
        original = source_closure._hash

        def counted(path, *, text):
            self.hashes += 1
            return original(path, text=text)
        stack.enter_context(mock.patch.object(source_closure, "_hash", side_effect=counted))

    def inventory(self):
        return source_closure.source_inventory(self.root)

    def armed(self):
        """Fill the memo and prove the next call is served from it."""
        first = self.inventory()
        self.hashes = 0
        self.test.assertEqual(first, self.inventory())
        self.test.assertEqual(0, self.hashes, "unchanged sources must be reused without rehashing")
        time.sleep(TICK)
        return first


class SourceClosureMemoTests(unittest.TestCase):
    # ---- negative controls (each must fail when the memo always hits) ----
    def control_content_edit(self):
        fixture = MemoFixture(self)
        before = fixture.armed()
        (fixture.root / "geometry-core/kernel/candidate.c").write_bytes(b"int kernel_changed;\n")
        after = fixture.inventory()
        self.assertNotEqual(before, after)
        self.assertEqual(reference(fixture.root), after)

    def control_same_size_edit_with_restored_mtime(self):
        fixture = MemoFixture(self)
        before = fixture.armed()
        path = fixture.root / "geometry-app/geometry_app/provider.py"
        status = path.stat()
        path.write_bytes(b"value = 'host-b'\n")
        os.utime(path, ns=(status.st_atime_ns, status.st_mtime_ns))
        self.assertEqual((status.st_size, status.st_mtime_ns), (path.stat().st_size, path.stat().st_mtime_ns))
        after = fixture.inventory()
        self.assertNotEqual(before, after)
        self.assertEqual(reference(fixture.root), after)

    def control_mtime_only_change_rehashes(self):
        fixture = MemoFixture(self)
        before = fixture.armed()
        path = fixture.root / "geometry-core/deep/nested/rules.inc"
        status = path.stat()
        os.utime(path, ns=(status.st_atime_ns, status.st_mtime_ns + 7_000_000_000))
        fixture.hashes = 0
        self.assertEqual(before, fixture.inventory())
        self.assertEqual(len(FILES), fixture.hashes, "a changed signature recomputes the whole inventory")

    def control_added_file_in_new_nested_directory(self):
        fixture = MemoFixture(self)
        before = fixture.armed()
        path = fixture.root / "geometry-templates/woodworking/geometry_woodworking/nested/new_adapter.py"
        path.parent.mkdir()
        path.write_bytes(b"new adapter\n")
        after = fixture.inventory()
        self.assertNotEqual(before, after)
        self.assertIn("geometry-templates/woodworking/geometry_woodworking/nested/new_adapter.py", dict(after))
        self.assertEqual(reference(fixture.root), after)

    def control_removed_file(self):
        fixture = MemoFixture(self)
        before = fixture.armed()
        (fixture.root / "geometry-templates/woodworking/native/members.h").unlink()
        after = fixture.inventory()
        self.assertNotEqual(before, after)
        self.assertEqual(reference(fixture.root), after)

    def control_replaced_file(self):
        fixture = MemoFixture(self)
        before = fixture.armed()
        path = fixture.root / "current_geometry.c"
        status = path.stat()
        replacement = path.with_name("replacement.tmp")
        replacement.write_bytes(b"int core_b;\n")
        os.utime(replacement, ns=(status.st_atime_ns, status.st_mtime_ns))
        os.replace(replacement, path)
        after = fixture.inventory()
        self.assertNotEqual(before, after)
        self.assertEqual(reference(fixture.root), after)

    def control_current_identity_turns_stale(self):
        fixture = MemoFixture(self)
        layout = source_closure._layout
        self.enterContext(mock.patch.object(source_closure, "_layout",
            side_effect=lambda repository=None: layout(fixture.root if repository is None else repository)))
        self.enterContext(mock.patch.object(source_closure, "_LOADED", source_closure.source_inventory()))
        self.assertTrue(source_closure.current_identity()["fresh"])
        fixture.hashes = 0
        self.assertTrue(source_closure.current_identity()["fresh"])
        self.assertEqual(0, fixture.hashes)
        time.sleep(TICK)
        path = fixture.root / "geometry-core/modeling/__init__.py"
        status = path.stat()
        path.write_bytes(b"value = 'facade-b'\n")
        os.utime(path, ns=(status.st_atime_ns, status.st_mtime_ns))
        self.assertFalse(source_closure.current_identity()["fresh"])

    def control_binary_same_size_rewrite(self):
        fixture = MemoFixture(self)
        first = source_closure.binary_identity(fixture.program)
        fixture.hashes = 0
        self.assertEqual(first, source_closure.binary_identity(fixture.program))
        self.assertEqual(0, fixture.hashes, "an unchanged adapter must be reused without rehashing")
        time.sleep(TICK)
        status = fixture.program.stat()
        fixture.program.write_bytes(b"native-adapter-b")
        os.utime(fixture.program, ns=(status.st_atime_ns, status.st_mtime_ns))
        second = source_closure.binary_identity(fixture.program)
        self.assertNotEqual(first, second)
        self.assertEqual(source_closure._hash(fixture.program, text=False), second[2])

    CONTROLS = ("control_content_edit", "control_same_size_edit_with_restored_mtime",
                "control_mtime_only_change_rehashes", "control_added_file_in_new_nested_directory",
                "control_removed_file", "control_replaced_file", "control_current_identity_turns_stale",
                "control_binary_same_size_rewrite")

    def test_content_edit_is_detected(self):
        self.control_content_edit()

    def test_same_size_edit_with_restored_mtime_is_detected(self):
        self.control_same_size_edit_with_restored_mtime()

    def test_mtime_only_change_recomputes_the_whole_inventory(self):
        self.control_mtime_only_change_rehashes()

    def test_added_file_in_new_nested_directory_is_detected(self):
        self.control_added_file_in_new_nested_directory()

    def test_removed_file_is_detected(self):
        self.control_removed_file()

    def test_replaced_file_is_detected(self):
        self.control_replaced_file()

    def test_current_identity_turns_stale_after_same_size_edit(self):
        self.control_current_identity_turns_stale()

    def test_binary_identity_detects_same_size_rewrite(self):
        self.control_binary_same_size_rewrite()

    # ---- positive and racy behaviour ----
    def test_memoized_inventory_equals_the_original_computation(self):
        fixture = MemoFixture(self)
        self.assertEqual(reference(fixture.root), fixture.armed())
        self.assertEqual(reference(fixture.root), fixture.inventory())

    def test_recent_timestamps_are_never_memoized(self):
        fixture = MemoFixture(self)
        with mock.patch.object(source_closure, "_now_ns", side_effect=time.time_ns):
            fixture.inventory()
            fixture.hashes = 0
            fixture.inventory()
            self.assertEqual(len(FILES), fixture.hashes, "just-written sources stay within the racy window")
            source_closure.binary_identity(fixture.program)
            fixture.hashes = 0
            source_closure.binary_identity(fixture.program)
            self.assertEqual(1, fixture.hashes)

    def test_real_repository_inventory_matches_original(self):
        with mock.patch.dict(source_closure._INVENTORIES, clear=True):
            self.assertEqual(reference(ROOT), source_closure.source_inventory(ROOT))
            self.assertEqual(reference(ROOT), source_closure.source_inventory(ROOT))

    # ---- mutation: a memo that always hits must turn every control red ----
    def test_every_control_fails_when_the_memo_always_hits(self):
        for name in self.CONTROLS:
            with self.subTest(control=name), \
                    mock.patch.object(source_closure, "_memo_valid", return_value=True), \
                    mock.patch.object(source_closure, "_binary_memo_valid", return_value=True):
                with self.assertRaises(AssertionError):
                    getattr(self, name)()


if __name__ == "__main__":
    unittest.main()
