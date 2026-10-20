#!/bin/bash
# issue #300 微基準:角材容量 64(現值)與 512(套 patch.diff)的載入時間 / 單條指令時間 / 堆疊餘裕。
#
# 這支腳本「只寫、沒跑過」。設計成由主迴圈經 WSL 的鎖執行(鎖的用法見 scratchpad/wsl-ci/wsl_locked3.sh 開頭):
#
#   wsl -d Ubuntu-24.04 -- bash <scratchpad>/wsl-ci/wsl_locked3.sh run \
#       'bash /mnt/d/geometry-axiom-work/drafts/issue300/bench/bench.sh all'
#
# 子指令(預設 all):
#   all        build -> worldbytes -> sanity -> stack -> run -> fit -> 複製結果。每次佔用 <= BENCH_BUDGET_SEC(+硬期限緩衝)。
#   build      只建置(解出 603e4195 的原始碼 -> src64;複製並套 patch.diff -> src512;各編一支 bridge)
#   sanity     worldbytes + 先決驗證(已知良好場景 / 產生器場景 / 第 65 支的容量行為)。失敗結束碼 3
#   stack      堆疊階梯(ulimit -S -s 由大到小)
#   run        主量測(可續跑;預算用完結束碼 10,再執行同一指令會接著做)
#   fit        用目前的 TSV 跑 fit.py
#   status     列出 TSV 已涵蓋的 unit
#   selftest   gen_scene / drive / fit 三個純 Python 自測(秒級,不需要 bridge,可在任何機器跑)
#
# 結束碼:0 全部完成;2 建置失敗;3 sanity 失敗(不要繼續量);10 預算用完、還有 unit 沒做(再跑一次);66 找不到 SHA;75 鎖被占用;70 環境錯誤。
#
# 環境變數(都有預設):
#   BENCH_ROOT        /var/tmp/ga-bench300   工作根目錄(ext4;別放 /tmp,WSL 閒置重開會清空)
#   BENCH_REPO        /mnt/d/geometry-axiom  只讀;用 git archive 取原始碼,不 clone、不建 worktree、不動工作樹
#   BENCH_SHA         603e4195               GEO-261 整合分支最終版
#   BENCH_PATCH       <本目錄>/../patch.diff
#   BENCH_BUDGET_SEC  1500                   軟預算(含建置);預測做不完的 unit 會延後。硬期限 = 軟預算 + BENCH_HARD_EXTRA_SEC
#   BENCH_HARD_EXTRA_SEC 240                 軟預算之後還允許跑多久(超過就殺掉正在跑的指令,rc=125)
#   BENCH_RUN_TIMEOUT 900                    單一指令(含整份 loadfile)的逾時秒數;逾時 rc=124,該 unit 視為已完成(確定性結果)
#   BENCH_NS          "16 32 64 128 256 512"   single 家族要量的 N
#   BENCH_HOUSE_NS    "128 256 512"          house 家族要量的 N(N>=100)
#   BENCH_FAMILIES    "single house"
#   BENCH_CAPS        "64 512"
#   BENCH_REPS        3                      每個 unit 的重複次數(第一次 load > BENCH_REP_CUTOFF 秒就只做 1 次)
#   BENCH_REP_CUTOFF  20
#   BENCH_STACK_RUNGS "16384 14336 12288 11264 10240 9216 8192 7168 6144 5120 4096"
#   BENCH_STACK_RES   256                    二分到這個解析度(KiB)
#   BENCH_CPU         (空)                   設了就用 taskset -c <N> 把 bridge 釘在那顆 CPU
#   BENCH_MODEL_BASE  0                      1 = 另外編 model-base 並多量一個 load-modelbase
#   BENCH_FORCE       0                      1 = 不看預算預測,硬做(要自己負責佔用時間)
#   BENCH_RETRY_TIMEOUTS 0                   1 = 之前 rc=124(逾時)的 unit 重做(調高 BENCH_RUN_TIMEOUT 之後用)
#   BENCH_COPY_TO     /mnt/d/geometry-axiom-work/drafts/issue300/bench/results   結果複製到這裡(Windows 可見);設空字串就不複製
#   CC                gcc
set -u

export PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin   # 只用 Linux 工具,不要誤抓 /mnt/c 的 python/git
export LANG=C.UTF-8 LC_ALL=C.UTF-8 PYTHONIOENCODING=utf-8 GIT_TERMINAL_PROMPT=0

# ----------------------------------------------------------------------------- 0. 自我搬家
# bash 邊跑邊讀腳本;若執行中有人改 D 槽上的原檔,正在跑的 bash 會讀到錯位片段。所以先把整個目錄複製到 ext4 再 exec 副本。
if [ -z "${BENCH_RELOCATED:-}" ]; then
  here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
  root="${BENCH_ROOT:-/var/tmp/ga-bench300}"
  mkdir -p "$root" || exit 70
  run="$root/run-$(date +%Y%m%d-%H%M%S)-$$"
  mkdir -p "$run/calib" || exit 70
  cp "$here/bench.sh" "$here/drive.py" "$here/gen_scene.py" "$here/fit.py" "$run/" || exit 70
  cp "$here"/calib/*.scene "$run/calib/" || exit 70
  export BENCH_RELOCATED=1 BENCH_SRC_DIR="$here" BENCH_RUN_DIR="$run" BENCH_ROOT="$root"
  export BENCH_T0="${BENCH_T0:-$(date +%s)}"
  exec bash "$run/bench.sh" "$@"
fi

cmd="${1:-all}"
[ "$#" -gt 0 ] && shift
root="$BENCH_ROOT"
run="$BENCH_RUN_DIR"
t0="$BENCH_T0"
repo="${BENCH_REPO:-/mnt/d/geometry-axiom}"
sha="${BENCH_SHA:-603e4195}"
patch="${BENCH_PATCH:-$BENCH_SRC_DIR/../patch.diff}"
budget="${BENCH_BUDGET_SEC:-1500}"
hard_extra="${BENCH_HARD_EXTRA_SEC:-240}"
until_epoch=$((t0 + budget))
run_timeout="${BENCH_RUN_TIMEOUT:-900}"
ns="${BENCH_NS:-16 32 64 128 256 512}"
house_ns="${BENCH_HOUSE_NS:-128 256 512}"
families="${BENCH_FAMILIES:-single house}"
caps="${BENCH_CAPS:-64 512}"
reps="${BENCH_REPS:-3}"
rep_cutoff="${BENCH_REP_CUTOFF:-20}"
rungs="${BENCH_STACK_RUNGS:-16384 14336 12288 11264 10240 9216 8192 7168 6144 5120 4096}"
res="${BENCH_STACK_RES:-256}"
copy_to="${BENCH_COPY_TO-/mnt/d/geometry-axiom-work/drafts/issue300/bench/results}"
CC="${CC:-gcc}"
command -v "$CC" >/dev/null 2>&1 || CC=cc

out="$root/out"; bin="$root/bin"; scenes="$root/scenes"; tsv="$out/bench.tsv"
mkdir -p "$out" "$bin" "$scenes" || exit 70

log() { printf '[bench %s +%4ds] %s\n' "$(date +%T)" "$(( $(date +%s) - t0 ))" "$*" >&2; }
csv() { echo "$1" | tr ' ' ','; }

# 單例鎖:同一個 BENCH_ROOT 一次只准一支(wsl_locked3 的鎖是外層;這是防誤啟動兩次)。
exec 9>"$root/.bench.lock"
if ! flock -n 9; then
  echo "[bench] another bench.sh holds $root/.bench.lock; refusing to start" >&2
  exit 75
fi
trap 'pkill -TERM -P $$ 2>/dev/null; exit 143' TERM INT   # 被中斷時帶走自己的子行程(python);bridge 由 setpriv --pdeathsig 跟著死

# ----------------------------------------------------------------------------- 1. 原始碼與建置
GIT=()
resolve_git() {
  local m
  GIT=(git -c safe.directory='*')
  for m in "$HOME"/ga-ci/mirrors/*.git; do      # 優先用 ext4 上既有的 mirror(wsl_ci 留下的),比讀 /mnt/d 快
    [ -d "$m" ] || continue
    if git -c safe.directory='*' --git-dir="$m" cat-file -e "$sha^{commit}" 2>/dev/null; then
      GIT=(git -c safe.directory='*' --git-dir="$m"); return 0
    fi
  done
  GIT=(git -c safe.directory='*' -C "$repo")
  "${GIT[@]}" cat-file -e "$sha^{commit}" 2>/dev/null
}

fullsha=""
patch_sha=""
phase_source() {
  if ! resolve_git; then
    log "SHA $sha not found in $repo or in ~/ga-ci/mirrors (fetch on the Windows side first)"; return 66
  fi
  fullsha="$("${GIT[@]}" rev-parse --verify --quiet "$sha^{commit}")" || return 66
  [ -f "$patch" ] || { log "patch not found: $patch"; return 66; }
  patch_sha="$(sha256sum "$patch" | cut -d' ' -f1)"
  local dst="$root/src64"
  if [ -f "$root/src64.stamp" ] && [ "$(cat "$root/src64.stamp")" = "$fullsha" ] && [ -f "$dst/current_geometry.c" ]; then
    log "src64 reused ($fullsha)"
  else
    log "extracting $fullsha -> $dst (git archive; no clone, no worktree)"
    rm -rf "$dst" "$root/src512" "$root/src512.stamp" "$root/src64.stamp"
    mkdir -p "$dst" || return 70
    local paths=(current_geometry.c _ax_r10_hole_follows_piece.scene _ax_r13_anchor_follows.scene _ax_r17_wall_column_face.scene
                 geometry-core geometry-app geometry-templates geometry-web)
    local excl=(':(exclude)geometry-core/domain-decoupling' ':(exclude)geometry-web/docs' ':(exclude)geometry-web/prototypes' ':(exclude)geometry-web/vendor')
    if ! ( set -o pipefail; "${GIT[@]}" archive --format=tar "$fullsha" -- "${paths[@]}" "${excl[@]}" | tar -x -C "$dst" ); then
      log "archive with excludes failed; retrying without excludes"
      rm -rf "$dst"; mkdir -p "$dst"
      ( set -o pipefail; "${GIT[@]}" archive --format=tar "$fullsha" -- "${paths[@]}" | tar -x -C "$dst" ) || return 70
    fi
    local f
    for f in current_geometry.c geometry-web/web_bridge.c geometry-templates/woodworking/native/members.h _ax_r13_anchor_follows.scene; do
      [ -f "$dst/$f" ] || { log "missing after extract: $f"; return 70; }
    done
    # current_geometry.c 是統一 CRLF(.gitattributes: -text);patch 的 CRLF 片段靠這個才套得上。
    grep -q $'\r' "$dst/current_geometry.c" || { log "current_geometry.c lost its CRLF bytes; patch would not apply"; return 70; }
    echo "$fullsha" > "$root/src64.stamp"
  fi
  # 容量 512 的樹:複製 src64 再套 patch.diff(只套產品檔,不套 tests/ 與 ARCHITECTURE.md)。
  dst="$root/src512"
  if [ -f "$root/src512.stamp" ] && [ "$(cat "$root/src512.stamp")" = "$fullsha:$patch_sha" ] && [ -f "$dst/current_geometry.c" ]; then
    log "src512 reused"
  else
    log "creating src512 = src64 + patch.diff"
    rm -rf "$dst" "$root/src512.stamp"
    cp -a "$root/src64" "$dst" || return 70
    local ap=(--whitespace=nowarn --exclude='tests/*' --exclude='ARCHITECTURE.md')
    if ! ( cd "$dst" && git apply --check "${ap[@]}" "$patch" ) 2>"$out/patch-check.log"; then
      log "patch.diff does not apply to $fullsha (see $out/patch-check.log). It was written for 09ab5f79; the files it touches are byte-identical at 603e4195 per git diff --numstat."
      return 70
    fi
    ( cd "$dst" && git apply "${ap[@]}" "$patch" ) || return 70
    grep -q '^#define WOOD_MEMBER_CAPACITY 512' "$dst/geometry-templates/woodworking/native/members.h" ||
      { log "after patch, members.h does not define WOOD_MEMBER_CAPACITY 512"; return 70; }
    echo "$fullsha:$patch_sha" > "$root/src512.stamp"
  fi
  return 0
}

build_one() {   # $1 = 64|512
  local cap="$1" src="$root/src$1" dir="$bin/cap$1" want
  mkdir -p "$dir"
  want="$fullsha:$([ "$cap" = 512 ] && echo "$patch_sha" || echo none):$("$CC" --version | head -1):-std=c11 -O2:model=${BENCH_MODEL_BASE:-0}"
  if [ -x "$dir/bridge" ] && [ "$(cat "$dir/STAMP" 2>/dev/null)" = "$want" ]; then
    log "cap$cap bridge reused"; return 0
  fi
  rm -f "$dir/STAMP"
  log "building cap$cap: $CC -std=c11 -O2 geometry-web/web_bridge.c -lm"
  ( cd "$src" && time "$CC" -std=c11 -O2 geometry-web/web_bridge.c -o "$dir/bridge.new" -lm ) >"$out/build-cap$cap.log" 2>&1 || return 1
  mv -f "$dir/bridge.new" "$dir/bridge" || return 1
  if [ "${BENCH_MODEL_BASE:-0}" = 1 ]; then
    ( cd "$src" && "$CC" -std=c11 -O2 geometry-core/model_base.c -o "$dir/model-base.new" -lm ) >>"$out/build-cap$cap.log" 2>&1 || return 1
    mv -f "$dir/model-base.new" "$dir/model-base" || return 1
  fi
  echo "$want" > "$dir/STAMP"
}

phase_build() {
  phase_source || return $?
  local pids=() rc=0 p cap
  for cap in 64 512; do
    case " $caps " in *" $cap "*) ;; *) continue ;; esac
    build_one "$cap" &
    pids+=($!)
  done
  for p in "${pids[@]}"; do wait "$p" || rc=2; done
  [ "$rc" = 0 ] || log "build failed; see $out/build-cap*.log"
  return $rc
}

env_report() {
  {
    echo "date=$(date -u +%FT%TZ)  sha=$fullsha  patch_sha256=$patch_sha"
    echo "kernel=$(uname -r)  nproc=$(nproc)  cc=$("$CC" --version | head -1)"
    grep -m1 'model name' /proc/cpuinfo 2>/dev/null
    grep -E 'MemTotal|MemAvailable' /proc/meminfo 2>/dev/null | tr '\n' ' '; echo
    echo "ulimit -s (before)=$(ulimit -s)  ulimit -Hs=$(ulimit -Hs)"
    echo "uptime: $(uptime)"
    echo "top cpu: $(ps -eo pcpu,comm --sort=-pcpu | sed -n 2,4p | tr '\n' ';')"
  } > "$out/env.txt" 2>&1
}

# ----------------------------------------------------------------------------- 2. 量測(都在 ulimit -s 16384 下;與 CI 的 `ulimit -s 16384` 同義)
drive() {
  local extra=()
  [ -n "${BENCH_CPU:-}" ] && extra+=(--cpu "$BENCH_CPU")
  [ "${BENCH_FORCE:-0}" = 1 ] && extra+=(--force)
  [ "${BENCH_RETRY_TIMEOUTS:-0}" = 1 ] && extra+=(--retry-timeouts)
  ( ulimit -s 16384 || exit 126
    exec python3 "$run/drive.py" --tsv "$tsv" --bin-root "$bin" --scene-dir "$scenes" --src-root "$root/src64" \
         --calib "$run/calib/f3-00.scene" --caps "$(csv "$caps")" --run-timeout "$run_timeout" \
         --budget-until "$until_epoch" --hard-extra "$hard_extra" "${extra[@]}" "$@" )
}

phase_worldbytes() { drive worldbytes; }
phase_sanity()     { drive sanity; }
phase_stack()      { drive stack --rungs "$(csv "$rungs")" --resolution "$res"; }
phase_run() {
  local mb=()
  [ "${BENCH_MODEL_BASE:-0}" = 1 ] && mb+=(--model-base)
  drive run --ns "$(csv "$ns")" --house-ns "$(csv "$house_ns")" --families "$(csv "$families")" \
        --reps "$reps" --rep-cutoff "$rep_cutoff" "${mb[@]}"
}
phase_fit() {
  [ -f "$tsv" ] || { log "no TSV yet"; return 0; }
  python3 "$run/fit.py" "$tsv" -o "$out/fit.md" --json "$out/fit.json"
}
publish() {
  [ -n "$copy_to" ] || return 0
  mkdir -p "$copy_to" 2>/dev/null || { log "cannot create $copy_to; results stay in $out"; return 0; }
  cp -f "$tsv" "$out/fit.md" "$out/fit.json" "$out/env.txt" "$out"/build-cap*.log "$copy_to"/ 2>/dev/null
  echo "$1" > "$copy_to/STATUS"
  log "copied results to $copy_to (STATUS: $1)"
}

# ----------------------------------------------------------------------------- 3. 主流程
case "$cmd" in
  selftest)
    rc=0
    python3 "$run/gen_scene.py" --selftest || rc=1
    python3 "$run/drive.py" selftest || rc=1
    python3 "$run/fit.py" --selftest || rc=1
    exit $rc ;;
  status)
    python3 "$run/drive.py" --tsv "$tsv" status; exit $? ;;
  fit)
    phase_fit; exit $? ;;
  build)
    phase_build; exit $? ;;
  sanity|stack|run|all)
    ;;
  *)
    echo "usage: bench.sh [all|build|sanity|stack|run|fit|status|selftest]" >&2; exit 64 ;;
esac

phase_build || { rc=$?; [ "$rc" = 1 ] && rc=2; log "build/source phase failed (rc=$rc)"; exit "$rc"; }
env_report
log "budget ${budget}s (soft) + ${hard_extra}s (hard); started $(( $(date +%s) - t0 ))s ago"
phase_worldbytes || { log "worldbytes failed"; exit 2; }
phase_sanity || { rc=$?; log "sanity failed (rc=$rc): do NOT trust any measurement; fix the cause first"; publish "SANITY-FAILED rc=$rc"; exit "$rc"; }
[ "$cmd" = sanity ] && exit 0

rc_run=0
case "$cmd" in
  stack) phase_stack; rc_run=$? ;;
  run)   phase_run; rc_run=$? ;;
  all)   phase_stack
         phase_run; rc_run=$? ;;
esac
echo "uptime at end: $(uptime)" >> "$out/env.txt"
phase_fit
if [ "$rc_run" = 10 ]; then
  publish "PARTIAL rc=10 at +$(( $(date +%s) - t0 ))s: budget exhausted, run bench.sh again to continue"
  log "PARTIAL: budget exhausted with units left. Run the same command again in the next lock slot."
else
  publish "DONE rc=$rc_run at +$(( $(date +%s) - t0 ))s"
fi
exit "$rc_run"
