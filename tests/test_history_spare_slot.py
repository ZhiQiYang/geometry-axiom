"""H382: unchanged public history bytes, cheaper full record and rollback.

On the base, characterization passes and the two named copy-budget assertions
fail. No timing threshold, source hash, physical slot number or new API is used.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "geometry-app/native"
CLIENT = ROOT / "tests/history_spare_slot_harness.c"


class Build:
    def __init__(self, directory):
        self.directory = Path(directory)
        self.windows = os.name == "nt"
        self.compiler = shutil.which(os.environ.get("CC", "cl" if self.windows else "cc"))
        if not self.compiler:
            raise RuntimeError("H382 requires a configured C compiler; this is not a test verdict")

    def command(self, command):
        result = subprocess.run(command, capture_output=True, text=True, timeout=60)
        if result.returncode:
            raise RuntimeError("H382 build failure is not a mutation kill: " + result.stdout + result.stderr)

    def compile(self, label, source=None, counted=True):
        path = self.directory / (label + ".c")
        path.write_bytes((MODULE / "history.c").read_bytes() if source is None else source)
        obj = self.directory / (label + (".obj" if self.windows else ".o"))
        exe = self.directory / (label + (".exe" if self.windows else ""))
        if self.windows:
            defines = ["/Dmemcpy=h382_counted_memcpy", "/Dmemmove=h382_counted_memmove"] if counted else []
            self.command([self.compiler, "/nologo", "/std:c11", "/O2", "/c", "/I" + str(MODULE), *defines,
                          str(path), "/Fo" + str(obj)])
            self.command([self.compiler, "/nologo", "/std:c11", "/O2", "/I" + str(MODULE), str(CLIENT),
                          str(obj), "/Fo" + str(self.directory / "client.obj"), "/Fe" + str(exe)])
        else:
            defines = ["-Dmemcpy=h382_counted_memcpy", "-Dmemmove=h382_counted_memmove"] if counted else []
            self.command([self.compiler, "-std=c11", "-O2", "-I", str(MODULE), *defines,
                          "-c", str(path), "-o", str(obj)])
            self.command([self.compiler, "-std=c11", "-O2", "-I", str(MODULE), str(CLIENT), str(obj), "-o", str(exe)])
        return exe


def run_case(exe, case):
    result = subprocess.run([str(exe), case], capture_output=True, text=True, timeout=10)
    if result.returncode not in (0, 1) or (result.returncode == 1 and "ASSERT:H382_" not in result.stderr):
        raise RuntimeError("H382 crash/setup failure is not a verdict: " + repr(result))
    return result


class HistorySpareSlot(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory(prefix="geometry-h382-")
        cls.addClassCleanup(cls.temp.cleanup)
        cls.exe = Build(cls.temp.name).compile("history")

    def assert_case(self, case):
        result = run_case(self.exe, case)
        print(result.stdout, end="")
        self.assertEqual(0, result.returncode, result.stderr)

    def test_characterization_matches_independent_shifting_lists(self):
        self.assert_case("semantic")

    def test_full_record_copies_exactly_one_snapshot(self):
        self.assert_case("record-cost")

    def test_full_failed_record_rollback_copies_no_snapshot(self):
        self.assert_case("rollback-cost")


def withdrawals():
    """Run only after P; every kill must be a normal, named assertion."""
    source = (MODULE / "history.c").read_bytes()
    controls = (
        ("H382_SPARE_ADDRESS", b"return history->evicted;", b"return history->undo;", "semantic", "H382_LOGICAL_BYTES"),
        ("H382_RECORD_HEAD", b"history->undo_head = (history->undo_head + 1) % (history->capacity + 1);",
         b"/* oldest incorrectly retained */", "semantic", "H382_LOGICAL_BYTES"),
        ("H382_ROLLBACK_HEAD", b"history->undo_head = (history->undo_head + history->capacity) % (history->capacity + 1);",
         b"/* missing rewind */", "semantic", "H382_LOGICAL_BYTES"),
        ("H382_RECORD_REDO", b"history->redo_count = 0;\n}", b"/* stale redo */\n}", "semantic", "H382_HISTORY_COUNTS"),
        ("H382_ROLLBACK_REDO", b"history->redo_count = history->record_redo_count;",
         b"history->redo_count = 0;", "semantic", "H382_HISTORY_COUNTS"),
        ("H382_ABORT_BYTES", b"memcpy(document, history->group_base, history->snapshot_size);",
         b"/* missing full abort */", "semantic", "H382_DOCUMENT_BYTES"),
        ("H382_RECORD_COPY_REGRESSION", b"history->undo_head = (history->undo_head + 1) % (history->capacity + 1);",
         b"for (size_t k = history->capacity; k > 0; --k)\n"
         b"            memmove(app_history_slot(history, history->undo, history->undo_head, k),\n"
         b"                app_history_slot(history, history->undo, history->undo_head, k - 1), history->snapshot_size);\n"
         b"        history->undo_head = (history->undo_head + 2) % (history->capacity + 1);",
         "record-cost", "H382_FULL_RECORD_COPIES_ONE"),
        ("H382_ROLLBACK_COPY_REGRESSION", b"    history->record_evicted = false;",
         b"    history->record_evicted = false;\n"
         b"    if (history->undo_count)\n"
         b"        memcpy(app_history_slot(history, history->undo, history->undo_head, history->undo_count),\n"
         b"            app_history_slot(history, history->undo, history->undo_head, 0), history->snapshot_size);",
         "rollback-cost", "H382_FULL_UNRECORD_COPIES_ZERO"),
    )
    results = []
    with tempfile.TemporaryDirectory(prefix="geometry-h382-withdrawals-") as directory:
        build = Build(directory)
        for marker, before, after, case, assertion in controls:
            # The head advance also appears in redo's unreachable defensive
            # bound. This control intentionally withdraws only record's site.
            occurrences = source.count(before)
            if occurrences != (2 if marker in ("H382_RECORD_HEAD", "H382_RECORD_COPY_REGRESSION") else 1):
                raise AssertionError("H382 withdrawal target changed: " + marker + " count=" + str(occurrences))
            triplet = []
            for phase, body in (("baseline", source), ("withdrawn", source.replace(before, after, 1)), ("restored", source)):
                exe = build.compile(marker + "-" + phase, body)
                if "COPY_REGRESSION" in marker:
                    semantic = run_case(exe, "semantic")
                    if semantic.returncode != 0:
                        raise AssertionError("Copy-cost withdrawal changed public behavior: " + semantic.stderr)
                result = run_case(exe, case)
                triplet.append({"phase": phase, "exit": result.returncode, "stdout": result.stdout, "stderr": result.stderr})
            if [row["exit"] for row in triplet] != [0, 1, 0] or "ASSERT:" + assertion not in triplet[1]["stderr"]:
                raise AssertionError(json.dumps({"marker": marker, "triplet": triplet}))
            results.append({"marker": marker, "assertion": assertion, "results": triplet})
    print(json.dumps({"schema": "h382-named-withdrawals/1", "results": results}, indent=2))


if __name__ == "__main__":
    if sys.argv[1:] == ["--withdrawals"]:
        withdrawals()
    else:
        unittest.main(verbosity=2)
