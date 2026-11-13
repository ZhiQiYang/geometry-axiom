#!/bin/bash
# Q38 section-profile mutation gate on a fixed SHA (+ optional patch) in a persistent ext4 clone.
# Run only through the lock:
#   wsl.exe -d Ubuntu-24.04 -- bash <sp>/wsl-ci/wsl_locked3.sh run "bash <sp>/wsl-ci/q38/q38_gate.sh <sha> <label> <patch|-> <gate|controls> [gate args...]"
# Writes run.log, gate.log, receipt.json and logs/ to /mnt/d/geometry-axiom-work/q38-<label>-<sha8>/.
set -u
sha="${1:?sha}"; label="${2:?label}"; patch="${3:?patch or -}"; entry="${4:?gate|controls}"; shift 4
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
base=/var/tmp/q38-geo261
out=/mnt/d/geometry-axiom-work/q38-$label-${sha:0:8}
mkdir -p "$out" "$base/tmp" "$base/bin"
export TMPDIR="$base/tmp" PATH=/opt/node/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
export LANG=C.UTF-8 LC_ALL=C.UTF-8 PYTHONIOENCODING=utf-8 PYTHONDONTWRITEBYTECODE=1
ulimit -s 16384
log="$out/run.log"
echo "start $(date -u +%FT%TZ) sha=$sha label=$label patch=$patch entry=$entry args=$* nproc=$(nproc)" > "$log"
if [ ! -d "$base/repo/.git" ]; then
  git -c safe.directory='*' clone -q --no-checkout /mnt/d/geometry-axiom "$base/repo" >> "$log" 2>&1 || { echo "clone failed" >> "$log"; exit 70; }
fi
cd "$base/repo" || exit 70
git -c safe.directory='*' fetch -q /mnt/d/geometry-axiom '+refs/heads/*:refs/remotes/src/*' >> "$log" 2>&1
git -c advice.detachedHead=false checkout -q -f "$sha" >> "$log" 2>&1 || { echo "checkout failed" >> "$log"; exit 70; }
git clean -q -fdx >> "$log" 2>&1
if [ "$patch" != "-" ]; then
  git apply --whitespace=nowarn "$patch" >> "$log" 2>&1 || { echo "patch failed" >> "$log"; exit 70; }
fi
echo "head=$(git rev-parse HEAD)" >> "$log"
git status --short >> "$log"
t0=$(date +%s)
python3 -c 'import sys
from pathlib import Path
from tests import binaries
binaries.OUT_DIR = Path(sys.argv[1])
raise SystemExit(binaries.main(["build", "model-base"]))' "$base/bin" >> "$log" 2>&1
brc=$?
echo "model-base build rc=$brc seconds=$(( $(date +%s) - t0 ))" >> "$log"
[ "$brc" -ne 0 ] && exit 71
export GEOMETRY_MODEL_BASE="$base/bin/model-base"
sha256sum "$GEOMETRY_MODEL_BASE" >> "$log"
rm -rf "$out/logs"
t1=$(date +%s)
if [ "$entry" = "controls" ]; then
  python3 -B -u "$here/q38_controls.py" --receipt "$out/receipt.json" --logs "$out/logs" "$@" > "$out/gate.log" 2>&1
else
  python3 -B -u tests/section_profile_mutation_check.py --receipt "$out/receipt.json" --logs "$out/logs" "$@" > "$out/gate.log" 2>&1
fi
rc=$?
echo "gate rc=$rc seconds=$(( $(date +%s) - t1 )) end=$(date -u +%FT%TZ)" >> "$log"
tail -5 "$out/gate.log" >> "$log"
tail -8 "$log"
exit $rc
