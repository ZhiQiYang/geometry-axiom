#!/bin/bash
# usage（非 root）: run_one.sh <walk 腳本名> <port> <輸出目錄>
# 以 Node 24 執行單一 walk；輸出目錄的 screens/ 與結果 JSON 由腳本寫入。
set -e
here=$(cd "$(dirname "$0")" && pwd)
[ "$(id -u)" != 0 ] || { echo "must run as non-root"; exit 1; }
export LANG=C.UTF-8 LC_ALL=C.UTF-8 NODE_PATH=${NODE_PATH:-/opt/node-tools/node_modules}
mkdir -p "$3/screens"
cd "$here" && APP_URL=http://localhost:$2/ OUT="$3" /opt/node24/bin/node "$1" 2>&1 | tee "$3/${1%.js}.log"
