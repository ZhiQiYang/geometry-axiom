#!/usr/bin/env bash
# Rerun #134 P88 (GEOMETRY_GRID_SYSTEM_ONLY) 3x on exact head, isolated worktree/port/profile.
# v2: singleton lock, no pipes on service start, unique CDP port + profile per run.
set -u
LOCK=/c/Users/Yang/AppData/Local/Temp/geobqa/p88rerun.lock
mkdir "$LOCK" 2>/dev/null || { echo "another instance holds $LOCK"; exit 9; }
echo $$ > "$LOCK/pid"
trap 'rm -rf "$LOCK"' EXIT
HEAD=77c3847f32b2ba0616bab6c8d0c8370082c4941c
WT='D:\geo-bqa-134r'
PORT=8874
SVC='D:\geometry-axiom-bqa\geometry-web\docs\evidence\browser-acceptance-20261006\env\svc.ps1'
W='C:\Users\Yang\AppData\Local\Temp\geobqa'
OUT=/d/geometry-axiom-bqa/geometry-web/docs/evidence/browser-acceptance-20261006/pr134/p88-rerun
mkdir -p "$OUT"
git -C /d/geometry-axiom worktree add --detach "$WT" $HEAD >/dev/null 2>&1 || true
echo "head=$(git -C "$WT" rev-parse HEAD) tree=$(git -C "$WT" rev-parse HEAD^{tree}) script_pid=$$" > "$OUT/versions.txt"
for i in 1 2 3; do
  CDP=$((9480 + i))
  echo "== run $i $(date -u +%FT%TZ) cdp=$CDP" >> "$OUT/summary.txt"
  powershell -NoProfile -File "$SVC" start "$WT" $PORT > "$OUT/svc-start-$i.txt" 2>&1 < /dev/null
  cat "$OUT/svc-start-$i.txt" >> "$OUT/summary.txt"
  curl -sS --max-time 20 "http://127.0.0.1:$PORT/runtime" > "$OUT/runtime-$i.json" 2>> "$OUT/summary.txt"
  START=$(date +%s)
  ( cd /d/geo-bqa-134r && GEOMETRY_FEEDBACK_DIR="$W\\fb-$PORT" GEOMETRY_TEST_URL=http://localhost:$PORT/ GEOMETRY_GRID_SYSTEM_ONLY=1 \
    GEOMETRY_CDP_PORT=$CDP GEOMETRY_CHROME_PROFILE="$W\\profile-p88r2-$i" GEOMETRY_GRID_RULE_SCREENSHOT_DIR="$W\\p88r2-shots-$i" \
    timeout 1500 node geometry-web/cdp_test.js ) > "$OUT/p88-run$i.log" 2>&1 < /dev/null
  RC=$?
  echo "run $i exit=$RC secs=$(( $(date +%s) - START ))" >> "$OUT/summary.txt"
  grep -E '^(FATAL:|CDP_RESULT)' "$OUT/p88-run$i.log" | cut -c1-400 >> "$OUT/summary.txt"
  powershell -NoProfile -File "$SVC" stop x $PORT >> "$OUT/summary.txt" 2>&1 < /dev/null
done
git -C /d/geometry-axiom worktree remove "$WT" && echo "worktree removed" >> "$OUT/summary.txt"
echo "ALL DONE" >> "$OUT/summary.txt"
