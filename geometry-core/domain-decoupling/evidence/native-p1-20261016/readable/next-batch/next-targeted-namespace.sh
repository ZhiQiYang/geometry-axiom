#!/usr/bin/env bash
set -euo pipefail
test -e /proc/$$/fd/7
test "$(stat -L -c %d:%i /proc/$$/fd/7)" = "$(stat -c %d:%i /run/lock/ga-wsl-v3.lock)"
if [ "${1:-}" != inner ]; then
  exec unshare --mount --net --propagation private bash "$0" inner
fi
mount --bind /var/tmp/geo261-baseline-a898ad6e/.git/geo261-environment/tmp /tmp
ip link set lo up
mkdir -p /tmp/geo261-bin
test -e /tmp/geo261-bin/python || ln -s /usr/bin/python3 /tmp/geo261-bin/python
export PATH=/tmp/geo261-bin:/opt/node/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
export GEOMETRY_MODEL_BASE=/tmp/geometry-tests/model-base
export GEOMETRY_TEST_BRIDGE=/tmp/geometry-tests/bridge
export GEOMETRY_ENGINEERING_BRIDGE=/tmp/geometry-tests/bridge
export GEOMETRY_FEEDBACK_DIR=/tmp/geo261-feedback
export PYTHONDONTWRITEBYTECODE=1
ulimit -s 16384
exec python3 -u /mnt/d/geometry-axiom-work/geo261-evidence/p1/next-batch/run-next-stages.py
