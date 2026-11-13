#!/usr/bin/env bash
set -euo pipefail
test -e /proc/$$/fd/7
test "$(stat -L -c %d:%i /proc/$$/fd/7)" = "$(stat -c %d:%i /run/lock/ga-wsl-v3.lock)"
if [ "${1:-}" != inner ]; then
  exec unshare --mount --propagation private bash "$0" inner
fi
mkdir -p /var/tmp/geo261-baseline-a898ad6e/.git/geo261-parameters-legacy-tmp
mount --bind /var/tmp/geo261-baseline-a898ad6e/.git/geo261-parameters-legacy-tmp /tmp
mkdir -p /tmp/geo261-bin
test -e /tmp/geo261-bin/python || ln -s /usr/bin/python3 /tmp/geo261-bin/python
export GEOMETRY_TEST_BRIDGE=/tmp/geometry-tests/bridge
export GEOMETRY_ENGINEERING_BRIDGE=/tmp/geometry-tests/bridge
export GEOMETRY_MODEL_BASE=/tmp/geometry-tests/model-base
export TMPDIR=/tmp
ulimit -s 16384
exec python3 -u /mnt/d/geometry-axiom-work/geo261-evidence/p1/exercise-parameters-legacy.py
