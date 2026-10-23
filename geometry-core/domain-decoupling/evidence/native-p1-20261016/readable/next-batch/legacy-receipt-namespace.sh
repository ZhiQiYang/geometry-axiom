#!/usr/bin/env bash
set -euo pipefail
test -e /proc/$$/fd/7
test "$(stat -L -c %d:%i /proc/$$/fd/7)" = "$(stat -c %d:%i /run/lock/ga-wsl-v3.lock)"
mount --bind "$1" /tmp
mkdir -p /tmp/geo261-bin
ln -s /usr/bin/python3 /tmp/geo261-bin/python
export PATH=/tmp/geo261-bin:/opt/node/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
export GEOMETRY_TEST_BRIDGE=/tmp/geometry-tests/bridge
export GEOMETRY_ENGINEERING_BRIDGE=/tmp/geometry-tests/bridge
export GEOMETRY_MODEL_BASE=/tmp/geometry-tests/model-base
export TMPDIR=/tmp
export PYTHONDONTWRITEBYTECODE=1
ulimit -s 16384
exec python3 -u "$(dirname "$0")/exercise-legacy-receipt.py" "$2"
