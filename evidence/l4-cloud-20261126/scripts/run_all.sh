#!/bin/bash
# usage（非 root，TMPDIR 已設）: run_all.sh <main 工作樹 A（R16 用）> <main 工作樹 B（R03 用）> <輸出目錄>
# A. R16：重啟私人服務（port 18881）一次、存 probe，跑 walk_r16_height.js（三個尺寸各開新瀏覽器）。
# B. R03：每個項目、每個階段前都重啟私人服務（port 18871，新程序／新 session）並存 probe；
#    第一階段 6 項各開新瀏覽器另存 .gcanvas；第二階段 6 項各在新服務程序＋新瀏覽器冷開；最後跑 oracle 逐支對照。
# 任一 walk 或對照失敗記 rc=1，其餘照跑，最後以非 0 結束（set -eo pipefail；probe 不是 fresh:true 則立即停止）。
set -eo pipefail
here=$(cd "$(dirname "$0")" && pwd)
wtA=$1; wtB=$2; out=$3
[ -n "$out" ] || { echo "usage: run_all.sh <wtA> <wtB> <out>"; exit 2; }
mkdir -p "$out/r16/screens" "$out/r03/screens"
probe() { # <worktree> <port> <feedback dir> <probe file>
  bash "$here/serve-wt.sh" "$1" "$2" "$3" | tail -1 > "$4"
  grep -q '"fresh": true' "$4" || { echo "probe not fresh: $4"; cat "$4"; exit 1; }
}
rc=0
probe "$wtA" 18881 "$TMPDIR/fb-r16" "$out/r16/runtime-probe.json"
WT="$wtA" bash "$here/run_one.sh" walk_r16_height.js 18881 "$out/r16" > /dev/null || { echo "walk_r16_height FAILED"; rc=1; }
(cd "$wtA" && python3 geometry-web/runtime_version.py --probe 18881) > "$out/r16/runtime-probe.after.json"
items="corner-max-min corner-min-max corner-max-max along-u size-2500x3000 recipes"
for ph in 1 2; do
  for it in $items; do
    probe "$wtB" 18871 "$TMPDIR/fb-r03-$it-p$ph" "$out/r03/runtime-probe.$it.phase$ph.json"
    PHASE=$ph ITEM=$it LOG_NAME="walk_r03b.$it.phase$ph.log" bash "$here/run_one.sh" walk_r03b.js 18871 "$out/r03" > /dev/null || { echo "walk_r03b $it phase$ph FAILED"; rc=1; }
  done
done
python3 -I "$here/oracle_compare_r03b.py" "$wtB" "$out/r03" > "$out/r03/oracle-compare.log" 2>&1 || { echo "oracle compare FAILED"; rc=1; }
for wt in "$wtA" "$wtB"; do (cd "$wt" && echo "$wt" && git rev-parse HEAD && git status --short | wc -l); done > "$out/worktree-state.txt"
echo "run_all rc=$rc"
exit $rc
