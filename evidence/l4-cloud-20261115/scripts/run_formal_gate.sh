#!/bin/bash
# Run the formal rule-case App browser gate, unmodified, against one clean worktree, and keep a receipt.
# usage: run_formal_gate.sh <worktree dir> <port> <receipt dir> <label>
# Starts a private test server from that worktree (not a user's service) and stops it afterwards.
wt=$1; port=$2; out=$3; label=$4
S=/tmp/claude-0/-home-user-geometry-axiom/c161fbcc-185e-5abd-ba3d-eaec6a803bff/scratchpad
mkdir -p "$out"; cd "$wt" || exit 2
head=$(git rev-parse HEAD); tree=$(git rev-parse 'HEAD^{tree}'); dirty=$(git status --porcelain | wc -l)
pkill -f "start_local.py --port $port"; pkill -f "serve.py $port"; sleep 2
ulimit -s 16384
python3 geometry-web/start_local.py --build-only > "$out/$label.build.log" 2>&1 || { echo "build failed"; exit 3; }
GEOMETRY_FEEDBACK_DIR="$S/fb-gate-$label" nohup python3 -u geometry-web/start_local.py --port $port > "$out/$label.server.log" 2>&1 &
for i in $(seq 1 90); do python3 geometry-web/runtime_version.py --probe $port >/dev/null 2>&1 && break; sleep 1; done
runtime=$(python3 geometry-web/runtime_version.py --probe $port) || { echo "server failed"; exit 4; }
work="$S/gate-out-$label"; rm -rf "$work"
started=$(date -u +%Y-%m-%dT%H:%M:%SZ); t0=$(date +%s)
GEOMETRY_TEST_URL="http://127.0.0.1:$port/" GEOMETRY_RULE_CASE_APP_OUT="$work" GEOMETRY_REQUIRE_CLEAN=1 \
  node tests/test_rule_case_app_browser.js > "$out/$label.stdout.txt" 2> "$out/$label.stderr.txt"
code=$?; t1=$(date +%s)
pkill -f "start_local.py --port $port"; pkill -f "serve.py $port"
python3 - "$out/$label.receipt.json" <<EOF
import json, sys
json.dump({
  "command": "GEOMETRY_TEST_URL=http://127.0.0.1:<port>/ GEOMETRY_RULE_CASE_APP_OUT=<temp dir> GEOMETRY_REQUIRE_CLEAN=1 node tests/test_rule_case_app_browser.js",
  "label": "$label", "head": "$head", "tree": "$tree", "uncommittedPaths": $dirty,
  "runtime": json.loads('''$runtime'''),
  "node": "$(node --version)", "chromium": "$(/usr/bin/chromium --version 2>/dev/null)",
  "startedAt": "$started", "seconds": $((t1 - t0)), "exitCode": $code,
  "passLines": sum(1 for line in open("$out/$label.stdout.txt", encoding="utf-8") if line.startswith("PASS ")),
}, open(sys.argv[1], "w", encoding="utf-8"), ensure_ascii=False, indent=1)
open(sys.argv[1], "a").write("\n")
EOF
echo "$label head=${head:0:8} dirty=$dirty exit=$code seconds=$((t1 - t0)) pass=$(grep -c '^PASS ' "$out/$label.stdout.txt")"
tail -3 "$out/$label.stdout.txt" | cut -c1-200; tail -4 "$out/$label.stderr.txt" | cut -c1-300
