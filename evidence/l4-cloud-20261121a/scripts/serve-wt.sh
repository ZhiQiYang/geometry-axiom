#!/bin/bash
# usage: serve-wt.sh <worktree name under scratchpad> <port>   (private test server, not a user's service)
S=/tmp/claude-0/-home-user-geometry-axiom/5c269b74-1aa0-5913-a228-836cc082e79f/scratchpad
wt=$1; port=$2
cd $S/$wt || exit 1
pkill -f "start_local.py --port $port"; pkill -f "serve.py $port"; sleep 2
ulimit -s 16384
export LC_ALL=C.UTF-8
python3 geometry-web/start_local.py --build-only > $S/build-$wt.log 2>&1 || { echo build failed; tail -5 $S/build-$wt.log; exit 1; }
GEOMETRY_FEEDBACK_DIR=$S/fb-$wt nohup python3 -u geometry-web/start_local.py --port $port > $S/server-$wt.log 2>&1 &
for i in $(seq 1 90); do python3 geometry-web/runtime_version.py --probe $port >/dev/null 2>&1 && break; sleep 1; done
python3 geometry-web/runtime_version.py --probe $port
