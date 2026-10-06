"""Synthetic pre-validation SQLite ledgers must survive upgrades without writes.

The fixture schema matches the earlier append-only store. No git history,
network, live database, private queue or product files are required.
"""

import datetime as dt
import hashlib
import http.client
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile
import threading
import unittest

from server import make_server
from store import Store


HERE = Path(__file__).resolve().parent
HEAD = "a" * 40
WHEN = (dt.datetime.now(dt.timezone.utc) - dt.timedelta(minutes=5)).isoformat()


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def checksum(value):
    return hashlib.sha256(canonical(value).encode()).hexdigest()


def old_event(kind, data, version=1):
    return {"event_id": f"synthetic-legacy:{kind}:{version}", "task_id": "LEGACY-QA",
            "kind": kind, "version": version, "occurred_at": WHEN, "data": data}


def snapshot(events, version=1):
    return {"schema_version": 1,
            "source": {"id": "synthetic-legacy-source", "kind": "manual_snapshot",
                       "version": version, "as_of": WHEN, "status": "ok"}, "events": events}


def proof(result="passed"):
    return {"id": "synthetic-reused-proof", "criterion": "behavior", "kind": "test",
            "timestamp": WHEN, "sha": HEAD, "result": result}


def pr():
    return {"number": 1, "url": "https://example.invalid/synthetic/legacy/pull/1",
            "head_sha": HEAD, "merged": True, "merged_head_sha": HEAD,
            "review_state": "approved"}


def legacy_database(directory, defect):
    """Write rows accepted by the earlier entrypoint, including its old defects."""
    directory.mkdir(mode=0o700)
    path = directory / "state.sqlite3"
    task = old_event("task", {"title": "合成舊版資料", "scope": "Synthetic legacy fixtures",
                            "files": ["synthetic/legacy.py"], "head_sha": HEAD,
                            "required_acceptance": ["behavior"], "approval_constraints": []})
    result = {"pr": pr(), "evidence": [proof()]}
    bad_step = {"name": "synthetic-step", "status": "completed", "conclusion": {"bad": "shape"}}
    if defect == "nested_evidence":
        result["evidence"][0].update(kind="ci", runner_id=123, steps=[bad_step])
    elif defect == "nested_pr":
        result["pr"]["ci"] = [{"name": "synthetic-job", "sha": HEAD, "status": "completed",
                                 "conclusion": "success", "runner_id": 123, "steps": [bad_step]}]
    elif defect == "conflicting_evidence":
        result["evidence"] = [proof("failed"), proof("passed")]
    elif defect == "healthy":
        pass
    else:
        raise AssertionError(defect)
    payload = snapshot([task, old_event("result", result)])
    with sqlite3.connect(path) as db:
        db.executescript("""
            CREATE TABLE sources(id TEXT PRIMARY KEY, current TEXT NOT NULL, last_good TEXT);
            CREATE TABLE snapshots(ordinal INTEGER PRIMARY KEY AUTOINCREMENT,
                source_id TEXT NOT NULL, source_version INTEGER NOT NULL,
                payload TEXT NOT NULL, checksum TEXT NOT NULL, UNIQUE(source_id,source_version));
            CREATE TABLE events(event_id TEXT PRIMARY KEY, source_id TEXT NOT NULL,
                source_version INTEGER NOT NULL, task_id TEXT NOT NULL, kind TEXT NOT NULL,
                version INTEGER NOT NULL, occurred_at TEXT NOT NULL, payload TEXT NOT NULL,
                applied INTEGER NOT NULL, UNIQUE(source_id,task_id,kind,version));
        """)
        db.execute("INSERT INTO sources VALUES(?,?,?)", (payload["source"]["id"], canonical(payload["source"]), canonical(payload["source"])))
        db.execute("INSERT INTO snapshots(source_id,source_version,payload,checksum) VALUES(?,?,?,?)",
                   (payload["source"]["id"], 1, canonical(payload), checksum(payload)))
        for item in payload["events"]:
            db.execute("INSERT INTO events VALUES(?,?,?,?,?,?,?,?,?)",
                       (item["event_id"], payload["source"]["id"], 1, item["task_id"], item["kind"],
                        item["version"], WHEN, canonical(item), 1))
    os.chmod(path, 0o600)
    return path


class LegacyUpgradeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="geometry-legacy-upgrade-")
        self.root = Path(self.temp.name)

    def tearDown(self):
        self.temp.cleanup()

    def assert_diagnostic(self, state):
        self.assertEqual(state["store_health"]["status"], "invalid")
        self.assertTrue(state["store_health"]["read_only"])
        self.assertTrue(state["store_health"]["issues"])
        self.assertEqual(state["ready"], [])
        self.assertTrue(all(task["delivery_status"] != "done" for task in state["tasks"]))
        self.assertIn("ledger_invalid", {alert["code"] for alert in state["alerts"]})
        self.assertRegex(state["state_hash"], r"^[0-9a-f]{64}$")

    def test_legacy_nested_ci_reopens_as_readable_diagnostic(self):
        for defect in ("nested_evidence", "nested_pr"):
            with self.subTest(defect=defect):
                path = legacy_database(self.root / defect, defect)
                original = path.read_bytes()
                state = Store(path).reconcile()
                self.assert_diagnostic(state)
                self.assertEqual(path.read_bytes(), original)

    def test_legacy_conflicting_proof_cannot_gain_done_from_new_review_pin(self):
        path = legacy_database(self.root / "conflict", "conflicting_evidence")
        original = path.read_bytes()
        store = Store(path)
        new_pr = pr()
        new_pr["reviewed_sha"] = HEAD
        with self.assertRaises(ValueError):
            store.import_snapshot(snapshot([old_event("result", {"pr": new_pr}, version=2)], version=2))
        self.assertEqual(path.read_bytes(), original)
        self.assert_diagnostic(store.reconcile())

    def test_healthy_legacy_ledger_remains_readable_and_accepts_valid_new_evidence(self):
        path = legacy_database(self.root / "healthy", "healthy")
        original = path.read_bytes()
        store = Store(path)
        state = store.reconcile()
        self.assertEqual(state["store_health"]["status"], "ok")
        self.assertFalse(state["store_health"]["read_only"])
        self.assertEqual(path.read_bytes(), original)
        self.assertEqual(state["tasks"][0]["id"], "LEGACY-QA")
        pinned = pr()
        pinned["reviewed_sha"] = HEAD
        accepted = store.import_snapshot(snapshot([old_event("result", {"pr": pinned}, version=2)], version=2))
        self.assertEqual(accepted["tasks"][0]["delivery_status"], "done")

    def test_legacy_cli_read_commands_return_diagnostic_json(self):
        path = legacy_database(self.root / "cli", "nested_evidence")
        original = path.read_bytes()
        for command in ("reconcile", "list-ready"):
            with self.subTest(command=command):
                completed = subprocess.run([sys.executable, str(HERE / "cli.py"), "--data-dir", str(path.parent), command],
                                           capture_output=True, text=True, timeout=15, check=False)
                self.assertEqual(completed.returncode, 0, completed.stderr)
                state = json.loads(completed.stdout)
                self.assertEqual(state["store_health"]["status"], "invalid")
                self.assertEqual(state["ready"], [])
        self.assertEqual(path.read_bytes(), original)

    def test_legacy_api_returns_diagnostic_instead_of_generic_error(self):
        path = legacy_database(self.root / "api", "nested_pr")
        original = path.read_bytes()
        server = make_server(path.parent, port=0)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            connection = http.client.HTTPConnection("127.0.0.1", server.server_port, timeout=5)
            try:
                connection.request("GET", "/api/state")
                response = connection.getresponse()
                body = response.read()
                self.assertEqual(response.status, 200, body)
                self.assert_diagnostic(json.loads(body))
            finally:
                connection.close()
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=5)
        self.assertEqual(path.read_bytes(), original)

    def test_invalid_legacy_store_preserves_rows_bytes_and_private_backup(self):
        path = legacy_database(self.root / "preserve", "conflicting_evidence")
        original = path.read_bytes()
        store = Store(path)
        state = store.reconcile()
        self.assert_diagnostic(state)
        safe = snapshot([old_event("task", {"title": "Synthetic attempted replacement"}, version=2)], version=2)
        export = {"schema_version": 1, "format": "geometry-work-manager-export", "snapshots": [safe]}
        export["checksum"] = checksum(export)
        attempts = (
            lambda: store.import_snapshot(safe),
            lambda: store.record_assignment(old_event("assignment", {"owner_thread": "synthetic-owner", "execution_status": "active"})),
            lambda: store.record_result(old_event("result", {"summary": "Synthetic attempted write"}, version=2)),
            lambda: store.restore(export),
        )
        for attempt in attempts:
            with self.assertRaises(ValueError):
                attempt()
            self.assertEqual(path.read_bytes(), original)
        with sqlite3.connect(path) as db:
            self.assertEqual(db.execute("SELECT COUNT(*) FROM events").fetchone()[0], 2)
            raw = db.execute("SELECT payload FROM events WHERE kind='result'").fetchone()[0]
            self.assertEqual([item["result"] for item in json.loads(raw)["data"]["evidence"]], ["failed", "passed"])
        self.assertTrue(state["store_health"]["backup_preserved"])
        self.assertEqual(state["store_health"]["backup_checksum"], hashlib.sha256(original).hexdigest())
        backups = [item for item in path.parent.rglob("*") if item.is_file() and item != path and item.read_bytes() == original]
        self.assertTrue(backups, "a private exact-byte backup must be retained")
        self.assertTrue(all(item.stat().st_mode & 0o777 == 0o600 for item in backups))
        self.assertNotIn(str(path.parent), json.dumps(state), "API diagnostics must not disclose local paths")


if __name__ == "__main__":
    unittest.main()
