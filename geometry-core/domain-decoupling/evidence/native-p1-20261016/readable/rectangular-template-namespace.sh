#!/usr/bin/env bash
set -euo pipefail
test -e /proc/$$/fd/7
test "$(stat -L -c %d:%i /proc/$$/fd/7)" = "$(stat -c %d:%i /run/lock/ga-wsl-v3.lock)"
SOURCE_ROOT="$1"
EVIDENCE_OUT="$2"
PRIVATE_TMP="$3"
mount --bind "$PRIVATE_TMP" /tmp
mkdir -p /tmp/geo261-bin
test -e /tmp/geo261-bin/python || ln -s /usr/bin/python3 /tmp/geo261-bin/python
export TMPDIR=/tmp
export GEO261_RECTANGULAR_EVIDENCE="$EVIDENCE_OUT/native-commands.json"
ulimit -s 16384
cd "$SOURCE_ROOT"
result=0
python3 -u tests/run_all.py --only rectangular_template || result=$?
if [ -d /tmp/geometry-tests/run_all-logs ]; then
  cp -a /tmp/geometry-tests/run_all-logs "$EVIDENCE_OUT/run-all-logs"
fi
exit "$result"
