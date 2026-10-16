#!/usr/bin/env bash
set -euo pipefail
CHECKOUT=/var/tmp/geo261-baseline-a898ad6e
EVIDENCE=/mnt/d/geometry-axiom-work/geo261-evidence/p1
mount --bind "$CHECKOUT/.git/geo261-environment/tmp" /tmp
ip link set lo up
mkdir -p /tmp/geo261-bin
if [ ! -e /tmp/geo261-bin/python ]; then
  ln -s /usr/bin/python3 /tmp/geo261-bin/python
fi
export PATH=/tmp/geo261-bin:/opt/node/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
export GEOMETRY_FEEDBACK_DIR=/tmp/geo261-feedback
export GEOMETRY_MODEL_BASE=/tmp/geometry-tests/model-base
export GEOMETRY_TEST_BRIDGE=/tmp/geometry-tests/bridge
export GEOMETRY_ENGINEERING_BRIDGE=/tmp/geometry-tests/bridge
export PYTHONDONTWRITEBYTECODE=1
ulimit -s 16384
cd "$CHECKOUT"
exec python3 -u "$EVIDENCE/run-stages.py"
