"""Focused operator-boundary tests. All records and paths are synthetic."""
import copy
import datetime as dt
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from store import Store, ValidationError, atomic_write_json

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
            "head_sha": HEAD, "merged_head_sha": HEAD, "merged": True, "review_state": "approved"}})

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
