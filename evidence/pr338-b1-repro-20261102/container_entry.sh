#!/bin/bash
set -euo pipefail
export DEBIAN_FRONTEND=noninteractive
export LANG=C.UTF-8
export LC_ALL=C.UTF-8
apt-get update > /evidence/apt-update.stdout.txt 2> /evidence/apt-update.stderr.txt
apt-get install -y --no-install-recommends gcc binutils libc6-dev python3 file \
  > /evidence/apt-install.stdout.txt 2> /evidence/apt-install.stderr.txt
ulimit -s 16384
exec python3 /input/evidence/pr338-b1-repro-20261102/reproduce.py --root /input --out /evidence
