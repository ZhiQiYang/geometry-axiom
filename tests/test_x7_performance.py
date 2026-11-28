"""X7 real-scene work budgets and byte/graph/error compatibility.

The only counter is at the actual full validator entry in a copied include
closure. The copied bridge also has a serial-path switch, deterministic test
nonces and two parser faults; production parsers/validators are still executed.
No timing from this instrumented binary is used as a performance sample.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tests/diagnostics"))
from tests import _bridge
from tests.test_geo261_wood_world_validation import copy_product_closure
import x7_scenarios as scenes
import x7_benchmark as benchmark
import x7_budget as budget_gate
from x7_budget_selftest import BudgetCheckerSelftest


def replace_once(path, before, after):
    data = path.read_bytes()
    scenes.require(data.count(before) == 1, "X7_OBSERVER_EXACT_SOURCE_SITE", str(path))
    path.write_bytes(data.replace(before, after))


def prepare_probe(out, mutate=None):
    """The serial switch invokes the preserved original per-line mark path.

    On T-only there is no batching helper and the product is already serial.
    Both versions compile and run: the named work assertion, not a missing
    symbol or an import/build failure, distinguishes the old implementation.
    """
    source = copy_product_closure(ROOT / "geometry-web/web_bridge.c", out)
    adapter = out / "geometry-web/framing_template_bridge.inc"
    has_batch = b"static bool framing_template_marks(World *w,FramingTemplateCall *c)" in adapter.read_bytes()
    globals_ = ("static unsigned long long g_x7_full;\n"
                "static unsigned g_x7_serial,g_x7_fault,g_x7_fail_snapshot,g_x7_snapshot_failures;\n"
                "static int g_x7_in_marks;\n"
                f"static const int g_x7_has_batch={int(has_batch)};\n")
    source.write_bytes(globals_.encode() + source.read_bytes())
    replace_once(out / "current_geometry.c",
                 b"    (void)world;\r\n    g_revalidate_error[0] = '\\0';",
                 b"    (void)world;\r\n    ++g_x7_full;\r\n    g_revalidate_error[0] = '\\0';")
    replace_once(out / "current_geometry.c",
                 b"static World *world_snapshot_take(WorldSnapshot *slot, const World *source)\r\n{",
                 b"static World *world_snapshot_take(WorldSnapshot *slot, const World *source)\r\n{\r\n"
                 b"    if(g_x7_in_marks&&g_x7_fail_snapshot){g_x7_fail_snapshot=0;++g_x7_snapshot_failures;return NULL;}")
    # Test nonce determinism permits a complete raw response byte comparison;
    # production entropy and its policy are not changed by this patch.
    replace_once(out / "geometry-web/timber_edit_bridge.inc",
                 b"static bool timber_edit_random_key(char out[65])\n{",
                 b"static bool timber_edit_random_key(char out[65])\n{\n"
                 b"    static unsigned nonce;snprintf(out,65,\"%064x\",++nonce);return true;")
    replace_once(adapter, b"static bool framing_template_line(World *w,char *text)\n{",
                 b"static bool framing_template_line(World *w,char *text)\n{\n"
                 b"    char fault[4096];\n"
                 b"    if(g_x7_fault&&!strncmp(text,\"guide \",6)){snprintf(fault,sizeof fault,\"%s+spec:x7_missing\",text);text=fault;}\n"
                 b"    if(g_x7_fault==2&&!strncmp(text,\"spec r03_mark_2_\",16)){snprintf(fault,sizeof fault,\"spec x7_bad not-an-integer\");text=fault;}")
    if has_batch:
        replace_once(adapter,
                     b"static bool framing_template_marks(World *w,FramingTemplateCall *c)\n{",
                     b"static bool framing_template_marks(World *w,FramingTemplateCall *c)\n{\n"
                     b"    if(g_x7_serial)return framing_template_marks_stage(w,c,g_reference_validation_deferred);")
        replace_once(adapter, b"    if(!(ok=framing_template_marks(w,c)))goto done;",
                     b"    g_x7_in_marks=1;ok=framing_template_marks(w,c);g_x7_in_marks=0;if(!ok)goto done;")
    shutil.copyfile(ROOT / "tests/diagnostics/x7_probe.inc", out / "geometry-web/x7_probe.inc")
    replace_once(source, b'#include "panel_fill_builder_bridge.inc"',
                 b'#include "panel_fill_builder_bridge.inc"\n#include "x7_probe.inc"')
    replace_once(source, b'        } else if (strcmp(line, "dump") == 0) {',
                 b'        } else if (strcmp(line, "x7-probe") == 0) {\n            x7_probe(arg);\n'
                 b'        } else if (strcmp(line, "x7-graph") == 0) {\n            x7_graph();\n'
                 b'        } else if (strcmp(line, "dump") == 0) {')
    # Withdrawal controls alter only this isolated, instrumented source copy.
    # Ordinary tests always compile the unmodified product closure above.
    if mutate is not None:
        mutate(out)
    return source


def build_probe(out, mutate=None):
    source = prepare_probe(out, mutate)
    exe = out / "x7-probe-bridge"
    command = [os.environ.get("CC", "cc"), "-std=c11", "-O2", str(source), "-lm", "-o", str(exe)]
    result = subprocess.run(command, capture_output=True, timeout=180)
    (out / "compile.stdout").write_bytes(result.stdout)
    (out / "compile.stderr").write_bytes(result.stderr)
    scenes.write_json(out / "compile.json", {"argv": command, "exit_code": result.returncode})
    scenes.require(result.returncode == 0, "X7_PROBE_COMPILES", result.stderr.decode(errors="replace"))
    return exe


def first_difference(left, right, path="value"):
    """Small diagnostics after an exact comparison; raw artifacts stay whole."""
    if isinstance(left, (bytes, str)) and type(left) is type(right):
        a = left.encode() if isinstance(left, str) else left
        b = right.encode() if isinstance(right, str) else right
        offset = next((i for i, (x, y) in enumerate(zip(a, b)) if x != y), min(len(a), len(b)))
        return (f"{path}: first_byte={offset}; bytes={len(a)}/{len(b)}; "
                f"sha256={hashlib.sha256(a).hexdigest()}/{hashlib.sha256(b).hexdigest()}")
    if isinstance(left, (list, tuple)) and type(left) is type(right):
        if len(left) != len(right):
            return f"{path}: length={len(left)}/{len(right)}"
        for index, (a, b) in enumerate(zip(left, right)):
            if a != b:
                return first_difference(a, b, f"{path}[{index}]")
    if isinstance(left, dict) and isinstance(right, dict):
        if left.keys() != right.keys():
            return f"{path}: different mapping keys"
        for key in left:
            if left[key] != right[key]:
                return first_difference(left[key], right[key], f"{path}[{key!r}]")
    return f"{path}: {left!r}/{right!r}"


class ProbeDialogue(scenes.Dialogue):
    """Negative parser cases compare exact nonempty stderr separately."""
    def __init__(self, *args, faults=False, **kwargs):
        self.faults = faults
        super().__init__(*args, **kwargs)

    def close(self):
        try:
            super().close()
        except AssertionError as error:
            if not (self.faults and str(error).startswith("X7_STDERR_EMPTY")
                    and self.process.returncode == 0 and self.closed):
                raise

    def observable_bytes(self):
        replies = self.stdout_path.read_bytes().splitlines(keepends=True)
        scenes.require(len(replies) == len(self.rows), "X7_ONE_RAW_REPLY_PER_REQUEST")
        return [(row["command"].split()[0], reply) for row, reply in zip(self.rows, replies)
                if not row["command"].startswith("x7-probe")]


class X7NativePerformance(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        requested = os.environ.get("GEOMETRY_X7_ARTIFACTS")
        if requested:
            cls.out = Path(requested).resolve()
            scenes.require(not cls.out.exists(), "X7_TEST_NEW_ARTIFACT_DIRECTORY")
            cls.out.mkdir(parents=True)
        else:
            cls.temp = tempfile.TemporaryDirectory(prefix="x7-native-")
            cls.addClassCleanup(cls.temp.cleanup)
            cls.out = Path(cls.temp.name)
        fixture = os.environ.get("GEOMETRY_X7_FIXTURES")
        if fixture:
            cls.bundle_path = Path(fixture).resolve()
        else:
            cls.bridge = _bridge.find_bridge()
            scenes.build_all(cls.out / "fixtures", cls.bridge)
            cls.bundle_path = cls.out / "fixtures/browser-bundle.json"
        cls.bundle, cls.fixture_root = benchmark.validate_bundle(cls.bundle_path)
        cls.cases = {case["key"]: case for case in cls.bundle["cases"]}
        cls.probe = build_probe(cls.out / "probe")

    def assert_exact(self, left, right, marker):
        # Compare the complete objects/bytes. Only the failure rendering is
        # bounded; the observation and its equality predicate are unchanged.
        if left != right:
            self.assert_contract(False, marker, first_difference(left, right))

    def assert_contract(self, condition, marker, detail=None):
        if not condition:
            error = self.failureException(marker + (": " + str(detail) if detail is not None else ""))
            # Only the actual named semantic assertions carry this attribute.
            # Protocol/child/timeout failures cannot acquire it from a path or
            # product message containing the marker's text.
            error.x7_assertion = marker
            raise error

    def exercise(self, key, serial, allocation=0):
        case = self.cases[key]
        before = scenes.read_file(case["beforeScene"], self.fixture_root)
        after = scenes.read_file(case["completedScene"], self.fixture_root)
        expected = json.loads(scenes.read_file(case["expectedGeometry"], self.fixture_root))
        name = f"{key}-serial{serial}-alloc{allocation}"
        with ProbeDialogue(self.out / "raw", name, str(self.probe)) as d:
            d.command("reset")
            d.command("loadfile " + str(self.fixture_root / case["beforeScene"]["path"]))
            baseline = d.command("dump")
            self.assert_exact(before, baseline["text"].encode(), "X7_BEFORE_BYTES")
            flags = d.command(f"x7-probe {serial} 0 {allocation}")
            preview = scenes.framing_preview(d, case["currentBoundary"], expect_ok=False)
            self.assert_contract(preview.get("ok") is True, "X7_COMPLETE_NATIVE_PREVIEW_ACCEPTED",
                                 {"code": preview.get("code"), "error": preview.get("error")})
            work = d.command("x7-probe")
            graph = d.command("x7-graph")
            self.assertTrue(graph["sealed"] and graph["nodes"] and graph["edges"], "X7_REAL_SEALED_SOURCE_GRAPH")
            self.assertNotRegex(graph["graph"], "MISSING_|UNHANDLED_", "X7_ALL_TYPED_GRAPH_VALUES")
            self.assert_exact(baseline, d.command("dump"), "X7_PREVIEW_ZERO_WRITE")
            self.assert_contract(flags["deferred"] == work["deferred"], "X7_DEFER_SCOPE_RESTORED",
                                 {"before": flags["deferred"], "after": work["deferred"]})
            self.assertEqual(flags["muted"], work["muted"], "X7_MUTE_SCOPE_RESTORED")
            d.command(f"x7-probe {serial} 0 0")
            scenes.framing_confirm(d, preview)
            confirmation = d.command("x7-probe")
            self.assert_contract(confirmation["full"] == 1, "X7_CONFIRM_FULL_VALIDATION_RETAINED",
                                 {"expected": 1, "actual": confirmation["full"]})
            self.assert_exact(after, d.command("dump")["text"].encode(), "X7_CONFIRMED_EXACT_BYTES")
            scenes.validate_references(d.command("references"), expected)
            d.command("objects")
            d.command("line undo")
            self.assert_exact(before, d.command("dump")["text"].encode(), "X7_ONE_HISTORY_UNDO_BYTES")
            d.command("line redo")
            self.assert_exact(after, d.command("dump")["text"].encode(), "X7_ONE_HISTORY_REDO_BYTES")
            d.command("loadfile " + str(self.fixture_root / case["completedScene"]["path"]))
            self.assert_exact(after, d.command("dump")["text"].encode(), "X7_COLD_LOAD_EXACT_BYTES")
        return d.observable_bytes(), work

    def compare_success(self, key):
        serial, old = self.exercise(key, 1)
        actual, work = self.exercise(key, 0)
        self.assert_exact(serial, actual, "X7_SERIAL_AND_BATCH_ALL_RESPONSE_AND_GRAPH_BYTES")
        print("X7_WORK", key, "serial=" + str(old["full"]), "actual=" + str(work["full"]),
              "bytes=PASS graph=PASS confirm=1", flush=True)
        self.assert_contract(work["full"] == 4, "X7_PREVIEW_FULL_VALIDATIONS_BOUNDED",
                             {"case": key, "expected": 4, "actual": work["full"]})

    def test_01_room53_work_and_exact_bytes(self):
        self.compare_success("room53")

    def test_02_house500_work_and_exact_bytes(self):
        self.compare_success("house500")

    def fault_case(self, serial, fault):
        case = self.cases["room53"]
        name = f"fault{fault}-serial{serial}"
        with ProbeDialogue(self.out / "raw", name, str(self.probe), faults=True) as d:
            d.command("reset")
            d.command("loadfile " + str(self.fixture_root / case["beforeScene"]["path"]))
            before = d.command("dump")
            flags = d.command(f"x7-probe {serial} {fault} 0")
            refusal = scenes.framing_preview(d, case["currentBoundary"], expect_ok=False)
            self.assertFalse(refusal["ok"], "X7_PARSER_FAULT_REJECTED")
            self.assertEqual("NATIVE_INVALID", refusal["code"], "X7_MARK_FAILURE_NATIVE_DIAGNOSTIC")
            self.assert_exact(before, d.command("dump"), "X7_FAILED_PREVIEW_ZERO_WRITE")
            state = d.command("x7-probe")
            self.assertEqual(flags["deferred"], state["deferred"], "X7_FAILED_DEFER_SCOPE_RESTORED")
            self.assertEqual(flags["muted"], state["muted"], "X7_FAILED_MUTE_SCOPE_RESTORED")
            # A subsequent independent bad reference still takes the normal
            # full validator. A leaked deferred flag cannot accept it.
            bad = d.command("line guide 15 1 u spec:x7_still_missing", expect_ok=False)
            self.assertFalse(bad.get("ok"), "X7_SUBSEQUENT_BAD_REFERENCE_REJECTED")
            self.assert_exact(before, d.command("dump"), "X7_SUBSEQUENT_FAILURE_ZERO_WRITE")
        return d.observable_bytes(), d.stderr_path.read_bytes(), state["issues"]

    def test_03_first_error_and_scope_on_both_failure_phases(self):
        for fault in (1, 2):
            with self.subTest(fault=fault):
                serial = self.fault_case(1, fault)
                fast = self.fault_case(0, fault)
                self.assert_exact(serial, fast, "X7_FAILURE_ORIGINAL_BYTES_STDERR_AND_ISSUES")
                self.assertTrue(serial[1], "X7_REAL_PARSER_ERROR_NOT_SWALLOWED")

    def test_04_optional_checkpoint_allocation_failure_falls_back(self):
        ordinary, old = self.exercise("room53", 1, 1)
        fallback, work = self.exercise("room53", 0, 1)
        self.assert_exact(ordinary, fallback, "X7_OPTIONAL_SNAPSHOT_FAILURE_EXACT_BYTES")
        self.assertEqual(old["full"], work["full"], "X7_SNAPSHOT_FAILURE_ORIGINAL_VALIDATIONS")
        self.assertEqual(int(work["hasBatch"]), work["snapshotFailures"], "X7_SNAPSHOT_FAILURE_ACTUALLY_INJECTED")

    def test_05_every_operation_sample_within_reviewed_budget(self):
        # Time only the ordinary official binary, never the observer build.
        out = self.out / "operation-budget"
        bridge = getattr(self, "bridge", None) or _bridge.find_bridge()
        command = [sys.executable, "-B", str(ROOT / "tests/diagnostics/x7_benchmark.py"),
                   "--fixtures", str(self.bundle_path), "--out", str(out),
                   "--repeats", "3", "--bridge", bridge]
        result = subprocess.run(command, capture_output=True, timeout=300)
        (self.out / "budget-run.stdout").write_bytes(result.stdout)
        (self.out / "budget-run.stderr").write_bytes(result.stderr)
        scenes.write_json(self.out / "budget-run.command.json", {"argv": command, "exit_code": result.returncode})
        self.assertEqual(0, result.returncode, "X7_BUDGET_REAL_COMMAND_SUCCESS: " + result.stderr.decode(errors="replace"))
        self.assertEqual(b"", result.stderr, "X7_BUDGET_REAL_COMMAND_STDERR")
        report = budget_gate.parse_json((out / "report.json").read_bytes())
        budget = budget_gate.parse_json((ROOT / "tests/diagnostics/x7_budgets.json").read_bytes())
        try:
            verdict = budget_gate.check_report(report, budget, out)
        except budget_gate.BudgetFailure as error:
            self.fail(error.marker + ": " + repr(error.detail))
        scenes.write_json(self.out / "budget-verdict.json", verdict)
        self.assertEqual(33, len(verdict["checks"]), "X7_ALL_33_OPERATION_BUDGETS")
        self.assertTrue(all(check["samples"] == 3 for check in verdict["checks"]), "X7_ALL_99_OPERATION_SAMPLES")


if __name__ == "__main__":
    unittest.main(verbosity=2)
