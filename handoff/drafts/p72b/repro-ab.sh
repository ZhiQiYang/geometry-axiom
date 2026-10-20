#!/bin/bash
# P72B A/B reproduction in WSL, GEOMETRY_COMPOSITION_ONLY (runs P72 then P72B only).
#   A = 09ab5f79 (unfixed control): expected FATAL "Unexpected native dialog at === P72B … confirm 建立一份空白新專案…"
#   B = fixed commit: expected "[EXPECTED NATIVE DIALOG] 建立一份空白新專案… accept=true" and every P72B check green.
# Run ONLY under the shared WSL lock, e.g. from Windows:
#   wsl -d Ubuntu-24.04 -- bash /mnt/c/Users/Yang/AppData/Local/Temp/claude/D--geometry-axiom/f46787ac-6918-4891-81a1-b3d8a9aa653c/scratchpad/wsl-ci/wsl_locked3.sh run 'bash /mnt/d/geometry-axiom-work/drafts/p72b/repro-ab.sh <A-sha> <B-sha> <out-dir>'
# Clean ext4 clones from the local CI mirror (same as ci_run.py: core.autocrlf=false, detached at the SHA),
# `npm run build` like the CI job, then start_local.py + cdp_test.js. Never pushes; never touches /mnt/d repos.
set -u
A=${1:?A sha}; B=${2:?B sha}; OUT=${3:?out dir}
export PATH=/opt/node/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
export LANG=C.UTF-8 LC_ALL=C.UTF-8 PYTHONIOENCODING=utf-8
REPO=/mnt/d/geometry-axiom
GA=/root/ga-ci
MIRROR="$GA/mirrors/$(printf '%s' "$REPO" | sha1sum | cut -c1-10).git"
ROOT=/root/p72b-repro/$(date +%Y%m%d-%H%M%S)
mkdir -p "$OUT" "$ROOT/shim"
ln -sf /usr/bin/python3 "$ROOT/shim/python"   # tests spawn plain 'python' (same shim as the CI receipts)
export PATH="$ROOT/shim:$PATH"
if [ -d "$MIRROR" ]; then git -C "$MIRROR" fetch -q origin; else mkdir -p "$GA/mirrors"; git clone -q --mirror "$REPO" "$MIRROR"; fi
echo "mirror=$MIRROR root=$ROOT out=$OUT" | tee "$OUT/run.txt"

run() {
  label=$1; sha=$2; port=$3; cdp=$4
  work="$ROOT/$label/repo"; tmp="$ROOT/$label/tmp"; mkdir -p "$tmp" "$tmp/feedback"
  git -c core.autocrlf=false clone -q --no-checkout "$MIRROR" "$work" || return 1
  git -C "$work" -c core.autocrlf=false -c advice.detachedHead=false checkout -q --detach "$sha" || return 1
  head=$(git -C "$work" rev-parse HEAD)
  [ -z "$(git -C "$work" status --porcelain)" ] || { echo "$label: clone not clean"; return 1; }
  echo "== $label head=$head" | tee -a "$OUT/run.txt"
  ( cd "$work" && TMPDIR="$tmp" npm run build > "$OUT/$label.build.log" 2>&1 ) || { echo "$label: build failed" | tee -a "$OUT/run.txt"; return 1; }
  ( cd "$work" && TMPDIR="$tmp" GEOMETRY_FEEDBACK_DIR="$tmp/feedback" python3 -u geometry-web/start_local.py --port "$port" > "$OUT/$label.server.log" 2>&1 ) &
  srv=$!
  up=0
  for _ in $(seq 1 240); do
    if ( cd "$work" && python3 geometry-web/runtime_version.py --probe "$port" > /dev/null 2>&1 ); then up=1; break; fi
    kill -0 "$srv" 2>/dev/null || break
    sleep 1
  done
  if [ "$up" != 1 ]; then echo "$label: server did not come up" | tee -a "$OUT/run.txt"; kill "$srv" 2>/dev/null; wait "$srv" 2>/dev/null; return 1; fi
  t0=$(date +%s)
  ( cd "$work" && ulimit -s 16384 && TMPDIR="$tmp" GEOMETRY_COMPOSITION_ONLY=1 GEOMETRY_CDP_PORT="$cdp" \
      GEOMETRY_TEST_URL="http://127.0.0.1:$port/" GEOMETRY_FEEDBACK_DIR="$tmp/feedback" \
      GEOMETRY_CHROME=/usr/bin/google-chrome GEOMETRY_CHROME_FLAGS=--no-sandbox \
      timeout 1800 node geometry-web/cdp_test.js > "$OUT/$label.log" 2>&1 )
  rc=$?
  kill "$srv" 2>/dev/null; wait "$srv" 2>/dev/null
  {
    echo "$label rc=$rc seconds=$(( $(date +%s) - t0 ))"
    echo "$label: P72 ✓=$(grep -c '^P72 .*✓' "$OUT/$label.log")  P72B ✓=$(grep -c '^P72B .*✓' "$OUT/$label.log")  ✗=$(grep -c '✗' "$OUT/$label.log")"
    grep -n "=== P72B\|Unexpected native dialog\|EXPECTED NATIVE DIALOG\|^FATAL:\|P72B saved artifact\|CDP_SECTIONS\|CDP FLOOR" "$OUT/$label.log" | cut -c1-260 | head -40
  } | tee -a "$OUT/run.txt"
}

run A-unfixed "$A" 18871 9371
run B-fixed "$B" 18872 9372
echo "done; clones kept under $ROOT (delete after review)" | tee -a "$OUT/run.txt"
