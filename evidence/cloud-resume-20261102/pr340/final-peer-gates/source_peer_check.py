"""Read-only Git identity and lineage review; run no repository gates."""
import hashlib
import json
import subprocess
from pathlib import Path

SOURCE = Path("/tmp/geometry-pr340-20261102")
OUT = Path(__file__).resolve().parent
FINAL = "b3a248607d7eb68d3167abbb926cf491d9b35a26"
MAIN = "5775a9e9e46bca801a9a70aaeafcdab9f597bc4d"
TOOLS = "502a64ff6214dd6060927b7f14643a533536f20d"
PRIOR = "1605a6c27c97c2aa5e6405bddc7d3b31f1fdd965"
OLD = "04959e04c334ceaf03f865514f76b1cac8ee91f2"
PREFIX = "evidence/geo340-convergence-175cee44/"
TOOL_PATHS = {".github/scripts/architecture_evidence.py", ".github/scripts/mutation_evidence.py",
              ".github/workflows/mutation-evidence.yml", "tests/MUTATION-EVIDENCE.md"}
commands = []
assertions = 0


def sha(body):
    return hashlib.sha256(body).hexdigest()


def require(value, message):
    global assertions
    assertions += 1
    if not value:
        raise ValueError(message)


def run(args, expected=0):
    argv = ["git", "-C", str(SOURCE), *args]
    result = subprocess.run(argv, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    receipt = dict(command=argv, exit=result.returncode, stdout_bytes=len(result.stdout),
                   stdout_sha256=sha(result.stdout), stderr_sha256=sha(result.stderr))
    if len(result.stdout) < 14000 and b"\0" not in result.stdout:
        receipt["stdout"] = result.stdout.decode("utf-8")
    if result.stderr:
        receipt["stderr"] = result.stderr.decode("utf-8", errors="replace")
    commands.append(receipt)
    require(result.returncode == expected, "command failed: " + repr(argv))
    return result.stdout


def tree(ref):
    rows = run(["ls-tree", "-r", "-z", ref]).split(b"\0")
    result = {}
    for row in rows:
        if not row:
            continue
        entry, path = row.split(b"\t", 1)
        mode, kind, oid = entry.decode().split(" ")
        result[path.decode("utf-8")] = dict(mode=mode, type=kind, oid=oid)
    return result


def closure(entries):
    body = b"".join((entry["mode"] + " " + entry["type"] + " " + entry["oid"] + "\t" + path).encode() + b"\0"
                    for path, entry in sorted(entries.items()))
    return dict(entries=len(entries), canonical_tree_entries_sha256=sha(body))


require(run(["rev-parse", "HEAD"]).decode().strip() == FINAL, "fixed final HEAD")
require(run(["rev-parse", "refs/remotes/origin/main"]).decode().strip() == MAIN, "cached main changed")
require(run(["status", "--porcelain=v1"]) == b"", "worktree dirty")
run(["diff", "--exit-code", "HEAD"])
run(["config", "--get", "core.sparseCheckout"])
sparse = run(["sparse-checkout", "list"]).decode()
run(["reflog", "-4", "--format=%H %gD %gs"])
parents = {}
for ref in (FINAL, PRIOR, TOOLS):
    parents[ref] = run(["show", "-s", "--format=%P", ref]).decode().strip().split()
require(parents[FINAL] == [PRIOR, TOOLS], "final ordinary merge parents")
require(parents[PRIOR] == [OLD, MAIN], "prior ordinary main merge parents")
require(parents[TOOLS][1] == MAIN and len(parents[TOOLS]) == 2, "tool head contains adopted main")
for ancestor in (MAIN, TOOLS, PRIOR, OLD):
    run(["merge-base", "--is-ancestor", ancestor, FINAL])

main, final, old, tools = tree(MAIN), tree(FINAL), tree(OLD), tree(TOOLS)
changed = {path for path in set(main) | set(final) if main.get(path) != final.get(path)}
history = {path for path in changed if path.startswith(PREFIX)}
require(len(history) == 17 and changed == history | TOOL_PATHS, "exactly 17 history plus 4 tooling changes")
require(all(path not in main for path in changed), "all 21 differences are additions")
main_projected = {path: entry for path, entry in main.items() if path not in changed}
final_projected = {path: entry for path, entry in final.items() if path not in changed}
require(main_projected == final_projected, "all other tracked source/mode/blob entries exactly equal main")
require(all(final[path] == tools[path] for path in TOOL_PATHS), "four tool entries exactly equal #366 head")
require(all(final[path] == old[path] for path in history), "17 historical entries unchanged from original #340 head")
run(["diff", "--name-status", MAIN, FINAL])
diff_prior = run(["diff", "--name-only", PRIOR, FINAL]).decode().splitlines()
require(set(diff_prior) == TOOL_PATHS, "final differs from old light-gate head by four tools only")
tool_entries = {}
for path in sorted(TOOL_PATHS):
    body = run(["show", FINAL + ":" + path])
    tool_entries[path] = dict(**final[path], sha256=sha(body), bytes=len(body))
spot_checks = {}
for path in ("AGENTS.md", "公理層.md", "current_geometry.c", "tests/mutants_results.json", "tests/mutate.py",
             "tests/mutation_bridge.py", "tests/run_all.py", "tests/run_all.expected.json", "tests/native_shards.py",
             "tests/native_shard_timings.json", "geometry-core/domain-decoupling/product-architecture.json"):
    require(main[path] == final[path], "named sensitive source equals main: " + path)
    spot_checks[path] = final[path]

historical_provenance = {}
for name in ("AGGREGATE_RESULT.json", "CURRENT_STATE.json", "MERGE_RESULT.json", "PUBLICATION_INDEX.json"):
    value = json.loads(run(["show", FINAL + ":" + PREFIX + name]))
    historical_provenance[name] = value
require(historical_provenance["AGGREGATE_RESULT.json"]["source"] == "175cee44c56c89871803d955c0c525236727ba65"
        and not historical_provenance["AGGREGATE_RESULT.json"]["fullAggregate"], "historical aggregate retains old selected scope")
require(historical_provenance["PUBLICATION_INDEX.json"]["noOldExecutionShaRelabelled"] is True, "historical origin not relabelled")
old_gate_path = OUT.parent / "original-gates/RESULT.json"
old_gate_body = old_gate_path.read_bytes()
old_gates = json.loads(old_gate_body)
require(old_gates["source_sha"] == PRIOR and all(row["source_sha"] == PRIOR for row in old_gates["commands"]),
        "old light gates remain attached to prior 1605 source")
merge_receipts = []
for name in ("merge-main.json", "merge-verified-tool.json"):
    body = (OUT.parent / name).read_bytes()
    receipt = json.loads(body)
    merge_commands = [row for row in receipt["commands"] if "merge" in row["command"]]
    require(len(merge_commands) == 1 and merge_commands[0]["exit"] == 0
            and "--no-ff" in merge_commands[0]["command"] and "'ort'" in merge_commands[0]["stdout"],
            name + " original ordinary merge receipt")
    merge_receipts.append(dict(file=name, sha256=sha(body), merge=merge_commands[0]))
require(run(["status", "--porcelain=v1"]) == b"", "worktree remained clean")

report = dict(passed=True, assertions=assertions, fixed_final=FINAL, fixed_main=MAIN, tools_source=TOOLS,
              old_pr340_head=OLD, old_light_gate_head=PRIOR, parents=parents, sparse_checkout=sparse,
              full_main_tree=closure(main), full_final_tree=closure(final),
              projected_main_source=closure(main_projected), projected_final_source=closure(final_projected),
              changed_entries={path: final[path] for path in sorted(changed)},
              historical_unchanged_entries={path: final[path] for path in sorted(history)},
              tool_entries=tool_entries, named_sensitive_entries=spot_checks,
              historical_provenance=historical_provenance, merge_receipts=merge_receipts,
              old_light_gate_receipt=dict(path=str(old_gate_path), sha256=sha(old_gate_body), source_sha=PRIOR),
              commands=commands,
              limits=["No gates, repository tests, API requests, fetch, push, comment or CI dispatch were executed.",
                      "Remote main freshness and remote PR state were not queried; cached origin/main only was checked.",
                      "Git graph and retained local ort merge receipts establish ordinary local lineage; no remote push behavior is claimed.",
                      "Historical evidence is byte-identical inherited material, not new b3a execution; no archive re-execution or payload re-audit."])
(OUT / "source-peer-review.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
print(json.dumps({key: report[key] for key in ("passed", "assertions", "fixed_final", "projected_main_source", "projected_final_source")}, ensure_ascii=False))
