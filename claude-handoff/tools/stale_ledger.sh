#!/bin/bash
# Re-run only the stale mutation ledger entries on a fixed SHA (clean ext4 clone), then --check.
# Run through the lock: wsl -d Ubuntu-24.04 -- bash <sp>/wsl-ci/wsl_locked3.sh run "bash <sp>/wsl-ci/stale_ledger.sh <sha> <label>"
set -u
sha="${1:?sha}"; label="${2:?label}"
out=/mnt/d/geometry-axiom-work/ledger-$label-${sha:0:8}
mkdir -p "$out"
w=$(mktemp -d /var/tmp/ledger.XXXXXX)
{
  echo "start $(date -u +%FT%TZ) sha=$sha"
  git -c safe.directory='*' clone -q --no-checkout /mnt/d/geometry-axiom "$w/repo"
  git -C "$w/repo" -c advice.detachedHead=false checkout -q "$sha"
} > "$out/run.log" 2>&1
cd "$w/repo" || exit 70
export TMPDIR="$w/tmp" PATH=/opt/node/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin LANG=C.UTF-8 LC_ALL=C.UTF-8 PYTHONIOENCODING=utf-8
mkdir -p "$TMPDIR"; ulimit -s 16384
python3 -B tests/mutate.py --check > "$out/check-before.log" 2>&1
echo "check_before_rc=$?" >> "$out/run.log"
ids=$(grep -oE '(STALE|UNRUN) M[0-9]+' "$out/check-before.log" | awk '{print $2}' | sort -u | tr '\n' ' ')
echo "stale_ids=$ids" >> "$out/run.log"
if [ -n "$ids" ]; then
  t0=$(date +%s)
  python3 -B -u tests/mutate.py $ids > "$out/mutate.log" 2>&1
  echo "mutate_rc=$? seconds=$(( $(date +%s) - t0 ))" >> "$out/run.log"
fi
python3 -B tests/mutate.py --check > "$out/check-after.log" 2>&1
echo "check_after_rc=$?" >> "$out/run.log"
cp tests/mutants_results.json "$out/mutants_results.json"
echo "end $(date -u +%FT%TZ)" >> "$out/run.log"
rm -rf "$w"
cat "$out/run.log"
