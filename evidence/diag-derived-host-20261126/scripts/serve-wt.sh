#!/bin/bash
# 啟動用全新的回報目錄；停止時用同一組參數加 --stop。不得接管既有服務。
set -eu
[ "$(id -u)" != 0 ] || { echo '須以非 root 執行' >&2; exit 1; }
helper=$(dirname "$(realpath "$0")")/owned_server.py
if [ "${1:-}" = --stop ]; then
    exec python3 -I "$helper" "$@"
fi
ulimit -s 16384
export LANG=C.UTF-8 LC_ALL=C.UTF-8
export PATH=/opt/node24/bin:$PATH
node -v | grep -q '^v24\.' || { echo '需要 Node 24' >&2; exit 1; }
exec python3 -I "$helper" "$@"
