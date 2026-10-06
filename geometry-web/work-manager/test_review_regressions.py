"""Independent review regressions. Synthetic records only; no live queue reads."""

import copy
import datetime as dt
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from store import Store


HEAD_A, HEAD_B = "a" * 40, "b" * 40
CLOCK = dt.datetime.now(dt.timezone.utc).replace(microsecond=0)


def stamp(minutes=0):
    return (CLOCK - dt.timedelta(minutes=30) + dt.timedelta(minutes=minutes)).isoformat()


def event(kind, data, task="REVIEW-QA", version=1, when=None, identity=None):
    return {"event_id": identity or f"synthetic-review:{task}:{kind}:{version}",
            "task_id": task, "kind": kind, "version": version,
            "occurred_at": when or stamp(), "data": data}


def task(task_id="REVIEW-QA", version=1, **updates):
    data = {"title": "合成審查回歸", "scope": "Synthetic review fixtures only",
            "files": [f"synthetic/{task_id}.py"], "branch": "qa/synthetic-review",
            "head_sha": HEAD_A, "required_acceptance": ["behavior"],
            "approval_constraints": [], "dependencies": []}
    data.update(updates)
    return event("task", data, task=task_id, version=version)


def proof(identity="synthetic-proof", head=HEAD_A, result="passed", minutes=0, **updates):
    value = {"id": identity, "criterion": "behavior", "kind": "test", "sha": head,
             "timestamp": stamp(minutes), "result": result,
             "url": "https://example.invalid/synthetic/proof"}
    value.update(updates)
    return value


def pull_request(head=HEAD_A, merged=False, review="approved", **updates):
    value = {"number": 1, "url": "https://example.invalid/synthetic/pull/1",
             "head_sha": head, "merged": merged,
             "merged_head_sha": head if merged else None, "review_state": review,
             "reviewed_sha": head if review in {"approved", "changes_requested"} else None}
    value.update(updates)
    return value


class ReviewRegressions(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="geometry-review-regression-")
        self.path = Path(self.temp.name) / "state"
        self.store = Store(self.path)
        self.version = 0
        self.clock = patch("store.utc_now", return_value=CLOCK)
        self.clock.start()

    def tearDown(self):
        self.clock.stop()
        self.temp.cleanup()

    def payload(self, events, version, minutes=0):
        return {"schema_version": 1,
                "source": {"id": "synthetic-review-source", "kind": "manual_snapshot",
                           "version": version, "as_of": stamp(minutes), "status": "ok"},
                "events": events}

    def ingest(self, *events, minutes=0, store=None):
        self.version += 1
        return (store or self.store).import_snapshot(self.payload(list(events), self.version, minutes))

    def view(self, task_id="REVIEW-QA", store=None):
        return next(item for item in (store or self.store).reconcile()["tasks"] if item["id"] == task_id)

    def prepare_review(self, head=HEAD_A):
        self.ingest(task(head_sha=head), event("result", {"pr": pull_request(head=head),
                    "evidence": [proof(head=head)]}))
        initial = self.view()
        self.assertEqual(initial["next_action_code"], "review_integration")
        self.assertTrue(initial["ready"])
        self.assertRegex(initial["next_action_pin"], r"^[0-9a-f]{64}$")
        return initial

    def complete_current_action(self, minutes=1):
        current = self.view()
        receipt = {"action": current["next_action_code"], "input_pin": current["next_action_pin"],
                   "timestamp": stamp(minutes), "summary": "Synthetic exact-input review completed"}
        completed = event("result", {"completed_actions": [receipt]},
                          version=2, when=stamp(minutes))
        self.version += 1
        self.store.record_result(self.payload([completed], self.version, minutes))
        return receipt

    def test_default_completion_hold_prevents_done_and_dependency_release(self):
        for action in ("publish", "merge", "execute", "all"):
            with self.subTest(action=action):
                parent_id, child_id = f"PARENT-{action}", f"CHILD-{action}"
                self.ingest(task(parent_id, approval_constraints=[{"action": action, "status": "denied"}]),
                            task(child_id, dependencies=[parent_id]),
                            event("result", {"evidence": [proof(identity=f"proof-{action}")],
                                             "pr": pull_request(merged=True)}, task=parent_id))
                parent, child = self.view(parent_id), self.view(child_id)
                self.assertTrue(parent["pr"]["merged"], "historical merge observation must remain traceable")
                self.assertNotEqual(parent["delivery_status"], "done")
                self.assertFalse(child["ready"], "completion hold cannot release dependencies")

    def test_active_owner_pending_pr_is_not_parallel_ready_work(self):
        self.ingest(task(), event("assignment", {"owner_thread": "synthetic-owner", "execution_status": "active"}),
                    event("result", {"pr": pull_request(review="pending"), "evidence": [proof()]}))
        self.assertFalse(self.view()["ready"])

    def test_completed_review_of_same_input_does_not_requeue(self):
        initial = self.prepare_review()
        self.complete_current_action()
        current = self.view()
        self.assertFalse(current["ready"])
        self.assertTrue(current["next_action_completed"])
        self.assertEqual(current["next_action_pin"], initial["next_action_pin"])
        self.assertNotIn(current["id"], {item["id"] for item in self.store.reconcile()["ready"]})

    def test_malformed_nested_ci_is_rejected_before_commit_and_reopens(self):
        bad_step = {"name": "synthetic-step", "status": "completed", "conclusion": {"bad": "shape"}}
        for location in ("evidence", "pr"):
            with self.subTest(location=location):
                isolated = Store(Path(self.temp.name) / location)
                isolated.import_snapshot(self.payload([task()], 1))
                before = isolated.reconcile()["state_hash"]
                data = {"pr": pull_request(merged=True), "evidence": [proof()]}
                if location == "evidence":
                    data["evidence"] = [proof(kind="ci", runner_id=123, steps=[bad_step])]
                else:
                    data["pr"]["ci"] = [{"name": "synthetic-job", "sha": HEAD_A, "status": "completed",
                                           "conclusion": "success", "runner_id": 123, "steps": [bad_step]}]
                rejection = None
                try:
                    isolated.import_snapshot(self.payload([event("result", data)], 2))
                except Exception as error:
                    rejection = error
                reopening_error, reopened = None, None
                try:
                    reopened = Store(isolated.path).reconcile()
                except Exception as error:
                    reopening_error = error
                self.assertIsNone(reopening_error, f"invalid data was committed: {reopening_error!r}")
                self.assertIsInstance(rejection, ValueError, "nested malformed data must be validated before commit")
                self.assertEqual(before, reopened["state_hash"])

    def test_aggregate_approval_without_reviewed_sha_cannot_follow_new_head(self):
        self.ingest(task(), event("result", {"pr": pull_request(), "evidence": [proof()]}))
        aggregate = pull_request(head=HEAD_B)
        aggregate.pop("reviewed_sha")
        newer = event("github", {"pr": aggregate,
                                 "evidence": [proof(identity="new-head-proof", head=HEAD_B, minutes=1)]},
                      version=2, when=stamp(1))
        self.ingest(newer, minutes=1)
        current = self.view()
        self.assertEqual(current["head_sha"], HEAD_B)
        self.assertEqual(current["pr"]["review_state"], "approved")
        self.assertNotEqual(current["pr"]["effective_review_state"], "approved")
        self.assertNotEqual(current["delivery_status"], "awaiting_integration")
        self.assertNotEqual(current["next_action_code"], "review_integration")

    def test_missing_review_pin_cannot_certify_approved_or_done(self):
        unpinned = pull_request(merged=True)
        unpinned.pop("reviewed_sha")
        self.ingest(task(), event("result", {"pr": unpinned, "evidence": [proof()]}))
        self.assertNotEqual(self.view()["pr"]["effective_review_state"], "approved")
        self.assertNotEqual(self.view()["delivery_status"], "done")

    def test_conflicting_duplicate_evidence_id_is_atomic_within_batch(self):
        self.ingest(task())
        before = self.store.reconcile()["state_hash"]
        failed, passed = proof(result="failed"), proof(result="passed")
        with self.assertRaises(ValueError):
            self.ingest(event("result", {"pr": pull_request(merged=True), "evidence": [failed, passed]}))
        self.assertEqual(before, Store(self.path).reconcile()["state_hash"])

    def test_conflicting_duplicate_evidence_id_is_atomic_across_batches(self):
        self.ingest(task(), event("result", {"evidence": [proof(result="failed")]}))
        before = self.store.reconcile()["state_hash"]
        with self.assertRaises(ValueError):
            self.ingest(event("result", {"pr": pull_request(merged=True), "evidence": [proof()]}, version=2))
        self.assertEqual(before, Store(self.path).reconcile()["state_hash"])

    def test_later_stale_head_proof_does_not_displace_current_head_pass(self):
        self.ingest(task(head_sha=HEAD_B), event("result", {"pr": pull_request(head=HEAD_B),
                    "evidence": [proof(identity="current-b-proof", head=HEAD_B)]}))
        before = self.view()
        self.assertEqual(before["acceptance"][0]["result"], "passed")
        self.ingest(event("result", {"evidence": [proof(identity="later-stale-a-proof", head=HEAD_A, minutes=1)]},
                          version=2, when=stamp(1)), minutes=1)
        after = self.view()
        self.assertEqual(after["acceptance"][0]["result"], "passed")
        self.assertEqual(after["acceptance"][0]["evidence_id"], "current-b-proof")
        self.assertEqual(after["delivery_status"], before["delivery_status"])
        self.assertEqual(after["next_action_code"], before["next_action_code"])
        self.assertEqual(len(after["evidence"]), 2, "stale evidence remains in audit history")

    def test_action_scoped_future_publish_hold_does_not_erase_historical_done(self):
        self.ingest(task(), event("result", {"pr": pull_request(merged=True), "evidence": [proof()]}))
        self.assertEqual(self.view()["delivery_status"], "done")
        future_hold = task(version=2, approval_constraints=[
            {"action": "publish", "status": "denied", "scope": "action", "reason": "Synthetic future action hold"}])
        future_hold["occurred_at"] = stamp(1)
        self.ingest(future_hold, minutes=1)
        self.assertEqual(self.view()["delivery_status"], "done")
        self.assertTrue(self.view()["pr"]["merged"])
        self.assertEqual(self.view()["approval_constraints"][0]["status"], "denied")

    def test_explicit_completion_scope_blocks_required_approval(self):
        self.ingest(task(approval_constraints=[{"action": "publish", "status": "required", "scope": "completion"}]),
                    event("result", {"pr": pull_request(merged=True), "evidence": [proof()]}))
        self.assertNotEqual(self.view()["delivery_status"], "done")
        self.assertTrue(self.view()["pr"]["merged"])

    def test_old_reviewed_sha_is_stale_even_when_pr_head_matches_current(self):
        self.ingest(task(head_sha=HEAD_B), event("result", {"pr": pull_request(head=HEAD_B, reviewed_sha=HEAD_A),
                    "evidence": [proof(head=HEAD_B)]}))
        current = self.view()
        self.assertEqual(current["pr"]["effective_review_state"], "stale")
        self.assertNotEqual(current["delivery_status"], "awaiting_integration")
        self.assertNotEqual(current["next_action_code"], "review_integration")

    def test_receipt_survives_source_refresh_and_irrelevant_stale_proof(self):
        initial = self.prepare_review(head=HEAD_B)
        self.complete_current_action()
        pin = initial["next_action_pin"]
        self.ingest(minutes=2)
        self.assertEqual(self.view()["next_action_pin"], pin)
        self.assertFalse(self.view()["ready"])
        stale = proof(identity="irrelevant-stale-a", head=HEAD_A, minutes=3)
        self.ingest(event("result", {"evidence": [stale]}, version=3, when=stamp(3)), minutes=3)
        current = self.view()
        self.assertEqual(current["acceptance"][0]["result"], "passed")
        self.assertEqual(current["next_action_pin"], pin)
        self.assertTrue(current["next_action_completed"])
        self.assertFalse(current["ready"])

    def test_old_head_proof_does_not_requeue_completed_check_with_no_current_proof(self):
        self.ingest(task(head_sha=HEAD_B), event("result", {"pr": pull_request(head=HEAD_B), "evidence": []}))
        initial = self.view()
        self.assertEqual(initial["acceptance"][0]["result"], "unknown")
        self.assertIsNone(initial["acceptance"][0]["evidence_id"])
        self.assertEqual(initial["next_action_code"], "verify_acceptance")
        self.assertTrue(initial["ready"])
        self.complete_current_action()
        self.assertFalse(self.view()["ready"])
        self.ingest(event("result", {"evidence": [proof(identity="only-old-head-proof", head=HEAD_A, minutes=2)]},
                          version=3, when=stamp(2)), minutes=2)
        current = self.view()
        self.assertEqual(current["acceptance"][0]["result"], "unknown")
        self.assertEqual(current["next_action_pin"], initial["next_action_pin"])
        self.assertTrue(current["next_action_completed"])
        self.assertFalse(current["ready"])
        self.assertEqual(len(current["evidence"]), 1, "old-head proof is retained as history")

    def test_new_head_invalidates_completed_receipt(self):
        initial = self.prepare_review()
        self.complete_current_action()
        newer = event("github", {"pr": pull_request(head=HEAD_B),
                      "evidence": [proof(identity="reviewed-b-proof", head=HEAD_B, minutes=2)]}, when=stamp(2))
        self.ingest(newer, minutes=2)
        current = self.view()
        self.assertNotEqual(current["next_action_pin"], initial["next_action_pin"])
        self.assertEqual(current["next_action_code"], "review_integration")
        self.assertTrue(current["ready"])
        self.assertFalse(current["next_action_completed"])

    def test_later_current_head_failure_invalidates_receipt_and_acceptance(self):
        initial = self.prepare_review(head=HEAD_B)
        self.complete_current_action()
        failed = proof(identity="current-b-later-failure", head=HEAD_B, result="failed", minutes=2)
        self.ingest(event("result", {"evidence": [failed]}, version=3, when=stamp(2)), minutes=2)
        current = self.view()
        self.assertEqual(current["acceptance"][0]["result"], "failed")
        self.assertNotEqual(current["next_action_pin"], initial["next_action_pin"])
        self.assertEqual(current["next_action_code"], "verify_acceptance")
        self.assertTrue(current["ready"])

    def test_owner_change_invalidates_receipt_but_active_owner_stays_unready(self):
        initial = self.prepare_review()
        self.complete_current_action()
        self.ingest(event("assignment", {"owner_thread": "synthetic-new-owner", "execution_status": "active"},
                          when=stamp(2)), minutes=2)
        current = self.view()
        self.assertNotEqual(current["next_action_pin"], initial["next_action_pin"])
        self.assertFalse(current["ready"])
        self.assertFalse(current["next_action_completed"])

    def test_changed_constraints_and_dependencies_change_input_pin(self):
        initial = self.prepare_review()
        self.complete_current_action()
        constraint = task(version=2, approval_constraints=[{"action": "publish", "scope": "action", "status": "required"}])
        constraint["occurred_at"] = stamp(2)
        self.ingest(constraint, minutes=2)
        constraints_pin = self.view()["next_action_pin"]
        self.assertNotEqual(constraints_pin, initial["next_action_pin"])
        dependencies = task(version=3, dependencies=["SYNTHETIC-UNKNOWN-DEPENDENCY"])
        dependencies["occurred_at"] = stamp(3)
        self.ingest(dependencies, minutes=3)
        self.assertNotEqual(self.view()["next_action_pin"], constraints_pin)
        self.assertFalse(self.view()["ready"])

    def test_local_wrong_action_pin_is_rejected_without_mutation(self):
        current = self.prepare_review()
        before = self.store.reconcile()["state_hash"]
        wrong = event("result", {"completed_actions": [{"action": current["next_action_code"],
            "input_pin": "0" * 64, "timestamp": stamp(1)}]}, version=2, when=stamp(1))
        with self.assertRaises(ValueError):
            self.store.record_result(self.payload([wrong], 2, 1))
        self.assertEqual(before, self.store.reconcile()["state_hash"])
        self.assertTrue(self.view()["ready"])

    def test_identical_duplicate_evidence_is_idempotent_within_and_across_events(self):
        same = proof()
        self.ingest(task(), event("result", {"pr": pull_request(), "evidence": [same, copy.deepcopy(same)]}))
        current = self.view()
        self.assertEqual(len(current["evidence"]), 1)
        pin = current["next_action_pin"]
        self.ingest(event("result", {"evidence": [copy.deepcopy(same)]}, version=2, when=stamp(1)), minutes=1)
        self.assertEqual(len(self.view()["evidence"]), 1)
        self.assertEqual(self.view()["next_action_pin"], pin)

    def test_conflicting_duplicate_evidence_across_events_in_same_batch_is_atomic(self):
        self.ingest(task())
        before = self.store.reconcile()["state_hash"]
        with self.assertRaises(ValueError):
            self.ingest(event("result", {"evidence": [proof(result="failed")]}, version=1),
                        event("result", {"evidence": [proof(result="passed")]}, version=2))
        self.assertEqual(before, Store(self.path).reconcile()["state_hash"])

    def test_evidence_identity_is_scoped_to_task(self):
        self.ingest(task("FIRST"), task("SECOND"),
                    event("result", {"evidence": [proof(result="failed")]}, task="FIRST"),
                    event("result", {"evidence": [proof(result="passed")]}, task="SECOND"))
        self.assertEqual(self.view("FIRST")["acceptance"][0]["result"], "failed")
        self.assertEqual(self.view("SECOND")["acceptance"][0]["result"], "passed")

    def test_successful_observation_refreshes_immutable_event_without_duplication(self):
        old_time = (CLOCK - dt.timedelta(hours=48)).isoformat()
        immutable = task()
        immutable["occurred_at"] = old_time
        old_snapshot = self.payload([immutable], 1)
        old_snapshot["source"]["as_of"] = old_time
        self.store.import_snapshot(old_snapshot)
        old_state = self.store.reconcile()
        self.assertIn("source_stale", {alert["code"] for alert in self.view()["alerts"]})
        observed = self.store.import_snapshot(self.payload([copy.deepcopy(immutable)], 2, 1))
        self.assertEqual(observed["operation"]["inserted"], 0)
        self.assertEqual(observed["operation"]["duplicates"], 1)
        self.assertEqual(observed["sources"][0]["freshness"], "current")
        self.assertEqual(observed["payload_hash"], old_state["payload_hash"])
        self.assertNotEqual(observed["state_hash"], old_state["state_hash"])
        current = self.view()
        self.assertEqual(current["source_provenance"][0]["freshness"], "current")
        self.assertEqual(current["source_provenance"][0]["last_verified_at"], stamp(1))
        self.assertEqual(current["source_provenance"][0]["observed_version"], 2)
        self.assertNotIn("source_stale", {alert["code"] for alert in current["alerts"]})
        self.assertTrue(current["ready"])
        self.assertEqual(current["last_event_at"], old_time, "an observation must not rewrite the immutable event")
        failed = self.payload([], 3, 2)
        failed["source"].update(status="error", error="Synthetic fetch unavailable")
        self.store.import_snapshot(failed)
        current = self.view()
        self.assertEqual(current["title"], immutable["data"]["title"])
        self.assertIn("source_error", {alert["code"] for alert in current["alerts"]})
        self.assertEqual(current["source_provenance"][0]["last_verified_at"], stamp(1))
        self.assertEqual(self.store.reconcile()["sources"][0]["last_success_at"], stamp(1))
        self.assertEqual(self.store.reconcile()["payload_hash"], observed["payload_hash"])

    def test_partial_observation_does_not_refresh_an_unobserved_task(self):
        old_time = (CLOCK - dt.timedelta(hours=48)).isoformat()
        first, second = task("FIRST"), task("SECOND")
        first["occurred_at"] = second["occurred_at"] = old_time
        initial = self.payload([first, second], 1)
        initial["source"]["as_of"] = old_time
        self.store.import_snapshot(initial)
        self.store.import_snapshot(self.payload([copy.deepcopy(second)], 2, 1))
        self.assertEqual(self.view("FIRST")["source_provenance"][0]["freshness"], "stale")
        self.assertEqual(self.view("SECOND")["source_provenance"][0]["freshness"], "current")


if __name__ == "__main__":
    unittest.main()
