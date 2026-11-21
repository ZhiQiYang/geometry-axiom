#!/bin/bash
# usage: run_walk.sh <main worktree dir> <port> <output dir> <scratch dir for feedback/logs>
# 每階段前重啟私人測試服務（新程序／新 session），並把 runtime probe 存到輸出目錄。
set -e
here=$(cd "$(dirname "$0")" && pwd)
wt=$1; port=$2; out=$3; tmp=$4
mkdir -p "$out" "$tmp"
export LANG=C.UTF-8 LC_ALL=C.UTF-8
export NODE_PATH=${NODE_PATH:-/opt/node-tools/node_modules}
NODE=${NODE:-/opt/node24/bin/node}
bash "$here/serve-wt.sh" "$wt" "$port" "$tmp/fb-phase1" | tail -1 > "$out/runtime-probe.phase1.json"
(cd "$here" && APP_URL=http://localhost:$port/ OUT="$out" PHASE=1 "$NODE" walk_r03.js) 2>&1 | tee "$out/walk_r03.phase1.log"
bash "$here/serve-wt.sh" "$wt" "$port" "$tmp/fb-phase2" | tail -1 > "$out/runtime-probe.phase2.json"
(cd "$here" && APP_URL=http://localhost:$port/ OUT="$out" PHASE=2 "$NODE" walk_r03.js) 2>&1 | tee "$out/walk_r03.phase2.log"
