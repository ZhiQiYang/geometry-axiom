"""Synthetic read-observation adaptation; never calls GitHub or a live store."""
import copy
import datetime as dt
from pathlib import Path
import sqlite3
import tempfile
import unittest

from adapter import adapt_observation
from store import Store, ValidationError

HEAD, MAIN = "a" * 40, "b" * 40
NOW = dt.datetime.now(dt.timezone.utc) - dt.timedelta(minutes=10)


def stamp(minutes=0):
    return (NOW + dt.timedelta(minutes=minutes)).isoformat()


def observation():
    prefix = "https://github.com/synthetic/queue"
    return {
        "format": "geometry-github-read-observation/1", "repository": "synthetic/queue",
        "observed_at": stamp(), "mode": "read_only_connector_snapshot",
        "main": {"sha": MAIN, "url": f"{prefix}/commit/{MAIN}"},
        "counts": {"open_issues": 1, "open_prs": 1},
        "issues": [{"task_id": "gh:issue:1", "number": 1, "title": "Synthetic issue", "state": "open", "updated_at": stamp(-1), "url": prefix + "/issues/1"}],
        "pull_requests": [{"task_id": "gh:pr:2", "number": 2, "title": "Synthetic PR", "state": "open", "draft": True, "head_sha": HEAD,
                           "base_ref": "main", "base_sha": MAIN, "author": "synthetic", "updated_at": stamp(-1), "url": prefix + "/pull/2"}],
        "exact_head_ci": [{"pr_number": number, "head_sha": sha, "runs": [{"id": run_id, "head_sha": sha, "status": "completed", "conclusion": "failure", "attempt": 1,
            "updated_at": stamp(-1), "url": f"{prefix}/actions/runs/{run_id}", "jobs": [{"id": run_id + 100, "name": "synthetic-job", "status": "completed", "conclusion": "failure", "runner_id": 0, "steps": []}]}]}
            for number, sha, run_id in [(None, MAIN, 3), (2, HEAD, 4)]],
    }


class AdapterTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="work-adapter-")
        self.store = Store(Path(self.temp.name) / "state")
        self.raw = observation()
        self.store.import_snapshot({"schema_version": 1,
            "source": {"id": "synthetic-existing", "kind": "operator", "version": 1, "as_of": stamp(-2), "status": "ok"},
            "events": [
                {"event_id": "synthetic-task", "task_id": "EXISTING-SLICE", "kind": "task", "version": 1, "occurred_at": stamp(-2), "data": {
                    "title": "Existing bounded scope", "scope": "Synthetic bounded files", "files": ["synthetic/file.py"], "head_sha": HEAD,
                    "refs": [{"kind": "issue", "number": 1, "url": self.raw["issues"][0]["url"]}, {"kind": "pr", "number": 2, "url": self.raw["pull_requests"][0]["url"]}],
                    "approval_constraints": [{"action": "merge", "status": "required"}], "required_acceptance": ["behavior"]}},
                {"event_id": "synthetic-assignment", "task_id": "EXISTING-SLICE", "kind": "assignment", "version": 1, "occurred_at": stamp(-2), "data": {"owner_thread": "synthetic-owner", "execution_status": "active"}},
                {"event_id": "synthetic-result", "task_id": "EXISTING-SLICE", "kind": "result", "version": 1, "occurred_at": stamp(-2), "data": {"pr": {
                    "number": 2, "url": self.raw["pull_requests"][0]["url"], "head_sha": HEAD, "merged": False, "draft": True, "review_state": "approved", "reviewed_sha": HEAD},
                    "evidence": [{"id": "synthetic-proof", "criterion": "behavior", "kind": "test", "timestamp": stamp(-2), "sha": HEAD, "result": "passed"}]}}
            ]})

    def tearDown(self):
        self.temp.cleanup()

    def count(self):
        with sqlite3.connect(self.store.path) as database:
            return database.execute("SELECT COUNT(*) FROM events").fetchone()[0]

    def test_maps_existing_slice_preserves_authority_and_ci_is_unexecuted(self):
        before = self.store.path.read_bytes()
        snapshot, report = adapt_observation(self.store, self.raw)
        self.assertEqual(before, self.store.path.read_bytes(), "adaptation must not write the ledger")
        self.assertEqual({event["task_id"] for event in snapshot["events"]}, {"EXISTING-SLICE"})
        self.assertEqual(len(report["mapped_existing_tasks"]), 2)
        state = self.store.import_snapshot(snapshot)
        self.assertEqual(len(state["tasks"]), 1)
        task = state["tasks"][0]
        self.assertEqual(task["execution_status"], "active")
        self.assertEqual(task["owner_thread"], "synthetic-owner")
        self.assertEqual(task["approval_constraints"][0]["status"], "required")
        self.assertEqual(task["pr"]["effective_review_state"], "approved")
        self.assertEqual(task["evidence"][0]["id"], "synthetic-proof")
        self.assertEqual(task["ci"][0]["effective_result"], "not_run")
        source = next(source for source in state["sources"] if source["id"] == "github-read-observation")
        self.assertEqual(source["ci"][0]["effective_result"], "not_run")

    def test_same_observation_idempotent_and_new_timestamp_refreshes_without_events(self):
        snapshot, _ = adapt_observation(self.store, self.raw)
        first = self.store.import_snapshot(snapshot)
        count = self.count()
        repeated, _ = adapt_observation(self.store, self.raw)
        self.assertEqual(repeated, snapshot)
        second = self.store.import_snapshot(repeated)
        self.assertEqual(first["state_hash"], second["state_hash"])
        self.assertEqual(self.count(), count)
        later = copy.deepcopy(self.raw)
        later["observed_at"] = stamp(1)
        refreshed, _ = adapt_observation(self.store, later)
        self.assertEqual(refreshed["events"], snapshot["events"])
        third = self.store.import_snapshot(refreshed)
        self.assertEqual(self.count(), count)
        self.assertEqual(first["payload_hash"], third["payload_hash"])
        self.assertNotEqual(first["state_hash"], third["state_hash"])
        provenance = next(p for p in third["tasks"][0]["source_provenance"] if p["id"] == "github-read-observation")
        self.assertEqual(provenance["last_verified_at"], stamp(1))

    def test_new_head_cannot_inherit_previous_review_validity(self):
        changed = copy.deepcopy(self.raw)
        changed["pull_requests"][0]["head_sha"] = "c" * 40
        changed["exact_head_ci"][1]["head_sha"] = "c" * 40
        changed["exact_head_ci"][1]["runs"][0]["head_sha"] = "c" * 40
        snapshot, _ = adapt_observation(self.store, changed)
        task = self.store.import_snapshot(snapshot)["tasks"][0]
        self.assertEqual(task["pr"]["review_state"], "approved")
        self.assertEqual(task["pr"]["reviewed_sha"], HEAD)
        self.assertEqual(task["pr"]["effective_review_state"], "stale")

    def test_malformed_nested_ci_rejected_without_changing_original_bytes(self):
        bad = copy.deepcopy(self.raw)
        bad["exact_head_ci"][1]["runs"][0]["jobs"][0]["steps"] = [{"name": "synthetic", "status": "completed", "conclusion": {"bad": "shape"}}]
        before = self.store.path.read_bytes()
        with self.assertRaises(ValidationError):
            adapt_observation(self.store, bad)
        self.assertEqual(before, self.store.path.read_bytes())

    def test_bad_counts_reference_and_head_rejected(self):
        mutations = [lambda v: v["counts"].update(open_issues=2),
                     lambda v: v["issues"][0].update(url="https://github.com/other/repo/issues/1"),
                     lambda v: v["exact_head_ci"][1].update(head_sha="d" * 40)]
        for mutation in mutations:
            bad = copy.deepcopy(self.raw)
            mutation(bad)
            before = self.store.path.read_bytes()
            with self.assertRaises(ValidationError):
                adapt_observation(self.store, bad)
            self.assertEqual(before, self.store.path.read_bytes())

    def test_missing_items_do_not_delete_registered_coverage(self):
        snapshot, _ = adapt_observation(self.store, self.raw)
        self.store.import_snapshot(snapshot)
        partial = copy.deepcopy(self.raw)
        partial.update(observed_at=stamp(1), issues=[], pull_requests=[], counts={"open_issues": 0, "open_prs": 0})
        partial["exact_head_ci"] = [partial["exact_head_ci"][0]]
        snapshot, _ = adapt_observation(self.store, partial)
        state = self.store.import_snapshot(snapshot)
        self.assertEqual(state["coverage"]["count"], 1)
        self.assertEqual(state["coverage"]["pr_count"], 1)
        self.assertEqual(len(state["tasks"]), 1)

    def test_new_metadata_does_not_invent_owner_scope_or_review(self):
        empty = Store(Path(self.temp.name) / "empty")
        snapshot, _ = adapt_observation(empty, self.raw)
        tasks = empty.import_snapshot(snapshot)["tasks"]
        self.assertTrue(all(task["execution_status"] == "unknown" and task["owner_thread"] is None and not task["scope"] for task in tasks))
        pr = next(task for task in tasks if task["id"] == "gh:pr:2")["pr"]
        self.assertEqual(pr["effective_review_state"], "unknown")

    def test_older_observation_rejected_without_writes(self):
        snapshot, _ = adapt_observation(self.store, self.raw)
        self.store.import_snapshot(snapshot)
        older = copy.deepcopy(self.raw)
        older["observed_at"] = stamp(-1)
        before = self.store.path.read_bytes()
        with self.assertRaises(ValidationError):
            adapt_observation(self.store, older)
        self.assertEqual(before, self.store.path.read_bytes())


if __name__ == "__main__":
    unittest.main()
