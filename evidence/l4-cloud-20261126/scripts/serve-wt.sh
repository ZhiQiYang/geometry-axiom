#!/bin/bash
# usage: serve-wt.sh <main worktree dir> <port> <feedback dir>   (private test server, not a user's service)
# 改自 evidence/l4-cloud-20261123/scripts/serve-wt.sh：要求非 root、回報目錄在 $TMPDIR 底下、Node 24。
# 唯一差異：本機沒有 /opt/node24，改用 PATH 上的 node（仍檢查 v24.）；加 pipefail。
set -eo pipefail
wt=$1; port=$2; fb=$3
[ "$(id -u)" != 0 ] || { echo "must run as non-root"; exit 1; }
case "$fb" in "${TMPDIR:?TMPDIR unset}"/*) ;; *) echo "feedback dir must be under TMPDIR=$TMPDIR"; exit 1;; esac
cd "$wt"
pkill -u "$(id -u)" -f "start_local.py --port $port" || true; pkill -u "$(id -u)" -f "serve.py $port" || true; sleep 2
ulimit -s 16384
export LANG=C.UTF-8 LC_ALL=C.UTF-8
node -v | grep -q '^v24\.' || { echo "node 24 required"; exit 1; }
python3 geometry-web/start_local.py --build-only > "$fb.build.log" 2>&1 || { echo build failed; tail -5 "$fb.build.log"; exit 1; }
mkdir -p "$fb"
GEOMETRY_FEEDBACK_DIR="$fb" nohup python3 -u geometry-web/start_local.py --port "$port" > "$fb.server.log" 2>&1 &
for i in $(seq 1 180); do python3 geometry-web/runtime_version.py --probe "$port" >/dev/null 2>&1 && break; sleep 1; done
python3 geometry-web/runtime_version.py --probe "$port"
