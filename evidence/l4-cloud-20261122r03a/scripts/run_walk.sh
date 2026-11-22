#!/bin/bash
# usage（非 root 使用者執行）: run_walk.sh <main worktree dir> <port> <output dir> <scratch dir under $TMPDIR> <repo root>
# 每階段前重啟私人測試服務（新程序／新 session），並把 runtime probe 存到輸出目錄。
# 第三階段的 v1 輸入是第一片 L4 另存的 r03.gcanvas（evidence/l4-cloud-20261121r03/main-3ef07683/），原樣複製為 v1-input.gcanvas。
set -e
here=$(cd "$(dirname "$0")" && pwd)
wt=$1; port=$2; out=$3; tmp=$4; repo=$5
mkdir -p "$out" "$tmp"
export LANG=C.UTF-8 LC_ALL=C.UTF-8
export NODE_PATH=${NODE_PATH:-/opt/node-tools/node_modules}
NODE=${NODE:-/opt/node24/bin/node}
first="$repo/evidence/l4-cloud-20261121r03/main-3ef07683"
cp "$first/r03.gcanvas" "$out/v1-input.gcanvas"
for ph in 1 2 3; do
  bash "$here/serve-wt.sh" "$wt" "$port" "$tmp/fb-phase$ph" | tail -1 > "$out/runtime-probe.phase$ph.json"
  (cd "$here" && APP_URL=http://localhost:$port/ OUT="$out" PHASE=$ph FIRST_RESULT="$first/walk_r03.phase1.result.json" "$NODE" walk_r03a.js) 2>&1 | tee "$out/walk_r03a.phase$ph.log"
done
