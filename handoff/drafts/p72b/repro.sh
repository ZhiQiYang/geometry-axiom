#!/bin/bash
# P72B minimal reproduction + control (GEO-261 integration head 09ab5f79).
# Written 2026-10-20 during a read-only analysis; NOT executed yet.
# Run ONLY when WSL is free, under the shared lock, e.g. from Windows:
#   wsl -d Ubuntu-24.04 -- bash /mnt/c/Users/Yang/AppData/Local/Temp/claude/D--geometry-axiom/f46787ac-6918-4891-81a1-b3d8a9aa653c/scratchpad/wsl-ci/wsl_locked3.sh run 'bash /mnt/d/geometry-axiom-work/drafts/p72b/repro.sh /root/p72b-repro /root/p72b-repro-out'
# $1 = a DISPOSABLE clean checkout of 09ab5f793e97a6be1a0a9e0c13d6ec7677d382e1 on the Linux filesystem
#      (the native binaries are built/reused by start_local.py through its hash cache).
# $2 = output directory for logs.
# Expected:
#   A-unpatched : P72 passes, "=== P72B" first check passes, then
#                 "Unexpected native dialog at === P72B ...: confirm 建立一份空白新專案…" (same as the 09ab5f79 canvas job).
#                 Because GEOMETRY_COMPOSITION_ONLY skips P22 and P53, this also proves the failure does not depend on
#                 P22's window.confirm spy or P53's reload: it is deterministic.
#   B-patched   : "[EXPECTED NATIVE DIALOG] 建立一份空白新專案… accept=true", then P72B continues
#                 ("更名預覽未先改 World" …). Any later red is a NEW finding (P72B has never run past this point).
#                 A fully green P72B prints 50 "P72B … ✓" lines (17 check() sites; 5 of them run 7x, one 4x).
# NOTE: partial mode never compares cdp_sections.golden.json. In the FULL canvas run cdp_floor.sectionOf()
#       files "=== P72B" under section P72 (regex P\d+), so the golden P72=52 (exact) becomes 52+50=102.
#       Without patch-golden.diff (or GEOMETRY_CDP_UPDATE_GOLDEN=1 on a green full run) the full job stays red.
set -u
repo=${1:?usage: repro.sh <clean-09ab5f79-checkout> <out-dir>}
out=${2:?usage: repro.sh <clean-09ab5f79-checkout> <out-dir>}
patch=/mnt/d/geometry-axiom-work/drafts/p72b/patch.diff
export PATH=/opt/node/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
export LANG=C.UTF-8 LC_ALL=C.UTF-8 PYTHONIOENCODING=utf-8
mkdir -p "$out/shim"
ln -sf /usr/bin/python3 "$out/shim/python"   # tests spawn plain 'python' (same shim as the CI receipts)
export PATH="$out/shim:$PATH"
cd "$repo" || exit 2
[ "$(git rev-parse HEAD)" = 09ab5f793e97a6be1a0a9e0c13d6ec7677d382e1 ] || { echo "wrong HEAD"; exit 2; }
git diff --quiet && git diff --cached --quiet || { echo "checkout is not clean"; exit 2; }

run() {
  label=$1
  port=18871
  fb=$(mktemp -d /tmp/p72b-feedback-XXXXXX)
  GEOMETRY_FEEDBACK_DIR="$fb" python3 -u geometry-web/start_local.py --port "$port" > "$out/$label.server.log" 2>&1 &
  srv=$!
  for _ in $(seq 1 120); do
    python3 geometry-web/runtime_version.py --probe "$port" > /dev/null 2>&1 && break
    kill -0 "$srv" 2>/dev/null || { echo "$label: server died"; cat "$out/$label.server.log"; return 1; }
    sleep 1
  done
  GEOMETRY_COMPOSITION_ONLY=1 GEOMETRY_CDP_PORT=9371 \
  GEOMETRY_TEST_URL="http://127.0.0.1:$port/" GEOMETRY_FEEDBACK_DIR="$fb" \
  GEOMETRY_CHROME=/usr/bin/google-chrome GEOMETRY_CHROME_FLAGS=--no-sandbox \
    timeout 1500 node geometry-web/cdp_test.js > "$out/$label.log" 2>&1
  rc=$?
  kill "$srv" 2>/dev/null; wait "$srv" 2>/dev/null
  echo "== $label rc=$rc"
  grep -n "=== P72B\|Unexpected native dialog\|EXPECTED NATIVE DIALOG\|^P72B \|^FATAL\|CDP_RESULT" "$out/$label.log" | cut -c1-240 | head -60
  echo "$label: P72 ✓=$(grep -c '^P72 .*✓' "$out/$label.log")  P72B ✓=$(grep -c '^P72B .*✓' "$out/$label.log")  (green target: 52 / 50)"
}

run A-unpatched
git apply --check "$patch" && git apply "$patch" && run B-patched
git checkout -- geometry-web/cdp_test.js geometry-web/grid_inspector_rename_test.js
git diff --quiet || echo "WARNING: checkout not restored"
