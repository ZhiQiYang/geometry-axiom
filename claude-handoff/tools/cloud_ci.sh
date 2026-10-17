#!/bin/bash
# Cloud pre-run of one job from the SHA's own .github/workflows/integration-tests.yml.
# NOT an official WSL receipt.  Usage: cloud_ci.sh <sha> <job> <port>
#   job: native | assembly | documents | grid | canvas | space | timber
# Each job gets its own clean worktree and TMPDIR so jobs can run side by side.
set -u
sha="${1:?sha}"; job="${2:?job}"; port="${3:-18839}"
# CLOUD_SCRATCH: where logs go (default: $HOME/cloud-ci); CLOUD_REPO: the repository clone (default: current git top level).
SP="${CLOUD_SCRATCH:-$HOME/cloud-ci}"
REPO="${CLOUD_REPO:-$(git rev-parse --show-toplevel)}"
out=$SP/ci/${sha:0:8}/$job
# Chrome crashes when TMPDIR is long (unix socket path limit), so TMPDIR is a short /tmp dir.
short=/tmp/gci/${sha:0:8}-$job
rm -rf "$out" "$short"; mkdir -p "$out/bin" "$short"
wt=$out/repo
git -C "$REPO" worktree add -q --detach "$wt" "$sha" || exit 70
ln -sf /usr/bin/python3 "$out/bin/python"
export TMPDIR="$short" PATH="$out/bin:/opt/node22/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
export LANG=C.UTF-8 LC_ALL=C.UTF-8 PYTHONIOENCODING=utf-8
ulimit -s 16384
cd "$wt" || exit 70
{
  echo "job=$job sha=$(git rev-parse HEAD) start=$(date -u +%FT%TZ)"
  echo "env: $(. /etc/os-release; echo $PRETTY_NAME) gcc=$(gcc -dumpfullversion) $(python3 --version) node=$(node --version) chrome=$(${CLOUD_CHROME:-/opt/pw-browsers/chromium-1194/chrome-linux/chrome} --version 2>/dev/null)"
} > "$out/run.log"
t0=$(date +%s)
if [ "$job" = native ]; then
  timeout 2700 python3 -u tests/run_all.py --build > "$out/job.log" 2>&1
  rc=$?
else
  export GEOMETRY_TEST_URL="http://127.0.0.1:$port/" GEOMETRY_FEEDBACK_DIR="$TMPDIR/feedback"
  export GEOMETRY_CHROME="${CLOUD_CHROME:-/opt/pw-browsers/chromium-1194/chrome-linux/chrome}" GEOMETRY_CHROME_FLAGS=--no-sandbox
  export GEOMETRY_BROWSER_SUITE=$job GEOMETRY_GRID_SYSTEM_SCREENSHOT_DIR="$TMPDIR/grid-screens" GEOMETRY_DOCUMENT_SCREENSHOT_DIR="$TMPDIR/doc-screens"
  unset GEOMETRY_WAIT_TRACE GEOMETRY_WAIT_TRACE_RUN_ID
  python3 geometry-web/start_local.py --build-only > "$out/build.log" 2>&1 || { echo "build failed" >> "$out/run.log"; rc=71; }
  if [ -z "${rc-}" ]; then
    python3 -u geometry-web/start_local.py --port "$port" > "$out/server.log" 2>&1 &
    server=$!
    for attempt in $(seq 1 60); do
      kill -0 "$server" 2>/dev/null || break
      python3 geometry-web/runtime_version.py --probe "$port" > /dev/null 2>&1 && break
      sleep 1
    done
    python3 geometry-web/runtime_version.py --probe "$port" >> "$out/run.log" 2>&1
    off=$(( port - 18000 ))
    case "$job" in
      assembly) GEOMETRY_CDP_PORT=$((9300+off)) GEOMETRY_ASSEMBLY_ONLY=1 timeout 2700 node geometry-web/cdp_test.js ;;
      grid) GEOMETRY_CDP_PORT=$((9300+off)) GEOMETRY_GRID_SYSTEM_ONLY=1 timeout 2700 node geometry-web/cdp_test.js ;;
      canvas) GEOMETRY_CDP_PORT=$((9300+off)) timeout 6300 node geometry-web/cdp_test.js ;;
      space) GEOMETRY_CDP_PORT=$((9300+off)) timeout 2700 node geometry-web/space_model_test.js ;;
      timber) GEOMETRY_CDP_PORT=$((9300+off)) GEOMETRY_TIMBER_ONLY=1 timeout 3600 node geometry-web/space_model_test.js ;;
      documents) GEOMETRY_CDP_PORT=$((9300+off)) timeout 1800 node geometry-web/documents_browser_test.js ;;
      *) echo "Unknown browser suite"; false ;;
    esac > "$out/job.log" 2>&1
    rc=$?
    kill "$server" 2>/dev/null; wait "$server" 2>/dev/null
  fi
fi
echo "rc=$rc seconds=$(( $(date +%s) - t0 )) end=$(date -u +%FT%TZ)" >> "$out/run.log"
tail -8 "$out/job.log" >> "$out/run.log"
cd "$SP"; git -C "$REPO" worktree remove --force "$wt"; rm -rf "$short"
cat "$out/run.log"
exit $rc
