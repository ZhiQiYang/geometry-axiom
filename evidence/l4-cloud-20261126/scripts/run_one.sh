#!/bin/bash
# usage（非 root）: run_one.sh <walk 腳本名> <port> <輸出目錄>
# 以 Node 24 執行單一 walk；輸出目錄的 screens/ 與結果 JSON 由腳本寫入。
# 沿用 evidence/l4-cloud-20261123/scripts/run_one.sh（已含 pipefail）；改用 PATH 上的 node 並檢查 v24。
# walk 任一核對項 FAIL 時 node 以非 0 結束，pipefail 讓本腳本也以非 0 結束。
# LOG_NAME 可指定記錄檔名（同一支 walk 跑多個項目時用），預設 <walk 名>.log。
set -eo pipefail
here=$(cd "$(dirname "$0")" && pwd)
[ "$(id -u)" != 0 ] || { echo "must run as non-root"; exit 1; }
node -v | grep -q '^v24\.' || { echo "node 24 required"; exit 1; }
export LANG=C.UTF-8 LC_ALL=C.UTF-8 NODE_PATH=${NODE_PATH:-/tmp/nodetools/node_modules}
mkdir -p "$3/screens"
cd "$here" && APP_URL=http://localhost:$2/ OUT="$3" node "$1" 2>&1 | tee "$3/${LOG_NAME:-${1%.js}.log}"
