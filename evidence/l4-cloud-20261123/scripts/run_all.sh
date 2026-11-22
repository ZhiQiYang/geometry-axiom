#!/bin/bash
# usage（非 root，TMPDIR 已設）: run_all.sh <main 工作樹> <port> <輸出目錄>
# 重啟私人測試服務一次（新程序／新 session），存 runtime probe，再依序跑六項；每項各開新瀏覽器。
set -e
here=$(cd "$(dirname "$0")" && pwd)
wt=$1; port=$2; out=$3
mkdir -p "$out/screens" "$out/pdf"
python3 -I "$wt/tests/diagnostics/pdf_snap_close_fixtures.py" --out "$TMPDIR/pdfgen" >/dev/null
cp "$TMPDIR/pdfgen/h-then-line.pdf" "$TMPDIR/pdfgen/manifest.json" "$out/pdf/"
bash "$here/serve-wt.sh" "$wt" "$port" "$TMPDIR/fb-final" | tail -1 > "$out/runtime-probe.json"
grep -q '"fresh": true' "$out/runtime-probe.json" || { echo "probe not fresh"; cat "$out/runtime-probe.json"; exit 1; }
rc=0
for w in walk_d06.js walk_d09.js walk_d02.js walk_pf4a.js walk_r17.js walk_r11_touch.js; do
  bash "$here/run_one.sh" "$w" "$port" "$out" | tail -1 || rc=1
done
(cd "$wt" && python3 geometry-web/runtime_version.py --probe "$port") > "$out/runtime-probe.after.json"
(cd "$wt" && git rev-parse HEAD && git status --short | wc -l) > "$out/worktree-state.txt"
exit $rc
