#!/bin/bash
# Run the GEO-262 card-reference compiled mutants (geometry-core/card-reference/run_mutations.py) on a fixed SHA.
# Run through the lock: wsl -d Ubuntu-24.04 -- bash <sp>/wsl-ci/wsl_locked3.sh run "bash <sp>/wsl-ci/card_ref_mutations.sh <sha> <label>"
set -u
sha="${1:?sha}"; label="${2:?label}"
out=/mnt/d/geometry-axiom-work/cardref-$label-${sha:0:8}
mkdir -p "$out"
w=$(mktemp -d /var/tmp/cardref.XXXXXX)
{
  echo "start $(date -u +%FT%TZ) sha=$sha"
  git -c safe.directory='*' clone -q --no-checkout /mnt/d/geometry-axiom "$w/repo"
  git -C "$w/repo" -c advice.detachedHead=false checkout -q "$sha"
  echo "head=$(git -C "$w/repo" rev-parse HEAD)"
} > "$out/run.log" 2>&1
cd "$w/repo" || exit 70
mkdir -p "$w/tmp"
export TMPDIR="$w/tmp" PATH=/opt/node/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin LANG=C.UTF-8 LC_ALL=C.UTF-8 PYTHONIOENCODING=utf-8 PYTHONDONTWRITEBYTECODE=1
ulimit -s 16384
t0=$(date +%s)
if [ -n "${AXIOM_ONLY:-}" ]; then echo "AXIOM_ONLY: skipped run_mutations.py" > "$out/mutations.log"; rc=0; else
python3 -B -u geometry-core/card-reference/run_mutations.py --output "$w/out" > "$out/mutations.log" 2>&1
rc=$?
fi
echo "run_mutations_rc=$rc seconds=$(( $(date +%s) - t0 ))" >> "$out/run.log"
[ -f "$w/out/report.json" ] && cp "$w/out/report.json" "$out/report.json"
tail -20 "$out/mutations.log" >> "$out/run.log"
if [ -f geometry-core/card-reference/run_axiom_mutations.py ]; then
  t1=$(date +%s)
  python3 -B -u geometry-core/card-reference/run_axiom_mutations.py --output "$w/out-axiom" > "$out/axiom-mutations.log" 2>&1
  arc=$?
  echo "run_axiom_mutations_rc=$arc seconds=$(( $(date +%s) - t1 ))" >> "$out/run.log"
  tail -20 "$out/axiom-mutations.log" >> "$out/run.log"
  [ "$arc" -ne 0 ] && rc=$arc
fi
tar -C "$w" -czf "$out/raw.tgz" out out-axiom 2>/dev/null
echo "end $(date -u +%FT%TZ)" >> "$out/run.log"
rm -rf "$w"
tail -12 "$out/run.log"
exit $rc
