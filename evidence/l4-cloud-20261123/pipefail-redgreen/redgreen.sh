#!/bin/bash
# usage（非 root）: redgreen.sh <含 run_one.sh/run_all.sh 的目錄> [fail|pass]
# 用必失敗的子命令（node 以 exit 3 結束）測 run_one.sh 與 run_all.sh 的外層結束碼。
# run_all.sh 依賴的 serve-wt.sh、PDF 夾具產生器、runtime_version.py 以樁代替；被測的兩支腳本是原檔 bytes。
src=$1; mode=${2:-fail}; t=$(mktemp -d); sb=$t/scripts; wt=$t/wt; out=$t/out
mkdir -p "$sb" "$wt/tests/diagnostics" "$wt/geometry-web"
cp "$src/run_one.sh" "$src/run_all.sh" "$sb/"
sha256sum "$sb/run_one.sh" "$sb/run_all.sh" | sed "s#$sb/##"
if [ "$mode" = pass ]; then printf 'console.log("PASS ok child"); process.exit(0);\n' > "$sb/walk_fail.js"; else printf 'console.log("FAIL deliberate child failure"); process.exit(3);\n' > "$sb/walk_fail.js"; fi
for w in walk_d06 walk_d09 walk_d02 walk_pf4a walk_r17 walk_r11_touch; do cp "$sb/walk_fail.js" "$sb/$w.js"; done
printf '#!/bin/bash\necho "{\\"fresh\\": true}"\n' > "$sb/serve-wt.sh"
printf 'import sys,os\no=sys.argv[sys.argv.index("--out")+1]\nos.makedirs(o,exist_ok=True)\nopen(o+"/h-then-line.pdf","w").write("x")\nopen(o+"/manifest.json","w").write("{}")\n' > "$wt/tests/diagnostics/pdf_snap_close_fixtures.py"
printf 'print("{}")\n' > "$wt/geometry-web/runtime_version.py"
(cd "$wt" && git init -q && git -c commit.gpgsign=false -c user.email=x@x -c user.name=x commit -q --allow-empty -m x)
echo "== run_one.sh walk_fail.js"
bash "$sb/run_one.sh" walk_fail.js 1 "$out"; echo "run_one.sh exit=$?"
echo "== run_all.sh"
TMPDIR=$t bash "$sb/run_all.sh" "$wt" 1 "$out"; echo "run_all.sh exit=$?"
rm -rf "$t"
