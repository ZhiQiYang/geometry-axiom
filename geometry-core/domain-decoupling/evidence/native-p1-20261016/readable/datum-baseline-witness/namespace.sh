#!/usr/bin/env bash
set -euo pipefail
test -e /proc/$$/fd/7
test "$(stat -L -c %d:%i /proc/$$/fd/7)" = "$(stat -c %d:%i /run/lock/ga-wsl-v3.lock)"
if [ "${1:-}" != inner ]; then
  exec unshare --mount --net --propagation private bash "$0" inner
fi
mount --bind /var/tmp/geo261-baseline-a898ad6e/.git/geo261-environment/tmp /tmp
export PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
export TMPDIR=/tmp
export PYTHONDONTWRITEBYTECODE=1
ulimit -s 16384
exec python3 -u /mnt/d/geometry-axiom-work/geo261-evidence/p1/datum-baseline-witness/run.py
