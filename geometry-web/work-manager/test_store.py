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
        self.assertEqual(current["delivery_status"], "verification_pending")
        self.assertEqual(current["head_alignment"], "different")
        self.assertIn("head_conflict", {item["code"] for item in current["alerts"]})

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

    def test_source_ci_is_observation_not_a_passing_work_item(self):
        source = {"id": "synthetic-main", "kind": "git", "version": 1, "as_of": WHEN,
                  "status": "ok", "source_sha": HEAD, "ci": [{
                      "name": "synthetic-main-check", "sha": HEAD, "status": "completed",
                      "conclusion": "success", "runner_id": 0, "steps": []}]}
        state = self.store.import_snapshot({"schema_version": 1, "source": source, "events": []})
        self.assertEqual(state["tasks"], [])
        self.assertEqual(state["sources"][0]["ci"][0]["effective_result"], "not_run")
        self.assertEqual(state["sources"][0]["ci_observed_at"], WHEN)
        self.assertIn("ci_not_run", {alert["code"] for alert in state["alerts"]})

    def test_source_ci_requires_its_exact_sha_and_failed_fetch_preserves_observation(self):
        source = {"id": "synthetic-main", "kind": "git", "version": 1, "as_of": WHEN,
                  "status": "ok", "source_sha": HEAD, "ci": [{
                      "name": "synthetic-main-check", "sha": "b" * 40, "status": "completed",
                      "conclusion": "success", "runner_id": 1,
                      "steps": [{"name": "test", "status": "completed", "conclusion": "success"}]}]}
        first = self.store.import_snapshot({"schema_version": 1, "source": source, "events": []})
        self.assertEqual(first["sources"][0]["ci"][0]["effective_result"], "stale")
        failure = {"schema_version": 1, "source": {
            "id": "synthetic-main", "kind": "git", "version": 2, "as_of": "2026-10-06T02:30:00Z",
            "status": "error", "error": "Synthetic unavailable source"}, "events": []}
        after = self.store.import_snapshot(failure)
        self.assertEqual(after["sources"][0]["ci"], first["sources"][0]["ci"])
        self.assertEqual(after["sources"][0]["ci_observed_at"], WHEN)
        self.assertEqual(after["payload_hash"], first["payload_hash"])

    def test_inventory_changes_payload_but_observation_refresh_does_not_reset_action(self):
        self.ingest(self.task())
        initial_task = self.view()
        inventory = {"repository": "synthetic/example", "complete": True, "issues": [{
            "number": 1, "url": "https://example.invalid/synthetic/example/issues/1",
            "task_ids": ["SYNTHETIC"]}]}
        payload = {"schema_version": 1, "source": {
            "id": "synthetic-inventory", "kind": "manual_snapshot", "version": 1,
            "as_of": WHEN, "status": "ok"}, "events": [], "issue_inventory": inventory}
        first = self.store.import_snapshot(payload)
        self.assertIsNone(first["coverage"]["repositories"][0]["issues"][0]["title"])
        second_payload = copy.deepcopy(payload)
        second_payload["source"].update(version=2, as_of="2026-10-06T02:30:00Z")
        second = self.store.import_snapshot(second_payload)
        self.assertEqual(first["payload_hash"], second["payload_hash"])
        self.assertNotEqual(first["state_hash"], second["state_hash"])
        second_payload["source"].update(version=3)
        second_payload["issue_inventory"]["issues"][0]["title"] = "Synthetic observed title"
        third = self.store.import_snapshot(second_payload)
        self.assertNotEqual(second["payload_hash"], third["payload_hash"])
        self.assertEqual(self.view()["next_action_pin"], initial_task["next_action_pin"])
        self.assertEqual(len(third["tasks"]), 1)

    def metadata(self, version=1, **updates):
        pr = {"number": 1, "url": "https://example.invalid/synthetic/pull/1",
              "head_sha": HEAD, "updated_at": "2026-10-06T02:20:00Z"}
        pr.update(updates)
        return self.event("github", {"pr_metadata": pr}, version=version,
                          when="2026-10-06T02:30:00Z")

    def ci_job(self, run_id=41, **updates):
        job = {"id": run_id + 100, "run_id": run_id, "attempt": 1,
               "name": "same-check-name", "sha": HEAD, "status": "completed", "conclusion": "success",
               "runner_id": 1, "steps": [{"name": "test", "status": "completed", "conclusion": "success"}]}
        job.update(updates)
        return job

    def ci_run(self, identity=41, **updates):
        run = {"id": identity, "sha": HEAD, "status": "completed", "conclusion": "success",
               "attempt": 1, "job_count": 1, "url": f"https://example.invalid/actions/runs/{identity}"}
        run.update(updates)
        return run

    def test_metadata_preserves_review_and_completed_check_for_identical_inputs(self):
        result = self.result([])
        result["data"]["pr"].update(merged=False, merged_head_sha=None)
        self.ingest(self.task(), result)
        initial = self.view()
        self.assertEqual(initial["next_action_code"], "verify_acceptance")
        self.store.record_result(self.event("result", {"completed_actions": [{
            "action": initial["next_action_code"], "input_pin": initial["next_action_pin"],
            "timestamp": WHEN}]}, event_id="synthetic-check-receipt"))
        self.ingest(self.metadata(), when="2026-10-06T02:30:00Z")
        current = self.view()
        self.assertEqual(current["pr"]["reviewed_sha"], HEAD)
        self.assertEqual(current["pr"]["effective_review_state"], "approved")
        self.assertEqual(current["head_changed_at"], WHEN)
        self.assertEqual(current["next_action_pin"], initial["next_action_pin"])
        self.assertTrue(current["next_action_completed"])
        self.assertFalse(current["ready"])

    def test_metadata_never_replaces_explicit_work_head_even_with_newer_remote_time(self):
        result = self.result([])
        result["data"]["pr"].update(merged=False, merged_head_sha=None)
        self.ingest(self.task(), result)
        newer = self.event("task", {"head_sha": "b" * 40}, version=2, when="2026-10-06T02:10:00Z")
        self.ingest(newer, when="2026-10-06T02:10:00Z")
        self.ingest(self.metadata(), when="2026-10-06T02:30:00Z")
        current = self.view()
        self.assertEqual(current["head_sha"], "b" * 40)
        self.assertEqual(current["published_head_sha"], HEAD)
        self.assertEqual(current["head_origin"], "work")
        self.assertEqual(current["head_changed_at"], "2026-10-06T02:10:00Z")
        self.assertEqual(current["head_alignment"], "different")
        self.assertEqual(current["pr"]["effective_review_state"], "stale")
        self.assertEqual(current["delivery_status"], "verification_pending")

    def test_pr_inferred_head_can_advance_without_reusing_old_review(self):
        result = self.result([])
        result["data"]["pr"].update(merged=False, merged_head_sha=None)
        self.ingest(self.task(head_sha=None), result)
        self.assertEqual(self.view()["head_origin"], "pr")
        self.ingest(self.metadata(head_sha="b" * 40), when="2026-10-06T02:30:00Z")
        current = self.view()
        self.assertEqual(current["head_sha"], "b" * 40)
        self.assertEqual(current["published_head_sha"], "b" * 40)
        self.assertEqual(current["pr"]["reviewed_sha"], HEAD)
        self.assertEqual(current["pr"]["effective_review_state"], "stale")

    def test_metadata_different_pr_does_not_carry_review_or_ci(self):
        result = self.result([])
        result["data"]["pr"].update(ci=[self.ci_job()], ci_runs=[self.ci_run()])
        self.ingest(self.task(), result)
        self.ingest(self.metadata(url="https://example.invalid/another-repo/pull/1"),
                    when="2026-10-06T02:30:00Z")
        current = self.view()
        self.assertEqual(current["pr"]["review_state"], "unknown")
        self.assertIsNone(current["pr"].get("reviewed_sha"))
        self.assertEqual(current["ci"], [])
        self.assertEqual(current["ci_runs"], [])

    def test_metadata_cannot_inject_review_or_approval_and_is_atomic(self):
        self.ingest(self.task())
        before = self.store.reconcile()["state_hash"]
        for field, value in (("review_state", "approved"), ("reviewed_sha", HEAD),
                             ("owner_thread", "synthetic-owner"), ("approval_constraints", [])):
            with self.subTest(field=field):
                with self.assertRaises(ValidationError):
                    self.ingest(self.metadata(**{field: value}))
                self.assertEqual(self.store.reconcile()["state_hash"], before)

    def test_run_failure_or_missing_jobs_cannot_be_replaced_by_passing_jobs(self):
        self.ingest(self.task())
        cases = [
            ([self.ci_job()], [self.ci_run(conclusion="failure")], "failed"),
            ([], [self.ci_run(job_count=0)], "not_run"),
            ([self.ci_job(runner_id=0, steps=[])], [self.ci_run()], "not_run"),
            ([self.ci_job()], [self.ci_run(job_count=2)], "unknown"),
            ([self.ci_job()], [self.ci_run()], "passed"),
        ]
        for version, (jobs, runs, expected) in enumerate(cases, 1):
            with self.subTest(expected=expected):
                result = self.result([self.evidence("stable-proof")])
                result["event_id"], result["version"] = f"synthetic-run-check-{version}", version
                result["data"]["pr"].update(ci=jobs, ci_runs=runs)
                self.ingest(result)
                current = self.view()
                self.assertEqual(current["ci_runs"][0]["effective_result"], expected)
                self.assertEqual(current["ci_runs"][0]["observed_job_count"], len(jobs))
                self.assertEqual(current["delivery_status"], "done" if expected == "passed" else "verification_pending")

    def test_empty_run_list_is_unknown_not_vacuously_passing(self):
        result = self.result([self.evidence("proof")])
        result["data"]["pr"].update(ci=[], ci_runs=[])
        self.ingest(self.task(), result)
        current = self.view()
        self.assertEqual(current["ci"], [])
        self.assertEqual(current["ci_runs"], [])
        self.assertEqual(current["delivery_status"], "verification_pending")
        self.assertIn("ci_unknown", {alert["code"] for alert in current["alerts"]})

    def test_same_named_jobs_keep_distinct_run_identity_and_run_semantics_pin(self):
        result = self.result([self.evidence("proof")])
        result["data"]["pr"].update(ci=[self.ci_job(41), self.ci_job(42)],
                                   ci_runs=[self.ci_run(41), self.ci_run(42)])
        self.ingest(self.task(), result)
        initial = self.view()
        self.assertEqual([job["run_id"] for job in initial["ci"]], [41, 42])
        self.assertEqual([run["observed_job_count"] for run in initial["ci_runs"]], [1, 1])
        self.assertEqual(initial["delivery_status"], "done")
        result["event_id"], result["version"] = "synthetic-run-failed", 2
        result["data"]["pr"]["ci_runs"][1]["conclusion"] = "failure"
        self.ingest(result)
        self.assertNotEqual(self.view()["next_action_pin"], initial["next_action_pin"])
        self.assertEqual(self.view()["delivery_status"], "verification_pending")

    def test_source_refresh_without_ci_retains_original_proof_time_and_stales_on_new_head(self):
        source = {"id": "synthetic-main", "kind": "git", "version": 1, "as_of": WHEN,
                  "status": "ok", "source_sha": HEAD, "ci": [self.ci_job()], "ci_runs": [self.ci_run()]}
        initial = self.store.import_snapshot({"schema_version": 1, "source": source, "events": []})
        source = {key: value for key, value in source.items() if key not in {"ci", "ci_runs"}}
        source.update(version=2, as_of="2026-10-06T02:10:00Z")
        refresh = self.store.import_snapshot({"schema_version": 1, "source": source, "events": []})
        self.assertEqual(refresh["sources"][0]["ci"], initial["sources"][0]["ci"])
        self.assertEqual(refresh["sources"][0]["ci_observed_at"], WHEN)
        self.assertEqual(refresh["payload_hash"], initial["payload_hash"])
        source.update(version=3, as_of="2026-10-06T02:20:00Z", source_sha="b" * 40)
        changed = self.store.import_snapshot({"schema_version": 1, "source": source, "events": []})
        self.assertEqual(changed["sources"][0]["ci"][0]["sha"], HEAD)
        self.assertEqual(changed["sources"][0]["ci"][0]["effective_result"], "stale")
        self.assertEqual(changed["sources"][0]["ci_runs"][0]["effective_result"], "stale")
        self.assertEqual(changed["sources"][0]["ci_observed_at"], WHEN)


if __name__ == "__main__":
    unittest.main()
