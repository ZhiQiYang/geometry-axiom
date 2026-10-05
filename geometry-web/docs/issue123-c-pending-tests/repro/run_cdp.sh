#!/bin/bash
# 用法: run_cdp.sh <label> <export 目錄(win 路徑)>   —— 跑 cdp_test.js(GEOMETRY_CDP_FROM_P31=1:略過 P1–P30,仍涵蓋 P31–結尾含 P35 的 :3976),20 分鐘上限
LABEL=$1; EXP=$2
W="$USERPROFILE/AppData/Local/Temp/geo123c"
mkdir -p "$W/cdp-$LABEL-profile-parent"
cd "$EXP/geometry-web"
export GEOMETRY_TEST_URL="http://127.0.0.1:8861/"
export GEOMETRY_FEEDBACK_DIR="$(cygpath -w "$W/fb")"
export GEOMETRY_CDP_PORT=9361
export GEOMETRY_CDP_FROM_P31=1
export GEOMETRY_CHROME_PROFILE="$(cygpath -w "$W/cdp-$LABEL-profile")"
export GEOMETRY_TEST_SCREENSHOT="$(cygpath -w "$W/cdp-$LABEL-shot.png")"
START=$(date +%s)
timeout 1200 node cdp_test.js > "$W/cdp-$LABEL.log" 2>&1
RC=$?
echo "EXIT=$RC SECONDS=$(( $(date +%s) - START ))" >> "$W/cdp-$LABEL.log"
