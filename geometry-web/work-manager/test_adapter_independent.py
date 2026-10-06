"""Independent adapter boundaries. Synthetic repositories and temp ledgers only."""

import datetime as dt
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from adapter import adapt_observation
from store import Store


NOW = dt.datetime.now(dt.timezone.utc).replace(microsecond=0)
HEAD, BASE = "a" * 40, "b" * 40
REPO = "synthetic-adapter-qa/alpha"
NUMBER = 701


def stamp(minutes=0):
    return (NOW - dt.timedelta(minutes=30) + dt.timedelta(minutes=minutes)).isoformat()


def pr_url(repository=REPO):
    return f"https://github.com/{repository}/pull/{NUMBER}"


def observation(repository=REPO, minutes=5, runs=None):
    return {"format": "geometry-github-read-observation/1",
            "repository": repository, "observed_at": stamp(minutes),
            "mode": "read_only_connector_snapshot",
            "main": {"sha": BASE, "url": f"https://github.com/{repository}/commit/{BASE}"},
            "counts": {"open_issues": 0, "open_prs": 1},
            "issues": [], "pull_requests": [{"task_id": f"gh:pr:{NUMBER}",
                "number": NUMBER, "title": "Synthetic adapter PR", "state": "open",
                "updated_at": stamp(), "url": pr_url(repository), "draft": False,
                "head_sha": HEAD, "base_ref": "main", "base_sha": BASE,
                "author": "synthetic-author"}],
            "exact_head_ci": ([] if runs is None else [
                {"pr_number": NUMBER, "head_sha": HEAD, "runs": runs}])}


def run(identity=9001, result="success", minutes=1, jobs=None):
    if jobs is None:
        jobs = [{"id": identity + 100, "name": "test", "status": "completed",
                 "conclusion": result, "runner_id": 123,
                 "steps": [{"name": "execute", "status": "completed", "conclusion": result}]}]
    return {"id": identity, "head_sha": HEAD, "status": "completed",
            "conclusion": result, "attempt": 1, "updated_at": stamp(minutes),
            "url": f"https://github.com/{REPO}/actions/runs/{identity}", "jobs": jobs}


class AdapterIndependentTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="geometry-adapter-independent-")
        self.store = Store(Path(self.temp.name) / "state")
        self.clock = patch("store.utc_now", return_value=NOW)
        self.clock.start()

    def tearDown(self):
        self.clock.stop()
        self.temp.cleanup()

    def seed(self, task_id="ADAPTER-LEAF", owner=None, constraints=None):
        def event(kind, data):
            return {"event_id": f"synthetic-adapter:{task_id}:{kind}", "task_id": task_id,
                    "kind": kind, "version": 1, "occurred_at": stamp(), "data": data}

        events = [event("task", {"title": "Owned synthetic work", "scope": "Synthetic adapter QA",
                    "files": [f"synthetic/{task_id.replace(':', '-')}.py"], "branch": "qa/synthetic-adapter",
                    "required_acceptance": ["behavior"], "dependencies": [],
                    "approval_constraints": constraints or [], "head_sha": HEAD,
                    "refs": [{"kind": "pr", "number": NUMBER, "url": pr_url()}]}),
                  event("result", {"pr": {"number": NUMBER, "url": pr_url(), "head_sha": HEAD,
                    "merged": False, "draft": False, "review_state": "approved", "reviewed_sha": HEAD},
                    "evidence": [{"id": "adapter-proof", "criterion": "behavior", "kind": "test",
                                  "timestamp": stamp(), "sha": HEAD, "result": "passed"}]})]
        if owner:
            events.append(event("assignment", {"owner_thread": owner, "execution_status": "active"}))
        self.store.import_snapshot({"schema_version": 1,
            "source": {"id": "synthetic-adapter-ledger", "kind": "operator", "version": 1,
                       "as_of": stamp(), "status": "ok"}, "events": events})
        return task_id

    def task(self, task_id="ADAPTER-LEAF"):
        return next(row for row in self.store.reconcile()["tasks"] if row["id"] == task_id)

    def ingest_observation(self, value, source_id="synthetic-observation"):
        snapshot, report = adapt_observation(self.store, value, source_id)
        self.store.import_snapshot(snapshot)
        return snapshot, report

    def complete_action(self, task_id="ADAPTER-LEAF"):
        current = self.task(task_id)
        receipt = {"action": current["next_action_code"], "input_pin": current["next_action_pin"],
                   "timestamp": stamp(1), "summary": "Synthetic bounded review completed"}
        self.store.import_snapshot({"schema_version": 1,
            "source": {"id": "synthetic-adapter-receipt", "kind": "operator", "version": 1,
                       "as_of": stamp(1), "status": "ok"},
            "events": [{"event_id": "synthetic-adapter:receipt", "task_id": task_id,
                        "kind": "result", "version": 1, "occurred_at": stamp(1),
                        "data": {"completed_actions": [receipt]}}]})
        return receipt

    def test_repeated_observation_refreshes_same_events_and_preserves_receipt(self):
        self.seed()
        receipt = self.complete_action()
        before = self.task()
        snapshot, report = self.ingest_observation(observation())
        first = self.task()
        self.assertEqual(report["mapped_existing_tasks"][0]["existing_task_id"], "ADAPTER-LEAF")
        self.assertEqual(first["next_action_pin"], before["next_action_pin"])
        self.assertEqual(first["completed_actions"], [receipt])
        self.assertTrue(first["next_action_completed"])
        second, _ = self.ingest_observation(observation(minutes=6))
        refreshed = self.task()
        self.assertEqual(snapshot["events"], second["events"])
        self.assertEqual(refreshed["next_action_pin"], before["next_action_pin"])
        self.assertFalse(refreshed["ready"])
        all_events = [event for part in self.store.export_snapshot()["snapshots"] for event in part["events"]]
        self.assertEqual(len({event["event_id"] for event in all_events}), 4)
        observed = next(source for source in refreshed["source_provenance"] if source["id"] == "synthetic-observation")
        self.assertEqual(observed["last_verified_at"], stamp(6))
        third, _ = adapt_observation(self.store, observation(minutes=6), "synthetic-observation")
        self.assertEqual(third, second, "same observed input must reuse its source version too")

    def test_alias_preserves_owner_review_approval_and_scope(self):
        constraints = [{"action": "publish", "status": "denied", "scope": "action"}]
        self.seed(owner="synthetic-owner", constraints=constraints)
        before = self.task()
        db_bytes = self.store.path.read_bytes()
        snapshot, report = adapt_observation(self.store, observation(), "synthetic-observation")
        self.assertFalse(report["database_modified"])
        self.assertEqual(self.store.path.read_bytes(), db_bytes)
        self.store.import_snapshot(snapshot)
        state = self.store.reconcile()
        self.assertEqual([task["id"] for task in state["tasks"]], ["ADAPTER-LEAF"])
        current = self.task()
        for key in ("owner_thread", "execution_status", "scope", "files", "branch", "approval_constraints",
                    "required_acceptance", "evidence", "assignment_history", "next_action_pin"):
            self.assertEqual(current[key], before[key], key)
        self.assertEqual(current["pr"]["reviewed_sha"], HEAD)
        self.assertEqual(current["pr"]["effective_review_state"], "approved")
        self.assertFalse(current["ready"])

    def test_partial_observation_keeps_unseen_work_and_inventory(self):
        self.seed()
        self.ingest_observation(observation())
        before = self.task()
        empty = observation(minutes=6)
        empty["pull_requests"] = []
        empty["counts"]["open_prs"] = 0
        self.ingest_observation(empty)
        state = self.store.reconcile()
        current = self.task()
        for key in ("pr", "evidence", "next_action_pin", "delivery_status"):
            self.assertEqual(current[key], before[key])
        self.assertEqual(state["coverage"]["pr_count"], 1)

    def test_review_change_does_not_reissue_unchanged_observed_metadata(self):
        self.seed()
        first, _ = self.ingest_observation(observation())
        changed_pr = {key: self.task()["pr"][key] for key in
                      ("number", "url", "head_sha", "merged", "draft", "review_state", "reviewed_sha")}
        changed_pr.update(review_state="changes_requested", reviewed_sha=HEAD)
        self.store.import_snapshot({"schema_version": 1,
            "source": {"id": "synthetic-independent-review", "kind": "operator", "version": 1,
                       "as_of": stamp(6), "status": "ok"},
            "events": [{"event_id": "synthetic-adapter:independent-review", "task_id": "ADAPTER-LEAF",
                        "kind": "result", "version": 1, "occurred_at": stamp(6),
                        "data": {"pr": changed_pr}}]})
        second, _ = self.ingest_observation(observation())
        self.assertEqual(second["events"], first["events"],
                         "unchanged observed metadata cannot copy a later independent review")
        self.assertEqual(self.task()["pr"]["review_state"], "changes_requested")
        self.assertEqual(self.task()["pr"]["effective_review_state"], "changes_requested")

    def test_multiple_issue_aliases_to_one_task_do_not_duplicate_events(self):
        self.seed()
        refs = self.task()["refs"] + [{"kind": "issue", "number": number,
                "url": f"https://github.com/{REPO}/issues/{number}"} for number in (501, 502)]
        self.store.import_snapshot({"schema_version": 1,
            "source": {"id": "synthetic-adapter-ledger", "kind": "operator", "version": 2,
                       "as_of": stamp(1), "status": "ok"},
            "events": [{"event_id": "synthetic-adapter:many-issues", "task_id": "ADAPTER-LEAF",
                        "kind": "task", "version": 2, "occurred_at": stamp(1),
                        "data": {"refs": refs}}]})
        value = observation()
        value["issues"] = [{"task_id": f"gh:issue:{number}", "number": number,
                            "title": f"Synthetic issue {number}", "state": "open", "updated_at": stamp(),
                            "url": f"https://github.com/{REPO}/issues/{number}"} for number in (501, 502)]
        value["counts"]["open_issues"] = 2
        snapshot, _ = self.ingest_observation(value)
        identities = [event["event_id"] for event in snapshot["events"]]
        self.assertEqual(len(identities), len(set(identities)))
        state = self.store.reconcile()
        self.assertEqual(len(state["tasks"]), 1)
        self.assertEqual(state["coverage"]["count"], 2)
        self.assertTrue(all(row["task_ids"] == ["ADAPTER-LEAF"]
                            for row in state["coverage"]["repositories"][0]["issues"]))

    def test_invalid_input_is_rejected_without_touching_database(self):
        self.seed()
        cases = []
        wrong_sha = observation(runs=[run()])
        wrong_sha["exact_head_ci"][0]["runs"][0]["head_sha"] = BASE
        cases.append(wrong_sha)
        malformed = observation(runs=[run()])
        malformed["exact_head_ci"][0]["runs"][0]["jobs"][0]["steps"][0]["conclusion"] = {"bad": "shape"}
        cases.append(malformed)
        wrong_count = observation()
        wrong_count["counts"]["open_prs"] = 2
        cases.append(wrong_count)
        for value in cases:
            with self.subTest(value=cases.index(value)):
                before = self.store.path.read_bytes()
                with self.assertRaises(ValueError):
                    adapt_observation(self.store, value)
                self.assertEqual(self.store.path.read_bytes(), before)

    def test_same_number_in_other_repository_cannot_overwrite_existing_task(self):
        self.seed(task_id=f"gh:pr:{NUMBER}")
        before = self.store.path.read_bytes()
        with self.assertRaises(ValueError):
            adapt_observation(self.store, observation(repository="synthetic-adapter-qa/beta"))
        self.assertEqual(self.store.path.read_bytes(), before)
        self.assertEqual(self.task(f"gh:pr:{NUMBER}")["pr"]["url"], pr_url())

    def test_canonical_task_with_only_another_pr_reference_is_not_rebound(self):
        identity = self.seed(task_id=f"gh:pr:{NUMBER}")
        other_pr = {"number": 799, "url": f"https://github.com/{REPO}/pull/799", "head_sha": HEAD,
                    "merged": False, "draft": False, "review_state": "approved", "reviewed_sha": HEAD}
        self.store.import_snapshot({"schema_version": 1,
            "source": {"id": "synthetic-adapter-ledger", "kind": "operator", "version": 2,
                       "as_of": stamp(1), "status": "ok"},
            "events": [{"event_id": f"synthetic-adapter:other-reference:{kind}", "task_id": identity,
                        "kind": kind, "version": 2, "occurred_at": stamp(1), "data": data}
                       for kind, data in (("task", {"refs": []}), ("result", {"pr": other_pr}))]})
        before = self.store.path.read_bytes()
        with self.assertRaises(ValueError):
            adapt_observation(self.store, observation())
        self.assertEqual(self.store.path.read_bytes(), before)
        self.assertEqual(self.task(identity)["pr"]["number"], 799)

    def test_older_remote_pr_head_does_not_roll_back_newer_task_head(self):
        self.seed()
        self.store.import_snapshot({"schema_version": 1,
            "source": {"id": "synthetic-adapter-ledger", "kind": "operator", "version": 2,
                       "as_of": stamp(2), "status": "ok"},
            "events": [{"event_id": "synthetic-adapter:new-head", "task_id": "ADAPTER-LEAF",
                        "kind": "task", "version": 2, "occurred_at": stamp(2),
                        "data": {"head_sha": BASE}}]})
        self.assertEqual(self.task()["pr"]["effective_review_state"], "stale")
        self.ingest_observation(observation(minutes=5))
        current = self.task()
        self.assertEqual(current["head_sha"], BASE, "poll time is not a new PR-head revision")
        self.assertEqual(current["pr"]["head_sha"], HEAD)
        self.assertEqual(current["pr"]["effective_review_state"], "stale")
        self.assertNotEqual(current["next_action_code"], "review_integration")

    def test_newer_remote_timestamp_cannot_replace_explicit_work_head(self):
        self.seed()
        self.store.import_snapshot({"schema_version": 1,
            "source": {"id": "synthetic-adapter-ledger", "kind": "operator", "version": 2,
                       "as_of": stamp(2), "status": "ok"},
            "events": [{"event_id": "synthetic-adapter:explicit-work-head", "task_id": "ADAPTER-LEAF",
                        "kind": "task", "version": 2, "occurred_at": stamp(2),
                        "data": {"head_sha": BASE}}]})
        value = observation(minutes=5)
        value["pull_requests"][0]["updated_at"] = stamp(3)
        self.ingest_observation(value)
        current = self.task()
        self.assertEqual(current["head_sha"], BASE,
                         "newer remote metadata still describes the published PR, not the explicit work head")
        self.assertEqual(current["pr"]["head_sha"], HEAD)
        self.assertEqual(current["pr"]["effective_review_state"], "stale")
        self.assertNotEqual(current["next_action_code"], "review_integration")

    def test_same_job_name_in_distinct_runs_does_not_hide_failure(self):
        self.seed()
        self.ingest_observation(observation(runs=[run(9001, "failure", 1), run(9002, "success", 2)]))
        task = self.task()
        self.assertIn("failed", {job["effective_result"] for job in task["ci"]})
        self.assertEqual(task["delivery_status"], "verification_pending")
        self.assertNotEqual(task["next_action_code"], "review_integration")

    def test_observed_run_without_jobs_is_not_empty_success(self):
        self.seed()
        self.ingest_observation(observation(runs=[run(jobs=[])]))
        task = self.task()
        execution = task["ci"] + task.get("ci_runs", [])
        self.assertTrue(execution, "an observed run with no execution detail must stay visible")
        self.assertTrue(any(item["effective_result"] != "passed" for item in execution))
        self.assertEqual(task["delivery_status"], "verification_pending")

    def test_failed_run_cannot_be_certified_by_only_its_passing_jobs(self):
        self.seed()
        observed_run = run()
        observed_run["conclusion"] = "failure"
        self.ingest_observation(observation(runs=[observed_run]))
        task = self.task()
        execution = task["ci"] + task.get("ci_runs", [])
        self.assertTrue(any(item["effective_result"] != "passed" for item in execution))
        self.assertEqual(task["delivery_status"], "verification_pending")


if __name__ == "__main__":
    unittest.main()
