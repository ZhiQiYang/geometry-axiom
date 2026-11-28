"""R09b D2/S1: bounded native-backed carrier drafts, not App authority.

T alone runs the existing D1 calculator. Its refusal (or fixed-carrier draft)
is caught at a named assertion after a real native fixture has succeeded.
Missing modules, environmental failures and timeouts are never accepted reds.
"""
from copy import deepcopy
import hashlib
import importlib
import importlib.util
import itertools
import json
import os
from pathlib import Path
import queue
import secrets
import subprocess
import sys
import tempfile
import threading
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
for directory in (ROOT, ROOT / "geometry-core", ROOT / "geometry-web"):
    if str(directory) not in sys.path:
        sys.path.insert(0, str(directory))

from tests import _bridge, binaries
from tests.oracles import r09b_model_carrier_edit as oracle
from modeling import ModelError, canonical_bytes
from modeling.base import load_base
import model_update
import source_reassociation as d1
import space_modeling


PROJECT = "r09b-d2-project"
LABELS = ["draft-floor", "draft-wall"]
SCENE = ("surface 0 origin 0 0 0 u +x v +y rect 0 0 4000 3000\n"
         "surface 1 origin 0 0 0 u +x v +y rect 0 0 4000 3000\n"
         "surface 2 origin 0 0 0 u +x v +z rect 0 0 4000 2000\n"
         "surface 3 origin 0 3000 0 u +x v +z rect 0 0 4000 2000\n")
OLD_USES = [{"placement_id": 0, "orientation": 1, "purpose": "boundary"},
            {"placement_id": 2, "orientation": -1, "purpose": "calculation-cap"}]
AUTHORITY = {"project": "caller-asserted", "history": "unverified", "confirmation": False,
             "carrierIds": "caller-provisional"}


def raw_record(record):
    return (json.dumps(record, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


def selection(uses=None, labels=None):
    return [{"carrierId": label, **deepcopy(use)} for label, use in
            zip(LABELS if labels is None else labels, OLD_USES if uses is None else uses)]


class ExistingD1:
    """Expose actual D1 behavior, without synthesizing D2 fields or promises."""
    capabilities = staticmethod(d1.capabilities)
    judge_roots = staticmethod(d1.judge_roots)
    prepare_candidate = staticmethod(d1.prepare_candidate)

    @staticmethod
    def validate_candidate(candidate, record_raw, source_scene, selected, *, carrier_ids, **kwargs):
        # D1 does not independently bind these caller inputs. Tests must expose
        # that limitation, rather than altering the old implementation here.
        return d1.validate_candidate(candidate, record_raw, source_scene, **kwargs)


def product_or_baseline():
    if importlib.util.find_spec("model_carrier_edit") is None:
        return ExistingD1
    return importlib.import_module("model_carrier_edit")


def js_judge(cases, *, corrupt_input=False):
    if any(case["same_project"] is not True for case in cases):
        raise AssertionError("R09B_D2_JS_SHARED_DOMAIN_ONLY")
    script = """const fs = require('fs');
const ledger = require(process.argv[1]);
const payload = JSON.parse(fs.readFileSync(0, 'utf8'));
const before = JSON.stringify(payload.cases);
const rows = payload.cases.map(c => ledger.judgeRoots(c.identity, c.graph));
if (payload.corrupt && payload.cases.length) payload.cases[0].identity.roots[0].id = 999999;
const after = JSON.stringify(payload.cases);
process.stdout.write(JSON.stringify({rows, before, after}));
"""
    child = subprocess.run(["node", "-e", script, str(ROOT / "geometry-web" / "identity-ledger.js")],
        input=json.dumps({"cases": cases, "corrupt": corrupt_input}), text=True,
        capture_output=True, timeout=60, check=False)
    if child.returncode != 0:
        raise RuntimeError("R09B_D2_NODE_ENVIRONMENT: " + child.stderr)
    response = json.loads(child.stdout)
    if response["before"] != response["after"]:
        raise AssertionError("R09B_D2_JS_INPUT_MUTATED_IN_NODE")
    return response["rows"]


class BoundedBridge(_bridge.BridgeSession):
    """One reply is bounded, including fixture and diagnostic entry steps."""
    def command(self, text):
        answer = queue.Queue(maxsize=1)
        def read():
            try:
                answer.put((True, super(BoundedBridge, self).command(text)))
            except BaseException as exc:
                answer.put((False, exc))
        thread = threading.Thread(target=read, daemon=True)
        thread.start()
        try:
            ok, value = answer.get(timeout=20)
        except queue.Empty:
            self.process.kill()
            self.process.wait(timeout=5)
            raise RuntimeError("R09B_D2_NATIVE_REPLY_TIMEOUT: " + text) from None
        if not ok:
            raise value
        return value


def native_view(scene, bridge):
    with tempfile.TemporaryDirectory(prefix="r09b-d2-view-") as directory:
        source = Path(directory) / "source.scene"
        source.write_text(scene, encoding="utf-8", newline="\n")
        with BoundedBridge(bridge, cwd=directory) as child:
            graph = child.command("source-inspect-file " + str(source))
            loaded = child.command("loadfile " + str(source))
            if graph.get("ok") is not True or loaded.get("ok") is not True:
                raise RuntimeError("R09B_D2_NATIVE_FIXTURE_INVALID")
            bare = child.command("dump-deidentified")
    if bare.get("ok") is not True:
        raise RuntimeError("R09B_D2_NATIVE_DEIDENTIFICATION_FAILED")
    return {"data": {"identityLedger": graph["identityLedger"]},
            "nodes": {row["key"]: row for row in graph["nodes"]}}, bare["text"]


class CarrierSelection(unittest.TestCase):
    def setUp(self):
        self.engine = product_or_baseline()

    def plan(self, chosen, labels=None, uses=None):
        function = getattr(self.engine, "plan_selection", None)
        self.assertTrue(callable(function), "R09B_D2_SELECTION_PLANNER_REQUIRED")
        return function(LABELS if labels is None else labels,
                        OLD_USES if uses is None else uses, chosen)

    def test_00_three_way_full_rows_over_source_sequences(self):
        cases = list(oracle.sequence_cases(depth=3))
        self.assertGreater(len(cases), 100, "R09B_D2_EXHAUSTIVE_DOMAIN_NONTRIVIAL")
        before = canonical_bytes(cases)
        expected = [oracle.classify_rows(c["identity"], c["graph"], same_project=True) for c in cases]
        js = js_judge(cases)
        native = [self.engine.judge_roots(c["identity"], c["graph"], same_project=True) for c in cases]
        self.assertEqual(js, expected, "R09B_D2_K3_ORACLE_FULL_ROWS")
        self.assertEqual(native, expected, "R09B_D2_THREE_WAY_FULL_ROWS")
        self.assertEqual(canonical_bytes(cases), before, "R09B_D2_PYTHON_INPUTS_UNCHANGED")
        self.assertEqual({row["status"] for rows in native for row in rows},
                         {"unknown", "absent", "replaced", "conflict", "continuous"},
                         "R09B_D2_ALL_FIVE_STATES")
        self.assertTrue(any(any(key.startswith("parameter-field:") for key in c["graph"]["nodes"])
                            for c in cases), "R09B_D2_FULL_GRAPH_HAS_THREE_PART_KEYS")
        print("R09B_D2_THREE_WAY " + json.dumps({"cases": len(cases), "rows": sum(map(len, native)),
              "sha256": hashlib.sha256(canonical_bytes(native)).hexdigest()}, sort_keys=True))

    def test_01_node_in_process_mutation_negative_control(self):
        case = next(iter(oracle.sequence_cases(depth=1)))
        baseline = js_judge([case])
        with self.assertRaisesRegex(AssertionError, "R09B_D2_JS_INPUT_MUTATED_IN_NODE"):
            js_judge([case], corrupt_input=True)
        self.assertEqual(js_judge([case]), baseline, "R09B_D2_JS_GUARD_RESTORED")

    def test_02_cross_project_is_explicit_not_manufactured_js_agreement(self):
        case = next(iter(oracle.sequence_cases(depth=1)))
        expected = oracle.classify_rows(case["identity"], case["graph"], same_project=False)
        self.assertEqual(self.engine.judge_roots(case["identity"], case["graph"], same_project=False), expected,
                         "R09B_D2_FOREIGN_SCOPE_UNKNOWN")
        foreign = {**case, "same_project": False}
        with self.assertRaisesRegex(AssertionError, "R09B_D2_JS_SHARED_DOMAIN_ONLY"):
            js_judge([foreign])

    def test_03_exhaustive_small_carrier_lists_match_independent_oracle(self):
        # Product and oracle see identical explicit inputs. The oracle is not
        # used to construct product inputs or called from product code.
        self.assertTrue(callable(getattr(self.engine, "plan_selection", None)),
                        "R09B_D2_SELECTION_PLANNER_REQUIRED")
        count = accepted = rejected = 0
        options = [{"carrierId": label, "placement_id": target,
                    "orientation": sign, "purpose": purpose}
                   for label, target, sign, purpose in itertools.product(
                       (LABELS[0], LABELS[1], "new"), range(3), (-1, 1),
                       ("boundary", "calculation-cap"))]
        for length in range(4):
            for chosen in itertools.product(options, repeat=length):
                chosen = deepcopy(list(chosen))
                expected = oracle.expected_selection(LABELS, OLD_USES, chosen)
                before = canonical_bytes([LABELS, OLD_USES, chosen])
                try:
                    actual = self.engine.plan_selection(LABELS, OLD_USES, chosen)
                except ModelError:
                    self.assertEqual(expected["outcome"], "rejected", "R09B_D2_LIST_ORACLE_ACCEPTANCE")
                    rejected += 1
                else:
                    self.assertEqual(expected["outcome"], "prepared", "R09B_D2_LIST_ORACLE_REJECTION")
                    self.assertEqual(actual, {name: expected[name] for name in ("rows", "removed", "orderChanged")},
                                     "R09B_D2_LIST_ORACLE_ALL_VALUES")
                    accepted += 1
                self.assertEqual(canonical_bytes([LABELS, OLD_USES, chosen]), before,
                                 "R09B_D2_LIST_INPUTS_UNCHANGED")
                count += 1
        self.assertEqual((count, accepted, rejected), (47989, 1800, 46189),
                         "R09B_D2_COMPLETE_CARRIER_LIST_DOMAIN")
        print("R09B_D2_LIST_SCAN " + json.dumps({"cases": count, "accepted": accepted, "rejected": rejected}))

    def test_04_reorder_keeps_orientation_and_purpose_on_carrier(self):
        actual = self.plan(selection()[::-1])
        self.assertTrue(actual["orderChanged"], "R09B_D2_REORDER_DETECTED")
        self.assertEqual([(row["carrierId"], row["beforeIndex"], row["after"]) for row in actual["rows"]],
            [(LABELS[1], 1, OLD_USES[1]), (LABELS[0], 0, OLD_USES[0])],
            "R09B_D2_SETTINGS_FOLLOW_CARRIER")

    def test_05_empty_duplicate_and_incomplete_new_rows_are_refused(self):
        valid = selection()
        invalid = [[], [valid[0], valid[0]],
                   [valid[0], {**valid[1], "placement_id": 0}],
                   [valid[0], {**valid[1], "carrierId": ""}],
                   [valid[0], {**valid[1], "carrierId": "\ud800"}],
                   [valid[0], {**valid[1], "carrierId": "x" * 129}],
                   [valid[0], {**valid[1], "orientation": True}],
                   [valid[0], {**valid[1], "placement_id": True}],
                   [valid[0], {**valid[1], "placement_id": -1}],
                   [valid[0], {**valid[1], "placement_id": 2**32}],
                   [valid[0], {**valid[1], "orientation": 0}],
                   [valid[0], {**valid[1], "purpose": "guessed"}]]
        for field in ("carrierId", "placement_id", "orientation", "purpose"):
            row = {"carrierId": "new", "placement_id": 3, "orientation": 1, "purpose": "boundary"}
            del row[field]
            invalid.append([*valid, row])
        for chosen in invalid:
            with self.subTest(chosen=chosen), self.assertRaises(ModelError,
                    msg="R09B_D2_EXPLICIT_UNIQUE_NONEMPTY_LIST"):
                self.plan(chosen)

    def test_06_retained_settings_cannot_silently_change(self):
        for field, value in (("orientation", -1), ("purpose", "calculation-cap")):
            chosen = selection()
            chosen[0][field] = value
            with self.subTest(field=field), self.assertRaises(ModelError,
                    msg="R09B_D2_RETAINED_SETTINGS_PINNED"):
                self.plan(chosen)

    def test_07_carrier_capacity_and_exact_old_mapping(self):
        uses = [{"placement_id": i, "orientation": 1, "purpose": "boundary"} for i in range(16)]
        labels = ["draft-" + str(i) for i in range(16)]
        self.assertEqual(len(self.plan(selection(uses, labels), labels, uses)["rows"]), 16,
                         "R09B_D2_SIXTEEN_ROWS_ACCEPTED")
        with self.assertRaises(ModelError, msg="R09B_D2_SEVENTEEN_ROWS_REJECTED"):
            self.plan(selection(uses, labels) + [{"carrierId": "extra", "placement_id": 16,
                     "orientation": 1, "purpose": "boundary"}], labels, uses)
        for bad in (["same", "same"], [LABELS[0]], ["x" * 129, LABELS[1]]):
            with self.subTest(labels=bad), self.assertRaises(ModelError,
                    msg="R09B_D2_OLD_LABEL_MAPPING_EXACT"):
                self.plan(selection(), bad)


class NativeCarrierEdit(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if os.name == "posix":
            import resource
            soft, hard = resource.getrlimit(resource.RLIMIT_STACK)
            if soft != resource.RLIM_INFINITY and soft < 16 * 1024 * 1024:
                resource.setrlimit(resource.RLIMIT_STACK,
                    (min(16 * 1024 * 1024, hard) if hard != resource.RLIM_INFINITY else 16 * 1024 * 1024, hard))
        programs = {}
        for name, variable in (("bridge", "GEOMETRY_TEST_BRIDGE"), ("model-base", "GEOMETRY_MODEL_BASE")):
            info = binaries.inspect_one(binaries.BY_NAME[name], path=os.environ.get(variable))
            if info.state != "fresh":
                raise RuntimeError("R09B_D2_NATIVE_ENVIRONMENT " + name + ": " + info.reason)
            programs[name] = str(info.path)
        cls.bridge, cls.base = programs["bridge"], programs["model-base"]
        cls.native = {"base_executable": cls.base, "bridge_executable": cls.bridge}
        with tempfile.TemporaryDirectory(prefix="r09b-d2-fixture-") as directory:
            path = Path(directory) / "fixture.scene"
            path.write_text(SCENE, encoding="utf-8", newline="\n")
            with BoundedBridge(cls.bridge, cwd=directory) as child:
                def command(text):
                    result = child.command(text)
                    if result.get("preview", {}).get("valid"):
                        result = child.command("line confirm " + str(result["preview"]["token"]))
                    if result.get("ok") is not True:
                        raise RuntimeError("R09B_D2_REAL_NATIVE_FIXTURE: " + repr((text, result)))
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
                cls.replacement_marks = command("identity-read")["marks"]
                command("line surface 0 origin 500 0 0 u +y v +z rect 0 0 4000 3000")
                cls.intersecting = command("dump")["text"]
                # Apply the same proper rigid rotation to both model faces.
                # Rotating only one face would intersect the other's interior.
                command("line surface 0 origin 0 0 0 u +y v +z rect 0 0 4000 3000")
                command("line surface 2 origin 0 0 0 u +y v +x rect 0 0 4000 2000")
                cls.rotated = command("dump")["text"]
                request = {"schema": "engineering-transaction/1",
                    "expectedRevision": command("engineering-read")["revision"],
                    "operations": [{"op": "put-parameter", "value": {"id": 9, "name": "Unrelated card",
                        "fields": [{"id": 2, "name": "Length", "type": "dimension", "input": "915"}]}}]}
                request_path = Path(directory) / "parameter.json"
                request_path.write_text(json.dumps(request), encoding="utf-8")
                pending = child.command("engineering-preview " + str(request_path))
                if pending.get("ok") is not True or not pending.get("preview", {}).get("valid"):
                    raise RuntimeError("R09B_D2_PARAMETER_FIXTURE")
                command("engineering-confirm " + str(pending["preview"]["token"]))
                cls.with_parameter = command("dump")["text"]
        cls.conflict = cls.active.replace(cls.mark(0), "SWAP_MARK").replace(cls.mark(1), cls.mark(0)).replace("SWAP_MARK", cls.mark(1))
        cls.legacy = cls.make_record(cls.bare)
        cls.identified = deepcopy(cls.legacy)
        cls.identified["sourceIdentity"] = {"schema": "model-source-identity/1", "roots": [
            {"role": "use", "kind": "placement", "id": u["placement_id"], "incarnation": cls.mark(u["placement_id"])}
            for u in OLD_USES]}
        cls.f1b = model_update.prepare_update({"record": deepcopy(cls.identified), "current_scene": cls.bare,
             "selection": {"mode": "faces", "uses": [{"placement_id": 0}, {"placement_id": 2}], "obstacles": []}}, **cls.native)
        cls.engine = product_or_baseline()
        cls.cache = {}

    @classmethod
    def mark(cls, identifier, marks=None):
        return next(row["mark"] for row in (cls.marks if marks is None else marks)
                    if row["kind"] == "placement" and row["id"] == identifier)

    @classmethod
    def make_record(cls, scene, uses=None):
        inputs = {"mode": "faces", "base_scene": load_base(scene, executable=cls.base)["base_scene"],
                  "uses": deepcopy(OLD_USES if uses is None else uses), "obstacles": []}
        result = space_modeling.preview(inputs, base_executable=cls.base)
        return {"id": "r09b-d2-model", "name": "D2 ordinary faces", "created_at": "2026-11-28T01:00:00.000Z",
            "source": {"kind": "scene", "placement_id": None, "boundary_id": None, "scene_hash": result["source_sha256"]},
            "input": inputs, "result": result}

    def candidate(self, chosen=None, *, scene=None, record=None, labels=None, project=PROJECT, record_project=PROJECT,
                  marker="R09B_D2_VALID_NATIVE_CANDIDATE"):
        chosen = selection() if chosen is None else chosen
        record = self.identified if record is None else record
        scene = self.active if scene is None else scene
        labels = LABELS if labels is None else labels
        encoded = raw_record(record)
        cache_key = (encoded, scene, canonical_bytes(chosen), canonical_bytes(labels), project, record_project)
        if cache_key not in self.cache:
            try:
                result = self.engine.prepare_candidate(encoded, scene, chosen,
                    project_id=project, record_project_id=record_project, carrier_ids=labels, **self.native)
            except ModelError as exc:
                self.fail(marker + ": existing/native calculation refused " + exc.code)
            self.cache[cache_key] = result
        result = deepcopy(self.cache[cache_key])
        self.assertEqual(result.get("schema"), "geometry-model-carrier-draft/1", marker + "_SCHEMA")
        return result

    def reject(self, chosen, marker, *, scene=None, record=None, labels=None, record_project=PROJECT):
        with self.assertRaises(ModelError, msg=marker) as caught:
            self.engine.prepare_candidate(raw_record(self.identified if record is None else record),
                self.active if scene is None else scene, chosen, project_id=PROJECT,
                record_project_id=record_project, carrier_ids=LABELS if labels is None else labels, **self.native)
        return caught.exception

    def validate(self, candidate, chosen=None, *, scene=None, record=None, labels=None, project=PROJECT):
        return self.engine.validate_candidate(candidate, raw_record(self.identified if record is None else record),
            self.active if scene is None else scene, selection() if chosen is None else chosen,
            project_id=project, record_project_id=PROJECT, carrier_ids=LABELS if labels is None else labels, **self.native)

    def test_00_existing_native_f1b_fixture_is_green_before_new_feature(self):
        self.assertEqual(self.f1b["record"]["result"], self.legacy["result"], "R09B_D2_REAL_F1B_BASELINE")
        self.assertEqual(self.legacy["result"]["summary"]["face_count"], 2)
        self.assertIsNone(self.legacy["result"]["volume"])
        self.assertNotEqual(self.mark(0), self.mark(0, self.replacement_marks))

    def test_01_native_add_rebuilds_all_packages(self):
        chosen = [*selection(), {"carrierId": "draft-new", "placement_id": 3,
                                "orientation": 1, "purpose": "boundary"}]
        draft = self.candidate(chosen, marker="R09B_D2_NATIVE_ADD")
        record = draft["geometryRecord"]
        expected_inputs = {"mode": "faces", "base_scene": self.legacy["input"]["base_scene"],
                           "uses": [{k: row[k] for k in ("placement_id", "orientation", "purpose")} for row in chosen],
                           "obstacles": []}
        expected = space_modeling.preview(expected_inputs, base_executable=self.base)
        self.assertEqual(record["result"], expected, "R09B_D2_NATIVE_ALL_PACKAGE_VALUES")
        self.assertEqual(record["result"]["summary"]["face_count"], 3)
        self.assertEqual(draft["plan"]["rows"][-1]["operation"], "added")
        self.assertIsNone(draft["frames"][-1]["before"])

    def test_02_native_remove_only_changes_model_inclusion(self):
        draft = self.candidate(selection()[1:], marker="R09B_D2_NATIVE_REMOVE")
        self.assertEqual(draft["geometryRecord"]["input"]["uses"], [OLD_USES[1]])
        self.assertEqual(draft["geometryRecord"]["result"]["summary"]["face_count"], 1)
        self.assertEqual([row["carrierId"] for row in draft["plan"]["removed"]], [LABELS[0]])
        self.assertEqual(draft["source"]["scene"], self.active, "R09B_D2_REMOVE_DOES_NOT_DELETE_WORLD")
        self.assertEqual(len(draft["comparison"]), 2, "R09B_D2_REMOVED_OLD_FACT_RETAINED")

    def test_03_native_reorder_preserves_settings_by_label(self):
        draft = self.candidate(selection()[::-1], marker="R09B_D2_NATIVE_REORDER")
        self.assertEqual(draft["geometryRecord"]["input"]["uses"], OLD_USES[::-1], "R09B_D2_NATIVE_SETTINGS_FOLLOW_CARRIER")
        self.assertEqual([row["carrierId"] for row in draft["currentReferences"]], LABELS[::-1])
        self.assertTrue(draft["plan"]["orderChanged"])

    def test_04_continuous_retarget_rechecks_explicit_orientation_and_purpose(self):
        chosen = selection()[:1]
        chosen[0].update(placement_id=3, orientation=-1, purpose="calculation-cap")
        draft = self.candidate(chosen, marker="R09B_D2_CONTINUOUS_RETARGET")
        self.assertEqual(draft["comparison"][0]["status"], "continuous")
        self.assertEqual(draft["plan"]["rows"][0]["operation"], "retargeted")
        self.assertEqual(draft["geometryRecord"]["input"]["uses"][0],
                         {"placement_id": 3, "orientation": -1, "purpose": "calculation-cap"})
        frame = draft["frames"][0]
        self.assertEqual(frame["beforeEffectiveNormal"], [0, 0, 1], "R09B_D2_OLD_EFFECTIVE_NORMAL")
        self.assertEqual(frame["afterEffectiveNormal"], [0, 1, 0], "R09B_D2_NEW_EFFECTIVE_NORMAL")
        self.assertEqual(frame["beforeOrientation"], 1)
        self.assertEqual(frame["afterOrientation"], -1)
        self.assertEqual([row["carrierId"] for row in draft["plan"]["removed"]], [LABELS[1]])
        disconnected = [*chosen, selection()[1]]
        error = self.reject(disconnected, "R09B_D2_NATIVE_DISCONNECTED_SHELL_REFUSED")
        self.assertEqual(error.code, "SHELL_DISCONNECTED")

    def test_05_rotated_same_target_keeps_relative_direction_and_shows_world_change(self):
        draft = self.candidate(scene=self.rotated, marker="R09B_D2_ROTATED_FRAME")
        frame = draft["frames"][0]
        self.assertEqual(frame["afterOrientation"], 1)
        self.assertEqual(frame["after"]["n"], [1, 0, 0])
        self.assertNotEqual(frame["beforeEffectiveNormal"], frame["afterEffectiveNormal"],
                            "R09B_D2_WORLD_DIRECTION_CHANGE_VISIBLE")
        error = self.reject(selection(), "R09B_D2_NATIVE_INTERSECTING_SHELL_REFUSED", scene=self.intersecting)
        self.assertEqual(error.code, "SHELL_SELF_INTERSECTION")

    def test_06_replaced_same_geometry_preserves_old_fact_and_new_reference(self):
        draft = self.candidate(scene=self.replaced, marker="R09B_D2_REPLACED_NOT_CONTINUOUS")
        self.assertEqual(draft["comparison"][0]["status"], "replaced", "R09B_D2_OLD_REPLACED_FACT")
        self.assertFalse(draft["comparison"][0]["definitionChanged"])
        self.assertEqual(draft["currentReferences"][0]["pin"]["incarnation"], self.mark(0, self.replacement_marks))
        self.assertEqual(json.loads(draft["beforeRaw"])["sourceIdentity"], self.identified["sourceIdentity"])
        self.assertIn(LABELS[0], draft["impact"]["nonContinuousCarrierIds"])

    def test_07_absent_and_conflict_are_manual_drafts_not_repairs(self):
        chosen = selection()
        chosen[0]["placement_id"] = 1
        for source, status in ((self.absent, "absent"), (self.conflict, "conflict")):
            with self.subTest(status=status):
                draft = self.candidate(chosen, scene=source, marker="R09B_D2_MANUAL_" + status.upper())
                self.assertEqual(draft["comparison"][0]["status"], status)
                self.assertEqual(draft["source"]["scene"], source, "R09B_D2_NO_IDENTITY_REPAIR")
                self.assertEqual(draft["currentReferences"][0]["pin"]["id"], 1)

    def test_08_unknown_inactive_keeps_no_mark_and_exact_old_bytes(self):
        draft = self.candidate(scene=self.bare, record=self.legacy, record_project=None,
                               marker="R09B_D2_UNKNOWN_MANUAL")
        self.assertEqual(draft["beforeRaw"].encode("utf-8"), raw_record(self.legacy), "R09B_D2_EXACT_OLD_BYTES")
        self.assertNotIn("sourceIdentity", json.loads(draft["beforeRaw"]))
        self.assertEqual([r["status"] for r in draft["comparison"]], ["unknown", "unknown"])
        for reference in draft["currentReferences"]:
            self.assertIsNone(reference["pin"]["incarnation"], "R09B_D2_NO_FABRICATED_MARK")
            self.assertEqual(reference["unknownReason"], "ledger-inactive")

    def test_09_geometry_inputs_and_packages_are_deidentified(self):
        draft = self.candidate(marker="R09B_D2_DEIDENTIFIED_DRAFT")
        record = draft["geometryRecord"]
        self.assertNotIn("sourceIdentity", record, "R09B_D2_PROJECTION_NOT_PERSISTENT_IDENTITY")
        replay = space_modeling.replay_stored(record["input"], record["result"], base_executable=self.base)
        self.assertEqual(record["result"], replay, "R09B_D2_NATIVE_FULL_REPLAY")
        self.assertEqual(record["source"]["scene_hash"], replay["source_sha256"])
        self.assertNotIn("identity ", record["input"]["base_scene"])
        for kind in model_update.PACKAGES:
            if record["result"].get(kind) is not None:
                self.assertNotIn("identity ", json.dumps(record["result"][kind], ensure_ascii=False))
                self.assertNotIn("identity-ledger/1", json.dumps(record["result"][kind], ensure_ascii=False))

    def test_10_parameter_field_in_complete_graph_does_not_break_ordinary_roots(self):
        graph, _ = native_view(self.with_parameter, self.bridge)
        self.assertIn("parameter-field:9:f2", graph["nodes"], "R09B_D2_REAL_THREE_PART_KEY")
        draft = self.candidate(scene=self.with_parameter, marker="R09B_D2_PARAMETER_FIELD_GRAPH")
        self.assertEqual([r["id"] for r in draft["comparison"]], [0, 2])
        expected = oracle.classify_rows(self.identified["sourceIdentity"], graph)
        self.assertEqual(self.engine.judge_roots(self.identified["sourceIdentity"], graph), expected)
        self.assertEqual(js_judge([{"identity": self.identified["sourceIdentity"], "graph": graph,
                                    "same_project": True}])[0], expected)

    def test_11_bad_i70_and_missing_target_are_operation_failures(self):
        missing = "\n".join(line for line in self.active.split("\n") if not line.startswith("identity placement 0 "))
        duplicate = self.active.replace(self.mark(1), self.mark(0))
        for bad in (missing, duplicate, "not-a-scene-command\n"):
            with self.subTest(bad=bad[-100:]):
                error = self.reject(selection(), "R09B_D2_I70_OPERATION_FAILURE", scene=bad)
                self.assertIn(error.code, ("REASSOCIATION_SOURCE_INVALID", "REASSOCIATION_SOURCE_MARK"))
        chosen = selection()
        chosen[0]["placement_id"] = 15
        self.reject(chosen, "R09B_D2_MISSING_SELECTED_TARGET")

    def test_12_native_rejects_empty_and_invalid_complete_selection(self):
        for chosen in ([], [selection()[0], selection()[0]],
                       [{**selection()[0], "orientation": -1}, selection()[1]]):
            with self.subTest(chosen=chosen):
                self.reject(chosen, "R09B_D2_NATIVE_SELECTION_GUARDS")
        for source, chosen in ((self.active + "\ud800", selection()),
                (self.active, [{**selection()[0], "carrierId": "\ud800"}, selection()[1]])):
            with self.subTest(unicode_source=source != self.active):
                error = None
                try:
                    self.engine.prepare_candidate(raw_record(self.identified), source, chosen,
                        project_id=PROJECT, record_project_id=PROJECT, carrier_ids=LABELS, **self.native)
                except (ModelError, UnicodeError) as exc:
                    error = exc
                self.assertIsInstance(error, ModelError, "R09B_D2_INVALID_UNICODE_CLASSIFIED")

    def test_13_external_original_selection_rejects_other_self_consistent_candidate(self):
        chosen = selection()
        chosen[0]["placement_id"] = 1
        other = self.candidate(chosen, marker="R09B_D2_EXTERNAL_SELECTION_FIXTURE")
        self.assertTrue(self.validate(other, chosen))
        with self.assertRaises(ModelError, msg="R09B_D2_EXTERNAL_SELECTION_BOUND"):
            self.validate(other, selection())

    def test_14_external_original_carrier_mapping_is_bound(self):
        draft = self.candidate(marker="R09B_D2_EXTERNAL_LABELS_FIXTURE")
        self.assertTrue(self.validate(draft))
        with self.assertRaises(ModelError, msg="R09B_D2_EXTERNAL_LABELS_BOUND"):
            self.validate(draft, labels=LABELS[::-1])

    def test_15_full_draft_revalidation_rejects_tampering(self):
        draft = self.candidate(marker="R09B_D2_VALIDATION_FIXTURE")
        for field, value in (("beforeRaw", "{}\n"), ("beforeSha256", "0" * 64),
            ("comparison", []), ("currentReferences", []), ("frames", []), ("requiredCapabilities", []),
            ("carrierIds", []), ("candidateNotSaveable", False), ("committed", True), ("contract", {})):
            altered = deepcopy(draft)
            altered[field] = value
            with self.subTest(field=field), self.assertRaises(ModelError, msg="R09B_D2_FULL_DRAFT_BINDING_" + field):
                self.validate(altered)
        self.assertTrue(self.validate(draft))

    def test_16_source_or_project_change_invalidates_draft(self):
        draft = self.candidate(marker="R09B_D2_SOURCE_BINDING_FIXTURE")
        for options in ({"scene": self.replaced}, {"project": "different-project"}):
            with self.subTest(options=options), self.assertRaises(ModelError, msg="R09B_D2_SOURCE_CONTEXT_BOUND"):
                self.validate(draft, **options)
        self.reject(selection(), "R09B_D2_KNOWN_FOREIGN_PROJECT_REFUSED", record_project="different-project")

    def test_17_bad_old_model_and_unsupported_attachment_are_not_discarded(self):
        wrong = deepcopy(self.identified)
        wrong["result"]["summary"]["face_count"] = 99
        self.reject(selection(), "R09B_D2_OLD_REPLAY_REQUIRED", record=wrong)
        extra = deepcopy(self.identified)
        extra["review"] = {"state": "verified"}
        self.reject(selection(), "R09B_D2_UNKNOWN_ATTACHMENT_NOT_DROPPED", record=extra)

    def test_18_capability_is_partial_and_has_no_commit_save_or_history(self):
        capabilities = self.engine.capabilities()
        self.assertEqual(capabilities.get("draftCapability"), "model-carrier-edit/1", "R09B_D2_PARTIAL_CAPABILITY")
        self.assertIs(capabilities["complete"], False)
        for field in ("commit", "save", "history"):
            self.assertIs(capabilities[field], False, "R09B_D2_NO_FALSE_HOST_AUTHORITY")
        self.assertEqual(capabilities["authority"], AUTHORITY)
        self.assertEqual(capabilities["capacities"]["faces"], 16)
        self.assertFalse(hasattr(self.engine, "Session"))
        draft = self.candidate(marker="R09B_D2_NO_PERSISTENT_AUTHORITY")
        self.assertIs(draft["candidateNotSaveable"], True)
        self.assertIs(draft["committed"], False)
        self.assertEqual(draft["authority"], AUTHORITY)
        self.assertNotIn("changed", draft, "R09B_D2_NO_HISTORY_SWITCH")
        import modeling
        self.assertNotIn("model-carrier-edit/1", modeling.CAPABILITIES)

    def test_19_source_scene_capacity_is_rejected_without_truncation(self):
        source = self.active + "#" + "x" * (1024 * 1024)
        error = self.reject(selection(), "R09B_D2_SOURCE_CAPACITY", scene=source)
        self.assertEqual(error.status, "UNSUPPORTED")

    def test_20_originals_unchanged_on_success_and_rejection(self):
        chosen = selection()[::-1]
        before = canonical_bytes([self.identified, chosen, LABELS])
        old_bytes = raw_record(self.identified)
        draft = self.candidate(chosen, marker="R09B_D2_NO_WRITES")
        self.assertEqual(draft["beforeRaw"].encode("utf-8"), old_bytes)
        self.reject([], "R09B_D2_FAILURE_NO_WRITES")
        self.assertEqual(canonical_bytes([self.identified, chosen, LABELS]), before, "R09B_D2_ALL_INPUTS_UNCHANGED")

    @staticmethod
    def fixed_graph(bindings, *, versions=None, fields=None):
        """Synthetic validated graph boundary, not a native-scene claim."""
        versions, fields = versions or {}, fields or {}
        nodes, edges = {}, {}
        for target, material in bindings.items():
            root = "placement:" + str(target)
            fixed = "material:" + material
            nodes[root] = {"key": root, "kind": "placement", "id": str(target), "version": 0,
                           "definitionFingerprint": "a" * 64}
            nodes[fixed] = {"key": fixed, "kind": "material", "id": material,
                            "version": versions.get(material, 1), "definitionFingerprint": "b" * 64}
            edges[root] = [{"from": root, "to": fixed, "relation": "fixed-source",
                            "field": fields.get(target, "A"), "active": True}]
        return nodes, edges, {}

    def fixed_check(self, before, after, chosen=None):
        function = getattr(self.engine, "_fixed_sources", None)
        self.assertTrue(callable(function), "R09B_D2_FIXED_SOURCE_GUARD_REQUIRED")
        chosen = selection() if chosen is None else chosen
        plan = self.engine.plan_selection(LABELS, OLD_USES, chosen)
        with patch.object(model_update, "_graph", side_effect=[before, after]) as graph:
            result = function(self.identified, "synthetic-source", plan, self.bridge)
            self.assertEqual(graph.call_count, 2, "R09B_D2_BOTH_FIXED_GRAPHS_READ")
        return result

    def test_21_fixed_versions_follow_each_carrier_not_global_union(self):
        old = self.fixed_graph({0: "wood-a", 2: "wood-b"})
        self.fixed_check(old, deepcopy(old), selection()[::-1])
        changes = (self.fixed_graph({0: "wood-a", 2: "wood-b"}, versions={"wood-a": 2}),
                   self.fixed_graph({0: "wood-b", 2: "wood-a"}))
        for after in changes:
            with self.subTest(after=after):
                with self.assertRaises(ModelError, msg="R09B_D2_FIXED_VERSION_PER_CARRIER") as caught:
                    self.fixed_check(old, after)
                self.assertEqual(caught.exception.code, "UPDATE_FIXED_VERSION")

    def test_22_fixed_field_associations_cannot_swap_while_union_matches(self):
        old = self.fixed_graph({0: "wood-a", 2: "wood-b"})
        new = self.fixed_graph({0: "wood-a", 2: "wood-b"}, fields={0: "B"})
        self.assertEqual(model_update._protected(old, self.identified["input"])[0],
                         model_update._protected(new, self.identified["input"])[0],
                         "R09B_D2_FIXED_UNION_COUNTEREXAMPLE")
        with self.assertRaises(ModelError, msg="R09B_D2_FIXED_ASSOCIATION_PER_CARRIER") as caught:
            self.fixed_check(old, new)
        self.assertEqual(caught.exception.code, "UPDATE_FIXED_VERSION")

    def test_23_explicit_added_removed_dependencies_do_not_upgrade_retained_rows(self):
        old = self.fixed_graph({0: "wood-a", 2: "wood-b"})
        new = self.fixed_graph({0: "wood-a", 2: "wood-b", 3: "wood-c"})
        added = [*selection(), {"carrierId": "new", "placement_id": 3, "orientation": 1, "purpose": "boundary"}]
        self.fixed_check(old, new, added)
        self.fixed_check(old, new, selection()[1:])
        broken = deepcopy(new)
        del broken[0]["material:wood-c"]
        with self.assertRaises(ModelError, msg="R09B_D2_NEW_SOURCE_CLOSURE_REQUIRED"):
            self.fixed_check(old, broken, added)

    def test_24_native_candidate_actually_calls_fixed_source_guard(self):
        guard = getattr(self.engine, "_fixed_sources", None)
        self.assertTrue(callable(guard), "R09B_D2_NATIVE_FIXED_GUARD_REQUIRED")
        with patch.object(self.engine, "_fixed_sources", side_effect=ModelError(
                "INVALID", "R09B_D2_FIXED_PROBE", "I76", "test boundary refusal")) as probe:
            failure = self.reject(selection(), "R09B_D2_NATIVE_FIXED_GUARD_USED")
        self.assertEqual(failure.code, "R09B_D2_FIXED_PROBE", "R09B_D2_NATIVE_FIXED_REFUSAL_PROPAGATED")
        self.assertEqual(probe.call_count, 1)

    def test_25_context_runtime_is_bound_before_old_replay_and_source_observation(self):
        # A real context supplies all native values; only its recorded runtime
        # hash is altered to emulate a version change during the earlier phase.
        context = list(d1._context(raw_record(self.identified), self.active, PROJECT, PROJECT,
                                  self.base, self.bridge))
        context[-1] = {**context[-1], "base_binary_sha256": "0" * 64}
        with patch.object(d1, "_context", return_value=tuple(context)):
            failure = self.reject(selection(), "R09B_D2_CONTEXT_RUNTIME")
        self.assertEqual(failure.status, "UNSUPPORTED")
        self.assertIn("RUNTIME", failure.code)

    def test_26_aggregate_request_budget_preserves_original_byte_cost(self):
        original = raw_record(self.identified)
        at_individual_limit = original + b" " * (8 * 1024 * 1024 - len(original))
        with self.assertRaises(ModelError, msg="R09B_D2_AGGREGATE_REQUEST_CAPACITY") as caught:
            self.engine.prepare_candidate(at_individual_limit, self.active, selection(),
                project_id=PROJECT, record_project_id=PROJECT, carrier_ids=LABELS, **self.native)
        self.assertEqual(caught.exception.status, "UNSUPPORTED")


if __name__ == "__main__":
    unittest.main(verbosity=2)
