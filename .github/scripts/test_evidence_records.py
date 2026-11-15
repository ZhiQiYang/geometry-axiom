"""Format/adoption controls; FixtureJudge receipts are NOT product execution evidence.

The real-repository round trip invokes the unchanged mutation judge separately.
Before evidence_records.py exists, the first regression uses the legacy ledger
reader and FixtureJudge, so its red result is stale input, not an import error.
"""
import contextlib
import copy
import gzip
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
from unittest import mock


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
TOOL = HERE / "evidence_records.py"


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def encoded(value):
    return (json.dumps(value, sort_keys=True, ensure_ascii=False, indent=2) + "\n").encode()


def seal(record):
    body = {key: value for key, value in record.items()
            if key not in ("record_sha256", "stale_from", "stale_why")}
    if body.get("verdict") == "stale" and record.get("stale_from"):
        body["verdict"] = record["stale_from"]
    return digest(json.dumps(body, sort_keys=True, ensure_ascii=False,
                             separators=(",", ":")).encode())


class FixtureJudge:
    """Deliberately synthetic, no compiler/browser/product subprocess is executed."""
    ids = ("A", "B")
    tool_sha256 = "c" * 64

    def __init__(self, root):
        self.root = Path(root)

    def record_hash(self, record):
        return seal(record)

    def expected_shards(self):
        return {"core-1": ["A"], "core-2": ["B"]}

    def evaluate(self, records):
        table = {}
        for rid in self.ids:
            record = records.get(rid)
            if record is None:
                table[rid] = None
                continue
            result = copy.deepcopy(record)
            if record.get("record_sha256") != seal(record):
                result["verdict"] = "invalid"
            elif record.get("source_sha256") != digest((self.root / (rid + ".input")).read_bytes()):
                result["verdict"] = "stale"
            table[rid] = result
        for rid in set(records) - set(self.ids):
            table[rid] = dict(records[rid], verdict="stale")
        counts = {key: 0 for key in ("killed", "crashed", "survived", "equivalent",
                                     "invalid", "stale", "blocked", "retired", "unrun")}
        for record in table.values():
            counts["unrun" if record is None else record["verdict"]] += 1
        code = 2 if counts["blocked"] else int(any(counts[k] for k in
                    ("survived", "invalid", "stale", "unrun")))
        return {"exit_code": code, "counts": counts, "table": table}


def module():
    spec = importlib.util.spec_from_file_location("issue214_evidence_records_tested", TOOL)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


class EvidenceRecordsTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="r214-record-fixture-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / "repo"
        (self.root / "tests").mkdir(parents=True)
        self.store = self.root / ".github/evidence/mutations"
        self.store.mkdir(parents=True)
        for rid in FixtureJudge.ids:
            (self.root / (rid + ".input")).write_text("before\n", encoding="utf-8")
        self.seed = {rid: self.record(rid, "a" * 40) for rid in FixtureJudge.ids}
        self.seed_raw = encoded(self.seed)
        (self.root / "tests/mutants_results.json").write_bytes(self.seed_raw)
        for arguments in (("init", "-q"), ("add", "tests/mutants_results.json"),
                          ("-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid",
                           "commit", "-qm", "synthetic receipt seed")):
            subprocess.run(["git", *arguments], cwd=self.root, check=True, capture_output=True)
        self.head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=self.root, text=True).strip()
        self.pin = {"schema": "geometry-mutation-record-seed/1", "base": self.head,
                    "path": "tests/mutants_results.json",
                    "blob": subprocess.check_output(["git", "rev-parse", "HEAD:tests/mutants_results.json"],
                                                   cwd=self.root, text=True).strip(),
                    "bytes": len(self.seed_raw), "sha256": digest(self.seed_raw)}
        (self.store / "seed.json").write_bytes(encoded(self.pin))
        self.artifact_ledgers = {}

    def record(self, rid, head):
        record = {"desc": "FIXTURE ONLY; not a product execution receipt: " + rid,
                  "verdict": "killed", "date": "fixture", "source_sha256":
                  digest((self.root / (rid + ".input")).read_bytes()),
                  "execution": {"schema": "fixture-only/no-product-execution",
                                "head": head, "tool_sha256": FixtureJudge.tool_sha256,
                                "platform": "posix"}}
        record["record_sha256"] = seal(record)
        return record

    def artifact(self, records=None, head="b" * 40, run_id="1"):
        records = records or {rid: self.record(rid, head) for rid in FixtureJudge.ids}
        folder = Path(self.temp.name) / "artifact"
        folder.mkdir(exist_ok=True)
        raw = encoded(records)
        self.artifact_ledgers[digest(raw)] = raw
        (folder / "mutants_results.json").write_bytes(raw)
        counts = FixtureJudge(self.root).evaluate(records)["counts"]
        manifests = []
        for name, ids in FixtureJudge(self.root).expected_shards().items():
            manifests.append({"schema": "geometry-mutation-ci-shard/1", "head": head,
                              "shard": name, "ids": ids, "run_id": run_id, "run_attempt": "1",
                              "platform": "posix", "tool_sha256": FixtureJudge.tool_sha256,
                              "supervisor_sha256": "d" * 64, "ledger_sha256": "1" * 64,
                              "cache_sha256": "2" * 64, "execution_log_sha256": "3" * 64,
                              "negative_cache_probe": {"id": ids[0],
                                  "expected": "cached binary differs from executed receipt", "strict_exit": 1},
                              "compiler": "SYNTHETIC FIXTURE; no product compilation"})
        summary = {"schema": "geometry-mutation-ci-summary/1", "head": head,
                   "table_size": len(records), "active": len(records), "counts": counts,
                   "ledger_sha256": digest(raw), "shards": manifests,
                   "binary_bytes_verified": True, "full_table_strict_exit": 0}
        (folder / "summary.json").write_bytes(encoded(summary))
        return folder, records, summary

    def overlay(self, record, summary, rid="A"):
        summary_raw = encoded(summary)
        origin = digest(summary_raw)
        payload = {"schema": "geometry-mutation-record-object/1", "id": rid, "record": record}
        raw = encoded(payload)
        object_sha = digest(raw)
        for name in ("objects", "refs", "origins", "ledgers"):
            (self.store / name).mkdir(exist_ok=True)
        (self.store / "origins" / (origin + ".json")).write_bytes(summary_raw)
        (self.store / "objects" / (object_sha + ".json")).write_bytes(raw)
        archive = io.BytesIO()
        with gzip.GzipFile(filename="", mode="wb", fileobj=archive, mtime=0) as stream:
            stream.write(self.artifact_ledgers[summary["ledger_sha256"]])
        (self.store / "ledgers" / (summary["ledger_sha256"] + ".json.gz")).write_bytes(archive.getvalue())
        ref = {"schema": "geometry-mutation-record-ref/1", "id": rid, "object_sha256": object_sha,
               "origin_summary_sha256": origin, "origin_ledger_sha256": summary["ledger_sha256"]}
        (self.store / "refs" / (rid + ".json")).write_bytes(encoded(ref))
        return self.store / "objects" / (object_sha + ".json")

    @contextlib.contextmanager
    def implementation(self):
        value = module()
        # Only these synthetic repositories replace the fixed migration anchor.
        with mock.patch.object(value, "FROZEN_SEED", self.pin, create=True), \
                mock.patch.object(value, "_judge", side_effect=lambda root: FixtureJudge(root)):
            yield value

    def snapshot(self):
        return {p.relative_to(self.store).as_posix(): p.read_bytes()
                for p in self.store.rglob("*") if p.is_file()}

    def test_overlay_restores_current_receipt_without_rehashing_original(self):
        (self.root / "A.input").write_text("after\n", encoding="utf-8")
        _, current, summary = self.artifact()
        self.overlay(current["A"], summary)
        if TOOL.is_file():
            with self.implementation() as value:
                loaded = value.load_records(self.root, self.store)
                result = value.strict_records(self.root, loaded)
        else:
            # Genuine legacy behavior: it ignores the overlay and returns stale.
            loaded = json.loads(self.seed_raw)
            result = FixtureJudge(self.root).evaluate(loaded)
        self.assertEqual(result["exit_code"], 0, "legacy reader ignores the valid overlay and remains stale")
        self.assertEqual(loaded["A"], current["A"])
        self.assertEqual(loaded["B"], self.seed["B"])
        self.assertEqual(loaded["A"]["record_sha256"], current["A"]["record_sha256"])
        self.assertEqual(loaded["A"]["execution"]["head"], "b" * 40)

    def test_materialize_uses_git_seed_even_when_working_view_is_overwritten(self):
        (self.root / "tests/mutants_results.json").write_text("garbage", encoding="utf-8")
        with self.implementation() as value:
            report = value.materialize(self.root, self.store)
        self.assertEqual(json.loads((self.root / "tests/mutants_results.json").read_bytes()), self.seed)
        self.assertFalse(report["binary_bytes_reverified"])
        self.assertEqual(report["strict_exit"], 0)

    def test_source_change_still_fails_and_does_not_publish_view(self):
        (self.root / "A.input").write_text("changed dependency", encoding="utf-8")
        target = Path(self.temp.name) / "never-written.json"
        with self.implementation() as value, self.assertRaisesRegex(ValueError, "strict"):
            value.materialize(self.root, self.store, target)
        self.assertFalse(target.exists())

    def test_missing_and_unknown_id_are_rejected(self):
        with self.implementation() as value:
            for records in ({"A": self.seed["A"]}, dict(self.seed, UNKNOWN=self.seed["A"])):
                with self.assertRaisesRegex(ValueError, "ID"):
                    value.strict_records(self.root, records)

    def test_cas_bytes_are_checked_before_parsing(self):
        _, current, summary = self.artifact()
        path = self.overlay(current["A"], summary)
        path.write_bytes(path.read_bytes() + b" ")
        with self.implementation() as value, self.assertRaisesRegex(ValueError, "hash"):
            value.load_records(self.root, self.store)

    def test_resealed_cas_cannot_change_original_record_seal(self):
        _, current, summary = self.artifact()
        record = copy.deepcopy(current["A"])
        record["execution"]["head"] = "e" * 40
        self.overlay(record, summary)
        with self.implementation() as value, self.assertRaisesRegex(ValueError, "record seal"):
            value.load_records(self.root, self.store)

    def test_seed_pin_and_duplicate_json_key_are_rejected(self):
        pin = self.store / "seed.json"
        with self.implementation() as value:
            pin.write_bytes(encoded(dict(self.pin, sha256="0" * 64)))
            with self.assertRaisesRegex(ValueError, "seed"):
                value.load_records(self.root, self.store)
            pin.write_text('{"schema":"a","schema":"b"}', encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "duplicate JSON key"):
                value.load_records(self.root, self.store)

    def test_committed_seed_and_matching_repin_cannot_replace_frozen_seed(self):
        replacement = copy.deepcopy(self.seed)
        replacement["A"]["date"] = "another internally valid synthetic execution"
        replacement["A"]["record_sha256"] = seal(replacement["A"])
        raw = encoded(replacement)
        (self.root / "tests/mutants_results.json").write_bytes(raw)
        subprocess.run(["git", "add", "tests/mutants_results.json"], cwd=self.root, check=True, capture_output=True)
        subprocess.run(["git", "-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid",
                        "commit", "-qm", "replace seed and repin"], cwd=self.root, check=True, capture_output=True)
        changed = dict(self.pin, base=subprocess.check_output(["git", "rev-parse", "HEAD"],
                      cwd=self.root, text=True).strip(), bytes=len(raw), sha256=digest(raw),
                      blob=hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest())
        (self.store / "seed.json").write_bytes(encoded(changed))
        with self.implementation() as value, self.assertRaisesRegex(ValueError, "fixed|frozen"):
            value.load_records(self.root, self.store)

    def test_same_head_valid_record_cannot_borrow_another_runs_summary(self):
        first = {rid: self.record(rid, "b" * 40) for rid in FixtureJudge.ids}
        first["A"]["date"] = "first real-shaped synthetic run"
        first["A"]["record_sha256"] = seal(first["A"])
        _, first, _ = self.artifact(first, run_id="1")
        second = copy.deepcopy(first)
        second["A"]["date"] = "second real-shaped synthetic run"
        second["A"]["record_sha256"] = seal(second["A"])
        _, second, summary = self.artifact(second, run_id="2")
        self.assertEqual(FixtureJudge(self.root).evaluate(first)["exit_code"], 0)
        self.assertEqual(FixtureJudge(self.root).evaluate(second)["exit_code"], 0)
        self.overlay(first["A"], summary)
        with self.implementation() as value, self.assertRaisesRegex(ValueError, "original ledger"):
            value.load_records(self.root, self.store)

    def test_ref_cannot_select_a_different_id(self):
        _, current, summary = self.artifact()
        self.overlay(current["A"], summary)
        path = self.store / "refs/A.json"
        ref = json.loads(path.read_bytes())
        ref["id"] = "B"
        path.write_bytes(encoded(ref))
        with self.implementation() as value, self.assertRaisesRegex(ValueError, "ref"):
            value.load_records(self.root, self.store)

    def test_adopt_preserves_fresh_record_and_replaces_only_stale(self):
        (self.root / "A.input").write_text("after\n", encoding="utf-8")
        folder, incoming, _ = self.artifact()
        with self.implementation() as value:
            report = value.adopt(self.root, folder, self.store)
            records = value.load_records(self.root, self.store)
            value.strict_records(self.root, records)
        self.assertEqual(report["updated"], ["A"])
        self.assertEqual(report["retained"], ["B"])
        self.assertEqual(records["A"], incoming["A"])
        self.assertEqual(records["B"], self.seed["B"])
        self.assertFalse((self.store / "refs/B.json").exists())
        self.assertFalse(report["binary_bytes_reverified"])

    def test_adoption_preserves_complete_ledger_original_bytes_in_deterministic_gzip(self):
        (self.root / "A.input").write_text("after\n", encoding="utf-8")
        folder, _, summary = self.artifact()
        raw = (folder / "mutants_results.json").read_bytes() + b" \n"
        (folder / "mutants_results.json").write_bytes(raw)
        summary["ledger_sha256"] = digest(raw)
        (folder / "summary.json").write_bytes(encoded(summary))
        with self.implementation() as value:
            report = value.adopt(self.root, folder, self.store)
        archive = (self.store / "ledgers" / (digest(raw) + ".json.gz")).read_bytes()
        self.assertEqual(gzip.decompress(archive), raw)
        self.assertEqual(archive[4:8], b"\0\0\0\0", "gzip must not record the wall-clock time")
        self.assertEqual(archive[3] & 8, 0, "gzip must not record a local filename")
        self.assertTrue(report["origin_ledger_stored"])

    def test_original_ledger_bytes_and_complete_membership_are_checked(self):
        _, current, summary = self.artifact()
        self.overlay(current["A"], summary)
        path = self.store / "ledgers" / (summary["ledger_sha256"] + ".json.gz")
        original = path.read_bytes()
        path.write_bytes(gzip.compress(gzip.decompress(original) + b" ", mtime=0))
        with self.implementation() as value, self.assertRaisesRegex(ValueError, "original ledger bytes hash"):
            value.load_records(self.root, self.store)
        path.write_bytes(original)
        partial = encoded({"A": current["A"]})
        changed = dict(summary, ledger_sha256=digest(partial))
        self.artifact_ledgers[digest(partial)] = partial
        self.overlay(current["A"], changed)
        with self.implementation() as value, self.assertRaisesRegex(ValueError, "original ledger IDs"):
            value.load_records(self.root, self.store)

    def test_fresh_adoption_makes_no_store_changes(self):
        folder, _, _ = self.artifact()
        before = self.snapshot()
        with self.implementation() as value:
            report = value.adopt(self.root, folder, self.store)
        self.assertEqual(report["updated"], [])
        self.assertEqual(self.snapshot(), before)

    def test_incoming_survived_is_rejected_even_when_current_is_fresh(self):
        records = {rid: self.record(rid, "b" * 40) for rid in FixtureJudge.ids}
        records["A"]["verdict"] = "survived"
        records["A"]["record_sha256"] = seal(records["A"])
        folder, _, _ = self.artifact(records)
        before = self.snapshot()
        with self.implementation() as value, self.assertRaises(ValueError):
            value.adopt(self.root, folder, self.store)
        self.assertEqual(self.snapshot(), before)

    def test_false_binary_summary_and_coverage_mismatch_are_rejected(self):
        folder, _, summary = self.artifact()
        with self.implementation() as value:
            for changed in (dict(summary, binary_bytes_verified=False),
                            dict(summary, table_size=3), dict(summary, full_table_strict_exit=1),
                            dict(summary, ledger_sha256="0" * 64)):
                (folder / "summary.json").write_bytes(encoded(changed))
                before = self.snapshot()
                with self.assertRaises(ValueError):
                    value.adopt(self.root, folder, self.store)
                self.assertEqual(self.snapshot(), before)

    def test_shard_coverage_cannot_duplicate_or_omit_a_current_id(self):
        folder, _, summary = self.artifact()
        summary["shards"][1]["ids"] = ["A"]
        (folder / "summary.json").write_bytes(encoded(summary))
        with self.implementation() as value, self.assertRaises(ValueError):
            value.adopt(self.root, folder, self.store)

    def test_complete_origin_cannot_mix_runs_or_attempts(self):
        folder, _, summary = self.artifact()
        with self.implementation() as value:
            for field in ("run_id", "run_attempt"):
                changed = copy.deepcopy(summary)
                changed["shards"][1][field] = "2"
                (folder / "summary.json").write_bytes(encoded(changed))
                before = self.snapshot()
                with self.assertRaisesRegex(ValueError, "origin run"):
                    value.adopt(self.root, folder, self.store)
                self.assertEqual(self.snapshot(), before)

    def test_cli_documents_explicit_artifact_alias(self):
        with self.implementation() as value:
            self.assertTrue(hasattr(value, "build_parser"), "R214_PARSE_ALIAS_MUST_BE_DIRECTLY_TESTABLE")
            parser = value.build_parser()
            for alias in ("--artifact-dir", "--artifact", "--artifacts"):
                with self.subTest(alias=alias):
                    args = parser.parse_args(("adopt", alias, str(self.root)))
                    self.assertEqual(args.artifact_dir, self.root)

    def test_conflicting_green_object_does_not_override_explicit_ref(self):
        (self.root / "A.input").write_text("after\n", encoding="utf-8")
        _, current, summary = self.artifact()
        self.overlay(current["A"], summary)
        extra = copy.deepcopy(current["A"])
        extra["date"] = "unselected green candidate"
        extra["record_sha256"] = seal(extra)
        raw = encoded({"schema": "geometry-mutation-record-object/1", "id": "A", "record": extra})
        (self.store / "objects" / (digest(raw) + ".json")).write_bytes(raw)
        with self.implementation() as value:
            self.assertEqual(value.load_records(self.root, self.store)["A"], current["A"])

    def test_independent_refs_merge_without_rewriting_the_seed_or_receipts(self):
        original_store = self.store
        left, right = Path(self.temp.name) / "left", Path(self.temp.name) / "right"
        shutil.copytree(original_store, left)
        shutil.copytree(original_store, right)
        (self.root / "A.input").write_text("after A\n", encoding="utf-8")
        _, left_records, left_summary = self.artifact(head="b" * 40)
        self.store = left
        self.overlay(left_records["A"], left_summary)
        (self.root / "A.input").write_text("before\n", encoding="utf-8")
        (self.root / "B.input").write_text("after B\n", encoding="utf-8")
        _, right_records, right_summary = self.artifact(head="c" * 40)
        self.store = right
        self.overlay(right_records["B"], right_summary, "B")
        for tree in (left, right):
            for source in tree.rglob("*"):
                if source.is_file():
                    target = original_store / source.relative_to(tree)
                    if target.exists():
                        self.assertEqual(target.read_bytes(), source.read_bytes())
                    else:
                        target.parent.mkdir(parents=True, exist_ok=True)
                        shutil.copyfile(source, target)
        self.store = original_store
        (self.root / "A.input").write_text("after A\n", encoding="utf-8")
        with self.implementation() as value:
            records = value.load_records(self.root, original_store)
            self.assertEqual(value.strict_records(self.root, records)["exit_code"], 0)
        self.assertEqual(records, {"A": left_records["A"], "B": right_records["B"]})
        self.assertEqual((self.root / "tests/mutants_results.json").read_bytes(), self.seed_raw)

    def test_init_pins_git_bytes_without_rewriting_source(self):
        (self.store / "seed.json").unlink()
        before = (self.root / "tests/mutants_results.json").read_bytes()
        with self.implementation() as value:
            pin = value.init_store(self.root, self.store)
        self.assertEqual(pin, self.pin)
        self.assertEqual((self.root / "tests/mutants_results.json").read_bytes(), before)

    def test_init_keeps_fixed_provenance_after_an_unrelated_commit(self):
        subprocess.run(["git", "-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid",
                        "commit", "--allow-empty", "-qm", "unrelated merge-shaped commit"],
                       cwd=self.root, check=True, capture_output=True)
        (self.store / "seed.json").unlink()
        with self.implementation() as value:
            self.assertEqual(value.init_store(self.root, self.store), self.pin)


class OriginalJudgeRoundTrip(unittest.TestCase):
    def test_current_store_round_trip_uses_unchanged_strict_judge(self):
        """Historical real receipts only: this does not execute product mutations."""
        value = module()
        with tempfile.TemporaryDirectory(prefix="r214-real-roundtrip-") as temp:
            store = Path(temp) / "store"
            shutil.copytree(ROOT / ".github/evidence/mutations", store)
            expected = value.load_records(ROOT, store)
            destination = Path(temp) / "view.json"
            with mock.patch.dict(os.environ, MUTATE_CACHE=str(Path(temp) / "no-binaries")):
                report = value.materialize(ROOT, store, destination)
            self.assertEqual(json.loads(destination.read_bytes()), expected)
            self.assertEqual(report["strict_exit"], 0)
            self.assertFalse(report["binary_bytes_reverified"])
            environment = dict(os.environ, MUTATE_RESULTS=str(destination), MUTATE_CACHE=str(Path(temp) / "no-binaries"))
            process = subprocess.run([os.sys.executable, "-B", "tests/mutate.py", "--check"],
                                     cwd=ROOT, env=environment, capture_output=True, text=True, timeout=120)
            self.assertEqual(process.returncode, 0, process.stdout + process.stderr)

    def test_existing_cache_tamper_is_not_hidden_by_adapter(self):
        value = module()
        records = value.load_records(ROOT)
        with tempfile.TemporaryDirectory(prefix="r214-cache-guard-") as temp:
            with mock.patch.dict(os.environ, MUTATE_CACHE=temp):
                judge = value.OriginalJudge(ROOT)
                mutant = next(m for m in judge.mt.MUTANTS if m.get("binary") != "bridge"
                              and records[m["id"]]["verdict"] != "retired")
                path = Path(temp) / mutant["id"] / "_mut.exe"
                path.parent.mkdir()
                path.write_bytes(b"deliberately does not match the executed binary receipt")
                with self.assertRaisesRegex(ValueError, "strict.*cached binary differs"):
                    value.strict_records(ROOT, records)


if __name__ == "__main__":
    unittest.main()
