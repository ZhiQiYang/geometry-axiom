#!/usr/bin/env bash
# 用法: start_server.sh <port 8800-8899>   起隔離服務並跑 probe;stop 用 stop_server.sh <port>
set -e
here="$(cd "$(dirname "$0")" && pwd)"
port="${1:?usage: start_server.sh <port>}"
python "$here/qa_server.py" start "$port"
python "$here/qa_server.py" probe "$port"
