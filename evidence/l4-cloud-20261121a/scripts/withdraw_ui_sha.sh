#!/bin/bash
# 具名撤回 L4_GCANVAS_RAW_SHA256：baseline（現行 ui.js）→ withdrawn（sha 改回 String(s)）→ restored，各跑 test_ui_sha.js。
# 用法：bash withdraw_ui_sha.sh <receipt.json>；撤回版寫在暫存目錄，不改工作樹。
set -u; here=$(cd "$(dirname "$0")" && pwd); out=$1; tmp=$(mktemp -d)
run() { node "$here/test_ui_sha.js" "$1" > "$tmp/$2.out" 2>&1; echo $?; }
b=$(run "$here/ui.js" baseline)
sed "s/update(Buffer.isBuffer(s) ? s : String(s))/update(String(s))/" "$here/ui.js" > "$tmp/ui.js"
grep -q "update(String(s))" "$tmp/ui.js" || { echo "mutant not applied"; exit 2; }
w=$(run "$tmp/ui.js" withdrawn)
r=$(run "$here/ui.js" restored)
named=$(grep -c "AssertionError.*L4_GCANVAS_RAW_SHA256: Buffer must hash raw bytes" "$tmp/withdrawn.out")
python3 - "$out" "$b" "$w" "$r" "$named" "$(sha256sum "$here/ui.js" | cut -d' ' -f1)" "$(node --version)" <<'PY'
import json,sys
o,b,w,r,n,h,v=sys.argv[1:]
json.dump({"assertion":"L4_GCANVAS_RAW_SHA256","mutant":"ui.js sha(): update(String(s))","baselineExit":int(b),"withdrawnExit":int(w),"withdrawnNamedAssertionFailure":int(n)>0,"restoredExit":int(r),"uiJsSha256":h,"node":v,
 "passed":int(b)==0 and int(w)==1 and int(n)>0 and int(r)==0},open(o,'w'),ensure_ascii=False,indent=1)
PY
cat "$out"; rm -rf "$tmp"
