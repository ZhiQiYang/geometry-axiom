"""True native isolation/freshness plus explicit synthetic transport controls.

NativeExecutor verdict tests use the registry-verified C bridge. The small C
harness below tests only private pipe/process failure boundaries; it cannot
produce a product case receipt or substitute for a geometry oracle.
"""
from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import tempfile
import threading
import time
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "geometry-core"))
sys.path.insert(0, str(ROOT))

from rule_cases.catalog import case
from rule_cases.definition import definition_hash, digest
from rule_cases.executor import (MAX_RECEIPT_BYTES, NativeExecutor, ReceiptValidationError,
                                 _Child, _Stop, _diagnostic_matches, refresh_receipt)
from rule_cases.runtime import runtime_identity
from tests import binaries
from tests._bridge import BridgeSession, find_bridge
from tests.test_assembly_rules import rule


class ExecutorBounds(unittest.TestCase):
    def test_host_limits_reject_bool_nonfinite_and_unbounded_values(self):
        for timeout in (True, 0, .009, 31, float("nan"), float("inf"), "1"):
            with self.subTest(timeout=timeout), self.assertRaises(ValueError):
                NativeExecutor(timeout_seconds=timeout)
        for size in (True, 0, -1, 2097153, 1.5, "1"):
            with self.subTest(size=size), self.assertRaises(ValueError):
                NativeExecutor(max_output_bytes=size)

    def test_project_context_rejects_invalid_scope_before_native_execution(self):
        value = case("legal-rule")
        executor = NativeExecutor()
        for project in (None, "", "x" * 129):
            with self.subTest(project=project), self.assertRaises(ValueError):
                executor.run(value, project_id=project, generation=0)
        for generation in (True, -1, 2**53, .5, "0"):
            with self.subTest(generation=generation), self.assertRaises(ValueError):
                executor.run(value, project_id="project", generation=generation)


class TrueNativeExecutor(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.bridge = find_bridge()
        cls.executor = NativeExecutor(cls.bridge)
        cls.definition = case("legal-rule")
        cls.receipt = cls.executor.run(cls.definition, project_id="receipt-project", generation=7)
        if cls.receipt["status"] != "passed":
            raise AssertionError(cls.receipt)
        cls.identity, _ = runtime_identity(cls.bridge)

    def run_case(self, value=None, **kwargs):
        return self.executor.run(value or self.definition, project_id="executor-project", generation=3, **kwargs)

    def test_repeated_runs_have_fresh_processes_and_remove_private_directories(self):
        second = self.run_case()
        self.assertEqual("passed", second["status"], second)
        self.assertNotEqual(self.receipt["conditions"]["nativePid"], second["conditions"]["nativePid"])
        for receipt in (self.receipt, second):
            self.assertTrue(receipt["conditions"]["isolated"])
            self.assertTrue(receipt["conditions"]["privateDirectoryRemoved"])
            self.assertIsInstance(receipt["conditions"]["nativePid"], int)

    def test_separate_formal_world_history_and_pending_token_survive_run(self):
        with tempfile.TemporaryDirectory(prefix="formal-case-control-") as name:
            with BridgeSession(self.bridge, cwd=name) as formal:
                self.assertTrue(formal.command("reset")["ok"])
                self.assertTrue(formal.command("line spec retained 27")["ok"])
                path = Path(name) / "pending.json"
                path.write_text(json.dumps({"schema": "assembly-transaction/1",
                                           "expectedRevision": formal.command("assembly-read")["revision"],
                                           "operations": [{"op": "publish-rule", "value": rule()}]}), encoding="utf-8")
                pending = formal.command("assembly-preview " + str(path))["preview"]
                self.assertTrue(pending["valid"])
                before = formal.command("dump"), formal.command("assembly-read")
                receipt = self.run_case()
                self.assertEqual("passed", receipt["status"], receipt)
                self.assertNotEqual(formal.process.pid, receipt["conditions"]["nativePid"])
                self.assertEqual(before, (formal.command("dump"), formal.command("assembly-read")))
                self.assertTrue(formal.command("assembly-confirm " + str(pending["token"]))["ok"])
                self.assertEqual(1, len(formal.command("assembly-read")["state"]["rules"]))
                self.assertTrue(formal.command("line undo")["ok"])
                self.assertEqual(before[0]["text"], formal.command("dump")["text"])
                self.assertTrue(formal.command("line undo")["ok"])
                self.assertNotIn("spec retained 27", formal.command("dump")["text"])

    def test_real_native_missing_capability_is_nonpass(self):
        value = deepcopy(self.definition)
        value["requiredCapabilities"].append("synthetic-absent-capability/1")
        receipt = self.run_case(value)
        self.assertEqual("missing-capability", receipt["status"], receipt)
        self.assertEqual(["synthetic-absent-capability/1"], receipt["missingCapabilities"])
        self.assertIsNone(receipt["actualOutcome"])
        self.assertEqual([], receipt["assertionResults"])
        self.assertTrue(receipt["conditions"]["privateDirectoryRemoved"])

    def test_precancelled_run_preserves_a_nonpass_receipt_and_cleans_up(self):
        cancelled = threading.Event()
        cancelled.set()
        receipt = self.run_case(cancel=cancelled)
        self.assertEqual(("blocked", "cancelled"), (receipt["status"], receipt["reason"]))
        self.assertIsNone(receipt["actualOutcome"])
        self.assertTrue(receipt["conditions"]["privateDirectoryRemoved"])

    def test_actual_bridge_output_above_tiny_cap_is_nonpass(self):
        receipt = NativeExecutor(self.bridge, max_output_bytes=1).run(
            self.definition, project_id="tiny-output-control", generation=0)
        self.assertEqual(("blocked", "output-capacity"), (receipt["status"], receipt["reason"]))
        self.assertIsNone(receipt["actualOutcome"])
        self.assertTrue(receipt["conditions"]["privateDirectoryRemoved"])

    def test_binary_without_sidecar_is_unknown_and_never_started(self):
        with tempfile.TemporaryDirectory(prefix="unknown-case-runtime-") as name:
            copied = Path(name) / Path(self.bridge).name
            shutil.copy2(self.bridge, copied)
            receipt = NativeExecutor(copied).run(self.definition, project_id="unknown-runtime", generation=0)
            self.assertEqual("unknown-runtime", receipt["status"], receipt)
            self.assertFalse(receipt["executor"]["known"])
            self.assertIsNone(receipt["conditions"]["nativePid"])
            self.assertIsNone(receipt["actualOutcome"])

    def test_sidecar_cannot_authorize_different_binary_bytes(self):
        with tempfile.TemporaryDirectory(prefix="changed-case-runtime-") as name:
            copied = Path(name) / Path(self.bridge).name
            shutil.copy2(self.bridge, copied)
            original_sidecar = Path(self.bridge + binaries.SIDECAR_SUFFIX)
            shutil.copy2(original_sidecar, Path(str(copied) + binaries.SIDECAR_SUFFIX))
            with copied.open("ab") as target:
                target.write(b"changed-after-build")
            receipt = NativeExecutor(copied).run(self.definition, project_id="changed-runtime", generation=0)
            self.assertEqual("unknown-runtime", receipt["status"], receipt)
            self.assertIsNone(receipt["conditions"]["nativePid"])

    def test_incorrect_member_or_joint_oracle_turns_real_native_acceptance_red(self):
        for kind in ("member_slot", "joint_tuple"):
            value = case("same-role-distinct-members")
            predicate = next(item for item in value["assertions"] if item["kind"] == kind)
            if kind == "member_slot":
                predicate["slotId"] = 13
            else:
                predicate["value"]["targetMember"] = 37
            with self.subTest(predicate=kind):
                receipt = self.run_case(value)
                self.assertEqual("accepted", receipt["actualOutcome"])
                self.assertEqual(("failed", "assertion-mismatch"), (receipt["status"], receipt["reason"]))
                self.assertTrue(any(not item["passed"] for item in receipt["assertionResults"]))

    def test_typed_native_selectors_survive_rule_and_binding_array_reordering(self):
        member = case("same-role-distinct-members")
        for key in ("slots", "members", "joints"):
            member["input"]["transaction"][0]["value"][key].reverse()
        incomplete = case("legal-incomplete-binding")
        for key in ("slots", "members", "joints"):
            incomplete["input"]["setup"][0]["value"][key].reverse()
        incomplete["sourcePins"][0]["sha256"] = digest(incomplete["input"]["setup"][0]["value"])
        incomplete["input"]["transaction"][0]["value"]["slots"].reverse()
        for value in (member, incomplete):
            with self.subTest(case=value["caseId"]):
                receipt = self.run_case(value)
                self.assertEqual("passed", receipt["status"], receipt)
                self.assertTrue(all(item["passed"] for item in receipt["assertionResults"]))

    def test_same_exact_domains_refresh_without_mutating_retained_evidence(self):
        saved = deepcopy(self.receipt)
        refreshed = refresh_receipt(self.receipt, self.definition, self.identity,
                                    project_id="receipt-project", generation=7)
        self.assertEqual(saved, self.receipt)
        self.assertEqual(saved, refreshed)
        self.assertIsNot(self.receipt, refreshed)
        refreshed["observations"]["after"]["rules"].clear()
        self.assertEqual(saved, self.receipt)

    def test_label_is_part_of_exact_definition_hash_and_stales_old_result(self):
        changed = deepcopy(self.definition)
        changed["label"] += " revised"
        self.assertNotEqual(definition_hash(self.definition), definition_hash(changed))
        refreshed = refresh_receipt(self.receipt, changed, self.identity)
        self.assertEqual("stale", refreshed["status"])
        self.assertEqual(["definition"], refreshed["staleReasons"])
        self.assertEqual("passed", refreshed["recordedStatus"])
        self.assertEqual(self.receipt["observations"], refreshed["observations"])
        self.assertEqual("passed", self.receipt["status"])

    def test_source_definition_change_stales_both_exact_domains(self):
        value = case("one-local-joint-new-version")
        receipt = self.run_case(value)
        changed = deepcopy(value)
        changed["input"]["setup"][0]["value"]["name"] += " changed"
        changed["sourcePins"][0]["sha256"] = digest(changed["input"]["setup"][0]["value"])
        refreshed = refresh_receipt(receipt, changed, receipt["executor"])
        self.assertEqual("stale", refreshed["status"])
        self.assertEqual(["definition", "source"], refreshed["staleReasons"])
        self.assertEqual(receipt["actualDiagnostics"], refreshed["actualDiagnostics"])
        self.assertEqual(receipt["assertionResults"], refreshed["assertionResults"])

    def test_each_runtime_identity_domain_stales_old_result(self):
        for key in ("nativeBinaryHash", "nativeSourceHash", "validatorVersion", "axiomHash", "assertionSchemaHash"):
            identity = deepcopy(self.identity)
            identity[key] = "f" * 64 if identity[key] != "f" * 64 else "0" * 64
            with self.subTest(domain=key):
                refreshed = refresh_receipt(self.receipt, self.definition, identity)
                self.assertEqual("stale", refreshed["status"])
                self.assertEqual(["runtime"], refreshed["staleReasons"])
                self.assertEqual(self.receipt["executor"], refreshed["executor"])

    def test_unknown_runtime_project_and_generation_each_stale_without_retargeting(self):
        controls = [({"known": False, "reason": "synthetic unknown"}, {}, "unknown-runtime"),
                    (self.identity, {"project_id": "other-project"}, "project-context"),
                    (self.identity, {"generation": 8}, "generation")]
        for identity, scope, reason in controls:
            with self.subTest(domain=reason):
                refreshed = refresh_receipt(self.receipt, self.definition, identity, **scope)
                self.assertEqual("stale", refreshed["status"])
                self.assertEqual([reason], refreshed["staleReasons"])
                self.assertEqual(self.receipt["context"], refreshed["context"])
                self.assertEqual(self.receipt["observations"], refreshed["observations"])

    def test_blocked_negative_diagnostic_evidence_remains_blocked_when_staled(self):
        value = case("fixed-version-immutable")
        live = self.run_case(value)
        self.assertEqual(("passed", "rejected"), (live["status"], live["actualOutcome"]), live)
        self.assertTrue(any(_diagnostic_matches(d, value["expect"]["diagnostic"])
                            for d in live["actualDiagnostics"]))
        # A complete receipt captured from the previous real native bridge is
        # historical evidence, never a substitute for this head's live result.
        receipt = json.loads((ROOT / "tests" / "fixtures" /
                              "rule_case_generic_immutable_receipt.json").read_text(encoding="utf-8"))
        saved = deepcopy(receipt)
        encoded = json.dumps(receipt, ensure_ascii=False, sort_keys=True,
                             separators=(",", ":"), allow_nan=False).encode("utf-8")
        self.assertEqual("4ce979de844171ac995c2c71d37d0958416ce6255f95f1a0c5bd9bb305662493",
                         hashlib.sha256(encoded).hexdigest())
        self.assertEqual(("blocked", "diagnostic-unavailable"), (receipt["status"], receipt["reason"]))
        self.assertEqual("rejected", receipt["actualOutcome"])
        self.assertEqual(value["expect"], receipt["authorExpected"])
        generic = [d for d in receipt["actualDiagnostics"] if d.get("code") == "ASSEMBLY_INVALID"]
        self.assertEqual(1, len(generic))
        self.assertEqual("I40/I41", generic[0]["clause"])
        self.assertNotIn("ref", generic[0])
        self.assertFalse(any(_diagnostic_matches(d, value["expect"]["diagnostic"])
                             for d in receipt["actualDiagnostics"]))
        observed = receipt["observations"]
        self.assertEqual(observed["before"], observed["after"])
        self.assertEqual(observed["beforeRevision"], observed["afterRevision"])
        self.assertEqual(observed["beforeDumpHash"], observed["afterDumpHash"])
        self.assertTrue(all(a["passed"] for a in receipt["assertionResults"]))
        refreshed = refresh_receipt(receipt, value, self.identity, generation=4)
        self.assertEqual("stale", refreshed["status"])
        self.assertIn("runtime", refreshed["staleReasons"])
        self.assertEqual("blocked", refreshed["recordedStatus"])
        self.assertEqual("rejected", refreshed["actualOutcome"])
        self.assertEqual(receipt["actualDiagnostics"], refreshed["actualDiagnostics"])
        self.assertEqual("blocked", receipt["status"])
        self.assertEqual(receipt["context"], refreshed["context"])
        self.assertEqual(observed, refreshed["observations"])
        self.assertEqual(saved, receipt)
        claimed = deepcopy(receipt)
        claimed["status"] = "passed"
        with self.assertRaisesRegex(ReceiptValidationError, "exact rejection evidence"):
            refresh_receipt(claimed, value, self.identity)

    def test_all_statuses_reject_malformed_retained_context_before_scope_refresh(self):
        statuses = ("not-run", "missing-capability", "blocked", "timeout", "crashed",
                    "failed", "passed", "stale", "unknown-runtime")
        contexts = ([], None, "malformed", 0, True, {}, {"projectId": "receipt-project"},
                    {"generation": 7}, {"projectId": [], "generation": 7},
                    {"projectId": "", "generation": 7}, {"projectId": "x" * 129, "generation": 7},
                    {"projectId": "界" * 43, "generation": 7},
                    {"projectId": "receipt-project", "generation": None},
                    {"projectId": "receipt-project", "generation": True},
                    {"projectId": "receipt-project", "generation": 7.0},
                    {"projectId": "receipt-project", "generation": -1},
                    {"projectId": "receipt-project", "generation": 2**53})
        for status in statuses:
            for context in contexts:
                receipt = deepcopy(self.receipt)
                receipt.update(status=status, context=context)
                with self.subTest(status=status, context=context), self.assertRaisesRegex(
                        ReceiptValidationError, "project context"):
                    refresh_receipt(receipt, self.definition, self.identity,
                                    project_id="receipt-project", generation=7)

    def test_nonpass_missing_or_malformed_context_rejects_without_scope_arguments(self):
        for context in (None, [], "malformed", {}):
            receipt = deepcopy(self.receipt)
            receipt.update(status="blocked", context=context)
            with self.subTest(context=context), self.assertRaisesRegex(
                    ReceiptValidationError, "project context"):
                refresh_receipt(receipt, self.definition, self.identity)
        receipt = deepcopy(self.receipt)
        receipt["status"] = "blocked"
        del receipt["context"]
        with self.assertRaisesRegex(ReceiptValidationError, "project context"):
            refresh_receipt(receipt, self.definition, self.identity)

    def test_nonpass_rejects_malformed_freshness_fields_before_early_return(self):
        controls = [(("caseId",), None), (("caseId",), []), (("caseId",), "x" * 65),
                    (("caseId",), "case with spaces"), (("definitionHash",), None),
                    (("sourceHash",), []), (("definitionHash",), "F" * 64),
                    (("executor",), None), (("executor",), []), (("executor",), "runtime"),
                    (("executor", "known"), None), (("executor", "known"), 1),
                    (("executor", "nativeBinaryHash"), "not-a-hash"),
                    (("staleReasons",), None), (("staleReasons",), "generation"),
                    (("staleReasons",), []), (("staleReasons",), [1]),
                    (("staleReasons",), ["unknown-reason"])]
        for path, value in controls:
            receipt = deepcopy(self.receipt)
            receipt["status"] = "blocked"
            parent = receipt
            for selector in path[:-1]:
                parent = parent[selector]
            parent[path[-1]] = value
            with self.subTest(field=path), self.assertRaises(ReceiptValidationError):
                refresh_receipt(receipt, self.definition, self.identity)
        for key in ("caseId", "definitionHash", "sourceHash", "executor"):
            receipt = deepcopy(self.receipt)
            receipt["status"] = "blocked"
            del receipt[key]
            with self.subTest(missing=key), self.assertRaises(ReceiptValidationError):
                refresh_receipt(receipt, self.definition, self.identity)
        for key in ("recordedStatus", "staleReasons"):
            receipt = deepcopy(self.receipt)
            receipt.update(status="stale", recordedStatus="blocked", staleReasons=["generation"])
            del receipt[key]
            with self.subTest(missing_stale=key), self.assertRaises(ReceiptValidationError):
                refresh_receipt(receipt, self.definition, self.identity)

    def test_matching_nonpass_and_stale_history_are_never_promoted(self):
        for status in ("not-run", "missing-capability", "blocked", "timeout", "crashed", "failed", "stale"):
            receipt = deepcopy(self.receipt)
            receipt["status"] = status
            if status == "stale":
                receipt.update(recordedStatus="blocked", staleReasons=["generation"])
            saved = deepcopy(receipt)
            matching = refresh_receipt(receipt, self.definition, self.identity,
                                       project_id="receipt-project", generation=7)
            changed = refresh_receipt(receipt, self.definition, self.identity,
                                      project_id="other-project", generation=8)
            again = refresh_receipt(changed, self.definition, self.identity,
                                    project_id="other-project", generation=8)
            with self.subTest(status=status):
                self.assertEqual(saved, receipt)
                self.assertEqual(saved, matching)
                self.assertEqual("stale", changed["status"])
                self.assertEqual("blocked" if status == "stale" else status, changed["recordedStatus"])
                self.assertEqual(changed, again)
                self.assertEqual(saved["context"], changed["context"])

    def test_unknown_runtime_nonpass_keeps_its_well_formed_scope_without_hashes(self):
        receipt = NativeExecutor("/unavailable-retained-receipt-test-binary").run(
            self.definition, project_id="receipt-project", generation=7)
        self.assertEqual("unknown-runtime", receipt["status"])
        refreshed = refresh_receipt(receipt, self.definition, receipt["executor"],
                                    project_id="receipt-project", generation=7)
        self.assertEqual("stale", refreshed["status"])
        self.assertEqual("unknown-runtime", refreshed["recordedStatus"])
        self.assertEqual(["unknown-runtime"], refreshed["staleReasons"])
        self.assertEqual(receipt["context"], refreshed["context"])
        self.assertFalse(refreshed["executor"]["known"])

    def test_minimal_matching_green_claim_lacks_required_native_evidence(self):
        claimed = {"status": "passed", "caseId": self.definition["caseId"],
                   "definitionHash": definition_hash(self.definition),
                   "sourceHash": digest(self.definition["sourcePins"]),
                   "executor": deepcopy(self.identity)}
        with self.assertRaises(ReceiptValidationError):
            refresh_receipt(claimed, self.definition, self.identity)

    def test_green_receipt_rejects_each_missing_native_evidence_field(self):
        paths = [(key,) for key in ("actualOutcome", "actualDiagnostics", "authorExpected",
                                    "observations", "conditions", "executor", "assertionResults")]
        paths += [("authorExpected", key) for key in ("outcome", "diagnostic")]
        paths += [("conditions", key) for key in ("isolated", "privateDirectoryRemoved", "nativePid")]
        paths += [("executor", key) for key in ("known", "nativeBinaryHash", "nativeSourceHash",
                                                "validatorVersion", "axiomHash", "assertionSchemaHash")]
        paths += [("observations", key) for key in ("before", "after", "beforeRevision", "afterRevision",
                                                    "beforeDumpHash", "afterDumpHash")]
        paths += [("assertionResults", 0, key) for key in ("kind", "passed", "predicate")]
        for path in paths:
            changed = deepcopy(self.receipt)
            parent = changed
            for selector in path[:-1]:
                parent = parent[selector]
            del parent[path[-1]]
            with self.subTest(missing=path), self.assertRaises(ReceiptValidationError):
                refresh_receipt(changed, self.definition, self.identity)

    def test_green_receipt_rejects_wrong_outcome_flags_and_evidence_types(self):
        controls = [(("actualOutcome",), "rejected"), (("actualDiagnostics",), {}),
                    (("status",), []), (("recordedStatus",), []),
                    (("conditions", "isolated"), 1), (("conditions", "privateDirectoryRemoved"), False),
                    (("conditions", "nativePid"), True), (("conditions", "nativePid"), 0),
                    (("executor", "known"), 1), (("executor", "nativeBinaryHash"), "G" * 64),
                    (("observations", "before"), []), (("observations", "after"), None),
                    (("observations", "beforeRevision"), True), (("observations", "afterRevision"), -1),
                    (("observations", "beforeDumpHash"), "not-a-hash"),
                    (("observations", "afterDumpHash"), "F" * 64), (("assertionResults",), {}),
                    (("assertionResults",), [])]
        for path, value in controls:
            changed = deepcopy(self.receipt)
            parent = changed
            for selector in path[:-1]:
                parent = parent[selector]
            parent[path[-1]] = value
            with self.subTest(field=path, value=value), self.assertRaises(ReceiptValidationError):
                refresh_receipt(changed, self.definition, self.identity)

    def test_green_assertions_are_recomputed_and_must_match_exact_case_contract(self):
        controls = []
        false_assertion = deepcopy(self.receipt)
        false_assertion["assertionResults"][0]["passed"] = False
        controls.append(false_assertion)
        false_native_observation = deepcopy(self.receipt)
        false_native_observation["observations"]["after"]["rules"] = []
        controls.append(false_native_observation)
        changed_predicate = deepcopy(self.receipt)
        changed_predicate["assertionResults"][1]["predicate"]["slotId"] = 13
        controls.append(changed_predicate)
        missing_true_predicates = deepcopy(self.receipt)
        missing_true_predicates["assertionResults"] = missing_true_predicates["assertionResults"][:1]
        controls.append(missing_true_predicates)
        mismatched_kind = deepcopy(self.receipt)
        mismatched_kind["assertionResults"][0]["kind"] = "member_slot"
        controls.append(mismatched_kind)
        changed_unasserted_definition = deepcopy(self.receipt)
        changed_unasserted_definition["observations"]["after"]["rules"][0]["value"]["name"] = "altered receipt source"
        controls.append(changed_unasserted_definition)
        for index, changed in enumerate(controls):
            with self.subTest(control=index), self.assertRaises(ReceiptValidationError):
                refresh_receipt(changed, self.definition, self.identity)

    def test_receipt_json_guard_rejects_cycles_depth_size_and_non_json_values(self):
        controls = [set(), (), b"bytes", object(), float("nan"), float("inf"), 2**80, "\ud800",
                    "x" * (MAX_RECEIPT_BYTES + 1)]
        nested = []
        for _ in range(40):
            nested = [nested]
        controls.append(nested)
        cycle = {}
        cycle["self"] = cycle
        controls.append(cycle)
        controls.append([None] * 65536)
        for index, value in enumerate(controls):
            changed = deepcopy(self.receipt)
            changed["syntheticMalformedPayload"] = value
            with self.subTest(control=index), self.assertRaises(ReceiptValidationError):
                refresh_receipt(changed, self.definition, self.identity)

    def test_valid_old_green_evidence_remains_stale_under_a_changed_current_oracle(self):
        changed_definition = deepcopy(self.definition)
        changed_definition["assertions"][1]["slotId"] = 13
        retained = refresh_receipt(self.receipt, changed_definition, self.identity)
        again = refresh_receipt(retained, changed_definition, self.identity)
        self.assertEqual("stale", again["status"])
        self.assertEqual("passed", again["recordedStatus"])
        self.assertEqual(["definition"], again["staleReasons"])
        for field in ("executor", "authorExpected", "actualOutcome", "actualDiagnostics", "observations", "assertionResults"):
            self.assertEqual(self.receipt[field], again[field])
        self.assertEqual("passed", self.receipt["status"])

    def test_stale_historical_green_evidence_still_rejects_false_assertion(self):
        changed_definition = deepcopy(self.definition)
        changed_definition["label"] += " changed"
        retained = refresh_receipt(self.receipt, changed_definition, self.identity)
        retained["assertionResults"][0]["passed"] = False
        with self.assertRaises(ReceiptValidationError):
            refresh_receipt(retained, changed_definition, self.identity)

    def test_generic_or_wrong_typed_diagnostics_cannot_promote_native_negative_to_green(self):
        value = case("fixed-version-immutable")
        receipt = self.run_case(value)
        expected = value["expect"]["diagnostic"]
        self.assertEqual(("passed", "rejected"), (receipt["status"], receipt["actualOutcome"]), receipt)
        self.assertTrue(any(_diagnostic_matches(d, expected) for d in receipt["actualDiagnostics"]))
        alternatives = [[{"code": "ASSEMBLY_INVALID", "clause": "I40/I41",
                          "message": "D32: published rule 17@1 is immutable"}],
                        [{"code": "RULE_VERSION_IMMUTABLE", "clause": "D32",
                          "message": "rule 17 version 1"}]]
        for key, replacement in (("code", "OTHER_REJECTION"), ("clause", "I40"),
                                 ("ref", {"kind": "rule", "id": 17, "version": 2})):
            diagnostic = deepcopy(expected)
            diagnostic[key] = replacement
            alternatives.append([diagnostic])
        for diagnostics in alternatives:
            self.assertFalse(any(_diagnostic_matches(d, expected) for d in diagnostics))
            claimed = deepcopy(receipt)
            claimed["status"] = "passed"
            claimed["actualDiagnostics"] = diagnostics
            with self.subTest(diagnostics=diagnostics), self.assertRaisesRegex(
                    ReceiptValidationError, "exact rejection evidence"):
                refresh_receipt(claimed, value, receipt["executor"])


class TypedDiagnosticControls(unittest.TestCase):
    def test_literal_refs_require_exact_json_types_and_keys(self):
        expected = {"code": "RULE_VERSION_IMMUTABLE", "clause": "D32",
                    "ref": {"kind": "rule", "id": 17, "version": 1}}
        for ref in ({"kind": "rule", "id": 17, "version": True},
                    {"kind": "rule", "id": 17, "version": 1.0},
                    {"kind": "rule", "id": 17, "version": 1, "fieldId": 9}):
            actual = {"code": "RULE_VERSION_IMMUTABLE", "clause": "D32", "ref": ref}
            with self.subTest(ref=ref):
                self.assertFalse(_diagnostic_matches(actual, expected))
        string_expected = {"code": "MATERIAL_DIMENSION", "clause": "D33",
                           "ref": {"kind": "material", "id": "pine", "version": 1}}
        string_actual = {"code": "MATERIAL_DIMENSION", "clause": "D33",
                         "ref": {"version": 1, "id": "pine", "kind": "material"}}
        self.assertTrue(_diagnostic_matches(string_actual, string_expected))

    def test_only_exact_typed_diagnostic_fields_match_human_text_never_does(self):
        expected = case("fixed-version-immutable")["expect"]["diagnostic"]
        exact = dict(deepcopy(expected), message="Human wording can change")
        self.assertTrue(_diagnostic_matches(exact, expected))
        controls = [{"code": "ASSEMBLY_INVALID", "clause": "I40/I41", "message": str(expected)},
                    {"code": expected["code"], "clause": expected["clause"], "message": str(expected["ref"])},
                    dict(exact, ref={"kind": "rule", "id": 17, "version": 2}),
                    dict(exact, clause="I40"), dict(exact, code="UNRELATED_ERROR")]
        for actual in controls:
            with self.subTest(actual=actual):
                self.assertFalse(_diagnostic_matches(actual, expected))


SYNTHETIC_BOUNDARY_C = r'''
#include <signal.h>
#include <stdio.h>
#include <string.h>
#ifdef _WIN32
#include <windows.h>
static void hang(void) { for (;;) Sleep(1000); }
#else
#include <sys/types.h>
#include <unistd.h>
static void hang(void) { for (;;) pause(); }
#endif
int main(void) {
    char line[80];
    if (!fgets(line, sizeof line, stdin)) return 0;
    if (!strncmp(line, "hang", 4)) hang();
    if (!strncmp(line, "crash", 5)) { raise(SIGSEGV); return 99; }
    if (!strncmp(line, "exit", 4)) return 7;
    if (!strncmp(line, "invalid", 7)) { puts("not json"); fflush(stdout); hang(); }
    if (!strncmp(line, "nonobject", 9)) { puts("[]"); fflush(stdout); hang(); }
    if (!strncmp(line, "extra", 5)) {
        puts("{\"ok\":true}"); puts("{\"ok\":true}"); fflush(stdout); return 0;
    }
    if (!strncmp(line, "final-", 6)) {
        puts("{\"ok\":true}"); fflush(stdout);
        while (getchar() != EOF) { }
        if (!strncmp(line, "final-crash", 11)) { raise(SIGSEGV); return 99; }
        if (!strncmp(line, "final-cap", 9)) {
            for (int i = 0; i < 4096; ++i) fputc('x', stdout);
            fflush(stdout);
        }
        hang();
    }
    if (!strncmp(line, "stdout-cap", 10) || !strncmp(line, "stderr-cap", 10)) {
        FILE *out = line[3] == 'o' ? stdout : stderr;
        for (int i = 0; i < 4096; ++i) fputc('x', out);
        fflush(out); hang();
    }
#ifndef _WIN32
    if (!strncmp(line, "orphan", 6)) {
        pid_t child = fork();
        if (child < 0) return 8;
        if (!child) hang();
        printf("{\"ok\":true,\"descendantPid\":%ld}\n", (long)child);
        fflush(stdout); return 0;
    }
#endif
    puts("{\"ok\":true}"); fflush(stdout); return 0;
}
'''


class SyntheticNativeFailureBoundaries(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        compiler = shutil.which(os.environ.get("CC", "cc"))
        if not compiler:
            raise unittest.SkipTest("Synthetic boundary controls require a C compiler")
        cls.temp = tempfile.TemporaryDirectory(prefix="rule-case-boundary-")
        cls.addClassCleanup(cls.temp.cleanup)
        cls.directory = Path(cls.temp.name)
        source = cls.directory / "boundary.c"
        source.write_text(SYNTHETIC_BOUNDARY_C, encoding="utf-8")
        cls.binary = cls.directory / ("boundary.exe" if os.name == "nt" else "boundary")
        compiled = subprocess.run([compiler, "-std=c11", "-O2", str(source), "-o", str(cls.binary)],
                                  capture_output=True, text=True, timeout=30)
        if compiled.returncode:
            raise AssertionError("Synthetic control compile failed: " + compiled.stderr)

    def child(self, *, seconds=2, cancel=None, cap=4096):
        child = _Child(self.binary, self.directory, time.monotonic() + seconds, cancel, cap)
        self.addCleanup(child.stop)
        return child

    def test_timeout_and_active_cancellation_are_nonpass_and_bounded(self):
        child = self.child(seconds=.1)
        started = time.monotonic()
        with self.assertRaises(_Stop) as timeout:
            child.command("hang")
        self.assertEqual(("timeout", "wall-time-limit"), (timeout.exception.status, timeout.exception.reason))
        self.assertLess(time.monotonic() - started, 1)
        event = threading.Event()
        child = self.child(cancel=event)
        timer = threading.Timer(.05, event.set)
        self.addCleanup(timer.cancel)
        timer.start()
        with self.assertRaises(_Stop) as cancelled:
            child.command("hang")
        self.assertEqual(("blocked", "cancelled"), (cancelled.exception.status, cancelled.exception.reason))

    def test_crash_and_nonzero_exit_never_supply_a_success_reply(self):
        for command, expected in (("crash", "crashed"), ("exit", "failed")):
            with self.subTest(control=command):
                child = self.child()
                with self.assertRaises(_Stop) as stopped:
                    child.command(command)
                self.assertEqual(expected, stopped.exception.status)
                self.assertTrue(stopped.exception.reason.startswith("native-exit:"))

    def test_stdout_and_stderr_share_a_total_output_cap(self):
        for command in ("stdout-cap", "stderr-cap"):
            with self.subTest(control=command):
                child = self.child(cap=64)
                with self.assertRaises(_Stop) as stopped:
                    child.command(command)
                self.assertEqual(("blocked", "output-capacity"), (stopped.exception.status, stopped.exception.reason))
                self.assertLessEqual(len(child.stderr), 4096)

    def test_invalid_json_and_nonobject_protocol_values_fail_closed(self):
        for command, reason in (("invalid", "invalid-native-json"), ("nonobject", "invalid-native-response")):
            with self.subTest(control=command):
                child = self.child()
                with self.assertRaises(_Stop) as stopped:
                    child.command(command)
                self.assertEqual(("failed", reason), (stopped.exception.status, stopped.exception.reason))

    def test_clean_final_native_exit_is_required_after_a_valid_reply(self):
        child = self.child()
        self.assertEqual({"ok": True}, child.command("ok"))
        child.finish()
        for command, status in (("final-crash", "crashed"), ("final-cap", "blocked")):
            with self.subTest(control=command):
                child = self.child(cap=64)
                self.assertEqual({"ok": True}, child.command(command))
                with self.assertRaises(_Stop) as stopped:
                    child.finish()
                self.assertEqual(status, stopped.exception.status)

    def test_unsolicited_extra_reply_cannot_be_accepted_at_finish(self):
        child = self.child()
        self.assertEqual({"ok": True}, child.command("extra"))
        with self.assertRaises(_Stop) as stopped:
            child.finish()
        self.assertEqual("failed", stopped.exception.status)
        self.assertEqual("unsolicited-native-response", stopped.exception.reason)

    def test_late_cancellation_interrupts_final_exit_wait(self):
        event = threading.Event()
        child = self.child(cancel=event, seconds=1)
        self.assertEqual({"ok": True}, child.command("final-hang"))
        timer = threading.Timer(.05, event.set)
        self.addCleanup(timer.cancel)
        timer.start()
        started = time.monotonic()
        with self.assertRaises(_Stop) as stopped:
            child.finish()
        self.assertEqual(("blocked", "cancelled"), (stopped.exception.status, stopped.exception.reason))
        self.assertLess(time.monotonic() - started, .5)

    @unittest.skipIf(os.name == "nt", "POSIX process group cleanup control")
    def test_exited_leader_cannot_leave_descendants_or_unbounded_pipe_cleanup(self):
        child = self.child()
        response = child.command("orphan")
        descendant = response["descendantPid"]
        child.process.wait(timeout=1)
        errors = []

        def cleanup():
            try:
                child.stop()
            except Exception as error:
                errors.append(error)

        cleaner = threading.Thread(target=cleanup, daemon=True)
        cleaner.start()
        cleaner.join(timeout=2)
        blocked = cleaner.is_alive()
        if blocked:
            # Even a regression leaves this test bounded and removes its child.
            try:
                os.killpg(child.process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            cleaner.join(timeout=2)
        self.assertFalse(blocked, "stop blocked after an exited leader left pipe-owning descendants")
        self.assertEqual([], errors)
        status = Path("/proc") / str(descendant) / "stat"
        deadline = time.monotonic() + .5
        while status.exists():
            state = status.read_text().rsplit(") ", 1)[1].split()[0]
            if state == "Z":
                break
            self.assertLess(time.monotonic(), deadline, "A pipe-owning descendant is still running")
            time.sleep(.01)


if __name__ == "__main__":
    unittest.main()
