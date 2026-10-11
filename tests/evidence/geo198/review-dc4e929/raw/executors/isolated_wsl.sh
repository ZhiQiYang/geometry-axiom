#!/bin/bash
# Invoke via: unshare --mount --propagation private bash THIS CHECKOUT OUT COMMAND...
set -eu
checkout=$(realpath "$1")
output=$(realpath -m "$2")
shift 2
case "$output" in /tmp/geo246-*) ;; *) echo 'OUT must be task-owned /tmp/geo246-*' >&2; exit 2;; esac
test -e "$checkout/.git"
test "$output" != "$checkout"
mkdir -p "$output/native" "$output/tmp" "$output/bin" /tmp/geometry-tests
mount --bind "$output/native" /tmp/geometry-tests
ln -sf /usr/bin/python3 "$output/bin/python"
export PATH="$output/bin:${GEO246_NODE_BIN:-/opt/node/bin}:/usr/bin:/bin"
export TMPDIR="$output/tmp"
export MUTATE_CACHE="$output/mutants"
ulimit -s "${GEO246_STACK_KB:-16384}"
cd "$checkout"
exec "$@"
