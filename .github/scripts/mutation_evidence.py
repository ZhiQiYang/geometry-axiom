"""CI supervisor for the unchanged, strict mutation runner and its artifacts."""
import argparse
import contextlib
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tarfile

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tests"))
import mutate as mt


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def supervisor_sha():
    return hashlib.sha256(Path(__file__).read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def read_json(path):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError("duplicate JSON key: " + key)
            result[key] = value
        return result
    return json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=unique)


def write_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def head():
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()


def shards():
    result = {}
    for kind, count in (("core", 4), ("bridge", 3)):
        items = [m for m in mt.MUTANTS if (m.get("binary") == "bridge") == (kind == "bridge")]
        for index in range(count):
            result[f"{kind}-{index + 1}"] = [m["id"] for m in items[index::count]]
    flat = [rid for ids in result.values() for rid in ids]
    assert len(flat) == len(set(flat)) == len(mt.MUTANTS)
    assert set(flat) == {m["id"] for m in mt.MUTANTS}
    return result


def selected(ids):
    return [m for m in mt.MUTANTS if m["id"] in ids]


def require_binaries(mutants, records, cache):
    """Unlike --check alone, artifact verification requires every executed binary."""
    for mutant in mutants:
        record = records[mutant["id"]]
        if record["verdict"] == "retired":
            continue
        execution = record["execution"]
        if mutant.get("binary") == "bridge":
            binary = "bridge.exe" if execution["platform"] == "nt" else "bridge"
            paths = [
                (cache / "_bridge-baseline" / execution["head"] / binary, execution["baseline_identity"]["exe_sha256"]),
                (cache / mutant["id"] / "bridge-mutant" / binary, execution["mutant_identity"]["exe_sha256"]),
                (cache / mutant["id"] / "bridge-restored" / binary, execution["restored_identity"]["exe_sha256"]),
            ]
        else:
            paths = [(cache / mutant["id"] / "_mut.exe", execution["exe_sha256"]),
                     (cache / "_baseline" / "baseline.exe", execution["baseline_exe_sha256"])]
        for path, expected in paths:
            if not path.is_file() or sha(path) != expected:
                raise ValueError("missing or changed executed binary: " + str(path))


def strict_check(mutants, ledger, cache):
    previous = mt.MUT_ROOT
    try:
        mt.MUT_ROOT = cache
        status = mt.check_pass(mutants, root=ROOT, results_path=ledger, require_execution=True)
        if status != 0:
            raise ValueError("strict mutation check failed: " + str(status))
    finally:
        mt.MUT_ROOT = previous


def negative_probe(mutants, ledger, records, cache):
    mutant = next(m for m in mutants if records[m["id"]]["verdict"] != "retired")
    execution = records[mutant["id"]]["execution"]
    if execution["platform"] != os.name:
        raise ValueError("negative cache probe must run on the execution platform")
    bridge = mutant.get("binary") == "bridge"
    path = (cache / mutant["id"] / "bridge-mutant" / ("bridge.exe" if os.name == "nt" else "bridge")) if bridge else cache / mutant["id"] / "_mut.exe"
    original = path.read_bytes()
    previous = mt.MUT_ROOT
    try:
        mt.MUT_ROOT = cache
        path.write_bytes(original + b"\nCI deliberately mismatched cache probe\n")
        problems = mt.execution_problems(mutant, records[mutant["id"]], records[mutant["id"]]["verdict"], mt.Sources(ROOT))
        expected = "bridge executable artifact changed" if bridge else "cached binary differs from executed receipt"
        if not any(expected in problem for problem in problems):
            raise ValueError("mismatched cache did not fail at the binary guard: " + repr(problems))
        with contextlib.redirect_stdout(sys.stdout):
            if mt.check_pass(mutants, root=ROOT, results_path=ledger, require_execution=True) != 1:
                raise ValueError("mismatched cache did not produce strict exit 1")
        return {"id": mutant["id"], "expected": expected, "strict_exit": 1}
    finally:
        path.write_bytes(original)
        mt.MUT_ROOT = previous


def run_shard(name, out):
    ids = shards()[name]
    out.mkdir(parents=True, exist_ok=False)
    cache, ledger = out / "cache", out / "mutants_results.json"
    cache.mkdir()
    subprocess.run(["git", "diff", "--exit-code", "HEAD"], cwd=ROOT, check=True)
    env = dict(os.environ, MUTATE_CACHE=str(cache), MUTATE_RESULTS=str(ledger), PYTHONUNBUFFERED="1")
    command = [sys.executable, "tests/mutate.py", *ids]
    with (out / "execution.log").open("w", encoding="utf-8") as log:
        process = subprocess.Popen(command, cwd=ROOT, env=env, stdout=subprocess.PIPE,
                                   stderr=subprocess.STDOUT, text=True, encoding="utf-8")
        for line in process.stdout:
            log.write(line)
            log.flush()
            print(line, end="", flush=True)
        status = process.wait()
    if status != 0:
        raise ValueError("mutation execution failed: " + str(status))
    records = read_json(ledger)
    if set(records) != set(ids):
        raise ValueError("shard ledger does not cover exactly its assigned IDs")
    if any(record.get("execution", {}).get("head") != head()
           for record in records.values() if record["verdict"] != "retired"):
        raise ValueError("shard contains execution receipts from another head")
    mutants = selected(ids)
    require_binaries(mutants, records, cache)
    strict_check(mutants, ledger, cache)
    probe = negative_probe(mutants, ledger, records, cache)
    require_binaries(mutants, records, cache)
    strict_check(mutants, ledger, cache)
    archive = out / "cache.tar.gz"
    def keep(info):
        # The committed scratch clone and optional OS core dumps are not receipts.
        if Path(info.name).name == "core" or Path(info.name).name.startswith("core."):
            return None
        return info
    with tarfile.open(archive, "w:gz") as tar:
        for path in sorted(cache.iterdir()):
            if path.name != "_bridge-work":
                tar.add(path, arcname=path.name, filter=keep)
    write_json(out / "manifest.json", {
        "schema": "geometry-mutation-ci-shard/1", "head": head(), "shard": name, "ids": ids,
        "run_id": os.environ.get("GITHUB_RUN_ID"), "run_attempt": os.environ.get("GITHUB_RUN_ATTEMPT"),
        "platform": os.name, "tool_sha256": mt.tool_hash(), "supervisor_sha256": supervisor_sha(),
        "ledger_sha256": sha(ledger), "cache_sha256": sha(archive),
        "execution_log_sha256": sha(out / "execution.log"), "negative_cache_probe": probe,
        "compiler": subprocess.check_output([os.environ.get("CC", "cc"), "--version"], text=True),
    })


def verify(artifacts, out):
    out.mkdir(parents=True, exist_ok=False)
    expected = shards()
    folders = sorted(path.parent for path in artifacts.glob("*/manifest.json"))
    if len(folders) != len(expected):
        raise ValueError("missing or extra shard artifacts")
    merged, seen, manifests = {}, set(), []
    for folder in folders:
        manifest = read_json(folder / "manifest.json")
        name = manifest["shard"]
        if name not in expected or name in seen or manifest["ids"] != expected[name]:
            raise ValueError("unknown, duplicate or changed shard assignment")
        seen.add(name)
        if (manifest["schema"] != "geometry-mutation-ci-shard/1" or manifest["head"] != head()
                or manifest["tool_sha256"] != mt.tool_hash() or manifest["supervisor_sha256"] != supervisor_sha()):
            raise ValueError("artifact source, runner or supervisor differs from checkout")
        for filename, field in (("mutants_results.json", "ledger_sha256"), ("cache.tar.gz", "cache_sha256"), ("execution.log", "execution_log_sha256")):
            if sha(folder / filename) != manifest[field]:
                raise ValueError("artifact bytes changed: " + filename)
        records = read_json(folder / "mutants_results.json")
        if set(records) != set(expected[name]) or set(records) & set(merged):
            raise ValueError("missing, unknown or duplicate mutation records")
        if any(record.get("execution", {}).get("head") != head()
               for record in records.values() if record["verdict"] != "retired"):
            raise ValueError("artifact contains execution receipts from another head")
        cache = out / name
        cache.mkdir()
        with tarfile.open(folder / "cache.tar.gz", "r:gz") as tar:
            tar.extractall(cache, filter="data")
        mutants = selected(expected[name])
        require_binaries(mutants, records, cache)
        strict_check(mutants, folder / "mutants_results.json", cache)
        merged.update(records)
        manifests.append(manifest)
    if seen != set(expected) or set(merged) != {m["id"] for m in mt.MUTANTS}:
        raise ValueError("aggregate is not the complete current mutation table")
    ledger = out / "mutants_results.json"
    write_json(ledger, merged)
    # Full-table source/closure/mutant/oracle/receipt validation is separate from
    # the required, byte-exact artifact checks performed for every shard above.
    strict_check(mt.MUTANTS, ledger, out / "no-local-binaries")
    previous = mt.MUT_ROOT
    try:
        mt.MUT_ROOT = out / "no-local-binaries"
        table = mt.evaluate_table(mt.MUTANTS, merged, mt.Sources(ROOT), "", mt.oracle_hash(), require_execution=True)
    finally:
        mt.MUT_ROOT = previous
    write_json(out / "summary.json", {
        "schema": "geometry-mutation-ci-summary/1", "head": head(), "table_size": len(mt.MUTANTS),
        "active": sum(record["verdict"] != "retired" for record in merged.values()),
        "counts": mt.tally(table), "ledger_sha256": sha(ledger), "shards": manifests,
        "binary_bytes_verified": True, "full_table_strict_exit": 0,
    })


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("plan", "run", "verify"))
    parser.add_argument("--shard")
    parser.add_argument("--out", type=Path)
    parser.add_argument("--artifacts", type=Path)
    args = parser.parse_args()
    if args.mode == "plan":
        print("matrix=" + json.dumps({"include": [{"shard": name} for name in shards()]}))
    elif args.mode == "run":
        run_shard(args.shard, args.out.resolve())
    else:
        verify(args.artifacts.resolve(), args.out.resolve())


if __name__ == "__main__":
    main()
