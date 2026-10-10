"""Independent inventory/umbrella coverage checks, using synthetic repositories."""

import copy
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from store import Store
from test_review_regressions import CLOCK, HEAD_A, event, proof, pull_request, stamp, task


REPO_A = "synthetic-work-qa/alpha"
REPO_B = "synthetic-work-qa/beta"


def issue_row(number, task_ids, repository=REPO_A, **updates):
    row = {"number": number, "url": f"https://github.com/{repository}/issues/{number}",
           "task_ids": task_ids, "title": f"Synthetic issue {number}"}
    row.update(updates)
    return row


def pr_row(number, task_ids, repository=REPO_A, **updates):
    row = {"number": number, "url": f"https://github.com/{repository}/pull/{number}",
           "task_ids": task_ids, "title": f"Synthetic PR {number}"}
    row.update(updates)
    return row


class CoverageTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="geometry-coverage-qa-")
        self.store = Store(Path(self.temp.name) / "state")
        self.clock = patch("store.utc_now", return_value=CLOCK)
        self.clock.start()

    def tearDown(self):
        self.clock.stop()
        self.temp.cleanup()

    def payload(self, events=(), version=1, source_id="synthetic-task-source", minutes=0, status="ok", **updates):
        value = {"schema_version": 1,
                 "source": {"id": source_id, "kind": "manual_snapshot", "version": version,
                            "as_of": stamp(minutes), "status": status}, "events": list(events)}
        if status == "error":
            value["source"]["error"] = "Synthetic inventory source unavailable"
        value.update(updates)
        return value

    def ingest_inventory(self, rows, repository=REPO_A, version=1, source_id="synthetic-inventory-source", minutes=0, complete=True):
        return self.store.import_snapshot(self.payload(version=version, source_id=source_id, minutes=minutes,
            issue_inventory={"repository": repository, "complete": complete, "issues": rows}))

    def state(self):
        return self.store.reconcile()

    def view(self, identity):
        return next(row for row in self.state()["tasks"] if row["id"] == identity)

    def test_issue_coverage_counts_repository_and_number_not_task_or_refresh_count(self):
        definitions, inventories = [], []
        for prefix, repository in (("A", REPO_A), ("B", REPO_B)):
            rows = []
            for number in range(1001, 1014):
                identity = f"COV-{prefix}-{number}"
                definitions.append(task(identity))
                rows.append(issue_row(number, [identity], repository))
            inventories.append((repository, rows))
        self.store.import_snapshot(self.payload(definitions))
        for index, (repository, rows) in enumerate(inventories):
            self.ingest_inventory(rows, repository=repository, source_id=f"synthetic-inventory-{index}")
        self.ingest_inventory(inventories[0][1], source_id="synthetic-inventory-0", version=2, minutes=1)
        coverage = self.state()["coverage"]
        self.assertEqual(coverage["count"], 26)
        self.assertEqual(coverage["captured"], 26)
        self.assertEqual(coverage["missing_scope"], 0)
        self.assertEqual({row["repository"] for row in coverage["repositories"]}, {REPO_A, REPO_B})
        self.assertEqual(sum(len(row["issues"]) for row in coverage["repositories"]), 26)

    def test_multiple_tasks_for_same_issue_do_not_double_count(self):
        self.store.import_snapshot(self.payload([task("FIRST"), task("SECOND")]))
        self.ingest_inventory([issue_row(1001, ["FIRST", "SECOND"])])
        coverage = self.state()["coverage"]
        self.assertEqual(coverage["count"], 1)
        self.assertEqual(coverage["captured"], 1)
        self.assertEqual(set(coverage["repositories"][0]["issues"][0]["task_ids"]), {"FIRST", "SECOND"})

    def test_umbrella_is_never_assignable_or_implicitly_done(self):
        self.store.import_snapshot(self.payload([
            task("GROUP", node_kind="umbrella"), task("CHILD", parent_id="GROUP"),
            event("result", {"pr": pull_request(merged=True), "evidence": [proof("group-proof")]}, task="GROUP"),
            event("result", {"pr": pull_request(merged=True), "evidence": [proof("child-proof")]}, task="CHILD"),
        ]))
        self.ingest_inventory([issue_row(1001, ["GROUP"])])
        group = self.view("GROUP")
        self.assertEqual(self.view("CHILD")["delivery_status"], "done")
        self.assertEqual(group["delivery_status"], "unknown")
        self.assertTrue(group["pr"]["merged"], "own historical facts must remain inspectable")
        self.assertFalse(group["ready"])
        self.assertEqual(group["next_action_code"], "inspect_group")
        self.assertEqual(group["next_action_mode"], "none")
        before = self.state()["state_hash"]
        assignment = event("assignment", {"owner_thread": "synthetic-owner", "execution_status": "active"}, task="GROUP", when=stamp(1))
        with self.assertRaises(ValueError):
            self.store.record_assignment(self.payload([assignment], version=2, minutes=1))
        self.assertEqual(before, self.state()["state_hash"])

    def test_parent_relationship_does_not_invent_dependencies(self):
        self.store.import_snapshot(self.payload([task("GROUP", node_kind="umbrella"), task("CHILD", parent_id="GROUP")]))
        parent, child = self.view("GROUP"), self.view("CHILD")
        self.assertEqual(child["dependencies"], [])
        self.assertIn("CHILD", parent["child_ids"])
        self.assertNotIn("dependency_incomplete", {row["code"] for row in child["alerts"]})
        self.assertTrue(child["ready"])
        self.assertEqual(parent["delivery_status"], "unknown")

    def test_missing_scope_distinguishes_umbrella_unscoped_and_uncaptured(self):
        self.store.import_snapshot(self.payload([task("GROUP", node_kind="umbrella"), task("WORK"), task("NO-FILES", files=[])]))
        self.ingest_inventory([issue_row(1001, ["GROUP"]), issue_row(1002, ["WORK"]),
                               issue_row(1003, ["NO-FILES"]), issue_row(1004, [])])
        coverage = self.state()["coverage"]
        self.assertEqual(coverage["count"], 4)
        self.assertEqual(coverage["captured"], 3)
        self.assertEqual(coverage["missing_scope"], 3)
        rows = {row["number"]: row for row in coverage["repositories"][0]["issues"]}
        self.assertEqual(rows[1002]["scope_status"], "known")
        self.assertEqual(rows[1001]["scope_status"], "missing")
        self.assertFalse(rows[1004]["captured"])

    def test_fresh_older_and_failed_inventory_preserve_work_and_completed_action(self):
        self.store.import_snapshot(self.payload([
            task("DONE"), task("ACTIVE"), task("REVIEW"),
            event("result", {"pr": pull_request(merged=True), "evidence": [proof("done-proof")]}, task="DONE"),
            event("assignment", {"owner_thread": "synthetic-active-owner", "execution_status": "active"}, task="ACTIVE"),
            event("result", {"pr": pull_request(), "evidence": [proof("review-proof")]}, task="REVIEW"),
        ]))
        candidate = self.view("REVIEW")
        receipt = event("result", {"completed_actions": [{"action": candidate["next_action_code"],
            "input_pin": candidate["next_action_pin"], "timestamp": stamp(1)}]}, task="REVIEW", version=2, when=stamp(1))
        self.store.record_result(self.payload([receipt], version=2, minutes=1))
        before = {identity: copy.deepcopy(self.view(identity)) for identity in ("DONE", "ACTIVE", "REVIEW")}
        rows = [issue_row(1001, ["DONE"]), issue_row(1002, ["ACTIVE"]), issue_row(1003, ["REVIEW"])]
        self.ingest_inventory(rows, minutes=2)
        fresh = copy.deepcopy(rows)
        fresh[0]["title"] = "Synthetic newer inventory title"
        self.ingest_inventory(fresh, version=3, minutes=4)
        self.ingest_inventory([], version=2, minutes=3)
        self.store.import_snapshot(self.payload(version=4, source_id="synthetic-inventory-source", minutes=5, status="error"))
        coverage = self.state()["coverage"]
        self.assertEqual(coverage["count"], 3)
        repository = coverage["repositories"][0]
        self.assertEqual(repository["source_version"], 3)
        self.assertEqual(repository["issues"][0]["title"], "Synthetic newer inventory title")
        for identity, original in before.items():
            current = self.view(identity)
            for key in ("execution_status", "delivery_status", "owner_thread", "evidence", "next_action_pin"):
                self.assertEqual(current[key], original[key], (identity, key))
        self.assertTrue(self.view("REVIEW")["next_action_completed"])
        self.assertFalse(self.view("REVIEW")["ready"])

    def test_same_pr_links_are_deduplicated_across_sources_and_issue_mapping(self):
        url = f"https://github.com/{REPO_A}/pull/5001"
        refs = [{"kind": "pr", "number": 5001, "url": url}]
        self.store.import_snapshot(self.payload([
            task("FIRST", refs=refs), task("SECOND", refs=refs), task("PR-5002"), task("ISSUE-1002"),
            event("result", {"pr": pull_request(number=5001, url=url), "evidence": [proof()]}, task="FIRST"),
        ]))
        self.store.import_snapshot(self.payload(source_id="synthetic-inventory-source",
            issue_inventory={"repository": REPO_A, "complete": True,
                             "issues": [issue_row(1001, ["FIRST", "SECOND"]), issue_row(1002, [])]},
            pr_inventory={"repository": REPO_A, "complete": True, "prs": [pr_row(5001, ["FIRST", "SECOND"])]}))
        coverage = self.state()["coverage"]
        self.assertEqual(coverage["pr_count"], 1)
        matches = [row for row in coverage["pr_links"] if row["url"] == url]
        self.assertEqual(len(matches), 1)
        self.assertEqual(set(matches[0]["task_ids"]), {"FIRST", "SECOND"})
        issues = {row["number"]: row for row in coverage["repositories"][0]["issues"]}
        self.assertEqual(len(issues[1001]["pr_links"]), 1)
        self.assertFalse(issues[1002]["captured"], "task IDs must not imply issue mappings")
        self.assertNotIn(5002, {row["number"] for row in coverage["pr_links"]})

    def test_partial_inventory_merges_and_complete_inventory_replaces_only_coverage(self):
        self.store.import_snapshot(self.payload([task("FIRST"), task("SECOND")]))
        self.ingest_inventory([issue_row(1001, ["FIRST"])])
        self.ingest_inventory([issue_row(1002, ["SECOND"])], version=2, minutes=1, complete=False)
        self.assertEqual(self.state()["coverage"]["count"], 2)
        self.assertFalse(self.state()["coverage"]["repositories"][0]["complete"])
        self.ingest_inventory([issue_row(1002, ["SECOND"])], version=3, minutes=2, complete=True)
        self.assertEqual(self.state()["coverage"]["count"], 1)
        self.assertEqual({row["id"] for row in self.state()["tasks"]}, {"FIRST", "SECOND"})

    def test_unknown_task_or_failed_inventory_input_is_rejected_atomically(self):
        self.store.import_snapshot(self.payload([task("KNOWN")]))
        self.ingest_inventory([issue_row(1001, ["KNOWN"])])
        before = self.state()["state_hash"]
        invalids = (
            self.payload(version=2, source_id="synthetic-inventory-source", issue_inventory={"repository": REPO_A, "complete": True,
                "issues": [issue_row(1002, ["SYNTHETIC-NOT-IMPORTED"])]}),
            self.payload(version=2, source_id="synthetic-inventory-source", status="error", issue_inventory={"repository": REPO_A,
                "complete": True, "issues": []}),
        )
        for value in invalids:
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    self.store.import_snapshot(value)
                self.assertEqual(before, self.state()["state_hash"])


if __name__ == "__main__":
    unittest.main()
