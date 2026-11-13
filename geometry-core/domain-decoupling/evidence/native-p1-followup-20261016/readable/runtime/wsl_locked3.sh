#!/bin/bash
# v3 (2026-10-11): serialize heavy WSL work.  NEW FILE on purpose: never overwrite a lock script that may be executing.
#   wsl -d Ubuntu-24.04 -- bash <scratchpad>/wsl-ci/wsl_locked3.sh ci <sha> <job-filter>
#   wsl -d Ubuntu-24.04 -- bash <scratchpad>/wsl-ci/wsl_locked3.sh run '<shell command>'
# One lock (/run/lock/ga-wsl-v3.lock) with an inode re-check, then wait until no foreign heavy process runs.
# Heavy = executable cc1 / chrome / node, or a python whose script is ci_run.py, ci_job.py or run_all.py.
# Waiting wrappers (any version) and flock processes are never counted.  Never delete /run/lock/ga-* or /tmp/ga-*.
set -u
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
lock=/run/lock/ga-wsl-v3.lock
holder=/run/lock/ga-wsl-v3.holder
mkdir -p /run/lock
while :; do
  exec 7>>"$lock"
  if ! flock -n 7; then
    echo "[wsl_locked3] waiting; holder: $(cat "$holder" 2>/dev/null)" >&2
    flock 7
  fi
  a=$(stat -L -c %d:%i /proc/$$/fd/7 2>/dev/null); b=$(stat -c %d:%i "$lock" 2>/dev/null)
  [ -n "$a" ] && [ "$a" = "$b" ] && break
  echo "[wsl_locked3] lock file replaced while waiting; retrying" >&2
  exec 7>&-
done

heavy_pids() {
  ps -eo pid=,comm=,args= | awk -v me="$$" '
    $1 == me { next }
    $2 == "cc1" || $2 == "chrome" || $2 == "node" { print $1; next }
    $2 ~ /^python/ && ($0 ~ /ci_run[.]py/ || $0 ~ /ci_job[.]py/ || $0 ~ /run_all[.]py/) { print $1 }'
}
waited=0
while p=$(heavy_pids | tr '\n' ' ') && [ -n "${p// /}" ]; do
  [ $((waited % 300)) -eq 0 ] && echo "[wsl_locked3] lock held; waiting for foreign heavy processes: $p" >&2
  sleep 15; waited=$((waited + 15))
done
[ "$waited" -gt 0 ] && echo "[wsl_locked3] quiesced after ${waited}s" >&2

echo "pid=$$ start=$(date -u +%FT%TZ) label=${WSL_CI_LABEL:-} args=$*" > "$holder"
mode="$1"; shift
case "$mode" in
  ci)  bash "$here/wsl_ci.sh" "$@"; rc=$? ;;
  run) bash -lc "$1"; rc=$? ;;
  *)   echo "usage: wsl_locked3.sh ci <sha> <jobs> | run '<cmd>'" >&2; rc=64 ;;
esac
: > "$holder"
exit $rc
