#!/bin/bash
# 用法: run_space.sh <label> <export 目錄(win 路徑)> —— 跑 space_model_test.js 的 space-flow 群組(含 GEO210 @690x668、390x844)
LABEL=$1; EXP=$2
W="$USERPROFILE/AppData/Local/Temp/geo123c"
cd "$EXP/geometry-web"
export GEOMETRY_TEST_URL="http://127.0.0.1:8861/"
export GEOMETRY_FEEDBACK_DIR="$(cygpath -w "$W/fb")"
export GEOMETRY_CDP_PORT=9362
export GEOMETRY_SPACE_FLOW_ONLY=1
export GEOMETRY_SPACE_TEST_DIR="$(cygpath -w "$W/space-$LABEL")"
START=$(date +%s)
timeout 1200 node space_model_test.js > "$W/space-$LABEL.log" 2>&1
echo "EXIT=$? SECONDS=$(( $(date +%s) - START ))" >> "$W/space-$LABEL.log"
