"""R14 P1: read the existing candidate, without creating or committing one.

Geometry expectations are independently constructed and checked from the input;
the live/candidate equality checks additionally protect the existing transport.
Run with the repository freshness-checked bridge. No browser claim is made.
"""
import copy
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from tests import _bridge
from tests.diagnostics import r14_panel_next_oracle as oracle


def case(panel=915, gap=2, anchor=0, divisions=(7, 2), cell=(-1, 0)):
    return {"u": {"kind": "panel", "panel": panel, "gap": gap, "anchor": anchor},
            "v": {"kind": "repeat", "phase": 0, "step": 400},
            "divisions": list(divisions), "cell": [str(x) for x in cell]}


class SealProbeSession:
    """Line protocol for the separately described, freshness-checked C probe.

    The ordinary bridge keeps _bridge's canonical fingerprint guard. The probe
    is checked against its own Binary descriptor immediately before spawning,
    since its source and instrumentation are deliberately different.
    """
    def __init__(self, binary):
        from tests import binaries
        info = binaries.inspect_one(binary)
        if info.state != "fresh":
            raise RuntimeError("R14CQ_SEAL_PROBE_NOT_FRESH: " + info.reason)
        self.stderr = tempfile.TemporaryFile(mode="w+b")
        try:
            self.process = subprocess.Popen([str(binary.path)], stdin=subprocess.PIPE,
                                            stdout=subprocess.PIPE, stderr=self.stderr,
                                            text=True, encoding="utf-8")
        except BaseException:
            self.stderr.close()
            raise
        self.stopped = False

    def command(self, text):
        self.process.stdin.write(text + "\n")
        self.process.stdin.flush()
        line = self.process.stdout.readline()
        if not line:
            self.stderr.seek(0)
            raise _bridge.BridgeClosed(self.stderr.read().decode("utf-8", errors="replace"),
                                       self.process.poll())
        return json.loads(line)

    def stop(self):
        if self.stopped:
            return
        self.stopped = True
        self.process.stdin.close()
        try:
            status = self.process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            self.process.kill()
            self.process.wait()
            raise RuntimeError("R14CQ_SEAL_PROBE_STOP_TIMEOUT")
        finally:
            self.process.stdout.close()
            self.stderr.close()
        if status != 0:
            raise _bridge.BridgeClosed("R14CQ_SEAL_PROBE_EXIT", status)


class WithdrawalDeadlines(unittest.TestCase):
    def test_partial_probe_reply_times_out_before_newline(self):
        from unittest.mock import patch
        from tests import binaries
        # A real pipe: readable bytes are not a complete protocol reply. The
        # fixture eventually supplies the newline so even a broken test ends.
        with tempfile.TemporaryDirectory() as tmp, patch.object(binaries, "OUT_DIR", Path(tmp)):
            src = Path(tmp) / "late.c"
            src.write_text('''#include <stdio.h>
#include <string.h>
#ifdef _WIN32
#include <windows.h>
#define DELAY() Sleep(4000)
#else
#include <unistd.h>
#define DELAY() sleep(4)
#endif
int main(void) {
    char buf[32];
    if (fgets(buf,sizeof buf,stdin) && !strcmp(buf,"partial\\n")) {
        fputs("{",stdout); fflush(stdout);
        fputs("partial sent\\n",stderr); fflush(stderr);
        DELAY(); puts("}");
    }
    return 0;
}
''', encoding="utf-8")
            binary = binaries.Binary("late", "late", str(src), ["/nologo"], [], [], [], smoke="bridge")
            built = binaries.build_one(binary)
            self.assertTrue(built.ok, ("R14CQ_TIMEOUT_FIXTURE_BUILD", built.detail))
            probe = SealProbeSession(binary)
            probe.reply_timeout = 1
            try:
                with self.assertRaisesRegex(TimeoutError, "R14CQ_SEAL_PROBE_REPLY_TIMEOUT.*partial",
                                            msg="R14CQ_PARTIAL_REPLY_MUST_TIME_OUT") as caught:
                    probe.command("partial")
                self.assertIn("partial sent", str(caught.exception), "R14CQ_TIMEOUT_KEEPS_PROBE_STDERR")
                self.assertIsNotNone(probe.process.poll(), "R14CQ_TIMEOUT_REAPS_PROBE")
            finally:
                probe.stop()

    def test_late_mutant_assertion_is_blocked_with_logs(self):
        self.check_blocked_mutant('time.sleep(4); self.fail("FIXTURE_ASSERT")', "R14CQ_JUDGE_TIMEOUT")

    def test_probe_timeout_from_mutant_judge_is_blocked(self):
        self.check_blocked_mutant('raise TimeoutError("R14CQ_SEAL_PROBE_REPLY_TIMEOUT: partial")',
                                  "R14CQ_SEAL_PROBE_REPLY_TIMEOUT")

    def check_blocked_mutant(self, mutant_action, reason):
        import threading
        from unittest.mock import patch
        from tests.diagnostics import r14_candidate_query_mutations as runner
        # Exercise the actual three judge processes, classification, restoration
        # and receipts. Only the C builds are irrelevant to this timing fixture.
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp)
            source = output / "original"
            script = source / runner.RUNNER
            script.parent.mkdir(parents=True)
            script.write_bytes((ROOT / runner.RUNNER).read_bytes())
            fixture = source / "fixture.py"
            fixture.write_text('import sys, time, unittest\n'
                               'class Judge(unittest.TestCase):\n'
                               '    def test_one(self):\n'
                               '        if False:\n'
                               '            print("entered mutant", flush=True)\n'
                               f'            {mutant_action}\n', encoding="utf-8")
            case = dict(name="SLOW", source="fixture.py", before="if False:", after="if True:",
                        test="fixture.Judge.test_one", tag="FIXTURE_ASSERT")
            build = dict(exit_code=0, report=dict(exit_code=0, fresh=True, binary_sha256="fixture",
                                                  info=dict(path=sys.executable)))
            with patch.object(runner, "JUDGE_TIMEOUT", 2, create=True), patch.object(runner, "build", return_value=build):
                runner.run_case(case, source, {"fixture.py": runner.sha(fixture.read_bytes())},
                                build, output, output, threading.Lock())
            directory = output / "SLOW"
            receipt = runner.read_json(directory / "report.json")
            self.assertEqual("blocked", receipt["status"], "R14CQ_TIMEOUT_MUST_BE_BLOCKED: " + reason)
            self.assertFalse(receipt["passed"], "R14CQ_TIMEOUT_IS_NOT_A_KILL")
            self.assertIn(reason, receipt["reason"], "R14CQ_NAMED_TIMEOUT_RECEIPT")
            self.assertIn("mutant-test", receipt["reason"], "R14CQ_TIMEOUT_IDENTIFIES_PHASE")
            self.assertIn(reason, (directory / "mutant-test.stderr.log").read_text(encoding="utf-8"))
            self.assertIn("entered mutant", (directory / "mutant-test.stdout.log").read_text(encoding="utf-8"))
            self.assertTrue((directory / "mutant-test.process.json").is_file(), "R14CQ_TIMEOUT_PROCESS_RECEIPT")
            self.assertTrue(receipt["all_copied_bytes_restored"], "R14CQ_TIMEOUT_RESTORES_SOURCE")
            self.assertEqual([0, 0], [receipt[key]["exit_code"] for key in ("baseline", "restored")])


class R14CandidateQuery(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if os.name != "nt":
            import resource
            soft, hard = resource.getrlimit(resource.RLIMIT_STACK)
            if soft != resource.RLIM_INFINITY and soft < 16 * 1024 * 1024:
                resource.setrlimit(resource.RLIMIT_STACK, (16 * 1024 * 1024, hard))
        cls.executable = _bridge.find_bridge()

    def setUp(self):
        self.session = _bridge.BridgeSession(self.executable)
        self.addCleanup(self.session.stop)
        directory = tempfile.TemporaryDirectory(prefix="r14-candidate-query-")
        self.addCleanup(directory.cleanup)
        self.directory = Path(directory.name)
        self.commit("reset")

    def ask(self, command):
        return self.session.command(command)

    def commit(self, command):
        result = self.ask("line " + command)
        if "preview" in result:
            self.assertTrue(result["preview"]["valid"], ("R14CQ_SETUP_VALID", command, result))
            result = self.ask("line confirm " + str(result["preview"]["token"]))
        self.assertTrue(result["ok"], ("R14CQ_SETUP_COMMIT", command, result))
        return result

    @staticmethod
    def source(panel=915, gap=2, anchor=0, u=None, v="repeat 0 400", prefix=""):
        u = u or f"repeat-panel {panel} gap {gap} from {anchor}"
        return f"grid-system 0 name-hex 523134 main-along none {prefix}u {u} v {v}"

    @staticmethod
    def rule(divisions=(7, 2), key=None, selector="all-cells", name="R14"):
        action = "create" if key is None else f"key {key}"
        return (f"grid-source-rule 0 {action} name-hex {name.encode().hex()} "
                f"selector {selector} divide {divisions[0]} {divisions[1]}")

    def seed(self, **kwargs):
        self.commit(self.source(**kwargs))
        self.commit(self.rule())

    def revision(self):
        value = self.ask("engineering-read")
        self.assertTrue(value["ok"], value)
        return value["revision"]

    def snapshot(self):
        return tuple(self.ask(command) for command in ("dump", "objects", "references", "engineering-read"))

    def preview(self, command, valid=True):
        before = self.snapshot()
        result = self.ask("line preview " + command)
        self.assertIn("preview", result, ("R14CQ_SETUP_PREVIEW", result))
        preview = result["preview"]
        self.assertEqual(valid, preview["valid"], ("R14CQ_SETUP_VALID", result))
        self.assertEqual(before, self.snapshot(), "R14CQ_PREVIEW_ZERO_WRITE")
        return preview

    def engineering(self, operations, valid=True, command="engineering-preview", schema="engineering-transaction/1"):
        before = self.snapshot()
        path = self.directory / "request.json"
        path.write_text(json.dumps({"schema": schema, "expectedRevision": self.revision(),
                                    "operations": operations}), encoding="utf-8")
        response = self.ask(command + " " + str(path))
        self.assertTrue(response["ok"], ("R14CQ_SETUP_ENGINEERING", response))
        self.assertEqual(valid, response["preview"]["valid"], response)
        self.assertEqual(before, self.snapshot(), "R14CQ_ENGINEERING_PREVIEW_ZERO_WRITE")
        return response["preview"]

    @staticmethod
    def parameter(panel="915"):
        return {"op": "put-parameter", "value": {"id": 10, "name": "Board", "fields": [
            {"id": 3, "name": "panel", "type": "dimension", "input": panel},
            {"id": 8, "name": "step", "type": "dimension", "input": "400"}]}}

    def query(self, preview, side="after", tail="system 0 rule 1 cell -1 0", kind="reference", code=None):
        before = self.snapshot()
        revision = self.revision()
        token = preview["token"] if isinstance(preview, dict) else preview
        response = self.ask(f"grid-rule-candidate-query {kind} {token} side {side} {tail}")
        self.assertEqual(before, self.snapshot(), "R14CQ_QUERY_ZERO_WRITE")
        if code:
            self.assertFalse(response.get("ok"), ("R14CQ_REJECT", code, response))
            self.assertEqual(code, response.get("code"), ("R14CQ_ERROR_CODE", response))
            self.assertNotIn("query", response, "R14CQ_NO_PARTIAL_GEOMETRY")
        else:
            self.assertTrue(response.get("ok"), ("R14CQ_CANDIDATE_AVAILABLE", response))
            self.assertEqual({"ok", "candidate", "source", "metrics", "query"}, set(response), "R14CQ_CLOSED_ENVELOPE")
            self.assertEqual({"kind": kind, "token": token, "side": side, "revision": str(revision)},
                             response["candidate"], "R14CQ_CANDIDATE_IDENTITY")
        return response

    def assert_geometry(self, query, inputs, label):
        expected = oracle.build(inputs)
        self.assertEqual("ok", expected["status"], (label, expected))
        self.assertEqual([], oracle.check(inputs, expected), "R14CQ_ORACLE_INDEPENDENT")
        actual = {"status": "ok", "code": expected["code"], "bounds": query["bounds"], "lines": []}
        for line in query["lines"]:
            self.assertEqual(1, len(line["segments"]), label + "_ONE_FULL_SEGMENT")
            segment = line["segments"][0]
            self.assertIn(line["axis"], ("u", "v"), label + "_AXIS")
            self.assertEqual(2, len(segment), label + "_SEGMENT_ENDPOINTS")
            self.assertTrue(all(len(point) == 2 and all(type(n) is int for n in point)
                                for point in segment), label + "_INTEGER_POINTS")
            along = 1 if line["axis"] == "u" else 0
            lo, hi = sorted(point[along] for point in segment)
            expected_segment = ([[line["coordinate"], lo], [line["coordinate"], hi]]
                                if line["axis"] == "u" else
                                [[lo, line["coordinate"]], [hi, line["coordinate"]]])
            self.assertEqual(expected_segment, segment, label + "_FULL_2D_SEGMENT")
            actual["lines"].append([line["axis"], line["innerIndex"], line["coordinate"], lo, hi])
        self.assertEqual(expected, actual, label)
        self.assertEqual([], oracle.check(inputs, actual), label + "_CHECKED")
        self.assertEqual(inputs["cell"], query["cell"], "R14CQ_CELL_STRINGS")

    def binding(self, boundary=1, binding=0, grid=10, cell=("-1", "0"), hole=False):
        outline = "100,200 2100,200 2100,1800 100,1800"
        if hole:
            outline += " hole 200,250 300,250 300,450 200,450"
        self.commit(f"boundary {boundary} outline {outline}")
        shape = self.ask(f"boundary {boundary}")
        self.assertTrue(shape["ok"], shape)
        self.commit(f"grid-binding {binding} on-boundary {boundary} from-system 0 vertex outer 0 "
                    f"geometry-hash {shape['geometryFingerprint']} cell {' '.join(cell)} anchor 0 1 0 1")
        self.commit(f"placement {boundary} on boundary {boundary} origin 0 0 0 u +x v +y")
        self.commit(f"grid {grid} on {boundary} from-binding {binding}")

    def test_01_create_rule_reads_after_before_missing_and_commits_same_candidate(self):
        self.commit(self.source())
        preview = self.preview(self.rule())
        before_world = self.snapshot()
        after = self.query(preview)
        self.assert_geometry(after["query"], case(), "R14CQ_NEW_RULE_COORDINATES")
        self.assertEqual({"u": {"pitch": 917, "divisions": 7, "innerStep": 131},
                          "v": {"pitch": 400, "divisions": 2, "innerStep": 200}}, after["metrics"], "R14CQ_METRICS")
        row = preview["gridSystems"][0]
        self.assertEqual(row["after"], after["source"], "R14CQ_SOURCE_FROM_SAME_SIDE")
        self.assertTrue(all(x["ref"] is None for x in after["query"]["lines"]), "R14CQ_SOURCE_REF_NULL")
        self.query(preview, side="before", code="QUERY_NOT_FOUND")
        self.assertEqual(before_world, self.snapshot(), "R14CQ_READS_KEEP_LIVE_RULE_ABSENT")
        self.commit("confirm " + str(preview["token"]))
        self.assertEqual(after["query"], self.ask("grid-rule-query system 0 rule 1 cell -1 0"), "R14CQ_CONFIRMED_EQUALS_CANDIDATE")
        next_preview = self.preview(self.rule(key=1, name="next"))
        self.assertEqual(preview["token"] + 1, next_preview["token"], "R14CQ_QUERY_NEVER_ALLOCATES_TOKEN")

    def test_02_source_edit_distinguishes_both_sides_from_live_and_preserves_history(self):
        self.seed()
        original = self.ask("dump")["text"]
        preview = self.preview(self.source(panel=922).replace("main-along none", "main-along u"))
        before = self.query(preview, side="before")
        after = self.query(preview)
        self.assertIsNone(before["source"]["mainAlong"], "R14CQ_SOURCE_BEFORE_MAIN_ALONG")
        self.assertEqual("u", after["source"]["mainAlong"], "R14CQ_SOURCE_AFTER_MAIN_ALONG")
        self.assert_geometry(before["query"], case(), "R14CQ_BEFORE_COORDINATES")
        self.assert_geometry(after["query"], case(panel=922), "R14CQ_AFTER_COORDINATES")
        self.assertNotEqual(before["query"], after["query"], "R14CQ_AFTER_IS_NOT_LIVE")
        for side, result in (("before", before), ("after", after)):
            self.assertEqual(preview["gridSystems"][0][side], result["source"], "R14CQ_SNAPSHOT_SOURCE")
        self.commit("confirm " + str(preview["token"]))
        committed = self.ask("dump")["text"]
        self.commit("undo")
        self.assertEqual(original, self.ask("dump")["text"], "R14CQ_NO_HIDDEN_HISTORY_STEP")
        self.commit("redo")
        self.assertEqual(committed, self.ask("dump")["text"], "R14CQ_REDO_SAME_WORLD")

    def test_03_delete_rule_does_not_fall_back_to_live_or_other_side(self):
        self.seed()
        live = self.ask("grid-rule-query system 0 rule 1 cell -1 0")
        preview = self.preview("grid-source-rule 0 delete 1")
        self.assertEqual(live, self.query(preview, side="before")["query"], "R14CQ_DELETED_BEFORE")
        self.query(preview, code="QUERY_NOT_FOUND")
        self.commit("confirm " + str(preview["token"]))
        self.assertFalse(self.ask("grid-rule-query system 0 rule 1 cell -1 0")["ok"], "R14CQ_DELETE_CONFIRM_STILL_WORKS")

    def test_04_engineering_card_and_parameter_values_are_resolved_in_selected_snapshot(self):
        for mode in ("card", "parameter"):
            with self.subTest(mode=mode):
                self.commit("reset")
                setup = self.engineering([self.parameter()])
                self.assertTrue(self.ask("engineering-confirm " + str(setup["token"]))["ok"])
                if mode == "card":
                    self.commit(self.source(u="repeat-panel card gap 2 from 0", v="repeat 0 card",
                                            prefix="card-reference 10 3 8 "))
                else:
                    self.commit(self.source(u="repeat-panel param:10:3 gap 2 from 0"))
                self.commit(self.rule())
                preview = self.engineering([self.parameter("922")])
                for side, panel in (("before", 915), ("after", 922)):
                    value = self.query(preview, kind="engineering", side=side)
                    self.assert_geometry(value["query"], case(panel=panel), "R14CQ_ENGINEERING_" + side.upper())
                    self.assertEqual(panel + 2, value["metrics"]["u"]["pitch"], "R14CQ_EFFECTIVE_METRICS")
                    source = value["source"]
                    if mode == "card":
                        self.assertEqual({"parameterId": 10, "uFieldId": 3, "vFieldId": 8}, source["cardReference"], "R14CQ_CARD_IDENTITY")
                        self.assertEqual(panel, source["uDefinition"]["effectivePanel"], "R14CQ_CARD_VALUE")
                        self.assertNotIn("panel", source["uDefinition"], "R14CQ_NO_CARD_FLATTENING")
                    else:
                        self.assertEqual({"kind": "parameter", "parameterId": 10, "fieldId": 3},
                                         source["uDefinition"]["parameterRefs"]["panel"], "R14CQ_PARAMETER_IDENTITY")
                self.query(preview, kind="reference", code="CANDIDATE_KIND")
                self.assertTrue(self.ask("engineering-confirm " + str(preview["token"]))["ok"], "R14CQ_ENGINEERING_CONFIRM_SURVIVES_READS")

    def test_05_binding_grid_clipping_uses_whole_parent_cell_and_keeps_tuple(self):
        self.seed()
        large = ("9007199254740993", "-9007199254740995")
        self.binding(cell=large, hole=True)
        preview = self.preview(self.source(panel=922))
        for side, step, upper in (("before", 131, 1017), ("after", 132, 1024)):
            values = {}
            for kind, identifier in (("binding", 0), ("grid", 10)):
                value = self.query(preview, side=side, tail=f"{kind} {identifier} rule 1 cell {' '.join(large)}")
                query = value["query"]
                values[kind] = query
                self.assertEqual(list(large), query["cell"], "R14CQ_LARGE_SIGNED_CELL")
                self.assertEqual([100, 200, upper, 600], query["bounds"], "R14CQ_BOUND_PARENT_NOT_VIEWPORT")
                u_lines = [x for x in query["lines"] if x["axis"] == "u"]
                self.assertEqual([100 + k * step for k in range(1, 7)], [x["coordinate"] for x in u_lines], "R14CQ_BOUND_CANDIDATE_COORDINATES")
                x = 100 + step
                self.assertEqual([[[x, 200], [x, 250]], [[x, 450], [x, 600]]], u_lines[0]["segments"], "R14CQ_HOLE_CLIP")
                for line in query["lines"]:
                    expected = None if kind == "binding" else {
                        "kind": "grid-rule-line", "appliedGridId": 10, "systemId": 0, "ruleKey": 1,
                        "cellI": large[0], "cellJ": large[1], "axis": line["axis"], "innerIndex": line["innerIndex"]}
                    self.assertEqual(expected, line["ref"], "R14CQ_PLACED_REF_TUPLE")
            a, b = copy.deepcopy(values["binding"]), copy.deepcopy(values["grid"])
            for line in b["lines"]:
                line["ref"] = None
            self.assertEqual(a, b, "R14CQ_BINDING_GRID_SAME_LOCAL_GEOMETRY")
        # A far-out cell retains every internal line with zero visible segments.
        hidden = self.query(preview, tail=f"grid 10 rule 1 cell {int(large[0])+10} {large[1]}")["query"]
        self.assertEqual(7, len(hidden["lines"]), "R14CQ_ZERO_VISIBLE_RETAINS_IDENTITIES")
        self.assertTrue(all(not x["segments"] for x in hidden["lines"]), "R14CQ_ZERO_VISIBLE_NO_FAKE_SEGMENTS")
        self.commit("confirm " + str(preview["token"]))

    def test_06_rectangle_capacity_sample_and_empty_selector_preserve_candidate(self):
        self.commit(self.source(u="repeat-panel 1 gap 1 from -1", v="repeat 0 2"))
        self.commit(self.rule(divisions=(2, 1)))
        preview = self.preview(self.rule(divisions=(2, 1), key=1, name="capacity"))
        failure = self.query(preview, tail="system 0 rule 1 rect 0 0 2050 2 mode exact limit 1024", code="QUERY_CAPACITY")
        self.assertEqual("1025", failure["requiredCells"], "R14CQ_CAPACITY_COUNT")
        sampled = self.query(preview, tail="system 0 rule 1 rect 0 0 200 200 mode sample limit 64")["query"]
        self.assertFalse(sampled["complete"], "R14CQ_SAMPLE_IS_NOT_EXACT")
        self.assertEqual("10000", sampled["requiredCells"], "R14CQ_SAMPLE_REQUIRED")
        stride = int(sampled["stride"])
        self.assertGreater(stride, 1)
        self.assertEqual([[str(k % 100), str(k // 100)] for k in range(0, 10000, stride)],
                         [x["cell"] for x in sampled["cells"]], "R14CQ_SAMPLE_REAL_INDICES")
        self.assertLessEqual(len(sampled["cells"]), 64)
        for cell in sampled["cells"]:
            self.assertEqual(1, len(cell["lines"]), "R14CQ_WHOLE_CELL_SAMPLING")
            self.assertEqual(2 * int(cell["cell"][0]) + 1, cell["lines"][0]["coordinate"], "R14CQ_SAMPLE_POSITION")
        self.commit("confirm " + str(preview["token"]))
        preview = self.preview(self.rule(divisions=(2, 1), key=1, selector="cell 0 0"))
        empty = self.query(preview, tail="system 0 rule 1 rect 2 2 4 4 mode exact limit 1")["query"]
        self.assertEqual({"ok": True, "complete": True, "requiredCells": "0", "stride": "1", "cells": []}, empty, "R14CQ_EMPTY_QUERY_HAS_SOURCE_METRICS")
        self.commit("confirm " + str(preview["token"]))

    def test_07_token_kind_mismatch_unknown_owner_and_invalid_queries_do_not_consume(self):
        self.seed()
        preview = self.preview(self.source(panel=922))
        self.query(preview, kind="engineering", code="CANDIDATE_KIND")
        for owner in ("assembly", "finish", "profile", "unknown"):
            self.query(preview, kind=owner, code="CANDIDATE_KIND")
        self.query(preview["token"] + 1, code="CANDIDATE_STALE")
        self.query(0, code="CANDIDATE_STALE")
        self.query(preview, tail="system 0 rule 1 cell 0 0 trailing", code="QUERY_INVALID")
        self.query(preview, tail="system 0 rule 1 rect 0 0 917 400 mode sample limit 0", code="QUERY_INVALID")
        self.query(preview, tail="system 0 rule 1 rect 0 0 917 400 mode exact limit 1025", code="QUERY_INVALID")
        self.query(preview, tail="system 0 rule 1 cell 9223372036854775808 0", code="QUERY_INVALID")
        self.query(preview, tail="system 99 rule 1 cell 0 0", code="QUERY_NOT_FOUND")
        self.query(preview, tail="system 0 rule 99 cell 0 0", code="QUERY_NOT_FOUND")
        self.assert_geometry(self.query(preview)["query"], case(panel=922), "R14CQ_VALID_AFTER_ERRORS")
        self.commit("confirm " + str(preview["token"]))

    def test_08_cancel_confirm_replace_invalid_and_geometry_revision_make_tokens_unreadable(self):
        self.seed()
        preview = self.preview(self.source(panel=922))
        self.commit("cancel-preview")
        self.query(preview, code="CANDIDATE_STALE")
        preview = self.preview(self.source(panel=922))
        self.commit("confirm " + str(preview["token"]))
        self.query(preview, code="CANDIDATE_STALE")
        old = self.preview(self.source(panel=915))
        new = self.preview(self.rule(key=1, name="new"))
        self.query(old, code="CANDIDATE_STALE")
        self.assert_geometry(self.query(new)["query"], case(panel=922), "R14CQ_NEW_TOKEN_UNAFFECTED")
        self.commit("cancel-preview")
        invalid = self.preview(self.rule(divisions=(5, 2), key=1), valid=False)
        self.query(invalid, code="CANDIDATE_STALE")
        self.commit("cancel-preview")
        stale = self.preview(self.source(panel=915))
        self.commit("boundary 9 outline 0,0 100,0 100,100 0,100")
        self.query(stale, code="CANDIDATE_STALE")
        self.assertFalse(self.ask("line confirm " + str(stale["token"]))["ok"], "R14CQ_STALE_CONFIRM_STILL_REFUSED")

    def test_09_canvas_position_keeps_geometry_candidate_readable(self):
        self.seed()
        preview = self.preview(self.source(panel=922))
        revision = self.revision()
        self.commit("canvas-pos grid-system 0 120 80")
        self.assertEqual(revision, self.revision(), "R14CQ_D12_DOES_NOT_EXPIRE_GEOMETRY")
        self.assert_geometry(self.query(preview)["query"], case(panel=922), "R14CQ_CANVAS_LAYOUT_IS_NOT_GEOMETRY")
        self.commit("confirm " + str(preview["token"]))

    def test_10_geometry_overflow_and_selector_miss_keep_pending_preview(self):
        self.seed()
        preview = self.preview(self.rule(key=1, selector="cell -1 0"))
        self.query(preview, tail="system 0 rule 1 cell 0 0", code="QUERY_INVALID")
        self.assert_geometry(self.query(preview)["query"], case(), "R14CQ_SELECTOR_MATCH")
        self.commit("cancel-preview")
        preview = self.preview(self.rule(key=1, name="range"))
        for value in ("9223372036854775807", "-9223372036854775808"):
            self.query(preview, tail=f"system 0 rule 1 cell {value} 0", code="QUERY_INVALID")
        self.assert_geometry(self.query(preview)["query"], case(), "R14CQ_RANGE_ERROR_DOES_NOT_CONSUME")
        self.commit("confirm " + str(preview["token"]))

    def test_11_exact_pitch_oracle_scan_matches_native_candidate_or_i25a_refusal(self):
        # Complete product cross-product: 9 consecutive panels, 3 gaps, 3
        # divisors, 2 signed cells; no selected-only happy-path sample.
        accepted = rejected = 0
        for panel in range(910, 919):
            # Independent cases must not accumulate an unrelated 81-case
            # undo history in one native World. Every input is still tested.
            with _bridge.BridgeSession(self.executable) as scanner:
                self.session = scanner
                for gap in (0, 2, 3):
                    for divisor in (5, 7, 13):
                        self.commit("reset")
                        self.commit(self.source(panel=panel, gap=gap, anchor=-17))
                        valid = (panel + gap) % divisor == 0
                        preview = self.preview(self.rule(divisions=(divisor, 2)), valid=valid)
                        if valid:
                            for i in (-1, 0):
                                inputs = case(panel, gap, -17, (divisor, 2), (i, -1))
                                value = self.query(preview, tail=f"system 0 rule 1 cell {i} -1")
                                self.assert_geometry(value["query"], inputs, "R14CQ_SCAN_EXACT_VALUE")
                            accepted += 1
                        else:
                            messages = json.dumps(preview["violations"])
                            self.assertIn("DIVISION_NOT_EXACT", messages, "R14CQ_SCAN_I25A_REASON")
                            self.query(preview, code="CANDIDATE_STALE")
                            rejected += 1
                        self.commit("cancel-preview")
        self.assertEqual(81, accepted + rejected, "R14CQ_SCAN_NO_DROPPED_CASES")
        self.assertGreater(accepted, 0)
        self.assertGreater(rejected, 0)
        print(f"R14CQ_NATIVE_SCAN cases={accepted+rejected} accepted={accepted} rejected={rejected}")

    def test_12_oracle_checker_rejects_forged_bounds_lines_and_status(self):
        inputs = case()
        output = oracle.build(inputs)
        self.assertEqual([], oracle.check(inputs, output), "R14CQ_ORACLE_BASELINE")
        for name in ("bounds", "position", "index", "missing", "rejected"):
            altered = copy.deepcopy(output)
            if name == "bounds":
                altered["bounds"][0] += 1
            elif name == "position":
                altered["lines"][0][2] += 1
            elif name == "index":
                altered["lines"][0][1] += 1
            elif name == "missing":
                altered["lines"].pop()
            else:
                altered["status"] = "rejected"
            self.assertTrue(oracle.check(inputs, altered), "R14CQ_ORACLE_SENSITIVITY_" + name.upper())
        self.assertEqual([], oracle.check(inputs, output), "R14CQ_ORACLE_RESTORED")
        nonintegral = case(panel=1830, gap=2, divisions=(5, 2))
        refused = oracle.build(nonintegral)
        self.assertEqual("rejected", refused["status"], "R14CQ_1832_NOT_366")
        self.assertEqual([], oracle.check(nonintegral, refused))
        exact = oracle.build(case(panel=1830, gap=0, divisions=(5, 2)))
        self.assertEqual([366, 732, 1098, 1464], [x[2] for x in exact["lines"] if x[0] == "u"], "R14CQ_1830_FIVE_INTERVALS")

    def test_13_real_foreign_candidate_owners_are_rejected_without_consuming_their_tokens(self):
        # These are the existing public owners' valid fixture definitions, not
        # misspelled owner strings in the new command's grammar.
        from tests.test_assembly_rules import rule as assembly_rule
        from tests.test_section_profile_native import profile as section_profile
        from tests.test_panel_fill_finish_surface import surface as finish_surface
        fixtures = (
            ("assembly", {"op": "publish-rule", "value": assembly_rule()}),
            ("section-profile", {"op": "put-profile", "value": section_profile()}),
            ("panel-fill", {"op": "put-finish-surface", "value": finish_surface(boundary=9, obstacles=[])}),
        )
        for owner, operation in fixtures:
            with self.subTest(owner=owner):
                self.commit("reset")
                self.seed()
                if owner == "panel-fill":
                    self.commit("boundary 9 outline 0,0 2000,0 2000,1600 0,1600")
                preview = self.engineering([operation], command=owner + "-preview",
                                           schema=owner + "-transaction/1")
                for kind in ("reference", "engineering"):
                    self.query(preview, kind=kind, code="CANDIDATE_KIND")
                self.assertTrue(self.ask(owner + "-confirm " + str(preview["token"]))["ok"],
                                "R14CQ_FOREIGN_CONFIRM_SURVIVES_READS")

    def test_14_open_history_group_refuses_read_then_same_token_recovers(self):
        self.seed()
        preview = self.preview(self.source(panel=922))
        revision = self.revision()
        self.commit("history-begin")
        self.assertEqual(revision, self.revision(), "R14CQ_GROUP_WITHOUT_REVISION_CHANGE")
        self.query(preview, code="CANDIDATE_STALE")
        self.commit("history-end")
        self.assert_geometry(self.query(preview)["query"], case(panel=922), "R14CQ_GROUP_CLOSED_RECOVERS_TOKEN")
        self.commit("confirm " + str(preview["token"]))

    def test_15_current_seal_guard_is_independent_of_revision_and_does_not_consume(self):
        # The probe is the real bridge with two test-only stdin markers. It
        # alters sealed operation metadata, not World, revision, or token.
        # Original binaries.py builds, smokes and fingerprints it; no sidecar
        # or product test hook is fabricated by this suite.
        from tests import binaries
        old_out = binaries.OUT_DIR
        try:
            binaries.OUT_DIR = self.directory / "seal-bin"
            binary = binaries.Binary(
                "r14-candidate-seal", "r14-candidate-seal", "tests/diagnostics/r14_candidate_query_seal.c",
                ["/nologo", "/utf-8", "/Od", "/W3", "/U_WIN32"], ["/STACK:16777216"],
                ["-std=c11", "-O0"], [], smoke="bridge")
            result = binaries.build_one(binary)
            self.assertIn(result.status, ("built", "reused"), ("R14CQ_SEAL_BUILD", result.status, result.detail))
            self.assertEqual("fresh", binaries.inspect_one(binary).state, "R14CQ_SEAL_BUILD_FRESH")
            probe = SealProbeSession(binary)
        finally:
            binaries.OUT_DIR = old_out
        self.addCleanup(probe.stop)
        self.session = probe
        self.commit("reset")
        self.commit(self.source())
        preview = self.preview(self.rule())
        revision = str(self.revision())
        before = self.snapshot()
        self.assertEqual({"ok": True, "tampered": True, "token": preview["token"], "revision": revision},
                         self.ask("r14-test-seal-tamper"), "R14CQ_SEAL_FIXTURE_READY")
        rejected = self.ask(f"grid-rule-candidate-query reference {preview['token']} side after system 0 rule 1 cell -1 0")
        self.assertFalse(rejected.get("ok"), "R14CQ_SEAL_STALE")
        self.assertEqual("CANDIDATE_STALE", rejected.get("code"), "R14CQ_SEAL_STALE")
        self.assertEqual(before, self.snapshot(), "R14CQ_SEAL_ZERO_WRITE")
        self.assertEqual({"ok": True, "tampered": False, "token": preview["token"], "revision": revision},
                         self.ask("r14-test-seal-restore"), "R14CQ_SEAL_FIXTURE_RESTORED")
        self.assert_geometry(self.query(preview)["query"], case(), "R14CQ_SEAL_RESTORED_COORDINATES")
        confirmed = self.ask("line confirm " + str(preview["token"]))
        self.assertTrue(confirmed.get("ok"), "R14CQ_SEAL_SAME_TOKEN_CONFIRMS")
        self.assertEqual(int(revision) + 1, confirmed.get("revision"), "R14CQ_SEAL_CONFIRM_ONE_REVISION")


if __name__ == "__main__":
    program = unittest.main(verbosity=2, exit=False)
    if program.result.skipped:
        print("R14CQ_BLOCKED: a skipped check is not a passing or killed-product receipt", file=sys.stderr)
        raise SystemExit(2)
    raise SystemExit(0 if program.result.wasSuccessful() else 1)
