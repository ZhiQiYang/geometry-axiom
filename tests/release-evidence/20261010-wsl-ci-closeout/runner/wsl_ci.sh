#!/bin/bash
# WSL CI-equivalent runner.  Usage (from Windows):
#   wsl -d Ubuntu-24.04 -- bash /mnt/c/Users/Yang/AppData/Local/Temp/claude/D--geometry-axiom/f46787ac-6918-4891-81a1-b3d8a9aa653c/scratchpad/wsl-ci/wsl_ci.sh <sha> <job-filter>
# job-filter: all | native | assembly,documents,grid,canvas,space,timber  (names come from the SHA's own workflow)
# See ci_run.py docstring for WSL_CI_* environment overrides.
set -u
if [ "$#" -lt 2 ]; then
  echo "usage: wsl_ci.sh <sha> <job-filter>" >&2
  exit 64
fi
# Linux-only PATH: WSL would otherwise resolve npm/python/node to the Windows ones under /mnt/c.
export PATH=/opt/node/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
export LANG=C.UTF-8 LC_ALL=C.UTF-8 PYTHONIOENCODING=utf-8
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec python3 -u "$here/ci_run.py" "$@"
