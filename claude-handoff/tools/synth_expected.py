"""Three-way synthesis of tests/run_all.expected.json for a train merge (P-090 / P-105).

Usage: python synth_expected.py <worktree> <ours-rev> <theirs-rev>
Per suite:
  - only one side changed it (added, removed or new count): take that side;
  - both sides changed a count suite: ours + theirs - base (both added tests to the same suite);
  - both sides changed it identically: take it;
  - anything else (mode change on both sides, add/remove clash): stop and report, never guess.
Writes the merged file in place (LF, same key order style as run_all --update-expected) and prints every decision.
"""
import json
import subprocess
import sys

wt, ours, theirs = sys.argv[1:4]


def git(*args):
    return subprocess.run(["git", *args], capture_output=True, cwd=wt, check=True).stdout


base = git("merge-base", ours, theirs).decode().strip()


def load(rev):
    return json.loads(git("show", f"{rev}:tests/run_all.expected.json"))


B, O, T = load(base), load(ours), load(theirs)
out = dict(O)
suites = {}
problems = []
for k in sorted(set(B["suites"]) | set(O["suites"]) | set(T["suites"])):
    b, o, t = B["suites"].get(k), O["suites"].get(k), T["suites"].get(k)
    if o == t:
        v, why = o, "same on both sides" if o != b else None
    elif o == b:
        v, why = t, "theirs only"
    elif t == b:
        v, why = o, "ours only"
    elif b and o and t and b.get("mode") == o.get("mode") == t.get("mode") == "count" and o.get("unit") == t.get("unit"):
        v = dict(o, count=o["count"] + t["count"] - b["count"])
        why = f"both: {o['count']} + {t['count']} - {b['count']}"
    else:
        problems.append((k, b, o, t))
        continue
    if why:
        print(f"{k:50s} {why:28s} -> {v}")
    if v is not None:
        suites[k] = v
if problems:
    for p in problems:
        print("UNRESOLVED", p)
    sys.exit(2)
out["suites"] = suites
with open(f"{wt}/tests/run_all.expected.json", "w", encoding="utf-8", newline="\n") as f:
    json.dump(out, f, ensure_ascii=False, indent=2)
    f.write("\n")
print("base", base[:8], "suites", len(suites))
