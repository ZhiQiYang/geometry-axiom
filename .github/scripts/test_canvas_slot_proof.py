"""Pure parser/provenance controls; these fixtures are not browser receipts."""
from copy import deepcopy
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

try:
    import canvas_slot_proof as proof
except ModuleNotFoundError as error:
    if error.name != "canvas_slot_proof":
        raise
    proof = None


def fixture():
    raw, rows = {}, []
    for control in proof.CONTROLS:
        row = {"id": control[0]}
        for phase in ("baseline", "withdrawn", "restored"):
            failed = phase == "withdrawn"
            variant = control[1] if failed else "none"
            original_hash, mutation_hash = proof.variant_hashes(variant)
            result = {"schema": "geometry-canvas-slot-probe/1", "mutation": variant, "completed": True,
                      "infrastructureError": False, "skipped": [], "browserVersion": "fixture-only",
                      "passedAssertions": 1 if failed else 2, "failedAssertions": 1 if failed else 0,
                      "registrySourceSha256": original_hash, "mutationSourceSha256": mutation_hash,
                      "tests": [{"id": test[0], "passed": not (failed and test == control),
                                 "oracle": control[2] if failed and test == control else None}
                                for test in proof.CONTROLS]}
            prefix = control[0] + "/" + phase
            stdout = ("CANVAS_SLOT_MUTATION_RESULT " + json.dumps(result) + "\n").encode()
            raw[prefix + ".stdout"], raw[prefix + ".stderr"] = stdout, b""
            row[phase] = {**proof.verify_phase(result, int(failed), control, phase),
                          "stdout": prefix + ".stdout", "stderr": prefix + ".stderr",
                          "stdoutSha256": proof.sha(stdout), "stderrSha256": proof.sha(b""),
                          "registrySourceSha256": original_hash, "mutationSourceSha256": mutation_hash,
                          "command": ["node", ".github/scripts/canvas_slot_probe.cjs", variant],
                          "files": {"mutations/" + prefix + ".stdout": proof.sha(stdout),
                                    "mutations/" + prefix + ".stderr": proof.sha(b"")}}
        rows.append(row)
    return {"schema": "geometry-canvas-slot-mutations/1", "acceptance": False, "rows": rows}, raw


class CanvasSlotProof(unittest.TestCase):
    def setUp(self):
        self.receipt, self.raw = fixture()

    def test_complete_parser_fixture_passes_without_claiming_browser_execution(self):
        wanted = proof.validate_mutations(self.receipt, self.raw.__getitem__)
        self.assertEqual(wanted, {"manifest.json", *self.raw})

    def test_six_captures_and_one_withdrawal_artifact_are_required(self):
        names = proof.expected_artifact_names("P999", "2")
        self.assertEqual(len(names), 7)
        self.assertEqual(set(names.values()), {"mutations", *("slot" + str(unit) + "/" + mode
                                                             for unit in (1, 2) for mode in proof.MODES)})
        self.assertTrue(all(name.startswith("canvas-slot-P999-2-") for name in names))

    def test_partial_scope_is_rejected_instead_of_cleared(self):
        with patch.dict(os.environ, {"GEOMETRY_PARAMETERS_ONLY": "1"}, clear=True):
            with self.assertRaisesRegex(ValueError, "SCOPE_CONTAMINATED"):
                proof.scope_environment("full")

    def test_golden_update_flag_is_rejected_even_when_empty(self):
        with patch.dict(os.environ, {"GEOMETRY_CDP_UPDATE_GOLDEN": ""}, clear=True):
            with self.assertRaisesRegex(ValueError, "SCOPE_CONTAMINATED"):
                proof.scope_environment("shard1")

    def test_each_scope_has_its_exact_harness_mode(self):
        with patch.dict(os.environ, {}, clear=True):
            self.assertNotIn("GEOMETRY_CDP_SHARD", proof.scope_environment("full"))
            self.assertEqual(proof.scope_environment("shard1")["GEOMETRY_CDP_SHARD"], "1/2")
            self.assertEqual(proof.scope_environment("shard2")["GEOMETRY_CDP_SHARD"], "2/2")

    def test_parser_rejects_missing_or_duplicate_result(self):
        raw = next(iter(self.raw.values()))
        for candidate in (b"", raw + raw):
            with self.subTest(raw=candidate), self.assertRaisesRegex(ValueError, "RESULT_COUNT"):
                proof.mutation_result(candidate)

    def test_infrastructure_failure_never_counts_as_a_kill(self):
        control = proof.CONTROLS[0]
        result = proof.mutation_result(self.raw[control[0] + "/withdrawn.stdout"])
        result["infrastructureError"] = True
        with self.assertRaisesRegex(ValueError, "INFRASTRUCTURE"):
            proof.verify_phase(result, 1, control, "withdrawn")

    def test_wrong_named_oracle_is_rejected(self):
        control = proof.CONTROLS[0]
        result = proof.mutation_result(self.raw[control[0] + "/withdrawn.stdout"])
        result["tests"][0]["oracle"] = "an unrelated assertion"
        with self.assertRaisesRegex(ValueError, "WRONG_ORACLE"):
            proof.verify_phase(result, 1, control, "withdrawn")

    def test_one_test_cannot_disappear_from_a_phase(self):
        control = proof.CONTROLS[0]
        result = proof.mutation_result(self.raw[control[0] + "/baseline.stdout"])
        result["tests"].pop()
        with self.assertRaisesRegex(ValueError, "TEST_SET"):
            proof.verify_phase(result, 0, control, "baseline")

    def test_skip_is_not_a_green_phase(self):
        control = proof.CONTROLS[0]
        result = proof.mutation_result(self.raw[control[0] + "/baseline.stdout"])
        result["skipped"] = [control[0]]
        with self.assertRaisesRegex(ValueError, "INFRASTRUCTURE"):
            proof.verify_phase(result, 0, control, "baseline")

    def test_true_is_not_an_exit_code(self):
        control = proof.CONTROLS[0]
        result = proof.mutation_result(self.raw[control[0] + "/withdrawn.stdout"])
        with self.assertRaisesRegex(ValueError, "MUTATION_EXIT"):
            proof.verify_phase(result, True, control, "withdrawn")

    def test_raw_hash_mismatch_is_rejected(self):
        self.raw[next(iter(self.raw))] += b"changed\n"
        with self.assertRaisesRegex(ValueError, "RAW_HASH"):
            proof.validate_mutations(self.receipt, self.raw.__getitem__)

    def test_phase_cannot_redirect_its_raw_path(self):
        self.receipt["rows"][0]["baseline"]["stdout"] = "../another.stdout"
        with self.assertRaisesRegex(ValueError, "RAW_PATH"):
            proof.validate_mutations(self.receipt, self.raw.__getitem__)

    def test_source_hash_is_bound_beyond_the_result_counts(self):
        item = self.receipt["rows"][0]["withdrawn"]
        item["mutationSourceSha256"] = "f" * 64
        with self.assertRaisesRegex(ValueError, "SOURCE_HASH"):
            proof.validate_mutations(self.receipt, self.raw.__getitem__)

    def test_fake_011_summary_cannot_replace_raw_010(self):
        self.receipt["rows"][0]["restored"]["exit"] = 1
        with self.assertRaisesRegex(ValueError, "MUTATION_EXIT"):
            proof.validate_mutations(self.receipt, self.raw.__getitem__)

    def test_node_and_python_use_identical_exact_withdrawal_bytes(self):
        expression = ("const P=require('./.github/scripts/canvas_slot_probe.cjs');"
                      "const r=P.loadWrapper(process.argv[1]);"
                      "process.stdout.write(JSON.stringify([r.registrySourceSha256,r.mutationSourceSha256]));")
        for variant in ("none", "omit-restore", "omit-guard"):
            with self.subTest(variant=variant):
                result = subprocess.check_output(["node", "-e", expression, variant], cwd=proof.ROOT)
                self.assertEqual(tuple(json.loads(result)), proof.variant_hashes(variant))

    def test_zip_is_deterministic_and_missing_raw_is_rejected(self):
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            folder = root / "input"
            for relative, raw in self.raw.items():
                target = folder / "mutations" / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(raw)
            (folder / "mutations/manifest.json").write_text(json.dumps(self.receipt), encoding="utf-8")
            first, second = root / "first.zip", root / "second.zip"
            proof.make_zip(folder, first)
            proof.make_zip(folder, second)
            self.assertEqual(first.read_bytes(), second.read_bytes())
            checked = proof.verify_mutation_archive(first, "mutations/manifest.json")
            self.assertEqual(checked["exitCodes"], [[0, 1, 0], [0, 1, 0]])
            (folder / "mutations" / next(iter(self.raw))).unlink()
            proof.make_zip(folder, second)
            with self.assertRaises((KeyError, ValueError)):
                proof.verify_mutation_archive(second, "mutations/manifest.json")

    def test_file_with_a_symlink_is_not_a_raw_capture(self):
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            (root / "source").write_bytes(b"fixture")
            (root / "alias").symlink_to(root / "source")
            with self.assertRaisesRegex(ValueError, "RAW_FILE"):
                proof.read(root / "alias")

    def capture_fixture(self, folder):
        scope = {"mode": "full", "url": "http://127.0.0.1:18839/", "feedbackDirectory": "/tmp/fixture-feedback"}
        result = {"scope": scope, "sections": {}, "passedAssertions": 0}
        raw = {"candidate.json": b"{}", "plan.json": b"{}", "stderr.log": b"", "runtime.stderr": b"",
               "stdout.log": ("CDP_RESULT " + json.dumps(result) + "\n").encode(),
               "runtime.stdout": json.dumps({"schema": "geometry-runtime/1", "fresh": True,
                                              "root": "/fixture-root", "version": "fixture-version"}).encode()}
        for name, value in raw.items():
            (folder / name).write_bytes(value)
        return {"schema": "geometry-canvas-slot-capture/1", "acceptance": False, "mode": "full",
                "command": ["node", "geometry-web/cdp_test.js"],
                "runtime_command": ["<python>", "-B", "geometry-web/runtime_version.py", "--probe", "18839"],
                "environment": {"GEOMETRY_TEST_URL": scope["url"], "GEOMETRY_FEEDBACK_DIR": scope["feedbackDirectory"]},
                "scope": scope, "sections": {}, "assertions": 0, "execution_root": "/fixture-root",
                "runtime_version": "fixture-version", "files": {name: proof.sha(value) for name, value in raw.items()}}

    def test_capture_checks_current_runtime_version_before_delegating(self):
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            receipt = self.capture_fixture(root)
            with patch.object(proof.evidence, "runtime_version", return_value="other-source"), patch.object(proof, "node") as gate:
                with self.assertRaisesRegex(ValueError, "RUNTIME_SOURCE"):
                    proof.verify_run(receipt, root)
                gate.assert_not_called()

    def test_capture_rejects_a_different_original_command(self):
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            receipt = self.capture_fixture(root)
            receipt["command"] = ["node", "an-unrelated-check.js"]
            with self.assertRaisesRegex(ValueError, "COMMAND"):
                proof.verify_run(receipt, root)

    def test_capture_summary_cannot_change_the_actual_scope(self):
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            receipt = self.capture_fixture(root)
            receipt["environment"]["GEOMETRY_FEEDBACK_DIR"] = "/tmp/another-feedback"
            with patch.object(proof.evidence, "runtime_version", return_value="fixture-version"):
                with self.assertRaisesRegex(ValueError, "FAKE_SUMMARY"):
                    proof.verify_run(receipt, root)


def load_tests(loader, tests, pattern):
    if proof is not None:
        return tests

    def missing_supervisor():
        raise AssertionError("R386 source-bound canvas slot supervisor is absent")

    return unittest.TestSuite([unittest.FunctionTestCase(missing_supervisor)])


if __name__ == "__main__":
    unittest.main()
