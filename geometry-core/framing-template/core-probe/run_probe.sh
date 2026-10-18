#!/bin/bash
# 下角材 oracle 探針。在 WSL 執行：bash run_probe.sh [輸出目錄]
# 預設輸出 /var/tmp/framing-core-probe。不要寫進其他 worktree，也不要覆蓋 repo 內的 scenes/。
# 本機 Windows 不跑這支腳本、不編譯。
#
# 結束碼分類（依 opus／ChatGPT 對 #297 的審查更正）：
#   current_geometry.c 的 main() 只回 0（接受）或 1（拒絕、參數錯、讀檔失敗），沒有別的回傳值。
#   所以只有 1 算規則拒絕。其他非 0（139／134 崩潰、124 逾時、127 找不到執行檔…）是「錯誤」，
#   不得計成拒絕；腳本最後的結束碼由 parse_results.py 決定，有任何「錯誤」或「幾何不符」列就非 0。
#
# 測試用環境變數（平常不用設）：
#   CORE_BIN          用這個現成的執行檔（或假核心）代替編譯 current_geometry.c
#   PROBE_SCENES_DIR  用這個目錄的 *.scene 代替 gen_scenes.py 的輸出
#   PYTHON            python 直譯器，預設 python3
#   CORE_TIMEOUT      每次呼叫核心的秒數上限，預設 120；沒有 timeout 指令就不設上限
#   TMPDIR            暫存根目錄，預設 /var/tmp
set -u
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo="$(cd "$here/../../.." && pwd)"
out="${1:-/var/tmp/framing-core-probe}"
py="${PYTHON:-python3}"
core_timeout="${CORE_TIMEOUT:-120}"
core_reject_rc=1  # 與 parse_results.CORE_REJECT_RC 相同
mkdir -p "$out"
out="$(cd "$out" && pwd)"  # 後面會 cd 到暫存目錄，輸出路徑要先絕對化

if ! command -v "$py" >/dev/null 2>&1; then
  echo "$py 不在 PATH，原始 log 無法彙整" | tee "$out/summary.txt"
  exit 70
fi

if [ -n "${PROBE_SCENES_DIR:-}" ]; then
  rm -rf "$out/scenes"
  mkdir -p "$out/scenes"
  cp "$PROBE_SCENES_DIR"/*.scene "$out/scenes/" || exit 70
else
  "$py" "$here/gen_scenes.py" --out "$out/scenes" --index "$out/index.json" || exit 70
fi

w=$(mktemp -d "${TMPDIR:-/var/tmp}/framing-core.XXXXXX")
cleanup() { rm -rf "$w"; }
trap cleanup EXIT
cd "$w" || exit 70

if [ -n "${CORE_BIN:-}" ]; then
  cp "$CORE_BIN" "$w/core" && chmod +x "$w/core"
  build_rc=$?
  echo "使用 CORE_BIN=$CORE_BIN，沒有編譯" > "$out/build.log"
else
  cp "$repo/current_geometry.c" "$w/current_geometry.c"
  cp -a "$repo/geometry-core" "$w/geometry-core"
  cc -std=c11 -O2 current_geometry.c -o core -lm > "$out/build.log" 2>&1
  build_rc=$?
fi
{
  echo "build_rc=$build_rc"
  echo "repo=$repo"
} > "$out/summary.txt"
if [ "$build_rc" -ne 0 ]; then
  echo "建置失敗，沒有場景結果" >> "$out/summary.txt"
  exit "$build_rc"
fi

timeout_cmd=""
if command -v timeout >/dev/null 2>&1; then
  timeout_cmd="timeout -k 2 $core_timeout"
else
  echo "沒有 timeout 指令，核心呼叫不設上限" >> "$out/summary.txt"
fi

# 呼叫核心一次。結束碼由呼叫者分類：0 接受、$core_reject_rc 拒絕、其餘 = 錯誤。
run_core() {
  # shellcheck disable=SC2086
  $timeout_cmd ./core --scene "$1" --no-window --out "$w/out.svg"
}

shopt -s nullglob
total_errors=0
for s in "$out/scenes"/*.scene; do
  n=$(basename "$s" .scene)
  d="$out/$n"
  mkdir -p "$d/blocks"
  run_core "$s" > "$d/full.out" 2> "$d/full.err"
  rc=$?
  echo "$rc" > "$d/full.rc"
  if [ "$rc" -eq 0 ]; then
    echo "$n full_rc=0" >> "$out/summary.txt"
    continue
  fi
  awk -v dir="$d/blocks" '
    BEGIN { n = 0; header = 1; file = "" }
    /^# probe-member / {
      header = 0
      n++
      file = sprintf("%s/m%03d.block", dir, n)
      print > file
      next
    }
    {
      if (header) print > (dir "/header")
      else if (file != "") print > file
    }
  ' "$s"
  retained=""
  rejected=""
  rej_count=0
  err_count=0
  member_count=0
  for block in "$d"/blocks/m*.block; do
    member_count=$((member_count + 1))
    k=$(basename "$block" .block)
    num=$((10#${k#m}))
    tmp="$w/try.scene"
    if [ -f "$d/blocks/header" ]; then
      cat "$d/blocks/header" > "$tmp"
    else
      : > "$tmp"
    fi
    for kept in $retained; do
      cat "$d/blocks/m$(printf '%03d' "$kept").block" >> "$tmp"
    done
    cat "$block" >> "$tmp"
    run_core "$tmp" > "$d/$k.out" 2> "$d/$k.err"
    one=$?
    echo "$one" > "$d/$k.rc"
    echo "$rejected" > "$d/$k.omit"
    if [ "$one" -eq 0 ]; then
      retained="$retained $num"
    elif [ "$one" -eq "$core_reject_rc" ]; then
      rejected="$rejected $num"
      rej_count=$((rej_count + 1))
    else
      # 崩潰、訊號、逾時：不是規則拒絕。仍從後面的前綴拿掉，免得一支異常拖垮整場；
      # parse_results.py 會把這一列標成「錯誤」。
      rejected="$rejected $num"
      err_count=$((err_count + 1))
    fi
  done
  total_errors=$((total_errors + err_count))
  echo "$n full_rc=$rc members=$member_count rejected=$rej_count errors=$err_count" >> "$out/summary.txt"
done
echo "total_core_errors=$total_errors" >> "$out/summary.txt"

"$py" "$here/parse_results.py" --run-dir "$out" --scenes "$out/scenes"
parse_rc=$?
echo "parse_rc=$parse_rc" >> "$out/summary.txt"
exit "$parse_rc"
