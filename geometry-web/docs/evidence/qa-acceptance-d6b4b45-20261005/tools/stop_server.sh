#!/usr/bin/env bash
# 只停 qa_server.py 在該埠起的那一個服務(含其 bridge 子行程)
here="$(cd "$(dirname "$0")" && pwd)"
python "$here/qa_server.py" stop "${1:?usage: stop_server.sh <port>}"
