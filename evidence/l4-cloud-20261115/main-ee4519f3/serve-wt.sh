#!/bin/bash
# usage: serve-wt.sh <worktree name under scratchpad> <port>   (private test server, not a user's service)
S=/tmp/claude-0/-home-user-geometry-axiom/c161fbcc-185e-5abd-ba3d-eaec6a803bff/scratchpad
wt=$1; port=$2
cd $S/$wt || exit 1
pkill -f "start_local.py --port $port"; pkill -f "serve.py $port"; sleep 2
ulimit -s 16384
python3 geometry-web/start_local.py --build-only > $S/build-$wt.log 2>&1 || { echo build failed; tail -5 $S/build-$wt.log; exit 1; }
GEOMETRY_FEEDBACK_DIR=$S/fb-$wt nohup python3 -u geometry-web/start_local.py --port $port > $S/server-$wt.log 2>&1 &
for i in $(seq 1 60); do python3 geometry-web/runtime_version.py --probe $port >/dev/null 2>&1 && break; sleep 1; done
python3 geometry-web/runtime_version.py --probe $port
