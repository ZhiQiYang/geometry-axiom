"""R461 R3: native D1 drafts, independent R57 oracle and existing K3 judge.

When only T is applied, ExistingF1b below exposes the actual existing producer
result without inventing v2 audit fields. Thus red assertions concern missing
old-record witnesses, history facts, frames or guards after real F1b succeeds;
they are not import failures. Only the exhaustive test explicitly reports the
absence of a third (Python) judge, after checking JS against the oracle.
"""
from copy import deepcopy
import hashlib
import importlib
import importlib.util
import json
import os
from pathlib import Path
import secrets
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
for directory in (ROOT, ROOT / "geometry-core", ROOT / "geometry-web"):
    if str(directory) not in sys.path:
        sys.path.insert(0, str(directory))

from tests import _bridge, binaries
from tests.oracles import r09b_source_reassociation as oracle
from modeling import ModelError, canonical_bytes
from modeling.base import load_base
import model_update
import space_modeling


SCENE = ("surface 0 origin 0 0 0 u +x v +y rect 0 0 4000 3000\n"
         "surface 1 origin 0 0 0 u +x v +y rect 0 0 4000 3000\n"
         "surface 2 origin 0 0 0 u +x v +z rect 0 0 4000 2000\n")
PROJECT = "r09b-project"
CARRIERS = ["draft-face-west", "draft-cap-north"]
AUTHORITY = {"project": "caller-asserted", "history": "unverified", "confirmation": False,
             "carrierIds": "caller-provisional"}


def raw_record(record):
    # A byte witness must preserve this noncanonical whitespace and final LF.
    return (json.dumps(record, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


def js_judge(cases):
    if any(case["same_project"] is not True for case in cases):
        raise AssertionError("R09B_JS_SHARED_DOMAIN_ONLY")
    script = """const fs=require('fs');
const ledger=require(process.argv[1]);
const cases=JSON.parse(fs.readFileSync(0,'utf8'));
process.stdout.write(JSON.stringify(cases.map(c=>ledger.judgeRoots(c.identity,c.graph))));
"""
    completed = subprocess.run(["node", "-e", script, str(ROOT / "geometry-web/identity-ledger.js")],
                               input=json.dumps(cases), capture_output=True, text=True, timeout=60)
    if completed.returncode:
        raise AssertionError("R09B_EXISTING_K3_JUDGE_EXECUTION: " + completed.stderr)
    return json.loads(completed.stdout)


def native_view(scene, bridge):
    with tempfile.TemporaryDirectory(prefix="r09b-read-") as directory:
        source = Path(directory) / "source.scene"
        source.write_text(scene, encoding="utf-8", newline="\n")
        with _bridge.BridgeSession(bridge, cwd=directory) as child:
            graph = child.command("source-inspect-file " + str(source))
            loaded = child.command("loadfile " + str(source))
            if graph.get("ok") is not True or loaded.get("ok") is not True:
                raise ModelError("INVALID", "R09B_NATIVE_SOURCE_INVALID", "I70", "原生來源讀取拒絕。")
            bare = child.command("dump-deidentified")
    assert bare.get("ok") is True, "R09B_NATIVE_DEIDENTIFIED"
    return {"data": {"identityLedger": graph["identityLedger"]},
            "nodes": {item["key"]: item for item in graph["nodes"]}}, bare["text"]


class ExistingF1b:
    """T-only baseline adapter; never fabricates the new draft guarantees."""
    @staticmethod
    def capabilities():
        import modeling
        return {"exchangeCapabilities": list(modeling.CAPABILITIES)}

    @staticmethod
    def inspect(record_raw, source_scene, *, project_id, record_project_id=None,
                base_executable=None, bridge_executable=None):
        record = json.loads(record_raw)
        graph, _ = native_view(source_scene, bridge_executable)
        identity = record.get("sourceIdentity", {"schema": "model-source-identity/1", "roots": [
            {"role": "use", "kind": "placement", "id": use["placement_id"], "incarnation": None}
            for use in record["input"]["uses"]]})
        rows = js_judge([{"identity": identity, "graph": graph, "same_project": True}])[0]
        if project_id != record_project_id:
            # Caller scope is outside judgeRoots. This adapter exposes that
            # distinction; it never changes graph.active to manufacture a JS
            # comparison that the existing function cannot itself express.
            rows = [dict(row, status="unknown", confirmed=False) for row in rows]
        return {"comparison": rows}

    @staticmethod
    def prepare_candidate(record_raw, source_scene, selection, *, project_id, carrier_ids,
                          record_project_id=None, base_executable=None, bridge_executable=None):
        _, bare = native_view(source_scene, bridge_executable)
        return model_update.prepare_update({"record": json.loads(record_raw), "current_scene": bare,
            "selection": {"mode": "faces", "uses": [{"placement_id": row["placement_id"]} for row in selection],
                          "obstacles": []}}, base_executable=base_executable, bridge_executable=bridge_executable)

    @staticmethod
    def validate_candidate(candidate, record_raw, source_scene, *, project_id, record_project_id=None,
                           base_executable=None, bridge_executable=None):
        # Existing F1b proves geometry replay, but does not claim a v2 audit.
        space_modeling.replay_stored(candidate["record"]["input"], candidate["record"]["result"],
                                     base_executable=base_executable)
        return True


def product_or_baseline():
    if importlib.util.find_spec("source_reassociation") is None:
        return ExistingF1b
    return importlib.import_module("source_reassociation")


class IndependentOracle(unittest.TestCase):
    def trace(self, events, seed=None):
        trace = oracle.run_sequence(events, seed)
        self.assertTrue(oracle.check_trace(trace))
        self.assertEqual(trace, oracle.run_sequence(events, seed), "R09B_ORACLE_DETERMINISTIC")
        return trace

    def test_00_typed_zero_incomplete_and_uncovered_are_distinct(self):
        source = oracle.initial()["source"]
        pin = oracle.initial()["binding"]
        self.assertEqual(oracle.classify(pin, source), "continuous")
        self.assertEqual(oracle.key({"kind": "column", "id": 0}), ("column", 0))
        self.assertNotEqual(oracle.key({"kind": "column", "id": 0}), oracle.key({"kind": "beam", "id": 0}))
        self.assertEqual(oracle.key({"kind": "parameter-field", "id": 0, "fieldId": 0}), ("parameter-field", 0, 0))
        for changed in (dict(source, complete=False), dict(source, objects=source["objects"] * 2)):
            with self.assertRaises(oracle.OracleError, msg="R09B_ORACLE_OPERATION_FAILURE_NOT_ABSENT"):
                oracle.classify(pin, changed)
        for identity in (-1, True, 2**32):
            with self.assertRaises(oracle.OracleError):
                oracle.key({"kind": "placement", "id": identity})
        owned = {"project": "p", "enabled": True, "complete": True,
                 "objects": [{"kind": "timber", "id": 0, "token": None, "covered": False}]}
        old = {"project": "p", "kind": "timber", "id": 0, "token": oracle.EPOCH + ":1"}
        self.assertEqual(oracle.classify(old, owned), "absent", "R09B_R57_UNCOVERED_ABSENT")

    def test_01_rename_and_return_keep_reference_and_geometry_snapshot(self):
        rows = self.trace([{"op": "rename", "name": "renamed"}, {"op": "rename", "name": "original"}])
        self.assertEqual([row["status"] for row in rows], ["continuous", "continuous"])
        self.assertEqual(rows[-1]["after"], oracle.initial(), "R09B_SOURCE_ABA_CONTENT_EQUAL")
        self.assertEqual(rows[-1]["generation"], 2)

    def test_02_preview_aba_and_undo_redo_never_revive_confirmation(self):
        for middle in ([{"op": "rename", "name": "renamed"}, {"op": "rename", "name": "original"}],
                       [{"op": "resize", "size": 2}, {"op": "undo"}, {"op": "redo"}, {"op": "undo"}],
                       [{"op": "branch"}]):
            with self.subTest(middle=middle):
                rows = self.trace([{"op": "preview", "id": 0}, *middle, {"op": "confirm"}])
                self.assertEqual(rows[-1]["outcome"], "I76_STALE", "R09B_SPEC_ABA_STAYS_STALE")
                self.assertEqual(rows[-1]["before"], rows[-1]["after"])

    def test_03_activation_is_separate_from_cancel_and_old_unknown(self):
        rows = self.trace([{"op": "load-inactive"}, {"op": "preview", "id": 0}, {"op": "activate"},
                           {"op": "confirm"}, {"op": "cancel"}])
        self.assertEqual(rows[-2]["outcome"], "I76_STALE")
        self.assertTrue(rows[-1]["after"]["source"]["enabled"], "R09B_CANCEL_DOES_NOT_UNDO_ACTIVATION")
        seed = oracle.initial()
        seed["binding"]["token"] = None
        observed = self.trace([{"op": "load-inactive"}, {"op": "activate"}], seed)
        self.assertEqual(observed[-1]["status"], "unknown", "R09B_ACTIVATE_NO_HISTORICAL_BACKFILL")

    def test_04_clear_load_and_same_project_branch_are_distinct(self):
        cleared = self.trace([{"op": "clear"}])[-1]
        loaded = self.trace([{"op": "load-inactive"}])[-1]
        branch = self.trace([{"op": "branch"}])[-1]
        self.assertEqual((cleared["status"], cleared["outcome"]), ("absent", "source-committed"))
        self.assertTrue(cleared["after"]["source"]["enabled"])
        self.assertEqual(cleared["allocation_epoch"], oracle.EPOCH)
        self.assertEqual((loaded["status"], loaded["outcome"]), ("unknown", "world-replaced"))
        self.assertIsNone(loaded["allocation_epoch"])
        self.assertEqual(branch["status"], "continuous")
        self.assertEqual(branch["before"], branch["after"])
        self.assertEqual(branch["generation"], 1)

    def test_05_old_trail_returns_continuous_without_rebinding_current(self):
        prefix = [{"op": "replace", "id": 0}, {"op": "preview", "id": 0}, {"op": "confirm"},
                  {"op": "load-original"}]
        rows = self.trace(prefix)
        current = rows[-1]["after"]
        self.assertEqual(rows[-1]["status"], "replaced", "R09B_CURRENT_PIN_STAYS_NEW")
        self.assertEqual(oracle.classify(current["receipts"][0]["old"], current["source"]), "continuous")
        self.assertEqual(current["receipts"][0]["old_status"], "replaced", "R09B_OLD_FACT_NOT_REWRITTEN")
        rebound = self.trace(prefix + [{"op": "preview", "id": 0}, {"op": "confirm"}])
        self.assertEqual(rebound[-1]["status"], "continuous")
        self.assertEqual(len(rebound[-1]["after"]["receipts"]), 2, "R09B_EXPLICIT_RETURN_ALLOWED")
        self.assertEqual(rebound[-1]["allocation_highwater"], rows[-1]["allocation_highwater"])

    def test_06_conflict_manual_decision_and_undo_before_creation(self):
        seed = oracle.initial()
        seed["binding"]["token"] = oracle.EPOCH + ":2"
        rows = self.trace([{"op": "preview", "id": 1}, {"op": "confirm"}], seed)
        self.assertEqual(rows[-1]["outcome"], "association-committed")
        self.assertEqual(rows[-1]["after"]["receipts"][0]["old_status"], "conflict")
        self.assertEqual(rows[-1]["before"]["source"], rows[-1]["after"]["source"])
        future_pin = oracle.initial()
        future_pin["binding"].update(id=2, token=oracle.EPOCH + ":3")
        restored = self.trace([{"op": "create", "id": 2}, {"op": "undo"}, {"op": "redo"}], future_pin)
        self.assertEqual([row["status"] for row in restored], ["continuous", "absent", "continuous"])

    def test_07_checker_controls_reject_named_corruption_and_restore(self):
        for name, marker in oracle.CONTROLS.items():
            with self.subTest(name=name):
                oracle.probe(name)
                with self.assertRaisesRegex(AssertionError, marker):
                    oracle.probe(name, corrupt=True)
                oracle.probe(name)

    def test_08_first_unknown_decision_is_recorded_then_same_decision_is_noop(self):
        seed = oracle.initial()
        seed["binding"]["token"] = None
        seed["source"]["enabled"] = False
        for obj in seed["source"]["objects"]:
            obj["token"] = None
        rows = self.trace([{"op": "preview"}, {"op": "confirm"}, {"op": "preview"}, {"op": "confirm"}], seed)
        self.assertEqual(rows[1]["outcome"], "association-committed", "R09B_ORACLE_FIRST_UNKNOWN_DECISION")
        self.assertEqual(len(rows[1]["after"]["receipts"]), 1)
        self.assertEqual(rows[-1]["outcome"], "no-op")
        self.assertEqual(len(rows[-1]["after"]["receipts"]), 1)

    def test_09_checker_rejects_invented_exact_new_target(self):
        rows = self.trace([{"op": "replace"}, {"op": "preview"}, {"op": "confirm"}])
        rows[-1]["after"]["binding"]["token"] = oracle.EPOCH + ":999"
        rows[-1]["after"]["receipts"][-1]["new"]["token"] = oracle.EPOCH + ":999"
        rows[-1]["status"] = "replaced"
        with self.assertRaisesRegex(AssertionError, "ORACLE_EXACT_NEW_TARGET", msg="R09B_ORACLE_INVENTED_NEW_TARGET"):
            oracle.check_trace(rows)

    def test_10_checker_rejects_stale_full_model_source(self):
        rows = self.trace([{"op": "resize", "size": 2}, {"op": "preview"}, {"op": "confirm"}])
        rows[-1]["after"]["model_source"] = deepcopy(rows[-1]["before"]["model_source"])
        with self.assertRaisesRegex(AssertionError, "ORACLE_FULL_MODEL_SOURCE", msg="R09B_ORACLE_STALE_FULL_MODEL"):
            oracle.check_trace(rows)

    def test_11_checker_rejects_forged_allocation_serial(self):
        rows = self.trace([{"op": "replace"}])
        rows[-1]["after"]["source"]["objects"][-1]["token"] = oracle.EPOCH + ":999"
        with self.assertRaisesRegex(AssertionError, "ORACLE_EXACT_ALLOCATED_MARK", msg="R09B_ORACLE_FALSE_ALLOCATION"):
            oracle.check_trace(rows)

    def test_12_checker_rejects_effective_receipt_on_source_only_change(self):
        rows = self.trace([{"op": "rename", "name": "renamed"}])
        state = rows[-1]["after"]
        state["receipts"].append({"old": deepcopy(state["binding"]), "new": deepcopy(state["binding"]),
                                   "source": deepcopy(state["source"]), "old_status": "continuous"})
        with self.assertRaisesRegex(AssertionError, "ORACLE_RECEIPT_ONLY_AFTER_CONFIRM", msg="R09B_ORACLE_UNCONFIRMED_RECEIPT"):
            oracle.check_trace(rows)

    def test_13_empty_world_activation_still_requires_configured_epoch(self):
        rows = self.trace([{"op": "load-inactive"}, {"op": "clear"}, {"op": "activate"}])
        self.assertTrue(rows[-1]["after"]["source"]["enabled"])
        self.assertIsNotNone(rows[-1]["allocation_epoch"], "R09B_ORACLE_EMPTY_ACTIVATION_NEEDS_EPOCH")
        self.assertEqual(rows[-1]["allocation_highwater"], 2)

    def test_14_checker_preserves_session_epoch_across_clear_and_history_restore(self):
        cases = (([{"op": "load-original"}], oracle.EPOCH),
                 ([{"op": "clear"}], None),
                 ([{"op": "load-original"}, {"op": "undo"}], oracle.EPOCH))
        for events, forged_epoch in cases:
            with self.subTest(events=events):
                rows = self.trace(events)
                rows[-1]["allocation_epoch"] = forged_epoch
                with self.assertRaisesRegex(AssertionError, "ORACLE_SESSION_EPOCH", msg="R09B_ORACLE_FALSE_EPOCH_TRANSITION"):
                    oracle.check_trace(rows)

    def test_15_fresh_epoch_cannot_reuse_seed_mark_prefix(self):
        seed = oracle.initial()
        old_epoch = "0" * 31 + "1"
        for obj in seed["source"]["objects"]:
            obj["token"] = old_epoch + obj["token"][32:]
        seed["binding"]["token"] = old_epoch + ":1"
        rows = self.trace([{"op": "branch"}, {"op": "replace"}], seed)
        self.assertNotEqual(rows[-1]["allocation_epoch"], old_epoch, "R09B_ORACLE_EPOCH_NOT_CURRENT_WORLD")

    def test_16_same_geometry_recreation_changes_identity_not_abstract_geometry(self):
        rows = self.trace([{"op": "replace"}, {"op": "preview"}, {"op": "confirm"}])
        self.assertEqual(rows[-1]["before"]["model_source"], rows[-1]["after"]["model_source"],
                         "R09B_ORACLE_SAME_GEOMETRY_DIFFERENT_IDENTITY")
        self.assertNotEqual(rows[-1]["before"]["binding"], rows[-1]["after"]["binding"])

    def test_17_nonconfirmation_cannot_claim_effective_association(self):
        rows = self.trace([{"op": "replace"}, {"op": "preview"}, {"op": "confirm"}])
        rows[-1]["event"] = {"op": "rename", "name": "forged"}
        try:
            oracle.check_trace(rows)
        except Exception as error:
            self.assertIsInstance(error, AssertionError, "R09B_ORACLE_NONCONFIRM_NAMED_REJECTION")
            self.assertIn("ORACLE_CONFIRM_ONLY", str(error), "R09B_ORACLE_NONCONFIRM_EXACT_REJECTION")
        else:
            self.fail("R09B_ORACLE_NONCONFIRM_COMMIT_ACCEPTED")


class SourceReassociation(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if os.name == "posix":
            import resource
            soft, hard = resource.getrlimit(resource.RLIMIT_STACK)
            wanted = 16 * 1024 * 1024
            if soft != resource.RLIM_INFINITY and soft < wanted:
                resource.setrlimit(resource.RLIMIT_STACK,
                    (min(wanted, hard) if hard != resource.RLIM_INFINITY else wanted, hard))
        programs = {}
        for name, variable in (("bridge", "GEOMETRY_TEST_BRIDGE"), ("model-base", "GEOMETRY_MODEL_BASE")):
            info = binaries.inspect_one(binaries.BY_NAME[name], path=os.environ.get(variable))
            if info.state != "fresh":
                raise RuntimeError("R09B_NATIVE_ENVIRONMENT " + name + ": " + info.reason)
            programs[name] = str(info.path)
        cls.bridge, cls.base = programs["bridge"], programs["model-base"]
        cls.native = {"base_executable": cls.base, "bridge_executable": cls.bridge}
        with tempfile.TemporaryDirectory(prefix="r09b-fixture-") as directory:
            path = Path(directory) / "fixture.scene"
            path.write_text(SCENE, encoding="utf-8", newline="\n")
            with _bridge.BridgeSession(cls.bridge, cwd=directory) as child:
                def command(text):
                    result = child.command(text)
                    if result.get("preview", {}).get("valid"):
                        result = child.command("line confirm " + str(result["preview"]["token"]))
                    if result.get("ok") is not True:
                        raise AssertionError(("R09B_REAL_NATIVE_FIXTURE", text, result))
                    return result
                command("loadfile " + str(path))
                cls.bare = command("dump")["text"]
                command("identity-epoch " + secrets.token_hex(16))
                command("line identity-ledger activate")
                cls.active = command("dump")["text"]
                cls.marks = command("identity-read")["marks"]
                command("line delete placement 0")
                cls.absent = command("dump")["text"]
                command("line surface 0 origin 0 0 0 u +x v +y rect 0 0 4000 3000")
                cls.replaced = command("dump")["text"]
                cls.replaced_marks = command("identity-read")["marks"]
                cls.replaced_bare = command("dump-deidentified")["text"]
                command("line surface 0 origin 500 0 0 u +y v -x rect 0 0 4000 3000")
                cls.rotated = command("dump")["text"]
                command("line delete placement 0")
                command("line delete placement 1")
                cls.no_target = command("dump")["text"]
        cls.conflict = cls.active.replace(cls.marker(0), "__SWAP__").replace(cls.marker(1), cls.marker(0)).replace("__SWAP__", cls.marker(1))
        inputs = {"mode": "faces", "base_scene": load_base(cls.bare, executable=cls.base)["base_scene"],
                  "uses": [{"placement_id": 0, "orientation": 1, "purpose": "boundary"},
                           {"placement_id": 2, "orientation": -1, "purpose": "calculation-cap"}], "obstacles": []}
        result = space_modeling.preview(inputs, base_executable=cls.base)
        cls.legacy = {"id": "r09b-model", "name": "R09b ordinary faces", "created_at": "2026-11-26T01:00:00.000Z",
                      "source": {"kind": "scene", "placement_id": None, "boundary_id": None, "scene_hash": result["source_sha256"]},
                      "input": inputs, "result": result}
        cls.identified = deepcopy(cls.legacy)
        cls.identified["sourceIdentity"] = {"schema": "model-source-identity/1", "roots": [
            {"role": "use", "kind": "placement", "id": use["placement_id"], "incarnation": cls.marker(use["placement_id"])}
            for use in inputs["uses"]]}
        cls.f1b = model_update.prepare_update({"record": deepcopy(cls.identified), "current_scene": cls.bare,
            "selection": {"mode": "faces", "uses": [{"placement_id": 0}, {"placement_id": 2}], "obstacles": []}}, **cls.native)
        cls.engine = product_or_baseline()
        cls.candidate_cache = {}

    @classmethod
    def marker(cls, identity, marks=None):
        return next(row["mark"] for row in (cls.marks if marks is None else marks)
                    if row["kind"] == "placement" and row["id"] == identity)

    def choices(self, identities=(1, 2), record=None):
        old = self.identified if record is None else record
        return [{"carrierId": label, "placement_id": identity, "orientation": use["orientation"], "purpose": use["purpose"]}
                for label, identity, use in zip(CARRIERS, identities, old["input"]["uses"])]

    def candidate(self, *, scene=None, record=None, identities=(1, 2), record_project=PROJECT, project=PROJECT):
        old = self.identified if record is None else record
        source = self.replaced if scene is None else scene
        encoded = raw_record(old)
        choices = self.choices(identities, old)
        cache_key = (encoded, source, canonical_bytes(choices), project, record_project)
        if cache_key not in self.candidate_cache:
            self.candidate_cache[cache_key] = self.engine.prepare_candidate(encoded, source, choices,
                project_id=project, record_project_id=record_project, carrier_ids=list(CARRIERS), **self.native)
        return deepcopy(self.candidate_cache[cache_key])

    def validate(self, candidate, *, scene=None, record=None, record_project=PROJECT, project=PROJECT):
        return self.engine.validate_candidate(candidate, raw_record(self.identified if record is None else record),
            self.replaced if scene is None else scene, project_id=project, record_project_id=record_project, **self.native)

    def test_00_original_f1b_and_real_native_fixture_already_pass(self):
        self.assertEqual(self.f1b["record"]["result"], self.legacy["result"], "R09B_REAL_F1B_BASELINE")
        self.assertIsNone(self.legacy["result"]["volume"])
        self.assertEqual(self.legacy["result"]["summary"]["face_count"], 2)
        self.assertCountEqual(self.bare.splitlines(), self.replaced_bare.splitlines())
        self.assertNotEqual(self.marker(0), self.marker(0, self.replaced_marks))

    def test_01_exhaustive_oracle_python_existing_k3_full_rows(self):
        cases = list(oracle.matrix_cases())
        before = canonical_bytes(cases)
        existing = js_judge(cases)
        expected = [oracle.judge_roots(case["identity"], case["graph"], same_project=case["same_project"]) for case in cases]
        self.assertEqual(existing, expected, "R09B_K3_ORACLE_FULL_ROWS")
        self.assertEqual(canonical_bytes(cases), before, "R09B_K3_AND_ORACLE_INPUT_UNCHANGED")
        self.assertTrue(hasattr(self.engine, "judge_roots"), "R09B_V2_PYTHON_JUDGE_PRESENT_AFTER_K3_ORACLE")
        actual = [self.engine.judge_roots(case["identity"], case["graph"], same_project=case["same_project"]) for case in cases]
        self.assertEqual(actual, expected, "R09B_THREE_WAY_FULL_ROWS")
        self.assertEqual(canonical_bytes(cases), before, "R09B_THREE_WAY_INPUT_UNCHANGED")
        self.assertEqual({row["status"] for rows in actual for row in rows}, set(oracle.STATES), "R09B_ALL_FIVE_STATES")
        print("R09B_THREE_WAY " + json.dumps({"cases": len(cases), "rows": sum(map(len, actual)),
            "sha256": hashlib.sha256(canonical_bytes(actual)).hexdigest()}, sort_keys=True))

    def test_02_native_statuses_and_content_comparison_are_separate(self):
        cases = ((self.active, "continuous"), (self.absent, "absent"), (self.replaced, "replaced"),
                 (self.conflict, "conflict"), (self.bare, "unknown"))
        for scene, status in cases:
            with self.subTest(status=status):
                old_raw = raw_record(self.identified)
                result = self.engine.inspect(old_raw, scene, project_id=PROJECT, record_project_id=PROJECT, **self.native)
                self.assertEqual(result["comparison"][0]["status"], status, "R09B_NATIVE_R57_" + status.upper())
                self.assertEqual(old_raw, raw_record(self.identified), "R09B_INSPECT_BYTES_UNCHANGED")
                self.assertEqual(result.get("beforeSha256"), hashlib.sha256(old_raw).hexdigest(), "R09B_INSPECTION_BINDS_OLD_BYTES")

    def test_03_legacy_unknown_keeps_exact_before_raw_and_no_backfill(self):
        candidate = self.candidate(record=self.legacy, record_project=None)
        self.assertEqual(candidate.get("beforeRaw"), raw_record(self.legacy).decode(), "R09B_V2_OLD_RECORD_WITNESS")
        self.assertNotIn("sourceIdentity", json.loads(candidate["beforeRaw"]))
        self.assertEqual(candidate["comparison"][0]["status"], "unknown")
        self.assertEqual(candidate["record"]["sourceIdentity"]["roots"][0]["id"], 1)
        self.assertIs(candidate["changed"], True, "R09B_NEW_DATA_DECISION_RECORDED")

    def test_04_absent_manual_target_rebuilds_all_rows_and_current_roots(self):
        candidate = self.candidate(scene=self.absent)
        self.assertEqual([row["placement_id"] for row in candidate["record"]["input"]["uses"]], [1, 2])
        self.assertEqual(candidate.get("comparison", [{}])[0].get("status"), "absent", "R09B_V2_ABSENT_FACT_RETAINED")
        roots = candidate["record"]["sourceIdentity"]["roots"]
        self.assertEqual([(row["id"], row["incarnation"]) for row in roots], [(1, self.marker(1)), (2, self.marker(2))])
        self.assertEqual(json.loads(candidate["beforeRaw"])["sourceIdentity"], self.identified["sourceIdentity"])
        self.assertTrue(self.validate(candidate, scene=self.absent))

    def test_05_equal_geometry_new_mark_never_rewrites_old_replaced_fact(self):
        candidate = self.candidate(identities=(0, 2))
        self.assertEqual(candidate.get("comparison", [{}])[0].get("status"), "replaced", "R09B_V2_MARK_BEATS_EQUAL_GEOMETRY")
        self.assertFalse(candidate["comparison"][0]["definitionChanged"])
        self.assertFalse(candidate["comparison"][0]["valueChanged"])
        self.assertEqual(candidate["record"]["sourceIdentity"]["roots"][0]["incarnation"], self.marker(0, self.replaced_marks))
        self.assertEqual(json.loads(candidate["beforeRaw"])["sourceIdentity"]["roots"][0]["incarnation"], self.marker(0))
        self.assertIs(candidate["changed"], True)

    def test_06_legal_world_conflict_allows_manual_draft_without_repairing_marks(self):
        candidate = self.candidate(scene=self.conflict)
        self.assertEqual(candidate.get("comparison", [{}])[0].get("status"), "conflict", "R09B_V2_CONFLICT_DIAGNOSTIC_RETAINED")
        self.assertEqual(candidate["source"]["scene"], self.conflict, "R09B_NO_MARK_REPAIR")
        self.assertEqual(candidate["currentReferences"][0]["pin"]["id"], 1)
        self.assertEqual(candidate["currentReferences"][0]["pin"]["incarnation"], self.marker(0))
        self.assertTrue(self.validate(candidate, scene=self.conflict))

    def test_07_inactive_source_preserves_unknown_new_reference_without_fabricated_mark(self):
        candidate = self.candidate(scene=self.bare, record=self.legacy, identities=(0, 2), record_project=None)
        expected = [{"carrierId": label, "pin": {"projectId": PROJECT, "kind": "placement", "id": identity, "incarnation": None},
                     "unknownReason": "ledger-inactive"} for label, identity in zip(CARRIERS, (0, 2))]
        self.assertEqual(candidate.get("currentReferences"), expected, "R09B_V2_INACTIVE_NO_FABRICATED_REFERENCE")
        self.assertNotIn("sourceIdentity", candidate["record"])
        self.assertEqual([row["status"] for row in candidate["comparison"]], ["unknown", "unknown"])
        self.assertNotIn("identity ", candidate["record"]["input"]["base_scene"])
        self.assertTrue(self.validate(candidate, scene=self.bare, record=self.legacy, record_project=None))

    def test_08_continuous_same_target_true_noop_keeps_complete_record(self):
        candidate = self.candidate(scene=self.active, identities=(0, 2))
        self.assertIs(candidate.get("changed"), False, "R09B_V2_TRUE_NOOP")
        self.assertEqual(candidate["record"], self.identified)
        self.assertEqual(candidate["beforeRaw"], raw_record(self.identified).decode())

    def test_09_continuous_other_target_requires_later_carrier_edit(self):
        with self.assertRaises(ModelError, msg="R09B_V2_CONTINUOUS_RETARGET_OUTSIDE_D1"):
            self.candidate(scene=self.active)

    def test_10_fixed_order_orientation_purpose_count_and_duplicate_guards(self):
        originals = self.choices()
        mutations = []
        for field, value in (("orientation", -1), ("purpose", "calculation-cap"), ("carrierId", CARRIERS[1])):
            choice = deepcopy(originals)
            choice[0][field] = value
            mutations.append((field, choice))
        duplicate = deepcopy(originals)
        duplicate[0]["placement_id"] = 2
        mutations.extend((("duplicate", duplicate), ("missing-row", originals[:1]), ("reordered", originals[::-1])))
        for label, choices in mutations:
            with self.subTest(guard=label), self.assertRaises(ModelError, msg="R09B_V2_FIXED_ROW_" + label):
                self.engine.prepare_candidate(raw_record(self.identified), self.replaced, choices,
                    project_id=PROJECT, record_project_id=PROJECT, carrier_ids=CARRIERS, **self.native)

    def test_11_missing_target_rejects_entire_batch_without_changing_old_record(self):
        before = raw_record(self.identified)
        with self.assertRaises(ModelError, msg="R09B_WHOLE_BATCH_NO_AVAILABLE_TARGET"):
            self.candidate(scene=self.no_target)
        self.assertEqual(raw_record(self.identified), before)

    def test_12_native_i70_errors_are_operation_failures_not_absent(self):
        missing = "\n".join(line for line in self.active.split("\n") if not line.startswith("identity placement 0 "))
        duplicate = self.active.replace(self.marker(1), self.marker(0))
        for source in (missing, duplicate, "unrecognized-source-line\n"):
            with self.subTest(source=source[-120:]), self.assertRaises(ModelError, msg="R09B_I70_FAILS_BEFORE_R57"):
                self.engine.inspect(raw_record(self.identified), source, project_id=PROJECT, record_project_id=PROJECT, **self.native)

    def test_13_frames_are_native_and_complete_model_replays_single_source(self):
        candidate = self.candidate(scene=self.rotated, identities=(0, 2))
        old_base = load_base(self.identified["input"]["base_scene"], executable=self.base)
        _, bare = native_view(self.rotated, self.bridge)
        new_base = load_base(bare, executable=self.base)
        def frame(base, identity):
            item = next(row for row in base["placements"] if row["id"] == identity)
            return {name: item[name] for name in ("origin", "u", "v", "n")}
        expected = [{"carrierId": label, "before": frame(old_base, identity), "after": frame(new_base, identity),
                     "orientation": use["orientation"], "purpose": use["purpose"]}
                    for label, identity, use in zip(CARRIERS, (0, 2), self.identified["input"]["uses"])]
        self.assertEqual(candidate.get("frames"), expected, "R09B_V2_NATIVE_OLD_AND_NEW_FRAMES")
        self.assertNotEqual(expected[0]["before"], expected[0]["after"])
        replay = space_modeling.replay_stored(candidate["record"]["input"], candidate["record"]["result"], base_executable=self.base)
        self.assertEqual(replay, candidate["record"]["result"], "R09B_COMPLETE_NATIVE_REPLAY")
        self.assertNotIn("identity ", candidate["record"]["input"]["base_scene"])
        self.assertEqual(candidate["record"]["source"]["scene_hash"], replay["source_sha256"])

    def test_14_revalidation_rejects_old_fact_witness_frame_and_capability_tampering(self):
        baseline = self.candidate()
        mutations = (("beforeRaw", "{}\n"), ("beforeSha256", "0" * 64), ("comparison", []),
                     ("frames", []), ("currentReferences", []), ("requiredCapabilities", []))
        for field, value in mutations:
            forged = deepcopy(baseline)
            forged[field] = value
            with self.subTest(field=field), self.assertRaises(ModelError, msg="R09B_V2_AUDIT_TAMPER_REJECT_" + field):
                self.validate(forged)
        self.assertTrue(self.validate(baseline))

    def test_15_different_current_mark_and_source_context_reject_validation(self):
        candidate = self.candidate()
        with self.assertRaises(ModelError, msg="R09B_V2_DIFFERENT_SOURCE_REJECTS_DRAFT"):
            self.validate(candidate, scene=self.rotated)
        with self.assertRaises(ModelError, msg="R09B_V2_DIFFERENT_CALLER_CONTEXT_REJECTS_DRAFT"):
            self.validate(candidate, project="other-project")
        with self.assertRaises(ModelError, msg="R09B_V2_FOREIGN_IMPORT_UNSUPPORTED"):
            self.candidate(record_project="other-project")

    def test_16_capability_declares_stateless_unverified_authority_and_bounded_drafts(self):
        capabilities = self.engine.capabilities()
        self.assertEqual(capabilities.get("authority"), AUTHORITY, "R09B_V2_NO_FALSE_HOST_AUTHORITY")
        self.assertFalse(capabilities["complete"])
        self.assertEqual(capabilities["consumers"], ["ordinary-faces-fixed"])
        self.assertEqual(capabilities["automaticReceiptKinds"], [])
        for field in ("commit", "save", "history", "modelCarrierEdit"):
            self.assertIs(capabilities[field], False)
        self.assertEqual(capabilities["capacities"], {"faces": 16, "recordBytes": 8388608,
            "draftBytes": 16777216, "sceneBytes": 1048576, "carrierLabelBytes": 128})
        self.assertFalse(hasattr(self.engine, "Session"), "R09B_NO_SECOND_HISTORY")
        candidate = self.candidate()
        self.assertIs(candidate["candidateNotSaveable"], True)
        self.assertIs(candidate["committed"], False)
        self.assertEqual(candidate["authority"], AUTHORITY)
        import modeling
        self.assertNotIn("source-reassociation/1", modeling.CAPABILITIES)

    def test_17_provisional_labels_have_exact_unique_bounded_mapping(self):
        duplicates = self.choices()
        duplicates[1]["carrierId"] = CARRIERS[0]
        long_label = self.choices()
        long_label[0]["carrierId"] = "x" * 129
        cases = (([CARRIERS[0], CARRIERS[0]], duplicates),
                 (["x" * 129, CARRIERS[1]], long_label), ([], self.choices()), (CARRIERS[::-1], self.choices()))
        for labels, choices in cases:
            with self.subTest(labels=labels), self.assertRaises(ModelError, msg="R09B_V2_PROVISIONAL_LABEL_GUARD"):
                self.engine.prepare_candidate(raw_record(self.identified), self.replaced, choices,
                    project_id=PROJECT, record_project_id=PROJECT, carrier_ids=labels, **self.native)

    def test_18_cross_project_unknown_is_separate_from_shared_js_domain(self):
        graph, _ = native_view(self.active, self.bridge)
        authorities = []
        for record_project in (None, "another-project"):
            with self.subTest(record_project=record_project):
                raw = raw_record(self.identified)
                info = self.engine.inspect(raw, self.active, project_id=PROJECT, record_project_id=record_project, **self.native)
                self.assertEqual([row["status"] for row in info["comparison"]], ["unknown", "unknown"])
                authorities.append(info.get("authority"))
                self.assertEqual(raw, raw_record(self.identified))
        self.assertEqual(authorities, [AUTHORITY, AUTHORITY], "R09B_V2_SCOPE_IS_CALLER_ASSERTED")
        identity = self.identified["sourceIdentity"]
        expected = oracle.judge_roots(identity, graph, same_project=False)
        self.assertEqual(self.engine.judge_roots(identity, graph, same_project=False), expected,
                         "R09B_PROJECT_SCOPE_ORACLE_AND_PYTHON_ONLY")
        with self.assertRaisesRegex(AssertionError, "R09B_JS_SHARED_DOMAIN_ONLY"):
            js_judge([{"identity": identity, "graph": graph, "same_project": False}])


if __name__ == "__main__":
    unittest.main(verbosity=2)
