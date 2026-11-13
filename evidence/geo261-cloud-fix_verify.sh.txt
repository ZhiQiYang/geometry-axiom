#!/bin/bash
# Verify a load-performance fix: (1) loadfile+dump byte-identical between base and fix, (2) interleaved load timing main/base/fix.
# Run through the lock: wsl -d Ubuntu-24.04 -- bash <sp>/wsl-ci/wsl_locked3.sh run "bash <sp>/wsl-ci/fix_verify.sh <main> <base> <fix> [ns] [reps]"
set -u
export PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin LANG=C.UTF-8 LC_ALL=C.UTF-8 PYTHONIOENCODING=utf-8
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
M="${1:?main}"; BASE="${2:?base}"; FIX="${3:?fix}"; NS="${4:-16,32,48,64}"; REPS="${5:-3}"
G=(git -c safe.directory='*' -C /mnt/d/geometry-axiom)
gen=/mnt/d/geometry-axiom-work/drafts/issue300/bench/gen_scene.py
w=$(mktemp -d /var/tmp/fixv.XXXXXX); cp "$here/scale_compare2.py" "$w/"
declare -A dir
for s in "$M" "$BASE" "$FIX"; do
  full="$("${G[@]}" rev-parse --verify --quiet "$s^{commit}")" || { echo "cannot resolve $s"; exit 66; }
  d="$w/${full:0:8}"; dir[$s]="$d"; mkdir -p "$d"
  paths=(); for p in current_geometry.c geometry-core geometry-app geometry-templates geometry-web; do
    "${G[@]}" cat-file -e "$full:$p" 2>/dev/null && paths+=("$p"); done
  excl=(':(exclude)geometry-core/domain-decoupling' ':(exclude)geometry-web/docs' ':(exclude)geometry-web/prototypes' ':(exclude)geometry-web/vendor' ':(exclude)geometry-web/node_modules')
  ( set -o pipefail; "${G[@]}" archive --format=tar "$full" -- "${paths[@]}" "${excl[@]}" | tar -x -C "$d" ) || { echo "archive failed $full"; exit 70; }
  ( cd "$d" && gcc -std=c11 -O2 geometry-web/web_bridge.c -o bridge -lm ) > "$w/build-${full:0:8}.log" 2>&1 || { echo "build failed $full"; tail -5 "$w/build-${full:0:8}.log"; exit 2; }
done
bfull="$("${G[@]}" rev-parse "$BASE^{commit}")"; ffull="$("${G[@]}" rev-parse "$FIX^{commit}")"; mfull="$("${G[@]}" rev-parse "$M^{commit}")"
out=/mnt/d/geometry-axiom-work/fix-verify-${ffull:0:8}
mkdir -p "$out"; cp "$w"/build-*.log "$out/"
{ echo "date=$(date -u +%FT%TZ) main=$mfull base=$bfull fix=$ffull ns=$NS reps=$REPS"; uptime; gcc --version | head -1; } > "$out/env.txt"
# (1) dump equivalence on generated scenes plus every repo-root scene of the base.
eq_fail=0
scenes=()
for n in ${NS//,/ }; do python3 "$gen" "$n" --family single > "$w/s$n.scene" 2>/dev/null; scenes+=("$w/s$n.scene"); done
while IFS= read -r p; do "${G[@]}" show "$bfull:$p" > "$w/repo-$(basename "$p")"; scenes+=("$w/repo-$(basename "$p")"); done < <("${G[@]}" ls-tree --name-only "$bfull" | grep '\.scene$')
for sc in "${scenes[@]}"; do
  for side in "$BASE" "$FIX"; do
    ( cd "$w" && ulimit -s 16384 && printf 'loadfile %s\ndump\n' "$sc" | timeout 900 "${dir[$side]}/bridge" ) > "$w/dump-$(basename "$sc")-${side:0:8}.out" 2>/dev/null
  done
  a="$w/dump-$(basename "$sc")-${BASE:0:8}.out"; b="$w/dump-$(basename "$sc")-${FIX:0:8}.out"
  if cmp -s "$a" "$b"; then r=IDENTICAL; else r=DIFFERENT; eq_fail=1; cp "$a" "$b" "$out/"; fi
  echo "$(basename "$sc") bytes=$(wc -c < "$a") sha=$(sha256sum "$a" | cut -c1-16) $r" | tee -a "$out/dump-equivalence.txt"
done
echo "dump equivalence: $([ $eq_fail = 0 ] && echo ALL-IDENTICAL || echo HAS-DIFFERENCES)" | tee -a "$out/dump-equivalence.txt"
# (2) timing, main first so ratios are vs main.
python3 "$w/scale_compare2.py" "$w" "$out" "main=${dir[$M]}" "base=${dir[$BASE]}" "fix=${dir[$FIX]}" --ns "$NS" --reps "$REPS"
rc=$?
echo "uptime at end: $(uptime)" >> "$out/env.txt"
rm -rf "$w"
[ $eq_fail = 0 ] || exit 4
exit $rc
