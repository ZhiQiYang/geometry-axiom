"""Whole-document H history: independent byte oracles and real bridge controls.

The isolated client links only history.c. It does not include a product World,
core object, template object, parser or precompiled application. Product controls
then replace that same H object in the actual bridge's link closure.
"""
from __future__ import annotations

from pathlib import Path
import json
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
from tests import geo300_scene_generator as scene_generator
from tests.test_geo261_wood_world_validation import copy_product_closure, PRODUCT_DEFINES

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

    def test_wrapped_ring_branch_group_clear_and_failed_record_keep_stack_order(self):
        # GEO-381 (#394 review F2): every operation with the ring head != 0.
        for case in ("wrap-branch", "wrap-group", "wrap-clear", "wrap-unrecord"):
            with self.subTest(case=case):
                self.assertEqual(0, self.case(case).returncode, self.case(case).stderr)

    def test_wrapped_ring_cases_fail_named_ring_withdrawals(self):
        # Each named withdrawal turns its wrap case red with a normal ASSERT.
        # The first two are ring-only bugs the 32-slot eviction case misses.
        controls = (
            ("wrap-branch-push-ignores-head", "app_history_record",
             "history->undo_head, history->undo_count++)",
             "history->record_evicted ? history->undo_head : 0, history->undo_count++)",
             "wrap-branch", "wrap-branch-undo-to-bottom"),
            ("wrap-group-redo-push-ignores-head", "app_history_redo",
             "app_history_slot(history, history->undo, history->undo_head, history->undo_count++)",
             "app_history_slot(history, history->undo, 0, history->undo_count++)",
             "wrap-group", "wrap-group-older-steps"),
            ("wrap-clear-keeps-undo", "app_history_clear",
             "history->undo_count = 0;", "/* stale undo */", "wrap-clear", "wrap-clear-counts"),
            ("wrap-unrecord-keeps-head", "app_history_unrecord",
             "history->undo_head = (history->undo_head + history->capacity - 1) % history->capacity;",
             "/* no ring rewind */", "wrap-unrecord", "wrap-unrecord-undo-order"),
        )
        for name, function, before, after, case, assertion in controls:
            with self.subTest(guard=name):
                self.assertEqual(0, self.case(case).returncode)
                executable, _ = self.mutant(name, function, before, after)
                result = self.case(case, executable)
                self.assertEqual(1, result.returncode, "Ring guard survived: " + name)
                self.assertIn("ASSERT:" + assertion, result.stderr)
                self.assertEqual(0, self.case(case).returncode)

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
            ("eviction-shift", "app_history_record", "history->undo_head = (history->undo_head + 1) % history->capacity;", "/* keep oldest slot */", "eviction", "eviction-keeps-latest-thirty-two"),
            ("eviction-limit", "app_history_record", "history->undo_count >= history->capacity", "history->undo_count + 1 >= history->capacity", "eviction", "capacity-thirty-two"),
            ("record-redo", "app_history_record", "history->redo_count = 0;", "/* preserve incorrectly */", "unrecord", "successful-record-clears-redo"),
            ("unrecord-oldest", "app_history_unrecord", "memcpy(app_history_slot(history, history->undo, history->undo_head, 0), history->evicted, history->snapshot_size);", "/* omit restored oldest */", "unrecord", "unrecord-restores-evicted-oldest"),
            ("unrecord-redo", "app_history_unrecord", "history->redo_count = history->record_redo_count;", "history->redo_count = 0;", "unrecord", "unrecord-restores-redo-count"),
            ("unrecord-marker", "app_history_unrecord", "history->record_evicted = false;", "/* stale marker */", "unrecord", "unrecord-clears-eviction-marker"),
            ("undo-restore", "app_history_undo", "restore(document, app_history_slot(history, history->undo, history->undo_head, --history->undo_count), opaque);", "--history->undo_count;", "callback", "undo-delegates-presentation"),
            ("redo-restore", "app_history_redo", "restore(document, app_history_slot(history, history->redo, history->redo_head, --history->redo_count), opaque);", "--history->redo_count;", "record", "redo-direction"),
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

    def wrapped_rejection_workflow(self, executable):
        """#394 review: a real current_geometry.c rejection after the 32-entry
        ring has wrapped (record, restore from peek_undo, unrecord), then the
        complete World undo/redo sequence."""
        build = native()
        path = build.work / "history-wrap-product.scene"
        path.write_text(SCENE, encoding="utf-8")
        with _bridge.BridgeSession(executable) as session:
            loaded = session.command("loadfile " + str(path))
            self.assertTrue(loaded["ok"], loaded)
            dumps = [session.command("dump")["text"]]
            for i in range(1, 41):
                self.assertTrue(session.line("spec x %d" % (600 + 5 * i))["ok"], i)
                dumps.append(session.command("dump")["text"])
            self.assertEqual(41, len(set(dumps)), "each edit must be a distinct World")
            self.assertFalse(session.line("spec x BAD")["ok"])
            self.assertEqual(dumps[40], session.command("dump")["text"], "product-wrap-rejection-keeps-world")
            self.assertFalse(session.line("redo")["ok"], "product-wrap-rejection-no-redo")
            for i in range(39, 7, -1):
                self.assertTrue(session.line("undo")["ok"], "product-wrap-rejection-undo-present %d" % i)
                self.assertEqual(dumps[i], session.command("dump")["text"], "product-wrap-rejection-undo-order %d" % i)
            self.assertFalse(session.line("undo")["ok"], "product-wrap-rejection-oldest-bound")
            self.assertEqual(dumps[8], session.command("dump")["text"])
            for i in range(9, 41):
                self.assertTrue(session.line("redo")["ok"], "product-wrap-rejection-redo-present %d" % i)
                self.assertEqual(dumps[i], session.command("dump")["text"], "product-wrap-rejection-redo-order %d" % i)

    def test_real_bridge_rejection_after_ring_wrap_keeps_world_history(self):
        build = native()
        self.wrapped_rejection_workflow(build.bridge())
        _, changed = self.mutant("product-wrap-unrecord-keeps-head", "app_history_unrecord",
            "history->undo_head = (history->undo_head + history->capacity - 1) % history->capacity;",
            "/* no ring rewind */")
        objects = build.product_objects()
        self.assertEqual(1, objects.count(build.host_history_object), "Real product must link one H history object")
        mutant = build.link("history-product-wrap-mutant", [build.bridge_object,
            *(changed if obj == build.host_history_object else obj for obj in objects)])
        with self.assertRaisesRegex(AssertionError, "product-wrap-rejection-undo-order"):
            self.wrapped_rejection_workflow(mutant)
        self.wrapped_rejection_workflow(build.bridge())


class HistoryRecordWork(unittest.TestCase):
    """GEO-381: the real step-by-step generator history copies a bounded number
    of snapshots per record once the 32-entry stack is full.

    A byte counter is added to a copied product closure as memcpy/memmove macros
    injected into the copied history.c. That file is #included into the bridge's
    unity translation unit, so the macros also stay in effect for the code that
    follows it in that unit. The printed number is still only app_history_record's
    own copies: the counter is zeroed at the start of app_history_record and
    printed at its end, and app_history_record calls no other copying function.
    The bound is a work count, not wall-clock time."""
    MARKER = b"GEO381-HISTORY-RECORD "
    # Ring eviction: one backup of the oldest snapshot and one new snapshot.
    RING_EVICTION = (b"        memcpy(history->evicted, app_history_slot(history, history->undo, history->undo_head, 0), history->snapshot_size);\n"
                     b"        history->undo_head = (history->undo_head + 1) % history->capacity;\n")
    # Named withdrawal: move every remaining snapshot down one logical slot
    # (the pre-GEO-381 shift) while keeping the same head; same history.
    SHIFT_EVICTION = (b"        memcpy(history->evicted, app_history_slot(history, history->undo, history->undo_head, 0), history->snapshot_size);\n"
                      b"        for (size_t k = 1; k < history->capacity; ++k)\n"
                      b"            memmove(app_history_slot(history, history->undo, history->undo_head, k - 1),\n"
                      b"                app_history_slot(history, history->undo, history->undo_head, k), history->snapshot_size);\n")

    @classmethod
    def setUpClass(cls):
        text, _ = scene_generator.build(24, "single")
        cls.statements = [line for line in text.splitlines() if line.strip() and not line.lstrip().startswith("#")]
        commands = ["reset"] + ["line " + s for s in cls.statements] + ["dump", "references"]
        commands += ["line undo"] * 33 + ["dump"] + ["line redo"] * 33 + ["dump", "references"]
        cls.payload = "".join(c + "\n" for c in commands).encode("utf-8")

    def counted_bridge(self, label, withdraw=False):
        build = native()
        destination = build.work / ("geo381-history-closure-" + label)
        destination.mkdir()
        entry = copy_product_closure(ROOT / "geometry-web/web_bridge.c", destination)
        history = destination / "geometry-app/native/history.c"
        source = history.read_bytes()
        include = b"#include <string.h>\n"
        record = b"void app_history_record(AppHistory *history, const void *document)\n{\n"
        end = b"    history->redo_count = 0;\n}\n"
        self.assertEqual(1, source.count(include))
        self.assertEqual(1, source.count(record))
        body = source.split(record, 1)[1].split(end, 1)[0]
        source = source.replace(include, include + b"#include <stdio.h>\nstatic size_t geo381_history_bytes;\n"
            b"#define memcpy(d, s, n) (geo381_history_bytes += (n), memcpy(d, s, n))\n"
            b"#define memmove(d, s, n) (geo381_history_bytes += (n), memmove(d, s, n))\n")
        source = source.replace(record + body + end, record + b"    geo381_history_bytes = 0;\n" + body +
            b"    history->redo_count = 0;\n    fprintf(stderr, \"GEO381-HISTORY-RECORD %zu %zu %d\\n\", geo381_history_bytes,"
            b" history->snapshot_size, (int)history->record_evicted);\n}\n")
        if withdraw:
            self.assertEqual(1, source.count(self.RING_EVICTION), "Named withdrawal must change one actual site")
            source = source.replace(self.RING_EVICTION, self.SHIFT_EVICTION)
        history.write_bytes(source)
        defines = [d for d in PRODUCT_DEFINES if not d.startswith("GEOMETRY_HOST_HISTORY_EXTERNAL")]
        obj = build.compile(entry, "geo381-history-" + label, defines)
        objects = build.product_objects()
        self.assertEqual(1, objects.count(build.host_history_object))
        return build.link("geo381-history-" + label, [obj, *(o for o in objects if o != build.host_history_object)])

    def history_work(self, bridge):
        result = _bridge.run_once(self.payload, text=False, bridge=bridge, timeout=600)
        self.assertEqual(0, result.returncode, result.stderr)
        rows = [line.split()[1:] for line in result.stderr.splitlines() if line.startswith(self.MARKER)]
        records = [(int(b), int(size), int(evicted)) for b, size, evicted in rows]
        other = b"".join(line + b"\n" for line in result.stderr.splitlines() if not line.startswith(self.MARKER))
        return result.stdout, other, records

    def test_real_history_eviction_copies_two_snapshots_and_withdrawal_is_red(self):
        plain = _bridge.run_once(self.payload, text=False, bridge=native().bridge(), timeout=600)
        self.assertEqual(0, plain.returncode, plain.stderr)
        self.assertNotIn(self.MARKER, plain.stderr, "product bridge must not carry the test marker")
        replies = [json.loads(line) for line in plain.stdout.splitlines()]
        self.assertEqual(len(self.statements) + 3 + 33 + 1 + 33 + 2, len(replies))
        self.assertTrue(all(row["ok"] for row in replies[:len(self.statements) + 3]))
        stdout, stderr, records = self.history_work(self.counted_bridge("fixed"))
        self.assertEqual((plain.stdout, plain.stderr), (stdout, stderr), "marker must not change replies or stderr")
        evicted = [row for row in records if row[2]]
        worst = max(b // size for b, size, _ in records)
        print("geo381-history phase=fixed records=%d evicted=%d max_snapshots_per_record=%d" % (len(records), len(evicted), worst))
        self.assertGreater(len(records), 32, "the real history must overflow the 32-entry stack")
        self.assertTrue(evicted, "the real history must evict the oldest entry")
        for copied, size, _ in records:
            self.assertLessEqual(copied, 2 * size, "ASSERT:geo381-history-record-copies-at-most-two-snapshots")
        stdout, stderr, red = self.history_work(self.counted_bridge("withdrawn", withdraw=True))
        print("geo381-history phase=withdrawn max_snapshots_per_record=%d" % max(b // size for b, size, _ in red))
        self.assertEqual((plain.stdout, plain.stderr), (stdout, stderr), "both evictions publish the same history")
        self.assertGreater(max(b // size for b, size, _ in red), 2, "withdrawal must restore the full-stack shift")
        _, _, restored = self.history_work(self.counted_bridge("restored"))
        self.assertEqual(records, restored)

if __name__ == "__main__":
    unittest.main(verbosity=2)
