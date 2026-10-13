#!/bin/bash
# Run the Q5 card-click probe against one or more SHAs in ext4 clones.
# Usage: run_q5.sh [sha ...]
# With no arguments, runs main, the chain tip, and fix/closeout-wsl-red-20261010
# when that branch exists and is a different commit from the tip.
set -u
export PATH=/opt/node/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
export LANG=C.UTF-8 LC_ALL=C.UTF-8 PYTHONIOENCODING=utf-8
export Q5_PROBE=1

SRC=/mnt/d/geometry-axiom
ROOT=/root/q5-clones
OUT=/mnt/c/Users/Yang/AppData/Local/Temp/claude/D--geometry-axiom/f46787ac-6918-4891-81a1-b3d8a9aa653c/scratchpad/q5-probe
PROBE="$OUT/q5_card_second_click.js"
MAIN=5cc1ffa1ee85120eca14258b86b715151cad274f
TIP=72a3cbf44814d86606531e6fcbd811aeab11548f

busy_lines() {
  # Match the live worker. Skip this awk itself: its argv contains the same
  # needles. A bash -lc line that only names start_local.py stays after that
  # process has exec'd into an idle serve.py; that is not a compile or a
  # browser test, and waiting on it never ends.
  ps -eo comm,args | awk '
    $1 == "awk" || $1 == "ps" { next }
    $1 ~ /^(cc1|gcc|g\+\+|clang|ld)$/ { print; next }
    index($0, "tests/run_all.py") { print; next }
    index($0, "cdp_test.js") { print; next }
    index($0, "space_model_test.js") { print; next }
    index($0, "documents_browser_test.js") { print; next }
    index($0, "_unittest_runner.py") { print; next }
    index($0, "section_profile_mutation") { print; next }
    index($0, "npm run build") || index($0, "npm exec") { print; next }
    $1 == "python3" && index($0, "start_local.py") { print; next }
    ($1 ~ /chrome/ || index($0, "/opt/google/chrome/chrome") || index($0, "google-chrome")) && index($0, "crashpad") == 0 { print; next }
  ' || true
}

wait_quiet() {
  local i line
  for i in $(seq 1 360); do
    line=$(busy_lines)
    if [ -z "$line" ]; then
      echo "[q5] quiet after ${i} checks load=$(cut -d' ' -f1-3 /proc/loadavg)"
      return 0
    fi
    echo "[q5] waiting for foreign compile/test:"
    echo "$line" | head -n 8
    sleep 5
  done
  echo "[q5] still busy after 30 minutes" >&2
  return 1
}

prepare_clone() {
  local sha="$1" dest="$ROOT/$sha"
  mkdir -p "$ROOT"
  if [ ! -d "$dest/.git" ]; then
    git -c core.autocrlf=false clone -q --no-checkout "$SRC" "$dest"
  fi
  git -c core.autocrlf=false -c advice.detachedHead=false -C "$dest" fetch -q "$SRC" "$sha"
  git -c core.autocrlf=false -c advice.detachedHead=false -C "$dest" checkout -q --detach "$sha"
  git -C "$dest" reset -q --hard "$sha"
  git -C "$dest" clean -qfd -e .build
  local head status
  head=$(git -C "$dest" rev-parse HEAD)
  status=$(git -C "$dest" status --porcelain)
  if [ "$head" != "$sha" ] || [ -n "$status" ]; then
    echo "[q5] clone not clean at $sha head=$head status=$status" >&2
    return 1
  fi
  echo "$dest"
}

server_mode() {
  local dest="$1"
  if [ -f "$dest/geometry-web/start_local.py" ]; then echo start_local; else echo serve; fi
}

run_sha() {
  local sha="$1" port="$2" label="$3"
  local dest mode fb logdir spid
  dest=$(prepare_clone "$sha") || return 1
  mode=$(server_mode "$dest")
  fb="/tmp/q5-fb-$label"
  logdir="$OUT/$label"
  mkdir -p "$logdir" "$fb"
  echo "[q5] $label $sha mode=$mode port=$port" | tee "$logdir/runner.log"
  {
    echo "sha=$sha"
    echo "mode=$mode"
    echo "port=$port"
    git -C "$dest" rev-parse HEAD
    git -C "$dest" status --porcelain
  } > "$logdir/identity.txt"
  (
    cd "$dest"
    ulimit -s 16384
    if [ "$mode" = "start_local" ]; then
      npm run build
    else
      npm run build
    fi
  ) > "$logdir/build.log" 2>&1
  local build_rc=$?
  if [ "$build_rc" != 0 ]; then
    echo "[q5] build failed rc=$build_rc" | tee -a "$logdir/runner.log"
    return 1
  fi
  spid=""
  kill_tree() {
    local pid="$1" sig="$2" child
    for child in $(ps -o pid= --ppid "$pid" 2>/dev/null); do
      kill_tree "$child" "$sig"
    done
    kill "-$sig" "$pid" 2>/dev/null || true
  }
  cleanup() {
    if [ -n "${spid:-}" ]; then
      kill_tree "$spid" TERM
      sleep 1
      kill_tree "$spid" KILL
    fi
    pkill -f "user-data-dir=/tmp/q5-chrome-" 2>/dev/null || true
  }
  trap cleanup RETURN
  (
    cd "$dest"
    ulimit -s 16384
    export GEOMETRY_FEEDBACK_DIR="$fb"
    if [ "$mode" = "start_local" ]; then
      exec python3 -u geometry-web/start_local.py --port "$port"
    fi
    export GEOMETRY_BRIDGE="$dest/.build/web_bridge"
    export GEOMETRY_MODEL_BASE="$dest/.build/model_base"
    exec python3 -u geometry-web/serve.py "$port"
  ) > "$logdir/server.log" 2>&1 &
  spid=$!
  echo "[q5] server pid=$spid" | tee -a "$logdir/runner.log"
  local attempt
  : > "$logdir/runtime.json"
  for attempt in $(seq 1 180); do
    if python3 "$dest/geometry-web/runtime_version.py" --probe "$port" > "$logdir/runtime.json" 2>"$logdir/runtime.err"; then
      break
    fi
    if ! kill -0 "$spid" 2>/dev/null; then
      echo "[q5] server exited before runtime probe" | tee -a "$logdir/runner.log"
      return 1
    fi
    sleep 2
  done
  if ! python3 "$dest/geometry-web/runtime_version.py" --probe "$port" > "$logdir/runtime.json" 2>"$logdir/runtime.err"; then
    echo "[q5] runtime probe failed" | tee -a "$logdir/runner.log"
    cat "$logdir/runtime.err" | tee -a "$logdir/runner.log"
    return 1
  fi
  echo "[q5] runtime ok" | tee -a "$logdir/runner.log"
  cat "$logdir/runtime.json" | tee -a "$logdir/runner.log"
  local node_rc=0
  GEOMETRY_REPO="$dest" \
  GEOMETRY_TEST_URL="http://127.0.0.1:$port/" \
  GEOMETRY_Q5_OUT="$logdir" \
  GEOMETRY_FEEDBACK_DIR="$fb" \
  GEOMETRY_CHROME=/usr/bin/google-chrome \
  GEOMETRY_CHROME_FLAGS=--no-sandbox \
  GEOMETRY_CDP_PORT=$((port + 1000)) \
  node "$PROBE" > "$logdir/probe.log" 2>&1 || node_rc=$?
  echo "[q5] probe rc=$node_rc" | tee -a "$logdir/runner.log"
  return "$node_rc"
}

wait_quiet || exit 1

if [ "$#" -gt 0 ]; then
  targets=("$@")
else
  targets=("$MAIN" "$TIP")
  fix=$(git -C "$SRC" rev-parse --verify --quiet fix/closeout-wsl-red-20261010 || true)
  if [ -n "$fix" ] && [ "$fix" != "$TIP" ]; then
    targets+=("$fix")
    echo "[q5] fix branch head $fix"
  elif [ -n "$fix" ]; then
    echo "[q5] fix/closeout-wsl-red-20261010 is $fix, same commit as the chain tip; not run twice"
    mkdir -p "$OUT/fix-same-as-tip"
    printf '%s\n' "$fix" "same commit as $TIP; probe result is the tip run" > "$OUT/fix-same-as-tip/NOTE.txt"
  else
    echo "[q5] fix/closeout-wsl-red-20261010 is absent"
  fi
fi

port=18951
rc_all=0
for sha in "${targets[@]}"; do
  label=${sha:0:8}
  # Re-check immediately before each timing-sensitive probe. Builds above already waited once.
  wait_quiet || exit 1
  if ! run_sha "$sha" "$port" "$label"; then
    rc_all=1
  fi
  port=$((port + 1))
done
echo "[q5] done rc=$rc_all"
exit "$rc_all"
