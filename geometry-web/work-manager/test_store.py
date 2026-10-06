"""Focused operator-boundary tests. All records and paths are synthetic."""
import copy
import contextlib
import datetime as dt
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from store import Store, ValidationError, atomic_write_json
from cli import main as cli_main

HEAD = "a" * 40
NOW = dt.datetime(2026, 10, 6, 3, 0, tzinfo=dt.timezone.utc)
WHEN = "2026-10-06T02:00:00Z"


class OperatorBoundaryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="geometry-work-manager-operator-test-")
        self.clock = patch("store.utc_now", return_value=NOW)
        self.clock.start()
        self.store = Store(Path(self.temp.name) / "private")
        self.version = 0

    def tearDown(self):
        self.clock.stop()
        self.temp.cleanup()

    def event(self, kind, data, task="SYNTHETIC", version=1, event_id=None, when=WHEN):
        return {"event_id": event_id or f"synthetic:{task}:{kind}:{version}",
                "task_id": task, "kind": kind, "version": version,
                "occurred_at": when, "data": data}

    def task(self, task="SYNTHETIC", **updates):
        data = {"title": "合成工作", "scope": "Only synthetic files",
                "files": ["synthetic/a.py"], "required_acceptance": ["behavior"],
                "head_sha": HEAD}
        data.update(updates)
        return self.event("task", data, task=task)

    def ingest(self, *events, when=WHEN):
        self.version += 1
        return self.store.import_snapshot({
            "schema_version": 1, "source": {"id": "synthetic-input", "kind": "manual_snapshot",
            "version": self.version, "as_of": when, "status": "ok"}, "events": list(events)})

    def view(self, task="SYNTHETIC"):
        return next(item for item in self.store.reconcile()["tasks"] if item["id"] == task)

    def assignment(self, **updates):
        data = {"owner_thread": "synthetic-owner", "execution_status": "active"}
        data.update(updates)
        return self.event("assignment", data, event_id="synthetic-local-assignment")

    def test_partial_snapshot_preserves_contributing_source_time(self):
        self.ingest(self.task())
        self.ingest(self.task("SECOND"), when="2026-10-06T02:30:00Z")
        first, second = self.view(), self.view("SECOND")
        self.assertEqual(first["source_provenance"][0]["as_of"], WHEN)
        self.assertEqual(first["source_provenance"][0]["version"], 1)
        self.assertEqual(second["source_provenance"][0]["version"], 2)
        self.assertEqual(len(self.store.reconcile()["tasks"]), 2)

    def test_unknown_scope_is_read_only_and_cannot_be_assigned(self):
        self.ingest(self.task(files=[]))
        task = self.view()
        self.assertIn("scope_unknown", {item["code"] for item in task["alerts"]})
        self.assertEqual(task["next_action_code"], "verify_scope")
        with self.assertRaises(ValidationError):
            self.store.record_assignment(self.assignment())

    def test_assignment_rejects_files_outside_scope_without_mutation(self):
        self.ingest(self.task())
        before = self.store.reconcile()["state_hash"]
        with self.assertRaises(ValidationError):
            self.store.record_assignment(self.assignment(files=["product/private.py"]))
        self.assertEqual(before, self.store.reconcile()["state_hash"])

    def test_assignment_rejects_different_owner_file_conflict(self):
        self.ingest(self.task(), self.task("SECOND"),
                    self.event("assignment", {"owner_thread": "other-owner", "execution_status": "active"}, task="SECOND"))
        before = self.store.reconcile()["state_hash"]
        with self.assertRaises(ValidationError):
            self.store.record_assignment(self.assignment())
        self.assertEqual(before, self.store.reconcile()["state_hash"])

    def test_result_cannot_start_work_bypassing_assignment(self):
        self.ingest(self.task(approval_constraints=[{"action": "execute", "status": "denied"}]))
        with self.assertRaises(ValidationError):
            self.store.record_result(self.event("result", {"execution_status": "active"}))
        self.assertEqual(self.view()["execution_status"], "unknown")

    def test_local_older_stream_version_is_rejected(self):
        self.ingest(self.task())
        current = self.assignment()
        current["version"] = 2
        self.store.record_assignment(current)
        older = self.assignment(execution_status="stopped")
        older["event_id"] = "synthetic-local-older"
        with self.assertRaises(ValidationError):
            self.store.record_assignment(older)
        self.assertEqual(self.view()["execution_status"], "active")

    def test_stop_without_owner_field_retains_assignment_identity(self):
        self.ingest(self.task(), self.assignment())
        self.ingest(self.event("assignment", {"execution_status": "stopped"}, version=2))
        self.assertEqual(self.view()["owner_thread"], "synthetic-owner")
        self.assertEqual(self.view()["execution_status"], "stopped")

    def test_blocked_work_can_resume_with_audited_reason(self):
        self.ingest(self.task(), self.assignment(execution_status="blocked"))
        self.assertFalse(self.view()["ready"])
        resume = self.assignment(reason="合成阻塞已明確排除")
        resume["event_id"] = "synthetic-local-resume"
        self.store.record_assignment(resume)
        self.assertEqual(self.view()["execution_status"], "active")
        self.assertIn("合成阻塞已明確排除", json.dumps(self.view()["assignment_history"], ensure_ascii=False))

    def evidence(self, identity, result="passed", **updates):
        evidence = {"id": identity, "criterion": "behavior", "kind": "test",
                    "timestamp": WHEN, "sha": HEAD, "result": result}
        evidence.update(updates)
        return evidence

    def result(self, evidence):
        return self.event("result", {"evidence": evidence, "pr": {
            "number": 1, "url": "https://example.invalid/synthetic/pull/1",
            "head_sha": HEAD, "merged_head_sha": HEAD, "merged": True,
            "review_state": "approved", "reviewed_sha": HEAD}})

    def test_simultaneous_failed_proof_wins_over_alphabetically_later_pass(self):
        self.ingest(self.task(), self.result([
            self.evidence("a-failure", result="failed"), self.evidence("z-pass")]))
        task = self.view()
        self.assertNotEqual(task["delivery_status"], "done")
        self.assertEqual(task["last_verified_evidence"]["result"], "failed")
        self.assertEqual(task["acceptance"][0]["result"], "failed")

    def test_failed_executed_ci_step_overrides_success_claim(self):
        self.ingest(self.task(), self.result([self.evidence("ci-claim", kind="ci",
            runner_id=12, steps=[{"name": "test", "status": "completed", "conclusion": "failure"}])]))
        task = self.view()
        self.assertNotEqual(task["delivery_status"], "done")
        self.assertEqual(task["acceptance"][0]["result"], "failed")

    def test_new_head_exposes_old_review_as_expired(self):
        old = self.result([self.evidence("old-head-proof")])
        old["data"]["pr"]["merged"] = False
        old["data"]["pr"]["merged_head_sha"] = None
        self.ingest(self.task(), old)
        self.assertEqual(self.view()["pr"]["effective_review_state"], "approved")
        newer = self.task(head_sha="b" * 40)
        newer["event_id"], newer["version"] = "synthetic-new-head", 2
        newer["occurred_at"] = "2026-10-06T02:30:00Z"
        self.ingest(newer, when="2026-10-06T02:30:00Z")
        current = self.view()
        self.assertEqual(current["pr"]["review_state"], "approved")
        self.assertEqual(current["pr"]["effective_review_state"], "stale")
        self.assertEqual(current["evidence"][0]["effective_result"], "unknown")
        self.assertEqual(current["delivery_status"], "awaiting_review")

    def test_postmerge_proof_preserves_actual_tested_merge_commit(self):
        merge_commit = "b" * 40
        result = self.result([self.evidence("synthetic-merge-test", kind="postmerge_test", sha=merge_commit)])
        result["data"]["pr"]["merge_commit_sha"] = merge_commit
        self.ingest(self.task(), result)
        task = self.view()
        self.assertEqual(task["delivery_status"], "done")
        self.assertEqual(task["evidence"][0]["sha"], merge_commit)
        self.assertEqual(task["evidence"][0]["bound_head_sha"], HEAD)
        self.assertEqual(task["evidence"][0]["validity"], "merged_commit")

    def test_postmerge_binding_requires_exact_merged_pr_and_commit(self):
        result = self.result([self.evidence("wrong-merge-proof", kind="postmerge_test", sha="b" * 40)])
        result["data"]["pr"]["merge_commit_sha"] = "c" * 40
        self.ingest(self.task(), result)
        self.assertNotEqual(self.view()["delivery_status"], "done")
        self.assertEqual(self.view()["evidence"][0]["validity"], "stale")
        second = self.result([self.evidence("unmerged-postmerge-proof", kind="postmerge_test", sha=HEAD)])
        second["event_id"], second["version"] = "synthetic-unmerged-postmerge", 2
        second["data"]["pr"].update(merged=False, merge_commit_sha=HEAD)
        self.ingest(second)
        self.assertEqual(self.view()["acceptance"][0]["result"], "unknown")

    def test_generic_test_cannot_use_merge_commit_as_head_alias(self):
        result = self.result([self.evidence("generic-merge-alias", sha="b" * 40)])
        result["data"]["pr"]["merge_commit_sha"] = "b" * 40
        self.ingest(self.task(), result)
        self.assertEqual(self.view()["evidence"][0]["effective_result"], "unknown")
        self.assertNotEqual(self.view()["delivery_status"], "done")

    def test_local_tree_equivalence_is_explicit_and_preserves_tested_sha(self):
        tested, tree = "b" * 40, "c" * 40
        result = self.result([self.evidence("local-tree-proof", kind="local_test", sha=tested,
                                           tree_sha=tree, equivalent_head_sha=HEAD)])
        self.ingest(self.task(head_tree_sha=tree), result)
        task = self.view()
        self.assertEqual(task["delivery_status"], "done")
        self.assertEqual(task["evidence"][0]["sha"], tested)
        self.assertEqual(task["evidence"][0]["validity"], "tree_equivalent")
        self.assertEqual(task["acceptance"][0]["result"], "passed")

    def test_tree_change_or_new_target_head_invalidates_equivalence(self):
        self.ingest(self.task(head_tree_sha="c" * 40), self.result([
            self.evidence("mapped-proof", kind="local_test", sha="b" * 40,
                          tree_sha="c" * 40, equivalent_head_sha=HEAD)]))
        for version, updates in ((2, {"head_tree_sha": "d" * 40}), (3, {"head_sha": "e" * 40, "head_tree_sha": "c" * 40})):
            with self.subTest(updates=updates):
                self.ingest(self.event("task", updates, version=version))
                self.assertEqual(self.view()["acceptance"][0]["result"], "unknown")
                self.assertNotEqual(self.view()["delivery_status"], "done")

    def test_ci_and_review_never_use_tree_equivalence(self):
        for kind in ("ci", "review"):
            with self.subTest(kind=kind):
                task_id = "SYNTHETIC-" + kind
                proof = self.evidence("not-local-proof", kind=kind, sha="b" * 40,
                    tree_sha="c" * 40, equivalent_head_sha=HEAD,
                    runner_id=12, steps=[{"name": "test", "status": "completed", "conclusion": "success"}])
                result = self.result([proof])
                result["task_id"], result["event_id"] = task_id, "synthetic-result-" + kind
                self.ingest(self.task(task_id, head_tree_sha="c" * 40), result)
                self.assertEqual(self.view(task_id)["evidence"][0]["effective_result"], "unknown")

    def test_transition_approval_request_is_waiting_not_permission(self):
        for action in ("ready", "ready_for_review", "publish_bundle", "publish_pr", "create_pr"):
            with self.subTest(action=action):
                task_id = "HOLD-" + action
                self.ingest(self.task(task_id, approval_constraints=[{
                    "action": action, "scope": "action", "status": "required", "reason": "合成批准請求待答覆"}]))
                task = self.view(task_id)
                self.assertEqual(task["delivery_status"], "approval_blocked")
                self.assertEqual(task["next_action_mode"], "wait")
                self.assertFalse(task["ready"])
                self.assertEqual(task["approval_constraints"][0]["status"], "required")

    def test_merge_action_hold_waits_without_repeating_approved_review(self):
        result = self.result([self.evidence("approved-proof")])
        result["data"]["pr"].update(merged=False, merged_head_sha=None)
        self.ingest(self.task(approval_constraints=[{"action": "merge", "scope": "action", "status": "required"}]), result)
        task = self.view()
        self.assertEqual(task["delivery_status"], "awaiting_integration")
        self.assertEqual(task["next_action_code"], "request_approval")
        self.assertEqual(task["next_action_mode"], "wait")
        self.assertFalse(task["ready"])

    def test_active_owner_collects_result_while_completion_merge_hold_remains(self):
        self.ingest(self.task(approval_constraints=[
            {"action": "execute", "scope": "action", "status": "granted"},
            {"action": "merge", "scope": "completion", "status": "required"}]))
        # An integration hold must not reject explicitly permitted execution.
        self.store.record_assignment(self.assignment())
        task = self.view()
        self.assertEqual(task["execution_status"], "active")
        self.assertEqual(task["delivery_status"], "approval_blocked")
        self.assertEqual(task["next_action_code"], "collect_result")
        self.assertEqual(task["next_action_mode"], "wait")
        self.assertFalse(task["ready"])

    def test_cli_ready_modes_separate_inspection_from_new_work(self):
        self.ingest(self.task("WRITE"))
        review = self.result([self.evidence("review-proof")])
        review["task_id"], review["event_id"] = "READ", "synthetic-read-result"
        review["data"]["pr"].update(merged=False, merged_head_sha=None, review_state="pending", reviewed_sha=None)
        self.ingest(self.task("READ"), review)
        for mode, expected in (("write", ["WRITE"]), ("read_only", ["READ"])):
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                exit_code = cli_main(["--data-dir", str(self.store.data_dir), "list-ready", "--mode", mode])
            payload = json.loads(output.getvalue())
            self.assertEqual(exit_code, 0)
            self.assertEqual([item["id"] for item in payload["ready"]], expected)
            self.assertEqual(payload["ready_counts"]["all"], 2)
            self.assertEqual(payload["state_hash"], self.store.reconcile()["state_hash"])

    def test_projection_failure_rolls_back_import_and_restore(self):
        self.ingest(self.task())
        before = self.store.reconcile()["state_hash"]
        with patch.object(self.store, "_read", side_effect=ValidationError("synthetic projection rejection")):
            with self.assertRaises(ValidationError):
                self.ingest(self.task("SECOND"))
        self.assertEqual(Store(self.store.path).reconcile()["state_hash"], before)
        empty = Store(Path(self.temp.name) / "restore")
        with patch.object(empty, "_read", side_effect=ValidationError("synthetic projection rejection")):
            with self.assertRaises(ValidationError):
                empty.restore(self.store.export_snapshot())
        self.assertEqual(Store(empty.path).reconcile()["tasks"], [])

    def test_private_database_and_atomic_export_permissions(self):
        self.ingest(self.task())
        export_path = Path(self.temp.name) / "private" / "backup.json"
        bundle = self.store.export_snapshot()
        atomic_write_json(export_path, bundle)
        self.assertEqual(self.store.path.stat().st_mode & 0o777, 0o600)
        self.assertEqual(self.store.data_dir.stat().st_mode & 0o777, 0o700)
        self.assertEqual(export_path.stat().st_mode & 0o777, 0o600)
        self.assertEqual(json.loads(export_path.read_text())["checksum"], bundle["checksum"])
        self.assertFalse(list(export_path.parent.glob(".backup.json.*")))


if __name__ == "__main__":
    unittest.main()
