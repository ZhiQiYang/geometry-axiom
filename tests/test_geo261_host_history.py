"""Whole-document H history: independent byte oracles and real bridge controls.

The isolated client links only history.c. It does not include a product World,
core object, template object, parser or precompiled application. Product controls
then replace that same H object in the actual bridge's link closure.
"""
from __future__ import annotations

from pathlib import Path
import re
import shutil
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from tests import _bridge
from tests.test_geo261_native_kernel import native
from tests.test_geo261_wood_product import SCENE

MODULE = ROOT / "geometry-app/native"


def definition(source, name):
    match = re.search(r"(?m)^(?:void|bool|const void \*)\s*" + re.escape(name) + r"\(", source)
    if match is None:
        raise AssertionError("Missing history function " + name)
    start = source.index("{", match.end())
    depth, end = 1, start + 1
    while depth:
        if end >= len(source):
            raise AssertionError("Unbalanced history function " + name)
        depth += (source[end] == "{") - (source[end] == "}")
        end += 1
    return source[match.start():end]


class HistorySourceBoundary(unittest.TestCase):
    def test_history_has_no_geometry_template_or_allocation_dependency(self):
        header = (MODULE / "history.h").read_text(encoding="utf-8")
        source = (MODULE / "history.c").read_text(encoding="utf-8")
        self.assertEqual([], re.findall(r'^\s*#include\s+"([^"]+)"', header, re.M))
        self.assertEqual(["history.h"], re.findall(r'^\s*#include\s+"([^"]+)"', source, re.M))
        executable = re.sub(r"/\*.*?\*/|//[^\n]*", "", source, flags=re.S)
        self.assertNotRegex(executable, r"\b(?:World|Timber|Geo\w*|wood_\w*|malloc|calloc|realloc|free)\b")

    def test_harness_uses_only_public_history_and_independent_byte_oracles(self):
        source = (ROOT / "tests/geo261_history_harness.c").read_text(encoding="utf-8")
        self.assertEqual(["history.h"], re.findall(r'^\s*#include\s+"([^"]+)"', source, re.M))
        self.assertNotIn("current_geometry", source)
        self.assertNotIn("history.c", source)
        self.assertIn("eviction-keeps-latest-thirty-two", source)
        self.assertIn("abort-full-snapshot", source)


class HostHistory(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        build = native()
        cls.directory = build.work / "isolated-host-history"
        cls.directory.mkdir(exist_ok=True)
        for name in ("history.h", "history.c"):
            shutil.copy2(MODULE / name, cls.directory / name)
        shutil.copy2(ROOT / "tests/geo261_history_harness.c", cls.directory / "history-client.c")
        cls.client = build.compile(cls.directory / "history-client.c", "history-client")
        cls.original = build.compile(cls.directory / "history.c", "history-isolated")
        cls.exe = build.link("history-client", [cls.client, cls.original])

    def case(self, name, executable=None):
        result = subprocess.run([str(executable or self.exe), name], capture_output=True, text=True, timeout=10)
        self.assertIn(result.returncode, (0, 1), "Crash/setup error is not a history verdict: " + result.stderr)
        if result.returncode == 1:
            self.assertRegex(result.stderr, r"ASSERT:[a-z0-9-]+")
        return result

    def test_record_undo_redo_full_snapshots_and_empty_states(self):
        self.assertEqual(0, self.case("record").returncode)

    def test_thirty_two_step_bound_and_oldest_eviction(self):
        self.assertEqual(0, self.case("eviction").returncode)

    def test_failed_record_restores_evicted_entry_and_redo_bytes(self):
        self.assertEqual(0, self.case("unrecord").returncode)

    def test_group_commit_is_one_step_and_clean_group_keeps_redo(self):
        self.assertEqual(0, self.case("group").returncode)

    def test_group_abort_is_full_atomic_and_idempotent(self):
        self.assertEqual(0, self.case("abort").returncode)

    def test_restore_hook_controls_presentation_but_abort_does_not_call_it(self):
        self.assertEqual(0, self.case("callback").returncode)

    def test_clear_drops_counts_and_group_without_erasing_storage(self):
        self.assertEqual(0, self.case("clear").returncode)

    def test_one_slot_history_keeps_zero_length_moves_valid(self):
        self.assertEqual(0, self.case("single").returncode)

    def mutant(self, name, function, before, after):
        build = native()
        source = (self.directory / "history.c").read_text(encoding="utf-8")
        function_source = definition(source, function)
        self.assertEqual(1, function_source.count(before), "Mutation target must be unique: " + name)
        self.assertEqual(1, source.count(function_source))
        changed = source.replace(function_source, function_source.replace(before, after))
        path = self.directory / ("history-" + name + ".c")
        path.write_text(changed, encoding="utf-8")
        obj = build.compile(path, "history-" + name)
        return build.link("history-" + name, [self.client, obj]), obj

    def test_removing_real_history_guards_fails_named_byte_oracles(self):
        controls = (
            ("record-bytes", "app_history_record", "document, history->snapshot_size);", "history->evicted, history->snapshot_size);", "record", "record-full-snapshot"),
            ("eviction-shift", "app_history_record", "history->snapshot_size * (history->capacity - 1)", "0", "eviction", "eviction-keeps-latest-thirty-two"),
            ("eviction-limit", "app_history_record", "history->undo_count >= history->capacity", "history->undo_count + 1 >= history->capacity", "eviction", "capacity-thirty-two"),
            ("record-redo", "app_history_record", "history->redo_count = 0;", "/* preserve incorrectly */", "unrecord", "successful-record-clears-redo"),
            ("unrecord-oldest", "app_history_unrecord", "memcpy(history->undo, history->evicted, history->snapshot_size);", "/* omit restored oldest */", "unrecord", "unrecord-restores-evicted-oldest"),
            ("unrecord-redo", "app_history_unrecord", "history->redo_count = history->record_redo_count;", "history->redo_count = 0;", "unrecord", "unrecord-restores-redo-count"),
            ("unrecord-marker", "app_history_unrecord", "history->record_evicted = false;", "/* stale marker */", "unrecord", "unrecord-clears-eviction-marker"),
            ("undo-restore", "app_history_undo", "restore(document, history->undo + history->snapshot_size * --history->undo_count, opaque);", "--history->undo_count;", "callback", "undo-delegates-presentation"),
            ("redo-restore", "app_history_redo", "restore(document, history->redo + history->snapshot_size * --history->redo_count, opaque);", "--history->redo_count;", "record", "redo-direction"),
            ("group-nested", "app_history_group_begin", "if (history->grouping) return false;", "/* permit nested begin */", "group", "nested-begin-rejected"),
            ("group-clean", "app_history_group_end", "if (history->group_dirty)", "if (true)", "group", "clean-group-preserves-redo"),
            ("group-dirty", "app_history_group_end", "if (history->group_dirty)", "if (false)", "group", "dirty-group-single-step"),
            ("group-base", "app_history_group_begin", "memcpy(history->group_base, document, history->snapshot_size);", "/* no base snapshot */", "group", "group-base-keeps-first-begin"),
            ("abort-copy", "app_history_group_abort", "memcpy(document, history->group_base, history->snapshot_size);", "/* no rollback */", "abort", "abort-full-snapshot"),
            ("abort-idempotent", "app_history_group_abort", "if (!history->grouping) return;", "/* repeat stale rollback */", "abort", "abort-idempotent"),
            ("abort-dirty", "app_history_group_abort", "history->group_dirty = false;", "/* stale dirty group */", "abort", "abort-closes-group"),
            ("clear-redo", "app_history_clear", "history->redo_count = 0;", "/* stale redo */", "clear", "clear-counts-and-group"),
            ("clear-group", "app_history_clear", "history->grouping = false;", "/* stale group */", "clear", "clear-counts-and-group"),
        )
        for name, function, before, after, case, assertion in controls:
            with self.subTest(guard=name):
                self.assertEqual(0, self.case(case).returncode)
                executable, _ = self.mutant(name, function, before, after)
                result = self.case(case, executable)
                self.assertEqual(1, result.returncode, "History guard survived: " + name)
                self.assertIn("ASSERT:" + assertion, result.stderr)
                self.assertEqual(0, self.case(case).returncode)

    def product_workflow(self, executable):
        build = native()
        path = build.work / "history-product.scene"
        path.write_text(SCENE, encoding="utf-8")
        with _bridge.BridgeSession(executable) as session:
            loaded = session.command("loadfile " + str(path))
            self.assertTrue(loaded["ok"], loaded)
            before = session.command("dump")["text"]
            self.assertTrue(session.line("spec x 600")["ok"])
            changed = session.command("dump")["text"]
            self.assertNotEqual(before, changed)
            self.assertTrue(session.line("undo")["ok"])
            self.assertEqual(before, session.command("dump")["text"])
            self.assertFalse(session.line("spec x BAD")["ok"])
            self.assertEqual(before, session.command("dump")["text"])
            self.assertTrue(session.line("redo")["ok"], "product-redo-after-rejection")
            self.assertEqual(changed, session.command("dump")["text"])
            self.assertTrue(session.line("history-begin")["ok"])
            self.assertTrue(session.line("spec x 700")["ok"])
            self.assertTrue(session.line("spec x 800")["ok"])
            self.assertTrue(session.line("history-end")["ok"])
            grouped = session.command("dump")["text"]
            self.assertNotEqual(changed, grouped)
            self.assertTrue(session.line("undo")["ok"])
            self.assertEqual(changed, session.command("dump")["text"])
            self.assertTrue(session.line("redo")["ok"])
            self.assertEqual(grouped, session.command("dump")["text"])
            self.assertTrue(session.line("history-begin")["ok"])
            self.assertTrue(session.line("spec x 900")["ok"])
            self.assertFalse(session.line("not-a-command")["ok"])
            self.assertEqual(grouped, session.command("dump")["text"])
            self.assertTrue(session.line("history-abort")["ok"])
            self.assertEqual(grouped, session.command("dump")["text"])

    def test_real_bridge_retains_redo_on_failure_and_group_atomicity(self):
        self.product_workflow(native().bridge())

    def test_real_bridge_consumes_same_history_object(self):
        build = native()
        self.product_workflow(build.bridge())
        client, changed = self.mutant("product-unrecord-redo", "app_history_unrecord",
            "history->redo_count = history->record_redo_count;", "history->redo_count = 0;")
        self.assertEqual(1, self.case("unrecord", client).returncode)
        objects = build.product_objects()
        self.assertEqual(1, objects.count(build.host_history_object), "Real product must link one H history object")
        mutant = build.link("history-product-mutant", [build.bridge_object,
            *(changed if obj == build.host_history_object else obj for obj in objects)])
        with self.assertRaisesRegex(AssertionError, "product-redo-after-rejection"):
            self.product_workflow(mutant)
        self.product_workflow(build.bridge())


if __name__ == "__main__":
    unittest.main(verbosity=2)
