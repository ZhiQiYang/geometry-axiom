#!/bin/bash
# usage: serve-wt.sh <main worktree dir> <port> <feedback dir>   (private test server, not a user's service)
wt=$1; port=$2; fb=$3
cd "$wt" || exit 1
pkill -f "start_local.py --port $port"; pkill -f "serve.py $port"; sleep 2
ulimit -s 16384
export LANG=C.UTF-8 LC_ALL=C.UTF-8
export PATH=/opt/node24/bin:$PATH
python3 geometry-web/start_local.py --build-only > "$fb.build.log" 2>&1 || { echo build failed; tail -5 "$fb.build.log"; exit 1; }
mkdir -p "$fb"
GEOMETRY_FEEDBACK_DIR="$fb" nohup python3 -u geometry-web/start_local.py --port $port > "$fb.server.log" 2>&1 &
for i in $(seq 1 120); do python3 geometry-web/runtime_version.py --probe $port >/dev/null 2>&1 && break; sleep 1; done
python3 geometry-web/runtime_version.py --probe $port
