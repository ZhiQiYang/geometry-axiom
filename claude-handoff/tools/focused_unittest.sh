#!/bin/bash
# Run named unittest modules on a fixed SHA in a clean ext4 clone (no early stop; every module runs).
# Run through the lock: wsl -d Ubuntu-24.04 -- bash <sp>/wsl-ci/wsl_locked3.sh run "bash <sp>/wsl-ci/focused_unittest.sh <sha> <label> <module...>"
set -u
sha="${1:?sha}"; label="${2:?label}"; shift 2
out=/mnt/d/geometry-axiom-work/focused-$label-${sha:0:8}
mkdir -p "$out"
w=$(mktemp -d /var/tmp/focused.XXXXXX)
{
  echo "start $(date -u +%FT%TZ) sha=$sha"
  echo "modules=$*"
  git -c safe.directory='*' clone -q --no-checkout /mnt/d/geometry-axiom "$w/repo"
  git -C "$w/repo" -c advice.detachedHead=false checkout -q "$sha"
  echo "head=$(git -C "$w/repo" rev-parse HEAD)"
} > "$out/run.log" 2>&1
cd "$w/repo" || exit 70
mkdir -p "$w/tmp" "$w/bin"; ln -s /usr/bin/python3 "$w/bin/python"
export TMPDIR="$w/tmp" PATH="$w/bin:/opt/node/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin" LANG=C.UTF-8 LC_ALL=C.UTF-8 PYTHONIOENCODING=utf-8 PYTHONDONTWRITEBYTECODE=1
ulimit -s 16384
t0=$(date +%s)
python3 -B -u -m unittest -v "$@" > "$out/unittest.log" 2>&1
rc=$?
echo "unittest_rc=$rc seconds=$(( $(date +%s) - t0 ))" >> "$out/run.log"
tail -5 "$out/unittest.log" >> "$out/run.log"
grep -E "^(FAIL|ERROR):" "$out/unittest.log" | sort | uniq > "$out/failures.txt"
echo "end $(date -u +%FT%TZ)" >> "$out/run.log"
rm -rf "$w"
cat "$out/run.log"
exit $rc
