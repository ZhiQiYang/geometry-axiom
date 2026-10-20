#!/bin/bash
# gprof profile of one bridge `loadfile` (single-family scene, N timbers) at one SHA.
# Run through the lock: wsl -d Ubuntu-24.04 -- bash <sp>/wsl-ci/wsl_locked3.sh run "bash <sp>/wsl-ci/load_profile.sh [sha] [n]"
set -u
export PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin LANG=C.UTF-8 LC_ALL=C.UTF-8 PYTHONIOENCODING=utf-8
S="${1:-603e4195cf4336321f8c6aa2b90d7ee8969e0572}"; N="${2:-48}"
G=(git -c safe.directory='*' -C /mnt/d/geometry-axiom)
full="$("${G[@]}" rev-parse --verify --quiet "$S^{commit}")" || { echo "cannot resolve $S"; exit 66; }
out=/mnt/d/geometry-axiom-work/load-profile-${full:0:8}-n$N
mkdir -p "$out"; w=$(mktemp -d /var/tmp/prof.XXXXXX); d="$w/src"; mkdir -p "$d"
paths=(); for p in current_geometry.c geometry-core geometry-app geometry-templates geometry-web; do
  "${G[@]}" cat-file -e "$full:$p" 2>/dev/null && paths+=("$p"); done
excl=(':(exclude)geometry-core/domain-decoupling' ':(exclude)geometry-web/docs' ':(exclude)geometry-web/prototypes' ':(exclude)geometry-web/vendor' ':(exclude)geometry-web/node_modules')
( set -o pipefail; "${G[@]}" archive --format=tar "$full" -- "${paths[@]}" "${excl[@]}" | tar -x -C "$d" ) || { echo "archive failed"; exit 70; }
# -fno-inline keeps static helpers visible as separate gprof entries; -O1 keeps the profile close to the -O2 shape without inlining everything away.
( cd "$d" && gcc -std=c11 -O1 -fno-inline -fno-omit-frame-pointer -pg geometry-web/web_bridge.c -o bridge -lm ) > "$out/build.log" 2>&1 || { echo "build failed"; tail -5 "$out/build.log"; exit 2; }
python3 /mnt/d/geometry-axiom-work/drafts/issue300/bench/gen_scene.py "$N" --family single > "$w/s.scene"
cp "$w/s.scene" "$out/scene-n$N.scene"
t0=$(date +%s.%N)
( cd "$w" && ulimit -s 16384 && printf 'loadfile %s\n' "$w/s.scene" | timeout 1200 "$d/bridge" > "$out/load.out" 2> "$out/load.err" ); rc=$?
t1=$(date +%s.%N)
echo "sha=$full n=$N rc=$rc seconds=$(python3 -c "print(round($t1-$t0,3))")" | tee "$out/run.txt"
head -c 300 "$out/load.out"; echo
[ -f "$w/gmon.out" ] || { echo "no gmon.out"; exit 3; }
gprof -b -p "$d/bridge" "$w/gmon.out" > "$out/flat.txt" 2>&1
gprof -b -q "$d/bridge" "$w/gmon.out" > "$out/callgraph.txt" 2>&1
head -40 "$out/flat.txt"
rm -rf "$w"
