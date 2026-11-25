#!/bin/bash
# usage（非 root，TMPDIR 已設）: run_all.sh <main 工作樹> <port> <輸出目錄>
# 重啟私人測試服務一次（新程序／新 session），存 runtime probe，再依序跑六項；每項各開新瀏覽器。
# 2026-11-23 修正（#453 審查須改四）：加 pipefail；任一 walk 失敗時 `|| rc=1` 才會生效，其餘 walk 照跑，最後以非 0 結束。
# 本輪 main-ea16e3f5/ 的既有收據是修正前的版本產生的，見 README「腳本結束碼」一節。
set -eo pipefail
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
