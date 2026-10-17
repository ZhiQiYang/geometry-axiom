#!/bin/bash
# Train 17: regenerate the whole mutation ledger on the merged source (P-090 / P-105), then --check.
# Run through the lock: wsl -d Ubuntu-24.04 -- bash <sp>/wsl-ci/wsl_locked3.sh run "bash <sp>/wsl-ci/t17_ledger.sh <sha>"
set -u
sha="${1:?sha}"
out=/mnt/d/geometry-axiom-work/train17-claude/ledger-${sha:0:8}
mkdir -p "$out"
w=$(mktemp -d /var/tmp/t17-ledger.XXXXXX)
{
  echo "start $(date -u +%FT%TZ) sha=$sha clone=$w"
  git -c safe.directory='*' clone -q --no-checkout /mnt/d/geometry-axiom "$w/repo"
  git -C "$w/repo" -c advice.detachedHead=false checkout -q "$sha"
  echo "checkout $(git -C "$w/repo" rev-parse HEAD)"
} > "$out/run.log" 2>&1
cd "$w/repo" || exit 70
export TMPDIR="$w/tmp" PATH=/opt/node/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin LANG=C.UTF-8 LC_ALL=C.UTF-8 PYTHONIOENCODING=utf-8
mkdir -p "$TMPDIR"
ulimit -s 16384
t0=$(date +%s)
python3 -B -u tests/mutate.py > "$out/mutate.log" 2>&1
echo "mutate_rc=$? seconds=$(( $(date +%s) - t0 ))" >> "$out/run.log"
python3 -B tests/mutate.py --check > "$out/check.log" 2>&1
echo "check_rc=$?" >> "$out/run.log"
cp tests/mutants_results.json "$out/mutants_results.json"
echo "end $(date -u +%FT%TZ)" >> "$out/run.log"
rm -rf "$w"
cat "$out/run.log"
