"""Independent, synthetic acceptance tests for the work-manager contract.

No product runtime, user feedback, credentials, or actual cloud task records are
read. Run: python3 -m unittest discover -s geometry-web/work-manager -p test_acceptance.py -v
"""

from __future__ import annotations

import copy
import contextlib
import datetime as dt
import http.client
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
import unittest
from unittest import mock


HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from store import Store  # noqa: E402
from server import make_server  # noqa: E402


BASE = dt.datetime.now(dt.timezone.utc).replace(microsecond=0) - dt.timedelta(minutes=30)


def at(minutes=0, microseconds=0):
    return (BASE + dt.timedelta(minutes=minutes, microseconds=microseconds)).isoformat()


NOW = at(30)
AS_OF = at()
HEAD_A = "a" * 40
HEAD_B = "b" * 40


def event(task_id, kind, version, data, event_id=None):
    return {
        "event_id": event_id or f"qa:{task_id}:{kind}:{version}",
        "task_id": task_id,
        "kind": kind,
        "version": version,
        "occurred_at": AS_OF,
        "data": data,
    }


def task_event(task_id="QA-1", version=1, **updates):
    data = {
        "title": "合成驗收工作",
        "scope": "Only synthetic work-manager acceptance fixtures",
        "files": [f"synthetic/{task_id}.py"],
        "branch": "qa/synthetic",
        "dependencies": [],
        "approval_constraints": [],
        "required_acceptance": ["behavior"],
        "head_sha": HEAD_A,
    }
    data.update(updates)
    return event(task_id, "task", version, data)


def assignment_event(task_id="QA-1", version=1, owner="synthetic-owner", status="active", **updates):
    data = {"owner_thread": owner, "execution_status": status}
    data.update(updates)
    return event(task_id, "assignment", version, data)


def evidence(criterion="behavior", sha=HEAD_A, **updates):
    data = {
        "id": f"qa-evidence:{criterion}:{sha}",
        "criterion": criterion,
        "kind": "test",
        "timestamp": AS_OF,
        "sha": sha,
        "result": "passed",
        "url": "https://example.invalid/synthetic-evidence",
    }
    data.update(updates)
    return data


def pr(sha=HEAD_A, merged=False, review="pending", **updates):
    data = {
        "number": 1,
        "url": "https://example.invalid/synthetic/pull/1",
        "head_sha": sha,
        "merged": merged,
        "merged_head_sha": sha if merged else None,
        "review_state": review,
        "reviewed_sha": sha if review in {"approved", "changes_requested"} else None,
    }
    data.update(updates)
    return data


def result_event(task_id="QA-1", version=1, **data):
    return event(task_id, "result", version, data)


def snapshot(events, version=1, **source_updates):
    source = {
        "id": "qa-synthetic-source",
        "kind": "manual_snapshot",
        "version": version,
        "as_of": AS_OF,
        "status": "ok",
    }
    source.update(source_updates)
    return {"schema_version": 1, "source": source, "events": events}


class AcceptanceTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="geometry-work-manager-qa-")
        self.path = Path(self.tmp.name) / "state"
        self.store = Store(self.path)
        self.source_version = 0

    def tearDown(self):
        self.tmp.cleanup()

    def ingest(self, *events):
        self.source_version += 1
        return self.store.import_snapshot(snapshot(list(events), self.source_version))

    def state(self, store=None):
        return (store or self.store).reconcile(now=NOW)

    def task(self, task_id="QA-1", store=None):
        return next(t for t in self.state(store)["tasks"] if t["id"] == task_id)

    def codes(self, task_id="QA-1"):
        return {a["code"] for a in self.task(task_id)["alerts"]}

    def ready_ids(self):
        return {item if isinstance(item, str) else item["id"] for item in self.state()["ready"]}

    def cli(self, *arguments):
        completed = subprocess.run(
            [sys.executable, str(HERE / "cli.py"), "--data-dir", str(self.path), *arguments],
            capture_output=True,
            text=True,
            timeout=20,
            check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        return json.loads(completed.stdout)

    def test_repeating_snapshot_is_idempotent(self):
        payload = snapshot([task_event(), assignment_event()])
        self.store.import_snapshot(payload)
        before = self.state()
        self.store.import_snapshot(payload)
        after = self.state()
        self.assertEqual(len(after["tasks"]), 1)
        self.assertEqual(before["state_hash"], after["state_hash"])

    def test_conflicting_event_id_is_rejected_without_partial_write(self):
        original = task_event()
        self.ingest(original)
        before = self.state()["state_hash"]
        conflict = copy.deepcopy(original)
        conflict["data"]["title"] = "conflicting body"
        with self.assertRaises(ValueError):
            self.ingest(task_event("QA-2"), conflict)
        self.assertEqual(before, self.state()["state_hash"])
        self.assertEqual([t["id"] for t in self.state()["tasks"]], ["QA-1"])

    def test_invalid_batch_is_atomic_and_can_reopen(self):
        self.ingest(task_event())
        before = self.state()["state_hash"]
        invalid = assignment_event(status="invented-status")
        with self.assertRaises(ValueError):
            self.ingest(task_event("QA-2"), invalid)
        reopened = Store(self.path)
        self.assertEqual(before, self.state(reopened)["state_hash"])

    def test_concurrent_import_cannot_mix_source_and_event_snapshots(self):
        self.ingest(task_event())
        writer = Store(self.path)
        writer_done = threading.Event()
        writer_errors = []
        update = snapshot([task_event("QA-2")], id="qa-concurrent-source")

        def write():
            try:
                writer.import_snapshot(update)
            except Exception as error:
                writer_errors.append(error)
            finally:
                writer_done.set()

        thread = threading.Thread(target=write, daemon=True)
        original_db = self.store._db

        class ReadGate:
            def __init__(self, connection):
                self.connection = connection

            def __getattr__(self, name):
                return getattr(self.connection, name)

            def execute(self, sql, *parameters):
                if sql.startswith("SELECT * FROM events"):
                    # A real concurrent writer reaches commit between the two
                    # projection reads. A read transaction must preserve the
                    # original snapshot and release it before writer commit.
                    thread.start()
                    writer_done.wait(timeout=0.25)
                return self.connection.execute(sql, *parameters)

        @contextlib.contextmanager
        def gated_db():
            with original_db() as connection:
                yield ReadGate(connection)

        try:
            with mock.patch.object(self.store, "_db", gated_db):
                coherent = self.state()
            self.assertEqual([task["id"] for task in coherent["tasks"]], ["QA-1"])
        finally:
            if thread.ident:
                thread.join(timeout=5)
        self.assertFalse(thread.is_alive(), "concurrent import did not finish")
        self.assertEqual(writer_errors, [])
        self.assertEqual({task["id"] for task in self.state()["tasks"]}, {"QA-1", "QA-2"})

    def test_older_source_cannot_replace_newer_task(self):
        self.store.import_snapshot(snapshot([task_event(version=2, title="current")], 10))
        self.store.import_snapshot(snapshot([task_event(version=1, title="stale")], 9))
        self.assertEqual(self.task()["title"], "current")

    def test_older_task_event_cannot_regress_in_newer_snapshot(self):
        self.ingest(task_event(version=3, title="current"))
        self.ingest(task_event(version=2, title="stale"))
        self.assertEqual(self.task()["title"], "current")

    def test_same_version_different_event_is_rejected(self):
        self.ingest(task_event(title="current"))
        collision = task_event(title="ambiguous revision")
        collision["event_id"] = "qa:conflicting-revision"
        before = self.state()["state_hash"]
        with self.assertRaises(ValueError):
            self.ingest(collision)
        self.assertEqual(before, self.state()["state_hash"])

    def test_old_independent_source_cannot_overwrite_new_head(self):
        newest = task_event(title="newer observation", head_sha=HEAD_B)
        newest["occurred_at"] = at(10)
        self.store.import_snapshot(snapshot([newest], id="qa-new-observation", as_of=at(10)))
        older = task_event(title="older observation", head_sha=HEAD_A)
        older["event_id"] = "qa:old-source:task:1"
        self.store.import_snapshot(snapshot([older], id="qa-old-observation"))
        self.assertEqual(self.task()["head_sha"], HEAD_B)

    def test_subsecond_order_is_preserved_across_independent_sources(self):
        newer = task_event(head_sha=HEAD_B)
        newer["occurred_at"] = at(microseconds=900000)
        self.store.import_snapshot(snapshot([newer], id="qa-new-subsecond", as_of=at(1)))
        older = task_event(version=9, head_sha=HEAD_A)
        older["occurred_at"] = at(microseconds=100000)
        self.store.import_snapshot(snapshot([older], id="qa-old-subsecond", as_of=at(1)))
        self.assertEqual(self.task()["head_sha"], HEAD_B)

    def test_assignment_cannot_smuggle_approval_changes(self):
        self.ingest(task_event(approval_constraints=[{"action": "execute", "status": "denied"}]))
        before = self.state()["state_hash"]
        forged = assignment_event(approval_constraints=[{"action": "execute", "status": "granted"}])
        with self.assertRaises(ValueError):
            self.ingest(forged)
        self.assertEqual(before, self.state()["state_hash"])

    def test_changed_head_expires_prior_acceptance(self):
        self.ingest(task_event(), result_event(evidence=[evidence()], pr=pr(merged=True, review="approved")))
        self.assertEqual(self.task()["delivery_status"], "done")
        self.ingest(task_event(version=2, head_sha=HEAD_B))
        self.assertNotEqual(self.task()["delivery_status"], "done")
        self.assertIn("evidence_stale", self.codes())

    def test_merge_must_match_current_exact_head(self):
        self.ingest(task_event(head_sha=HEAD_B), result_event(evidence=[evidence(sha=HEAD_B)], pr=pr(sha=HEAD_B, merged=True, review="approved", merged_head_sha=HEAD_A)))
        self.assertNotEqual(self.task()["delivery_status"], "done")

    def test_unknown_head_cannot_validate_acceptance(self):
        self.ingest(task_event(head_sha=None), result_event(evidence=[evidence(sha=None)], pr=pr(sha=None, merged=True, review="approved")))
        self.assertNotEqual(self.task()["delivery_status"], "done")

    def test_all_required_acceptance_is_required(self):
        self.ingest(task_event(required_acceptance=["behavior", "integration"]), result_event(evidence=[evidence()], pr=pr(merged=True, review="approved")))
        self.assertNotEqual(self.task()["delivery_status"], "done")

    def test_empty_acceptance_is_unknown_not_done(self):
        self.ingest(task_event(required_acceptance=[]), result_event(evidence=[evidence()], pr=pr(merged=True, review="approved")))
        self.assertNotEqual(self.task()["delivery_status"], "done")

    def test_expired_evidence_is_not_current(self):
        self.ingest(task_event(), result_event(evidence=[evidence(expires_at=at(15))], pr=pr(merged=True, review="approved")))
        self.assertNotEqual(self.task()["delivery_status"], "done")
        self.assertIn("evidence_stale", self.codes())

    def test_later_failed_acceptance_cannot_hide_behind_old_pass(self):
        self.ingest(task_event(), result_event(evidence=[evidence()], pr=pr(merged=True, review="approved")))
        self.assertEqual(self.task()["delivery_status"], "done")
        failed = evidence(id="qa-later-failure", timestamp=at(15), result="failed")
        update = result_event(version=2, evidence=[failed])
        update["occurred_at"] = at(15)
        self.store.import_snapshot(snapshot([update], 2, as_of=at(15)))
        self.assertNotEqual(self.task()["delivery_status"], "done")
        self.assertEqual(self.task()["last_verified_evidence"]["result"], "failed")
        self.assertEqual(self.task()["last_verified_evidence"]["id"], "qa-later-failure")

    def test_ci_without_runner_or_steps_is_not_passed(self):
        for updates in ({"runner_id": 0, "steps": [{"name": "test", "conclusion": "success"}]}, {"runner_id": 123, "steps": []}):
            with self.subTest(updates=updates):
                version = self.source_version + 1
                self.ingest(task_event(version=version), result_event(version=version, evidence=[evidence(id=f"qa-ci-attempt-{version}", kind="ci", **updates)], pr=pr(merged=True, review="approved")))
                self.assertNotEqual(self.task()["delivery_status"], "done")
                self.assertIn("ci_not_run", self.codes())

    def test_malformed_ci_steps_cannot_certify_execution(self):
        malformed = [
            {"evidence": [evidence(id="qa-malformed-ci-proof", kind="ci", runner_id=123, steps=[{}])], "pr": pr(merged=True, review="approved")},
            {"evidence": [evidence(id="qa-malformed-pr-ci-proof")], "pr": pr(merged=True, review="approved", ci=[{"name": "synthetic-ci", "sha": HEAD_A, "status": "completed", "conclusion": "success", "runner_id": 123, "steps": [{}]}])},
        ]
        self.ingest(task_event())
        for data in malformed:
            with self.subTest(data=data):
                before = self.state()["state_hash"]
                version = self.source_version + 1
                try:
                    self.ingest(result_event(version=version, **data))
                except ValueError:
                    self.assertEqual(before, self.state()["state_hash"])
                self.assertNotEqual(self.task()["delivery_status"], "done")

    def test_future_source_or_result_cannot_claim_completion(self):
        for future_source in (True, False):
            with self.subTest(future_source=future_source):
                isolated = Store(Path(self.tmp.name) / f"future-{future_source}")
                result = result_event(evidence=[evidence()], pr=pr(merged=True, review="approved"))
                if not future_source:
                    result["occurred_at"] = at(1440)
                source = {"as_of": at(1440)} if future_source else {}
                isolated.import_snapshot(snapshot([task_event(), result], **source))
                self.assertNotEqual(self.task(store=isolated)["delivery_status"], "done")

    def test_blocked_is_not_done_even_with_merge_and_evidence(self):
        self.ingest(task_event(), assignment_event(status="blocked"), result_event(evidence=[evidence()], pr=pr(merged=True, review="approved")))
        self.assertEqual(self.task()["execution_status"], "blocked")
        self.assertNotEqual(self.task()["delivery_status"], "done")

    def test_stopped_executor_without_pr_is_a_delivery_gap(self):
        self.ingest(task_event(), assignment_event(status="stopped"))
        task = self.task()
        self.assertEqual(task["execution_status"], "stopped")
        self.assertNotEqual(task["delivery_status"], "done")
        self.assertIn("delivery_gap", self.codes())

    def test_stopped_executor_with_pr_stays_pending_review(self):
        self.ingest(task_event(), assignment_event(status="stopped"), result_event(evidence=[evidence()], pr=pr()))
        task = self.task()
        self.assertEqual(task["execution_status"], "stopped")
        self.assertEqual(task["delivery_status"], "awaiting_review")

    def test_finished_result_without_pr_still_has_delivery_gap(self):
        self.ingest(task_event(), assignment_event(), result_event(execution_status="finished", evidence=[evidence()]))
        task = self.task()
        self.assertEqual(task["execution_status"], "finished")
        self.assertNotEqual(task["delivery_status"], "done")
        self.assertIn("delivery_gap", self.codes())

    def test_started_owner_alone_is_never_a_delivery(self):
        self.ingest(task_event(), assignment_event())
        self.assertEqual(self.task()["execution_status"], "active")
        self.assertNotEqual(self.task()["delivery_status"], "done")

    def test_new_assignment_releases_old_reservation_and_keeps_history(self):
        self.ingest(task_event(), assignment_event(owner="owner-old", status="stopped", reserved=True))
        self.ingest(assignment_event(version=2, owner="owner-new", reserved=False))
        task = self.task()
        self.assertEqual(task["owner_thread"], "owner-new")
        self.assertEqual(task["execution_status"], "active")
        self.assertFalse(task.get("reserved", False))
        bundle_text = json.dumps(self.store.export_snapshot())
        self.assertIn("owner-old", bundle_text)
        self.assertIn("owner-new", bundle_text)

    def test_same_file_different_active_owners_are_conflicted(self):
        self.ingest(task_event("QA-1", files=["synthetic/shared.py"]), assignment_event("QA-1", owner="owner-one"), task_event("QA-2", files=["synthetic/shared.py"]), assignment_event("QA-2", owner="owner-two"))
        self.assertIn("file_conflict", self.codes("QA-1"))
        self.assertIn("file_conflict", self.codes("QA-2"))

    def test_directory_scope_overlap_is_conflicted(self):
        self.ingest(task_event("QA-1", files=["synthetic/directory/"]), assignment_event("QA-1", owner="owner-one"), task_event("QA-2", files=["synthetic/directory/child.py"]), assignment_event("QA-2", owner="owner-two"))
        self.assertIn("file_conflict", self.codes("QA-1"))
        self.assertIn("file_conflict", self.codes("QA-2"))

    def test_dependency_cycle_is_visible_and_not_ready(self):
        self.ingest(task_event("QA-1", dependencies=["QA-2"]), task_event("QA-2", dependencies=["QA-1"]))
        for task_id in ("QA-1", "QA-2"):
            self.assertIn("dependency_cycle", self.codes(task_id))
            self.assertNotIn(task_id, self.ready_ids())

    def test_approval_constraint_remains_a_gate(self):
        self.ingest(task_event(approval_constraints=[{"action": "execute", "status": "denied", "reason": "Synthetic explicit hold"}]), assignment_event(status="stopped"))
        self.assertIn("approval_required", self.codes())
        self.assertEqual(self.task()["approval_constraints"][0]["status"], "denied")
        self.assertNotIn("QA-1", self.ready_ids())

    def test_delivery_does_not_grant_publication_permission(self):
        self.ingest(task_event(approval_constraints=[{"action": "publish", "status": "denied", "reason": "Synthetic explicit hold"}]), result_event(evidence=[evidence()], pr=pr(merged=True, review="approved")))
        task = self.task()
        self.assertEqual(task["approval_constraints"][0]["status"], "denied")
        self.assertNotEqual(task.get("next_action"), "publish")

    def test_missing_owner_and_future_schedule_are_visible(self):
        self.ingest(task_event(not_before=at(1440)), assignment_event(owner=None, status="unassigned"))
        self.assertIn("owner_missing", self.codes())
        self.assertIn("not_before", self.codes())
        self.assertNotIn("QA-1", self.ready_ids())

    def test_failed_source_fetch_keeps_tasks_and_reports_error(self):
        self.ingest(task_event())
        self.store.import_snapshot(snapshot([], 2, status="error", error="Synthetic unavailable source"))
        self.assertEqual(self.task()["title"], "合成驗收工作")
        codes = {a["code"] for a in self.state().get("alerts", [])}
        codes.update(self.codes())
        self.assertIn("source_error", codes)

    def test_unknown_schema_and_kind_are_rejected_without_mutation(self):
        self.ingest(task_event())
        before = self.state()["state_hash"]
        bad_schema = snapshot([task_event("QA-2")], 2)
        bad_schema["schema_version"] = 999
        bad_source = snapshot([task_event("QA-2")], 2, kind="invented")
        for payload in (bad_schema, bad_source):
            with self.subTest(payload=payload):
                with self.assertRaises(ValueError):
                    self.store.import_snapshot(payload)
                self.assertEqual(before, self.state()["state_hash"])

    def test_export_restore_roundtrip_and_checksum_tamper(self):
        self.ingest(task_event(), assignment_event())
        bundle = self.store.export_snapshot()
        restored = Store(Path(self.tmp.name) / "restored")
        restored.restore(copy.deepcopy(bundle))
        self.assertEqual(self.state()["state_hash"], self.state(restored)["state_hash"])
        altered = copy.deepcopy(bundle)
        altered["checksum"] = "0" * 64
        with self.assertRaises(ValueError):
            restored.restore(altered)
        self.assertEqual(self.state()["state_hash"], self.state(restored)["state_hash"])

    def test_older_backup_cannot_rollback_nonempty_store(self):
        self.ingest(task_event())
        old_backup = self.store.export_snapshot()
        self.ingest(task_event(version=2, head_sha=HEAD_B, title="new head"))
        before = self.state()["state_hash"]
        with self.assertRaises(ValueError):
            self.store.restore(old_backup)
        self.assertEqual(before, self.state()["state_hash"])
        self.assertEqual(self.task()["head_sha"], HEAD_B)

    def test_cli_reconcile_uses_same_projection_hash(self):
        self.ingest(task_event())
        output = self.cli("reconcile")
        self.assertEqual(output["state_hash"], self.store.reconcile()["state_hash"])

    def test_cli_records_assignment_idempotently(self):
        self.ingest(task_event())
        payload = snapshot([assignment_event()], 2)
        input_file = Path(self.tmp.name) / "synthetic-assignment.json"
        input_file.write_text(json.dumps(payload), encoding="utf-8")
        self.cli("record-assignment", str(input_file))
        before = self.state()["state_hash"]
        self.cli("record-assignment", str(input_file))
        self.assertEqual(before, self.state()["state_hash"])
        self.assertEqual(self.task()["owner_thread"], "synthetic-owner")

    def test_cli_records_result_without_confusing_finished_with_done(self):
        self.ingest(task_event(), assignment_event())
        payload = snapshot([result_event(execution_status="finished", evidence=[evidence()], pr=pr())], 2)
        input_file = Path(self.tmp.name) / "synthetic-result.json"
        input_file.write_text(json.dumps(payload), encoding="utf-8")
        self.cli("record-result", str(input_file))
        task = self.task()
        self.assertEqual(task["execution_status"], "finished")
        self.assertEqual(task["delivery_status"], "awaiting_review")


class ServerAcceptanceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory(prefix="geometry-work-manager-http-qa-")
        cls.path = Path(cls.tmp.name) / "state"
        store = Store(cls.path)
        store.import_snapshot(snapshot([task_event()]))
        close = getattr(store, "close", None)
        if close:
            close()
        cls.server = make_server(cls.path, port=0)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(timeout=5)
        cls.tmp.cleanup()

    def request(self, method="GET", path="/api/state", headers=None):
        connection = http.client.HTTPConnection("127.0.0.1", self.server.server_port, timeout=5)
        try:
            connection.request(method, path, headers=headers or {})
            response = connection.getresponse()
            return response.status, dict(response.getheaders()), response.read()
        finally:
            connection.close()

    def test_state_matches_local_projection_and_has_private_headers(self):
        status, headers, body = self.request()
        self.assertEqual(status, 200)
        served = json.loads(body)
        store = Store(self.path)
        try:
            self.assertEqual(served["state_hash"], store.reconcile()["state_hash"])
        finally:
            close = getattr(store, "close", None)
            if close:
                close()
        self.assertEqual(headers["Cache-Control"], "no-store")
        self.assertEqual(headers["X-Content-Type-Options"], "nosniff")
        self.assertEqual(headers["X-Frame-Options"], "DENY")
        self.assertIn("script-src 'self'", headers["Content-Security-Policy"])
        self.assertNotIn("Access-Control-Allow-Origin", headers)

    def test_changed_server_code_is_not_misreported_as_current(self):
        with mock.patch("server.code_fingerprint", return_value="synthetic-changed-code"):
            self.assertEqual(self.request()[0], 503)
            self.assertEqual(self.request(path="/api/export")[0], 503)
        status, _, body = self.request()
        self.assertEqual(status, 200)
        self.assertIn("state_hash", json.loads(body))

    def test_cross_origin_and_foreign_hosts_are_rejected(self):
        for headers in ({"Host": "foreign.invalid"}, {"Origin": "https://foreign.invalid"}, {"Sec-Fetch-Site": "cross-site"}, {"Sec-Fetch-Site": "same-site"}):
            with self.subTest(headers=headers):
                self.assertEqual(self.request(headers=headers)[0], 403)

    def test_http_api_cannot_mutate(self):
        before = json.loads(self.request()[2])["state_hash"]
        for method in ("POST", "PUT", "PATCH", "DELETE"):
            with self.subTest(method=method):
                self.assertEqual(self.request(method=method)[0], 405)
        self.assertEqual(json.loads(self.request()[2])["state_hash"], before)

    def test_only_whitelisted_files_are_served(self):
        for path in ("/store.py", "/.local/state.sqlite3", "/../schema.json", "/%2e%2e/AGENTS.md", "/api/mutate", "/api/state/extra"):
            with self.subTest(path=path):
                self.assertEqual(self.request(path=path)[0], 404)

    def test_public_bind_is_rejected(self):
        for host in ("0.0.0.0", "::", "192.0.2.1", "foreign.invalid"):
            with self.subTest(host=host):
                with self.assertRaises(ValueError):
                    make_server(self.path, host=host, port=0)

    def test_backup_endpoint_is_same_origin_download(self):
        status, headers, body = self.request(path="/api/export")
        self.assertEqual(status, 200)
        self.assertIn("attachment", headers["Content-Disposition"])
        self.assertIn("checksum", json.loads(body))


if __name__ == "__main__":
    unittest.main()
