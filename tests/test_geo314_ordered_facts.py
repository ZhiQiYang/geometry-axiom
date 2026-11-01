"""Actual H candidate evidence, seals and confirmation, with normal-ASSERT controls.

The witness includes the production bridge. Negative controls compile temporary
copies of the same source closure, changing only the named guard; no source or
binary in the invoking checkout is modified. The MP3-only observation is an
explicit preview-masked equivalent, and the paired MP1+MP3 control proves depth.
"""
from __future__ import annotations

import base64
import json
from pathlib import Path
import re
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from tests.test_geo261_native_kernel import native
from tests.test_parameters_core import card, field

DEFINES = ["GEOMETRY_KERNEL_EXTERNAL=1", "GEOMETRY_WOODWORKING_EXTERNAL=1",
           "GEOMETRY_HOST_HISTORY_EXTERNAL=1", "GEOMETRY_HOST_CANDIDATE_EXTERNAL=1"]
WORLD = "geometry-app/native/world_candidate.inc"
CURRENT = "current_geometry.c"
BATCH = "geometry-web/engineering_bridge.inc"
TRANSACTIONS = "geometry-core/transactions.inc"
CLOSURE = (WORLD, CURRENT, BATCH, TRANSACTIONS, "geometry-web/web_bridge.c",
           "tests/geo314_stagger_facts_harness.c")
CONFIRM_CONTEXT = (
    "    g_boundary_keyed_update=candidate->operation.boundary_keyed;g_boundary_keyed_id=candidate->operation.boundary_id;\n"
    "    bool ok=app_world_candidate_evaluate(candidate,app_world_revalidate_evaluate,&candidate->before)==GEO_CANDIDATE_OK;")
DSL_BASELINE = "const World *previous_baseline=g_subgrid_before;g_subgrid_before=call->before;"
CONFIRM_BASELINE = "const World *previous=g_subgrid_before;g_subgrid_before=&candidate->before;"


def replace_once(source, before, after):
    if source.count(before) != 1:
        raise AssertionError("Production control must have one exact anchor: " + before)
    return source.replace(before, after)


class OrderedStaggerFacts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        build = native()
        cls.directory = build.work / "geo314-ordered-facts"
        cls.directory.mkdir()
        cls.fixture = ROOT / "tests/fixtures/legacy-two-axis-stagger-param.scene"
        if not cls.fixture.is_file():
            raise AssertionError("Missing frozen pre-policy legacy fixture: " + str(cls.fixture))
        rows = re.findall(r"^grid-system (\d+) .*stagger param:901:1.*stagger param:901:2",
                          cls.fixture.read_text(encoding="utf-8"), re.M)
        if len(rows) != 1:
            raise AssertionError("The frozen fixture must declare one independent 400/300 parameter baseline")
        cls.identifier = int(rows[0])
        value = {"id": cls.identifier, "name": "G", "mainAlong": "none",
                 "u": "repeat 0 2000 stagger 500", "v": "repeat 0 1830 stagger param:901:2"}
        parameter = card(901, "offset", [field(1, "500"), field(2, "300")])
        good = {"schema": "engineering-transaction/1", "expectedRevision": 0,
                "operations": [parameter, {"op": "put-grid-system", "value": value}]}
        bad = json.loads(json.dumps(good))
        bad["operations"][1]["value"]["u"] = "repeat 0 2000 stagger 450"
        cls.good = cls.directory / "good.json"
        cls.bad = cls.directory / "bad.json"
        cls.good.write_text(json.dumps(good, ensure_ascii=False), encoding="utf-8")
        cls.bad.write_text(json.dumps(bad, ensure_ascii=False), encoding="utf-8")
        archive = base64.b64encode(json.dumps(bad["operations"][1], ensure_ascii=False,
                                           separators=(",", ":")).encode("utf-8")).decode("ascii")
        cls.archive = cls.directory / "archive-command.txt"
        cls.archive.write_text("engineering archive " + archive, encoding="utf-8")
        cls.original = {path: (ROOT / path).read_text(encoding="utf-8") for path in CLOSURE}
        cls.executables = {}
        cls.exe = cls.compile_closure("baseline", ())

    @classmethod
    def compile_closure(cls, name, changes):
        """Only quoted include locations change besides the explicit controls."""
        key = (name, tuple(changes))
        if key in cls.executables:
            return cls.executables[key]
        build = native()
        directory = cls.directory / name
        directory.mkdir()
        source = dict(cls.original)
        for path, before, after in changes:
            source[path] = replace_once(source[path], before, after)
        outputs = {str((ROOT / path).resolve()): directory / path for path in CLOSURE}
        for path in CLOSURE:
            original = ROOT / path
            target = outputs[str(original.resolve())]
            target.parent.mkdir(parents=True, exist_ok=True)

            def include(match):
                include_path = (original.parent / match.group(1)).resolve()
                if str(include_path) in outputs:
                    destination = outputs[str(include_path)]
                elif include_path.is_file():
                    destination = include_path
                else:
                    return match.group(0)
                return '#include "' + destination.as_posix() + '"'

            relocated = re.sub(r'^#include "([^"\n]+)"', include, source[path], flags=re.M)
            target.write_text(relocated, encoding="utf-8")
        client = build.compile(outputs[str((ROOT / CLOSURE[-1]).resolve())],
                               "geo314-ordered-" + name, DEFINES)
        exe = build.link("geo314-ordered-" + name, [client, *build.product_objects()])
        cls.executables[key] = exe
        return exe

    def run_case(self, name, exe=None):
        saved = self.directory / ("saved-" + name + ".scene")
        result = subprocess.run([str(exe or self.exe), name, str(self.fixture), str(self.good),
                                 str(self.bad), str(saved), str(self.archive)],
                                capture_output=True, text=True, timeout=60)
        self.assertIn(result.returncode, (0, 1), "Crash/setup failure is not a guard verdict: "
                      + result.stdout + result.stderr)
        return result

    def pass_case(self, name, exe=None):
        result = self.run_case(name, exe)
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        self.assertEqual([], [row for row in result.stderr.splitlines() if row.startswith("ASSERT:")])
        if not name.startswith("archive-"):
            self.assertEqual("", result.stderr)
        self.assertTrue(result.stdout.endswith("PASS " + name + "\n"), result.stdout)
        return result

    @staticmethod
    def row(result):
        return {"command": result.args, "exit_code": result.returncode,
                "stdout": result.stdout, "stderr": result.stderr}

    def control(self, name, case, marker, changes):
        baseline = self.pass_case(case)
        changed = self.run_case(case, self.compile_closure(name, tuple(changes)))
        self.assertEqual(1, changed.returncode, changed.stdout + changed.stderr)
        self.assertEqual(["ASSERT:" + marker],
                         [row for row in changed.stderr.splitlines() if row.startswith("ASSERT:")],
                         "A different assertion, a crash or setup error cannot count as this control")
        self.assertFalse(changed.stdout.endswith("PASS " + case + "\n"), changed.stdout)
        restored = self.pass_case(case)
        print("GEO314_H_CONTROL_JSON " + json.dumps({"control": name,
            "baseline": self.row(baseline), "withdrawn": self.row(changed),
            "restored": self.row(restored)}, ensure_ascii=False), flush=True)

    def test_ordered_facts_are_exact_original_steps_and_sealed_with_candidate(self):
        self.pass_case("sealed")

    def test_fact_bytes_order_count_revision_and_provider_tampering_are_rejected(self):
        self.pass_case("tamper")

    def test_confirm_revalidation_retains_identical_facts_candidate_and_revision(self):
        self.pass_case("confirm-evidence")

    def test_cancel_and_stale_confirmation_clear_evidence_without_publication(self):
        self.pass_case("cancel")
        self.pass_case("stale")

    def test_failed_preview_clears_evidence_and_keeps_definition_and_revision(self):
        self.pass_case("failure")

    def test_success_clears_evidence_and_dump_history_reopen_preserve_definition_bytes(self):
        self.pass_case("success")

    def test_dispose_clears_owned_evidence_before_candidate_pool_reuse(self):
        self.pass_case("dispose")

    def test_withdrawing_facts_digest_guard_fails_normal_byte_tamper_assertion(self):
        self.control("no-facts-seal", "tamper", "ordered-facts-byte-tamper-rejected", [
            (WORLD, "return !strcmp(hash,candidate->operation.stagger_seal);", "return true;")])

    def test_withdrawing_facts_at_confirmation_fails_locked_Q3_positive(self):
        self.control("confirm-drops-facts", "confirm-evidence", "ordered-confirm-retains-evidence", [
            (CURRENT, CONFIRM_CONTEXT, CONFIRM_CONTEXT.replace("    bool ok=",
                "    app_world_candidate_clear_stagger(candidate);\n    bool ok="))])

    def test_final_store_only_without_step_recording_fails_locked_Q3_positive(self):
        self.control("no-recorded-order", "sealed", "ordered-card-then-unbind-preview-valid", [
            (BATCH, "if(ok&&!app_stagger_record_step(candidate,&stagger_before))", "if(0)")])

    def test_withdrawing_failed_preview_cleanup_fails_normal_ownership_assertion(self):
        self.control("failure-keeps-facts", "failure", "ordered-failed-preview-clears-evidence", [
            (BATCH, "if(!ok)app_world_candidate_clear_stagger(transaction);",
             "if(0)app_world_candidate_clear_stagger(transaction);")])

    def test_archive_preview_and_confirmation_pin_their_independent_rejections(self):
        self.pass_case("archive-preview")
        self.pass_case("archive-depth")

    def test_withdrawing_archive_baseline_breaks_preview_but_confirmation_still_rejects(self):
        change = (TRANSACTIONS, DSL_BASELINE, DSL_BASELINE.replace("=call->before;", "=NULL;"))
        self.control("archive-no-baseline", "archive-preview",
                     "ordered-archive-preview-rejects-value-change", [change])
        self.pass_case("archive-depth", self.compile_closure("archive-no-baseline", (change,)))

    def test_confirmation_only_is_equivalent_but_paired_missing_baselines_fail_confirm_assertion(self):
        confirm = (CURRENT, CONFIRM_BASELINE, CONFIRM_BASELINE.replace("=&candidate->before;", "=NULL;"))
        # Preview rejects before confirmation is reachable. This is observed as
        # equivalent, never reported as a killed standalone MP3 mutant.
        equivalent = self.pass_case("archive-depth", self.compile_closure("confirm-only-equivalent", (confirm,)))
        print("GEO314_MP3_EQUIVALENT_JSON " + json.dumps(self.row(equivalent), ensure_ascii=False), flush=True)
        submission = (TRANSACTIONS, DSL_BASELINE, DSL_BASELINE.replace("=call->before;", "=NULL;"))
        self.control("paired-archive-and-confirm-no-baseline", "archive-depth",
                     "ordered-confirmation-baseline-still-rejects", [submission, confirm])


if __name__ == "__main__":
    unittest.main(verbosity=2)
