#!/bin/bash
# Compare scene-load time vs timber count N between two SHAs through web_bridge loadfile (same path as issue300 bench/drive.py).
# Default: main adbaebf9 vs GEO-261 603e4195. Sources come from git archive (no clone, no worktree).
# Run through the lock: wsl -d Ubuntu-24.04 -- bash <sp>/wsl-ci/wsl_locked3.sh run "bash <sp>/wsl-ci/scale_compare.sh [shaA] [shaB] [ns] [reps]"
set -u
export PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin LANG=C.UTF-8 LC_ALL=C.UTF-8 PYTHONIOENCODING=utf-8
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
A="${1:-adbaebf9c73ea6801d7b4d5214e4b846b132923b}"; B="${2:-603e4195cf4336321f8c6aa2b90d7ee8969e0572}"
NS="${3:-16,32,48,64}"; REPS="${4:-3}"
G=(git -c safe.directory='*' -C /mnt/d/geometry-axiom)
out=/mnt/d/geometry-axiom-work/scale-compare-${A:0:8}-${B:0:8}
mkdir -p "$out"; w=$(mktemp -d /var/tmp/scale.XXXXXX)
cp "$here/scale_compare2.py" "$w/"
sides=()
for s in "$A" "$B"; do
  full="$("${G[@]}" rev-parse --verify --quiet "$s^{commit}")" || { echo "cannot resolve $s"; exit 66; }
  d="$w/${full:0:8}"; mkdir -p "$d"
  paths=(); for p in current_geometry.c geometry-core geometry-app geometry-templates geometry-web; do
    "${G[@]}" cat-file -e "$full:$p" 2>/dev/null && paths+=("$p"); done
  echo "${full:0:8} paths: ${paths[*]}" >> "$out/env.txt"
  excl=(':(exclude)geometry-core/domain-decoupling' ':(exclude)geometry-web/docs' ':(exclude)geometry-web/prototypes' ':(exclude)geometry-web/vendor' ':(exclude)geometry-web/node_modules')
  ( set -o pipefail; "${G[@]}" archive --format=tar "$full" -- "${paths[@]}" "${excl[@]}" | tar -x -C "$d" ) || { echo "archive failed $full"; exit 70; }
  ( cd "$d" && gcc -std=c11 -O2 geometry-web/web_bridge.c -o bridge -lm ) > "$out/build-${full:0:8}.log" 2>&1 \
    || { echo "build failed $full"; tail -5 "$out/build-${full:0:8}.log"; exit 2; }
  echo "built ${full:0:8} $(sha256sum "$d/bridge" | cut -c1-16)" | tee -a "$out/env.txt"
  sides+=("${full:0:8}=$d")
done
{ echo "date=$(date -u +%FT%TZ) A=$A B=$B ns=$NS reps=$REPS"; uptime; gcc --version | head -1; } >> "$out/env.txt"
python3 "$w/scale_compare2.py" "$w" "$out" "${sides[@]}" --ns "$NS" --reps "$REPS"
rc=$?
echo "uptime at end: $(uptime)" >> "$out/env.txt"
rm -rf "$w"
exit $rc
