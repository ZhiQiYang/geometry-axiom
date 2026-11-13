#!/usr/bin/env bash
set -euo pipefail
test -e /proc/$$/fd/7
test "$(stat -L -c %d:%i /proc/$$/fd/7)" = "$(stat -c %d:%i /run/lock/ga-wsl-v3.lock)"
SOURCE=a898ad6e12707104568679591fe1b21804bfc3df
CHECKOUT=/var/tmp/geo261-baseline-a898ad6e
EVIDENCE=/mnt/d/geometry-axiom-work/geo261-evidence/p1
OBJECTS=/mnt/d/geometry-axiom/.git/objects
if [ ! -e "$CHECKOUT" ]; then
  mkdir "$CHECKOUT"
  git -C "$CHECKOUT" init --quiet
  git -C "$CHECKOUT" config core.autocrlf false
  printf '%s\n' "$OBJECTS" > "$CHECKOUT/.git/objects/info/alternates"
  git -C "$CHECKOUT" checkout --quiet --detach "$SOURCE"
fi
test "$(git -C "$CHECKOUT" rev-parse HEAD)" = "$SOURCE"
test -z "$(git -C "$CHECKOUT" status --porcelain=v1)"
mkdir -p "$CHECKOUT/.git/geo261-environment/tmp"
exec unshare --mount --net --propagation private bash "$EVIDENCE/baseline-namespace.sh"
