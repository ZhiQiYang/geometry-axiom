#!/bin/bash
# 下角材 oracle 探針。在 WSL 執行：bash run_probe.sh [輸出目錄]
# 預設輸出 /var/tmp/framing-core-probe。不要寫進其他 worktree，也不要覆蓋 repo 內的 scenes/。
# 本機 Windows 不跑這支腳本、不編譯。
set -u
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo="$(cd "$here/../../.." && pwd)"
out="${1:-/var/tmp/framing-core-probe}"
mkdir -p "$out"

if ! command -v python3 >/dev/null 2>&1; then
  echo "python3 不在 PATH，原始 log 無法彙整" | tee "$out/summary.txt"
  exit 70
fi

python3 "$here/gen_scenes.py" --out "$out/scenes" --index "$out/index.json" || exit 70

w=$(mktemp -d /var/tmp/framing-core.XXXXXX)
cleanup() { rm -rf "$w"; }
trap cleanup EXIT
cp "$repo/current_geometry.c" "$w/current_geometry.c"
cp -a "$repo/geometry-core" "$w/geometry-core"
cd "$w" || exit 70
cc -std=c11 -O2 current_geometry.c -o core -lm > "$out/build.log" 2>&1
build_rc=$?
{
  echo "build_rc=$build_rc"
  echo "repo=$repo"
} > "$out/summary.txt"
if [ "$build_rc" -ne 0 ]; then
  echo "建置失敗，沒有場景結果" >> "$out/summary.txt"
  exit "$build_rc"
fi

shopt -s nullglob
for s in "$out/scenes"/*.scene; do
  n=$(basename "$s" .scene)
  d="$out/$n"
  mkdir -p "$d/blocks"
  ./core --scene "$s" --no-window --out "$w/out.svg" > "$d/full.out" 2> "$d/full.err"
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
    ./core --scene "$tmp" --no-window --out "$w/out.svg" > "$d/$k.out" 2> "$d/$k.err"
    one=$?
    echo "$one" > "$d/$k.rc"
    echo "$rejected" > "$d/$k.omit"
    if [ "$one" -eq 0 ]; then
      retained="$retained $num"
    else
      rejected="$rejected $num"
      rej_count=$((rej_count + 1))
    fi
  done
  echo "$n full_rc=$rc members=$member_count rejected=$rej_count" >> "$out/summary.txt"
done

python3 "$here/parse_results.py" --run-dir "$out" --scenes "$out/scenes"
parse_rc=$?
echo "parse_rc=$parse_rc" >> "$out/summary.txt"
exit "$parse_rc"
