"""Keep mutation receipts in the repository without rewriting the frozen ledger.

The Git ledger is an immutable migration seed. Explicit per-ID references select
content-addressed, lossless records from a verified complete CI artifact. The
unchanged mutation judge decides freshness; this module never edits a receipt,
computes a replacement record seal, or claims to reverify absent binary bytes.
"""
from __future__ import annotations

import argparse
import gzip
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import zlib


ROOT = Path(__file__).resolve().parents[2]
STORE = Path(".github/evidence/mutations")
SEED_PATH = "tests/mutants_results.json"
FROZEN_SEED = {
    "schema": "geometry-mutation-record-seed/1",
    "base": "11eddfdb4d7b1f76aedfe001e084a3840790bedc",
    "path": SEED_PATH,
    "blob": "ceaf8d2979b5e8868b6a36c395d37cfe42d9de2e",
    "bytes": 13985837,
    "sha256": "9e31f91a6221b8ff31a041ae6b30514185d245bcbc1f0dbbab7ea641d45b1a31",
}
GOOD = {"killed", "crashed", "equivalent", "retired"}
COUNTERS = GOOD | {"survived", "invalid", "stale", "blocked", "unrun"}


def _sha(raw):
    return hashlib.sha256(raw).hexdigest()


def _canonical(value):
    return (json.dumps(value, sort_keys=True, ensure_ascii=False, indent=2,
                       allow_nan=False) + "\n").encode("utf-8")


def _gzip(raw):
    """Reversible original bytes, independent of file name and wall-clock time."""
    output = io.BytesIO()
    with gzip.GzipFile(filename="", mode="wb", fileobj=output, mtime=0) as stream:
        stream.write(raw)
    return output.getvalue()


def _json(raw):
    def unique(pairs):
        value = {}
        for key, item in pairs:
            if key in value:
                raise ValueError("duplicate JSON key: " + key)
            value[key] = item
        return value

    def invalid(value):
        raise ValueError("non-finite JSON number: " + value)

    return json.loads(raw, object_pairs_hook=unique, parse_constant=invalid)


def _hex(value, size=64):
    return isinstance(value, str) and re.fullmatch(r"[0-9a-f]{%d}" % size, value) is not None


def _id(value):
    return isinstance(value, str) and re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]*", value) is not None


def _require(condition, message):
    if not condition:
        raise ValueError(message)


def _read(path):
    path = Path(path)
    _require(path.is_file() and not path.is_symlink(), "missing or linked evidence file: " + str(path))
    return path.read_bytes()


def _store(root, store):
    return Path(store).resolve() if store is not None else Path(root).resolve() / STORE


def _git(root, *arguments):
    return subprocess.check_output(["git", *arguments], cwd=root, stderr=subprocess.PIPE)


def _head(root):
    value = _git(root, "rev-parse", "HEAD").decode().strip()
    _require(_hex(value, 40), "invalid checkout head")
    return value


def _atomic(path, raw):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    _require(not path.is_symlink(), "refuse linked evidence destination")
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(dir=path.parent, delete=False) as stream:
            temporary = Path(stream.name)
            stream.write(raw)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def _immutable(path, raw):
    path = Path(path)
    if path.exists() or path.is_symlink():
        _require(_read(path) == raw, "immutable evidence object differs: " + str(path))
    else:
        _atomic(path, raw)


class OriginalJudge:
    """Use the original evaluator, including its existing binary-cache checks."""

    def __init__(self, root):
        self.root = Path(root).resolve()
        tests = self.root / "tests"
        for name in ("binaries", "run_tests", "mutation_bridge"):
            loaded = sys.modules.get(name)
            if loaded is not None:
                _require(Path(loaded.__file__).resolve().parent == tests,
                         "judge dependency imported from another checkout: " + name)
        old_path = sys.path[:]
        try:
            sys.path.insert(0, str(tests))
            spec = importlib.util.spec_from_file_location("_evidence_original_mutate_" + str(id(self)), tests / "mutate.py")
            self.mt = importlib.util.module_from_spec(spec)
            sys.modules[spec.name] = self.mt
            spec.loader.exec_module(self.mt)
        finally:
            sys.path[:] = old_path
        self.ids = tuple(m["id"] for m in self.mt.MUTANTS)
        _require(len(self.ids) == len(set(self.ids)), "duplicate mutation definition ID")
        self.tool_sha256 = self.mt.tool_hash()

    def record_hash(self, record):
        return self.mt.record_hash(record)

    def expected_shards(self):
        result = {}
        for kind, count in (("core", 4), ("bridge", 3)):
            ids = [m["id"] for m in self.mt.MUTANTS
                   if (m.get("binary") == "bridge") == (kind == "bridge")]
            for index in range(count):
                result[f"{kind}-{index + 1}"] = ids[index::count]
        return result

    def evaluate(self, records):
        old_path = sys.path[:]
        try:
            sys.path.insert(0, str(self.root / "tests"))
            table = self.mt.evaluate_table(self.mt.MUTANTS, records, self.mt.Sources(self.root),
                                          "", self.mt.oracle_hash(), require_execution=True)
            counts = self.mt.tally(table)
            return {"exit_code": self.mt.exit_code(counts, strict=True), "counts": counts, "table": table}
        finally:
            sys.path[:] = old_path


def _judge(root):
    return OriginalJudge(root)


def _record(judge, rid, record):
    _require(_id(rid) and isinstance(record, dict), "invalid mutation record ID/object")
    _require(_hex(record.get("record_sha256")) and
             record["record_sha256"] == judge.record_hash(record), "original record seal differs: " + rid)


def _seed(root, store):
    pin = _json(_read(store / "seed.json"))
    _require(isinstance(pin, dict) and set(pin) == {"schema", "base", "path", "blob", "bytes", "sha256"},
             "invalid seed pin fields")
    _require(pin["schema"] == "geometry-mutation-record-seed/1" and _hex(pin["base"], 40)
             and pin["path"] == SEED_PATH and _hex(pin["blob"], 40) and _hex(pin["sha256"])
             and type(pin["bytes"]) is int and pin["bytes"] > 0, "invalid seed pin")
    _require(pin == FROZEN_SEED, "seed pin differs from fixed migration seed")
    # HEAD contains the frozen seed even in shallow CI; base is provenance only.
    raw = _git(root, "show", "HEAD:" + SEED_PATH)
    blob = hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()
    _require((blob, len(raw), _sha(raw)) == (pin["blob"], pin["bytes"], pin["sha256"]),
             "frozen Git seed bytes differ from pin")
    records = _json(raw)
    _require(isinstance(records, dict), "seed ledger must be an object")
    return pin, records


def init_store(root=ROOT, store=None):
    root, store = Path(root).resolve(), _store(root, store)
    if (store / "seed.json").exists():
        return _seed(root, store)[0]
    pin = dict(FROZEN_SEED)
    raw = _git(root, "show", "HEAD:" + SEED_PATH)
    blob = hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()
    _require((blob, len(raw), _sha(raw)) == (pin["blob"], pin["bytes"], pin["sha256"]),
             "frozen Git seed bytes differ from fixed migration seed")
    records = _json(raw)
    _require(isinstance(records, dict) and records, "seed ledger must be a nonempty object")
    judge = _judge(root)
    for rid, record in records.items():
        _record(judge, rid, record)
    _immutable(store / "seed.json", _canonical(pin))
    return pin


def _summary(summary):
    """Validate original supervisor provenance, not absent binary artifacts."""
    _require(isinstance(summary, dict) and summary.get("schema") == "geometry-mutation-ci-summary/1",
             "invalid verified summary schema")
    _require(_hex(summary.get("head"), 40) and _hex(summary.get("ledger_sha256")), "invalid summary identity")
    _require(summary.get("binary_bytes_verified") is True and
             type(summary.get("full_table_strict_exit")) is int and summary["full_table_strict_exit"] == 0,
             "summary did not verify complete original binary bytes and strict receipts")
    size, active, counts = summary.get("table_size"), summary.get("active"), summary.get("counts")
    _require(type(size) is int and size > 0 and type(active) is int and 0 <= active <= size,
             "invalid summary coverage size")
    _require(isinstance(counts, dict) and set(counts) == COUNTERS and
             all(type(value) is int and value >= 0 for value in counts.values()), "invalid summary counts")
    _require(sum(counts.values()) == size and active == size - counts["retired"] and
             not any(counts[k] for k in COUNTERS - GOOD), "summary coverage/counts are not complete and green")
    manifests = summary.get("shards")
    _require(isinstance(manifests, list) and manifests, "missing verified summary shards")
    ids, names, tools, supervisors, runs = {}, set(), set(), set(), set()
    for manifest in manifests:
        _require(isinstance(manifest, dict) and manifest.get("schema") == "geometry-mutation-ci-shard/1",
                 "invalid original shard schema")
        name = manifest.get("shard")
        _require(isinstance(name, str) and re.fullmatch(r"(?:core|bridge)-[1-9][0-9]*", name)
                 and name not in names, "invalid or duplicate shard name")
        names.add(name)
        assigned = manifest.get("ids")
        _require(isinstance(assigned, list) and assigned and all(_id(rid) for rid in assigned)
                 and len(assigned) == len(set(assigned)), "invalid shard IDs")
        _require(manifest.get("head") == summary["head"] and manifest.get("platform") in ("posix", "nt"),
                 "shard execution source/platform differs")
        for field in ("tool_sha256", "supervisor_sha256", "ledger_sha256", "cache_sha256", "execution_log_sha256"):
            _require(_hex(manifest.get(field)), "invalid original shard hash: " + field)
        tools.add(manifest["tool_sha256"])
        supervisors.add(manifest["supervisor_sha256"])
        for field in ("run_id", "run_attempt"):
            _require(isinstance(manifest.get(field), str) and re.fullmatch(r"[1-9][0-9]*", manifest[field]),
                     "missing official CI " + field)
        runs.add((manifest["run_id"], manifest["run_attempt"]))
        probe = manifest.get("negative_cache_probe")
        expected = "bridge executable artifact changed" if name.startswith("bridge-") else "cached binary differs from executed receipt"
        _require(isinstance(probe, dict) and probe.get("id") in assigned and
                 type(probe.get("strict_exit")) is int and probe["strict_exit"] == 1 and probe.get("expected") == expected,
                 "missing original negative binary guard proof")
        for rid in assigned:
            _require(rid not in ids, "duplicate shard coverage ID: " + rid)
            ids[rid] = manifest
    _require(len(ids) == size and len(tools) == len(supervisors) == len(runs) == 1,
             "incomplete or inconsistent shard coverage/origin run")
    return ids


def _origin_record(record, rid, summary, membership):
    _require(rid in membership, "record ID absent from original artifact coverage")
    if record.get("verdict") == "retired":
        return
    execution, manifest = record.get("execution"), membership[rid]
    _require(isinstance(execution, dict) and execution.get("head") == summary["head"]
             and execution.get("tool_sha256") == manifest["tool_sha256"]
             and execution.get("platform") == manifest["platform"], "record origin differs from original verified summary")


def _original_ledger(store, summary, membership):
    path = store / "ledgers" / (summary["ledger_sha256"] + ".json.gz")
    try:
        raw = gzip.decompress(_read(path))
    except (OSError, EOFError, zlib.error) as exc:
        raise ValueError("cannot read compressed original ledger: " + str(path)) from exc
    _require(_sha(raw) == summary["ledger_sha256"], "original ledger bytes hash differs")
    records = _json(raw)
    _require(isinstance(records, dict) and set(records) == set(membership),
             "original ledger IDs differ from complete summary membership")
    return records


def load_records(root=ROOT, store=None):
    root, store = Path(root).resolve(), _store(root, store)
    _, records = _seed(root, store)
    judge = _judge(root)
    for rid, record in records.items():
        _record(judge, rid, record)
    references = store / "refs"
    origins = {}
    if not references.exists():
        return records
    _require(references.is_dir() and not references.is_symlink(), "invalid reference directory")
    for path in sorted(references.iterdir()):
        _require(path.suffix == ".json" and _id(path.stem), "invalid ref filename")
        ref = _json(_read(path))
        _require(isinstance(ref, dict) and set(ref) == {"schema", "id", "object_sha256",
                 "origin_summary_sha256", "origin_ledger_sha256"}, "invalid ref fields")
        _require(ref["schema"] == "geometry-mutation-record-ref/1" and ref["id"] == path.stem
                 and all(_hex(ref[key]) for key in ("object_sha256", "origin_summary_sha256", "origin_ledger_sha256")),
                 "ref ID or hash differs")
        raw = _read(store / "objects" / (ref["object_sha256"] + ".json"))
        _require(_sha(raw) == ref["object_sha256"], "CAS object hash differs")
        payload = _json(raw)
        _require(isinstance(payload, dict) and set(payload) == {"schema", "id", "record"}
                 and payload["schema"] == "geometry-mutation-record-object/1" and payload["id"] == ref["id"],
                 "CAS object/ref ID differs")
        rid, record = ref["id"], payload["record"]
        _record(judge, rid, record)
        origin_sha = ref["origin_summary_sha256"]
        if origin_sha not in origins:
            origin_raw = _read(store / "origins" / (origin_sha + ".json"))
            _require(_sha(origin_raw) == origin_sha, "original summary hash differs")
            summary = _json(origin_raw)
            membership = _summary(summary)
            origins[origin_sha] = summary, membership, _original_ledger(store, summary, membership)
        summary, membership, original = origins[origin_sha]
        _require(summary["ledger_sha256"] == ref["origin_ledger_sha256"], "ref original ledger hash differs")
        _require(record == original.get(rid), "selected record differs from its original ledger member: " + rid)
        _origin_record(record, rid, summary, membership)
        records[rid] = record
    return records


def strict_records(root, records):
    judge = _judge(Path(root).resolve())
    _require(isinstance(records, dict) and set(records) == set(judge.ids), "full current mutation ID coverage differs")
    for rid, record in records.items():
        _record(judge, rid, record)
    result = judge.evaluate(records)
    reasons = [rid + ": " + ("unrun" if record is None else
               str(record.get("stale_why") or record.get("why") or record.get("verdict")))
               for rid, record in result["table"].items()
               if record is None or record.get("verdict") not in GOOD]
    _require(result["exit_code"] == 0, "original strict mutation check failed: " +
             str(result["counts"]) + "; " + "; ".join(reasons[:6]))
    return result


def materialize(root=ROOT, store=None, destination=None):
    root = Path(root).resolve()
    records = load_records(root, store)
    result = strict_records(root, records)
    path = Path(destination) if destination is not None else root / SEED_PATH
    raw = _canonical(records)
    _atomic(path, raw)
    return {"schema": "geometry-mutation-record-view/1", "head": _head(root), "records": len(records),
            "path": str(path), "bytes": len(raw), "sha256": _sha(raw), "strict_exit": result["exit_code"],
            "counts": result["counts"], "binary_bytes_reverified": False}


def adopt(root, artifact_dir, store=None):
    root, store, artifact_dir = Path(root).resolve(), _store(root, store), Path(artifact_dir).resolve()
    summary_raw = _read(artifact_dir / "summary.json")
    ledger_raw = _read(artifact_dir / "mutants_results.json")
    summary, incoming = _json(summary_raw), _json(ledger_raw)
    membership = _summary(summary)
    _require(_sha(ledger_raw) == summary["ledger_sha256"], "complete artifact ledger hash differs")
    judge = _judge(root)
    _require({m["shard"]: m["ids"] for m in summary["shards"]} == judge.expected_shards(),
             "artifact does not cover the current shard assignment")
    for manifest in summary["shards"]:
        _require(manifest["tool_sha256"] == judge.tool_sha256, "original mutation execution tool changed")
    # Check the entire incoming artifact before considering any fresh old entry.
    checked = strict_records(root, incoming)
    _require(checked["counts"] == summary["counts"] and len(incoming) == summary["table_size"],
             "verified summary differs from actual complete ledger")
    for rid, record in incoming.items():
        _origin_record(record, rid, summary, membership)
    current = load_records(root, store)
    _require(set(current) <= set(judge.ids), "current store has unknown mutation IDs")
    effective = judge.evaluate(current)["table"]
    updated, retained, combined = [], [], dict(current)
    for rid in sorted(judge.ids):
        record = effective.get(rid)
        verdict = "unrun" if record is None else record.get("verdict")
        if verdict in GOOD:
            retained.append(rid)
        elif verdict in ("stale", "unrun"):
            combined[rid] = incoming[rid]
            updated.append(rid)
        else:
            raise ValueError("current " + str(verdict) + " record cannot be silently replaced: " + rid)
    strict_records(root, combined)
    origin_sha = _sha(summary_raw)
    # All validation completes before any persistent object or ref is written.
    pending = []
    for rid in updated:
        raw = _canonical({"schema": "geometry-mutation-record-object/1", "id": rid, "record": incoming[rid]})
        object_sha = _sha(raw)
        ref = {"schema": "geometry-mutation-record-ref/1", "id": rid, "object_sha256": object_sha,
               "origin_summary_sha256": origin_sha, "origin_ledger_sha256": summary["ledger_sha256"]}
        pending.append((rid, object_sha, raw, _canonical(ref)))
    if updated:
        _immutable(store / "origins" / (origin_sha + ".json"), summary_raw)
        _immutable(store / "ledgers" / (summary["ledger_sha256"] + ".json.gz"), _gzip(ledger_raw))
    for rid, object_sha, raw, ref_raw in pending:
        _immutable(store / "objects" / (object_sha + ".json"), raw)
        _atomic(store / "refs" / (rid + ".json"), ref_raw)
    return {"schema": "geometry-mutation-record-adoption/1", "head": _head(root),
            "origin_head": summary["head"], "origin_summary_sha256": origin_sha,
            "origin_ledger_sha256": summary["ledger_sha256"], "updated": updated, "retained": retained,
            "strict_exit": 0, "origin_ledger_stored": bool(updated),
            "origin_binary_bytes_verified": True, "binary_bytes_reverified": False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("init", "check", "materialize", "adopt"))
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--store", type=Path)
    parser.add_argument("--destination", type=Path)
    parser.add_argument("--artifact-dir", "--artifact", "--artifacts", dest="artifact_dir", type=Path)
    args = parser.parse_args()
    try:
        if args.mode == "init":
            result = init_store(args.root, args.store)
        elif args.mode == "materialize":
            result = materialize(args.root, args.store, args.destination)
        elif args.mode == "adopt":
            _require(args.artifact_dir is not None, "adopt requires --artifact-dir")
            result = adopt(args.root, args.artifact_dir, args.store)
        else:
            records = load_records(args.root, args.store)
            checked = strict_records(args.root, records)
            result = {"records": len(records), "strict_exit": checked["exit_code"],
                      "counts": checked["counts"], "binary_bytes_reverified": False}
        print(json.dumps(result, ensure_ascii=False, sort_keys=True))
        return 0
    except (OSError, ValueError, RuntimeError, subprocess.CalledProcessError) as exc:
        print("EVIDENCE_RECORDS_REFUSED: " + str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
