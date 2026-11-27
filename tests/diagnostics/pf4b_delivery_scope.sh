#!/bin/sh
# #474 專用：比較 PR 分岔點與候選樹，不禁止日後由獨立的 PF-5 PR 交付。
set -eu
if [ "$#" -ne 2 ]; then
    echo "用法：sh $0 <PR merge-base> <候選 commit 或 tree>" >&2
    exit 2
fi
cd "$(git rev-parse --show-toplevel)"
changed=$(git diff --no-renames --name-only "$1^{tree}" "$2^{tree}" -- \
    geometry-web/docs/PF5-GEOMETRY-DESIGN.md \
    tests/pf5_geometry_oracle.py \
    tests/pf5_geometry_check.py \
    tests/pf5_geometry_mutations.py \
    tests/test_pf5_geometry_oracle.py \
    tests/suites.d/py__test_pf5_geometry_oracle.json)
if [ -n "$changed" ]; then
    printf 'FAIL PF4B_NO_PF5_DELIVERY：PF-4B 差異含 PF-5 檔案\n%s\n' "$changed" >&2
    exit 1
fi
printf 'PASS PF4B_NO_PF5_DELIVERY\n'
