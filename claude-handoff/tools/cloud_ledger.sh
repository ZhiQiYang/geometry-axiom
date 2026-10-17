#!/bin/bash
# Regenerate the whole mutation ledger on one committed SHA (cloud port of
# claude-handoff/tools/t17_ledger.sh). Groups run side by side, each with its own
# MUTATE_RESULTS and TMPDIR (AGENTS.md: never let two processes write one results
# file); the rows are merged with mutate.save_records and judged by --check.
# NOT an official WSL receipt.   Usage: ledger.sh <worktree> <out-dir> <stack-kb|unlimited>
set -u
wt="${1:?worktree}"; out="${2:?out}"; stack="${3:-16384}"
mkdir -p "$out"
cd "$wt" || exit 70
export PATH=/opt/node22/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin LANG=C.UTF-8 LC_ALL=C.UTF-8 PYTHONIOENCODING=utf-8
ulimit -s "$stack"
head=$(git rev-parse HEAD)
[ -z "$(git status --porcelain)" ] || { echo "worktree not clean" > "$out/run.log"; exit 71; }
echo "start $(date -u +%FT%TZ) head=$head stack=$(ulimit -s)" > "$out/run.log"
ids=$(python3 - <<'EOF'
import re, pathlib
s = pathlib.Path('tests/mutate.py').read_text(encoding='utf-8')
core, bridge = [], []
for m in re.finditer(r'dict\(id="(M\d+)"(.*?)(?=\n    dict\(id=|\n\]\n)', s, re.S):
    (bridge if 'binary="bridge"' in m.group(2) else core).append(m.group(1))
half = (len(core) + 1) // 2
print(' '.join(core[:half])); print(' '.join(core[half:])); print(' '.join(bridge))
EOF
)
g1=$(sed -n 1p <<< "$ids"); g2=$(sed -n 2p <<< "$ids"); g3=$(sed -n 3p <<< "$ids")
echo "core-a: $g1" >> "$out/run.log"; echo "core-b: $g2" >> "$out/run.log"; echo "bridge: $g3" >> "$out/run.log"
run_group() {
  # Each group gets its own clean worktree of the same SHA, so the core groups'
  # temporary _mutant_<id>.c files never touch the tree another group reads.
  local name=$1; shift
  local tmp=/tmp/gci/ledger-$name; rm -rf "$tmp"; mkdir -p "$tmp"
  local gw="$out/wt-$name"
  git -C "$wt" worktree add -q --detach "$gw" "$head" || { echo "$name worktree failed" >> "$out/run.log"; return; }
  local t0=$(date +%s)
  (cd "$gw" && MUTATE_RESULTS="$out/$name.json" TMPDIR="$tmp" python3 -B -u tests/mutate.py "$@" > "$out/$name.log" 2>&1)
  echo "$name rc=$? seconds=$(( $(date +%s) - t0 ))" >> "$out/run.log"
  git -C "$wt" worktree remove --force "$gw"
}
run_group core-a $g1 &
run_group core-b $g2 &
run_group bridge $g3 &
wait
python3 - "$out" <<'EOF' >> "$out/run.log" 2>&1
import json, pathlib, sys
sys.path.insert(0, 'tests')
import mutate
out = pathlib.Path(sys.argv[1])
merged = {}
for name in ('core-a', 'core-b', 'bridge'):
    rows = mutate.load_records(out / f'{name}.json')
    dup = set(rows) & set(merged)
    assert not dup, dup
    merged.update(rows)
mutate.save_records(mutate.RESULTS, merged)
print('merged rows', len(merged))
EOF
python3 -B tests/mutate.py --check > "$out/check.log" 2>&1
echo "check_rc=$?" >> "$out/run.log"
tail -3 "$out/check.log" >> "$out/run.log"
cp tests/mutants_results.json "$out/mutants_results.json"
echo "end $(date -u +%FT%TZ)" >> "$out/run.log"
cat "$out/run.log"
